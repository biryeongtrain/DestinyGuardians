package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.combat.Combat;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.*;
import java.util.*;

/** Loaded-world sword geometry. No ammo/energy mutation, delayed actions, target lock or forced camera. */
public final class SwordMelee {
    private SwordMelee() {}
    private static Vec3 body(ServerPlayer player) { return player.position().add(0,.9,0); }
    static Vec3 point(LivingEntity target) { return target.position().add(0,target.getBbHeight()*.5,0); }
    private static Vec3 forward(ServerPlayer player) { return Vec3.directionFromRotation(0,player.getYRot()); }
    private static boolean enemy(ServerPlayer player,LivingEntity target) {
        return Combat.isEnemy(player,target)&&!player.isAlliedTo(target)
                &&!(target instanceof TamableAnimal animal&&animal.isTame());
    }
    private static List<LivingEntity> candidates(ServerPlayer player,boolean lunge) { return candidates(player,lunge,1); }
    private static List<LivingEntity> candidates(ServerPlayer player,boolean lunge,double scale) {
        double range=Math.min(8,(lunge?SwordArc.LUNGE_RANGE:SwordArc.LIGHT_RANGE)*scale); // SwordArc.inside cap
        double height=lunge?SwordArc.LUNGE_HEIGHT:SwordArc.LIGHT_HEIGHT;
        double cosine=lunge?SwordArc.LUNGE_COS:SwordArc.LIGHT_COS;
        Vec3 origin=body(player),forward=forward(player);
        // Body boxes can intersect this search even if the entity's feet are outside it;
        // the precise authored cone/height test below remains authoritative.
        return player.level().getEntitiesOfClass(LivingEntity.class,
                AABB.ofSize(origin,(range+1)*2,(height+2)*2,(range+1)*2),target->{
                    if(!enemy(player,target))return false;
                    Vec3 delta=point(target).subtract(origin);
                    return SwordArc.inside(forward.x,forward.z,delta.x,delta.y,delta.z,range,cosine,height);
                }).stream().sorted(Comparator.comparingDouble((LivingEntity e)->point(e).distanceToSqr(origin))
                        .thenComparing(LivingEntity::getUUID)).limit(SwordArc.MAX_CANDIDATES).toList();
    }
    private static boolean loaded(ServerPlayer player,AABB box) {
        var level=player.level();
        return level.hasChunkAt(BlockPos.containing(box.minX,box.minY,box.minZ))
                &&level.hasChunkAt(BlockPos.containing(box.minX,box.minY,box.maxZ))
                &&level.hasChunkAt(BlockPos.containing(box.maxX,box.minY,box.minZ))
                &&level.hasChunkAt(BlockPos.containing(box.maxX,box.minY,box.maxZ));
    }
    private static boolean visible(ServerPlayer player,LivingEntity target) {
        if(!loaded(player,target.getBoundingBox())||!player.level().getWorldBorder().isWithinBounds(target.getBoundingBox()))return false;
        Vec3 from=player.getEyePosition(),to=point(target);
        int steps=Math.max(1,(int)Math.ceil(from.distanceTo(to)*2));
        for(int i=0;i<=steps;i++)
            if(!player.level().hasChunkAt(BlockPos.containing(from.lerp(to,(double)i/steps))))return false;
        var wall=player.level().clip(new ClipContext(from,to,
                ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,player));
        return wall.getType()==HitResult.Type.MISS; // An exact endpoint wall tie belongs to the wall.
    }
    static List<LivingEntity> cleave(ServerPlayer player) {
        return candidates(player,false).stream().filter(target->visible(player,target)).limit(SwordArc.MAX_HITS).toList();
    }
    /** Closest currently visible, forward legal target; never a saved lock or movement without an accepted light. */
    static void lunge(ServerPlayer player) { lunge(player,SwordArc.STEP); }
    /** Lunge toward the closest visible legal target, otherwise step forward along the body yaw. */
    public static void lunge(ServerPlayer player,double fallback) {
        for(var target:candidates(player,true)) {
            if(!visible(player,target))continue;
            Vec3 delta=target.position().subtract(player.position());
            double distance=Math.hypot(delta.x,delta.z);
            move(player,new Vec3(delta.x,0,delta.z),Math.max(SwordArc.lungeDistance(distance),Math.min(fallback,Math.max(0,distance-SwordArc.LUNGE_STOP))));
            return;
        }
        move(player,forward(player),fallback);
    }
    /** W323 Valiant Charge: acquisition range and lunge distance scaled; long moves are split into legal steps. */
    public static void lunge(ServerPlayer player,double fallback,double scale) {
        if(!Double.isFinite(scale)||scale<=1||scale>2) { lunge(player,fallback); return; }
        for(var target:candidates(player,true,scale)) {
            if(!visible(player,target))continue;
            Vec3 delta=target.position().subtract(player.position());
            double distance=Math.hypot(delta.x,delta.z);
            double reach=Math.min(Math.max(0,distance-SwordArc.LUNGE_STOP),SwordArc.LUNGE_MAX*scale);
            moveFar(player,new Vec3(delta.x,0,delta.z),Math.max(reach,Math.min(fallback,Math.max(0,distance-SwordArc.LUNGE_STOP))));
            return;
        }
        moveFar(player,forward(player),fallback*scale);
    }
    private static void moveFar(ServerPlayer player,Vec3 direction,double distance) {
        if(!Double.isFinite(distance)||distance<=0)return;
        double first=Math.min(2,distance);
        Vec3 start=player.position();
        move(player,direction,first);
        if(distance>first&&player.position().distanceToSqr(start)>=first*first-1e-3)move(player,direction,Math.min(2,distance-first));
    }
    /** Horizontal sampled displacement; preserves Y, view and native delta velocity. No chunk loads. */
    static void move(ServerPlayer player,Vec3 direction,double distance) {
        if(!Double.isFinite(distance)||distance<=0||distance>2||!Double.isFinite(direction.x)||!Double.isFinite(direction.z))return;
        Vec3 step=new Vec3(direction.x,0,direction.z);
        if(step.lengthSqr()<1e-8)return;
        Vec3 start=player.position(),end=start,unit=step.normalize();
        int steps=(int)Math.ceil(distance/.1);
        for(int i=1;i<=steps;i++) {
            Vec3 next=start.add(unit.scale(Math.min(distance,i*.1)));
            AABB box=player.getBoundingBox().move(next.subtract(start));
            if(!loaded(player,box)||!player.level().getWorldBorder().isWithinBounds(box)
                    ||!player.level().noCollision(player,box))break;
            end=next;
        }
        if(end.distanceToSqr(start)>1e-8) {
            // Native teleport uses relative-zero delta on the wire (preserve the
            // client's real velocity), but its server base is getKnownMovement(),
            // not getDeltaMovement(). Keep our existing server velocity as well;
            // otherwise a lunge can erase falling motion before the next move packet.
            Vec3 velocity=player.getDeltaMovement();
            player.teleportTo(end.x,end.y,end.z);
            player.setDeltaMovement(velocity);
        }
    }
}
