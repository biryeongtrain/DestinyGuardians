package kim.biryeong.destiny.activity.presentation;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.AABB;

/** Read-only admission of one swept interval; no implicit chunk loads or flight authorization cache.
 * A coordinator must retain its own chunk leases and recheck before movement. */
public final class FlightTerrain {
    private static final long MAX_BLOCK_CELLS = 262_144;
    public enum Result { CLEAR, OUTSIDE, TOO_LARGE, UNLOADED, BLOCKED }
    interface Probe {
        boolean inside(AABB box);
        boolean loaded(int chunkX, int chunkZ);
        boolean collides(AABB box);
    }
    private FlightTerrain() { }

    public static Result inspect(ServerLevel level, AABB swept) {
        if (!level.getServer().isSameThread()) throw new IllegalStateException("Flight terrain check off server thread");
        return inspect(swept, new Probe() {
            public boolean inside(AABB box) {
                return level.getWorldBorder().isWithinBounds(box)
                        && !level.isOutsideBuildHeight((int)Math.floor(box.minY))
                        && !level.isOutsideBuildHeight((int)Math.floor(box.maxY));
            }
            public boolean loaded(int x, int z) { return level.hasChunkAt(new BlockPos(x<<4,64,z<<4)); }
            public boolean collides(AABB box) { return level.getBlockCollisions(null,box).iterator().hasNext(); }
        });
    }

    static Result inspect(AABB b, Probe probe) {
        for(double v:new double[]{b.minX,b.minY,b.minZ,b.maxX,b.maxY,b.maxZ})
            if(!Double.isFinite(v)||Math.abs(v)>30_000_000) return Result.OUTSIDE;
        if(!probe.inside(b)) return Result.OUTSIDE;
        // Minecraft's collision iterator also consults neighboring blocks for extended shapes.
        int x0=(int)Math.floor(b.minX)-1,x1=(int)Math.floor(b.maxX)+1;
        int y0=(int)Math.floor(b.minY)-1,y1=(int)Math.floor(b.maxY)+1;
        int z0=(int)Math.floor(b.minZ)-1,z1=(int)Math.floor(b.maxZ)+1;
        double cells=(double)(x1-x0+1)*(y1-y0+1)*(z1-z0+1);
        if(cells>MAX_BLOCK_CELLS) return Result.TOO_LARGE;
        for(int x=x0>>4;x<=x1>>4;x++) for(int z=z0>>4;z<=z1>>4;z++)
            if(!probe.loaded(x,z)) return Result.UNLOADED;
        return probe.collides(b)?Result.BLOCKED:Result.CLEAR;
    }
}
