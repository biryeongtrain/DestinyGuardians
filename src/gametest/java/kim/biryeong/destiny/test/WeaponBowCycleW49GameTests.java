package kim.biryeong.destiny.test;

import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/** Real server item/use/reload routing; not native client or visual-animation evidence. */
public final class WeaponBowCycleW49GameTests {
    private record Bow(ServerPlayer player,ItemStack stack,WeaponProfile profile) {}
    private static void check(GameTestHelper h,boolean ok,String message) { h.assertTrue(ok,Component.literal(message)); }
    private static Bow bow(GameTestHelper h,String id) {
        var p=TestPlayers.create(h,new Vec3(2.5,1,6.5),-90,-15);
        var e=WeaponCatalog.find(id).orElseThrow();var f=WeaponProfile.forEntry(e);
        var stack=WeaponItems.create(e);p.setItemInHand(InteractionHand.MAIN_HAND,stack);
        TestCleanup.register(h, ()->{WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        return new Bow(p,stack,f);
    }
    private static int rounds(Bow b) { return WeaponItems.magazine(b.stack,b.profile).rounds(); }
    private static void use(GameTestHelper h,Bow b) { WeaponCombatItem.INSTANCE.use(h.getLevel(),b.player,InteractionHand.MAIN_HAND); }
    private static void ticks(GameTestHelper h,Bow b,int until) {
        for(int i=1;i<=until;i++)h.runAfterDelay(i,()->{WeaponRuntime.tickPlayer(b.player);TestPlayers.drain(b.player);});
    }
    private static void shootAndNock(GameTestHelper h,Bow b) {
        b.player.releaseUsingItem();
        check(h,rounds(b)==0,"Released charged arrow actually spends its loaded unit");
        WeaponRuntime.tickPlayer(b.player);
        check(h,WeaponRuntime.reloading(b.player),"Shot itself starts nocking without another press");
    }

    @GameTest(structure="destiny-test:floor",maxTicks=110, environment = "destiny-test:w90_isolated")
    public void everySelectedBowAutomaticallyNocksAndHudTracksRealDeadlineWithoutInput(GameTestHelper h) {
        var bows=WeaponCatalog.all().stream().filter(e->e.family().equals("bow"))
                .map(e->bow(h,e.id())).toList();
        check(h,!bows.isEmpty(),"Selected bow catalog is nonempty");
        for(var b:bows){
            check(h,b.stack.get(DataComponents.LORE).lines().stream().anyMatch(x->x.getString().contains("시위 풀기")),
                    "New live bow help describes the real Q let-down route");
            use(h,b);ticks(h,b,85);
        }
        h.runAfterDelay(20,()->{
            for(var b:bows) {
                shootAndNock(h,b);
                var hud=AmmoHud.current(b.player).orElseThrow();
                check(h,hud.rounds()==0&&hud.reloadDuration()==b.profile.firstReloadTicks()
                        &&hud.reloadRemaining()==b.profile.firstReloadTicks(),"HUD starts actual nock phase, not draw time");
                var before=b.stack.copy();CombatHud.update(b.player);CombatHud.update(b.player);
                check(h,ItemStack.matches(before,b.stack),"HUD reads cannot grant a loaded arrow");
            }
        });
        for(var b:bows) {
            h.runAfterDelay(20+b.profile.firstReloadTicks()-1,
                    ()->check(h,rounds(b)==0,"No early arrow before nock deadline"));
            h.runAfterDelay(20+b.profile.firstReloadTicks()+1,()->{
                check(h,rounds(b)==1&&!WeaponRuntime.reloading(b.player),"Nock completes without any new press");
                check(h,!b.player.isUsingItem()&&AmmoHud.current(b.player).orElseThrow().reloadRemaining()==0,
                        "No automatic draw/fire queued by the released input");
            });
        }
        h.runAfterDelay(86,()->{
            for(var b:bows)check(h,rounds(b)==1,"Loaded arrow remains idle without input");h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=110, environment = "destiny-test:w90_isolated")
    public void heldNextPressDuringNockBuffersDrawButNeverAutomaticallyReleasesArrow(GameTestHelper h) {
        var b=bow(h,"biting_winds");int r=20,n=b.profile.firstReloadTicks(),d=b.profile.chargeTicks();
        use(h,b);ticks(h,b,90);
        h.runAfterDelay(r,()->shootAndNock(h,b));
        h.runAfterDelay(r+1,()->{
            use(h,b);check(h,b.player.isUsingItem(),"Real new press buffers next draw during nock");
        });
        h.runAfterDelay(r+n-1,()->check(h,rounds(b)==0,"Holding next draw cannot accelerate nock"));
        h.runAfterDelay(r+n+d+2,()->{
            check(h,rounds(b)==1&&!WeaponRuntime.reloading(b.player),"Even a fully drawn bow never auto-releases");
            shootAndNock(h,b);check(h,rounds(b)==0,"Release of buffered full draw fires the next real arrow");
        });
        h.runAfterDelay(r+2*n+d+4,()->{
            check(h,rounds(b)==1&&!b.player.isUsingItem(),"Second shot also nocks without another click");h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=90, environment = "destiny-test:w90_isolated")
    public void bufferedNockTimeCannotCountAsDrawTimeAndEarlyReleaseStillFiresPartialArrow(GameTestHelper h) {
        var b=bow(h,"biting_winds");int r=20,n=b.profile.firstReloadTicks();use(h,b);ticks(h,b,70);
        h.runAfterDelay(r,()->shootAndNock(h,b));
        h.runAfterDelay(r+1,()->use(h,b));
        h.runAfterDelay(r+n+1,()->{
            check(h,rounds(b)==1,"Nock completed");b.player.releaseUsingItem();
            check(h,rounds(b)==0,"Early release fires a partial arrow instead of silently dropping the input");
            WeaponRuntime.tickPlayer(b.player);
            check(h,WeaponRuntime.reloading(b.player),"Partial release also starts automatic nock");
        });
        h.runAfterDelay(71,()->{
            check(h,rounds(b)==1&&!b.player.isUsingItem(),"Partial release nocks once and leaves no delayed shot");h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=80, environment = "destiny-test:w90_isolated")
    public void bufferedPartialArrowProducesLessRealTargetDamageThanFullDraw(GameTestHelper h) {
        var b=bow(h,"biting_winds");b.player.setXRot(0);
        var target=h.spawn(EntityTypes.HUSK,new Vec3(4.5,1.8,6.5));
        target.setNoAi(true);target.setNoGravity(true);
        target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
        target.getAttribute(Attributes.ARMOR).setBaseValue(0);
        target.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        target.setHealth(1000);TestCleanup.register(h, target::discard);
        int n=b.profile.firstReloadTicks();float[] full={0},beforePartial={0};
        use(h,b);ticks(h,b,65);
        h.runAfterDelay(20,()->shootAndNock(h,b));
        h.runAfterDelay(21,()->use(h,b));
        h.runAfterDelay(25,()->{
            full[0]=1000-target.getHealth();check(h,full[0]>0,"Full draw projectile made a real body hit");
        });
        h.runAfterDelay(20+n+1,()->{
            beforePartial[0]=target.getHealth();b.player.releaseUsingItem();
            check(h,rounds(b)==0,"One-tick buffered draw fires partial projectile after real nock");
        });
        h.runAfterDelay(20+n+10,()->{
            float partial=beforePartial[0]-target.getHealth();
            check(h,partial>0&&partial<full[0]*.8f,"Nock time is not inherited as full charge: actual partial impact is weaker");
            h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=70, environment = "destiny-test:w90_isolated")
    public void reloadPacketLetsFullyDrawnBowDownWithoutFiringOrRefilling(GameTestHelper h) {
        var b=bow(h,"biting_winds");use(h,b);ticks(h,b,45);
        h.runAfterDelay(20,()->{
            check(h,InputRouter.onPlayerAction(b.player,ServerboundPlayerActionPacket.Action.DROP_ITEM),"Q packet consumed by live weapon route");
            check(h,rounds(b)==1&&!WeaponRuntime.reloading(b.player)&&!b.player.isUsingItem(),"Q cancels draw, not ammunition or nock");
            b.player.releaseUsingItem();WeaponRuntime.releaseUse(b.player,b.stack);
            check(h,WeaponRuntime.activeProjectiles(b.player)==0,"Stale release after let-down fires nothing");
        });
        h.runAfterDelay(46,()->{check(h,rounds(b)==1,"No delayed ammo change");h.succeed();});
    }

    @GameTest(structure="destiny-test:floor",maxTicks=90, environment = "destiny-test:w90_isolated")
    public void reloadPacketDisarmsBufferedDrawWithoutCancellingRealNockTransfer(GameTestHelper h) {
        var b=bow(h,"biting_winds");int n=b.profile.firstReloadTicks();use(h,b);ticks(h,b,70);
        h.runAfterDelay(20,()->shootAndNock(h,b));
        h.runAfterDelay(21,()->use(h,b));
        h.runAfterDelay(22,()->{
            check(h,WeaponRuntime.reload(b.player),"Reload command lets buffered draw down");
            check(h,!b.player.isUsingItem()&&WeaponRuntime.reloading(b.player),"Existing nock deadline continues but held draw is cancelled");
        });
        h.runAfterDelay(20+n+2,()->check(h,rounds(b)==1&&!b.player.isUsingItem(),"Arrow arrives without armed draw"));
        h.runAfterDelay(71,()->{check(h,rounds(b)==1,"No automatic release after disarming");h.succeed();});
    }

    @GameTest(structure="destiny-test:floor",maxTicks=90, environment = "destiny-test:w90_isolated")
    public void skillCancellationStopsNockAndPendingShotUntilActualReloadRequest(GameTestHelper h) {
        var b=bow(h,"biting_winds");int n=b.profile.firstReloadTicks();use(h,b);ticks(h,b,75);
        h.runAfterDelay(20,()->{
            shootAndNock(h,b);WeaponRuntime.cancelUseForSkill(b.player);
            check(h,!WeaponRuntime.reloading(b.player),"Skill cancels owned nock session");
        });
        h.runAfterDelay(20+n+2,()->{
            check(h,rounds(b)==0&&!WeaponRuntime.reloading(b.player),"Cancelled candidate cannot silently restart or grant arrow");
            check(h,WeaponRuntime.reload(b.player),"Actual next reload request restarts preparation");
        });
        h.runAfterDelay(20+2*n+4,()->{
            check(h,rounds(b)==1&&!b.player.isUsingItem(),"Explicit restart completes without ghost draw");h.succeed();
        });
    }
}
