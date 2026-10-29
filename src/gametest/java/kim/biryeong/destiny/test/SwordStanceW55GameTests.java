package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.destiny.weapon.*;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.bone.BoneMovement;
import kr.toxicity.model.api.bone.RenderedBone;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.tracker.TrackerModifier;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.gametest.framework.GameTestSequence;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Real BetterModel clocks/sent transforms and server gameplay, not native-client rendering. */
public final class SwordStanceW55GameTests {
    private static final String FLOOR="destiny-test:floor";
    private static void check(GameTestHelper h,boolean ok,String message) {h.assertTrue(ok,Component.literal(message));}
    private static GameTestSequence loaded(GameTestHelper h) {
        return h.startSequence().thenWaitUntil(()->check(h,BetterModel.limb(SwordPoseW146Assets.MODEL_NAME).isPresent(),"Active raised sword limb loaded"));
    }
    private static ServerPlayer player(GameTestHelper h,double z) {
        var p=TestPlayers.create(h,new Vec3(2.5,1,z),-90,0);p.setOnGround(true);
        p.setItemInHand(InteractionHand.OFF_HAND,new ItemStack(Items.TORCH,7));
        TestCleanup.register(h, ()->{WeaponRuntime.cleanup(p);AbilityService.cleanup(p);PlayerAnimations.stop(p);SuperCamera.stop(p);TestPlayers.remove(p);});
        return p;
    }
    private static ItemStack equip(ServerPlayer p,int rounds) {
        var e=WeaponCatalog.find("abide_the_return").orElseThrow();var stack=WeaponItems.create(e);
        WeaponItems.save(stack,new WeaponMagazine(WeaponProfile.forEntry(e),rounds,0));
        SwordItems.save(stack,SwordCycle.CAPACITY,0);p.setItemInHand(InteractionHand.MAIN_HAND,stack);
        WeaponRuntime.tickPlayer(p);return stack;
    }
    private static int rounds(ItemStack s) {return WeaponItems.magazine(s,WeaponProfile.forEntry(WeaponItems.entry(s).orElseThrow())).rounds();}
    private static void heartbeat(GameTestHelper h,ServerPlayer p) {
        check(h,SuperCamera.move(p,new ServerboundMovePlayerPacket.Rot(p.getYRot(),p.getXRot(),false,false)),"Sword camera accepts server rotation packet");
    }
    private static EntityTracker tracker(ServerPlayer p) {
        return BetterModel.limb(SwordPoseW146Assets.MODEL_NAME).orElseThrow().getOrCreate(ModPlayer.of(p.connection),TrackerModifier.DEFAULT);
    }
    private static BoneMovement sent(RenderedBone bone) {
        try {
            var field=bone.getClass().getDeclaredField("globalState");field.setAccessible(true);var handler=field.get(bone);
            var current=handler.getClass().getDeclaredField("current");current.setAccessible(true);
            return new BoneMovement().set((BoneMovement)current.get(handler));
        } catch(ReflectiveOperationException e) {throw new AssertionError(e);}
    }
    private static boolean changed(BoneMovement a,BoneMovement b) {
        return a.position().distanceSquared(b.position())>1e-8||Math.abs(a.rotation().dot(b.rotation()))<.999999f;
    }
    private static void pose(GameTestHelper h,ServerPlayer p,SwordStance stance) {
        check(h,("h15_"+stance.clip()).equals(PlayerAnimations.swordPose(p)),"Actual underlay selects "+stance);
    }

