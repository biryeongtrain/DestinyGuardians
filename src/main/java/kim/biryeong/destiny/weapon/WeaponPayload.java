package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.combat.Combat;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.*;
import java.util.*;

/** One immediate emission's explosion, not a projectile or a proc that recursively fires another shot.
 * The caller applies physical damage first, then these nonprecision contacts with the same paid source.
 * Selection never writes item state, invents ammunition, modifies terrain, or creates fire. */
public final class WeaponPayload {
    public static final int MAX_CONTACTS=128;
    public static final class Token {
        public static final Token NONE=new Token(null,null,null,null);
        private final ServerPlayer owner;
        private final ServerLevel level;
        private final ItemStack stack;
        private final WeaponCatalog.Entry entry;
        private boolean consumed;
        private Token(ServerPlayer owner,ServerLevel level,ItemStack stack,WeaponCatalog.Entry entry) {
            this.owner=owner;this.level=level;this.stack=stack;this.entry=entry;
        }
        public boolean active() {return owner!=null;}
    }
    public record Contact(LivingEntity target,Vec3 point,float fraction) {}
    private WeaponPayload() {}
    private static boolean ownerValid(ServerPlayer p) {
        return p!=null&&p.isAlive()&&!p.isRemoved()&&!p.isSpectator()&&!p.hasDisconnected()
                &&!AbilityService.inSuper(p)&&WeaponLoadout.canUse(p);
    }
    public static Token capture(ServerPlayer p,WeaponCatalog.Entry entry,WeaponProfile profile) {
        if(!ownerValid(p)||profile.mode()!=WeaponProfile.Mode.HITSCAN||profile.burst()!=1||profile.pellets()!=1
                ||WeaponItems.entry(p.getMainHandItem()).filter(entry::equals).isEmpty()
                ||WeaponPerks.selected(p.getMainHandItem(),PayloadProfile.ID).isEmpty())return Token.NONE;
        return new Token(p,p.level(),p.getMainHandItem(),entry);
    }
    private static boolean valid(ServerPlayer p,Token token) {
        if(token==null||token==Token.NONE||token.consumed||token.owner!=p||token.level!=p.level()||!ownerValid(p)
                ||WeaponItems.entry(token.stack).filter(token.entry::equals).isEmpty()
                ||WeaponPerks.selected(token.stack,PayloadProfile.ID).isEmpty())return false;
        for(int i=0;i<p.getInventory().getContainerSize();i++)if(p.getInventory().getItem(i)==token.stack)return true;
        return false;
    }
    private static boolean finite(Vec3 p) {return p!=null&&Double.isFinite(p.x)&&Double.isFinite(p.y)&&Double.isFinite(p.z);}
    private static boolean enemy(ServerPlayer p,LivingEntity target) {
        return Combat.isEnemy(p,target)&&!p.isAlliedTo(target)&&!(target instanceof TamableAnimal tame&&tame.isTame());
    }
    private static Vec3 nearest(AABB b,Vec3 p) {
        return new Vec3(Math.clamp(p.x,b.minX,b.maxX),Math.clamp(p.y,b.minY,b.maxY),Math.clamp(p.z,b.minZ,b.maxZ));
    }
    /** Exactly once per captured shot. A miss does not detonate, while a collider hit does not require HP loss.
     * Block faces are offset outward 1/64 block to keep native clip from starting inside the collider.
     * Nonprimary range/attenuation use the nearest AABB point; the actual struck body gets full explosion.
     * These geometry, attenuation and cap choices are explicit local PvE rules. */
    public static List<Contact> detonate(ServerPlayer p,Token token,HitResult hit) {
        return detonate(p, token, hit, null);
    }
    /** The already-confirmed hitscan victim retains its direct explosion at the sampled body. */
    public static List<Contact> detonate(ServerPlayer p,Token token,HitResult hit,AABB primaryBody) {
        if(!valid(p,token))return List.of();
        token.consumed=true;
        if(hit==null||hit.getType()==HitResult.Type.MISS||!finite(hit.getLocation()))return List.of();
        Vec3 center=hit.getLocation();
        if(center.distanceToSqr(p.getEyePosition())>(WeaponBallistics.MAX_TRACE+1)*(WeaponBallistics.MAX_TRACE+1))return List.of();
        if(hit instanceof BlockHitResult block) {
            var face=block.getDirection();center=center.add(face.getStepX()/64.0,face.getStepY()/64.0,face.getStepZ()/64.0);
        }
        if(!WeaponWavefront.loadedSegment(token.level,p.getEyePosition(),center))return List.of();
        final Vec3 origin=center;
        LivingEntity primary=hit instanceof EntityHitResult entity&&entity.getEntity() instanceof LivingEntity living?living:null;
        var candidates=token.level.getEntitiesOfClass(LivingEntity.class,AABB.ofSize(origin,PayloadProfile.radius()*2,PayloadProfile.radius()*2,PayloadProfile.radius()*2).inflate(1e-6),
                target->enemy(p,target)&&nearest(target.getBoundingBox(),origin).distanceToSqr(origin)<=PayloadProfile.radius()*PayloadProfile.radius());
        if(primaryBody!=null && primary!=null && primary.level()==token.level && enemy(p,primary)
                && nearest(primaryBody,origin).distanceToSqr(origin)<=PayloadProfile.radius()*PayloadProfile.radius()
                && !candidates.contains(primary)) candidates.add(primary);
        var contacts=new ArrayList<Contact>();
        for(var target:candidates.stream().sorted(Comparator.<LivingEntity>comparingInt(e->e==primary?0:1)
                .thenComparingDouble(e->nearest(e.getBoundingBox(),origin).distanceToSqr(origin)).thenComparing(LivingEntity::getUUID)).toList()) {
            var point=nearest(target==primary&&primaryBody!=null?primaryBody:target.getBoundingBox(),origin);
            if(!WeaponWavefront.loadedSegment(token.level,origin,point))continue;
            if(target!=primary) {
                var wall=token.level.clip(new ClipContext(origin,point,ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,p));
                if(wall.getType()!=HitResult.Type.MISS&&origin.distanceToSqr(wall.getLocation())+1e-6<origin.distanceToSqr(point))continue;
            }
            float fraction=target==primary?1:PayloadProfile.splash(origin.distanceTo(point));
            if(fraction>0)contacts.add(new Contact(target,point,fraction));
            if(contacts.size()>=MAX_CONTACTS)break; // Occluded candidates never spend the contact budget.
        }
        // Existing native impact accents, not an extracted Explosive Payload effect or new audio.
        token.level.sendParticles(ParticleTypes.EXPLOSION,origin.x,origin.y,origin.z,1,0,0,0,0);
        token.level.sendParticles(ParticleTypes.CRIT,origin.x,origin.y,origin.z,6,.12,.12,.12,.04);
        return List.copyOf(contacts);
    }
}
