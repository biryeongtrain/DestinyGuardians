package kim.biryeong.destiny.ability.warlock;

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
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Brightness;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.*;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.util.*;

/** W230: independent cast sessions and finite, epoch-owned Well fields. No inventory/flight mutations. */
public final class WarlockExpandedSupers {
    public static final Identifier WELL_OF_RADIANCE = DestinyGuardians.id("warlock/well_of_radiance");
    public static final Identifier CHAOS_REACH = DestinyGuardians.id("warlock/chaos_reach");
    public static final Identifier NOVA_WARP = DestinyGuardians.id("warlock/nova_warp");
    private static final Map<ServerPlayer, Session> ACTIVE = new IdentityHashMap<>();
    private static final Map<ServerPlayer, Well> WELLS = new IdentityHashMap<>();
    private WarlockExpandedSupers() {}

    public static void register() {
        AbilityRegistry.register(new Expanded(WELL_OF_RADIANCE, Element.SOLAR, 455, "빛의 샘"));
        AbilityRegistry.register(new Expanded(CHAOS_REACH, Element.ARC, 455, "혼돈 범위"));
        AbilityRegistry.register(new Expanded(NOVA_WARP, Element.VOID, 556, "신성 차원"));
    }

    private static final class Expanded extends Ability {
        Expanded(Identifier id, Element e, double cooldown, String name) {
            super(id, GuardianClass.WARLOCK, AbilitySlot.SUPER, e, cooldown, name);
        }
        @Override public boolean activate(ServerPlayer p) {
            if (AbilityService.inSuper(p) || ACTIVE.containsKey(p)) return false;
            Epoch epoch = new Epoch(p, id());
            if (!epoch.valid() || !ClassAbilityEffects.beginSuper(p, element(), id().getPath())) return false;
            Session session = new Session(epoch, this);
            ACTIVE.put(p, session);
            session.begin();
            AbilityService.startSuper(p, session);
            return true;
        }
    }

    /** Object identities prevent old callbacks surviving data/runtime/loadout/connection replacement. */
    private static final class Epoch {
        final ServerPlayer owner;
        final ServerLevel level;
        final GuardianData data;
        final GuardianRuntime runtime;
        final Loadout loadout;
        final Object connection;
        final Identifier id;
        boolean cancelled;
        Epoch(ServerPlayer p, Identifier id) {
            owner = p; level = p.level(); data = Guardians.data(p); runtime = Guardians.runtime(p);
            loadout = data.loadout().orElse(null); connection = p.connection; this.id = id;
        }
        boolean valid() {
            return !cancelled && owner.isAlive() && !owner.isRemoved() && !owner.isSpectator()
                    && !owner.hasDisconnected() && owner.connection == connection && owner.level() == level
                    && owner.getAttachedOrElse(Guardians.DATA, null) == data
                    && Guardians.runtimeIfPresent(owner).orElse(null) == runtime
                    && data.guardianClass() == GuardianClass.WARLOCK && loadout != null
                    && data.loadout().orElse(null) == loadout && Objects.equals(loadout.get(AbilitySlot.SUPER), id);
        }
    }

    public static void tick(MinecraftServer server) {
        for (Session s : List.copyOf(ACTIVE.values())) {
            if (s.epoch.level.getServer() == server && !s.epoch.valid()) cleanup(s.epoch.owner);
        }
        for (Well field : List.copyOf(WELLS.values())) {
            if (field.epoch.level.getServer() != server) continue;
            if (!field.tick()) { WELLS.remove(field.epoch.owner, field); field.destroy(); }
        }
    }

    public static void cleanup(ServerPlayer p) {
        Session session = ACTIVE.remove(p);
        if (session != null) {
            session.epoch.cancelled = true;
            if (session.epoch.runtime.superSession == session) session.epoch.runtime.superSession = null;
            session.end();
            PlayerAnimations.stop(p);
            SuperCamera.stop(p);
        }
        Well field = WELLS.remove(p);
        if (field != null) { field.epoch.cancelled = true; field.destroy(); }
    }

    public static void clearAll() {
        Set<ServerPlayer> owners = Collections.newSetFromMap(new IdentityHashMap<>());
        owners.addAll(ACTIVE.keySet()); owners.addAll(WELLS.keySet());
        for (ServerPlayer p : owners) cleanup(p);
    }

    /** Master applies this once, only for PRIMARY/SPECIAL/HEAVY in Combat.damage. No buff stacking. */
    public static double outgoingDamageMultiplier(ServerPlayer p) {
        double result = 1;
        for (Well field : WELLS.values()) if (field.contains(p)) result = Math.max(result, field.multiplier);
        return result;
    }

