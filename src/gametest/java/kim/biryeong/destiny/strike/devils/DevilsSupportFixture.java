package kim.biryeong.destiny.strike.devils;

import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.LinkedHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;

public final class DevilsSupportFixture {
    private static void check(GameTestHelper h,boolean ok,String text) { h.assertTrue(ok,Component.literal(text)); }
    public static void verify(GameTestHelper h, ServerPlayer player) {
        var level=h.getLevel();var base=h.absolutePos(new BlockPos(3,20,3));
        var saved=new LinkedHashMap<BlockPos,BlockState>();
        for(var p:BlockPos.betweenClosed(base.offset(-1,-1,-1),base.offset(1,3,1))) {
            saved.put(p.immutable(),level.getBlockState(p));level.setBlockAndUpdate(p,Blocks.AIR.defaultBlockState());
        }
        try {
            var feet=Vec3.atLowerCornerOf(base).add(.5,.5,.5);
            level.setBlockAndUpdate(base,Blocks.STONE_SLAB.defaultBlockState());
            check(h,level.getBlockState(BlockPos.containing(feet).below()).isAir(),"Old integer-below probe misses bottom slab");
            check(h,DevilsSpatial.groundedPlayer(level,player,feet),"Bottom slab is a valid revival surface");
            check(h,!DevilsSpatial.groundedPlayer(level,player,feet.add(0,.3,0)),"Air above slab is not grounded");
            check(h,!DevilsSpatial.groundedPlayer(level,player,feet.add(0,-.2,0)),"Feet inside slab are rejected");
            level.setBlockAndUpdate(base,Blocks.STONE.defaultBlockState());
            feet=Vec3.atLowerCornerOf(base).add(.5,1,.5);
            check(h,DevilsSpatial.groundedPlayer(level,player,feet),"Full block remains valid");
            level.setBlockAndUpdate(base.above(),Blocks.STONE.defaultBlockState());
            check(h,!DevilsSpatial.groundedPlayer(level,player,feet),"Obstructed body cannot revive");
            level.setBlockAndUpdate(base.above(),Blocks.AIR.defaultBlockState());
            level.setBlockAndUpdate(base,Blocks.STONE_STAIRS.defaultBlockState()
                    .setValue(net.minecraft.world.level.block.StairBlock.FACING,net.minecraft.core.Direction.NORTH));
            feet=Vec3.atLowerCornerOf(base).add(.5,1,.4);
            check(h,DevilsSpatial.groundedPlayer(level,player,feet),"Stair top supports a body that partly overhangs the lower step");
            level.setBlockAndUpdate(base,Blocks.AIR.defaultBlockState());
            check(h,!DevilsSpatial.groundedPlayer(level,player,feet),"Removed stair is not support");
            level.setBlockAndUpdate(base,Blocks.STONE.defaultBlockState());
            level.setBlockAndUpdate(base.above(),Blocks.WATER.defaultBlockState());
            check(h,!DevilsSpatial.groundedPlayer(level,player,feet),"Flooded feet are rejected");
        } finally { saved.forEach(level::setBlockAndUpdate); }
    }
}
