package kim.biryeong.destiny.ability.jump;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.Motion;
import kim.biryeong.destiny.ability.hunter.HunterJump;
import kim.biryeong.destiny.ability.titan.TitanJump;
import kim.biryeong.destiny.ability.warlock.WarlockJump;
import kim.biryeong.destiny.fx.ClassAbilityEffects;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

import static kim.biryeong.destiny.ability.jump.JumpPhysics.*;

/** Shared registration/lifecycle; no vanilla flight, gravity, or movement attribute ownership. */
public final class JumpAbilities {
    public static final Identifier HUNTER_HIGH = id("hunter/double_jump");
    public static final Identifier HUNTER_STRAFE = id("hunter/strafe_jump");
    public static final Identifier HUNTER_TRIPLE = id("hunter/triple_jump");
    public static final Identifier HUNTER_BLINK = id("hunter/blink");
    public static final Identifier TITAN_HIGH = id("titan/high_lift");
    public static final Identifier TITAN_STRAFE = id("titan/jump");
    public static final Identifier TITAN_CATAPULT = id("titan/catapult_lift");
    public static final Identifier WARLOCK_STRAFE = id("warlock/strafe_glide");
    public static final Identifier WARLOCK_BURST = id("warlock/burst_glide");
    public static final Identifier WARLOCK_BALANCED = id("warlock/jump");
    public static final Identifier WARLOCK_BLINK = id("warlock/blink");
    private static final Map<UUID, AirState> STATES = new HashMap<>();
    private static final Map<UUID, MovementSample> MOVEMENT = new HashMap<>();
    private static boolean registered;
    private JumpAbilities() { }
    private static Identifier id(String path) { return DestinyGuardians.id(path); }

    /** Replaces the old class registrars' four jump registrations, including their saved IDs. */
    public static void register() {
        if (registered) return;
        AbilityRegistry.register(new HunterJump(HUNTER_HIGH, "높은 점프", Mode.HUNTER_HIGH));
        AbilityRegistry.register(new HunterJump(HUNTER_STRAFE, "제어 점프", Mode.HUNTER_STRAFE));
        AbilityRegistry.register(new HunterJump(HUNTER_TRIPLE, "삼중 점프", Mode.HUNTER_TRIPLE));
        AbilityRegistry.register(new HunterJump(HUNTER_BLINK, "점멸 (아크)", Mode.HUNTER_BLINK));
        AbilityRegistry.register(new TitanJump(TITAN_HIGH, "높은 리프트", Mode.TITAN_HIGH));
        AbilityRegistry.register(new TitanJump());
        AbilityRegistry.register(new TitanJump(TITAN_CATAPULT, "도약 리프트", Mode.TITAN_CATAPULT));
        AbilityRegistry.register(new WarlockJump(WARLOCK_STRAFE, "제어 활공", Mode.WARLOCK_STRAFE));
        AbilityRegistry.register(new WarlockJump(WARLOCK_BURST, "폭발 활공", Mode.WARLOCK_BURST));
        AbilityRegistry.register(new WarlockJump(WARLOCK_BALANCED));
        AbilityRegistry.register(new WarlockJump(WARLOCK_BLINK, "점멸 (공허)", Mode.WARLOCK_BLINK));
        registered = true;
    }

    private static final class AirState {
        final ServerPlayer owner;
        final ServerLevel level;
        final Budget budget = new Budget();
        Ability ability;
        Loadout loadout;
        double acceleration, ceiling, descent, horizontalLimit;
        GlideCarry glide;
        AirState(ServerPlayer owner) { this.owner = owner; level = owner.level(); }
        boolean alive() {
            return owner.isAlive() && !owner.isRemoved() && !owner.hasDisconnected()
                    && !owner.isSpectator() && owner.level() == level;
        }
        void cancel() { budget.cancel(); ability = null; loadout = null; glide = null; }
    }