    /** Query the live field, so leaving, destruction and expiry revoke protection immediately. */
    public static boolean inWell(ServerPlayer p) {
        return WELLS.values().stream().anyMatch(field -> field.contains(p));
    }

    public static String status(ServerPlayer p) {
        Session s = ACTIVE.get(p); Well w = WELLS.get(p);
        return "active=" + (s == null ? "none" : s.path) + " age=" + (s == null ? 0 : s.age)
                + " windup=" + (s == null ? 0 : s.windup) + " pulses=" + (s == null ? 0 : s.pulses)
                + " bursts=" + (s == null ? 0 : s.bursts) + " blinks=" + (s == null ? 0 : s.blinks)
                + " charge=" + (s == null || s.chargeAt < 0 ? 0 : Math.max(0, s.chargeAt - s.age))
                + " nextAttack=" + (s == null ? -1 : s.nextAttack) + " chargeAt=" + (s == null ? -1 : s.chargeAt)
                + " spent=" + (s == null ? 0 : s.spent) + " lastTick=" + (s == null ? -1 : s.lastTick)
                + " well=" + (w != null && w.epoch.valid()) + " fieldAge=" + (w == null ? 0 : w.age)
                + " empower=" + outgoingDamageMultiplier(p);
    }

    private static final class Session implements SuperSession {
        final Epoch epoch;
        final Expanded ability;
        final String path;
        final int duration, windup, exit, chargeTicks;
        int age, spent, pulses, bursts, blinks, nextAttack, chargeAt = -1, landAt = -1;
        long lastTick = Long.MIN_VALUE;
        boolean alive = true, lastResult = true, planted, landing;
        final boolean airCast;
        Visual beam, aura;
        Session(Epoch epoch, Expanded ability) {
            this.epoch = epoch; this.ability = ability; path = ability.id().getPath();
            airCast = !supported(epoch.owner);
            duration = ticks(ability, "duration_ticks", well() ? 600 : chaos() ? 80 : 490, 20, 1200);
            // Shared durationTicks is pure ceil(20TPS); ONCE start blending costs one extra tick.
            windup = 1 + ClassSuperModelAssets.durationTicks(path, airCast && well() ? "start_air" : "start",
                    well() ? airCast ? 12 : 36 : chaos() ? 15 : 41);
            exit = chaos() ? 1 + ClassSuperModelAssets.durationTicks(path, "end", 8) : 0;
            chargeTicks = ticks(ability, "charge_ticks", 12, 1, 40);
        }
        boolean well() { return ability.id().equals(WELL_OF_RADIANCE); }
        boolean chaos() { return ability.id().equals(CHAOS_REACH); }
        @Override public boolean damageResistanceActive() {
            return alive && epoch.valid() && !well() && age + spent < duration;
        }
        void begin() {
            // beginSuper selects _start_air/_start once. Never restart the same source clip here.
            SuperCamera.blockMovement(epoch.owner, chaos() ? duration + exit : well() && airCast ? 160 : windup);
        }
        @Override public boolean tick() {
            if (!alive || !epoch.valid()) return false;
            long now = epoch.level.getGameTime();
            if (lastTick == now) return lastResult;
            lastTick = now;
            ClassAbilityEffects.superTick(epoch.owner, ability.element(), path, age);
            lastResult = well() ? tickWell() : chaos() ? tickChaos() : tickNova();
            age++;
            return lastResult;
        }
        private boolean tickWell() {
            if (planted) return false;
            if (!airCast && age >= windup) return plant();
            if (airCast && age >= windup) {
                if (!landing && supported(epoch.owner)) {
                    landing = true;
                    landAt = age + 1 + ClassSuperModelAssets.durationTicks(path, "land", 22);
                    play("land");
                }
                if (landing && age >= landAt) return plant();
            }
            // Native gravity/collision stays authoritative. Void/fall casts cannot create a floating field.
            return age < ticks(ability, "air_timeout_ticks", 160, 40, 200);
        }
        private boolean plant() {
            Vec3 floor = support(epoch.owner);
            if (floor == null) return false;
            Well old = WELLS.remove(epoch.owner);
            if (old != null) old.destroy();
            WELLS.put(epoch.owner, new Well(epoch, ability, floor.add(0, .025, 0)));
            planted = true;
            ClassAbilityEffects.burst(epoch.owner, floor, Element.SOLAR, 3);
            ClassAbilityEffects.sound(epoch.owner, Element.SOLAR, path, "super.fire");
            return false; // Session/camera ends; the field has a separate finite lease.
        }
        private boolean tickChaos() {
            if (age >= duration) {
                if (beam != null) { beam.destroy(); beam = null; }
                if (age == duration) play("end");
                return age < duration + exit;
            }
            if (age < windup) return true;
            if (age == windup) ClassAbilityEffects.sound(epoch.owner, Element.ARC, path, "super.fire");
            Vec3 from = epoch.owner.getEyePosition();
            Vec3 direction = epoch.owner.getLookAngle().normalize();
            double range = value(ability, "range", 24, 2, 40);
            Vec3 max = from.add(direction.scale(range));
            HitResult block = epoch.level.clip(new ClipContext(from, max, ClipContext.Block.COLLIDER,
                    ClipContext.Fluid.NONE, epoch.owner));
            Vec3 end = block.getLocation();
            LivingEntity nearest = null;
            double best = from.distanceToSqr(end);
            AABB search = new AABB(from, end).inflate(.5);
            for (LivingEntity target : epoch.level.getEntitiesOfClass(LivingEntity.class, search)) {
                if (!WarlockAbilities.enemy(epoch.owner, target)) continue;
                var hit = target.getBoundingBox().inflate(.12).clip(from, end);
                if (hit.isEmpty()) continue;
                double distance = from.distanceToSqr(hit.get());
                if (distance < best) { best = distance; nearest = target; end = hit.get(); }
            }
            if (beam == null) beam = new Visual(epoch, path, from, new Vector3f(1));
            beam.beam(from, end, (float) value(ability, "beam_width", 1.8, .2, 4));
            if ((age - windup) % ticks(ability, "pulse_ticks", 3, 1, 10) == 0) {
                pulses++;
                if (nearest != null && visible(epoch, from, end))
                    damage(nearest, (float) value(ability, "damage", 3, .1, 30));
                Fx.line(epoch.owner, epoch.level, from, end, Element.ARC.glow(), .25, .7f);
            }
            return true;
        }
        private boolean tickNova() {
            if (age + spent >= duration) return false;
            if (chargeAt >= 0) {
                if (aura == null) aura = new Visual(epoch, path, epoch.owner.position(), new Vector3f(.3f));
                float fraction = Math.clamp(1f - (float)(chargeAt - age) / chargeTicks, 0f, 1f);
                aura.point(epoch.owner.position().add(0, 1, 0), new Vector3f(.5f + fraction * 2.5f));
                if (age >= chargeAt) {
                    chargeAt = -1; bursts++;
                    if (aura != null) { aura.destroy(); aura = null; }
                    double radius = value(ability, "radius", 4.4, 1, 8);
                    Vec3 origin = epoch.owner.position().add(0, .8, 0);
                    for (LivingEntity target : Combat.enemiesNear(epoch.level, epoch.owner, origin, radius))
                        if (WarlockAbilities.enemy(epoch.owner, target) && visible(epoch, origin, WarlockAbilities.center(target)))
                            damage(target, (float) value(ability, "damage", 16, .1, 100));
                    ClassAbilityEffects.burst(epoch.owner, origin, Element.VOID, radius);
                    ClassAbilityEffects.sound(epoch.owner, Element.VOID, path, "super.impact");
                }
            }
            return true;
        }
        @Override public void primary() {
            if (!alive || !epoch.valid() || well() || chaos() || age < windup || age < nextAttack
                    || chargeAt >= 0 || age + spent >= duration) return;
            // Native shift may be temporarily cleared by the movement gate; last client input remains authoritative.
            if (epoch.owner.getLastClientInput().shift() || epoch.owner.isShiftKeyDown()) {
                nextAttack = age + ticks(ability, "blink_interval_ticks", 10, 4, 30);
                if (blink()) { blinks++; spent += Math.max(1, (int)Math.ceil(duration * .035)); }
                return;
            }
            chargeAt = age + chargeTicks;
            nextAttack = chargeAt + ticks(ability, "burst_recovery_ticks", 6, 1, 30);
            spent += Math.max(1, (int)Math.ceil(duration * .05));
            ClassAbilityEffects.attack(epoch.owner, Element.VOID, path);
            ClassAbilityEffects.sound(epoch.owner, Element.VOID, path, "super.fire");
        }
        private boolean blink() {
            ServerPlayer p = epoch.owner;
            Vec3 start = p.position(), direction = p.getLookAngle().normalize();
            double range = value(ability, "blink_range", 4, .5, 6);
            Vec3 safe = start;
            // Swept boxes join every previous step; thin collision shapes cannot be skipped.
            for (double distance = .25; distance <= range + .0001; distance += .25) {
                Vec3 next = start.add(direction.scale(distance));
                AABB destination = p.getBoundingBox().move(next.subtract(start));
                AABB swept = p.getBoundingBox().move(safe.subtract(start)).minmax(destination);
                if (!epoch.level.isInWorldBounds(BlockPos.containing(next))
                        || !loaded(epoch.level, swept)
                        || !epoch.level.getWorldBorder().isWithinBounds(destination)
                        || !epoch.level.noCollision(p, swept)) break;
                safe = next;
            }
            if (safe.distanceToSqr(start) < .25) return false;
            Fx.line(epoch.owner, epoch.level, start.add(0, .9, 0), safe.add(0, .9, 0), Element.VOID.glow(), .2, .6f);
            Vec3 velocity = p.getDeltaMovement();
            p.teleportTo(safe.x, safe.y, safe.z);
            p.setDeltaMovement(velocity);
            ClassAbilityEffects.burst(p, safe.add(0, .8, 0), Element.VOID, .7);
            return true;
        }
        void damage(LivingEntity target, float damage) {
            if (alive && epoch.valid() && WarlockAbilities.enemy(epoch.owner, target))
                Combat.damage(epoch.level, epoch.owner, target, damage, ability.element(), AmmoGeneration.SUPER);
        }
        void play(String phase) {
            String clip = ClassSuperModelAssets.prefix(path) + "_" + phase;
            if (ClassSuperModelAssets.hasClip(clip)) PlayerAnimations.play(epoch.owner, clip);
        }
        @Override public void end() {
            if (!alive) return;
            alive = false; ACTIVE.remove(epoch.owner, this);
            chargeAt = -1;
            if (beam != null) beam.destroy();
            if (aura != null) aura.destroy();
            SuperCamera.blockMovement(epoch.owner, 0);
            ClassAbilityEffects.endSuper(epoch.owner, ability.element(), path);
            // Chaos exit has already played; Well immediately returns to normal weapon use.
            PlayerAnimations.stop(epoch.owner);
            SuperCamera.stop(epoch.owner);
        }
        @Override public float remaining() {
            int limit = well() ? airCast ? 160 : windup + 1 : duration;
            return alive ? Math.clamp(1f - (float)(age + spent) / limit, 0f, 1f) : 0;
        }
    }

