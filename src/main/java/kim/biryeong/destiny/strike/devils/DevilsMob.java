package kim.biryeong.destiny.strike.devils;

import eu.pb4.polymer.core.api.entity.PolymerEntity;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.*;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.*;
import java.util.*;

/** Strike-owned enemy, using authored fixed-three tuning. No vanilla attack goals or loot. */
public final class DevilsMob extends Monster implements PolymerEntity, kim.biryeong.destiny.loot.LootTagged, kim.biryeong.destiny.combat.StrikeCombatant {
    final DevilsPlan.Kind kind;
    DevilsActors runtime;
    DevilsDirector.ActorRef ref;
    DevilsPlan.Slot slot;
    boolean neutral;
    private Vec3 home;
    private DevilsActorModel model;
    private DevilsWalkerState walker;
    private DevilsMob root;
    private DevilsWalkerState.Region region;
    private final List<DevilsMob> parts = new ArrayList<>();
    private boolean deathReported, armorOpen;
    private int secondaryCooldown=60, secondaryWindup, secondaryBurst, secondaryGap;
    private Vec3 secondaryAim;
    private int deathDuration=24;
    private int age, cooldown = 40, windup, burst, burstGap, warpAt = 200, warpTicks;
    private LivingEntity target;
    private ServerPlayer priorityPlayer;
    private int playerMemoryUntil;
    private static final int PLAYER_MEMORY_TICKS = 100;
    private Vec3 aim, warpDestination;
    private final List<Bolt> bolts = new ArrayList<>();
    private Vec3 hazard;
    private int hazardUntil;
    private DevilsWalkerState.Phase previousWalker;
    private boolean attackMelee, attackSniper, blinkPending;
    private record ShotKey(UUID owner, UUID direct, int tick) { }
    private static final class Bolt {
        Vec3 at; final Vec3 velocity; final float damage; final double radius; int life = 80;
        Bolt(Vec3 at, Vec3 velocity, float damage, double radius) { this.at=at; this.velocity=velocity; this.damage=damage; this.radius=radius; }
    }
    public DevilsMob(EntityType<? extends DevilsMob> type, Level level) {
        super(type, level);
        kind = DevilsActors.KINDS.getOrDefault(type, DevilsPlan.Kind.DREG);
        xpReward = 0; setPersistenceRequired(); setSilent(true);
        if (DevilsActors.flying(kind) || kind == DevilsPlan.Kind.WALKER || type == DevilsActors.PART) setNoGravity(true);
        if (kind == DevilsPlan.Kind.SHANK || kind == DevilsPlan.Kind.WIZARD)
            moveControl = new net.minecraft.world.entity.ai.control.FlyingMoveControl(this, 20, true);
    }
    void bind(DevilsActors runtime, DevilsDirector.Spawn spawn, Vec3 at, DevilsWalkerState walker) {
        this.runtime=runtime; this.slot=spawn.slot(); this.ref=spawn.ref(); this.home=at; this.walker=walker;
        setPos(at.x, at.y, at.z);
        setHealth((float)spawn.health()); setAbsorptionAmount((float)spawn.shield());
        armorOpen=kind==DevilsPlan.Kind.BRIG && spawn.health()<=kind.health()*.5;
        // The two Brigs enter their first windup three seconds apart.
        cooldown = kind == DevilsPlan.Kind.BRIG ? 40 + slot.index()*60 : 30 + slot.index()*3;
    }
    boolean attachModel() { model=DevilsActorModel.attach(this); if(model!=null&&armorOpen)model.armorOpen(); return model != null; }
    public DevilsPlan.Kind kind() { return kind; }
    /** Destiny enemy ranks: red-bar minors, yellow-bar majors, Brig/Walker/Sepiks bosses; walker parts drop nothing. */
    @Override public Tier lootTier() {
        if (root != null) return Tier.NONE;
        return switch (kind) {
            case DREG, VANDAL, SHANK, THRALL, ACOLYTE -> Tier.MINOR;
            case MARAUDER, CAPTAIN, KNIGHT, WIZARD, SERVITOR -> Tier.MAJOR;
            case BRIG, WALKER, SEPIKS -> Tier.BOSS;
        };
    }
    public DevilsDirector.ActorRef reference() { return ref; }
    public boolean armorOpen() { return armorOpen; }
    public boolean walkerPart() { return root != null; }
    @Override public DevilsMob damageOwner() { return root == null ? this : root; }
    @Override public java.util.OptionalDouble damagePool() {
        var state = walkerState();
        return state == null ? java.util.OptionalDouble.empty() : java.util.OptionalDouble.of(state.damagePool());
    }
    @Override public kim.biryeong.destiny.combat.CombatantRank rank() {
        return switch (kind) {
            case WALKER, SEPIKS -> kim.biryeong.destiny.combat.CombatantRank.BOSS;
            case BRIG -> kim.biryeong.destiny.combat.CombatantRank.MINIBOSS;
            case CAPTAIN, KNIGHT, WIZARD, SERVITOR -> kim.biryeong.destiny.combat.CombatantRank.ELITE;
            default -> kim.biryeong.destiny.combat.CombatantRank.RANK_AND_FILE;
        };
    }
    @Override public kim.biryeong.destiny.combat.CombatantShields.Type shieldType() {
        return kind == DevilsPlan.Kind.WIZARD ? kim.biryeong.destiny.combat.CombatantShields.Type.SOLAR
                : kim.biryeong.destiny.combat.CombatantShields.Type.ARC;
    }
    @Override public kim.biryeong.destiny.sound.EnemyHeadburstSounds.Family headburstFamily() {
        if (walkerPart()) return null;
        return switch (kind) {
            case DREG -> kim.biryeong.destiny.sound.EnemyHeadburstSounds.Family.FALLEN_DREG;
            case VANDAL, MARAUDER -> kim.biryeong.destiny.sound.EnemyHeadburstSounds.Family.FALLEN_VANDAL;
            case CAPTAIN -> kim.biryeong.destiny.sound.EnemyHeadburstSounds.Family.FALLEN_CAPTAIN;
            default -> null;
        };
    }
    public DevilsWalkerState walkerState() { return root == null ? walker : root.walker; }
    /** WeaponPrecision must call this before its generic humanoid/head branch. No damage multiplication here. */
    @Override public boolean precisionAt(Vec3 point) {
        if (root != null) return region == DevilsWalkerState.Region.CORE && root.walker.phase() == DevilsWalkerState.Phase.EXPOSED;
        if (kind == DevilsPlan.Kind.WALKER) return false;
        if (kind == DevilsPlan.Kind.BRIG) return armorOpen && point.y > getY()+getBbHeight()*.5 && point.y < getY()+getBbHeight()*.78;
        if (kind == DevilsPlan.Kind.SEPIKS || kind == DevilsPlan.Kind.SERVITOR)
            {
            Vec3 relative=point.subtract(position());
            double yaw=Math.toRadians(getYRot());
            double lateral=relative.x*Math.cos(yaw)+relative.z*Math.sin(yaw);
            double forward=-relative.x*Math.sin(yaw)+relative.z*Math.cos(yaw);
            return Math.abs(lateral)<getBbWidth()*.18 && forward>getBbWidth()*.2
                    && Math.abs(relative.y-getBbHeight()*.5)<getBbHeight()*.18;
        }
        return kind != DevilsPlan.Kind.SHANK && point.y >= getY()+getBbHeight()*.75;
    }
    private boolean mobileFlyer() { return kind == DevilsPlan.Kind.SHANK || kind == DevilsPlan.Kind.WIZARD; }
    private Vec3 lastOverMap;
    /** Flyers fight around the pad they entered at; caves and side passages beyond it are not part of the encounter. */
    static final double FLYER_LEASH = 24, FLYER_LEASH_DOWN = 5, FLYER_LEASH_UP = 9;
    private boolean withinLeash(Vec3 at) {
        double dx = at.x - home.x, dz = at.z - home.z;
        return dx * dx + dz * dz <= FLYER_LEASH * FLYER_LEASH && at.y >= home.y - FLYER_LEASH_DOWN && at.y <= home.y + FLYER_LEASH_UP + 2.5;
    }
    /**
     * Flyers can be knocked or steered past the rim of the built map, where nobody can reach them and the encounter
     * stalls. Remember the last position over the map and put the flyer back there instead of losing it.
     * Returns false when the mob was removed this tick.
     */
    private boolean keepFlyerOverMap(ServerLevel level) {
        Vec3 at = position();
        boolean inside = runtime.environment.contains(slot.zone(), at)
                && runtime.environment.contains(slot.zone(), at.add(1.5, 0, 1.5)) && runtime.environment.contains(slot.zone(), at.add(-1.5, 0, -1.5))
                && withinLeash(at)
                && (age % 5 != 0 || DevilsSpatial.flightSupported(level, at));
        if (inside) { if (age % 5 == 0) lastOverMap = at; return true; }
        Vec3 back = lastOverMap != null ? lastOverMap : home;
        if (!runtime.environment.contains(slot.zone(), back) || getY() < level.getMinY() + 1 && lastOverMap == null) { discard(); return false; }
        getNavigation().stop();
        setDeltaMovement(Vec3.ZERO);
        teleportTo(back.x, back.y, back.z);
        return true;
    }
    @Override protected void registerGoals() { }
    @Override protected net.minecraft.world.entity.ai.navigation.PathNavigation createNavigation(Level level) {
        var typeKind = DevilsActors.KINDS.getOrDefault(getType(), DevilsPlan.Kind.DREG);
        return typeKind == DevilsPlan.Kind.SHANK || typeKind == DevilsPlan.Kind.WIZARD
                ? new net.minecraft.world.entity.ai.navigation.FlyingPathNavigation(this, level)
                : super.createNavigation(level);
    }
    @Override protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (root != null) { if(root.isRemoved()) discard(); return; }
        if (runtime == null) { discard(); return; }
        if (runtime.paused()) { getNavigation().stop(); setDeltaMovement(Vec3.ZERO); return; }
        age++;
        if (mobileFlyer()) { if (!keepFlyerOverMap(level)) return; }
        else if (!runtime.environment.contains(slot.zone(), position()) || getY()<level.getMinY()+1) { discard(); return; }
        if (model != null) { model.tick(); model.cloak(kind==DevilsPlan.Kind.MARAUDER && windup==0 && cooldown>10); }
        if(blinkPending) { blinkPending=false; blink(level); }
        if (walker != null) {
            walker.tick(); placeParts();
            if (previousWalker != walker.phase()) {
                previousWalker=walker.phase();
                if(previousWalker==DevilsWalkerState.Phase.RECOVER)runtime.environment.sound(this,"recover");
                model.play(switch(previousWalker) {case STAGGER -> "stagger"; case EXPOSED -> "weakpoint_open"; case RECOVER -> "recover"; default -> "idle";});
                if(previousWalker != DevilsWalkerState.Phase.ARMORED) { windup=0; burst=0; secondaryWindup=secondaryBurst=0; }
            }
        }
        tickBolts(level);
        if(hazard != null) {
            if(age >= hazardUntil) hazard=null;
            else if(age%15==0) { ring(level,hazard,3); splash(level,hazard,1,3); }
        }
        if (kind == DevilsPlan.Kind.SEPIKS) {
            if (!runtime.director.get().phase().damagePhase() && !runtime.director.get().phase().shieldPhase()) return;
            if (warpTicks>0) { tickWarp(level); return; }
            if(age>=warpAt && runtime.director.get().phase().damagePhase()) {
                warpAt=age+200;
                warpDestination=runtime.environment.sepiksWarp(this).orElse(null);
                if(warpDestination!=null) { warpTicks=24; tickWarp(level); return; }
            }
            if (age%10==0 && age%100>=20 && age%100<=50) splash(level,position().add(0,1,0),2,4);
            if (age%100<20 && age%4==0) ring(level,position(),4);
        }
        var nextTarget = selectTarget();
        if (nextTarget instanceof ServerPlayer player && target != player) focusPlayer(player);
        else changeTarget(nextTarget);
        if(target==null) { getNavigation().stop(); model.base("idle"); return; }
        lookAtTarget();
        if (walker != null && walker.phase()!=DevilsWalkerState.Phase.ARMORED) return;
        if((kind==DevilsPlan.Kind.WALKER||kind==DevilsPlan.Kind.BRIG)&&windup==0&&burst==0&&tickSecondary(level))return;
        if(burst>0) {
            if(--burstGap<=0) { fire(level); burst--; burstGap=kind==DevilsPlan.Kind.SEPIKS?10:7; }
            return;
        }
        if(windup>0) {
            getNavigation().stop(); model.base("idle");
            if(age%4==0) { if(radius()>0) ring(level,aim,radius()); else level.sendParticles(ParticleTypes.ELECTRIC_SPARK,getX(),getEyeY(),getZ(),2,.1,.1,.1,0); }
            if(--windup==0) {
                if(attackMelee) {
                    if(valid(target)&&distanceToSqr(target)<9&&getSensing().hasLineOfSight(target)) hurtTarget(level,target,meleeDamage());
                    model.play("melee"); runtime.environment.sound(this,"melee");
                } else { burst=burstSize(); burstGap=1; model.play("shoot"); }
                cooldown=period();
            }
            return;
        }
        if(cooldown>0) cooldown--;
        moveToRange();
        if(cooldown<=0 && getSensing().hasLineOfSight(target)) {
            double dist=distanceToSqr(target);
            attackMelee=kind==DevilsPlan.Kind.THRALL||kind==DevilsPlan.Kind.MARAUDER||dist<6.25&&!kind.boss()&&!DevilsActors.flying(kind);
            if(attackMelee && dist>9) return;
            attackSniper=kind==DevilsPlan.Kind.VANDAL && slot.index()%3==0;
            int lead=attackMelee? (kind==DevilsPlan.Kind.MARAUDER?10:12) : telegraph();
            aim=target.position().add(0,radius()>0?.15:target.getBbHeight()*.6,0);
            if(runtime.reserve(this,target,aim,lead+(attackMelee?0:(int)Math.ceil(position().distanceTo(aim)/.9)),kind==DevilsPlan.Kind.WALKER||kind==DevilsPlan.Kind.BRIG,attackSniper,attackMelee)) {
                windup=lead; runtime.environment.sound(this,"charge"); model.cloak(false); model.play(attackMelee?"melee":"charge");
            }
        }
    }
    LivingEntity selectTarget() {
        if (valid(priorityPlayer)) {
            if (distanceToSqr(priorityPlayer)<64*64 && getSensing().hasLineOfSight(priorityPlayer)) playerMemoryUntil=age+PLAYER_MEMORY_TICKS;
            if (age<playerMemoryUntil) return priorityPlayer;
        }
        priorityPlayer=null;
        var seen=runtime.targets().stream().filter(p->valid(p)&&distanceToSqr(p)<64*64
                &&getSensing().hasLineOfSight(p)).min(Comparator.comparingDouble(this::distanceToSqr)).orElse(null);
        if(seen!=null) { priorityPlayer=seen;playerMemoryUntil=age+PLAYER_MEMORY_TICKS;return seen; }
        if (target instanceof DevilsMob && valid(target) && distanceToSqr(target)<64*64 && age%20!=0) return target;
        return runtime.combatTargets(this).stream().filter(p->p instanceof DevilsMob&&distanceToSqr(p)<64*64)
                .min(Comparator.comparingDouble(this::distanceToSqr)).orElse(null);
    }
    private void focusPlayer(ServerPlayer player) {
        if (!valid(player)) return;
        priorityPlayer=player;playerMemoryUntil=age+PLAYER_MEMORY_TICKS;
        changeTarget(player);
    }
    private void changeTarget(LivingEntity nextTarget) {
        if (target != nextTarget) {
            // Every new target gets its own warning, including faction replacements and lost players.
            // Already fired projectiles keep their trajectory.
            windup=burst=secondaryWindup=secondaryBurst=0;
            aim=secondaryAim=null;runtime.cancelAttack(this);
        }
        target=nextTarget;
    }
    private boolean valid(LivingEntity target) { return runtime.validTarget(this, target); }
    private void lookAtTarget() {
        Vec3 d=target.position().subtract(position());
        float want=(float)Math.toDegrees(Math.atan2(-d.x,d.z));
        float delta=net.minecraft.util.Mth.wrapDegrees(want-getYRot());
        float yaw=getYRot()+Math.clamp(delta,-4,4); setYRot(yaw); setYBodyRot(yaw); setYHeadRot(yaw);
    }
    private void moveToRange() {
        if(kind==DevilsPlan.Kind.WALKER||kind==DevilsPlan.Kind.SEPIKS||kind==DevilsPlan.Kind.SERVITOR) { model.base("idle"); return; }
        double range=kind==DevilsPlan.Kind.THRALL||kind==DevilsPlan.Kind.MARAUDER?2:kind==DevilsPlan.Kind.BRIG?22:14;
        if(distanceToSqr(target)<range*range && getSensing().hasLineOfSight(target)) {getNavigation().stop(); model.base("idle"); return;}
        Vec3 destination=target.position();
        double homeRadius=kind==DevilsPlan.Kind.BRIG?16:mobileFlyer()?FLYER_LEASH-4:32;
        Vec3 relative=destination.subtract(home).multiply(1,0,1);
        if(relative.length()>homeRadius) destination=home.add(relative.normalize().scale(homeRadius));
        if(!runtime.environment.contains(slot.zone(),destination))return;
        if(DevilsActors.flying(kind)) {
            destination = new Vec3(destination.x, Math.clamp(destination.y + 1, home.y - 3, home.y + 6), destination.z);
            if (age % 10 == 0 && runtime.environment.contains(slot.zone(), destination)) {
                var path = getNavigation().createPath(BlockPos.containing(destination), 1);
                boolean inside = path != null;
                if (path != null) for (int i=0;i<path.getNodeCount();i++) {
                    var node=path.getNode(i);
                    var nodeAt = new Vec3(node.x+.5,node.y,node.z+.5);
                    if (!runtime.environment.contains(slot.zone(), nodeAt) || mobileFlyer() && (!withinLeash(nodeAt) || !DevilsSpatial.flightSupported((ServerLevel) level(), nodeAt))) {inside=false;break;}
                }
                if (inside) getNavigation().moveTo(path, 1); else getNavigation().stop();
            }
        } else if(age%10==0) getNavigation().moveTo(destination.x,destination.y,destination.z,kind==DevilsPlan.Kind.THRALL?1.35:1);
        model.base(kind==DevilsPlan.Kind.THRALL?"run":"walk");
    }
    private boolean tickSecondary(ServerLevel level) {
        if(secondaryCooldown>0)secondaryCooldown--;
        if(secondaryBurst>0) {
            if(--secondaryGap<=0) {
                Vec3 from=position().add(0,getBbHeight()*.55,0);
                if(bolts.size()<12)bolts.add(new Bolt(from,secondaryAim.subtract(from).normalize().scale(1),kind==DevilsPlan.Kind.BRIG?6:2,0));
                runtime.environment.sound(this,"secondary_fire");model.play("shoot");secondaryBurst--;secondaryGap=7;
            }
            return true;
        }
        if(secondaryWindup>0) {
            if(secondaryWindup%4==0)level.sendParticles(ParticleTypes.ELECTRIC_SPARK,getX(),getY()+getBbHeight()*.55,getZ(),2,.2,.2,.2,0);
            if(--secondaryWindup==0){secondaryBurst=kind==DevilsPlan.Kind.BRIG?1:3;secondaryGap=1;secondaryCooldown=kind==DevilsPlan.Kind.BRIG?105:75;}
            return true;
        }
        if(secondaryCooldown==0&&cooldown>20&&valid(target)&&getSensing().hasLineOfSight(target)) {
            secondaryAim=target.position().add(0,target.getBbHeight()*.6,0);secondaryWindup=12;
            runtime.environment.sound(this,"secondary_charge");return true;
        }
        return false;
    }
    private int telegraph() {return switch(kind){case WALKER->40;case BRIG->30;case KNIGHT->18;case VANDAL->attackSniper?16:10;default->10;};}
    // User tuning: 50% more recovery between attacks; damage and actor caps are unchanged.
    private int period(){return (switch(kind){case DREG->30;case VANDAL->attackSniper?60:36;case SHANK->12;case MARAUDER->32;case CAPTAIN,SERVITOR->50;case THRALL->20;case ACOLYTE->28;case KNIGHT->56;case WIZARD->40;case BRIG->120;case WALKER->140;case SEPIKS->60;}) * 3 / 2;}
    private int burstSize(){return switch(kind){case DREG,CAPTAIN,WIZARD,SEPIKS->3;default->1;};}
    private float shotDamage(){return switch(kind){case DREG,ACOLYTE,WIZARD->2;case SHANK->1.5f;case VANDAL->attackSniper?6:3;case CAPTAIN,SERVITOR->3;case KNIGHT,SEPIKS->5;case BRIG->8;case WALKER->10;default->3;};}
    private float meleeDamage(){return switch(kind){case CAPTAIN->6;case THRALL->3;default->4;};}
    private double radius(){return switch(kind){case KNIGHT->2.5;case BRIG->4;case WALKER->5;default->0;};}
    private void fire(ServerLevel level) {
        if(aim==null||bolts.size()>=12)return;
        runtime.environment.sound(this,kind==DevilsPlan.Kind.VANDAL&&attackSniper?"sniper_fire":"fire");
        Vec3 from=position().add(0,getBbHeight()*.65,0);
        Vec3 end=radius()>0?aim:valid(target)?target.position().add(0,target.getBbHeight()*.6,0):aim;
        bolts.add(new Bolt(from,end.subtract(from).normalize().scale(kind==DevilsPlan.Kind.SEPIKS?.65:.9),shotDamage(),radius()));
        if(kind==DevilsPlan.Kind.WIZARD && hazard==null && valid(target)) {hazard=new Vec3(aim.x,aim.y-target.getBbHeight()*.6,aim.z);hazardUntil=age+120;runtime.environment.sound(this,"hazard",hazard);}
    }
    private void tickBolts(ServerLevel level) {
        var it=bolts.iterator();
        while(it.hasNext()) {
            var b=it.next(); if(--b.life<=0) {it.remove();continue;}
            Vec3 end=b.at.add(b.velocity);
            if(!level.hasChunkAt(BlockPos.containing(end))) {it.remove();continue;}
            var wall=level.clip(new ClipContext(b.at,end,ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,this));
            Vec3 stop=wall.getType()==HitResult.Type.MISS?end:wall.getLocation();
            LivingEntity hit=null; double nearest=b.at.distanceToSqr(stop)+1e-6;
            for(var p:runtime.combatTargets(this)) {
                var contact=p.getBoundingBox().inflate(.12).clip(b.at,stop);
                double d=p.getBoundingBox().inflate(.12).contains(b.at)?0:contact.map(v->v.distanceToSqr(b.at)).orElse(Double.POSITIVE_INFINITY);
                if(d<nearest){nearest=d;hit=p;}
            }
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK,stop.x,stop.y,stop.z,1,0,0,0,0);
            if(hit!=null||wall.getType()!=HitResult.Type.MISS) {
                Vec3 at=hit==null?stop:b.at.add(b.velocity.normalize().scale(Math.sqrt(nearest)));
                if(b.radius>0){splash(level,at,b.damage,b.radius);runtime.environment.sound(this,"impact",at);}else if(hit!=null)hurtTarget(level,hit,b.damage);
                it.remove();
            } else b.at=end;
        }
    }
    private void splash(ServerLevel level,Vec3 center,float amount,double radius) {
        for(var p:runtime.combatTargets(this)) {
            double distance=p.position().add(0,.8,0).distanceTo(center);
            if(distance>radius)continue;
            var wall=level.clip(new ClipContext(center,p.position().add(0,.8,0),ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,this));
            if(wall.getType()!=HitResult.Type.MISS)continue;
            float minimum=kind==DevilsPlan.Kind.WALKER?3:kind==DevilsPlan.Kind.BRIG?2:amount*.3f;
            hurtTarget(level,p,(float)(amount-(amount-minimum)*distance/radius));
        }
    }
    private void hurtTarget(ServerLevel level,LivingEntity p,float amount) {
        if(valid(p)) { p.damageCooldownTime=0; p.hurtServer(level,damageSources().mobAttack(this),amount); }
    }
    private static void ring(ServerLevel level,Vec3 at,double radius) {
        if(at==null)return;
        for(int i=0;i<16;i++){double a=i*Math.PI/8;level.sendParticles(ParticleTypes.FLAME,at.x+Math.cos(a)*radius,at.y+.1,at.z+Math.sin(a)*radius,1,0,0,0,0);}
    }
    private void blink(ServerLevel level) {
        for(int side:new int[]{1,-1}) {
            double yaw=Math.toRadians(getYRot());
            Vec3 candidate=position().add(Math.cos(yaw)*side*4,0,Math.sin(yaw)*side*4);
            if(candidate.distanceToSqr(home)>16*16||!runtime.environment.contains(slot.zone(),candidate))continue;
            var below=BlockPos.containing(candidate).below();
            if(!level.hasChunkAt(below)||level.getBlockState(below).getCollisionShape(level,below).isEmpty())continue;
            if(!level.noCollision(this,getBoundingBox().move(candidate.subtract(position()))))continue;
            if(runtime.targets().stream().anyMatch(p->p.distanceToSqr(candidate)<9))continue;
            if(level.clip(new ClipContext(getEyePosition(),candidate.add(0,getEyeHeight(),0),ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,this)).getType()!=HitResult.Type.MISS)continue;
            var path=getNavigation().createPath(candidate.x,candidate.y,candidate.z,0);
            if(path==null||!path.canReach())continue;
            level.sendParticles(ParticleTypes.REVERSE_PORTAL,getX(),getY()+1,getZ(),12,.3,.8,.3,.05);
            runtime.environment.sound(this,"teleport_begin");
            getNavigation().stop();setPos(candidate.x,candidate.y,candidate.z);setDeltaMovement(Vec3.ZERO);model.play("evade");
            runtime.environment.sound(this,"teleport_end");
            return;
        }
    }
    private void tickWarp(ServerLevel level) {
        if(warpTicks==24)runtime.environment.sound(this,"teleport_begin");
        warpTicks--;
        if(warpTicks%4==0)level.sendParticles(ParticleTypes.REVERSE_PORTAL,getX(),getY()+getBbHeight()/2,getZ(),12,2,2,2,.05);
        if(warpTicks==8) {
            Vec3 at=warpDestination;
            if(at!=null && runtime.environment.commitSepiksWarp(this, at)) {
                setPos(at.x,at.y,at.z); runtime.environment.sound(this,"teleport_end");
            }
        }
        if(warpTicks==0)warpDestination=null;
    }
    @Override public boolean hurtServer(ServerLevel level,DamageSource source,float amount) {
        if(runtime==null||runtime.paused()||isDeadOrDying())return false;
        var attacker = source.getEntity();
        if (!(attacker instanceof ServerPlayer p && runtime.member(p))
                && !(attacker instanceof DevilsMob mob && runtime.validTarget(mob, damageOwner()))) return false;
        if(attacker instanceof ServerPlayer player && amount>0) damageOwner().focusPlayer(player);
        if(root!=null) {
            return root.hitRegion(region,source,amount)>0;
        }
        if(warpTicks>0) { level.sendParticles(ParticleTypes.CRIT,getX(),getEyeY(),getZ(),2,.3,.3,.3,0); return false; }
        if(walker!=null)return hitRegion(DevilsWalkerState.Region.HULL,source,amount)>0;
        float allowed=(float)runtime.director.get().allowedDamage(ref,getHealth(),amount);
        if(allowed<=0)return false;
        float shieldBefore=getAbsorptionAmount();
        boolean accepted=super.hurtServer(level,source,allowed);
        if(accepted) {
            if(kind==DevilsPlan.Kind.CAPTAIN&&shieldBefore>0&&getAbsorptionAmount()<=0)blinkPending=true;
            runtime.director.get().healthChanged(ref,getHealth(),getAbsorptionAmount());
            if(kind==DevilsPlan.Kind.BRIG && !armorOpen && getHealth()<=getMaxHealth()*.5) {
                armorOpen=true; model.play("armor_break"); model.armorOpen();
                runtime.environment.sound(this,"armor_break");
                level.sendParticles(ParticleTypes.EXPLOSION,getX(),getY()+3,getZ(),1,0,0,0,0);
            }
            if(isAlive()) {
                if(model!=null)model.hit();
                runtime.environment.sound(this,"hurt");
            }
        }
        return accepted;
    }
    private float hitRegion(DevilsWalkerState.Region region,DamageSource source,float amount) {
        double allowed=runtime.director.get().allowedDamage(ref,getHealth(),amount);
        if(allowed<=0||walker==null||isDeadOrDying())return 0;
        var owner=source.getEntity();var direct=source.getDirectEntity();
        Object key=kim.biryeong.destiny.combat.Combat.damageEmission(source);
        if(key==null)key=new ShotKey(owner==null?null:owner.getUUID(),direct==null?null:direct.getUUID(),level().getServer().getTickCount());
        var hit=walker.hit(region,allowed,key);
        if(hit.applied()<=0)return 0;
        if(hit.legBroken()) {windup=0;burst=0;secondaryWindup=secondaryBurst=0;model.play("leg_break");}
        if(!region.leg()) {
            setHealth((float)walker.core());
            runtime.director.get().healthChanged(ref,getHealth(),0);
            if(hit.killed())die(source);
        }
        model.hit();return (float)hit.applied();
    }
    boolean spawnParts() {
        for(var region:DevilsWalkerState.Region.values()) {
            if(region==DevilsWalkerState.Region.HULL)continue;
            var part=new DevilsMob(DevilsActors.PART,level());
            part.root=this;part.runtime=runtime;part.slot=slot;part.ref=ref;part.region=region;part.noPhysics=true;
            part.getAttribute(Attributes.MAX_HEALTH).setBaseValue(100000);part.setHealth(100000);
            parts.add(part);
        }
        placeParts();
        for(var part:parts)if(!((ServerLevel)level()).addFreshEntity(part))return false;
        return true;
    }
    private void placeParts() {
        for(var part:parts) {
            int i=part.region.ordinal();
            double x=i<6?(i%2==0?-3.1:3.1):0, z=i<6?3.0-(i/2)*3.0:1.7, y=i<6?.3:2.4;
            double yaw=Math.toRadians(-getYRot());
            Vec3 at=position().add(x*Math.cos(yaw)-z*Math.sin(yaw),y,x*Math.sin(yaw)+z*Math.cos(yaw));
            part.setPos(at.x,at.y,at.z);part.setYRot(getYRot());
            if(part.isAlive())part.setHealth(part.getMaxHealth());
        }
    }
    @Override public void die(DamageSource source) {
        if(deathReported)return;deathReported=true;
        super.die(source);deathDuration=model==null?24:model.deathTicks();if(runtime!=null&&root==null)runtime.environment.sound(this,"death");if(model!=null)model.play("death");
        for(var part:parts)part.discard();parts.clear();bolts.clear();hazard=null;
        if(runtime!=null&&root==null)runtime.removed(this,true);
    }
    @Override protected void tickDeath() {
        deathTime++;
        if(kind.boss()&&deathTime%8==0&&level() instanceof ServerLevel level)
            level.sendParticles(ParticleTypes.EXPLOSION,getX(),getY()+getBbHeight()*.5,getZ(),1,1,1,1,0);
        if(deathTime>=deathDuration)remove(RemovalReason.KILLED);
    }
    @Override public void onRemoval(RemovalReason reason) {
        super.onRemoval(reason);if(model!=null)model.close();
        for(var part:List.copyOf(parts))part.discard();parts.clear();bolts.clear();
        if(runtime!=null&&root==null&&!deathReported)runtime.removed(this,false);
    }
    @Override protected void onBelowWorld(){discard();}
    @Override public boolean isNoGravity(){return root!=null||DevilsActors.flying(kind)||kind==DevilsPlan.Kind.WALKER||super.isNoGravity();}
    @Override public boolean shouldBeSaved(){return false;}
    @Override public void checkDespawn(){}
    @Override public boolean removeWhenFarAway(double distance){return false;}
    @Override protected boolean shouldDropLoot(ServerLevel level){return false;}
    @Override public boolean causeFallDamage(double d,float m,DamageSource source){return false;}
    @Override protected SoundEvent getAmbientSound(){return null;}
    @Override public Component getName(){return Component.literal(switch(kind){case DREG->"드렉";case VANDAL->"반달";case SHANK->"생크";case MARAUDER->"약탈자";case CAPTAIN->"대장";case THRALL->"스랄";case ACOLYTE->"시종";case KNIGHT->"기사";case WIZARD->"마법사";case SERVITOR->"보호막 서비터";case BRIG->"브리그";case WALKER->"악마의 워커";case SEPIKS->"세픽스 프라임";});}
    @Override public EntityType<?> getPolymerEntityType(PacketContext context){return EntityTypes.ZOMBIE;}
    @Override public boolean sendPacketsTo(ServerPlayer player){return root==null;}
    @Override public void modifyRawTrackedData(List<SynchedEntityData.DataValue<?>> data,ServerPlayer player,boolean initial){
        boolean found=false;
        for(int i=0;i<data.size();i++){var value=data.get(i);if(value.id()==DATA_SHARED_FLAGS_ID.id()&&value.value() instanceof Byte b){data.set(i,SynchedEntityData.DataValue.create(DATA_SHARED_FLAGS_ID,(byte)(b|32)));found=true;}}
        if(initial&&!found)data.add(SynchedEntityData.DataValue.create(DATA_SHARED_FLAGS_ID,(byte)(entityData.get(DATA_SHARED_FLAGS_ID)|32)));
    }
}