    /** Track all connected players before their first air-jump, not only active ability sessions. */
    private static final class MovementSample {
        final ServerPlayer owner;
        final ServerLevel level;
        final MotionTracker tracker;
        MovementSample(ServerPlayer player, long now) {
            owner = player; level = player.level();
            tracker = new MotionTracker(position(player), now);
        }
        MotionEstimate sample(long now) {
            Vec3 known = owner.getKnownMovement();
            return tracker.observe(now, position(owner), new Velocity(known.x, known.y, known.z), owner.onGround());
        }
        private static Displacement position(ServerPlayer player) {
            Vec3 position = player.position();
            return new Displacement(position.x, position.y, position.z);
        }
    }

    private static MovementSample track(ServerPlayer player, long now) {
        MovementSample sample = MOVEMENT.get(player.getUUID());
        if (sample == null || sample.owner != player || sample.level != player.level()) {
            sample = new MovementSample(player, now); MOVEMENT.put(player.getUUID(), sample);
        }
        return sample;
    }

    private static MotionEstimate momentum(ServerPlayer player, long now) {
        return track(player, now).sample(now);
    }

    private static boolean airborne(ServerPlayer player) {
        return !player.onGround() && !player.getAbilities().flying && !player.isNoGravity()
                && !player.isInWater() && !player.isInLava() && !player.isPassenger()
                && !player.onClimbable() && !player.isFallFlying();
    }

    private static boolean selected(ServerPlayer player, Ability ability) {
        return Guardians.data(player).guardianClass() == ability.guardianClass()
                && Objects.equals(AbilityService.idOf(player, AbilitySlot.JUMP), ability.id())
                && (ability.element() == Element.KINETIC
                || CharacterLoadouts.subclass(Guardians.data(player)) == ability.element());
    }

    /** Shared entry for the old public constructors and every new selectable variant. */
    public static boolean activate(ServerPlayer player, Ability ability, Mode mode) {
        if (!player.isAlive() || player.isRemoved() || player.hasDisconnected() || player.isSpectator()
                || !airborne(player) || !selected(player, ability)
                || kim.biryeong.destiny.camera.SuperCamera.movementBlocked(player)) return false;
        AirState state = STATES.get(player.getUUID());
        if (state != null && (state.owner != player || !state.alive())) {
            STATES.remove(player.getUUID()); state = null;
        }
        if (state == null) { state = new AirState(player); STATES.put(player.getUUID(), state); }
        int now = state.level.getServer().getTickCount();
        // A failed collision probe consumes neither a Blink charge nor airborne fuel.
        Vec3 destination = mode.kind == Kind.BLINK ? blinkDestination(player, ability) : null;
        if (mode.kind == Kind.BLINK && destination == null) return false;
        int duration = (int) value(ability, "duration_ticks", mode.duration, 1, 100);
        Press press = state.budget.press(mode, now, duration);
        if (press == Press.REJECTED) return false;
        if (press == Press.STOPPED) { state.cancel(); return true; }
        state.ability = ability;
        state.loadout = Guardians.data(player).loadout().orElse(null);
        state.acceleration = value(ability, "acceleration", mode.acceleration, .081, .16);
        state.ceiling = value(ability, "max_up_speed", mode.verticalLimit, .1, .8);
        state.descent = value(ability, "descent_speed", mode.verticalLimit, .06, .5);
        MotionEstimate observed = momentum(player, now);
        Velocity current = observed.velocity(), velocity = current;
        Vec3 direction = inputDirection(player);
        state.horizontalLimit = Math.max(mode.horizontalSpeed, current.horizontalSpeed());
        switch (mode.kind) {
            case HUNTER -> {
                double strength = ability instanceof HunterJump jump ? jump.strength() : mode.impulse;
                double carry = value(ability, "horizontal_carry", 1, .25, 1.25);
                velocity = hunter(mode, new Velocity(current.x() * carry, current.y(), current.z() * carry),
                        direction.x, direction.z, strength);
                Guardians.runtime(player).airJumpsUsed++;
                move(player, velocity);
            }
            case LIFT -> {
                velocity = steer(velocity, direction.x, direction.z,
                        mode == Mode.TITAN_CATAPULT ? .18 : mode.steering, mode.horizontalSpeed);
                move(player, new Velocity(velocity.x(), liftStart(mode, current.y()), velocity.z()));
                Guardians.runtime(player).airJumpsUsed++;
            }
            case GLIDE -> {
                if (mode == Mode.WARLOCK_BURST) velocity = burstGlide(velocity, direction.x, direction.z, mode.horizontalSpeed);
                else velocity = steer(velocity, direction.x, direction.z, mode.steering, mode.horizontalSpeed);
                state.glide = new GlideCarry();
                double vertical = state.glide.apply(now, observed, state.descent, ceilingBlocked(player));
                move(player, new Velocity(velocity.x(), vertical, velocity.z()));
                Guardians.runtime(player).airJumpsUsed++;
            }
            case BLINK -> {
                Vec3 start = player.position();
                player.teleportTo(destination.x, destination.y, destination.z);
                MOVEMENT.put(player.getUUID(), new MovementSample(player, now));
                // Teleport has no additional launch impulse; preserve the accepted incoming velocity.
                Motion.setVelocity(player, new Vec3(current.x(), current.y(), current.z()));
                player.resetFallDistance();
                Fx.line(player, state.level, start.add(0, .9, 0), destination.add(0, .9, 0), ability.element().glow(), .2, .6f);
                Guardians.runtime(player).airJumpsUsed++;
            }
        }
        effects(player, ability);
        return true;
    }

