package kim.biryeong.destiny.strike.devils;

import com.mojang.math.Transformation;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import org.joml.Vector3f;
import java.util.*;

/** Authored steel ammo cases with special/heavy colour strips. Never modifies terrain or containers. */
public final class DevilsSupplyStations implements AutoCloseable {
    private final ServerLevel level;
    private final Map<DevilsPlan.Zone, Vec3> positions = new EnumMap<>(DevilsPlan.Zone.class);
    private final List<Display.BlockDisplay> displays = new ArrayList<>();
    private boolean closed;
    public DevilsSupplyStations(ServerLevel level) { this.level=level; }
    public boolean prepare() {
        if(closed)return false;
        for(var zone:DevilsPlan.Zone.values()) {
            if(positions.containsKey(zone))continue;
            var at=locate(zone);
            if(at.isEmpty())return false;
            var p=at.get();
            try {
                part(p.add(-.4,0,-.3),new Vector3f(.8f,.55f,.6f),Blocks.IRON_BLOCK.defaultBlockState());
                part(p.add(-.34,.56,-.24),new Vector3f(.24f,.035f,.48f),colour("lime_concrete"));
                part(p.add(.10,.56,-.24),new Vector3f(.24f,.035f,.48f),colour("purple_concrete"));
                positions.put(zone,p);
            } catch(RuntimeException e) { close();throw e; }
        }
        return true;
    }
    private void part(Vec3 at,Vector3f scale,BlockState state) {
        var display=new Display.BlockDisplay(EntityTypes.BLOCK_DISPLAY,level);
        display.setPos(at);display.setBlockState(state);display.setNoGravity(true);
        display.setTransformation(new Transformation(new Vector3f(),null,scale,null));
        if(!level.addFreshEntity(display))throw new IllegalStateException("Supply display admission failed");
        displays.add(display);
    }
    private static BlockState colour(String id) {
        return net.minecraft.core.registries.BuiltInRegistries.BLOCK.getValue(
                net.minecraft.resources.Identifier.withDefaultNamespace(id)).defaultBlockState();
    }
    private Optional<Vec3> locate(DevilsPlan.Zone zone) {
        var origin=DevilsWorldBuild.origin(zone);
        var entry=DevilsMaps.anchor(zone,zone.name()+".IN",origin).pos();
        var seats=new ArrayList<Vec3>();
        for(int i=0;i<3;i++)seats.add(DevilsMaps.anchor(zone,zone.name()+".IN."+i,origin).pos());
        for(int radius=4;radius<=7;radius++)for(int i=0;i<16;i++) {
            double angle=i*Math.PI/8;
            var top=entry.add(Math.cos(angle)*radius,3,Math.sin(angle)*radius);
            if(!level.hasChunkAt(BlockPos.containing(top)))continue;
            var hit=level.clip(new ClipContext(top,top.add(0,-6,0),ClipContext.Block.COLLIDER,
                    ClipContext.Fluid.NONE,CollisionContext.empty()));
            if(hit.getType()!=HitResult.Type.BLOCK)continue;
            var at=hit.getLocation();
            if(seats.stream().anyMatch(s->s.distanceToSqr(at)<4))continue;
            var box=new AABB(at.x-.4,at.y+.01,at.z-.3,at.x+.4,at.y+.6,at.z+.3);
            if(!DevilsMaps.contains(zone,origin,new Vec3(box.minX,box.minY,box.minZ))
                    ||!DevilsMaps.contains(zone,origin,new Vec3(box.maxX,box.maxY,box.maxZ))
                    ||level.getBlockCollisions(null,box).iterator().hasNext()||!DevilsSpatial.supported(level,box))continue;
            if(!level.getFluidState(BlockPos.containing(at)).isEmpty())continue;
            return Optional.of(at);
        }
        return Optional.empty();
    }
    boolean lookingAt(ServerPlayer p,DevilsPlan.Zone zone) {
        var at=positions.get(zone);
        if(closed||at==null||p.level()!=level||!p.isAlive()||p.isSpectator())return false;
        var center=at.add(0,.3,0);var toward=center.subtract(p.getEyePosition());
        if(!inReach(p.position(),at,p.getLookAngle(),toward))return false;
        return level.clip(new ClipContext(p.getEyePosition(),center,ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE,p)).getType()==HitResult.Type.MISS;
    }
    static boolean inReach(Vec3 feet,Vec3 at,Vec3 look,Vec3 toward) {
        return Double.isFinite(feet.distanceToSqr(at))&&feet.distanceToSqr(at)<=9
                &&toward.lengthSqr()>1e-6&&look.dot(toward.normalize())>=.94;
    }
    @Override public void close(){if(closed)return;closed=true;displays.forEach(Display.BlockDisplay::discard);displays.clear();positions.clear();}
}
