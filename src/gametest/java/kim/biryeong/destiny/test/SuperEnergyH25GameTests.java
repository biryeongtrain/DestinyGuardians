package kim.biryeong.destiny.test;

import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.Element;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.TrackerModifier;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.phys.Vec3;
import java.util.List;

/** Actual transmitted display-transform/socket parity, bounded displays and cleanup. Not pixel proof. */
public final class SuperEnergyH25GameTests {
    private static void check(GameTestHelper h,boolean b,String why){h.assertTrue(b,Component.literal(why));}
    private static void loaded(GameTestHelper h,Runnable r) {
        h.startSequence().thenWaitUntil(()->check(h,BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(),"Limb loaded")).thenExecute(r);
    }
    private static void pose(GameTestHelper h,net.minecraft.server.level.ServerPlayer p,Element element) {
        check(h,PlayerAnimations.loop(p,element==Element.ARC?"super_arc":"super_void"),"Actual loop starts");
        PlayerAnimations.superItem(p,SuperVisuals.item(element),element==Element.VOID);
        var tracker=BetterModel.limb(HunterModelAssets.MODEL_NAME).orElseThrow().getOrCreate(ModPlayer.of(p.connection),TrackerModifier.DEFAULT);
        ((ServerAnimationClock)(Object)tracker).destiny$advanceServerTick();
    }
    private static Object field(Object receiver,String name) throws ReflectiveOperationException {
        var f=receiver.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(receiver);
    }
    private static Object packed(Object data,String name) throws ReflectiveOperationException {
        var item=field(data,name);var method=item.getClass().getDeclaredMethod("getForceValue");method.setAccessible(true);
        return ((net.minecraft.network.syncher.SynchedEntityData.DataValue<?>)method.invoke(item)).value();
    }
    private static eu.pb4.polymer.virtualentity.api.ElementHolder energyHolder(net.minecraft.server.level.ServerPlayer owner) {
        try {
            var active=Class.forName("kim.biryeong.destiny.fx.SuperEnergyVfx").getDeclaredField("ACTIVE");
            active.setAccessible(true);
            for(var e:(List<?>)active.get(null)) if(field(e,"owner")==owner)
                return (eu.pb4.polymer.virtualentity.api.ElementHolder)field(e,"holder");
            throw new AssertionError("Missing fixture energy");
        } catch(ReflectiveOperationException e){throw new AssertionError(e);}
    }
    @GameTest(structure="destiny-test:floor",maxTicks=1200, environment = "destiny-test:w90_isolated")
    public void socketsMatchNativeDisplayTransformAtDifferentYawPitchAndFixtureMovement(GameTestHelper h) {
        loaded(h,()->{
            for(Element element:List.of(Element.ARC,Element.VOID)) for(int pitch:new int[]{-35,0,35}) {
                var p=TestPlayers.create(h,new Vec3(2.5,1,6.5),pitch==0?0:70,pitch);
                try {
                    pose(h,p,element);
                    var tracker=BetterModel.limb(HunterModelAssets.MODEL_NAME).orElseThrow().getOrCreate(ModPlayer.of(p.connection),TrackerModifier.DEFAULT);
                    p.setPos(p.position().add(1.25,.4,-.75));
                    ((ServerAnimationClock)(Object)tracker).destiny$advanceServerTick();
                    var b=tracker.bone(x->x.name().rawName().equals(element==Element.VOID?"pli_left_item":"pri_right_item"));
                    // BM serializes animation transforms in its separate packet metadata buffer,
                    // NOT the backing native entity's unchanged SynchedEntityData.
                    var packetData=field(field(field(b,"globalState"),"transformer"),"entityData");
                    var transform=new com.mojang.math.Transformation(new org.joml.Vector3f((org.joml.Vector3fc)packed(packetData,"translation")),
                            new org.joml.Quaternionf((org.joml.Quaternionfc)packed(packetData,"rotation")),
                            new org.joml.Vector3f((org.joml.Vector3fc)packed(packetData,"scale")),new org.joml.Quaternionf());
                    for(Vec3 raw:element==Element.VOID?List.of(new Vec3(11.27,20,8),new Vec3(16.24,8,8)):List.of(new Vec3(8,-15,8),new Vec3(8,31,8))) {
                        var v=new org.joml.Vector3f((float)(raw.x-8)/16,(float)(raw.y-8)/16,(float)(raw.z-8)/16);
                        if(element==Element.VOID)v.rotateY(-(float)Math.PI/2);
                        v.add(0,.125f,0).rotateY((float)Math.PI);
                        transform.getMatrix().transformPosition(v);
                        // BM keeps the unmounted backing entity off-world; SetPassengers supplies
                        // the vanilla riding anchor in the actual client.
                        v.rotateY(-(float)Math.toRadians(tracker.getPipeline().getRotation().y()));
                        // Reproduce native passenger positioning, not the implementation socket helper.
                        var nativeDisplay=(net.minecraft.world.entity.Display.ItemDisplay)field(b.getDisplay(),"display");
                        // BM mounts via packet only; its backing display refuses server riding.
                        var seat=p.getPassengerRidingPosition(nativeDisplay).subtract(nativeDisplay.getVehicleAttachmentPoint(p));
                        Vec3 expected=seat.add(v.x,v.y,v.z);
                        check(h,seat.y-p.getY()>.5,"Native passenger anchor cannot be omitted");
                        Vec3 actual=PlayerAnimations.equipmentPoint(p,element==Element.VOID,raw.x,raw.y,raw.z);
                        check(h,actual!=null&&actual.distanceTo(expected)<.002,"Native socket parity "+element+" pitch="+pitch+" gap="+(actual==null?-1:actual.distanceTo(expected)));
                    }
                    check(h,PlayerAnimations.equipmentPoint(p,element!=Element.VOID,8,8,8)==null,"Wrong equipment hand cannot produce a guessed socket");
                } catch(ReflectiveOperationException e){throw new AssertionError(e);}
                finally{TestPlayers.remove(p);}
            }
            h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=1200, environment = "destiny-test:w90_isolated")
    public void actualArcAndVoidReuseSixSlotsAndCancellationDoesNotTouchOtherOwner(GameTestHelper h) {
        loaded(h,()->{
            var a=TestPlayers.create(h,new Vec3(2.5,1,6.5),0,0);var b=TestPlayers.create(h,new Vec3(5.5,1,6.5),40,-20);
            try {
                pose(h,a,Element.ARC);pose(h,b,Element.VOID);
                SuperVfx.materialize(a,Element.ARC);SuperVfx.materialize(b,Element.VOID);
                SuperVfx.tickEquipmentEnergy(h.getLevel().getServer());
                check(h,SuperVfx.energyDisplayCount(a)==6&&SuperVfx.energyDisplayCount(b)==6,"Six real reusable item displays each");
                for(int i=0;i<10;i++)SuperVfx.tickEquipmentEnergy(h.getLevel().getServer());
                check(h,SuperVfx.energyDisplayCount(a)==6&&SuperVfx.energyDisplayCount(b)==6,"Same tick cannot multiply displays");
                var holder=energyHolder(a);
                ((eu.pb4.polymer.virtualentity.api.attachment.EntityAttachment)holder.getAttachment()).updateCurrentlyTracking(List.of());
                check(h,holder.getWatchingPlayers().contains(a.connection),"Owner survives periodic tracker pruning");
                SuperVfx.dematerialize(a,Element.ARC);
                check(h,SuperVfx.energyDisplayCount(a)==0&&SuperVfx.energyDisplayCount(b)==6,"Owner-isolated normal end");
                check(h,holder.getAttachment()==null&&holder.getWatchingPlayers().isEmpty(),"Destroyed energy detaches and removes all watches");
                SuperVfx.cancelOwned(b);SuperVfx.cancelOwned(b);
                check(h,SuperVfx.energyDisplayCount(b)==0,"Idempotent explicit cleanup");
                check(h,SuperVfx.activeCount(a)==0&&SuperVfx.activeCount(b)==0,"Legacy beam slots retain their contract");
                h.succeed();
            } finally{TestPlayers.remove(a);TestPlayers.remove(b);}
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=1200, environment = "destiny-test:w90_isolated")
    public void noPoseCannotAllocateAndVoidReleaseSurvivesNormalEndThenExpires(GameTestHelper h) {
        quiet(h,()->{
        var p=TestPlayers.create(h,new Vec3(2.5,1,6.5),0,0);TestCleanup.register(h, ()->TestPlayers.remove(p));
        SuperVfx.materialize(p,Element.VOID);SuperVfx.tickEquipmentEnergy(h.getLevel().getServer());
        check(h,SuperVfx.energyDisplayCount(p)==0,"No limb pose means no floating near-face substitute");
        SuperVfx.voidRelease(p,p.getEyePosition(),p.getLookAngle());SuperVfx.dematerialize(p,Element.VOID);
        h.runAfterDelay(2,()->check(h,SuperVfx.energyDisplayCount(p)==6,"World release shock survives normal end"));
        h.runAfterDelay(9,()->{
            check(h,SuperVfx.energyDisplayCount(p)==0&&SuperVfx.energySnapshots().stream().noneMatch(s->s.owner().equals(p.getUUID())),"Release bundle expires after eight server ticks");h.succeed();
        });
        });
    }
    private static void quiet(GameTestHelper h,Runnable action) {
        long[] since={-1};
        h.startSequence().thenWaitUntil(()->{
            if(!SuperVfx.energySnapshots().isEmpty()||!SuperVfx.lifecycleSnapshots().isEmpty())since[0]=-1;
            else if(since[0]<0)since[0]=h.getTick();
            check(h,since[0]>=0&&h.getTick()-since[0]>=10,"Wait for quiet shared pools without allocating or evicting another test");
        }).thenExecute(action);
    }
    @GameTest(structure="destiny-test:floor",maxTicks=1200, environment = "destiny-test:w90_isolated")
    public void hardCapsAndWorldChangeCannotLeaveAnEnergyBundle(GameTestHelper h) {
        quiet(h,()->{
        var players=new java.util.ArrayList<net.minecraft.server.level.ServerPlayer>();
        try {
            for(int i=0;i<10;i++){
                var p=TestPlayers.create(h,new Vec3(2.5,1,6.5),0,0);players.add(p);
                pose(h,p,Element.ARC);SuperVfx.materialize(p,Element.ARC);
                SuperVfx.tickEquipmentEnergy(h.getLevel().getServer());
            }
            check(h,SuperVfx.energySnapshots().size()<=8,"Global hard ceiling eight bundles = at most48 displays");
            check(h,SuperVfx.energySnapshots().stream().mapToInt(SuperVfx.EnergySnapshot::displays).sum()==48,"Eight live holders really allocate 48, never 60 displays");
            check(h,SuperVfx.energySnapshots().stream().noneMatch(s->s.owner().equals(players.getFirst().getUUID())),"Oldest bundle evicted");
            var last=players.getLast();var other=h.getLevel().getServer().getLevel(net.minecraft.world.level.Level.NETHER);
            check(h,other!=null,"Other dimension available");last.setServerLevel(other);
            SuperVfx.tickEquipmentEnergy(h.getLevel().getServer());
            check(h,SuperVfx.energySnapshots().stream().noneMatch(s->s.owner().equals(last.getUUID())),"Dimension mismatch cleans up without transferring effects");
            h.succeed();
        } finally{players.forEach(TestPlayers::remove);}
        });
    }
}
