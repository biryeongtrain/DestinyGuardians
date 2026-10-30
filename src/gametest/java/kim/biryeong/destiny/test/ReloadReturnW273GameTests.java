package kim.biryeong.destiny.test;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponPerkHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.phys.Vec3;

/** Real runtime/Polymer regression; native frame/contact verification remains master Vision. */
public final class ReloadReturnW273GameTests {
    private static final String FLOOR = "destiny-test:floor", ENV = "destiny-test:w90_isolated";
    private static void check(GameTestHelper h, boolean value, String why) {
        h.assertTrue(value, Component.literal(why));
    }
    private static final class Fixture {
        final ServerPlayer player;
        final WeaponProfile profile;
        final ItemStack gun;
        final Identifier idle;
        final long total;
        Fixture(GameTestHelper h, String id, int reserve) {
            player = TestPlayers.create(h, new Vec3(2.5,1,6.5), -90, 90);
            player.setNoGravity(true);
            TestCleanup.register(h, () -> {
                WeaponRuntime.cleanup(player); WeaponPerkHud.remove(player);
                CombatHud.remove(player); TestPlayers.remove(player);
            });
            var entry = WeaponCatalog.find(id).orElseThrow();
            profile = WeaponProfile.forEntry(entry); gun = WeaponItems.create(entry);
            WeaponItems.save(gun, new WeaponMagazine(profile,1,reserve));
            player.setItemInHand(InteractionHand.MAIN_HAND,gun); tick();
            idle = wire().get(DataComponents.ITEM_MODEL); total = ammo().total();
            h.onEachTick(this::tick);
        }
        void tick() { WeaponRuntime.tickPlayer(player); TestPlayers.drain(player); }
        WeaponMagazine ammo() { return WeaponItems.magazine(gun,profile); }
        ItemStack wire() {
            var context = ((PacketContextProvider)(Object)player.connection).getPacketContext();
            return PolymerItemUtils.getPolymerItemStack(gun,context,player.level().registryAccess());
        }
        float selector(int slot) {
            var value = gun.getOrDefault(DataComponents.CUSTOM_MODEL_DATA,CustomModelData.EMPTY).getFloat(slot);
            return value == null ? -1 : value;
        }
        int start(GameTestHelper h, boolean honed) {
            check(h,honed ? WeaponRuntime.reloadHoned(player) : WeaponRuntime.reload(player),"Actual reload accepted");
            return WeaponRuntime.ammunition(player).orElseThrow().reloadDuration();
        }
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=10)
    public void cosmeticClockPublishesEndpointAndCannotExtendItself(GameTestHelper h) {
        for (int duration : new int[]{1,5,61,1200}) {
            var clock = new WeaponReloadReturn(duration);
            float previous = -1;
            for (int i=0;i<=duration;i++) {
                float current = clock.progress(i,i/(float)duration);
                check(h,current>=previous && current<1,"Source playback remains monotonic before completion");
                previous=current;
            }
            check(h,!clock.active(duration),"A normalized selector cannot authorize recovery");
            clock.complete(duration);
            for (int i=0;i<=WeaponReloadReturn.RETURN_TICKS;i++) {
                float current=clock.progress(duration+i,1);
                check(h,clock.active(duration+i) && current>=previous,"Funded tail advances monotonically");
                clock.complete(duration+i); // Repeated tick publication must not move its deadline.
                previous=current;
            }
            check(h,previous==1 && !clock.active(duration+WeaponReloadReturn.RETURN_TICKS+1),
                    "Pose60 is published once before retirement; duplicate completion never extends it");
        }
        h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=200)
    public void fullReadyKeepsExistingBankThroughPose60WithoutExtraCredit(GameTestHelper h) {
        var f=new Fixture(h,"beloved",12); int duration=f.start(h,false);
        h.runAfterDelay(duration-1,()->{f.tick();check(h,WeaponRuntime.reloading(f.player),"Original full-ready deadline unchanged");});
        float[] last={-1};
        for(int tail=0;tail<=WeaponReloadReturn.RETURN_TICKS;tail++) {
            final int at=tail;
            h.runAfterDelay(duration+tail,()->{
                f.tick();
                check(h,!WeaponRuntime.reloading(f.player) && f.ammo().rounds()==f.profile.magazine()
                        && f.ammo().total()==f.total,"Gameplay completed once; recovery never credits ammo");
                check(h,WeaponReloadPresentation.returning(f.player,f.gun)
                        && WeaponReloadPresentation.ownedBy(f.player,f.gun),"Owner retains cosmetic route after gameplay ends");
                float selector=f.selector(1);
                check(h,selector>=last[0] && selector<=1.0011f,"Existing bank advances, never rewinds");last[0]=selector;
                check(h,!f.idle.equals(f.wire().get(DataComponents.ITEM_MODEL)),"Actual Polymer carrier retains reload model");
                check(h,!WeaponReloadPresentation.active(f.gun.copy()),"Copied selector never obtains return authority");
                if(at==WeaponReloadReturn.RETURN_TICKS)check(h,selector>=1,"Final pose60 reaches the wire before idle");
            });
        }
        h.runAfterDelay(duration+WeaponReloadReturn.RETURN_TICKS+1,()->{
            f.tick();check(h,!WeaponReloadPresentation.active(f.gun) && f.idle.equals(f.wire().get(DataComponents.ITEM_MODEL)),
                    "Idle restored after endpoint publication");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=200)
    public void acceptedShotImmediatelyRetiresRecoveryWithoutDelayingFire(GameTestHelper h) {
        var f=new Fixture(h,"beloved",12);int duration=f.start(h,false);
        h.runAfterDelay(duration,()->{
            f.tick();check(h,WeaponReloadPresentation.returning(f.player,f.gun),"Recovery starts on full-ready");
            int loaded=f.ammo().rounds();
            check(h,WeaponRuntime.beginUse(f.player),"Shot accepted on original full-ready tick");
            WeaponRuntime.releaseUse(f.player,f.gun);
            check(h,f.ammo().rounds()==loaded-1 && !WeaponReloadPresentation.active(f.gun),
                    "One real debit and no lingering reload parts/hands");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=200)
    public void copiedSwapRetiresOldReturnWithoutAdmittingCopiedSelectors(GameTestHelper h) {
        var f=new Fixture(h,"beloved",12);int duration=f.start(h,false);
        h.runAfterDelay(duration+1,()->{
            f.tick();check(h,WeaponReloadPresentation.returning(f.player,f.gun),"Live return before swap");
            var copy=f.gun.copy();f.player.setItemInHand(InteractionHand.MAIN_HAND,copy);
            check(h,!WeaponReloadPresentation.active(f.gun) && !WeaponReloadPresentation.active(copy),
                    "Exact stack identity rejects both old owner pose and copied selector immediately");
            f.tick();check(h,!WeaponReloadPresentation.ownedBy(f.player,f.gun),"Runtime retires donor binding");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=200)
    public void skillCancelsRecoveryAndEarlyCancelNeverCreatesOne(GameTestHelper h) {
        var f=new Fixture(h,"beloved",12);int duration=f.start(h,false);
        h.runAfterDelay(duration+1,()->{
            f.tick();check(h,WeaponReloadPresentation.returning(f.player,f.gun),"Live return before skill");
            WeaponRuntime.cancelUseForSkill(f.player);
            check(h,!WeaponReloadPresentation.active(f.gun),"Skill clears cosmetic route immediately");
        });
        h.runAfterDelay(duration+9,()->{
            f.tick();check(h,!WeaponReloadPresentation.active(f.gun),"Cancelled recovery cannot reappear");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=200)
    public void earlySkillCancelNeverStartsCompletionRecovery(GameTestHelper h) {
        var f=new Fixture(h,"beloved",12);int duration=f.start(h,false);
        WeaponRuntime.cancelUseForSkill(f.player);
        h.runAfterDelay(duration+9,()->{
            f.tick();check(h,!WeaponReloadPresentation.active(f.gun) && f.ammo().rounds()==1
                    && f.ammo().total()==f.total,"Cancelled reload neither funds ammo nor starts a ghost return");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=100)
    public void honedCompletionFinishesExisting61PoseBankBeforeChargedIdle(GameTestHelper h) {
        var f=new Fixture(h,"izanagis_burden",5);int duration=f.start(h,true);
        h.runAfterDelay(duration,()->{
            f.tick();check(h,!WeaponRuntime.reloading(f.player) && WeaponIzanagi.charge(f.gun)==4
                    && f.ammo().rounds()==1 && f.ammo().reserve()==2,"Original Honed transaction commits at its original deadline");
            check(h,WeaponIzanagiPresentation.returning(f.player,f.gun) && f.selector(6)>=2 && f.selector(6)<3,
                    "Honed source tail remains visible instead of jumping to charged idle4");
        });
        h.runAfterDelay(duration+6,()->{f.tick();check(h,f.selector(6)>=3 && f.selector(6)<3.001f,"Honed pose60 published");});
        h.runAfterDelay(duration+7,()->{
            f.tick();check(h,!WeaponIzanagiPresentation.returning(f.player,f.gun) && f.selector(6)>=4
                    && WeaponIzanagi.charge(f.gun)==4,"Charged idle restored without spending saved charge");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=100)
    public void shotDuringHonedReturnConsumesChargeAndClearsItsPose(GameTestHelper h) {
        var f=new Fixture(h,"izanagis_burden",5);int duration=f.start(h,true);
        h.runAfterDelay(duration,()->{
            f.tick();check(h,WeaponIzanagiPresentation.returning(f.player,f.gun),"Honed return active");
            check(h,WeaponRuntime.beginUse(f.player),"Honed shot is available at the unchanged deadline");
            WeaponRuntime.releaseUse(f.player,f.gun);
            check(h,WeaponIzanagi.charge(f.gun)==0 && !WeaponIzanagiPresentation.returning(f.player,f.gun)
                    && !WeaponIzanagiPresentation.active(f.gun),"One charged shot retires old recovery immediately");h.succeed();
        });
    }
}