    public static void tick(MinecraftServer server) {
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            track(player, server.getTickCount()).sample(server.getTickCount());
        }
        MOVEMENT.values().removeIf(sample -> sample.level.getServer() == server
                && (!sample.owner.isAlive() || sample.owner.isRemoved() || sample.owner.hasDisconnected()
                || sample.owner.level() != sample.level));
        for (AirState state : List.copyOf(STATES.values())) {
            if (state.level.getServer() == server) tick(state, server.getTickCount());
        }
    }

    /** WarlockAbilities' no-argument compatibility hook; common tick can run before or after it. */
    public static void tickLegacyWarlock() {
        for (AirState state : List.copyOf(STATES.values())) {
            tick(state, state.level.getServer().getTickCount());
        }
    }

    private static void tick(AirState state, long now) {
        ServerPlayer player = state.owner;
        if (!state.alive()) { STATES.remove(player.getUUID(), state); return; }
        if (!state.budget.observe(now, player.onGround())) return;
        if (player.onGround()) {
            state.cancel(); Guardians.runtime(player).airJumpsUsed = 0; return;
        }
        if (state.budget.active() == null) return;
        if (!airborne(player) || state.ability == null || !selected(player, state.ability)
                || !Objects.equals(state.loadout, Guardians.data(player).loadout().orElse(null))
                || kim.biryeong.destiny.camera.SuperCamera.movementBlocked(player)) {
            state.cancel(); return;
        }
        Mode mode = state.budget.active();
        if (!state.budget.propel(now)) return;
        MotionEstimate observed = momentum(player, now);
        Velocity current = capHorizontal(observed.velocity(), state.horizontalLimit);
        Vec3 direction = inputDirection(player);
        Velocity velocity = steer(current, direction.x, direction.z, mode.steering, state.horizontalLimit);
        double vertical = mode.kind == Kind.LIFT ? liftTick(current.y(), state.acceleration, state.ceiling)
                : state.glide.apply(now, observed, state.descent, ceilingBlocked(player));
        move(player, new Velocity(velocity.x(), vertical, velocity.z()));
        if (now % 4 == 0) {
            Element element = CharacterLoadouts.subclass(Guardians.data(player));
            Fx.burst(player, state.level, player.position(), element == null ? Element.KINETIC : element, 3, .15);
        }
    }

    public static boolean active(ServerPlayer player, Kind kind) {
        AirState state = STATES.get(player.getUUID());
        return state != null && state.owner == player && state.alive() && airborne(player)
                && state.budget.active() != null && state.budget.active().kind == kind
                && state.ability != null && selected(player, state.ability)
                && Objects.equals(state.loadout, Guardians.data(player).loadout().orElse(null));
    }

    /** Menu cleanup cancels thrust only. Death/disconnect/dimension change retires the whole epoch. */
    public static void cleanup(ServerPlayer player) {
        MovementSample movement = MOVEMENT.get(player.getUUID());
        if (movement != null && movement.owner == player && (!player.isAlive() || player.isRemoved()
                || player.hasDisconnected() || player.level() != movement.level)) MOVEMENT.remove(player.getUUID());
        AirState state = STATES.get(player.getUUID());
        if (state == null || state.owner != player) return;
        if (!state.alive()) STATES.remove(player.getUUID(), state);
        else {
            state.cancel();
            if (player.onGround()) state.budget.observe(state.level.getServer().getTickCount(), true);
        }
    }

    public static void clearAll() { STATES.clear(); MOVEMENT.clear(); }

    private static Vec3 inputDirection(ServerPlayer player) {
        var input = Guardians.runtime(player).lastInput;
        return !input.forward() && !input.backward() && !input.left() && !input.right()
                ? Vec3.ZERO : Motion.inputDirection(player, input);
    }

    private static void move(ServerPlayer player, Velocity velocity) {
        Motion.setVelocity(player, new Vec3(velocity.x(), velocity.y(), velocity.z()));
        player.resetFallDistance();
    }

    private static boolean ceilingBlocked(ServerPlayer player) {
        return !player.level().noCollision(player, player.getBoundingBox().move(0, .05, 0));
    }

    private static double value(Ability ability, String key, double fallback, double min, double max) {
        return finite(ability.param(key, fallback), fallback, min, max);
    }

    private static void effects(ServerPlayer player, Ability ability) {
        Element element = ability.element() == Element.KINETIC ? CharacterLoadouts.subclass(Guardians.data(player)) : ability.element();
        if (element == null) element = Element.KINETIC;
        Fx.burst(player, player.level(), player.position(), element, 8, .22);
        ClassAbilityEffects.sound(player, element, "jump");
    }

    private static Vec3 blinkDestination(ServerPlayer player, Ability ability) {
        double range = value(ability, "blink_range", 5.25, .5, 5.25);
        double verticalLimit = value(ability, "blink_vertical_limit", 2.5, .1, 2.5);
        // Aim defines direction (MC adaptation); cap vertical displacement without enlarging range.
        Vec3 look = player.getLookAngle();
        Displacement desired = blinkVector(look.x, look.y, look.z, range, verticalLimit);
        Displacement safe = sweepBlink(desired, (previous, next) -> {
            AABB from = player.getBoundingBox().move(previous.x(), previous.y(), previous.z());
            AABB to = player.getBoundingBox().move(next.x(), next.y(), next.z());
            return clear(player, from.minmax(to));
        });
        return safe.length() < .25 ? null : player.position().add(safe.x(), safe.y(), safe.z());
    }

    /** Swept full player volume checks walls/ceilings, border, build height, and loaded chunks. */
    private static boolean clear(ServerPlayer player, AABB swept) {
        ServerLevel level = player.level();
        if (!level.getWorldBorder().isWithinBounds(swept)) return false;
        for (double x : new double[]{swept.minX, swept.maxX}) {
            for (double z : new double[]{swept.minZ, swept.maxZ}) {
                for (double y : new double[]{swept.minY, swept.maxY}) {
                    BlockPos corner = BlockPos.containing(x, y, z);
                    if (!level.isInWorldBounds(corner) || !level.hasChunkAt(corner)) return false;
                }
            }
        }
        return level.noCollision(player, swept);
    }
}
