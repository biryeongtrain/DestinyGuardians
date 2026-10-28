package kim.biryeong.destiny.ability.titan;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ChunkAttachment;
import eu.pb4.polymer.virtualentity.api.elements.BlockDisplayElement;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import net.minecraft.core.component.DataComponents;
import net.minecraft.world.item.ItemDisplayContext;
import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Brightness;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.*;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.*;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import java.util.*;

/** Stationary, destructible ranged cover. Virtual display, never a world block or melee immunity. */
public final class TitanClassAbility extends Ability {
    private static final Map<UUID,Barrier> ACTIVE=new HashMap<>();
    private static boolean initialized;
    private static final double THICKNESS=.12;
    private static final class Barrier {
        final TitanAbilities.Context c;
        final Vec3 center,normal,right;
        final double width,height;
        final long until;
        final ElementHolder holder=new ElementHolder();
        double hp;
        Barrier(TitanAbilities.Context c,Vec3 center,Vec3 normal,double width,double height,int duration,double hp) {
            this.c=c;this.center=center;this.normal=normal;this.right=new Vec3(normal.z,0,-normal.x);
            this.width=width;this.height=height;this.hp=hp;until=c.level.getGameTime()+duration;
            var item=ClassAbilityEffects.item("titan/class_ability");
            var model=item.get(DataComponents.ITEM_MODEL);
            if(model!=null&&model.getNamespace().equals("destiny")&&model.getPath().equals("class_ability/titan/class_ability")) {
                // Authored energy VFX: canonical [0,0,0]..[16,16,16], anchor[8,8,8].
                // Scale the unit model to the same physical cover rectangle and thickness.
                var display=new ItemDisplayElement(item);
                display.setItemDisplayContext(ItemDisplayContext.NONE);
                display.setBillboardMode(Display.BillboardConstraints.FIXED);
                display.setScale(new Vector3f((float)width,(float)height,(float)THICKNESS));
                // Authored +Z -> fixed outward normal; compensate ItemDisplayRenderer's Y=PI.
                display.setLeftRotation(new Quaternionf().rotationTo(0,0,1,(float)normal.x,0,(float)normal.z).rotateY((float)Math.PI));
                display.setBrightness(new Brightness(15,15));holder.addElement(display);
            } else {
                var display=new BlockDisplayElement(Blocks.STAINED_GLASS.lightBlue().defaultBlockState());
                display.setScale(new Vector3f((float)width,(float)height,(float)THICKNESS));
                display.setLeftRotation(new Quaternionf().rotationTo(0,0,1,(float)normal.x,0,(float)normal.z));
                Vec3 corner=right.scale(-width/2).add(0,-height/2,0).add(normal.scale(-THICKNESS/2));
                display.setTranslation(new Vector3f((float)corner.x,(float)corner.y,(float)corner.z));
                display.setBrightness(new Brightness(15,15));holder.addElement(display);
            }
            ChunkAttachment.ofTicking(holder,c.level,center);
            holder.startWatching(c.owner);
        }
        boolean valid() {return hp>0&&c.valid()&&c.level.getGameTime()<until;}
        Vec3 intersection(Vec3 from,Vec3 to) {
            double a=from.subtract(center).dot(normal),b=to.subtract(center).dot(normal);
            if(a<=1e-5||b>0||a-b<1e-7)return null;
            Vec3 hit=from.add(to.subtract(from).scale(a/(a-b))),rel=hit.subtract(center);
            return Math.abs(rel.dot(right))<=width/2&&Math.abs(rel.y)<=height/2?hit:null;
        }
        boolean spend(double amount) {
            hp-=amount;
            if(hp<=0)remove(c.owner);
            return true; // Last hit is fully blocked; boolean Fabric event cannot pass an overflow portion.
        }
    }
    public TitanClassAbility() {super(TitanAbilities.CLASS_ABILITY,GuardianClass.TITAN,AbilitySlot.CLASS_ABILITY,Element.KINETIC,101.3,"높은 방벽");}
    static void init() {
        if(initialized)return;initialized=true;
        ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity,source,amount)->!(entity instanceof ServerPlayer p)||allowDamage(p,source,amount));
    }
    @Override public boolean activate(ServerPlayer p) {
        if(!TitanAbilities.eligible(p)||!p.onGround()||p.isInWater()||p.isInLava()||p.isPassenger()||p.isSleeping()||p.isFallFlying())return false;
        Vec3 normal=Motion.horizontalLook(p);
        double width=TitanAbilities.value(this,"width",3,1,5),height=TitanAbilities.value(this,"height",2.4,1,3);
        Vec3 center=p.position().add(normal.scale(1.35)).add(0,height/2,0);
        // Read-only support and full rectangle clearance, including obstruction between caster and cover.
        var support=p.level().clip(new ClipContext(center.add(0,-height/2+.15,0),center.add(0,-height/2-.4,0),
                ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,p));
        Vec3 right=new Vec3(normal.z,0,-normal.x);
        AABB box=AABB.ofSize(center.add(0,.01,0),Math.abs(right.x)*width+Math.abs(normal.x)*THICKNESS,
                height-.02,Math.abs(right.z)*width+Math.abs(normal.z)*THICKNESS);
        if(support.getType()!=HitResult.Type.BLOCK||!p.level().noCollision(p,box)
                ||p.level().clip(new ClipContext(p.getEyePosition(),center,ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,p)).getType()!=HitResult.Type.MISS)return false;
        var c=TitanAbilities.context(p);if(!c.valid())return false;
        Barrier next=new Barrier(c,center,normal,width,height,TitanAbilities.ticks(this,"duration_ticks",400,600),
                TitanAbilities.value(this,"health",80,1,500));
        remove(p);ACTIVE.put(p.getUUID(),next);
        ClassAbilityEffects.sound(p,elementFor(p),"class.cast");return true;
    }
    private static Element elementFor(ServerPlayer p) {
        return AbilityService.equipped(p,AbilitySlot.SUPER).map(Ability::element).orElse(Element.ARC);
    }
    private static boolean hostile(ServerPlayer p,Entity e) {
        return e instanceof Mob mob&&mob.level()==p.level()&&TitanAbilities.enemy(p,mob);
    }
    private static boolean projectileThreat(ServerPlayer p,Projectile projectile) {
        return projectile.getOwner()==null||hostile(p,projectile.getOwner());
    }
    private static boolean ranged(DamageSource source) {
        return !source.is(DamageTypeTags.BYPASSES_SHIELD)
                &&(source.is(DamageTypeTags.IS_PROJECTILE)||source.is(DamageTypeTags.IS_EXPLOSION)
                ||source.getDirectEntity() instanceof Projectile);
    }
    /** Real event path also exposed for deterministic server fixtures; returns true to let damage through. */
    public static boolean allowDamage(ServerPlayer victim,DamageSource source,float amount) {
        if(!Float.isFinite(amount)||amount<=0||!ranged(source))return true;
        Vec3 origin=source.getSourcePosition();
        Entity direct=source.getDirectEntity();
        if(!hostile(victim,source.getEntity())&&!(source.getEntity()==null&&direct instanceof Projectile projectile
                &&projectileThreat(victim,projectile)))return true;
        if(direct!=null&&direct.level()!=victim.level())return true;
        Vec3 to=victim.getBoundingBox().getCenter();
        for(Barrier b:List.copyOf(ACTIVE.values())) {
            if(!b.valid()) {remove(b.c.owner);continue;}
            if(b.c.level!=victim.level())continue;
            Vec3 from=origin;
            // A fast arrow may already be touching its victim. Reconstruct its incoming segment,
            // rather than using a distant shooter's position and incorrectly blocking a curved shot.
            if(direct instanceof Projectile projectile&&from!=null&&b.intersection(from,to)==null) {
                Vec3 v=projectile.getDeltaMovement();
                if(v.lengthSqr()>1e-8)from=projectile.position().subtract(v.normalize().scale(v.length()+2));
            }
            if(from!=null&&b.intersection(from,to)!=null)return !b.spend(amount);
        }
        return true;
    }
    static void tick(MinecraftServer server) {
        for(Barrier b:List.copyOf(ACTIVE.values())) {
            if(b.c.level.getServer()!=server)continue;
            if(!b.valid()) {remove(b.c.owner);continue;}
            // Native entities only; virtual SimProjectile visuals have no world collision entity.
            for(Projectile arrow:b.c.level.getEntitiesOfClass(Projectile.class,AABB.ofSize(b.center,32,16,32))) {
                if(arrow.isRemoved()||!projectileThreat(b.c.owner,arrow))continue;
                Vec3 from=new Vec3(arrow.xo,arrow.yo,arrow.zo),to=arrow.position();
                Vec3 hit=b.intersection(from,to);
                if(hit==null) {from=arrow.position();to=from.add(arrow.getDeltaMovement());hit=b.intersection(from,to);}
                if(hit==null)continue;
                var obstruction=b.c.level.clip(new ClipContext(from,hit,ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,arrow));
                if(obstruction.getType()!=HitResult.Type.MISS)continue;
                arrow.discard();b.spend(10);
                Fx.burst(b.c.level,hit,elementFor(b.c.owner),5,.15);
                if(b.hp<=0)break;
            }
        }
    }
    public static boolean active(ServerPlayer p) {var b=ACTIVE.get(p.getUUID());return b!=null&&b.c.owner==p;}
    public static double health(ServerPlayer p) {var b=ACTIVE.get(p.getUUID());return b!=null&&b.c.owner==p?b.hp:0;}
    public static int displays(ServerPlayer p) {return active(p)?1:0;}
    private static void remove(ServerPlayer p) {var b=ACTIVE.get(p.getUUID());if(b!=null&&b.c.owner==p){ACTIVE.remove(p.getUUID());b.holder.destroy();}}
    static void cleanup(ServerPlayer p) {remove(p);}
    static void clearAll() {for(Barrier b:List.copyOf(ACTIVE.values()))remove(b.c.owner);}
}
