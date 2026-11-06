package kim.biryeong.destiny.test;

import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.combat.MeleeLunge;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Legacy sword fixtures now advance one real native server physics frame per test tick. */
final class MeleeNativeTestFrames {
    private static final Map<GameTestHelper,List<Runnable>> DRIVERS=new IdentityHashMap<>();
    private MeleeNativeTestFrames() { }
    /** Called only at test entry, before GameTestInfo starts iterating its scheduled-runnable map. */
    static void install(GameTestHelper h) {
        if(DRIVERS.containsKey(h))return;
        var drivers=new ArrayList<Runnable>();DRIVERS.put(h,drivers);
        h.onEachTick(()->List.copyOf(drivers).forEach(Runnable::run));
        TestCleanup.register(h,()->DRIVERS.remove(h));
    }
    /** Safe from a running callback: only our owned list changes, never GameTestInfo's scheduler. */
    static void track(GameTestHelper h,Runnable driver) {
        var drivers=DRIVERS.get(h);
        if(drivers==null)throw new AssertionError("Install native frame drivers at test entry");
        drivers.add(driver);
    }
    /** Explicit native collision fixture at the player's actual feet, including the full forward dash route. */
    static void prepareGround(GameTestHelper h,ServerPlayer p) {
        BlockPos floor=BlockPos.containing(p.getX(),p.getY()-.01,p.getZ());
        for(int x=-1;x<=10;x++)for(int z=-2;z<=2;z++)
            p.level().setBlockAndUpdate(floor.offset(x,0,z),Blocks.STONE.defaultBlockState());
        h.assertTrue(!p.level().noCollision(p,p.getBoundingBox().move(0,-.05,0)),
                Component.literal("Native fixture has real solid collision immediately under feet: "+p.position()+" floor="+floor));
        Vec3 velocity=p.getDeltaMovement();p.setDeltaMovement(new Vec3(velocity.x,-.0784,velocity.z));
        p.setOnGround(true);
    }
    static void cameraFrame(ServerPlayer p) {
        if(!MeleeLunge.active(p))return;
        if(!SuperCamera.active(p))SuperCamera.startSword(p);
        SuperCamera.move(p,new ServerboundMovePlayerPacket.Rot(p.getYRot(),p.getXRot(),p.onGround(),false));
        p.connection.tick();
    }
}