    private static final class Well {
        final Epoch epoch; final Vec3 origin;
        final int duration, interval; final double radius, height, multiplier;
        final float healing; final Visual ring, sword;
        long lastTick = Long.MIN_VALUE; int age; boolean destroyed;
        Well(Epoch epoch, Expanded ability, Vec3 origin) {
            this.epoch = epoch; this.origin = origin;
            duration = ticks(ability, "duration_ticks", 600, 20, 1200);
            interval = ticks(ability, "heal_interval_ticks", 5, 1, 40);
            radius = value(ability, "radius", 5, 1, 10); height = value(ability, "height", 2.5, 1, 5);
            healing = (float)value(ability, "heal", 2, .1, 10);
            multiplier = value(ability, "weapon_multiplier", 1.25, 1, 2);
            ring = new Visual(epoch, "warlock/well_of_radiance", origin, new Vector3f((float)(radius * 2), 1, (float)(radius * 2)));
            sword = new Visual(epoch, "warlock/well_of_radiance_sword", origin, new Vector3f(1));
        }
        boolean contains(Player player) {
            if (destroyed || !epoch.valid() || age >= duration || player.level() != epoch.level
                    || !player.isAlive() || player.isRemoved() || player.isSpectator()
                    || player instanceof ServerPlayer server && server.hasDisconnected()) return false;
            if (player != epoch.owner && !epoch.owner.isAlliedTo(player)) return false;
            double dx = player.getX() - origin.x, dz = player.getZ() - origin.z;
            return dx * dx + dz * dz <= radius * radius && player.getY() >= origin.y - .3
                    && player.getY() <= origin.y + height
                    && visible(epoch, origin.add(0, .35, 0), player.position().add(0, .5, 0));
        }
        boolean tick() {
            if (destroyed || !epoch.valid() || age >= duration) return false;
            long now = epoch.level.getGameTime();
            if (lastTick == now) return true;
            lastTick = now;
            ring.tick(); sword.tick();
            if (age % 5 == 0) Fx.ring(epoch.owner, epoch.level, origin, radius, Element.SOLAR.glow(), 40);
            if (age % interval == 0) {
                for (Player ally : epoch.level.getEntitiesOfClass(Player.class,
                        new AABB(origin, origin).inflate(radius, height, radius)))
                    if (ally != epoch.owner && contains(ally)) ally.heal(healing);
                if (contains(epoch.owner)) epoch.owner.heal(healing);
            }
            age++;
            return true;
        }
        void destroy() {
            if (destroyed) return;
            destroyed = true; ring.destroy(); sword.destroy();
        }
    }

