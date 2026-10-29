package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.fx.SwordPoseW146Assets;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.destiny.sound.DestinySounds;
import kim.biryeong.destiny.weapon.*;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.gametest.framework.GameTestSequence;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Actual queued inline sound packets and server contact state, not native input/decoding/acoustic proof. */
public final class SwordAudioW56GameTests {
    private static final String FLOOR="destiny-test:floor";
    private static void check(GameTestHelper h,boolean ok,String msg) {h.assertTrue(ok,Component.literal(msg));}
    private static long now(ServerPlayer p) {return p.level().getServer().getTickCount();}
    private static GameTestSequence loaded(GameTestHelper h) {
        return h.startSequence().thenWaitUntil(()->check(h,BetterModel.limb(SwordPoseW146Assets.MODEL_NAME).isPresent(),"Sword limb loaded"));
    }
    private static ServerPlayer owner(GameTestHelper h,double z) {
        var p=TestPlayers.create(h,new Vec3(2.5,1,z),-90,0);p.setOnGround(true);
        TestCleanup.register(h, ()->{WeaponRuntime.cleanup(p);AbilityService.cleanup(p);SuperCamera.stop(p);PlayerAnimations.stop(p);foreign(p,p);TestPlayers.remove(p);});
        return p;
    }
    private static ServerPlayer listener(GameTestHelper h,double z) {
        var p=TestPlayers.create(h,new Vec3(2.5,1,z),-90,0);h.getLevel().addNewPlayer(p);
        TestCleanup.register(h, ()->{h.getLevel().removePlayerImmediately(p,Entity.RemovalReason.DISCARDED);TestPlayers.remove(p);});return p;
    }
    private static ItemStack equip(ServerPlayer p,String id,int rounds) {
        var e=WeaponCatalog.find(id).orElseThrow();var stack=WeaponItems.create(e);
        WeaponItems.save(stack,new WeaponMagazine(WeaponProfile.forEntry(e),rounds,0));SwordItems.save(stack,SwordCycle.CAPACITY,0);
        p.setItemInHand(InteractionHand.MAIN_HAND,stack);WeaponRuntime.tickPlayer(p);return stack;
    }
    private static int rounds(ItemStack s) {return WeaponItems.magazine(s,WeaponProfile.forEntry(WeaponItems.entry(s).orElseThrow())).rounds();}
    private static void use(GameTestHelper h,ServerPlayer p) {p.gameMode.useItem(p,h.getLevel(),p.getMainHandItem(),InteractionHand.MAIN_HAND);}
    private static void heartbeat(ServerPlayer p) {SuperCamera.move(p,new ServerboundMovePlayerPacket.Rot(p.getYRot(),p.getXRot(),false,false));}
    private static boolean isSword(String path) {
        return path.startsWith("weapon.sword.")||path.startsWith("weapon.falling_guillotine.")
                ||path.startsWith("weapon.crown_splitter.")||path.startsWith("weapon.temptation_s_hook.");
    }
    private static List<ClientboundSoundPacket> sounds(ServerPlayer listener) {
        return TestPlayers.outbound(listener).stream().filter(ClientboundSoundPacket.class::isInstance).map(ClientboundSoundPacket.class::cast)
                .filter(p->p.getSound().value().location().getNamespace().equals("destiny")&&isSword(p.getSound().value().location().getPath())).toList();
    }
    private static ClientboundSoundPacket at(ServerPlayer p,String key) {return DestinySounds.packet(key,p.getEyePosition(),SoundSource.PLAYERS,.8f,0);}
    private static boolean sameOrigin(ClientboundSoundPacket p,ClientboundSoundPacket ref) {
        return p.getX()==ref.getX()&&p.getY()==ref.getY()&&p.getZ()==ref.getZ();
    }
    private static long count(List<ClientboundSoundPacket> list,ClientboundSoundPacket ref) {
        return list.stream().filter(p->sameOrigin(p,ref)&&p.getSound().value().location().equals(ref.getSound().value().location())).count();
    }
    private static void foreign(ServerPlayer p,Entity entity) {
        try {var f=ServerPlayer.class.getDeclaredField("camera");f.setAccessible(true);f.set(p,entity);}
        catch(ReflectiveOperationException e) {throw new AssertionError(e);}
    }
    private record Case(String id,boolean heavy,boolean empty,boolean ground,String key) { }

