package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.fx.SwordPoseW146Assets;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.destiny.weapon.*;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.gametest.framework.GameTestSequence;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Real server tick/HP/packet-handler tests. No wall-clock delay, native client or framebuffer proof. */
public final class SwordContactW54GameTests {
    private static final String FLOOR="destiny-test:floor";
    private static final float HP=1000;
    private static final double EPS=1e-6;
    private static void check(GameTestHelper h,boolean ok,String text) { h.assertTrue(ok,Component.literal(text)); }
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static GameTestSequence loaded(GameTestHelper h) {
        return h.startSequence().thenWaitUntil(()->check(h,BetterModel.limb(SwordPoseW146Assets.MODEL_NAME).isPresent(),"Sword limb loaded"));
    }
    private static ServerPlayer player(GameTestHelper h,double z,boolean hunter) {
        var p=hunter?TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,z),-90,0)
                :TestPlayers.create(h,new Vec3(2.5,1,z),-90,0);
        p.setOnGround(true);
        var level=p.level();
        TestCleanup.register(h, ()->{
            WeaponRuntime.cleanup(p);AbilityService.cleanup(p);CombatHud.remove(p);
            p.setServerLevel(level);foreignCamera(p,p);TestPlayers.remove(p);
        });
        return p;
    }
    private static ItemStack equip(ServerPlayer p,String id,int rounds) {
        var entry=WeaponCatalog.find(id).orElseThrow();var stack=WeaponItems.create(entry);
        WeaponItems.save(stack,new WeaponMagazine(WeaponProfile.forEntry(entry),rounds,0));
        SwordItems.save(stack,SwordCycle.CAPACITY,0);
        p.setItemInHand(InteractionHand.MAIN_HAND,stack);WeaponRuntime.tickPlayer(p);return stack;
    }
    private static int rounds(ItemStack stack) {
        return WeaponItems.magazine(stack,WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow())).rounds();
    }
    private static Husk target(GameTestHelper h,double x,double z) {
        var e=h.spawn(EntityTypes.HUSK,new Vec3(x,1,z));e.setNoAi(true);e.setNoGravity(true);e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HP);e.getAttribute(Attributes.ARMOR).setBaseValue(0);
        e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);e.setHealth(HP);
        TestCleanup.register(h, e::discard);return e;
    }
    private static void use(GameTestHelper h,ServerPlayer p) {
        p.gameMode.useItem(p,h.getLevel(),p.getMainHandItem(),InteractionHand.MAIN_HAND);
    }
    /** Embedded-player camera occupancy injection only; native setCamera requires chunk registration. */
    private static void foreignCamera(ServerPlayer p,Entity camera) {
        try {var f=ServerPlayer.class.getDeclaredField("camera");f.setAccessible(true);f.set(p,camera);}
        catch(ReflectiveOperationException e) {throw new AssertionError(e);}
    }

    @GameTest(structure=FLOOR,maxTicks=800, environment = "destiny-test:w90_isolated")
    public void lightAndFiveHeavyFormsCommitCostThenContactExactlyOnceAtAuthoredCue(GameTestHelper h) {
        var p=player(h,6.5,false);var enemy=target(h,4.5,6.5);
        var sequence=loaded(h);
        var ids=List.of("abide_the_return","abide_the_return","goldtusk","crown_splitter","falling_guillotine","temptation_s_hook");
        for(int index=0;index<ids.size();index++) {
            String id=ids.get(index);boolean heavy=index>0;
            ItemStack[] stack={null};long[] started={0},frames={0};int[] paid={0};Vec3[] body={null};
            boolean[] observed={false,false};float[] finalHp={HP};
            var profile=SwordProfile.of(WeaponCatalog.find(id).orElseThrow());
            int delay=SwordTiming.contactTicks(profile.shape(),heavy,1);
            sequence.thenExecute(()->{
                p.setPos(h.absoluteVec(new Vec3(2.5,1,6.5)));p.setYRot(-90);p.setXRot(0);
                enemy.setPos(h.absoluteVec(new Vec3(4.5,1,6.5)));enemy.setHealth(HP);enemy.damageCooldownTime=0;
                stack[0]=equip(p,id,20);started[0]=now(p);body[0]=p.position();
                if(heavy)use(h,p);else InputRouter.onPunch(p);
                paid[0]=rounds(stack[0]);
                check(h,paid[0]==20-(heavy?profile.heavyCost():1),id+": acceptance pays exactly once");
                check(h,enemy.getHealth()==HP&&p.position().distanceToSqr(body[0])<EPS&&WeaponRuntime.activeProjectiles(p)==0,
                        id+": no HP, dash/lunge or projectile on acceptance");
                check(h,PlayerAnimations.swordAttacking(p),id+": real limb one-shot starts before gameplay contact");
                frames[0]=PlayerAnimations.serverFrames(p);
                if(heavy)use(h,p);else {InputRouter.onPunch(p);WeaponRuntime.onPunch(p);}
                check(h,rounds(stack[0])==paid[0],id+": duplicate input cannot pay/restart");
            }).thenExecuteFor(16,()->{
                long elapsed=now(p)-started[0];
                WeaponRuntime.tickPlayer(p);
                if(elapsed<delay) {
                    observed[0]=true;
                    check(h,enemy.getHealth()==HP&&p.position().distanceToSqr(body[0])<EPS&&WeaponRuntime.activeProjectiles(p)==0,
                            id+": windup remains effect-free at tick "+elapsed+"/"+delay);
                }
                if(elapsed==delay) {
                    observed[1]=true;
                    long advanced=PlayerAnimations.serverFrames(p)-frames[0];
                    System.out.println("W54 contact "+id+" heavy="+heavy+" tick="+elapsed+" actualBMFrames="+advanced);
                    check(h,PlayerAnimations.swordAttacking(p)&&advanced>=delay*2L,
                            id+": real animation clock has reached the contact deadline before HP/release");
                    if(profile.shape()==SwordProfile.Shape.CASTER&&heavy)
                        check(h,WeaponRuntime.activeProjectiles(p)==1&&enemy.getHealth()==HP,"Caster releases at cue; travel still precedes HP");
                    else check(h,enemy.getHealth()<HP,id+": real HP changes at the exact cue tick");
                    float once=enemy.getHealth();int projectiles=WeaponRuntime.activeProjectiles(p);
                    WeaponRuntime.tickPlayer(p);WeaponRuntime.tickPlayer(p);
                    check(h,enemy.getHealth()==once&&WeaponRuntime.activeProjectiles(p)==projectiles,
                            id+": repeated same-tick processing cannot repeat a contact");
                }
                check(h,rounds(stack[0])==paid[0],id+": contact/late ticks never charge additional ammo");
                if(elapsed>delay+4) {
                    if(finalHp[0]==HP)finalHp[0]=enemy.getHealth();
                    check(h,enemy.getHealth()==finalHp[0],id+": no repeated late HP transaction");
                }
            }).thenExecute(()->check(h,observed[0]&&observed[1]&&enemy.getHealth()<HP,id+": observed actual windup, exact cue and final HP"))
                    .thenIdle(35);
        }
        sequence.thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=240, environment = "destiny-test:w90_isolated")
    public void secondAndThirdComboUseTheirOwnLaterCueAndPreserveFinisherDamage(GameTestHelper h) {
        var p=player(h,6.5,false);var enemy=target(h,4.5,6.5);ItemStack[] stack={null};
        var sequence=loaded(h).thenExecute(()->stack[0]=equip(p,"abide_the_return",12));
        float[] damage=new float[3];
        for(int i=0;i<3;i++) {
            int combo=i+1,delay=SwordTiming.contactTicks(SwordProfile.Shape.UPPERCUT,false,combo);
            long[] started={0};boolean[] due={false};
            sequence.thenExecute(()->{
                enemy.setHealth(HP);enemy.damageCooldownTime=0;started[0]=now(p);InputRouter.onPunch(p);
                check(h,WeaponRuntime.swordStatus(p).orElseThrow().combo()==combo&&rounds(stack[0])==12-combo,"Accepted three-step combo/cost");
            }).thenExecuteFor(7,()->{
                long elapsed=now(p)-started[0];WeaponRuntime.tickPlayer(p);
                if(elapsed<delay)check(h,enemy.getHealth()==HP,"Combo "+combo+" has no early damage");
                if(elapsed==delay) {due[0]=true;damage[combo-1]=HP-enemy.getHealth();check(h,damage[combo-1]>0,"Combo exact contact");}
            }).thenExecute(()->check(h,due[0],"Exact combo contact was observed")).thenIdle(8);
        }
        sequence.thenExecute(()->check(h,Math.abs(damage[0]-damage[1])<.001&&damage[2]>damage[1],"Third-hit damage multiplier remains real HP, not presentation telemetry"))
                .thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=180, environment = "destiny-test:w90_isolated")
    public void cancellationMatrixCannotDeliverStaleDamageOrRefundAcceptedCosts(GameTestHelper h) {
        var names=List.of("swap","skill","cleanup","guard","spectator","death","dimension","foreign","teleport","abilityCleanup");
        var players=new ArrayList<ServerPlayer>();var stacks=new ArrayList<ItemStack>();
        var trackers=new ArrayList<kr.toxicity.model.api.tracker.EntityTracker>();
        var enemy=target(h,4.5,6.5);long[] started={0};
        for(int i=0;i<names.size();i++)players.add(player(h,6.5,false));
        loaded(h).thenExecute(()->{
            started[0]=now(players.getFirst());
            for(var p:players) {
                stacks.add(equip(p,"crown_splitter",20));use(h,p);
                var tracker=BetterModel.limb(SwordPoseW146Assets.MODEL_NAME).orElseThrow().getOrCreate(
                        kr.toxicity.model.api.mod.platform.ModPlayer.of(p.connection),
                        kr.toxicity.model.api.tracker.TrackerModifier.DEFAULT);
                check(h,PlayerAnimations.swordAttacking(p)&&!tracker.isClosed(),"Cancellation fixture owns a live attack tracker");
                trackers.add(tracker);
            }
            check(h,enemy.getHealth()==HP,"All cancellation cases start before contact");
        }).thenExecuteAfter(1,()->{
            players.get(0).setItemInHand(InteractionHand.MAIN_HAND,new ItemStack(Items.STONE));
            WeaponRuntime.cancelUseForSkill(players.get(1));
            WeaponRuntime.cleanup(players.get(2));
            players.get(3).setShiftKeyDown(true);
            players.get(4).setGameMode(GameType.SPECTATOR);
            var dead=players.get(5);dead.hurtServer(h.getLevel(),dead.damageSources().genericKill(),10000);
            var moved=players.get(6);
            for(var level:h.getLevel().getServer().getAllLevels())if(level!=h.getLevel()) {moved.setServerLevel(level);break;}
            var marker=new net.minecraft.world.entity.Display.ItemDisplay(EntityTypes.ITEM_DISPLAY,h.getLevel());
            foreignCamera(players.get(7),marker);
            players.get(8).setPos(players.get(8).position().add(9,0,0));
            AbilityService.cleanup(players.get(9)); // Also used by class/subclass-change commands.
            // These explicit cancellations close the original run before an eligible held sword can rebind.
            for(int i:List.of(1,2,9))check(h,trackers.get(i).isClosed()&&!PlayerAnimations.swordPlaying(players.get(i)),
                    names.get(i)+": cancellation immediately closes the exact original tracker");
            for(int i=0;i<players.size();i++) {
                var p=players.get(i);WeaponRuntime.tickPlayer(p);
                check(h,!PlayerAnimations.swordAttacking(p),names.get(i)+": cancellation stops the accepted one-shot");
                if(!names.get(i).equals("guard")&&!names.get(i).equals("teleport"))
                    check(h,trackers.get(i).isClosed(),names.get(i)+": invalidation closes the exact original tracker even if eligibility starts a new loop");
            }
        }).thenExecuteFor(14,()->{
            for(var p:players)WeaponRuntime.tickPlayer(p);
            check(h,enemy.getHealth()==HP,"No cancelled windup can resolve late HP");
            for(int i=0;i<players.size();i++)check(h,rounds(stacks.get(i))==16&&WeaponRuntime.activeProjectiles(players.get(i))==0,
                    names.get(i)+": accepted cost remains spent without stale projectile/refund");
        }).thenExecute(()->{
            check(h,now(players.getFirst())-started[0]>SwordTiming.contactTicks(SwordProfile.Shape.SLAM,true,0),"Actually waited past all deadlines");
            for(int i=0;i<players.size();i++) {
                var p=players.get(i);
                check(h,!PlayerAnimations.swordAttacking(p),names.get(i)+": cancelled windup has no one-shot");
                if(names.get(i).equals("guard"))
                    check(h,!trackers.get(i).isClosed()&&PlayerAnimations.swordPlaying(p)
                                    &&!WeaponRuntime.swordStatus(p).orElseThrow().guarding()
                                    &&SwordItems.energy(stacks.get(i))==0&&"h15_sword_idle".equals(PlayerAnimations.swordPose(p)),
                            "Sneak cancels only the attack and retains idle: committed heavy spent all energy, so no guard may be fabricated");
                else if(Set.of("skill","cleanup","abilityCleanup","dimension").contains(names.get(i)))
                    check(h,trackers.get(i).isClosed()&&(!PlayerAnimations.swordPlaying(p)
                                    ||"h15_sword_idle".equals(PlayerAnimations.swordPose(p))),
                            names.get(i)+": original attack tracker stays closed; eligible rebinding may own a fresh idle underlay");
                else check(h,trackers.get(i).isClosed()&&!PlayerAnimations.swordPlaying(p),
                        names.get(i)+": invalid owner, foreign camera or teleport watchdog closes the full owned sword playback");
            }
        }).thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=100, environment = "destiny-test:w90_isolated")
    public void contactReacquiresCurrentAimTargetsAndNewBlockingWalls(GameTestHelper h) {
        var turn=player(h,1.5,false);var blocked=player(h,6.5,false);var moved=player(h,11.5,false);
        var old=target(h,4.5,1.5);var behind=target(h,.5,1.5);var wallTarget=target(h,4.5,6.5);var entrant=target(h,11.5,11.5);
        loaded(h).thenExecute(()->{
            for(var p:List.of(turn,blocked,moved)) {equip(p,"abide_the_return",12);InputRouter.onPunch(p);}
        }).thenExecuteAfter(1,()->{
            turn.setYRot(90);turn.setYHeadRot(90);
            h.setBlock(3,1,6,Blocks.STONE);h.setBlock(3,2,6,Blocks.STONE);
            entrant.setPos(h.absoluteVec(new Vec3(4.5,1,11.5)));
        }).thenExecuteAfter(5,()->{
            for(var p:List.of(turn,blocked,moved))WeaponRuntime.tickPlayer(p);
            check(h,old.getHealth()==HP&&behind.getHealth()<HP,"Contact uses current yaw, not a captured old target/cone");
            check(h,wallTarget.getHealth()==HP,"A collider added during windup blocks actual contact HP");
            check(h,entrant.getHealth()<HP,"A newly arrived legal target can be hit at contact");
        }).thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=100, environment = "destiny-test:w90_isolated")
    public void actualHotbarAndOffhandRoundTripsCancelEvenWithinOneServerTick(GameTestHelper h) {
        var hotbar=player(h,2.5,false);var offhand=player(h,9.5,false);
        var a=target(h,4.5,2.5);var b=target(h,4.5,9.5);ItemStack[] stacks=new ItemStack[2];
        loaded(h).thenExecute(()->{
            stacks[0]=equip(hotbar,"abide_the_return",12);stacks[1]=equip(offhand,"abide_the_return",12);
            hotbar.getInventory().setItem(1,new ItemStack(Items.DIAMOND,2));
            offhand.setItemInHand(InteractionHand.OFF_HAND,new ItemStack(Items.TORCH,7));
            InputRouter.onPunch(hotbar);InputRouter.onPunch(offhand);
            hotbar.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));
            hotbar.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(0));
            for(int i=0;i<2;i++)offhand.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                    ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND,BlockPos.ZERO,Direction.UP));
            check(h,hotbar.getMainHandItem()==stacks[0]&&offhand.getMainHandItem()==stacks[1]
                    &&offhand.getOffhandItem().is(Items.TORCH)&&offhand.getOffhandItem().getCount()==7,
                    "Both real native handlers return the exact items in the same tick");
        }).thenExecuteAfter(8,()->{
            WeaponRuntime.tickPlayer(hotbar);WeaponRuntime.tickPlayer(offhand);
            check(h,a.getHealth()==HP&&b.getHealth()==HP&&rounds(stacks[0])==11&&rounds(stacks[1])==11,
                    "Unobserved-by-polling round trips cannot resurrect the old accepted contact/refund");
        }).thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=100, environment = "destiny-test:w90_isolated")
    public void redundantAndInvalidHotbarPacketsDoNotCancelAValidContact(GameTestHelper h) {
        var p=player(h,6.5,false);var enemy=target(h,4.5,6.5);ItemStack[] stack={null};
        loaded(h).thenExecute(()->{
            stack[0]=equip(p,"abide_the_return",12);InputRouter.onPunch(p);
            p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(0));
            p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(-1));
            p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(9));
            check(h,enemy.getHealth()==HP&&p.getMainHandItem()==stack[0],"No slot mutation from invalid/same-slot packets");
        }).thenExecuteAfter(6,()->{
            WeaponRuntime.tickPlayer(p);
            check(h,enemy.getHealth()<HP&&rounds(stack[0])==11,"Validated native slot hook does not spuriously veto real contact");
        }).thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=120, environment = "destiny-test:w90_isolated")
    public void actualSolarHandoffCancelsPendingSwordAndForeignRollRejectsNewCost(GameTestHelper h) {
        var solar=player(h,2.5,true);var roll=player(h,9.5,true);
        var a=target(h,4.5,2.5);var b=target(h,4.5,9.5);ItemStack[] stacks=new ItemStack[2];
        loaded(h).thenExecute(()->{
            stacks[0]=equip(solar,"crown_splitter",20);stacks[1]=equip(roll,"abide_the_return",12);
            use(h,solar);Guardians.data(solar).setSuperEnergy(1);
            check(h,AbilityService.use(solar,AbilitySlot.SUPER)==AbilityService.Result.OK,"Real Solar ability accepted");
            check(h,PlayerAnimations.play(roll,"h15_roll_forward"),"Real ordinary foreign limb starts");
            InputRouter.onPunch(roll);
            check(h,rounds(stacks[0])==16&&rounds(stacks[1])==12,"Solar preserves committed cost; foreign roll rejects new sword payment");
        }).thenExecuteAfter(12,()->{
            WeaponRuntime.tickPlayer(solar);WeaponRuntime.tickPlayer(roll);
            check(h,a.getHealth()==HP&&b.getHealth()==HP,"No stale sword HP during actual skill/super handoff");
            check(h,AbilityService.inSuper(solar)&&!SuperCamera.active(solar),"Solar retains first-person super ownership");
        }).thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=120, environment = "destiny-test:w90_isolated")
    public void acceptanceAfterAnimationTickCannotDamageBeforeTheActualClockReachesCue(GameTestHelper h) {
        var p=player(h,6.5,false);var enemy=target(h,4.5,6.5);
        boolean[] flags={false,false,false,false};long[] started={0},frames={0};ItemStack[] stack={null};
        TestCleanup.register(h, ()->flags[0]=false);
        // Test-only late-phase caller: register AFTER runtime and animation listeners.
        // Listener is inert except for its one armed call and never asserts outside GameTest.
        ServerTickEvents.END_SERVER_TICK.register(server->{
            if(!flags[0]||server!=p.level().getServer())return;
            flags[0]=false;
            InputRouter.onPunch(p);started[0]=now(p);frames[0]=PlayerAnimations.serverFrames(p);flags[1]=true;
        });
        int delay=SwordTiming.contactTicks(SwordProfile.Shape.UPPERCUT,false,1);
        loaded(h).thenExecute(()->{stack[0]=equip(p,"abide_the_return",12);flags[0]=true;})
                .thenWaitUntil(()->check(h,flags[1],"Late-phase attack actually accepted"))
                .thenExecuteFor(9,()->{
                    long elapsed=now(p)-started[0],actual=PlayerAnimations.serverFrames(p)-frames[0];
                    WeaponRuntime.tickPlayer(p);
                    if(elapsed<delay||actual<delay*2L) {
                        if(elapsed>=delay)flags[2]=true;
                        check(h,enemy.getHealth()==HP,"Time alone cannot trigger HP while actual model is before its cue: elapsed="+elapsed+" BM="+actual);
                    } else {
                        flags[3]=true;check(h,enemy.getHealth()<HP,"Actual clock crossing releases accepted contact");
                    }
                    check(h,rounds(stack[0])==11,"Clock phase cannot cause extra ammo payment");
                }).thenExecute(()->check(h,flags[2]&&flags[3],"Observed the real late-phase gap and subsequent contact, not an unexecuted branch"))
                .thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=100, environment = "destiny-test:w90_isolated")
    public void closedCosmeticCannotEraseAcceptedTimedGameplayOrCauseAnImmediateHit(GameTestHelper h) {
        var p=player(h,6.5,false);var enemy=target(h,4.5,6.5);ItemStack[] stack={null};long[] started={0};
        boolean[] phases={false,false};
        int delay=SwordTiming.contactTicks(SwordProfile.Shape.UPPERCUT,false,1);
        loaded(h).thenExecute(()->{
            stack[0]=equip(p,"abide_the_return",12);started[0]=now(p);InputRouter.onPunch(p);
            check(h,PlayerAnimations.swordAttacking(p),"Accepted fallback fixture initially has a real one-shot");
            // Cosmetic-only failure injection, NOT a skill/inventory/lifecycle cancellation.
            PlayerAnimations.stopSword(p);
            check(h,!PlayerAnimations.swordPlaying(p)&&enemy.getHealth()==HP,"Closing cosmetic alone cannot cause early damage");
        }).thenExecuteFor(8,()->{
            long elapsed=now(p)-started[0];WeaponRuntime.tickPlayer(p);
            if(elapsed<delay) {phases[0]=true;check(h,enemy.getHealth()==HP,"Closed visual still respects authored windup");}
            if(elapsed==delay) {phases[1]=true;check(h,enemy.getHealth()<HP,"Timed contact survives cosmetic-only failure");}
            check(h,rounds(stack[0])==11&&!PlayerAnimations.swordPlaying(p),"Fallback neither refunds nor restarts failed cosmetics");
        }).thenExecute(()->check(h,phases[0]&&phases[1],"Both actual fallback phases were observed"))
                .thenSucceed();
    }
}