    /** Asset absence degrades only the visual, never gameplay ownership. */
    private static final class Visual {
        final Vec3 anchor; ElementHolder holder; ItemDisplayElement display; boolean destroyed;
        Visual(Epoch epoch, String path, Vec3 anchor, Vector3f scale) {
            this.anchor = anchor;
            try {
                var item = ClassAbilityEffects.item(path);
                if (!item.has(DataComponents.ITEM_MODEL)) return;
                holder = new ElementHolder(); display = new AbilityDisplayElement(epoch.owner, item);
                display.setItemDisplayContext(ItemDisplayContext.NONE);
                display.setBrightness(new Brightness(15, 15));
                display.setTeleportDuration(1);
                display.setLeftRotation(new Quaternionf().rotationY((float)Math.PI));
                display.setScale(scale); holder.addElement(display);
                ChunkAttachment.ofTicking(holder, epoch.level, anchor);
            } catch (RuntimeException failure) {
                if (holder != null) holder.destroy(); holder = null; display = null;
                DestinyGuardians.LOGGER.warn("W230 optional visual unavailable: {}", path, failure);
            }
        }
        void point(Vec3 at, Vector3f scale) {
            if (display == null || destroyed) return;
            display.setOffset(at.subtract(anchor)); display.setScale(scale); tick();
        }
        void beam(Vec3 start, Vec3 end, float width) {
            if (display == null || destroyed) return;
            Vec3 d = end.subtract(start); double length = d.length();
            if (length < .001) { display.setScale(new Vector3f(0)); return; }
            Vec3 unit = d.scale(1 / length);
            display.setOffset(start.subtract(anchor));
            // 26.3 DisplayRenderer.ItemDisplayRenderer.submitInner rotates Y by PI immediately before
            // item.submit. Our model has canonical +Z and NONE has no art rotation. Thus Qaim*Ypi
            // cancels the renderer Ypi, yielding +Z -> current ray (diagonal scale commutes with Ypi).
            display.setLeftRotation(new Quaternionf().rotationTo(0, 0, 1, (float)unit.x, (float)unit.y, (float)unit.z)
                    .rotateY((float)Math.PI));
            display.setScale(new Vector3f(width, width, (float)length)); tick();
        }
        void tick() { if (!destroyed && holder != null) holder.tick(); }
        void destroy() { if (destroyed) return; destroyed = true; if (holder != null) holder.destroy(); }
    }

