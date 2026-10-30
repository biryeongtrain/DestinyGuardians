package kim.biryeong.destiny.ability.hunter;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ChunkAttachment;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.AmmoGeneration;
import kim.biryeong.destiny.weapon.SwordTiming;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.*;
import org.joml.Vector3f;
import java.util.*;

/** W230. Four separately equipped supers; source contacts remain explicit provisional cues. */
public final class HunterExpandedSupers {
    public static final Identifier BLADE_BARRAGE = id("blade_barrage");
    public static final Identifier SPECTRAL_BLADES = id("spectral_blades");
    public static final Identifier GATHERING_STORM = id("gathering_storm");
    public static final Identifier STORMS_EDGE = id("storms_edge");
    private enum Kind { BARRAGE, SPECTRAL, GATHERING, EDGE }
    private static final Map<ServerPlayer, Lease> OWNERS = new IdentityHashMap<>();
    private static final Map<ServerPlayer, Session> ACTIVE = new IdentityHashMap<>();
    private static final List<StaffField> FIELDS = new ArrayList<>();
    private static final List<EmbeddedKnife> KNIVES = new ArrayList<>();
    private HunterExpandedSupers() {}
    private static Identifier id(String name) { return DestinyGuardians.id("hunter/" + name); }
    public static void register() {
        AbilityRegistry.register(new Expanded(BLADE_BARRAGE, Element.SOLAR, "칼날 장전", Kind.BARRAGE));
        AbilityRegistry.register(new Expanded(SPECTRAL_BLADES, Element.VOID, "스펙트럼 칼날", Kind.SPECTRAL));
        AbilityRegistry.register(new Expanded(GATHERING_STORM, Element.ARC, "폭풍결집", Kind.GATHERING));
        AbilityRegistry.register(new Expanded(STORMS_EDGE, Element.ARC, "폭풍의 칼날", Kind.EDGE));
    }
    private static final class Expanded extends Ability {
        final Kind kind;
        Expanded(Identifier id, Element element, String name, Kind kind) {
            super(id, GuardianClass.HUNTER, AbilitySlot.SUPER, element, 556, name); this.kind = kind;
        }
        @Override public boolean activate(ServerPlayer p) {
            if (AbilityService.inSuper(p) || ACTIVE.containsKey(p) || !eligible(p, this)) return false;
            // A fresh accepted activation retires previous fields of this particular owner only.
            cleanup(p);
            if (!ClassAbilityEffects.beginSuper(p, element(), id().getPath())) return false;
            Lease lease = new Lease(p, this);
            Session session = new Session(lease, this);
            OWNERS.put(p, lease); ACTIVE.put(p, session);
            SuperCamera.blockMovement(p, session.windup);
            AbilityService.startSuper(p, session);
            return true;
        }
    }
    private static boolean eligible(ServerPlayer p, Ability a) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && Guardians.data(p).guardianClass() == GuardianClass.HUNTER
                && Objects.equals(Guardians.data(p).loadout().map(l -> l.get(AbilitySlot.SUPER)).orElse(null), a.id());
    }
    private static final class Lease {
        final ServerPlayer owner; final ServerLevel level; final GuardianData data;
        final GuardianRuntime runtime; final Loadout loadout; final Object connection;
        final Expanded ability;
        final Set<SimProjectile> flights = Collections.newSetFromMap(new IdentityHashMap<>());
        boolean cancelled; int emitted, impacts, blinks, volleys, contacts;
        Lease(ServerPlayer p, Expanded a) {
            owner=p; level=p.level(); data=Guardians.data(p); runtime=Guardians.runtime(p);
            loadout=data.loadout().orElseThrow(); connection=p.connection; ability=a;
        }
        boolean valid() {
            return !cancelled && owner.connection == connection && eligible(owner, ability)
                    && owner.level() == level && owner.getAttachedOrElse(Guardians.DATA, null) == data
                    && Guardians.runtimeIfPresent(owner).orElse(null) == runtime
                    && data.loadout().orElse(null) == loadout;
        }
    }
    /** Global field/flight lifecycle. Session time is independent and gameTime-idempotent. */
    public static void tick(MinecraftServer server) {
        for (Lease l : List.copyOf(OWNERS.values())) {
            if (!l.valid()) cleanup(l.owner);
            else l.flights.removeIf(SimProjectile::isDone);
        }
        for (StaffField f : List.copyOf(FIELDS)) if (!f.tick()) { f.destroy(); FIELDS.remove(f); }
        for (EmbeddedKnife k : List.copyOf(KNIVES)) if (!k.tick()) KNIVES.remove(k);
    }
    public static void cleanup(ServerPlayer p) {
        Lease l = OWNERS.remove(p);
        if (l != null) l.cancelled = true; // Revoke callbacks before detaching any displays.
        Session s = ACTIVE.remove(p);
        if (s != null) {
            Guardians.runtimeIfPresent(p).ifPresent(r -> { if (r.superSession == s) r.superSession = null; });
            s.end();
        }
        for (StaffField f : List.copyOf(FIELDS)) if (f.lease.owner == p) { f.destroy(); FIELDS.remove(f); }
        KNIVES.removeIf(k -> k.lease.owner == p);
        if (l != null) { for (SimProjectile f : List.copyOf(l.flights)) f.cancel(); l.flights.clear(); }
    }
    public static void clearAll() { for (ServerPlayer p : List.copyOf(OWNERS.keySet())) cleanup(p); }
    public static String status(ServerPlayer p) {
        Lease l = OWNERS.get(p); Session s = ACTIVE.get(p);
        return "active=" + (s != null) + " id=" + (l == null ? "none" : l.ability.id())
                + " emitted=" + (l == null ? 0 : l.emitted) + " impacts=" + (l == null ? 0 : l.impacts)
                + " volleys=" + (l == null ? 0 : l.volleys) + " blinks=" + (l == null ? 0 : l.blinks)
                + " contacts=" + (l == null ? 0 : l.contacts) + " fields=" + fieldCount(p)
                + " embedded=" + KNIVES.stream().filter(k -> k.lease.owner == p).count()
                + " flights=" + (l == null ? 0 : l.flights.stream().filter(f -> !f.isDone()).count())
                + " charges=" + (s == null ? 0 : s.charges) + " cloaked=" + (s != null && s.cloaked())
                + " invisibility=" + p.hasEffect(MobEffects.INVISIBILITY)
                + " cloakOwned=" + (s != null && s.cloak != null && s.cloak.ownsCurrent())
                + " aiDrops=" + (s == null || s.cloak == null ? 0 : s.cloak.aiDrops);
    }
    public static int fieldCount(ServerPlayer p) { return (int) FIELDS.stream().filter(f -> f.lease.owner == p).count(); }
    public static int emitted(ServerPlayer p) { Lease l=OWNERS.get(p); return l == null ? 0 : l.emitted; }
    public static int blinkCount(ServerPlayer p) { Lease l=OWNERS.get(p); return l == null ? 0 : l.blinks; }
    public static Vec3 fieldOrigin(ServerPlayer p) {
        return FIELDS.stream().filter(f -> f.lease.owner == p).map(f -> f.origin).findFirst().orElse(null);
    }
    private static double value(Ability a, String key, double fallback, double min, double max) {
        double v=a.param(key, fallback); return Double.isFinite(v) ? Math.clamp(v,min,max) : fallback;
    }
    private static int ticks(Ability a, String key, int fallback, int min, int max) {
        return (int) value(a,key,fallback,min,max);
    }
    private static boolean enemy(Lease l, LivingEntity e) {
        return e.level() == l.level && Combat.isEnemy(l.owner,e) && !l.owner.isAlliedTo(e)
                && !(e instanceof TamableAnimal tame && tame.isTame());
    }
    private static Vec3 center(LivingEntity e) { return e.position().add(0,e.getBbHeight()*.5,0); }
    private static boolean visible(Lease l, Vec3 from, Vec3 to) {
        return l.valid() && l.level.clip(new ClipContext(from,to,ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE,l.owner)).getType() == HitResult.Type.MISS;
    }
    private static List<LivingEntity> targets(Lease l, Vec3 origin, double radius) {
        if (!l.valid()) return List.of();
        return Combat.enemiesNear(l.level,l.owner,origin,radius).stream().filter(e -> enemy(l,e)
                && visible(l,origin,center(e))).limit(32).toList();
    }
    private static void damage(Lease l, LivingEntity e, float damage) {
        if (l.valid() && enemy(l,e)) Combat.damage(l.level,l.owner,e,damage,l.ability.element(),AmmoGeneration.SUPER);
    }
    private static Vec3 impactPoint(HitResult h) {
        if (h instanceof BlockHitResult b) {
            var d=b.getDirection(); return h.getLocation().add(d.getStepX()*.08,d.getStepY()*.08,d.getStepZ()*.08);
        }
        return h.getLocation();
    }
    private static void blast(Lease l, Vec3 at, double radius, float damage) {
        for (LivingEntity e : targets(l,at,radius)) damage(l,e,damage);
        ClassAbilityEffects.burst(l.owner,at,l.ability.element(),radius);
    }
    /**
     * Identity-owned vanilla cloak. MobEffectInstance.update can mutate the same live object when
     * another source adds invisibility; token identity alone is insufficient to distinguish that.
     * A foreign update irrevocably relinquishes ownership, even if its value/flags are identical.
     */
    private static final class CloakEffect extends MobEffectInstance {
        final Object token;
        boolean foreignUpdate;
        CloakEffect(Object token) {
            super(MobEffects.INVISIBILITY,4,0,true,false,false);
            this.token=token;
        }
        @Override public boolean update(MobEffectInstance incoming) {
            if (!(incoming instanceof CloakEffect own && own.token == token)) foreignUpdate=true;
            return super.update(incoming);
        }
    }
    private static final class ScopedCloak {
        final Lease lease;
        final Object token=new Object();
        CloakEffect installed;
        int aiDrops;
        ScopedCloak(Lease lease) { this.lease=lease; }
        boolean ownsCurrent() {
            return installed!=null && !installed.foreignUpdate
                    && lease.owner.getEffect(MobEffects.INVISIBILITY)==installed;
        }
        void sync(boolean wanted) {
            if (!wanted || !lease.valid()) { release(); return; }
            MobEffectInstance current=lease.owner.getEffect(MobEffects.INVISIBILITY);
            if (current==null) {
                CloakEffect candidate=new CloakEffect(token);
                lease.owner.addEffect(candidate,lease.owner);
                installed=lease.owner.getEffect(MobEffects.INVISIBILITY)==candidate?candidate:null;
            } else if (ownsCurrent()) {
                // Short refresh bounds residue if shutdown interrupts cleanup. Never extend a foreign cloak.
                if (current.getDuration()<=2) lease.owner.addEffect(new CloakEffect(token),lease.owner);
            } else installed=null;
            if (!lease.owner.hasEffect(MobEffects.INVISIBILITY)) return;
            // Drop only this cloaked owner's nearby hostile aggro. Other targets/goals are untouched.
            // Inspect raw selection: getTarget() can mask a retained target after vanilla validity changes.
            // Vanilla visibility weighting remains authoritative outside this bounded aggro intervention.
            for (Mob mob : lease.level.getEntitiesOfClass(Mob.class,lease.owner.getBoundingBox().inflate(24),
                    mob -> enemy(lease,mob) && mob.getTargetUnchecked()==lease.owner).stream().limit(32).toList()) {
                mob.setTarget(null); aiDrops++;
            }
        }
        void release() {
            // Foreign pre-existing, force-replaced and same-object-refreshed effects are all preserved.
            if (ownsCurrent()) lease.owner.removeEffect(MobEffects.INVISIBILITY);
            installed=null;
        }
    }
    private static final class Session implements SuperSession {
        final Lease lease; final Expanded ability; final String path; final ScopedCloak cloak;
        final long started; final int windup, firstContact, secondContact;
        long endAt, nextAttack, lastTick=Long.MIN_VALUE, pendingAt=-1, decloakedUntil;
        boolean ended, firstDone, secondDone, heavyPending; int charges=3, combo, attackCount, visibleDrainRemainder;
        Session(Lease l, Expanded a) {
            lease=l; ability=a; path=a.id().getPath(); started=l.level.getGameTime();
            cloak=a.kind==Kind.SPECTRAL?new ScopedCloak(l):null;
            windup=ClassSuperModelAssets.durationTicks(path,"start", ticks(a,"cast_ticks",a.kind==Kind.BARRAGE?40:a.kind==Kind.SPECTRAL?30:a.kind==Kind.GATHERING?33:34,1,100)) + SwordTiming.START_TICKS;
            // Original game hit/release events are unavailable; these cue fractions are provisional.
            firstContact=Math.clamp(ticks(a,"first_contact_ticks",Math.max(1,(int)(windup*.45)),1,150),1,windup);
            secondContact=Math.clamp(ticks(a,"second_contact_ticks",Math.max(firstContact+1,(int)(windup*.72)),1,150),firstContact,windup);
            int duration=ticks(a,"duration_ticks",a.kind==Kind.SPECTRAL?470:a.kind==Kind.EDGE?400:windup+12,windup+1,1200);
            endAt=started+duration;
            nextAttack=started+windup;
        }
        private boolean live() { return !ended && lease.valid(); }
        private long now() { return lease.level.getGameTime(); }
        @Override public boolean tick() {
            if (!live() || now() >= endAt) return false;
            if (lastTick == now()) return true;
            lastTick=now(); long age=now()-started;
            ClassAbilityEffects.superTick(lease.owner,ability.element(),path,(int)age);
            switch (ability.kind) {
                case BARRAGE -> {
                    if (!firstDone && age >= firstContact) { firstDone=true; fan(-1); }
                    if (!secondDone && age >= secondContact) { secondDone=true; fan(1); }
                    // Cast recovers independently; finite knife/embedded leases finish after camera release.
                    if (secondDone && age >= windup) return false;
                }
                case GATHERING -> {
                    if (!firstDone && age >= firstContact) { firstDone=true; throwStaff(); }
                    // The separate lease owns the flight and field after camera recovery.
                    if (age >= windup) return false;
                }
                case EDGE -> {
                    if (!firstDone && age >= firstContact) { firstDone=true; charges--; dagger(); }
                    if (pendingAt >= 0 && now() >= pendingAt) { pendingAt=-1; dagger(); }
                    if (charges == 0 && pendingAt < 0 && now() >= nextAttack
                            && lease.flights.stream().allMatch(SimProjectile::isDone)) return false;
                }
                case SPECTRAL -> {
                    if (age >= windup && !cloaked() && ++visibleDrainRemainder >= 2) {
                        visibleDrainRemainder=0; endAt--; // DDC visible passive drain is 50% faster.
                    }
                    if (pendingAt >= 0 && now() >= pendingAt) { pendingAt=-1; slash(heavyPending); }
                    cloak.sync(cloaked());
                    if (cloaked() && age % 8 == 0) Fx.ring(lease.owner, lease.level,lease.owner.position().add(0,.12,0),.65,Element.VOID.color(),10);
                }
            }
            return true;
        }
        @Override public void primary() {
            if (!live() || now() >= endAt || now() < nextAttack || now()-started < windup || pendingAt >= 0) return;
            if (ability.kind == Kind.SPECTRAL) {
                heavyPending=lease.owner.isShiftKeyDown();
                String phase=heavyPending ? "attack3" : (combo++ & 1) == 1 ? "attack2" : "attack";
                playAttack(phase);
                int animation=clipTicks(phase,heavyPending?18:12);
                int contact=ticks(ability,heavyPending?"heavy_contact_ticks":phase.equals("attack2")?"attack2_contact_ticks":"attack_contact_ticks",heavyPending?3:phase.equals("attack2")?4:6,1,40)+SwordTiming.START_TICKS;
                pendingAt=now()+Math.min(contact,animation);
                nextAttack=now()+Math.max(animation,ticks(ability,"attack_interval_ticks",10,3,60));
                decloakedUntil=Long.MAX_VALUE; // Heavy contact restores the scoped cloak; light leaves it removed.
                cloak.sync(false);
                endAt=Math.max(now()+1,endAt-ticks(ability,heavyPending?"heavy_cost_ticks":"light_cost_ticks",heavyPending?35:10,0,120));
                SuperCamera.blockMovement(lease.owner,Math.min(animation,8));
            } else if (ability.kind == Kind.EDGE && charges > 0 && lease.flights.stream().allMatch(SimProjectile::isDone)) {
                charges--; playAttack("attack");
                int animation=clipTicks("attack",24);
                pendingAt=now()+Math.min(animation,ticks(ability,"attack_contact_ticks",10,1,60)+SwordTiming.START_TICKS);
                nextAttack=now()+animation;
                SuperCamera.blockMovement(lease.owner,animation);
            }
        }
        private int clipTicks(String phase,int fallback) {
            if (ability.kind==Kind.EDGE && phase.equals("attack")
                    && !ClassSuperModelAssets.hasClip(ClassSuperModelAssets.prefix(path)+"_attack")) phase="start";
            return ClassSuperModelAssets.durationTicks(path,phase,fallback)+SwordTiming.START_TICKS;
        }
        private void playAttack(String phase) {
            String clip=ClassSuperModelAssets.prefix(path)+"_"+phase;
            if (ability.kind==Kind.EDGE && phase.equals("attack") && !ClassSuperModelAssets.hasClip(clip))
                clip=ClassSuperModelAssets.prefix(path)+"_start";
            if (ClassSuperModelAssets.hasClip(clip)) PlayerAnimations.play(lease.owner,clip);
            else ClassAbilityEffects.attack(lease.owner,ability.element(),path);
        }
        boolean cloaked() { return ability.kind==Kind.SPECTRAL && now()-started>=windup && now()>=decloakedUntil; }
        private void fan(int side) {
            // Both knife fans belong to one cast cue; do not layer the full clip on the second fan.
            if (++lease.volleys == 1) ClassAbilityEffects.sound(lease.owner,ability.element(),path,"super.fire");
            int count=ticks(ability,"knives_per_volley",7,3,9);
            Vec3 look=lease.owner.getLookAngle().normalize();
            Vec3 right=look.cross(new Vec3(0,1,0));
            if (right.lengthSqr()<.001) right=new Vec3(1,0,0); else right=right.normalize();
            for (int i=0;i<count;i++) {
                double offset=(i-(count-1)/2.0)*value(ability,"fan_spread",.055,.01,.15)+side*.015;
                Vec3 velocity=look.add(right.scale(offset)).normalize().scale(value(ability,"projectile_speed",1.5,.5,3));
                lease.emitted++;
                SimProjectile flight=SimProjectile.launch(lease.owner,lease.owner.getEyePosition(),velocity,.012,60,
                        ClassAbilityEffects.item(path),.65f,ability.element().color(),hit -> {
                            if (!lease.valid()) return;
                            lease.impacts++;
                            if (hit instanceof EntityHitResult entity && entity.getEntity() instanceof LivingEntity target)
                                damage(lease,target,(float)value(ability,"impact_damage",1,.1,10));
                            KNIVES.add(new EmbeddedKnife(lease,hit));
                        });
                lease.flights.add(flight);
            }
            // Finite projectile/embedded leases outlive this short cast camera.
            endAt=Math.max(endAt,started+windup+1);
        }
        private void throwStaff() {
            // R1d: the cast rig kept its staff after impact. Release only the matching virtual presentation.
            ClassAbilityEffects.releaseHand(lease.owner,path);
            lease.emitted++; ClassAbilityEffects.sound(lease.owner,ability.element(),path,"super.fire");
            lease.flights.add(SimProjectile.launch(lease.owner,lease.owner.getEyePosition(),
                    lease.owner.getLookAngle().scale(value(ability,"projectile_speed",1.65,.5,3)),.018,60,
                    ClassAbilityEffects.item(path),1.15f,ability.element().color(),hit -> {
                        if (!lease.valid()) return;
                        lease.impacts++; Vec3 at=impactPoint(hit);
                        // A lifetime miss is not a collision-stuck staff: leave no airborne field.
                        if (hit instanceof BlockHitResult b && lease.level.getBlockState(b.getBlockPos()).isAir()) return;
                        for (StaffField old : List.copyOf(FIELDS)) if (old.lease.owner==lease.owner) { old.destroy(); FIELDS.remove(old); }
                        blast(lease,at,value(ability,"radius",4,1,6),(float)value(ability,"impact_damage",15,.1,60));
                        FIELDS.add(new StaffField(lease,at));
                        ClassAbilityEffects.sound(lease.owner,ability.element(),path,"super.impact");
                    }));
        }
        private void slash(boolean heavy) {
            attackCount++; lease.contacts++; if (heavy) decloakedUntil=0;
            ClassAbilityEffects.sound(lease.owner,ability.element(),path,"super.fire");
            Vec3 eye=lease.owner.getEyePosition(), look=lease.owner.getLookAngle();
            double range=value(ability,heavy?"heavy_range":"range",heavy?4:3.3,1,5);
            for (LivingEntity e : targets(lease,eye,range)) {
                Vec3 delta=center(e).subtract(eye);
                if (delta.lengthSqr()<.01 || delta.normalize().dot(look) > (heavy?.15:.3))
                    damage(lease,e,(float)value(ability,heavy?"heavy_damage":"damage",heavy?18:11,.1,60));
            }
            ClassAbilityEffects.burst(lease.owner,eye.add(look.scale(1.5)),Element.VOID,heavy?2:1.2);
        }
        private void dagger() {
            lease.emitted++; ClassAbilityEffects.sound(lease.owner,ability.element(),path,"super.fire");
            lease.flights.add(SimProjectile.launch(lease.owner,lease.owner.getEyePosition(),
                    lease.owner.getLookAngle().scale(value(ability,"projectile_speed",2,.5,3)),0,25,
                    ClassAbilityEffects.item(path),.8f,ability.element().color(),hit -> {
                        if (!live()) return;
                        lease.impacts++; Vec3 at=impactPoint(hit);
                        Vec3 destination=safeBlink(lease,at,value(ability,"blink_range",15,2,20));
                        if (destination == null) { ClassAbilityEffects.burst(lease.owner,at,Element.ARC,1); return; }
                        lease.owner.teleportTo(destination.x,destination.y,destination.z);
                        lease.blinks++;
                        // Do not acquire gravity/flying/noPhysics or touch the real inventory.
                        blast(lease,lease.owner.position().add(0,1,0),value(ability,"radius",4,1,6),
                                (float)value(ability,"damage",20,.1,80));
                        playAttack("blink");
                        nextAttack=Math.max(nextAttack,now()+clipTicks("blink",12));
                        ClassAbilityEffects.sound(lease.owner,ability.element(),path,"super.impact");
                    }));
        }
        @Override public void end() {
            if (ended) return; ended=true;
            if (cloak!=null) cloak.release();
            ACTIVE.remove(lease.owner,this);
            if (ability.kind!=Kind.GATHERING && ability.kind!=Kind.BARRAGE) {
                for (SimProjectile f : List.copyOf(lease.flights)) f.cancel(); lease.flights.clear();
            }
            SuperCamera.blockMovement(lease.owner,0);
            ClassAbilityEffects.endSuper(lease.owner,ability.element(),path);
        }
        @Override public float remaining() {
            if (ended) return 0;
            return Math.clamp((float)(endAt-now())/Math.max(1,endAt-started),0f,1f);
        }
        @Override public java.util.OptionalInt ammunition() {
            return ability.kind==Kind.EDGE ? java.util.OptionalInt.of(charges) : java.util.OptionalInt.empty();
        }
        @Override public int ammunitionCapacity() { return ability.kind==Kind.EDGE ? 3 : 1; }
    }
    /** Safe swept player-volume route: three height rays, body collision samples and border/chunk guards. */
    private static Vec3 safeBlink(Lease l, Vec3 impact, double range) {
        Vec3 from=l.owner.position(); Vec3 toward=impact.subtract(l.owner.getEyePosition());
        if (toward.lengthSqr()<.01) return null;
        Vec3 back=toward.normalize().scale(-.8);
        Vec3 base=impact.add(back).add(0,-.8,0);
        for (double dy : new double[]{0,.5,1,-.5}) {
            Vec3 to=base.add(0,dy,0), delta=to.subtract(from);
            if (delta.length()>range || delta.length()<.3) continue;
            int steps=Math.max(1,(int)Math.ceil(delta.length()/.2)); boolean clear=true;
            for (int step=1;step<=steps && clear;step++) {
                Vec3 point=from.add(delta.scale((double)step/steps)); BlockPos bp=BlockPos.containing(point);
                AABB box=l.owner.getBoundingBox().move(point.subtract(from)).deflate(.01);
                clear=l.level.hasChunkAt(bp) && l.level.getWorldBorder().isWithinBounds(bp)
                        && l.level.noCollision(l.owner,box);
            }
            for (double height : new double[]{.1,.9,1.7})
                if (!visible(l,from.add(0,height,0),to.add(0,height,0))) clear=false;
            // Require reachable support within 1.5 blocks, instead of sending the body into a void.
            if (clear) {
                var support=l.level.clip(new ClipContext(to.add(0,.05,0),to.add(0,-1.5,0),
                        ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,l.owner));
                if (support.getType()!=HitResult.Type.MISS) return to;
            }
        }
        return null;
    }
    private static final class EmbeddedKnife {
        final Lease lease; final Vec3 origin; final LivingEntity target; final Vec3 local;
        final long detonate;
        EmbeddedKnife(Lease l,HitResult hit) {
            lease=l; origin=impactPoint(hit);
            target=hit instanceof EntityHitResult e && e.getEntity() instanceof LivingEntity living ? living : null;
            local=target==null?Vec3.ZERO:origin.subtract(target.position());
            detonate=l.level.getGameTime()+ticks(l.ability,"detonation_delay_ticks",10,1,40);
        }
        boolean tick() {
            if (!lease.valid()) return false;
            if (lease.level.getGameTime()<detonate) return true;
            Vec3 at=target!=null && !target.isRemoved() && target.level()==lease.level?target.position().add(local):origin;
            blast(lease,at,value(lease.ability,"radius",2.2,.5,4),(float)value(lease.ability,"damage",8,.1,40));
            return false;
        }
    }
    private static final class StaffField {
        final Lease lease; final Vec3 origin,visualOrigin; final long started,expires;
        final ElementHolder holder; long lastTick=Long.MIN_VALUE, nextPulse; boolean destroyed, struck;
        StaffField(Lease l,Vec3 at) {
            lease=l; origin=at; started=l.level.getGameTime();
            var ground=l.level.clip(new ClipContext(at,at.add(0,-8,0),ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,l.owner));
            visualOrigin=ground.getType()==HitResult.Type.MISS?at:ground.getLocation().add(0,.025,0);
            expires=started+ticks(l.ability,"lightning_delay_ticks",40,0,100)
                    +ticks(l.ability,"field_delay_ticks",24,0,100)+ticks(l.ability,"field_duration_ticks",160,20,600);
            nextPulse=started+ticks(l.ability,"lightning_delay_ticks",40,0,100)+ticks(l.ability,"field_delay_ticks",24,0,100);
            holder=new ElementHolder();
            ItemDisplayElement display=new AbilityDisplayElement(l.owner,ClassAbilityEffects.item("hunter/gathering_storm_embedded"));
            display.setItemDisplayContext(ItemDisplayContext.NONE);
            display.setScale(new Vector3f(1f)); display.setTeleportDuration(1);
            holder.addElement(display);
            try { ChunkAttachment.ofTicking(holder,l.level,visualOrigin); }
            catch (RuntimeException ex) { holder.destroy(); throw ex; }
        }
        boolean tick() {
            long now=lease.level.getGameTime();
            if (destroyed || !lease.valid() || now>=expires) return false;
            if (lastTick==now) return true; lastTick=now;
            double radius=value(lease.ability,"radius",4,1,6);
            if ((now-started)%5==0) Fx.ring(lease.owner, lease.level,visualOrigin,radius,Element.ARC.color(),28);
            if (!struck && now>=started+ticks(lease.ability,"lightning_delay_ticks",40,0,100)) {
                struck=true;
                blast(lease,origin,radius,(float)value(lease.ability,"lightning_damage",12,.1,60));
                ClassAbilityEffects.sound(lease.owner,Element.ARC,lease.ability.id().getPath(),"super.impact");
            }
            if (now>=nextPulse) {
                nextPulse=now+ticks(lease.ability,"pulse_ticks",14,5,60);
                for (LivingEntity e : targets(lease,origin,radius)) {
                    damage(lease,e,(float)value(lease.ability,"pulse_damage",5,.1,30));
                    Fx.line(lease.owner, lease.level,origin,center(e),Element.ARC.color(),.18,1f);
                }
                // Local lightning stroke stops at the field, not at a global weather strike.
                var roof=lease.level.clip(new ClipContext(origin,origin.add(0,5,0),
                        ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,lease.owner));
                Vec3 top=roof.getType()==HitResult.Type.MISS?origin.add(0,5,0):roof.getLocation();
                Fx.line(lease.owner, lease.level,top,origin,Element.ARC.glow(),.2,1f);
            }
            holder.tick(); return true;
        }
        void destroy() { if (!destroyed) { destroyed=true; holder.destroy(); } }
    }
}
