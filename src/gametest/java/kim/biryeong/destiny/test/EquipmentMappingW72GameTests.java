package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.fx.HunterModelAssets;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.fx.SuperVisuals;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.tracker.TrackerModifier;
import kr.toxicity.model.api.tracker.TrackerUpdateAction;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Display;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

/** Actual BM equipment refreshes, not a comparison against the requested Playback field.
 * Synchronous public mapping refresh is a deterministic reproduction of the overwrite path;
 * it does not pretend to replay the unrecorded W71 scheduler interleaving.
 */
public final class EquipmentMappingW72GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static Object field(Object receiver, String name) {
        try { var f=receiver.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(receiver); }
        catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }
    private static Display.ItemDisplay hand(EntityTracker t, boolean left) {
        var b=t.bone(v->v.name().rawName().equals(left?"pli_left_item":"pri_right_item"));
        return (Display.ItemDisplay)field(b.getDisplay(),"display");
    }
    private static void item(GameTestHelper h, Display.ItemDisplay display, ItemStack expected, String message) {
        var actual=display.getItemStack();
        check(h, ItemStack.isSameItem(actual,expected) && actual.getCount()==expected.getCount()
                && java.util.Objects.equals(actual.get(DataComponents.ITEM_MODEL),expected.get(DataComponents.ITEM_MODEL))
                && java.util.Objects.equals(actual.get(DataComponents.CUSTOM_NAME),expected.get(DataComponents.CUSTOM_NAME)),
                message+": actual="+actual+" model="+actual.get(DataComponents.ITEM_MODEL));
    }
    private static void loaded(GameTestHelper h, Runnable action) {
        h.startSequence().thenWaitUntil(()->check(h, BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(),"Hunter model loaded"))
                .thenExecute(()->{action.run();h.succeed();});
    }
    private static net.minecraft.server.level.ServerPlayer player(GameTestHelper h, Element e) {
        var p=TestPlayers.hunter(h,e,new Vec3(3.5,1,3.5),0,0);
        TestCleanup.register(h, ()->TestPlayers.remove(p));
        p.setOnGround(true);
        p.setItemInHand(InteractionHand.MAIN_HAND,new ItemStack(Items.STICK,2));
        p.getMainHandItem().set(DataComponents.CUSTOM_NAME,Component.literal("Real main hand"));
        p.setItemInHand(InteractionHand.OFF_HAND,new ItemStack(Items.DIAMOND,3));
        return p;
    }
    private static EntityTracker tracker(net.minecraft.server.level.ServerPlayer p) {
        return BetterModel.limb(HunterModelAssets.MODEL_NAME).orElseThrow().getOrCreate(ModPlayer.of(p.connection),TrackerModifier.DEFAULT);
    }
    @GameTest(structure="destiny-test:floor",maxTicks=1200, environment = "destiny-test:w90_isolated")
    public void realVoidActivationSurvivesRepeatedDependencyEquipmentRefresh(GameTestHelper h) {
        loaded(h,()->{
            var p=player(h,Element.VOID);var main=p.getMainHandItem().copy();var off=p.getOffhandItem().copy();
            Guardians.data(p).setSuperEnergy(1);
            check(h,AbilityService.use(p,AbilitySlot.SUPER)==AbilityService.Result.OK,"Actual Void activation");
            var t=tracker(p);
            for(int i=0;i<32;i++) {
                t.update(TrackerUpdateAction.itemMapping());
                item(h,hand(t,true),SuperVisuals.drawnBow(),"Actual mapped left remains drawn after dependency refresh "+i);
                item(h,hand(t,false),ItemStack.EMPTY,"Actual draw hand remains empty "+i);
            }
            check(h,ItemStack.matches(main,p.getMainHandItem())&&ItemStack.matches(off,p.getOffhandItem()),"No real inventory edit");
            AbilityService.endSuper(p);
            item(h,hand(t,true),p.getOffhandItem(),"End restores live left");
            item(h,hand(t,false),p.getMainHandItem(),"End restores live right");
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=1200, environment = "destiny-test:w90_isolated")
    public void rightPropPreservesLiveLeftAndExplicitHandSwitchRestoresIt(GameTestHelper h) {
        loaded(h,()->{
            var p=player(h,Element.ARC);
            check(h,PlayerAnimations.loop(p,"super_arc"),"Actual Arc loop");var t=tracker(p);
            PlayerAnimations.superItem(p,SuperVisuals.item(Element.ARC));
            p.setItemInHand(InteractionHand.OFF_HAND,new ItemStack(Items.EMERALD,5));
            t.update(TrackerUpdateAction.itemMapping());
            item(h,hand(t,false),SuperVisuals.item(Element.ARC),"Right staff survives mapping");
            item(h,hand(t,true),p.getOffhandItem(),"Non-overridden left stays live");
            PlayerAnimations.superItem(p,SuperVisuals.drawnBow(),true);
            item(h,hand(t,false),ItemStack.EMPTY,"Bow empties right");
            PlayerAnimations.superItem(p,SuperVisuals.item(Element.SOLAR));
            item(h,hand(t,true),p.getOffhandItem(),"Switch back from left prop restores live left immediately");
            t.update(TrackerUpdateAction.itemMapping());
            item(h,hand(t,false),SuperVisuals.item(Element.SOLAR),"New right prop survives mapping");
            PlayerAnimations.stop(p);
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=1200, environment = "destiny-test:w90_isolated")
    public void emptyPropAndStopRestoreCurrentInventoryRatherThanCapturedStacks(GameTestHelper h) {
        loaded(h,()->{
            var p=player(h,Element.VOID);check(h,PlayerAnimations.loop(p,"super_void"),"Actual Void loop");var t=tracker(p);
            var prop=SuperVisuals.drawnBow();PlayerAnimations.superItem(p,prop,true);
            prop.setCount(7);prop.set(DataComponents.CUSTOM_NAME,Component.literal("Changed caller copy"));
            t.update(TrackerUpdateAction.itemMapping());
            item(h,hand(t,true),SuperVisuals.drawnBow(),"Visual prop snapshots input, not caller mutable stack");
            p.setItemInHand(InteractionHand.MAIN_HAND,new ItemStack(Items.GOLD_INGOT,4));
            p.setItemInHand(InteractionHand.OFF_HAND,new ItemStack(Items.AMETHYST_SHARD,6));
            PlayerAnimations.superItem(p,ItemStack.EMPTY);
            t.update(TrackerUpdateAction.itemMapping());
            item(h,hand(t,true),p.getOffhandItem(),"EMPTY restores current offhand");
            item(h,hand(t,false),p.getMainHandItem(),"EMPTY restores current mainhand");
            PlayerAnimations.superItem(p,SuperVisuals.releasedBow(),true);
            PlayerAnimations.stop(p);
            check(h,t.isClosed(),"Stop closes actual tracker");
            item(h,hand(t,true),p.getOffhandItem(),"Stop restores live left");
            item(h,hand(t,false),p.getMainHandItem(),"Stop restores live right");
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=1200, environment = "destiny-test:w90_isolated")
    public void foreignTrackerRetainsDefaultMappingAndStoppedOverrideCannotAffectReplacement(GameTestHelper h) {
        loaded(h,()->{
            var p=player(h,Element.ARC);var foreign=tracker(p);
            foreign.update(TrackerUpdateAction.itemMapping());
            item(h,hand(foreign,true),p.getOffhandItem(),"Unowned left maps normally");
            item(h,hand(foreign,false),p.getMainHandItem(),"Unowned right maps normally");
            foreign.close();
            check(h,PlayerAnimations.loop(p,"super_void"),"Owned first tracker");var first=tracker(p);
            PlayerAnimations.superItem(p,SuperVisuals.drawnBow(),true);PlayerAnimations.stop(p);
            check(h,PlayerAnimations.loop(p,"super_arc"),"Owned replacement tracker");var second=tracker(p);
            check(h,first!=second,"Actual distinct replacement");PlayerAnimations.superItem(p,SuperVisuals.item(Element.ARC));
            first.update(TrackerUpdateAction.itemMapping());second.update(TrackerUpdateAction.itemMapping());
            item(h,hand(second,false),SuperVisuals.item(Element.ARC),"Old tracker refresh cannot affect current staff");
            item(h,hand(second,true),p.getOffhandItem(),"Replacement non-overridden hand stays live");
            PlayerAnimations.stop(p);
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=1200, environment = "destiny-test:w90_isolated")
    public void mapperEvaluatedBeforeOverrideCannotCommitItsStaleHandAfterPublication(GameTestHelper h) {
        loaded(h,()->{
            var p=player(h,Element.VOID);check(h,PlayerAnimations.loop(p,"super_void"),"Actual Void loop");var t=tracker(p);
            var bone=t.bone(b->b.name().rawName().equals("pli_left_item"));
            var original=bone.getItemMapper();
            var evaluated=new java.util.concurrent.CountDownLatch(1);
            var release=new java.util.concurrent.CountDownLatch(1);
            var error=new java.util.concurrent.atomic.AtomicReference<Throwable>();
            var producer=new java.util.concurrent.atomic.AtomicReference<Thread>();
            var stale=new java.util.concurrent.atomic.AtomicReference<kr.toxicity.model.api.util.TransformedItemStack>();
            bone.setItemMapper(new kr.toxicity.model.api.bone.BoneItemMapper() {
                @Override public kr.toxicity.model.api.platform.PlatformItemTransform transform() {return original.transform();}
                @Override public kr.toxicity.model.api.util.TransformedItemStack apply(
                        kr.toxicity.model.api.bone.BoneRenderContext context,
                        kr.toxicity.model.api.util.TransformedItemStack previous) {
                    var value=original.apply(context,previous);
                    if(Thread.currentThread()==producer.get()) {
                        stale.set(value);evaluated.countDown();
                        try { if(!release.await(3,java.util.concurrent.TimeUnit.SECONDS)) throw new AssertionError("Release latch timeout"); }
                        catch(InterruptedException e) {Thread.currentThread().interrupt();throw new AssertionError(e);}
                    }
                    return value;
                }
            });
            Thread worker=new Thread(()->{
                try {bone.updateItem(b->true);} catch(Throwable e) {error.set(e);}
            },"w72-inflight-equipment");
            worker.setDaemon(true);producer.set(worker);
            try {
                worker.start();
                try {check(h,evaluated.await(2,java.util.concurrent.TimeUnit.SECONDS),"Real mapper evaluated before new override");}
                catch(InterruptedException e) {Thread.currentThread().interrupt();throw new AssertionError(e);}
                check(h,stale.get()!=null,"Producer has an actual mapped value, not a synthetic result");
                PlayerAnimations.superItem(p,SuperVisuals.drawnBow(),true);
                release.countDown();
                try {worker.join(2000);} catch(InterruptedException e) {Thread.currentThread().interrupt();throw new AssertionError(e);}
                check(h,!worker.isAlive()&&error.get()==null,"In-flight real update completed without error: "+error.get());
                item(h,hand(t,true),SuperVisuals.drawnBow(),"A value evaluated before publication is rejected at native commit");
                PlayerAnimations.superItem(p,ItemStack.EMPTY);
                bone.itemStack(b->true,kr.toxicity.model.api.util.TransformedItemStack.of(
                        kr.toxicity.model.api.mod.platform.ModItemStack.of(SuperVisuals.drawnBow())));
                item(h,hand(t,true),p.getOffhandItem(),"Delayed stale prop cannot resurrect after clear");
                check(h,bone.getItemMapper().transform()==original.transform(),"Original native handed transform preserved");
            } finally {
                release.countDown();
                try {worker.join(2000);} catch(InterruptedException e) {Thread.currentThread().interrupt();}
                bone.setItemMapper(original);PlayerAnimations.stop(p);
            }
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=1200, environment = "destiny-test:w90_isolated")
    public void preexistingForeignLimbIsNotSilentlyAdoptedOrClosed(GameTestHelper h) {
        loaded(h,()->{
            var p=player(h,Element.ARC);var foreign=tracker(p);
            TestCleanup.register(h, foreign::close);
            check(h,!PlayerAnimations.loop(p,"super_arc"),"Do not adopt an existing foreign same-model tracker without binding ownership");
            check(h,!foreign.isClosed()&&!PlayerAnimations.isPlaying(p),"Foreign tracker remains open and not registered as ours");
            PlayerAnimations.superItem(p,SuperVisuals.item(Element.ARC));
            PlayerAnimations.stop(p);foreign.update(TrackerUpdateAction.itemMapping());
            item(h,hand(foreign,true),p.getOffhandItem(),"Foreign left stays live");
            item(h,hand(foreign,false),p.getMainHandItem(),"Foreign right stays live");
        });
    }

}
