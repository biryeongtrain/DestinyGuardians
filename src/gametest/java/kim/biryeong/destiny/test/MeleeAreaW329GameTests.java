package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.ability.hunter.*;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.combat.MeleeSweep;
import kim.biryeong.destiny.combat.MeleeLunge;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.input.GuardianAction;
import kim.biryeong.destiny.weapon.*;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Real HP, accepted input, world collision and native connection checks. Master owns native client QA. */
public final class MeleeAreaW329GameTests {
    private static final String FLOOR="destiny-test:floor", ENV="destiny-test:w90_isolated";
    private static final float HP=200;
    private static void check(GameTestHelper h,boolean value,String reason) {h.assertTrue(value,Component.literal(reason));}
    private static ServerPlayer player(GameTestHelper h,Vec3 pos) {
        var p=TestPlayers.hunter(h,Element.ARC,pos,-90,0,"W329"+UUID.randomUUID().toString().substring(0,7));
        p.setOnGround(true);
        if(pos.y==1)MeleeNativeTestFrames.prepareGround(h,p);
        TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);SuperCamera.stop(p);PlayerAnimations.stop(p);TestPlayers.remove(p);});
        return p;
    }
    private static Husk foe(GameTestHelper h,double x,double y,double z) {
        var e=h.spawn(EntityTypes.HUSK,new Vec3(x,y,z));e.setNoAi(true);e.setNoGravity(true);e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HP);e.getAttribute(Attributes.ARMOR).setBaseValue(0);
        e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);e.setHealth(HP);
        TestCleanup.register(h,e::discard);return e;
    }
    private static void equip(ServerPlayer p,String id,int rounds) {
        var entry=WeaponCatalog.find(id).orElseThrow();var stack=WeaponItems.create(entry);
        WeaponItems.save(stack,new WeaponMagazine(WeaponProfile.forEntry(entry),rounds,0));
        p.setItemInHand(InteractionHand.MAIN_HAND,stack);WeaponRuntime.tickPlayer(p);
    }
    private static int rounds(ServerPlayer p) {
        var stack=p.getMainHandItem();return WeaponItems.magazine(stack,WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow())).rounds();
    }
    private static void nativeFrame(ServerPlayer p) {
        p.connection.handleClientTickEnd(ServerboundClientTickEndPacket.INSTANCE);
        if(!SuperCamera.active(p)&&MeleeLunge.active(p)) {
            // Emulate the client applying the last real motion packet, not server-side post-travel drag.
            var packets=TestPlayers.outbound(p);
            Vec3 velocity=p.getDeltaMovement();
            for(var packet:packets)if(packet instanceof ClientboundSetEntityMotionPacket motion&&motion.id()==p.getId())
                velocity=motion.movement();
            Vec3 next=p.position().add(velocity);
            p.connection.handleMovePlayer(new ServerboundMovePlayerPacket.Pos(next.x,next.y,next.z,p.onGround(),false));
        }
        p.connection.handleClientTickEnd(ServerboundClientTickEndPacket.INSTANCE);
        p.connection.tick();
    }
    private static void wall(GameTestHelper h,int x,int z) {
        for(int y=1;y<=4;y++)h.setBlock(x,y,z,Blocks.STONE);
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=40)
    public void glaiveCleaveHitsBothSidesOnceAndExcludesRearAllyAndWall(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        var p=player(h,new Vec3(2.5,1,6.5));equip(p,"nezarec_s_whisper",0);
        var a=foe(h,4.5,1,5.3);var b=foe(h,4.5,1,7.7);var rear=foe(h,1.2,1,6.5);
        var hidden=foe(h,5.5,1,6.5);wall(h,4,6);
        var ally=foe(h,3.5,1,6.5);var scores=h.getLevel().getScoreboard();
        var team=scores.addPlayerTeam("w329_"+UUID.randomUUID().toString().substring(0,8));
        scores.addPlayerToTeam(p.getScoreboardName(),team);scores.addPlayerToTeam(ally.getScoreboardName(),team);
        TestCleanup.register(h,()->scores.removePlayerTeam(team));
        WeaponRuntime.onPunch(p);
        check(h,a.getHealth()<HP&&a.getHealth()==b.getHealth(),"Both visible side foes receive one equal real contact");
        float once=a.getHealth();WeaponRuntime.onPunch(p);
        check(h,a.getHealth()==once&&b.getHealth()==once&&rounds(p)==0,"Same-tick spam cannot repeat damage or manufacture ammo");
        check(h,rear.getHealth()==HP&&ally.getHealth()==HP&&hidden.getHealth()==HP,"Rear, ally and wall-occluded foes retain HP");
        h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=40)
    public void targetlessSwordContactMovesTwoGroundAndFiveAirForOneAmmo(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        var ground=player(h,new Vec3(2.5,1,3));var air=player(h,new Vec3(2.5,120,9));air.setOnGround(false);
        equip(ground,"falling_guillotine",12);equip(air,"falling_guillotine",12);
        Vec3 g=ground.position(),a=air.position();
        WeaponRuntime.onPunch(ground);WeaponRuntime.onPunch(air);
        check(h,ground.position().equals(g)&&air.position().equals(a),"Windup cannot move before contact");
        MeleeNativeTestFrames.track(h,()->{WeaponRuntime.tickPlayer(ground);WeaponRuntime.tickPlayer(air);nativeFrame(ground);nativeFrame(air);});
        h.runAfterDelay(20,()->{
            check(h,Math.abs(ground.getX()-g.x-2)<.01&&Math.abs(air.getX()-a.x-5)<.01,"Accepted targetless contact uses 2 ground / 5 air horizontal tuning: ground="+ground.position().subtract(g)+" air="+air.position().subtract(a)+" active="+MeleeLunge.active(ground)+"/"+MeleeLunge.active(air));
            check(h,Math.abs(ground.getY()-g.y)<1e-5&&ground.onGround()&&air.getY()<a.y,"Ground dash keeps real floor contact while air dash preserves falling gravity");
            check(h,rounds(ground)==11&&rounds(air)==11,"One contact costs one round regardless of displacement");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=40)
    public void lungeStopsAtLowBodyWallAndRebasesOnlyItsOwnNativeConnection(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        var p=player(h,new Vec3(2.5,1,6.5));var other=player(h,new Vec3(2.5,1,11));
        // Register both native connections; ChunkMap.move requires real world membership.
        for(var owner:List.of(p,other)) {
            h.getLevel().addNewPlayer(owner);
            TestCleanup.register(h,()->{if(h.getLevel().getEntity(owner.getId())==owner)
                h.getLevel().removePlayerImmediately(owner,net.minecraft.world.entity.Entity.RemovalReason.DISCARDED);});
        }
        equip(p,"falling_guillotine",12);
        check(h,SuperCamera.swordActive(p),"Collision fixture uses the real equipped sword camera/native-physics path");
        Vec3 start=p.position(),otherStart=other.position();
        var obstruction=net.minecraft.core.BlockPos.containing(start.x+1.5,start.y,start.z);
        p.level().setBlockAndUpdate(obstruction,Blocks.STONE.defaultBlockState());
        check(h,!p.level().noCollision(p,p.getBoundingBox().move(1.5,0,0)),"Low wall intersects the actual player's swept body at foot height");
        p.setDeltaMovement(new Vec3(.1,-.3,.2));
        SwordMelee.lunge(p,5);
        check(h,p.position().equals(start),"Starting a velocity lease never teleports the body");
        check(h,TestPlayers.outbound(p).stream().anyMatch(x->x instanceof ClientboundSetEntityMotionPacket m&&m.id()==p.getId()),"Real player native motion packet is emitted");
        MeleeNativeTestFrames.track(h,()->{
            SuperCamera.move(p,new ServerboundMovePlayerPacket.Rot(p.getYRot(),p.getXRot(),p.onGround(),false));
            nativeFrame(p);
        });
        h.runAfterDelay(8,()->{
            check(h,p.getX()>start.x&&p.getBoundingBox().maxX<=obstruction.getX()+.001
                    &&p.getY()==start.y&&p.onGround(),"Whole body native collision stops at actual low wall: delta="+p.position().subtract(start)+" boxMax="+p.getBoundingBox().maxX+" wall="+obstruction);
            check(h,other.position().equals(otherStart),"A different connection is never moved");
            check(h,!MeleeLunge.active(p),"Velocity ownership is finite");
            // The separate ordinary connection retains vanilla validation without the sword camera's packet ownership.
            check(h,!SuperCamera.active(other),"Adversarial movement fixture has no camera ownership");
            TestPlayers.drain(other);other.connection.resetPosition();
            other.connection.handleClientTickEnd(ServerboundClientTickEndPacket.INSTANCE);
            other.connection.handleMovePlayer(new ServerboundMovePlayerPacket.Pos(other.getX()+100,other.getY(),other.getZ(),true,false));
            other.connection.handleClientTickEnd(ServerboundClientTickEndPacket.INSTANCE);
            check(h,other.position().distanceToSqr(otherStart)<1e-8&&!other.hasDisconnected()
                    &&TestPlayers.outbound(other).stream().anyMatch(ClientboundPlayerPositionPacket.class::isInstance),
                    "Ordinary vanilla validation rejects and corrects unowned 100-block movement without malformed-packet disconnect");
            h.succeed();
        });
    }

    private static double number(Object object,String name) {
        try{var field=object.getClass().getDeclaredField(name);field.setAccessible(true);return field.getDouble(object);}
        catch(ReflectiveOperationException e){throw new AssertionError(e);}
    }
    private static void loaded(GameTestHelper h,Runnable body) {
        h.startSequence().thenWaitUntil(()->check(h,BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(),"Waiting for real Hunter limb"))
                .thenExecute(body);
    }
    private static ServerPlayer superPlayer(GameTestHelper h,Identifier id,Vec3 pos,boolean grounded) {
        var p=player(h,pos);var element=AbilityRegistry.get(id).orElseThrow().element();
        Guardians.data(p).setLoadout(GuardianClass.HUNTER,HunterAbilities.preset(element).with(AbilitySlot.SUPER,id));
        Guardians.data(p).setSuperEnergy(1);p.setOnGround(grounded);
        check(h,AbilityService.use(p,AbilitySlot.SUPER)==AbilityService.Result.OK,"Actual named super activates");
        MeleeNativeTestFrames.track(h,()->{
            if(AbilityService.inSuper(p)) {
                SuperCamera.move(p,new ServerboundMovePlayerPacket.Rot(p.getYRot(),p.getXRot(),grounded,false));
                AbilityService.tickPlayer(p);
                nativeFrame(p);
            }
            TestPlayers.drain(p);
        });return p;
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=1200)
    public void arcStaffAndSpectralActualContactsCleaveWithoutCrosshairAndRejectSpam(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        loaded(h,()->{
            var arc=superPlayer(h,HunterAbilities.ARC_STAFF,new Vec3(2.5,1,3),true);
            var spectral=superPlayer(h,HunterExpandedSupers.SPECTRAL_BLADES,new Vec3(2.5,1,9),true);
            var a=foe(h,4.6,1,2);var b=foe(h,4.6,1,4);var c=foe(h,4.6,1,8);var d=foe(h,4.6,1,10);
            var rear=foe(h,1,1,3);arc.setXRot(75);spectral.setXRot(75);
            int ready=Math.max(SuperAttackTiming.ARC_DEPLOY,
                    MeleeSuperAnimationTiming.durationTicks("w230_hunter_spectral_blades_start",30))+2;
            h.runAfterDelay(ready,()->{
                Vec3 before=arc.position();for(int i=0;i<8;i++){AbilityService.perform(arc,GuardianAction.PRIMARY);AbilityService.perform(spectral,GuardianAction.PRIMARY);}
                check(h,arc.position().equals(before)&&a.getHealth()==HP&&c.getHealth()==HP,"Accepted input waits for real contact and spam cannot dash early");
            });
            int settled=Math.max(MeleeSuperAnimationTiming.contactTicks(MeleeSuperAnimationTiming.arcAttack(true,0),SuperAttackTiming.ARC_CONTACT),
                    MeleeSuperAnimationTiming.contactTicks("w230_hunter_spectral_blades_attack",7))+6;
            h.runAfterDelay(ready+settled,()->{
                check(h,a.getHealth()<HP&&a.getHealth()==b.getHealth(),"Arc Staff sweeps both side foes with steep view pitch");
                check(h,c.getHealth()<HP&&c.getHealth()==d.getHealth(),"Spectral light sweeps both side foes with steep view pitch: hp="+c.getHealth()+"/"+d.getHealth()+" position="+spectral.position()+" active="+AbilityService.inSuper(spectral));
                float ah=a.getHealth(),ch=c.getHealth();
                var apos=arc.position();var spos=spectral.position();
                for(int i=0;i<8;i++){AbilityService.perform(arc,GuardianAction.PRIMARY);AbilityService.perform(spectral,GuardianAction.PRIMARY);}
                check(h,arc.position().equals(apos)&&spectral.position().equals(spos)&&a.getHealth()==ah&&c.getHealth()==ch,"Input spam never creates immediate extra lunge/damage");
                check(h,rear.getHealth()==HP&&Guardians.data(arc).superEnergy()==0&&Guardians.data(spectral).superEnergy()==0,"Rear foe excluded and accepted casts pay energy only once");h.succeed();
            });
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=1200)
    public void arcStaffAndSpectralTargetlessAirContactsTravelFiveAndStaleSessionCannotMove(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        loaded(h,()->{
            var arc=superPlayer(h,HunterAbilities.ARC_STAFF,new Vec3(2.5,120,3),false);
            var spectral=superPlayer(h,HunterExpandedSupers.SPECTRAL_BLADES,new Vec3(2.5,1,9),true);
            Vec3 a=arc.position(),s=spectral.position();
            int ready=Math.max(SuperAttackTiming.ARC_DEPLOY,
                    MeleeSuperAnimationTiming.durationTicks("w230_hunter_spectral_blades_start",30))+2;
            int settled=Math.max(MeleeSuperAnimationTiming.contactTicks(MeleeSuperAnimationTiming.arcAttack(false,0),SuperAttackTiming.ARC_CONTACT),
                    MeleeSuperAnimationTiming.contactTicks("w230_hunter_spectral_blades_attack_air",7))+6;
            // 26.3 runs tick-map callbacks in hash order, then sequences. Keep native onEachTick physics
            // before acceptance/assertions, so the +2 landing check really observes two complete frames.
            h.startSequence().thenExecuteAfter(ready,()->{
                AbilityService.perform(arc,GuardianAction.PRIMARY);
                // Spectral warmed up on real ground: no unrelated 30+ block accumulated fall damage.
                // Accept a short airborne contact, then let native gravity land it during the authored windup.
                check(h,spectral.onGround()&&spectral.getHealth()==20,"Spectral starts its regression jump alive on actual solid ground");
                spectral.setPos(spectral.getX(),spectral.getY()+.2,spectral.getZ());
                spectral.setDeltaMovement(new Vec3(0,-.2,0));spectral.setOnGround(false);
                check(h,!spectral.level().noCollision(spectral,spectral.getBoundingBox().move(0,-.25,0)),
                        "The airborne fixture has its real floor immediately below the short fall");
                AbilityService.perform(spectral,GuardianAction.PRIMARY);
                check(h,PlayerAnimations.activeClip(spectral).equals("w230_hunter_spectral_blades_attack_air"),
                        "Accepted short fall selects the actual airborne source attack");
            }).thenExecuteAfter(2,()->{
                check(h,spectral.onGround()&&Math.abs(spectral.getY()-s.y)<1e-6,
                        "Spectral lands by native floor collision during contact windup: position="+spectral.position()
                                +" velocity="+spectral.getDeltaMovement()+" groundY="+s.y+" onGround="+spectral.onGround());
                AbilityService.perform(spectral,GuardianAction.PRIMARY); // Rejected cooldown input cannot replace the air snapshot.
            }).thenExecuteAfter(settled-2,()->{
                check(h,spectral.isAlive()&&AbilityService.inSuper(spectral),"The short landing must preserve the real Spectral session without fall death");
                check(h,Math.abs(arc.getX()-a.x-5)<.01&&Math.abs(spectral.getX()-s.x-5)<.01,"Arc air contact and Spectral accepted-air contact retain five blocks even after windup landing: arc="+arc.position().subtract(a)+" spectral="+spectral.position().subtract(s)+" grounded="+spectral.onGround());
                var stale=Guardians.runtime(arc).superSession;AbilityService.endSuper(arc);Vec3 after=arc.position();
                check(h,!MeleeSuperMovement.contact(arc,stale,4,.3,1.8,true,e->{})&&arc.position().equals(after),"Retired session cannot move/query even when called directly");
                h.succeed();
            });
        });
    }
}
