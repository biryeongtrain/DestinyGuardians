package kim.biryeong.destiny.campaign.fallen;

import eu.pb4.polymer.core.api.entity.PolymerEntity;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.campaign.RisingServices;
import kim.biryeong.destiny.campaign.RisingServices.FallenKind;
import kim.biryeong.destiny.campaign.fallen.FallenArchetypes.Archetype;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/**
 * Server-side Fallen combatant (W300). A Polymer entity the vanilla client sees as an always-invisible zombie;
 * the visible body is a BetterModel tracker. The server bounding box is the real hit volume, so the existing
 * hitscan/projectile/ability systems damage it unchanged, and WeaponPrecision grants head crits on the top quarter
 * once the type is in {@code destiny:weapon_precision_humanoids}.
 * Roles: infantry/shank (AI in {@link FallenBrain}), Walker anchor (AI in {@link WalkerBoss.Runtime}) and Walker
 * hit-region parts (no AI, never sent to clients).
 */
public class FallenMob extends Monster implements PolymerEntity {
    enum Role { INFANTRY, WALKER, WALKER_PART }

    private static final int INVISIBLE_BIT = 1 << 5;

    final FallenKind kind;
    final Role role;
    private Archetype archetype;
    private RisingServices.Difficulty tuning;
    private RisingServices.FallenListener listener;
    private boolean configured, active = true, defeatedFired, lostFired, spawnPlayed;
    private Vec3 home;
    private FallenBrain brain;
    private FallenModels models;
    private boolean modelAttached;
    private FallenHealthBars healthBar;
    private WalkerBoss.Runtime boss;
    // Walker part state
    private WalkerBoss.Runtime owner;
    private WalkerBoss.Region region;
    private WalkerBoss.Box partBox;
    private int deathDuration = 24;

    public FallenMob(EntityType<? extends FallenMob> type, Level level) {
        super(type, level);
        this.kind = RisingFallen.kindOf(type);
        this.role = type == RisingFallen.WALKER_PART ? Role.WALKER_PART
                : kind == FallenKind.WALKER ? Role.WALKER : Role.INFANTRY;
        this.archetype = FallenArchetypes.of(kind);
        this.xpReward = 0;
        this.models = FallenModels.detached(this);
        setPersistenceRequired();
        if (role != Role.INFANTRY || archetype.flying()) setNoGravity(true);
        if (role == Role.WALKER_PART) { setSilent(true); noPhysics = true; }
        if (role == Role.WALKER) noPhysics = true;
    }

    // ------------------------------------------------------------------------------------------ configuration

    void configure(Archetype base, RisingServices.Difficulty tuning, RisingServices.FallenListener listener) {
        this.tuning = tuning;
        this.archetype = base.tuned(tuning);
        this.listener = listener;
        this.configured = true;
        this.home = position();
        setAttribute(Attributes.MAX_HEALTH, role == Role.INFANTRY ? archetype.health() : 1000);
        setAttribute(Attributes.MOVEMENT_SPEED, archetype.walkSpeed());
        setAttribute(Attributes.FOLLOW_RANGE, 48);
        setAttribute(Attributes.KNOCKBACK_RESISTANCE, archetype.knockbackResistance());
        setAttribute(Attributes.ARMOR, 0);
        setAttribute(Attributes.STEP_HEIGHT, role == Role.INFANTRY ? 1.0 : 0);
        if (archetype.shield() > 0) setAttribute(Attributes.MAX_ABSORPTION, archetype.shield());
        setHealth(getMaxHealth());
        if (archetype.shield() > 0) setAbsorptionAmount((float) archetype.shield());
        if (role == Role.INFANTRY) brain = new FallenBrain(this);
        if (role == Role.WALKER) boss = WalkerBoss.create(this, tuning);
    }

    void bindPart(WalkerBoss.Runtime owner, WalkerBoss.Region region, WalkerBoss.Box box) {
        this.owner = owner;
        this.region = region;
        this.partBox = box;
        this.configured = true;
        this.archetype = FallenArchetypes.of(FallenKind.WALKER);
        setAttribute(Attributes.MAX_HEALTH, 1000);
        setAttribute(Attributes.KNOCKBACK_RESISTANCE, 1);
        setHealth(getMaxHealth());
        refreshDimensions();
    }