    private static Vec3 support(ServerPlayer p) {
        var hit = p.level().clip(new ClipContext(p.position().add(0, .12, 0), p.position().add(0, -.3, 0),
                ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
        return hit instanceof BlockHitResult block && hit.getType() == HitResult.Type.BLOCK && block.getDirection() == Direction.UP
                ? new Vec3(p.getX(), hit.getLocation().y, p.getZ()) : null;
    }
    private static boolean supported(ServerPlayer p) { return support(p) != null; }
    private static boolean loaded(ServerLevel level, AABB box) {
        return level.hasChunkAt(BlockPos.containing(box.minX, box.minY, box.minZ))
                && level.hasChunkAt(BlockPos.containing(box.maxX, box.minY, box.minZ))
                && level.hasChunkAt(BlockPos.containing(box.minX, box.minY, box.maxZ))
                && level.hasChunkAt(BlockPos.containing(box.maxX, box.minY, box.maxZ));
    }
    private static boolean visible(Epoch epoch, Vec3 from, Vec3 to) {
        return epoch.valid() && epoch.level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, epoch.owner)).getType() == HitResult.Type.MISS;
    }
    private static double value(Ability ability, String key, double fallback, double min, double max) {
        return WarlockAbilities.value(ability, key, fallback, min, max);
    }
    private static int ticks(Ability ability, String key, int fallback, int min, int max) {
        return WarlockAbilities.ticks(ability, key, fallback, min, max);
    }
}
