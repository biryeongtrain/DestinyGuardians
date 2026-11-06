package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.ability.Motion;
import kim.biryeong.destiny.guardian.Guardians;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import java.util.function.BooleanSupplier;
import java.util.function.Consumer;

/** A short accepted attack owns native velocity, never a movement-check exemption or a saved target. */
public final class MeleeLunge {
    public static final int PHYSICS_TICKS=5;
    private static final Map<ServerPlayer,Dash> ACTIVE=new IdentityHashMap<>();
    private static boolean initialized;
    private MeleeLunge() { }
    private static final class Dash {
        final ServerPlayer p;final Object level,connection,runtime,data,stack,loadout,superSession;
        final BooleanSupplier accepted;final Vec3 direction;final double budget,reach,cosine,height;
        final Consumer<LivingEntity> contact;final Set<UUID> hit=new HashSet<>();
        final long expires;Vec3 before,clientBefore,assigned=Vec3.ZERO;double travelled;int steps;
        Dash(ServerPlayer p,Vec3 direction,double budget,BooleanSupplier accepted,
             double reach,double cosine,double height,Consumer<LivingEntity> contact) {
            this.p=p;this.direction=direction;this.budget=budget;this.accepted=accepted;
            this.reach=reach;this.cosine=cosine;this.height=height;this.contact=contact;
            level=p.level();connection=p.connection;runtime=Guardians.runtime(p);data=Guardians.data(p);stack=p.getMainHandItem();
            loadout=Guardians.data(p).loadout().orElse(null);
            superSession=Guardians.runtime(p).superSession;
            expires=p.level().getGameTime()+PHYSICS_TICKS+3;
        }
        boolean valid() {
            return p.isAlive()&&!p.isRemoved()&&!p.isSpectator()&&!p.isPassenger()&&!p.hasDisconnected()
                    &&p.level()==level&&p.connection==connection&&Guardians.runtimeIfPresent(p).orElse(null)==runtime
                    &&Guardians.data(p)==data&&Guardians.data(p).loadout().orElse(null)==loadout
                    &&p.getMainHandItem()==stack&&p.level().getGameTime()<expires&&accepted.getAsBoolean();
        }
        void contacts(Vec3 start,Vec3 end) {
            if(contact==null)return;
            for(var target:MeleeSweep.sweep(p,start,end,reach,cosine,height)) {
                if(!valid()||hit.size()>=MeleeSweep.MAX_HITS)break;
                if(hit.add(Combat.damageOwner(target).getUUID()))contact.accept(target);
            }
        }
    }
    private static void initialize() {
        if(initialized)return;initialized=true;
        ServerPlayConnectionEvents.DISCONNECT.register((handler,server)->cancel(handler.player));
        ServerTickEvents.END_SERVER_TICK.register(server->{
            for(var d:List.copyOf(ACTIVE.values()))if(d.p.level().getServer()==server&&!d.valid())cancel(d.p);
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(server->{
            for(var d:List.copyOf(ACTIVE.values()))if(d.p.level().getServer()==server)cancel(d.p);
        });
    }
    public static boolean start(ServerPlayer p,Vec3 direction,double distance,BooleanSupplier valid,
                                double reach,double cosine,double height,Consumer<LivingEntity> contact) {
        initialize();
        if(!Double.isFinite(distance)||distance<=0||distance>8||!Double.isFinite(direction.x)||!Double.isFinite(direction.z))return false;
        Vec3 flat=new Vec3(direction.x,0,direction.z);if(flat.lengthSqr()<1e-8)return false;
        Dash d=new Dash(p,flat.normalize(),distance,valid,reach,cosine,height,contact);
        if(!d.valid())return false;
        cancel(p);ACTIVE.put(p,d);d.contacts(p.position(),p.position());
        // Publish the same initial impulse used by the next native server physics tick.
        assign(d);return true;
    }
    public static boolean active(ServerPlayer p) {
        var d=ACTIVE.get(p);return d!=null&&d.valid();
    }
    private static void assign(Dash d) {
        double distance=Math.min(d.budget-d.travelled,d.budget/PHYSICS_TICKS);
        double allowed=0;
        for(int i=1;i<=Math.ceil(distance/.05);i++) {
            double amount=Math.min(distance,i*.05);var box=d.p.getBoundingBox().move(d.direction.scale(amount));
            var level=d.p.level();
            if(!level.hasChunkAt(BlockPos.containing(box.minX,box.minY,box.minZ))
                    ||!level.hasChunkAt(BlockPos.containing(box.minX,box.minY,box.maxZ))
                    ||!level.hasChunkAt(BlockPos.containing(box.maxX,box.minY,box.minZ))
                    ||!level.hasChunkAt(BlockPos.containing(box.maxX,box.maxY,box.maxZ))
                    ||!level.getWorldBorder().isWithinBounds(box)||!level.noCollision(d.p,box))break;
            allowed=amount;
        }
        d.assigned=d.direction.scale(allowed);
        Vec3 velocity=d.p.getDeltaMovement();
        Motion.setVelocity(d.p,new Vec3(d.assigned.x,velocity.y,d.assigned.z));
    }
    /** Called from the existing native doTick hook, after camera input and before native travel. */
    public static void beforePhysics(ServerPlayer p) {
        Dash d=ACTIVE.get(p);if(d==null)return;
        if(!d.valid()||d.steps>=PHYSICS_TICKS||d.travelled>=d.budget-1e-5){cancel(p);return;}
        d.before=p.position();
        // Camera sessions already own server physics. Ordinary first-person movement
        // remains client-predicted and uses vanilla handlePlayerPositionChange validation.
        if(kim.biryeong.destiny.camera.SuperCamera.active(p)){p.xxa=0;p.zza=0;p.setJumping(false);}
        assign(d);
    }
    /** Damage follows only the actual collision-resolved segment, never the predicted full destination. */
    public static void afterPhysics(ServerPlayer p) {
        Dash d=ACTIVE.get(p);if(d==null||d.before==null)return;
        Vec3 from=d.before;d.before=null;
        if(!d.valid()||p.position().distanceToSqr(from)>64){cancel(p);return;}
        d.steps++;
        if(!kim.biryeong.destiny.camera.SuperCamera.active(p)) {
            // Vanilla will rewind this speculative doTick step. Never damage from it.
            if(d.steps>=PHYSICS_TICKS)cancel(p);
            return;
        }
        Vec3 moved=p.position().subtract(from);double horizontal=Math.hypot(moved.x,moved.z);
        d.travelled+=horizontal;
        p.connection.resetPosition(); // Retain this one native step through tickPlayer's firstGood rewind.
        if(d.travelled<=d.budget+.1)d.contacts(from,p.position());
        if(horizontal<1e-5||d.steps>=PHYSICS_TICKS||d.travelled>=d.budget-1e-5)cancel(p);
    }
    /** Observe only; no cancellation, tolerance changes or exceptions to vanilla validation. */
    public static void beforeClientMovement(ServerPlayer p) {
        Dash d=ACTIVE.get(p);
        if(d!=null&&d.valid()&&!kim.biryeong.destiny.camera.SuperCamera.active(p))d.clientBefore=p.position();
    }
    public static void afterClientMovement(ServerPlayer p) {
        Dash d=ACTIVE.get(p);if(d==null||d.clientBefore==null)return;
        Vec3 from=d.clientBefore;d.clientBefore=null;
        if(!d.valid()) {cancel(p);return;}
        Vec3 delta=p.position().subtract(from);double horizontal=Math.hypot(delta.x,delta.z);
        if(delta.lengthSqr()>64||horizontal>d.budget-d.travelled+.1) {cancel(p);return;}
        d.travelled+=horizontal;
        if(horizontal>1e-5)d.contacts(from,p.position());
        if(d.travelled>=d.budget-1e-5)cancel(p);
    }
    public static void cancel(ServerPlayer p) {
        Dash d=ACTIVE.remove(p);if(d==null||p.level()!=d.level||p.connection!=d.connection)return;
        // Relinquish only our horizontal impulse; preserve gravity and a foreign replacement impulse.
        Vec3 now=p.getDeltaMovement();
        double horizontal=Math.hypot(now.x,now.z);
        if(horizontal<=d.assigned.length()+.05&&(horizontal<1e-5
                ||(now.x*d.direction.x+now.z*d.direction.z)/horizontal>.98))
            Motion.setVelocity(p,new Vec3(0,now.y,0));
    }
    public static void cancelWeapon(ServerPlayer p) {
        Dash d=ACTIVE.get(p);if(d!=null&&d.superSession==null)cancel(p);
    }
}
