package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.Fx;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.*;
import java.util.*;

/** Bounded shot-owned ground wave. No global sessions, chunk loads, terrain edits, ammo or ability calls.
 * Separate lateral lanes stop at solid walls/unsupported gaps; 0.25-block terrain samples follow collision shapes.
 * These block-terrain/height/speed rules are authored Minecraft adaptation, not original mesh physics.
 */
final class WeaponWavefront {
    record Contact(LivingEntity target, Vec3 point) {}
    private record Segment(Vec3 from,Vec3 to) {}
    private static final double SAMPLE=.25, EPS=.04;
    private static final int MAX_TARGETS=128;
    private final ServerPlayer owner;
    private final WaveFrameProfile.Profile profile;
    private final Vec3 forward;
    private final Vec3[] tips;
    private final double laneWidth;
    private final int color;
    private final boolean stasis;
    private final Set<LivingEntity> touched=Collections.newSetFromMap(new IdentityHashMap<>());
    private double distance;
    private int age;
    private final kim.biryeong.destiny.fx.WaveCrestVfx visual;

    WeaponWavefront(ServerPlayer owner,WaveFrameProfile.Profile profile,Vec3 origin,Vec3 direction,
                    WeaponCharacteristics.Damage element) {
        this.owner=owner;this.profile=profile;
        forward=new Vec3(direction.x,0,direction.z).normalize();
        if(forward.lengthSqr()<.99)throw new IllegalArgumentException("Wave needs horizontal direction");
        int lanes=(int)Math.ceil(profile.width()/.5);tips=new Vec3[lanes];laneWidth=profile.width()/lanes;
        Vec3 right=new Vec3(-forward.z,0,forward.x);
        for(int i=0;i<lanes;i++) {
            double offset=(i+.5)*laneWidth-profile.width()/2;
            // Reach every lateral lane FROM the impact. Independent far-side probes could
            // otherwise seed a new wave across a wall or an unsupported lateral gap.
            Vec3 previous=support(origin,origin.y);
            int samples=Math.max(1,(int)Math.ceil(Math.abs(offset)/SAMPLE));
            for(int sample=1;sample<=samples&&previous!=null;sample++) {
                Vec3 desired=origin.add(right.scale(offset*sample/samples));
                Vec3 next=support(desired,previous.y-EPS);
                previous=next!=null&&traversable(previous,next)?next:null;
            }
            tips[i]=previous;
        }
        color=element.color();stasis=element==WeaponCharacteristics.Damage.STASIS;
        visual=new kim.biryeong.destiny.fx.WaveCrestVfx(owner,origin,forward,stasis,laneWidth,lanes);
    }
    /** Conservative supercover: a tiny diagonal can cross a third chunk between its endpoints.
     * Checking every column in the segment rectangle forbids clip() from loading an unchecked corner.
     */
    static boolean loadedSegment(net.minecraft.server.level.ServerLevel level,Vec3 from,Vec3 to) {
        // BlockGetter.traverseBlocks extends each endpoint by 1e-7 * axis displacement.
        // Fixed absolute padding alone misses adjacent chunks on longer near-boundary rays.
        Vec3 padding=to.subtract(from).scale(1e-7);
        Vec3 a=from.subtract(padding),b=to.add(padding);
        int minX=net.minecraft.util.Mth.floor(Math.min(a.x,b.x)-1e-7)>>4;
        int maxX=net.minecraft.util.Mth.floor(Math.max(a.x,b.x)+1e-7)>>4;
        int minZ=net.minecraft.util.Mth.floor(Math.min(a.z,b.z)-1e-7)>>4;
        int maxZ=net.minecraft.util.Mth.floor(Math.max(a.z,b.z)+1e-7)>>4;
        for(int x=minX;x<=maxX;x++)for(int z=minZ;z<=maxZ;z++)
            if(!level.hasChunkAt(new BlockPos(x*16,net.minecraft.util.Mth.floor(from.y),z*16)))return false;
        return level.getWorldBorder().isWithinBounds(BlockPos.containing(from))
                &&level.getWorldBorder().isWithinBounds(BlockPos.containing(to));
    }
    private boolean loaded(Vec3 from,Vec3 to) { return loadedSegment(owner.level(),from,to); }
    private Vec3 support(Vec3 point,double oldY) {
        Vec3 above=new Vec3(point.x,oldY+profile.stepUp()+EPS,point.z);
        Vec3 below=new Vec3(point.x,oldY-profile.stepDown()-EPS,point.z);
        if(!loaded(above,below))return null;
        var hit=owner.level().clip(new ClipContext(above,below,ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,owner));
        if(hit.getType()!=HitResult.Type.BLOCK||hit.getDirection()!=Direction.UP)return null;
        double y=hit.getLocation().y;
        if(y-oldY>profile.stepUp()+.001||oldY-y>profile.stepDown()+.001)return null;
        return new Vec3(point.x,y+EPS,point.z);
    }
    private boolean clear(Vec3 from,Vec3 to) {
        if(!loaded(from,to))return false;
        return owner.level().clip(new ClipContext(from,to,ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,owner))
                .getType()==HitResult.Type.MISS;
    }
    private boolean traversable(Vec3 from,Vec3 to) {
        // Lift the traversal ray over an admitted low step; never penetrate a full-block riser.
        double crest=Math.max(from.y,to.y)+EPS;
        return clear(new Vec3(from.x,crest,from.z),new Vec3(to.x,crest,to.z));
    }
    boolean alive() { return distance<profile.length()&&age<100&&Arrays.stream(tips).anyMatch(Objects::nonNull); }
    void close() {visual.close();}
    List<Contact> advance() {
        if(!alive())return List.of();
        age++;
        var segments=new ArrayList<Segment>();
        double remaining=Math.min(profile.speed(),profile.length()-distance);
        while(remaining>1e-6) {
            double step=Math.min(SAMPLE,remaining);
            for(int i=0;i<tips.length;i++) {
                var previous=tips[i];if(previous==null)continue;
                var desired=previous.add(forward.scale(step));
                var next=support(desired,previous.y-EPS);
                if(next==null||!traversable(previous,next)){tips[i]=null;continue;}
                segments.add(new Segment(previous,next));tips[i]=next;
            }
            distance+=step;remaining-=step;
        }
        visual.update(tips,age,profile.length()-distance);
        if(segments.isEmpty())return List.of();
        double minX=Double.POSITIVE_INFINITY,minY=minX,minZ=minX,maxX=Double.NEGATIVE_INFINITY,maxY=maxX,maxZ=maxX;
        for(var segment:segments) {
            minX=Math.min(minX,Math.min(segment.from.x,segment.to.x));maxX=Math.max(maxX,Math.max(segment.from.x,segment.to.x));
            minZ=Math.min(minZ,Math.min(segment.from.z,segment.to.z));maxZ=Math.max(maxZ,Math.max(segment.from.z,segment.to.z));
            minY=Math.min(minY,Math.min(segment.from.y,segment.to.y));maxY=Math.max(maxY,Math.max(segment.from.y,segment.to.y));
        }
        var bounds=new AABB(minX-laneWidth,minY-EPS,minZ-laneWidth,maxX+laneWidth,maxY+profile.height(),maxZ+laneWidth);
        var targets=owner.level().getEntitiesOfClass(LivingEntity.class,bounds,
                e->Combat.isEnemy(owner,e)&&!owner.isAlliedTo(e)&&!(e instanceof TamableAnimal tame&&tame.isTame())&&!touched.contains(e))
                .stream().sorted(Comparator.comparingDouble((LivingEntity e)->e.getBoundingBox().getCenter().distanceToSqr(segments.getFirst().from))
                        .thenComparing(LivingEntity::getUUID)).limit(MAX_TARGETS).toList();
        var result=new ArrayList<Contact>();
        for(var target:targets) {
            if(touched.size()>=MAX_TARGETS)break;
            var b=target.getBoundingBox();
            for(var segment:segments) {
                if(!WaveFrameProfile.intersects(forward.x,forward.z,segment.from.x,segment.from.y-EPS,segment.from.z,
                        segment.to.x,segment.to.y-EPS,segment.to.z,laneWidth,profile.height(),b.minX,b.minY,b.minZ,b.maxX,b.maxY,b.maxZ))continue;
                var center=b.getCenter();
                Vec3 point=new Vec3(center.x,Math.clamp(segment.to.y+.35,b.minY+.001,b.maxY-.001),center.z);
                if(!clear(segment.to.add(0,.12,0),point))continue;
                touched.add(target);result.add(new Contact(target,point));break;
            }
        }
        // The model is the moving body. Sparse native sparks are accents, or a budget fallback.
        for(int i=0;i<tips.length;i++)if(tips[i]!=null&&(!visual.visible()||age%4==0&&i%2==0)) {
            var tip=tips[i];
            if(!visual.visible())owner.level().sendParticles(Fx.dust(color,1.1f),tip.x,tip.y+.2,tip.z,1,0,.1,0,0);
            owner.level().sendParticles(stasis?ParticleTypes.SNOWFLAKE:ParticleTypes.PORTAL,tip.x,tip.y+.3,tip.z,1,0,.1,0,.01);
        }
        return result;
    }
}
