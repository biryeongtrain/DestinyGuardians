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
    public static void lunge(ServerPlayer player,double distance) { lunge(player,distance,1); }
    public static void lunge(ServerPlayer player,double distance,double scale) {
        sweepLunge(player,distance,scale,()->true,0,0,0,null);
    }
    /** Accepted attack owns a bounded native velocity lease; geometry follows actual movement ticks. */
    public static void sweepLunge(ServerPlayer player,double distance,double scale,
            java.util.function.BooleanSupplier valid,double reach,double cosine,double height,
            java.util.function.Consumer<LivingEntity> contact) {
        if(!Double.isFinite(distance)||distance<=0||distance>8)return;
        scale=Double.isFinite(scale)?Math.clamp(scale,1,2):1;
        Vec3 direction=forward(player);double budget=Math.min(8,distance*scale);
        for(var target:candidates(player,true,scale)) {
            if(!visible(player,target))continue;
            Vec3 delta=target.position().subtract(player.position());
            double horizontal=Math.hypot(delta.x,delta.z);
            budget=Math.min(budget,Math.max(0,horizontal-SwordArc.LUNGE_STOP));
            direction=new Vec3(delta.x,0,delta.z);break;
        }
        if(budget<=1e-5) {
            if(contact!=null)for(var target:kim.biryeong.destiny.combat.MeleeSweep.frontal(player,reach,cosine,height))contact.accept(target);
            return;
        }
        kim.biryeong.destiny.combat.MeleeLunge.start(player,direction,budget,valid,reach,cosine,height,contact);
    }
    /** Heavy dash shares the same finite velocity path, without target acquisition. */
    static void move(ServerPlayer player,Vec3 direction,double distance) {
        kim.biryeong.destiny.combat.MeleeLunge.start(player,direction,distance,()->true,0,0,0,null);
    }
}
