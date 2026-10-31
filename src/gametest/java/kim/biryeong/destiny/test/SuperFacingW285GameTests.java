package kim.biryeong.destiny.test;

import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.input.ClientControls;
import kim.biryeong.gcbserver.player.GCBPlayer;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.bone.RenderedBone;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import java.util.Map;
import java.util.function.Function;

public final class SuperFacingW285GameTests {
    private static void check(GameTestHelper h, boolean value, String message) { h.assertTrue(value, Component.literal(message)); }
    private static Object field(Object target, String name) {
        try { var f=(target instanceof Class<?> c?c:target.getClass()).getDeclaredField(name); f.setAccessible(true); return f.get(target instanceof Class<?>?null:target); }
        catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }
    private static Object session(Class<?> type, ServerPlayer p) { return ((Map<?,?>)field(type,"ACTIVE")).get(p.getUUID()); }
    private static ServerPlayer owner(GameTestHelper h, String version) {
        var p=TestPlayers.hunter(h,Element.ARC,new Vec3(3,1,3),0,0);
        if(version!=null){((GCBPlayer)p).gcb$markHasMod();((GCBPlayer)p).gcb$setModVersion(version);}
        TestCleanup.register(h,()->{SuperCamera.stop(p);PlayerAnimations.stop(p);ClientControls.forget(p);TestPlayers.remove(p);});
        return p;
    }
    private static void loaded(GameTestHelper h,Runnable body) {
        h.startSequence().thenWaitUntil(()->check(h,BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(),"Wait for limb"))
                .thenExecute(body);
    }
    @GameTest(structure="destiny-test:floor",maxTicks=1200,environment="destiny-test:w258_camera_clock")
    public void allHunterSupersFollowYawAndUpperBodyPitch(GameTestHelper h) {
        loaded(h,()->{
            for(String clip:new String[]{"super_arc","super_solar","super_void"}) {
                var p=owner(h,null);
                check(h,PlayerAnimations.loop(p,clip),clip+" starts");
                var tracker=(EntityTracker)field(session(PlayerAnimations.class,p),"tracker");
                var chest=tracker.bones().stream().filter(b->b.name().rawName().equals("pc_chest")).findFirst().orElseThrow();
                @SuppressWarnings("unchecked") var modifier=(Function<Quaternionf,Quaternionf>)field(chest,"globalRotModifier");
                for(float yaw:new float[]{90,-179,179}) {
                    p.setYRot(yaw); p.setXRot(35);
                    check(h,Math.abs(tracker.rotation().y()-yaw)<.01,clip+" tracks stationary view yaw");
                    ((ServerAnimationClock)(Object)tracker).destiny$advanceServerTick();
                    check(h,Math.abs(tracker.getPipeline().getRotation().y()-yaw)<.01,clip+" publishes view yaw to pipeline");
                    for(var bone:tracker.bones()) if(bone.getDisplay()!=null) {
                        var display=(Entity)field(bone.getDisplay(),"display");
                        check(h,Math.abs(display.getYRot()-yaw)<.01,clip+" rotates actual display "+bone.name().rawName());
                    }
                    var q=modifier.apply(new Quaternionf());
                    check(h,Math.abs(q.x-(float)Math.sin(Math.toRadians(35)/2))<.001,clip+" pitches chest with view");
                    p.setXRot(-35);q=modifier.apply(new Quaternionf());
                    check(h,q.x<0,clip+" follows upward pitch too");
                }
                PlayerAnimations.stop(p);
            }
            h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=1200,environment="destiny-test:w258_camera_clock")
    public void predictedCarrierHasExactSeatVelocityAndCleanup(GameTestHelper h) {
        loaded(h,()->{
            var p=owner(h,"4.2.0");
            check(h,PlayerAnimations.loop(p,"super_arc")&&SuperCamera.start(p,Element.ARC),"Start GCB camera");
            var mount=(Entity)field(session(SuperCamera.class,p),"mount");
            check(h,mount instanceof Mob && mount.isInvisible() && !mount.hasControllingPassenger(),"Prediction uses invisible server-authoritative Mob");
            check(h,!p.isPassenger()&&p.level().getEntity(mount.getId())==null,"No real mount or world entity");
            check(h,field(session(SuperCamera.class,p),"camera")!=mount,"Camera stays separate from the player and limb passenger chain");
            var seat=mount.getPassengerRidingPosition(p).subtract(p.getVehicleAttachmentPoint(mount));
            check(h,seat.distanceToSqr(p.position())<1e-8,"Carrier compensates actual passenger attachment");
            check(h,mount.getBoundingBox().minY>=p.getY(),"Small carrier cannot intersect the floor at rest");
            Vec3 before=p.position();p.setPos(before.add(.2,0,.1));
            SuperCamera.move(p,new ServerboundMovePlayerPacket.Rot(0,0,true,false));SuperCamera.tick(p.level().getServer());
            check(h,mount.getDeltaMovement().distanceToSqr(new Vec3(.2,0,.1))<1e-8,"Prediction receives resolved body displacement");
            SuperCamera.tick(p.level().getServer());
            check(h,mount.getDeltaMovement().lengthSqr()==0,"Stopping sends zero, no stale extrapolation");
            SuperCamera.stop(p);check(h,!SuperCamera.active(p)&&!p.isPassenger(),"Stop retires only virtual carrier");
            h.succeed();
        });
    }
    private static void flatten(net.minecraft.network.protocol.Packet<?> packet, java.util.List<net.minecraft.network.protocol.Packet<?>> out) {
        if (packet instanceof net.minecraft.network.protocol.game.ClientboundBundlePacket bundle)
            bundle.subPackets().forEach(child -> flatten(child,out));
        else out.add(packet);
    }
    private static boolean hiddenFlag(ServerPlayer p, boolean hidden) {
        var packets=new java.util.ArrayList<net.minecraft.network.protocol.Packet<?>>();
        TestPlayers.outbound(p).forEach(packet->flatten(packet,packets));
        int flagsId=kr.toxicity.model.mixin.EntityAccessor.bettermodel$getDataSharedFlagsId().id();
        Byte last=null;
        for(var packet:packets) if(packet instanceof net.minecraft.network.protocol.game.ClientboundSetEntityDataPacket data && data.id()==p.getId())
            for(var value:data.packedItems()) if(value.id()==flagsId && value.value() instanceof Byte flags) last=flags;
        return last!=null && ((last&32)!=0)==hidden;
    }
    @GameTest(structure="destiny-test:floor",maxTicks=1200,environment="destiny-test:w258_camera_clock")
    public void ownerBodyMaskIsPacketOnlyAndRestoresOnClose(GameTestHelper h) {
        loaded(h,()->{
            var p=owner(h,"4.2.0");
            var manager=BetterModel.platform().manager(kr.toxicity.model.api.manager.PlayerManager.class);
            manager.player(kr.toxicity.model.api.mod.platform.ModPlayer.of(p.connection));
            TestCleanup.register(h,()->((Map<?,?>)field(manager.getClass(),"playerMap")).remove(p.getUUID()));
            check(h,PlayerAnimations.loop(p,"super_arc")&&SuperCamera.start(p,Element.ARC),"Start owner rig");
            var tracker=(EntityTracker)field(session(PlayerAnimations.class,p),"tracker");
            check(h,tracker.registry().spawn(kr.toxicity.model.api.mod.platform.ModPlayer.of(p.connection)),"Register live owner viewer");
            TestPlayers.drain(p);
            PlayerAnimations.tick(p.level().getServer());
            check(h,hiddenFlag(p,true),"Owner receives invisible vanilla body after visible rig spawn");
            check(h,!p.isInvisible(),"Real server player visibility is untouched");
            SuperCamera.stop(p);
            check(h,!(boolean)field(session(PlayerAnimations.class,p),"ownerBodyHidden"),"Same-tick stop resets owner mask session");
            PlayerAnimations.stop(p);
            check(h,hiddenFlag(p,false),"Close restores live body flags");
            check(h,!p.isInvisible()&&!p.isPassenger(),"Cleanup preserves actual body state");
            h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=40,environment="destiny-test:w258_camera_clock")
    public void unknownAndOlderClientsKeepDisplayCarrier(GameTestHelper h) {
        for(String v:new String[]{null,"","unknown","4.1.9","4.2.0","4.3.0","5.0.0"}) {
            var p=owner(h,v);boolean expected=v!=null&&(v.equals("4.2.0")||v.equals("4.3.0")||v.equals("5.0.0"));
            check(h,ClientControls.mountPrediction(p)==expected,"Version gate "+v);
            check(h,SuperCamera.start(p,Element.ARC),"Camera starts");
            var mount=(Entity)field(session(SuperCamera.class,p),"mount");
            check(h,(mount instanceof Mob)==expected,"Only supported peer gets Mob "+v);
            var seat=mount.getPassengerRidingPosition(p).subtract(p.getVehicleAttachmentPoint(mount));
            check(h,expected || seat.distanceToSqr(p.position())<1e-8,"No fallback height regression");
            SuperCamera.stop(p);
        }
        h.succeed();
    }
}
