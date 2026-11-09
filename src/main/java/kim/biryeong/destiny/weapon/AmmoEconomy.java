package kim.biryeong.destiny.weapon;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.fx.AmmoBrickVisual;
import net.fabricmc.fabric.api.attachment.v1.*;
import net.fabricmc.fabric.api.entity.event.v1.*;
import net.fabricmc.fabric.api.event.lifecycle.v1.*;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.*;
import net.minecraft.sounds.*;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.*;
import java.util.*;

/** Personal PvE ammo earned from confirmed combat. Called on the server thread, no inventory shadow pool. */
public final class AmmoEconomy {
    public static final AttachmentType<AmmoMeters> METERS=AttachmentRegistry.create(DestinyGuardians.id("ammo_meters_w42"),
            b->b.persistent(AmmoMeters.CODEC).copyOnDeath());
    public static final int ASSIST_TICKS=200, BRICK_LIFETIME=2400, MAX_BRICKS=24, MAX_VICTIMS=2048, MAX_CONTRIBUTORS=8;
    /** Current Bungie 9.5.0 Marksman pickup radius; ordinary body pickup stays 1.5 blocks. */
    public static final double MARKSMAN_PICKUP_RADIUS = 15;
    private record Contribution(ServerPlayer player,AmmoGeneration source,long tick) {}
    private record Victim(LivingEntity entity,Map<UUID,Contribution> contributors) {}
    private record Brick(ServerPlayer owner,ServerLevel level,WeaponAmmoType type,Vec3 position,long expires,ElementHolder visual) {}
    private static final Map<UUID,Victim> VICTIMS=new LinkedHashMap<>();
    private static final Map<UUID,List<Brick>> BRICKS=new HashMap<>();
    private static boolean initialized;
    private AmmoEconomy() {}
    public static void init() {
        if(initialized)return;initialized=true;
        ServerTickEvents.END_SERVER_TICK.register(AmmoEconomy::tick);
        ServerPlayConnectionEvents.DISCONNECT.register((h,s)->cleanup(h.getPlayer()));
        ServerLivingEntityEvents.AFTER_DEATH.register((e,s)->{if(e instanceof ServerPlayer p)cleanup(p);});
        ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.register((p,from,to)->cleanup(p));
        ServerLifecycleEvents.SERVER_STOPPING.register(s->clear());
    }
    public static AmmoMeters meters(ServerPlayer p) {
        if (kim.biryeong.destiny.crucible.CrucibleRuntime.participating(p))
            return new AmmoMeters((int)Math.min(AmmoMeters.MAX,
                    kim.biryeong.destiny.crucible.CrucibleAmmo.meter(p) * AmmoMeters.FULL),0);
        return p.getAttachedOrElse(METERS,AmmoMeters.EMPTY);
    }
    private static boolean eligible(ServerPlayer p) {return !kim.biryeong.destiny.crucible.CrucibleRuntime.participating(p)&&p.isAlive()&&!p.isRemoved()&&!p.isSpectator()&&WeaponLoadout.enabled(p);}
    public static boolean hasType(ServerPlayer p,WeaponAmmoType type) {
        return WeaponLoadout.enabled(p)&&WeaponLoadout.equipped(p).stream().anyMatch(e->e.characteristics().ammo()==type);
    }
    /** Called only after the damage path has actually decreased HP/absorption. Corpses/misses cannot mint points. */
    public static void afterDamage(ServerPlayer p,LivingEntity target,AmmoGeneration source,float before,float after) {
        if(kim.biryeong.destiny.crucible.CrucibleRuntime.participating(p)) {
            kim.biryeong.destiny.crucible.CrucibleAmmo.afterDamage(p,target,source,before,after);
            return;
        }
        if(p.level()!=target.level()||!(target instanceof Enemy)||p.isAlliedTo(target)
                ||!Float.isFinite(before)||!Float.isFinite(after)||after>=before)return;
        long now=p.level().getGameTime();
        Victim v=VICTIMS.get(target.getUUID());
        if(v==null||v.entity()!=target) {
            if(!eligible(p))return;
            if(VICTIMS.size()>=MAX_VICTIMS)VICTIMS.remove(VICTIMS.keySet().iterator().next());
            v=new Victim(target,new LinkedHashMap<>());VICTIMS.put(target.getUUID(),v);
        }
        if(eligible(p)) {
            if(!v.contributors().containsKey(p.getUUID())&&v.contributors().size()>=MAX_CONTRIBUTORS)
                v.contributors().remove(v.contributors().keySet().iterator().next());
            v.contributors().put(p.getUUID(),new Contribution(p,source,now));
        }
        if(target.isAlive()&&!target.isDeadOrDying())return;
        VICTIMS.remove(target.getUUID());
        for(var c:v.contributors().values()) {
            var owner=c.player();
            if(!eligible(owner)||owner.level()!=target.level()||now-c.tick()>ASSIST_TICKS)continue;
            var gains=c.source().gains(owner!=p);
            var previous=meters(owner);
            owner.setAttached(METERS,previous.add(hasType(owner,WeaponAmmoType.SPECIAL)?gains.special():0,
                    hasType(owner,WeaponAmmoType.HEAVY)?gains.heavy():0));
            dropOwed(owner,target.position());
        }
    }
    /** Bounded downward query, never force-loads chunks. Pits/liquids/inside-block positions defer owed ammo. */
    public static Optional<Vec3> safePosition(ServerLevel level,Vec3 at) {
        if(!Double.isFinite(at.x)||!Double.isFinite(at.y)||!Double.isFinite(at.z))return Optional.empty();
        BlockPos start=BlockPos.containing(at);
        if(!level.hasChunkAt(start)||!level.getWorldBorder().isWithinBounds(start))return Optional.empty();
        for(int y=start.getY();y>=Math.max(level.getMinY(),start.getY()-8);y--) {
            var floor=new BlockPos(start.getX(),y,start.getZ());var state=level.getBlockState(floor);
            if(!state.getFluidState().isEmpty())return Optional.empty();
            if(!state.isFaceSturdy(level,floor,net.minecraft.core.Direction.UP))continue;
            Vec3 pos=new Vec3(at.x,y+1.08,at.z);var box=AABB.ofSize(pos.add(0,.12,0),.8,.3,.8);
            if(level.noCollision(box)&&level.getBlockState(floor.above()).getFluidState().isEmpty())return Optional.of(pos);
            return Optional.empty();
        }
        return Optional.empty();
    }
    private static void dropOwed(ServerPlayer p,Vec3 at) {
        var safe=safePosition(p.level(),at);if(safe.isEmpty())return;
        List<Brick> list=BRICKS.computeIfAbsent(p.getUUID(),id->new ArrayList<>());
        for(var type:List.of(WeaponAmmoType.SPECIAL,WeaponAmmoType.HEAVY)) {
            if(list.size()>=MAX_BRICKS||!hasType(p,type)||!meters(p).owed(type))continue;
            // Separate green/purple shells from the same defeat instead of z-fighting at one anchor.
            var typed=safePosition(p.level(),at.add(type==WeaponAmmoType.SPECIAL?-.35:.35,0,0));
            if(typed.isEmpty())continue;
            Vec3 where=typed.get();
            var visual=AmmoBrickVisual.create(p,type,where);
            list.add(new Brick(p,p.level(),type,where,p.level().getGameTime()+BRICK_LIFETIME,visual));
            // Spend only after an actual personal pickup exists, not merely because the meter filled.
            p.setAttached(METERS,meters(p).spend(type));
        }
        if(list.isEmpty())BRICKS.remove(p.getUUID());
    }
    private static int grant(ServerPlayer p,WeaponAmmoType type) {
        var matching=WeaponLoadout.equipped(p).stream().filter(e->e.characteristics().ammo()==type).toList();
        // A real personal heavy brick can still be consumed for its Lead from Gold
        // reserve grant when Heavy itself is full. A full Special grant returns zero:
        // no-space keeps the brick, and a successful pickup is removed exactly once.
        int total=type==WeaponAmmoType.HEAVY?WeaponLeadFromGold.grant(p):0;
        for(var e:matching) {
            var ammo=WeaponItems.magazine(e.stack(),WeaponProfile.forEntry(e.weapon()));
            int amount=AmmoGeneration.split(AmmoGeneration.perBrick(e.weapon()),matching.size());
            int gained=SwordItems.isSword(e.stack())?ammo.addLoaded(amount):ammo.addReserve(amount);
            if(gained>0){WeaponItems.save(e.stack(),ammo);total+=gained;}
        }
        if(type==WeaponAmmoType.SPECIAL || type==WeaponAmmoType.HEAVY) {
            for(var stack:WeaponOverflow.eligible(p)) {
                var entry=WeaponItems.entry(stack).orElseThrow();
                var ammo=WeaponItems.magazine(stack,WeaponProfile.forEntry(entry));
                int gained=ammo.reloadOverflow(WeaponOverflow.target(stack,entry));
                if(gained>0) { WeaponItems.save(stack,ammo); total+=gained; }
            }
        }
        if(total>0){p.getInventory().setChanged();p.containerMenu.broadcastChanges();}
        return total;
    }
    /** Server body proximity plus collision ray; remote super cameras never remotely collect bricks. */
    private static boolean canReach(ServerPlayer p,Brick b,double radiusSquared,boolean requireSight) {
        if(p.position().distanceToSqr(b.position())>radiusSquared)return false;
        if(!requireSight)return true;
        Vec3 from=p.position().add(0,.4,0);
        return p.level().clip(new ClipContext(from,b.position(),ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,p)).getType()==HitResult.Type.MISS;
    }
    /** Activation-only 15-block body sphere, not a camera/magnet loop. The official radius is
     * known; through-wall behavior is an authored spherical policy, not live D2 verification.
     * Existing per-owner grants, splitting, no-space retention, expiry and loaded-chunk checks apply.
     * @return number of personal bricks actually consumed, not ammo rounds
     */
    public static int collectForMarksmanDodge(ServerPlayer p) {
        return collect(p,MARKSMAN_PICKUP_RADIUS*MARKSMAN_PICKUP_RADIUS,false);
    }
    /** W322 Shoot to Loot: a personal Special/Heavy brick crossed by an accepted weapon ray segment.
     * Same grant/no-space retention/expiry as a body pickup. @return bricks actually consumed. */
    public static int collectAlong(ServerPlayer p,Vec3 from,Vec3 to,double radius) {
        var list=BRICKS.get(p.getUUID());if(list==null||from==null||to==null)return 0;
        int consumed=0;
        for(var it=list.iterator();it.hasNext();) {
            var b=it.next();
            if(b.owner()!=p||!eligible(p)||p.level()!=b.level()||p.level().getGameTime()>=b.expires()
                    ||b.type()==WeaponAmmoType.PRIMARY
                    ||kim.biryeong.destiny.combat.StasisCrystals.segmentDistance(from,to,
                        b.position().add(0,AmmoBrickVisual.SCALE*.5,0))>radius)continue;
            if(grant(p,b.type())>0) {
                b.visual().destroy();it.remove();consumed++;
                p.level().playSound(null,p.blockPosition(),SoundEvents.ITEM_PICKUP,SoundSource.PLAYERS,.45f,b.type()==WeaponAmmoType.SPECIAL?1.5f:.8f);
            }
        }
        if(list.isEmpty())BRICKS.remove(p.getUUID());
        return consumed;
    }
    public static void tickPlayer(ServerPlayer p) { collect(p,2.25,true); }
    private static int collect(ServerPlayer p,double radiusSquared,boolean requireSight) {
        var list=BRICKS.get(p.getUUID());if(list==null)return 0;
        int consumed=0;
        for(var it=list.iterator();it.hasNext();) {
            var b=it.next();
            boolean invalid=b.owner()!=p||!eligible(p)||p.level()!=b.level()||p.level().getGameTime()>=b.expires()
                    ||!p.level().hasChunkAt(BlockPos.containing(b.position()));
            boolean picked=!invalid&&canReach(p,b,radiusSquared,requireSight)&&grant(p,b.type())>0;
            if(invalid||picked) {
                b.visual().destroy();it.remove();
                if(picked) { consumed++;p.level().playSound(null,p.blockPosition(),SoundEvents.ITEM_PICKUP,SoundSource.PLAYERS,.45f,b.type()==WeaponAmmoType.SPECIAL?1.5f:.8f); }
            }
        }
        if(list.isEmpty())BRICKS.remove(p.getUUID());
        return consumed;
    }
    private static void tick(MinecraftServer server) {
        for(var list:List.copyOf(BRICKS.values()))if(!list.isEmpty()&&list.getFirst().owner().level().getServer()==server)tickPlayer(list.getFirst().owner());
        VICTIMS.values().removeIf(v->v.entity().level().getServer()==server&&(v.entity().isRemoved()
                ||v.contributors().values().stream().allMatch(c->v.entity().level().getGameTime()-c.tick()>ASSIST_TICKS)));
    }
    public static int bricks(ServerPlayer p){return BRICKS.getOrDefault(p.getUUID(),List.of()).size();}
    public static List<Vec3> brickPositions(ServerPlayer p){return BRICKS.getOrDefault(p.getUUID(),List.of()).stream().map(Brick::position).toList();}
    public static Collection<net.minecraft.server.network.ServerGamePacketListenerImpl> brickWatchers(ServerPlayer p) {
        return BRICKS.getOrDefault(p.getUUID(),List.of()).stream().flatMap(b->b.visual().getWatchingPlayers().stream()).toList();
    }
    public static void cleanup(ServerPlayer p) {
        var list=BRICKS.get(p.getUUID());
        if(list!=null) {
            list.removeIf(b->{if(b.owner()!=p)return false;b.visual().destroy();return true;});
            if(list.isEmpty())BRICKS.remove(p.getUUID());
        }
        VICTIMS.values().forEach(v->v.contributors().values().removeIf(c->c.player()==p));
        VICTIMS.values().removeIf(v->v.contributors().isEmpty());
        // Immutable persistent meters survive death/reconnect; transient scene objects do not.
    }
    public static void clear(){for(var list:List.copyOf(BRICKS.values()))list.forEach(b->b.visual().destroy());BRICKS.clear();VICTIMS.clear();}
}
