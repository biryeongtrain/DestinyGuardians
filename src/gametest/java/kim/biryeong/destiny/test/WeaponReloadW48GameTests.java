package kim.biryeong.destiny.test;

import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/** Server integration, not evidence of native client input or framebuffer rendering. */
public final class WeaponReloadW48GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static WeaponProfile profile() { return WeaponProfile.forEntry(WeaponCatalog.find("long_arm").orElseThrow()); }
    private static ServerPlayer player(GameTestHelper h, int rounds) {
        var p=TestPlayers.create(h,new Vec3(2.5,1,6.5),-90,0);
        var e=WeaponCatalog.find("long_arm").orElseThrow();
        var stack=WeaponItems.create(e);
        WeaponItems.save(stack,new WeaponMagazine(profile(),rounds,0));
        p.setItemInHand(InteractionHand.MAIN_HAND,stack);
        TestCleanup.register(h, ()->{WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        return p;
    }
    private static int rounds(ItemStack stack) { return WeaponItems.magazine(stack,profile()).rounds(); }
    private static void ticks(GameTestHelper h,ServerPlayer p,int duration) {
        for(int i=1;i<=duration;i++) h.runAfterDelay(i,()->WeaponRuntime.tickPlayer(p));
    }

    @GameTest(structure="destiny-test:floor",maxTicks=90, environment = "destiny-test:w90_isolated")
    public void twoRoundInsertsUseSeparateInitialAndRepeatHudPhasesAndSwapPreservesSavedAmmo(GameTestHelper h) {
        var p=player(h,0);var stack=p.getMainHandItem();var f=profile();
        check(h,f.shellReload()&&f.roundsPerInsert()==2&&f.firstReloadTicks()==20&&f.reloadTicks()==13,
                "Reference-informed Long Arm policy, not whole-magazine scout curve");
        check(h,WeaponRuntime.reload(p),"Starts empty reload");
        var initial=AmmoHud.current(p).orElseThrow();
        check(h,initial.rounds()==0&&initial.reloadDuration()==20&&initial.reloadRemaining()==20,"HUD owns first insert deadline");
        ticks(h,p,21);
        h.runAfterDelay(19,()->check(h,rounds(stack)==0,"No early predicted ammunition"));
        h.runAfterDelay(21,()->{
            var hud=AmmoHud.current(p).orElseThrow();
            check(h,rounds(stack)==2&&hud.rounds()==2&&hud.reserve()==0&&hud.infiniteReserve(),"Two real primary rounds, no fake finite reserve");
            check(h,hud.reloadDuration()==13&&hud.reloadRemaining()>0&&hud.reloadRemaining()<=13,"HUD uses current repeat phase, not initial or full-mag duration");
            var before=stack.copy();CombatHud.update(p);CombatHud.update(p);
            check(h,ItemStack.matches(before,stack),"Repeated HUD projections do not mutate saved ammo");
            p.setItemInHand(InteractionHand.MAIN_HAND,ItemStack.EMPTY);WeaponRuntime.tickPlayer(p);
            p.setItemInHand(InteractionHand.MAIN_HAND,stack);
        });
        h.runAfterDelay(65,()->{
            WeaponRuntime.tickPlayer(p);
            check(h,rounds(stack)==2&&!WeaponRuntime.reloading(p),"Swap cancels all future inserts without refilling saved stack");
            h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=70, environment = "destiny-test:w90_isolated")
    public void lastOddRoundStopsAtOfficialCapacityAndSerializesWithoutExtraInsert(GameTestHelper h) {
        var f=profile();var p=player(h,f.magazine()-1);var stack=p.getMainHandItem();
        check(h,WeaponRuntime.reload(p),"Reloads one missing round");ticks(h,p,55);
        h.runAfterDelay(21,()->{
            check(h,rounds(stack)==f.magazine()&&!WeaponRuntime.reloading(p),"Final two-round insert truncates to one missing slot");
            check(h,AmmoHud.current(p).orElseThrow().rounds()==f.magazine(),"HUD never exceeds official capacity");
        });
        h.runAfterDelay(56,()->{
            var copy=stack.copy();check(h,rounds(copy)==f.magazine()&&!WeaponRuntime.reloading(p),"Copied saved stack stays full, no later grant");
            h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=80, environment = "destiny-test:w90_isolated")
    public void heldEmptyHeartbeatCannotFireInsertedPairButNewPressInterruptsExactlyOnce(GameTestHelper h) {
        var p=player(h,0);var stack=p.getMainHandItem();WeaponRuntime.heartbeatUse(p);
        for(int i=1;i<=21;i++) {
            int tick=i;h.runAfterDelay(i,()->{
                if(tick%4==0)WeaponRuntime.heartbeatUse(p);
                WeaponRuntime.tickPlayer(p);
            });
        }
        h.runAfterDelay(21,()->check(h,rounds(stack)==2&&WeaponRuntime.reloading(p),"Held trigger cannot spend newly inserted pair"));
        h.runAfterDelay(28,()->{
            check(h,WeaponRuntime.heartbeatUse(p),"Fresh press after lease gap interrupts incremental reload");
            for(int duplicate=0;duplicate<20;duplicate++)WeaponRuntime.heartbeatUse(p);
            check(h,rounds(stack)==1&&!WeaponRuntime.reloading(p),"Only one shot, no duplicate refill or cadence bypass");
        });
        h.runAfterDelay(60,()->{
            WeaponRuntime.tickPlayer(p);check(h,rounds(stack)==1,"Cancelled future pair never arrives");h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=80, environment = "destiny-test:w90_isolated")
    public void skillCancellationStopsRepeatPhaseWithoutDiscardingFirstPair(GameTestHelper h) {
        var p=player(h,0);var stack=p.getMainHandItem();check(h,WeaponRuntime.reload(p),"Starts reload");ticks(h,p,60);
        h.runAfterDelay(21,()->{
            check(h,rounds(stack)==2,"Only first pair arrived");WeaponRuntime.cancelUseForSkill(p);
            check(h,!WeaponRuntime.reloading(p),"Skill cancels current insert deadline");
        });
        h.runAfterDelay(61,()->{
            check(h,rounds(stack)==2&&AmmoHud.current(p).orElseThrow().reloadRemaining()==0,"Skill leaves stored pair and clears HUD progress");
            h.succeed();
        });
    }
}
