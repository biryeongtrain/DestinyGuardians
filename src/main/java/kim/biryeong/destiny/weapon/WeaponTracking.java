package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.combat.Combat;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.*;
import java.util.*;

/** Tick-owned prelaunch lock. HUD/status/capture never advance it. All quantitative policy is local. */
public final class WeaponTracking {
    public enum Phase { IDLE, ACQUIRING, LOCKED }
    public record Status(boolean supported,Phase phase,UUID candidate,int ticks,int requiredTicks) {
        public UUID lockedTarget() {return phase==Phase.LOCKED?candidate:null;}
    }
    private static final Map<UUID,Session> SESSIONS=new HashMap<>();
    private static final int MAX_CANDIDATES=32;
    private static final double MIN_DOT=Math.cos(Math.toRadians(TrackingProfile.CONE_DEGREES));
    private static final class Session {
        final ServerPlayer owner;final ServerLevel level;final ItemStack stack;
        LivingEntity target;int samples,searchOffset;long last=Long.MIN_VALUE;
        Session(ServerPlayer p) {owner=p;level=p.level();stack=p.getMainHandItem();}
        void reset() {target=null;samples=0;searchOffset=0;last=Long.MIN_VALUE;}
    }
    /** Paid-shot snapshot. Never chooses a replacement; stow and later trait edits do not rewrite it. */
    static final class Flight {
        final ServerPlayer owner;final ServerLevel level;final LivingEntity target;final UUID id;
        boolean active=true;
        Flight(ServerPlayer p,LivingEntity target) {owner=p;level=p.level();this.target=target;id=target.getUUID();}
        Vec3 steer(Vec3 position,Vec3 velocity) {
            if(!active)return velocity;
            // LOS is acquisition-only. A wall still stops the ordinary actual segment trace.
            if(owner.level()!=level||target.level()!=level||!enemy(owner,target)
                    ||!finite(position)||!finite(target.position())
                    ||!level.hasChunkAt(BlockPos.containing(target.position()))
                    ||!level.getWorldBorder().isWithinBounds(BlockPos.containing(target.position()))) {
                active=false;return velocity;
            }
            var desired=point(target).subtract(position);
            var v=TrackingSteering.turn(new TrackingSteering.Vector(velocity.x,velocity.y,velocity.z),
                    new TrackingSteering.Vector(desired.x,desired.y,desired.z),TrackingProfile.TURN_RADIANS);
            return new Vec3(v.x(),v.y(),v.z());
        }
    }
    private WeaponTracking() {}
    private static long now(ServerPlayer p) {return p.level().getServer().getTickCount();}
    private static boolean enemy(ServerPlayer p,LivingEntity e) {
        return !e.isRemoved()&&e.isAlive()&&e.level()==p.level()&&Combat.isEnemy(p,e)&&!p.isAlliedTo(e)
                &&!(e instanceof TamableAnimal tame&&tame.isTame());
    }
    private static boolean finite(Vec3 v) {return Double.isFinite(v.x)&&Double.isFinite(v.y)&&Double.isFinite(v.z);}
    private static Vec3 point(LivingEntity e) {return e.getBoundingBox().getCenter();}
    private static boolean input(ServerPlayer p) {return TrackingProfile.supports(p.getMainHandItem())&&WeaponAiming.trackingInput(p);}
    private static boolean visible(ServerPlayer p,LivingEntity target) {
        if(!enemy(p,target))return false;
        Vec3 from=p.getEyePosition(),to=point(target),delta=to.subtract(from);
        double distance=delta.length();
        if(!finite(from)||!finite(to)||distance<1e-6||distance>TrackingProfile.RANGE
                ||p.getLookAngle().dot(delta.scale(1/distance))<MIN_DOT
                ||!WeaponWavefront.loadedSegment(p.level(),from,to))return false;
        return p.level().clip(new ClipContext(from,to,ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,p)).getType()==HitResult.Type.MISS;
    }
    private static LivingEntity candidate(ServerPlayer p,Session s) {
        var from=p.getEyePosition();
        // Entity queries enumerate loaded entities; never request/get a missing chunk.
        var candidates=p.level().getEntitiesOfClass(LivingEntity.class,new AABB(from,from).inflate(TrackingProfile.RANGE),
                        e->enemy(p,e)&&finite(point(e))&&point(e).distanceToSqr(from)<=TrackingProfile.RANGE*TrackingProfile.RANGE
                                &&p.getLookAngle().dot(point(e).subtract(from).normalize())>=MIN_DOT)
                .stream().sorted(Comparator.comparingDouble((LivingEntity e)->-p.getLookAngle().dot(point(e).subtract(from).normalize()))
                        .thenComparingDouble(e->point(e).distanceToSqr(from)).thenComparing(LivingEntity::getUUID)).toList();
        if(candidates.isEmpty()) {s.searchOffset=0;return null;}
        int start=Math.floorMod(s.searchOffset,candidates.size()),count=Math.min(MAX_CANDIDATES,candidates.size());
        // Rotate the bounded LOS budget after an empty window: a dense occluded prefix cannot
        // permanently starve a visible off-axis target. A valid existing lock never rescans.
        for(int i=0;i<count;i++) {
            var target=candidates.get((start+i)%candidates.size());
            if(visible(p,target)) {s.searchOffset=0;return target;}
        }
        s.searchOffset=(start+count)%candidates.size();return null;
    }
    public static void update(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());
        if(s!=null&&(s.owner!=p||s.stack!=p.getMainHandItem()||s.level!=p.level())) {SESSIONS.remove(p.getUUID(),s);s=null;}
        if(!TrackingProfile.supports(p.getMainHandItem())||!p.isAlive()||p.isRemoved()||p.hasDisconnected()||p.isSpectator()) {
            cleanup(p);return;
        }
        if(s==null) {s=new Session(p);SESSIONS.put(p.getUUID(),s);}
        if(!input(p)) {s.reset();return;}
        long tick=now(p);
        if(s.last==tick)return;
        if(s.last!=tick-1) {s.target=null;s.samples=0;}
        var target=s.target!=null&&visible(p,s.target)?s.target:candidate(p,s);
        if(target!=s.target) {s.target=target;s.samples=0;}
        s.samples=target==null?0:Math.min(TrackingProfile.ACQUIRE_TICKS,s.samples+1);s.last=tick;
    }
    /** Also advances ADS-only embedded actors once per global server tick, without firing a dummy round. */
    static void tick(MinecraftServer server) {
        for(var s:List.copyOf(SESSIONS.values()))if(s.level.getServer()==server) {
            WeaponAiming.tick(s.owner);update(s.owner);
        }
    }
    public static Status status(ServerPlayer p) {
        boolean supported=TrackingProfile.supports(p.getMainHandItem());
        var idle=new Status(supported,Phase.IDLE,null,0,TrackingProfile.ACQUIRE_TICKS);
        var s=SESSIONS.get(p.getUUID());
        if(s==null||s.owner!=p||s.level!=p.level()||s.stack!=p.getMainHandItem()||!input(p)
                ||s.target==null||s.samples==0||now(p)<s.last||now(p)-s.last>1||!visible(p,s.target))return idle;
        return new Status(true,s.samples>=TrackingProfile.ACQUIRE_TICKS?Phase.LOCKED:Phase.ACQUIRING,
                s.target.getUUID(),s.samples,TrackingProfile.ACQUIRE_TICKS);
    }
    static Flight capture(ServerPlayer p) {
        var status=status(p);
        if(status.lockedTarget()==null)return null;
        var s=SESSIONS.get(p.getUUID());return new Flight(p,s.target);
    }
    public static void invalidate(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());if(s!=null&&s.owner==p)s.reset();
    }
    public static void edited(ItemStack stack) {
        for(var s:SESSIONS.values())if(s.stack==stack)s.reset();
    }
    public static void cleanup(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());if(s!=null&&s.owner==p)SESSIONS.remove(p.getUUID(),s);
    }
    public static void clear() {SESSIONS.clear();}
}
