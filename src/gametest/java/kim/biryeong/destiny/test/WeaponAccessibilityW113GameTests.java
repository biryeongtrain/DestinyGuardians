package kim.biryeong.destiny.test;

import com.mojang.brigadier.exceptions.CommandSyntaxException;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;
import java.util.UUID;

/** Real command/runtime/inventory clocks, not native-input or rendered-game evidence. */
public final class WeaponAccessibilityW113GameTests {
    private static final String FLOOR="destiny-test:w109_arena", ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean ok,String why) { h.assertTrue(ok,Component.literal(why)); }
    private static final class Fixture {
        final GameTestHelper h; final ServerPlayer p; final ItemStack gun; final WeaponProfile profile;
        boolean renew=true;
        Fixture(GameTestHelper h,String id,Boolean auto,boolean nativeGrip) {
            this.h=h;
            p=TestPlayers.create(h,new Vec3(24,1,24),0,-85,"W113_"+UUID.randomUUID().toString().substring(0,8));
            p.setNoGravity(true);p.setOnGround(true);
            gun=WeaponModels.withGrip(WeaponItems.create(WeaponCatalog.find(id).orElseThrow()),
                    nativeGrip?WeaponModels.Grip.NATIVE:WeaponModels.Grip.TWO_HAND).orElseThrow();
            p.setItemInHand(InteractionHand.MAIN_HAND,gun);
            profile=WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());
            // Initial attachment value is fixture setup, not an input setting change.
            if (auto != null) WeaponAccessibility.setEnabled(p,auto);
            WeaponRuntime.tickPlayer(p);
            TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);TestPlayers.remove(p);});
            h.onEachTick(()->{
                if(renew&&WeaponModels.twoHanded(gun))WeaponRuntime.heartbeatUse(p);
                WeaponRuntime.tickPlayer(p);
                if(!WeaponModels.twoHanded(gun)&&p.isUsingItem())WeaponRuntime.continueUse(p);
                TestPlayers.drain(p);
            });
        }
        void press() {
            boolean accepted=WeaponModels.twoHanded(gun)?WeaponRuntime.heartbeatUse(p):WeaponRuntime.beginUse(p);
            check(h,accepted,"Real owned trigger accepted");
            if(!WeaponModels.twoHanded(gun))p.startUsingItem(InteractionHand.MAIN_HAND);
        }
        int rounds() { return WeaponItems.magazine(gun,profile).rounds(); }
        void neutral() { renew=false;WeaponRuntime.releaseUse(p,gun);p.stopUsingItem(); }
    }
    private static int execute(ServerPlayer p,String cmd) {
        try { return p.level().getServer().getCommands().getDispatcher().execute(cmd,p.createCommandSourceStack()); }
        catch(CommandSyntaxException e) { throw new AssertionError(e); }
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=20)
    public void ordinaryPlayerCanOnlyChangeOwnSettingAndStatusDoesNotBindCombat(GameTestHelper h) {
        var p=TestPlayers.create(h,new Vec3(1,1,1),0,-85);
        var other=TestPlayers.create(h,new Vec3(2,1,1),0,-85);
        TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);TestPlayers.remove(p);TestPlayers.remove(other);});
        check(h,WeaponAccessibility.enabled(p)&&WeaponAccessibility.enabled(other),"Hold-to-fire defaults on independently");
        check(h,execute(p,"destiny settings full_auto off")==1&&!WeaponAccessibility.enabled(p)
                &&WeaponAccessibility.enabled(other),"Explicit opt-out changes self only");
        var before=p.getMainHandItem().copy();
        for(int i=0;i<5;i++)check(h,execute(p,"destiny settings full_auto")==1,"NonOP read status");
        check(h,ItemStack.matches(before,p.getMainHandItem())&&WeaponHandling.presentation(p).isEmpty()
                &&!WeaponRuntime.reloading(p),"Status has no inventory/runtime side effects");
        check(h,execute(p,"destiny settings full_auto on")==1&&WeaponAccessibility.enabled(p)
                &&WeaponAccessibility.enabled(other),"Self-only preference, no OP requirement");
        boolean rejected=false;
        try { p.level().getServer().getCommands().getDispatcher().execute("destiny settings full_auto off @a",p.createCommandSourceStack()); }
        catch(CommandSyntaxException expected) { rejected=true; }
        check(h,rejected&&WeaponAccessibility.enabled(p),"No target overload or trailing-argument mutation");
        check(h,execute(p,"destiny settings full_auto off")==1&&!WeaponAccessibility.enabled(p),"Disable self");h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=50)
    public void offKeepsSemiAutomaticWhileOnRepeatsAtOriginalCadenceInBothCarriers(GameTestHelper h) {
        var off=new Fixture(h,"austringer",false,false);
        var auto=new Fixture(h,"austringer",true,false);
        var nativeAuto=new Fixture(h,"austringer",true,true);
        int capacity=auto.rounds();off.press();auto.press();nativeAuto.press();
        h.runAfterDelay(24,()->{
            check(h,off.rounds()==capacity-1,"Explicit opt-out remains one real trigger");
            int expected=1+(int)Math.floor(24/auto.profile.cadenceTicks()+1e-7);
            check(h,auto.rounds()==capacity-expected&&nativeAuto.rounds()==capacity-expected,
                    "Both carriers repeat without rate or cost changes");
            auto.neutral();nativeAuto.neutral();off.neutral();int remaining=auto.rounds();
            h.runAfterDelay(10,()->{check(h,auto.rounds()==remaining&&nativeAuto.rounds()==remaining,"Release stops repetitions");h.succeed();});
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=45)
    public void duplicatePacketsCannotMultiplyEnabledShotsAndExpiredLeaseStopsThem(GameTestHelper h) {
        var f=new Fixture(h,"austringer",true,false);int before=f.rounds();f.press();
        for(int i=0;i<30;i++)WeaponRuntime.heartbeatUse(f.p);
        check(h,f.rounds()==before-1,"Same-tick duplicates pay once");f.renew=false;
        h.runAfterDelay(25,()->{check(h,f.rounds()==before-1,"No fresh heartbeat after six ticks cannot reach next nine-tick shot");h.succeed();});
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=50)
    public void repeatedPulseTriggersKeepOriginalWithinBurstSpacingAndPerRoundCost(GameTestHelper h) {
        var f=new Fixture(h,"blast_furnace",null,false);int before=f.rounds();
        long tick=f.p.level().getServer().getTickCount();f.press();
        var reference=new WeaponCycle();var rounds=new WeaponMagazine(f.profile,before,0);
        check(h,reference.fire(tick,f.profile,rounds),"Reference original unmodified pulse cycle accepts first trigger");
        for(int i=1;i<=32;i++){int elapsed=i;h.runAfterDelay(i,()->{
            // GameTest delayed callbacks have no ordering guarantee relative to
            // onEachTick. Process this actual server tick before comparing its
            // bolts; duplicate same-tick processing must itself remain harmless.
            WeaponRuntime.tickPlayer(f.p);
            long current=tick+elapsed;
            for(int n=0;n<f.profile.burst();n++)if(!reference.burst(current,rounds))break;
            reference.fire(current,f.profile,rounds);
            check(h,f.rounds()==rounds.rounds(),"Every actual tick matches original burst cadence/ammo, actual="+f.rounds()
                    +" expected="+rounds.rounds()+" elapsed="+elapsed+" actualClock="+(f.p.level().getServer().getTickCount()-tick));
            if(elapsed==32){f.neutral();h.succeed();}
        });}
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=100)
    public void fullAutoFusionChargesAgainInsteadOfSkippingSecondChargeOrPayingPerBolt(GameTestHelper h) {
        var f=new Fixture(h,"stormchaser",true,false);int before=f.rounds();f.press();
        long started=f.p.level().getServer().getTickCount();
        int charge=f.profile.chargeTicks();int nextChargeAt=charge+(int)Math.ceil(f.profile.cadenceTicks());
        h.runAfterDelay(charge+1,()->check(h,f.rounds()==before-1,"First complete charge pays one shared cartridge"));
        h.runAfterDelay(nextChargeAt+2,()->{
            var state=WeaponRuntime.chargeState(f.p);
            check(h,state.phase()==WeaponChargeState.Phase.CHARGING&&state.progress()>0&&state.progress()<1,
                    "Second charge is real and incomplete after previous burst/cadence");
            check(h,f.rounds()==before-1,"Recharging is not a paid shot");
        });
        h.runAfterDelay(nextChargeAt+charge+1,()->{
            check(h,f.p.level().getServer().getTickCount()-started>=nextChargeAt+charge
                    &&f.rounds()==before-2,"Second discharge pays once only after fresh full charge");f.neutral();h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=45)
    public void changingPreferenceRetiresUnpaidChargeButKeepsPaidBurstAndCosts(GameTestHelper h) {
        var unpaid=new Fixture(h,"stormchaser",true,false);int a=unpaid.rounds();unpaid.press();
        h.runAfterDelay(2,()->{check(h,WeaponAccessibility.setEnabled(unpaid.p,false),"Actual setting changed");unpaid.renew=false;
            check(h,WeaponRuntime.chargeState(unpaid.p).phase()==WeaponChargeState.Phase.IDLE&&unpaid.rounds()==a,"Unpaid charge canceled without ammo");});
        var paid=new Fixture(h,"stormchaser",true,false);int b=paid.rounds();paid.press();
        h.runAfterDelay(paid.profile.chargeTicks()+1,()->{
            check(h,WeaponRuntime.chargeState(paid.p).phase()==WeaponChargeState.Phase.BURSTING,"Paid remaining bolts before setting change");
            WeaponAccessibility.setEnabled(paid.p,false);paid.renew=false;
            check(h,WeaponRuntime.chargeState(paid.p).phase()==WeaponChargeState.Phase.BURSTING&&paid.rounds()==b-1,
                    "Preference change is not refund, new shot or paid-burst cancellation");
        });
        h.runAfterDelay(35,()->{check(h,paid.rounds()==b-1&&unpaid.rounds()==a
                &&WeaponRuntime.chargeState(paid.p).phase()==WeaponChargeState.Phase.IDLE,"Only paid burst drains then idle");h.succeed();});
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=85)
    public void enabledInputCannotQueueAShotThroughManualReload(GameTestHelper h) {
        var f=new Fixture(h,"austringer",true,false);
        WeaponItems.save(f.gun,new WeaponMagazine(f.profile,3,0));f.press();
        check(h,WeaponRuntime.reload(f.p),"Actual manual primary reload starts");
        h.runAfterDelay(f.profile.reloadTicks()+12,()->{
            check(h,!WeaponRuntime.reloading(f.p)&&f.rounds()==f.profile.magazine(),
                    "Held heartbeat during manual reload never queues late shot");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=100)
    public void shotCausedReloadCanContinueEnabledNativeInputButMustRechargeAfterwards(GameTestHelper h) {
        var f=new Fixture(h,"stormchaser",true,true);
        WeaponItems.save(f.gun,new WeaponMagazine(f.profile,1,2));f.press();
        int reloadEnd=f.profile.chargeTicks()+(int)Math.ceil((f.profile.burst()-1)*f.profile.burstSpacingTicks())+f.profile.reloadTicks();
        h.runAfterDelay(reloadEnd+3,()->{
            var state=WeaponRuntime.chargeState(f.p);
            check(h,f.rounds()==2&&state.phase()==WeaponChargeState.Phase.CHARGING&&state.progress()<1,
                    "Real post-empty reload transfers reserve then a new charge begins, never free discharge");f.neutral();h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=45)
    public void noOpSettingKeepsInputButRealToggleRequiresFreshTwoHandPress(GameTestHelper h) {
        var f=new Fixture(h,"austringer",true,false);int before=f.rounds();f.press();
        check(h,!WeaponAccessibility.setEnabled(f.p,true),"Same value is not an input action");
        h.runAfterDelay(11,()->{
            check(h,f.rounds()==before-2,"No-op setting did not interrupt live input");
            WeaponAccessibility.setEnabled(f.p,false);WeaponAccessibility.setEnabled(f.p,true);
        });
        h.runAfterDelay(24,()->{check(h,f.rounds()==before-2,"Continuous heartbeat across real toggles cannot forge fresh press");
            f.renew=false;
            h.runAfterDelay(8,()->{f.press();check(h,f.rounds()==before-3,"Fresh gap permits exactly one legitimate trigger");f.neutral();h.succeed();});
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=35)
    public void sameTickStowAndSpectatorCannotCarryEnabledPendingInput(GameTestHelper h) {
        var f=new Fixture(h,"stormchaser",true,false);int before=f.rounds();f.press();
        WeaponRuntime.inventoryStowing(f.p,f.gun);f.renew=false;
        h.runAfterDelay(20,()->{
            check(h,f.rounds()==before,"Exact object stowed and returned cannot carry charge");
            f.p.setGameMode(GameType.SPECTATOR);
            check(h,!WeaponRuntime.heartbeatUse(f.p)&&WeaponRuntime.chargeState(f.p).phase()==WeaponChargeState.Phase.IDLE,
                    "Enabled preference does not override spectator eligibility");h.succeed();
        });
    }
}