    private void setAttribute(net.minecraft.core.Holder<net.minecraft.world.entity.ai.attributes.Attribute> attr, double v) {
        var inst = getAttribute(attr);
        if (inst != null) inst.setBaseValue(v);
    }

    Archetype archetype() { return archetype; }
    FallenModels models() { return models; }
    Vec3 home() { return home == null ? position() : home; }
    public FallenKind fallenKind() { return kind; }
    public boolean isWalkerPart() { return role == Role.WALKER_PART; }
    public WalkerBoss.Runtime walker() { return boss; }
    boolean active() { return active; }

    void setActiveState(boolean value) {
        if (active == value) return;
        active = value;
        if (!value) {
            if (brain != null) brain.stop();
            getNavigation().stop();
            setDeltaMovement(Vec3.ZERO);
            models.base(FallenModels.Action.IDLE);
        }
    }

    void aggro(LivingEntity attacker) { if (brain != null) brain.aggro(attacker); }

    // ------------------------------------------------------------------------------------------ ticking

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (!configured) {
            // /summon or an unconfigured spawn: first-mission tuning, no listener.
            configure(FallenArchetypes.of(kind), RisingServices.Difficulty.FIRST_MISSION, null);
            if (role == Role.WALKER) boss.spawnParts();
        }
        if (role == Role.WALKER_PART) {
            if (owner == null || owner.disposing() || owner.anchor.isRemoved()) discard();
            return;
        }
        if (!modelAttached) { modelAttached = true; models.close(); models = FallenModels.attach(this, true); }
        if (!spawnPlayed) {
            spawnPlayed = true;
            FallenWeapons.spawnPuff(level, this);
            if (role == Role.INFANTRY) models.play(FallenModels.Action.SPAWN);
            models.base(FallenModels.Action.IDLE);
        }
        models.light(false);
        if (role != Role.WALKER_PART) {
            if (healthBar == null) healthBar = new FallenHealthBars(this);
            healthBar.tick(level);
        }
        if (role == Role.WALKER) { if (boss != null) boss.tick(level, active); return; }
        if (active && brain != null) brain.tick(level);
        else if (!active) getNavigation().stop();
    }

    /** Engaged Fallen keep their weapon on the target while strafing (BetterModel follows body yaw). */
    @Override
    protected void tickHeadTurn(float bodyRot) {
        float facing = brain == null || !active || isDeadOrDying() ? Float.NaN : brain.facing();
        if (Float.isNaN(facing)) { super.tickHeadTurn(bodyRot); return; }
        setYBodyRot(facing);
        setYHeadRot(facing);
    }

    // ------------------------------------------------------------------------------------------ damage

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (role == Role.WALKER_PART) {
            if (source.is(DamageTypeTags.BYPASSES_INVULNERABILITY) && source.getEntity() == null) return super.hurtServer(level, source, amount);
            if (owner == null || !(source.getEntity() instanceof LivingEntity)) return false;
            float shown = owner.partHit(region, source, amount, null);
            if (shown <= 0) return false;
            return super.hurtServer(level, source, shown);
        }
        if (role == Role.WALKER) {
            // The anchor is armored; only /kill style damage reaches it (and counts as a kill).
            if (source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
                if (boss != null) boss.dispose();
                return super.hurtServer(level, source, amount);
            }
            if (boss != null && source.getEntity() instanceof LivingEntity) boss.partHit(WalkerBoss.Region.HULL, source, amount, null);
            return false;
        }
        if (isDeadOrDying()) return false;
        float shieldBefore = getAbsorptionAmount();
        boolean result = super.hurtServer(level, source, amount);
        if (!result) return false;
        boolean broken = shieldBefore > 0 && getAbsorptionAmount() <= 0;
        if (shieldBefore > 0) {
            if (broken) FallenWeapons.shieldBreak(level, this); else FallenWeapons.shieldHit(level, this);
        } else FallenWeapons.hitSpark(level, this);
        models.tint();
        if (brain != null && isAlive() && active) brain.hurt(source, amount, broken);
        else if (isAlive()) models.play(FallenModels.Action.HIT);
        return true;
    }

    @Override
    public boolean isInvulnerableTo(ServerLevel level, DamageSource source) {
        // Environmental damage cannot quietly "defeat" required mission enemies (fall, suffocation, drowning).
        if (source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) return super.isInvulnerableTo(level, source);
        if (source.getEntity() == null && source.getDirectEntity() == null) return true;
        return super.isInvulnerableTo(level, source);
    }

    /** Walker death: the Machine reached zero core. Routes through the normal death path exactly once. */
    void bossKilled(DamageSource source) {
        if (isDeadOrDying()) return;
        setHealth(0);
        die(source);
    }

    @Override
    public void die(DamageSource source) {
        boolean first = !defeatedFired && role != Role.WALKER_PART;
        super.die(source);
        if (!first) return;
        defeatedFired = true;
        if (brain != null) brain.stop();
        getNavigation().stop();
        if (boss != null) boss.dispose();
        if (healthBar != null) healthBar.close();
        if (level() instanceof ServerLevel level && role == Role.INFANTRY) {
            FallenSounds.bark(this, FallenSounds.death(kind), true);
            if (archetype.flying()) FallenSounds.play(level, position().add(0, .5, 0), FallenSounds.Ev.SHANK_EXPLODE);
        }
        deathDuration = models.death(role == Role.WALKER ? 70 : 24);
        if (role == Role.WALKER) deathDuration = Math.max(deathDuration, 60);
        RisingFallen.released(this);
        notify(true);
    }

    @Override
    protected void tickDeath() {
        deathTime++;
        if (level() instanceof ServerLevel level) {
            if (role == Role.WALKER) {
                if (deathTime % 9 == 0) {
                    Vec3 at = position().add((random.nextDouble() - .5) * 4, 1 + random.nextDouble() * 4, (random.nextDouble() - .5) * 4);
                    level.sendParticles(net.minecraft.core.particles.ParticleTypes.EXPLOSION, at.x, at.y, at.z, 1, 0, 0, 0, 0);
                    FallenVfx.explosion(level, at, 1.6, FallenArchetypes.WALKER_ORANGE, false);
                    if (deathTime % 18 == 0) FallenSounds.play(level, at, FallenSounds.Ev.WALKER_LEG_EXPLO);
                }
            } else {
                if (deathTime == 1 && kind == FallenKind.SHANK) FallenVfx.shankBurst(level, position().add(0, getBbHeight() * .5, 0));
                if (deathTime == 12 && !archetype.flying())
                    FallenSounds.play(level, position().add(0, .3, 0), FallenSounds.bodyfall(kind));
                FallenWeapons.dissolve(level, this, deathTime, deathDuration);
            }
        }
        if (deathTime >= deathDuration && !isRemoved()) {
            // Walker: hide the model swap-out inside a final core blast instead of a silent pop.
            if (role == Role.WALKER && level() instanceof ServerLevel level) {
                Vec3 at = position().add(0, 2.5, 0);
                level.sendParticles(net.minecraft.core.particles.ParticleTypes.EXPLOSION_EMITTER, at.x, at.y, at.z, 1, 0, 0, 0, 0);
                FallenVfx.walkerDeath(level, at);
                FallenSounds.play(level, at, FallenSounds.Ev.WALKER_EXPLODE);
            }
            remove(RemovalReason.KILLED);
        }
    }

    @Override
    public void onRemoval(RemovalReason reason) {
        super.onRemoval(reason);
        models.close();
        if (healthBar != null) healthBar.close();
        if (boss != null) boss.dispose();
        RisingFallen.released(this);
        if (!defeatedFired && !lostFired && role != Role.WALKER_PART) {
            lostFired = true;
            notify(false);
        }
    }

    private void notify(boolean defeated) {
        if (listener == null) return;
        try {
            if (defeated) listener.defeated(this); else listener.lost(this);
        } catch (RuntimeException e) {
            DestinyGuardians.LOGGER.error("Fallen listener failed ({})", defeated ? "defeated" : "lost", e);
        }
    }

    // ------------------------------------------------------------------------------------------ vanilla behaviour

    /** Falling out of the world is a loss (director resets/respawns), never a kill. */
    @Override protected void onBelowWorld() { discard(); }

    /** Walker/parts/flyers never take gravity, even when /summon NBT resets the NoGravity flag. */
    @Override public boolean isNoGravity() { return role != Role.INFANTRY || archetype.flying() || super.isNoGravity(); }

    @Override public boolean shouldBeSaved() { return false; }
    @Override public boolean removeWhenFarAway(double distance) { return false; }
    @Override public void checkDespawn() { }
    @Override protected boolean shouldDropLoot(ServerLevel level) { return false; }
    @Override public boolean causeFallDamage(double distance, float multiplier, DamageSource source) { return false; }
    @Override public boolean isPushable() { return role == Role.INFANTRY && !archetype.flying(); }
    @Override public void push(Entity entity) { if (isPushable()) super.push(entity); }
    @Override protected SoundEvent getAmbientSound() { return null; }
    /** D2 barks replace the vanilla hurt/death sounds; the vanilla ones remain only if the D2 events are unmapped. */
    @Override protected SoundEvent getHurtSound(DamageSource source) {
        if (role != Role.INFANTRY || kim.biryeong.destiny.sound.DestinySounds.has(FallenSounds.hurt(kind).key())) return null;
        return archetype.flying() ? SoundEvents.IRON_GOLEM_HURT : SoundEvents.SPIDER_HURT;
    }
    @Override protected SoundEvent getDeathSound() {
        if (role != Role.INFANTRY || kim.biryeong.destiny.sound.DestinySounds.has(FallenSounds.death(kind).key())) return null;
        return archetype.flying() ? SoundEvents.IRON_GOLEM_DEATH : SoundEvents.SPIDER_DEATH;
    }
    @Override protected float getSoundVolume() { return .7f; }
    @Override public float getVoicePitch() { return archetype.kind() == FallenKind.CAPTAIN ? .7f : 1.15f; }
    @Override protected void playStepSound(BlockPos pos, BlockState state) {
        if (role == Role.INFANTRY && !archetype.flying()) super.playStepSound(pos, state);
    }

    @Override
    protected EntityDimensions getDefaultDimensions(Pose pose) {
        if (role == Role.WALKER_PART && partBox != null) return EntityDimensions.fixed(partBox.width(), partBox.height());
        return super.getDefaultDimensions(pose);
    }

    @Override
    public Component getName() {
        if (hasCustomName()) return super.getName();
        return Component.literal(switch (kind) {
            case DREG -> "드렉";
            case VANDAL -> "반달";
            case CAPTAIN -> "캡틴";
            case SHANK -> "생크";
            case WALKER -> "워커";
        });
    }

    // ------------------------------------------------------------------------------------------ Polymer

    @Override
    public EntityType<?> getPolymerEntityType(PacketContext context) { return net.minecraft.world.entity.EntityTypes.ZOMBIE; }

    /** Hit-region parts are server-only collision volumes. */
    @Override
    public boolean sendPacketsTo(ServerPlayer player) { return role != Role.WALKER_PART; }

    /** The vanilla base body is always invisible to clients; BetterModel (or the fallback display) is the body. */
    @Override
    public void modifyRawTrackedData(List<SynchedEntityData.DataValue<?>> data, ServerPlayer player, boolean initial) {
        boolean found = false;
        for (int i = 0; i < data.size(); i++) {
            var value = data.get(i);
            if (value.id() == DATA_SHARED_FLAGS_ID.id() && value.value() instanceof Byte b) {
                data.set(i, SynchedEntityData.DataValue.create(DATA_SHARED_FLAGS_ID, (byte) (b | INVISIBLE_BIT)));
                found = true;
            }
        }
        if (initial && !found)
            data.add(SynchedEntityData.DataValue.create(DATA_SHARED_FLAGS_ID, (byte) (entityData.get(DATA_SHARED_FLAGS_ID) | INVISIBLE_BIT)));
    }
}