    @GameTest(structure=FLOOR,maxTicks=1000, environment = "destiny-test:w90_isolated")
    public void selectedActionsAreSilentAtAcceptanceThenQueueOnceAtActualContactWithNoDuplicatePayment(GameTestHelper h) {
        var p=owner(h,6.5);var ear=listener(h,4.5);var sequence=loaded(h);
        var cases=List.of(
                new Case("falling_guillotine",false,false,true,"weapon.falling_guillotine.light"),
                new Case("falling_guillotine",true,false,true,"weapon.falling_guillotine.heavy"),
                new Case("crown_splitter",false,false,true,"weapon.crown_splitter.light"),
                new Case("crown_splitter",true,false,true,"weapon.crown_splitter.heavy"),
                new Case("crown_splitter",true,false,false,"weapon.crown_splitter.heavy_air"),
                new Case("temptation_s_hook",false,false,true,"weapon.temptation_s_hook.light"),
                new Case("temptation_s_hook",false,true,true,"weapon.temptation_s_hook.empty_light"),
                new Case("temptation_s_hook",true,false,true,"weapon.sword.caster.release"),
                new Case("abide_the_return",false,false,true,"weapon.sword.light"),
                new Case("abide_the_return",true,false,true,"weapon.sword.uppercut"),
                new Case("goldtusk",true,false,true,"weapon.sword.fire"));
        for(var c:cases) {
            long[] started={0},frames={0};int[] received={0},paid={0};boolean[] due={false};ItemStack[] stack={null};ClientboundSoundPacket[] origin={null};
            var shape=SwordProfile.of(WeaponCatalog.find(c.id()).orElseThrow()).shape();int delay=SwordTiming.contactTicks(shape,c.heavy(),1);
            sequence.thenExecute(()->{
                p.setShiftKeyDown(false);p.setPos(h.absoluteVec(new Vec3(2.5,1,6.5)));p.setOnGround(c.ground());
                stack[0]=equip(p,c.id(),c.empty()?0:20);origin[0]=at(p,c.key());sounds(ear);started[0]=now(p);
                if(c.heavy())use(h,p);else InputRouter.onPunch(p);
                frames[0]=PlayerAnimations.serverFrames(p);paid[0]=rounds(stack[0]);
                check(h,PlayerAnimations.swordAttacking(p),"Accepted real swing "+c);
                check(h,sounds(ear).stream().noneMatch(x->sameOrigin(x,origin[0])),"No old fire or action sound at acceptance "+c);
                if(c.id().equals("crown_splitter")&&c.heavy())p.setOnGround(!c.ground()); // Selection uses accepted ground snapshot.
                if(c.heavy())use(h,p);else InputRouter.onPunch(p);
                check(h,rounds(stack[0])==paid[0],"Rejected duplicate cannot pay twice "+c);
            }).thenExecuteFor(delay+4,()->{
                heartbeat(p);WeaponRuntime.tickPlayer(p);
                long elapsed=now(p)-started[0],actual=PlayerAnimations.serverFrames(p)-frames[0];
                var events=sounds(ear).stream().filter(x->sameOrigin(x,origin[0])).toList();
                for(var x:events) {
                    check(h,x.getSound().value().location().getPath().equals(c.key()),"Correct action instead of generic/double-layer swing "+c);
                    check(h,elapsed>=delay&&actual>=delay*2L,"Actual cue/clock precedes sound dispatch "+c);
                    check(h,x.getSource()==SoundSource.PLAYERS&&x.getPitch()==1&&x.getVolume()==.8f,"Native inline positional packet contract");received[0]++;
                }
                if(elapsed>=delay&&actual>=delay*2L)due[0]=true;
                check(h,received[0]<=1&&rounds(stack[0])==paid[0],"One action per accepted contact, no audio-induced extra payment "+c);
            }).thenExecute(()->check(h,due[0]&&received[0]==1,"Observed exactly one actual cue sound "+c)).thenIdle(32);
        }
        sequence.thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=180, environment = "destiny-test:w90_isolated")
    public void swappedSkilledGuardedAndForeignCancelledWindupsHaveNoLateActionPackets(GameTestHelper h) {
        var ear=listener(h,4.5);var owners=new ArrayList<ServerPlayer>();var stacks=new ArrayList<ItemStack>();var origins=new ArrayList<ClientboundSoundPacket>();
        for(int i=0;i<4;i++)owners.add(owner(h,6.5));
        loaded(h).thenExecute(()->{
            for(var p:owners) {stacks.add(equip(p,"crown_splitter",20));origins.add(at(p,"weapon.crown_splitter.heavy"));use(h,p);}
            check(h,sounds(ear).stream().noneMatch(x->origins.stream().anyMatch(ref->sameOrigin(x,ref))),"All four accepted windups initially silent");
        }).thenExecuteAfter(1,()->{
            owners.get(0).setItemInHand(InteractionHand.MAIN_HAND,new ItemStack(Items.STONE));
            WeaponRuntime.cancelUseForSkill(owners.get(1));owners.get(2).setShiftKeyDown(true);
            foreign(owners.get(3),new net.minecraft.world.entity.Display.ItemDisplay(EntityTypes.ITEM_DISPLAY,h.getLevel()));
            for(var p:owners)WeaponRuntime.tickPlayer(p);
        }).thenExecuteFor(14,()->{
            for(var p:owners) {heartbeat(p);WeaponRuntime.tickPlayer(p);}
            check(h,sounds(ear).stream().noneMatch(x->x.getSound().value().location().getPath().equals("weapon.crown_splitter.heavy")
                    &&origins.stream().anyMatch(ref->sameOrigin(x,ref))),"Cancelled pending action cannot leak a late swing packet");
            for(int i=0;i<4;i++)check(h,rounds(stacks.get(i))==16&&WeaponRuntime.activeProjectiles(owners.get(i))==0,"Audio cancellation never refunds or creates gameplay");
        }).thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=180, environment = "destiny-test:w90_isolated")
    public void guardOneShotUsesOnlyRealRisingEdgesAndCannotSpamPerTickOrRapidToggle(GameTestHelper h) {
        var p=owner(h,6.5);var ear=listener(h,4.5);ClientboundSoundPacket[] ref={null};int[] count={0};
        loaded(h).thenExecute(()->{equip(p,"falling_guillotine",12);ref[0]=at(p,"weapon.falling_guillotine.guard");sounds(ear);p.setShiftKeyDown(true);})
                .thenExecuteFor(20,()->{heartbeat(p);WeaponRuntime.tickPlayer(p);count[0]+=count(sounds(ear),ref[0]);check(h,count[0]<=1,"Held guard is not a loop or per-tick fire hose");})
                .thenExecute(()->{
                    check(h,count[0]==1&&WeaponRuntime.swordStatus(p).orElseThrow().guarding(),"Real guard produced one bounded action");
                    // SwordCycle advances only once per real tick. Release now and reenter next tick;
                    // a false->true pair after this tick was consumed is not a mechanically active edge.
                    p.setShiftKeyDown(false);WeaponRuntime.tickPlayer(p);
                    check(h,!WeaponRuntime.swordStatus(p).orElseThrow().guarding(),"Release immediately ceases valid guard");
                    check(h,count(sounds(ear),ref[0])==0,"Release is silent");
                }).thenExecuteAfter(1,()->{
                    p.setShiftKeyDown(true);heartbeat(p);WeaponRuntime.tickPlayer(p);
                    check(h,WeaponRuntime.swordStatus(p).orElseThrow().guarding(),"Next real tick has mechanically active guard");
                    count[0]+=count(sounds(ear),ref[0]);check(h,count[0]==2,"Later valid guard edge emits one new sample");
                    for(int i=0;i<20;i++) {p.setShiftKeyDown(false);WeaponRuntime.tickPlayer(p);p.setShiftKeyDown(true);WeaponRuntime.tickPlayer(p);}
                    check(h,count(sounds(ear),ref[0])==0,"Same-tick rapid reentry cannot bypass sound retrigger cap");
                }).thenExecuteFor(12,()->{heartbeat(p);WeaponRuntime.tickPlayer(p);long got=count(sounds(ear),ref[0]);
                    check(h,got==0,"Suppressed edge does not start a delayed sound mid-hold");})
                .thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=120, environment = "destiny-test:w90_isolated")
    public void emptyAmmoAndCommittedHeavyZeroEnergyDoNotInventGuardAudio(GameTestHelper h) {
        var empty=owner(h,2.5);var spent=owner(h,9.5);var ear=listener(h,6.5);ClientboundSoundPacket[] refs={null,null};
        loaded(h).thenExecute(()->{
            equip(empty,"crown_splitter",0);equip(spent,"crown_splitter",20);
            refs[0]=at(empty,"weapon.crown_splitter.guard");refs[1]=at(spent,"weapon.crown_splitter.guard");sounds(ear);
            use(h,spent);empty.setShiftKeyDown(true);spent.setShiftKeyDown(true);
        }).thenExecuteFor(12,()->{
            heartbeat(empty);heartbeat(spent);WeaponRuntime.tickPlayer(empty);WeaponRuntime.tickPlayer(spent);
            check(h,!WeaponRuntime.swordStatus(empty).orElseThrow().guarding()&&!WeaponRuntime.swordStatus(spent).orElseThrow().guarding(),"Both guard fixtures remain mechanically invalid");
            var list=sounds(ear);check(h,count(list,refs[0])+count(list,refs[1])==0,"Raw sneak cannot dispatch guard audio without ammo/energy/readiness");
        }).thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=180, environment = "destiny-test:w90_isolated")
    public void casterReleaseAndImpactAreSeparateActualSpatialEventsWithRealHp(GameTestHelper h) {
        var p=owner(h,6.5);var ear=listener(h,4.5);ClientboundSoundPacket[] release={null};int[] releases={0},impacts={0};
        var enemy=h.spawn(EntityTypes.HUSK,new Vec3(10.5,1,6.5));enemy.setNoAi(true);enemy.setNoGravity(true);
        enemy.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);enemy.getAttribute(Attributes.ARMOR).setBaseValue(0);
        enemy.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);enemy.setHealth(1000);TestCleanup.register(h, enemy::discard);
        final Vec3 targetOrigin=enemy.position(); // Packet location is a collision snapshot, not post-hit entity motion.
        // Vanilla packet accessors convert their integer coordinates through float. Quantize the
        // fixture through the same codec; random far-away GameTest origins lose sub-block precision.
        final var targetPacket=DestinySounds.packet("weapon.sword.caster.impact",targetOrigin,SoundSource.PLAYERS,.8f,0);
        loaded(h).thenExecute(()->{equip(p,"temptation_s_hook",20);release[0]=at(p,"weapon.sword.caster.release");sounds(ear);use(h,p);})
                .thenExecuteFor(24,()->{
                    heartbeat(p);WeaponRuntime.tickPlayer(p);
                    for(var s:sounds(ear)) {
                        String key=s.getSound().value().location().getPath();
                        if(key.equals("weapon.sword.caster.release")&&sameOrigin(s,release[0]))releases[0]++;
                        if(key.equals("weapon.sword.caster.impact")&&Math.abs(s.getX()-targetPacket.getX())<=2&&Math.abs(s.getZ()-targetPacket.getZ())<.25
                                &&Math.abs(s.getY()-targetPacket.getY())<3) {
                            impacts[0]++;check(h,releases[0]==1&&enemy.getHealth()<1000,"Only actual projectile collision queues remote impact and HP");
                        }
                    }
                    check(h,releases[0]<=1&&impacts[0]<=1,"Projectile does not repeat release or collision audio");
                }).thenExecute(()->check(h,releases[0]==1&&impacts[0]==1&&WeaponRuntime.activeProjectiles(p)==0,"Observed one release and one real far contact, then shot cleanup: release="+releases[0]+", impact="+impacts[0]+", HP="+enemy.getHealth()))
                .thenSucceed();
    }

    @GameTest(structure=FLOOR,maxTicks=160, environment = "destiny-test:w90_isolated")
    public void guardCleanupNeverSendsSharedStopSoundThatCouldSilenceAnotherOwner(GameTestHelper h) {
        var a=owner(h,2.5);var b=owner(h,9.5);var ear=listener(h,6.5);ClientboundSoundPacket[] refs={null,null};int[] seen={0,0};
        loaded(h).thenExecute(()->{
            equip(a,"abide_the_return",12);equip(b,"abide_the_return",12);refs[0]=at(a,"weapon.sword.guard");refs[1]=at(b,"weapon.sword.guard");
            sounds(ear);a.setShiftKeyDown(true);b.setShiftKeyDown(true);
        }).thenExecuteFor(3,()->{
            heartbeat(a);heartbeat(b);WeaponRuntime.tickPlayer(a);WeaponRuntime.tickPlayer(b);var list=sounds(ear);
            for(int i=0;i<2;i++)seen[i]+=count(list,refs[i]);
        }).thenExecute(()->{
            check(h,seen[0]==1&&seen[1]==1,"Both independent source positions queued exactly one family guard sample");
            TestPlayers.drain(ear);a.setItemInHand(InteractionHand.MAIN_HAND,ItemStack.EMPTY);WeaponRuntime.tickPlayer(a);
            var wire=TestPlayers.outbound(ear);
            check(h,wire.stream().noneMatch(ClientboundStopSoundPacket.class::isInstance),"No event-global stop can cut B's same-key guard tail");
            check(h,WeaponRuntime.swordStatus(b).orElseThrow().guarding()&&PlayerAnimations.swordPlaying(b)&&SuperCamera.swordActive(b),"A cleanup cannot alter B's guard, rig or camera");
        }).thenSucceed();
    }
}
