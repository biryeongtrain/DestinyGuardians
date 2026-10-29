package kim.biryeong.destiny.test;

import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/** Server callback regression for the W179 trace. Not native-client timing evidence. */
public final class ShellInterruptW180GameTests {
    private static final String FLOOR="destiny-test:floor", ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean ok,String why){h.assertTrue(ok,Component.literal(why));}
    private static final class Fixture {
        final ServerPlayer player;
        final WeaponProfile profile=WeaponProfile.forEntry(WeaponCatalog.find("mindbender_s_ambition_adept").orElseThrow());
        final ItemStack gun;
        boolean sawNewReload;
        Fixture(GameTestHelper h,WeaponModels.Grip grip){
            player=TestPlayers.create(h,new Vec3(2.5,1,6.5),-90,-80);
            gun=WeaponModels.withGrip(WeaponItems.create(WeaponCatalog.find("mindbender_s_ambition_adept").orElseThrow()),grip).orElseThrow();
            WeaponItems.save(gun,new WeaponMagazine(profile,0,20));
            player.setItemInHand(InteractionHand.MAIN_HAND,gun);
            h.onEachTick(this::tick);
            TestCleanup.register(h,()->{WeaponRuntime.cleanup(player);CombatHud.remove(player);TestPlayers.remove(player);});
            check(h,WeaponRuntime.reload(player),"Accepted existing empty incremental reload / "+grip);
        }
        void tick(){WeaponRuntime.tickPlayer(player);TestPlayers.drain(player);}
        WeaponMagazine ammo(){return WeaponItems.magazine(gun,profile);}
        void pressAndRelease(){
            WeaponCombatItem.INSTANCE.use(player.level(),player,InteractionHand.MAIN_HAND);
            // Native protocol gets its actual release; two-hand ends by heartbeat expiry.
            if(!WeaponModels.twoHanded(gun))player.releaseUsingItem();
        }
    }
    private static Fixture[] pair(GameTestHelper h){return new Fixture[]{new Fixture(h,WeaponModels.Grip.NATIVE),new Fixture(h,WeaponModels.Grip.TWO_HAND)};}

    @GameTest(structure=FLOOR,maxTicks=135,environment=ENV)
    public void singleFundedShellFiresOnceThenExistingLastShotPolicyReloadsWithoutAnotherTrigger(GameTestHelper h){
        var fixtures=pair(h);
        h.runAfterDelay(16,()->{
            for(var f:fixtures){
                f.tick();check(h,f.ammo().rounds()==1&&f.ammo().reserve()==19,"First real16tick insert owns exactly one shell");
                f.pressAndRelease();check(h,f.ammo().rounds()==0&&f.ammo().reserve()==19,"One real use callback spends the inserted shell");
                check(h,!WeaponInsertPresentation.active(f.gun),"Old insert prop clears immediately on paid shot");
            }
        });
        for(int delay=17;delay<=112;delay++){
            int at=delay;
            h.runAfterDelay(delay,()->{
                for(var f:fixtures){
                    // No new use/heartbeat/console-reload callback after the single shot.
                    f.tick();f.sawNewReload|=WeaponRuntime.reloading(f.player);
                    check(h,f.ammo().total()==19,"Automatic transfer cannot fabricate reserve or fire a second round");
                    if(at==20)check(h,WeaponRuntime.reloading(f.player),"Last-shot automatic reload explains W179 final reloading=true");
                    if(at==112){
                        check(h,f.sawNewReload&&!WeaponRuntime.reloading(f.player),"Shot-owned candidate reloads and retires without new input");
                        check(h,f.ammo().rounds()==5&&f.ammo().reserve()==14,"Exactly five real reserve units transfer, no latent extra shot");
                        check(h,!WeaponInsertPresentation.active(f.gun),"New reload's cosmetic return also retires");
                    }
                }
                if(at==112)h.succeed();
            });
        }
    }

    @GameTest(structure=FLOOR,maxTicks=100,environment=ENV)
    public void twoFundedShellsLeaveOneRoundAndDoNotRestartReloadWithoutNewInput(GameTestHelper h){
        var fixtures=pair(h);
        h.runAfterDelay(32,()->{
            for(var f:fixtures){
                f.tick();check(h,f.ammo().rounds()==2&&f.ammo().reserve()==18,"Second actual insert funded");
                f.pressAndRelease();check(h,f.ammo().rounds()==1&&f.ammo().reserve()==18,"Exactly one of two shells fires");
                check(h,!WeaponRuntime.reloading(f.player)&&!WeaponInsertPresentation.active(f.gun),"Paid shot cancels existing reload immediately");
            }
        });
        for(int delay=33;delay<=86;delay++){
            int at=delay;
            h.runAfterDelay(delay,()->{
                for(var f:fixtures){
                    f.tick();check(h,!WeaponRuntime.reloading(f.player)&&f.ammo().rounds()==1&&f.ammo().reserve()==18,
                            "Nonempty interrupt stays cancelled beyond old deadlines; no repeated trigger or free inserts");
                }
                if(at==86)h.succeed();
            });
        }
    }

    @GameTest(structure=FLOOR,maxTicks=50,environment=ENV)
    public void earlySkillCancelIsNotARecentlyPaidLastShotAndCannotQueueAutomaticReload(GameTestHelper h){
        var fixtures=pair(h);
        h.runAfterDelay(8,()->{for(var f:fixtures)WeaponRuntime.cancelUseForSkill(f.player);});
        h.runAfterDelay(40,()->{
            for(var f:fixtures){
                f.tick();check(h,!WeaponRuntime.reloading(f.player)&&f.ammo().rounds()==0&&f.ammo().reserve()==20,
                        "Cancelled empty item does not spontaneously reload on its old timer");
                check(h,!WeaponInsertPresentation.active(f.gun),"No stale selector binding");
            }
            h.succeed();
        });
    }
}