    @GameTest(structure=FLOOR,maxTicks=160, environment = "destiny-test:w90_isolated")
    public void fourLoopsAdvanceActualFullBodyTransformsOnOneTrackerWithoutGameplayMutation(GameTestHelper h) {
        var p=player(h,6.5);
        loaded(h).thenExecute(()->{
            var stack=equip(p,12);var original=stack.copy();var location=p.position();var velocity=p.getDeltaMovement();
            var t=tracker(p);var clock=(ServerAnimationClock)(Object)t;
            long expected=clock.destiny$serverFrames();
            for(var stance:SwordStance.values()) {
                check(h,PlayerAnimations.swordPose(p,stance),"Loop starts "+stance);
                check(h,tracker(p)==t&&!t.isClosed(),"Stance changes reuse exact live tracker");
                pose(h,p,stance);
                var names=List.of("pri_right_item","pc_chest","pll_left_leg");
                var bones=names.stream().map(name->t.bone(b->b.name().rawName().equals(name))).toList();
                check(h,bones.stream().noneMatch(Objects::isNull),"Skin/equipment full-body bones present");
                var before=bones.stream().map(SwordStanceW55GameTests::sent).toList();var moved=new boolean[3];
                for(int tick=0;tick<24;tick++) {
                    clock.destiny$advanceServerTick();expected+=2;
                    for(int i=0;i<bones.size();i++) {
                        var value=sent(bones.get(i));
                        check(h,value.position().isFinite()&&value.rotation().isFinite()&&value.scale().isFinite(),"Finite sent transform "+stance+"/"+names.get(i));
                        moved[i]|=changed(before.get(i),value);
                    }
                }
                for(int i=0;i<3;i++)check(h,moved[i],"Authored loop changes actual sent body/equipment transform "+stance+"/"+names.get(i));
                check(h,clock.destiny$serverFrames()==expected,"Loop changes preserve monotonic real clock, exactly2frames/tick");
                long frames=clock.destiny$serverFrames();
                check(h,PlayerAnimations.swordPose(p,stance)&&clock.destiny$serverFrames()==frames,"Repeated same pose cannot restart or advance clock");
            }
            check(h,ItemStack.matches(stack,original)&&p.position().equals(location)&&p.getDeltaMovement().equals(velocity)
                    &&p.getOffhandItem().is(Items.TORCH)&&p.getOffhandItem().getCount()==7&&!PlayerAnimations.swordAttacking(p),
                    "Loop sampling changes no ammo/energy/offhand/body/velocity and fabricates no attack");
        }).thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=160, environment = "destiny-test:w90_isolated")
    public void resolvedDisplacementAirAndAuthoritativeGuardChooseLoopsWithoutRestartingTracker(GameTestHelper h) {
        var p=player(h,6.5);EntityTracker[] t={null};ItemStack[] stack={null};
        loaded(h).thenExecute(()->{
            stack[0]=equip(p,12);t[0]=tracker(p);pose(h,p,SwordStance.IDLE);
            // Explicit server fixture displacement, not native movement-input proof.
            p.setPos(p.position().add(.2,0,0));
        }).thenIdle(1).thenExecute(()->{
            pose(h,p,SwordStance.MOVE);
        }).thenIdle(1).thenExecute(()->{
            pose(h,p,SwordStance.IDLE);p.setOnGround(false);
        }).thenIdle(1).thenExecute(()->{
            pose(h,p,SwordStance.AIR);p.setOnGround(true);p.setShiftKeyDown(true);
        }).thenIdle(2).thenExecute(()->{
            heartbeat(h,p);WeaponRuntime.tickPlayer(p);
            check(h,WeaponRuntime.swordStatus(p).orElseThrow().guarding(),"Authoritative energy guard is active");
            pose(h,p,SwordStance.GUARD);p.setShiftKeyDown(false);
        }).thenIdle(1).thenExecute(()->{
            pose(h,p,SwordStance.IDLE);p.setShiftKeyDown(true);
            WeaponItems.save(stack[0],new WeaponMagazine(WeaponProfile.forEntry(WeaponCatalog.find("abide_the_return").orElseThrow()),0,0));
        }).thenIdle(1).thenExecute(()->{
            pose(h,p,SwordStance.IDLE);
            check(h,tracker(p)==t[0]&&!t[0].isClosed()&&rounds(stack[0])==0&&!PlayerAnimations.swordAttacking(p),
                    "Selectors retain exact limb and raw sneak on empty sword cannot invent guard or attack");
        }).thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=180, environment = "destiny-test:w90_isolated")
    public void acceptedSwingMasksStancesThenReturnsToLiveAirLoopOnSameClock(GameTestHelper h) {
        var p=player(h,6.5);EntityTracker[] t={null};long[] frames={0};ItemStack[] stack={null};
        loaded(h).thenExecute(()->{
            stack[0]=equip(p,12);t[0]=tracker(p);InputRouter.onPunch(p);frames[0]=PlayerAnimations.serverFrames(p);
            check(h,PlayerAnimations.swordAttacking(p)&&rounds(stack[0])==11,"Accepted swing pays once and masks base loop");
            p.setOnGround(false);
            check(h,PlayerAnimations.swordPose(p,SwordStance.AIR)&&PlayerAnimations.swordAttacking(p)
                    &&PlayerAnimations.serverFrames(p)==frames[0]&&tracker(p)==t[0],"Stance request cannot cut swing or reset its actual contact clock");
        }).thenExecuteFor(4,()->{
            heartbeat(h,p);WeaponRuntime.tickPlayer(p);
            check(h,PlayerAnimations.swordAttacking(p)&&rounds(stack[0])==11,"Air state does not interrupt or recharge accepted swing");
        }).thenWaitUntil(()->{
            heartbeat(h,p);check(h,!PlayerAnimations.swordAttacking(p),"Waiting for actual one-shot recovery");
        }).thenExecute(()->{
            pose(h,p,SwordStance.AIR);
            check(h,PlayerAnimations.swordPlaying(p)&&!t[0].isClosed()&&tracker(p)==t[0]
                    &&PlayerAnimations.serverFrames(p)>frames[0]&&SuperCamera.swordActive(p)&&rounds(stack[0])==11,
                    "Actual one-shot returns to current air underlay with same limb/clock/camera and no second cost");
        }).thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=180, environment = "destiny-test:w90_isolated")
    public void earlyGuardCancelsPendingHpButRetainsUnderlayThenRaisesBladeWhenEligible(GameTestHelper h) {
        var p=player(h,6.5);ItemStack[] stack={null};EntityTracker[] t={null};
        var enemy=h.spawn(EntityTypes.HUSK,new Vec3(4.5,1,6.5));enemy.setNoAi(true);enemy.setNoGravity(true);
        enemy.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);enemy.getAttribute(Attributes.ARMOR).setBaseValue(0);enemy.setHealth(1000);
        TestCleanup.register(h, enemy::discard);
        loaded(h).thenExecute(()->{stack[0]=equip(p,12);t[0]=tracker(p);InputRouter.onPunch(p);})
                .thenExecuteAfter(1,()->{
                    p.setShiftKeyDown(true);WeaponRuntime.tickPlayer(p);
                    check(h,!PlayerAnimations.swordAttacking(p)&&!t[0].isClosed()&&tracker(p)==t[0],"Guard cancels owned windup only, not persistent limb");
                }).thenExecuteFor(20,()->{
                    heartbeat(h,p);WeaponRuntime.tickPlayer(p);
                    check(h,enemy.getHealth()==1000&&rounds(stack[0])==11,"Cancelled contact never causes stale HP or cost refund");
                }).thenExecute(()->{
                    pose(h,p,SwordStance.GUARD);
                    check(h,WeaponRuntime.swordStatus(p).orElseThrow().guarding()&&tracker(p)==t[0]
                            &&!t[0].isClosed()&&SuperCamera.swordActive(p),"Eligible energy guard raises blade on original limb and rear camera");
                }).thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=160, environment = "destiny-test:w90_isolated")
    public void closedCosmeticIsNotRecreatedUntilRealBindingChange(GameTestHelper h) {
        var p=player(h,6.5);EntityTracker[] original={null};ItemStack[] stack={null};
        loaded(h).thenExecute(()->{
            stack[0]=equip(p,12);original[0]=tracker(p);PlayerAnimations.stopSword(p);
            check(h,original[0].isClosed()&&!PlayerAnimations.swordPlaying(p),"Owned cosmetic explicitly closes");
        }).thenExecuteFor(4,()->{
            heartbeat(h,p);WeaponRuntime.tickPlayer(p);
            check(h,!PlayerAnimations.swordPlaying(p)&&original[0].isClosed()&&rounds(stack[0])==12,"Same binding does not retry failed cosmetic or change ammo");
        }).thenExecute(()->{
            var next=stack[0].copy();p.setItemInHand(InteractionHand.MAIN_HAND,next);WeaponRuntime.tickPlayer(p);
            pose(h,p,SwordStance.IDLE);
            check(h,PlayerAnimations.swordPlaying(p)&&tracker(p)!=original[0]&&rounds(next)==12,
                    "New exact stack binding permits one fresh persistent limb without an ammo refill");
        }).thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=160, environment = "destiny-test:w90_isolated")
    public void ordinarySkillNeverReusesSwordLoopRigAndOtherOwnerKeepsItsStance(GameTestHelper h) {
        var a=player(h,2.5);var b=player(h,9.5);
        loaded(h).thenExecute(()->{
            equip(a,12);equip(b,12);var ta=tracker(a);var tb=tracker(b);
            long frames=PlayerAnimations.serverFrames(b);
            check(h,PlayerAnimations.play(a,"grenade"),"Ordinary skill starts while sword loop was active");
            check(h,ta.isClosed()&&PlayerAnimations.foreignToSword(a)&&!PlayerAnimations.swordPlaying(a),
                    "Skill owns correct Hunter rig instead of attaching to sword underlay or leaving it active");
            check(h,!PlayerAnimations.swordPose(a,SwordStance.GUARD)&&!PlayerAnimations.swordAttack(a,"sword_light_1"),
                    "Neither sword stance nor swing can steal skill ownership");
            SwordPresentation.cleanup(a);
            check(h,PlayerAnimations.foreignToSword(a)&&tracker(b)==tb&&!tb.isClosed()
                    &&PlayerAnimations.serverFrames(b)==frames&&SuperCamera.swordActive(b),"Sword-only cleanup preserves foreign skill and other owner's exact clock/camera/limb");
            pose(h,b,SwordStance.IDLE);
        }).thenSucceed();
    }
}
