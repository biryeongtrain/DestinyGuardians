package kim.biryeong.destiny.campaign.fallen;

import eu.pb4.polymer.core.api.entity.PolymerEntityUtils;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.campaign.RisingServices;
import kim.biryeong.destiny.campaign.RisingServices.FallenKind;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLevelEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityAttachment;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.IdentityHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/**
 * W300 Fallen service: registers the Polymer entity types and implements {@link RisingServices.Fallen}.
 * Call {@link #init()} from the mod initializer (entity types must register before registries freeze).
 * Active AI is budgeted to {@link #MAX_ACTIVE_PER_LEVEL} per level (one Fantasy instance = one level); extra
 * activation requests wait in a queue and start when a slot frees.
 */
public final class RisingFallen implements RisingServices.Fallen {
    public static final int MAX_ACTIVE_PER_LEVEL = 24;

    public static EntityType<FallenMob> DREG, VANDAL, CAPTAIN, SHANK, WALKER, WALKER_PART;
    private static final Map<EntityType<?>, FallenKind> KINDS = new IdentityHashMap<>();
    private static final RisingFallen INSTANCE = new RisingFallen();
    private static boolean initialized;

    private static final class Budget {
        final Set<FallenMob> running = new LinkedHashSet<>();
        final Deque<FallenMob> waiting = new ArrayDeque<>();
    }
    private static final Map<ServerLevel, Budget> BUDGETS = new IdentityHashMap<>();

    private RisingFallen() {}

    public static RisingFallen instance() { return INSTANCE; }

    public static void init() {
        if (initialized) return;
        initialized = true;
        DREG = register("rising_dreg", FallenKind.DREG);
        VANDAL = register("rising_vandal", FallenKind.VANDAL);
        CAPTAIN = register("rising_captain", FallenKind.CAPTAIN);
        SHANK = register("rising_shank", FallenKind.SHANK);
        WALKER = register("rising_walker", FallenKind.WALKER);
        // Part boxes are per-instance (FallenMob#getDefaultDimensions); this is only the default.
        WALKER_PART = register("rising_walker_part", FallenKind.WALKER);
        PolymerEntityUtils.registerType(DREG, VANDAL, CAPTAIN, SHANK, WALKER, WALKER_PART);

        ServerTickEvents.END_SERVER_TICK.register(server -> {
            FallenWeapons.tick(server);
            SkiffDrop.tick(server);
            for (var entry : BUDGETS.entrySet()) if (entry.getKey().getServer() == server) promote(entry.getValue());
        });
        ServerLevelEvents.UNLOAD.register((server, level) -> { BUDGETS.remove(level); FallenWeapons.clear(level); SkiffDrop.clear(level); });
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> {
            BUDGETS.keySet().removeIf(level -> level.getServer() == server);
            FallenWeapons.clearAll();
            FallenSounds.clear();
            SkiffDrop.clearAll();
        });
        RisingServices.register(INSTANCE);
    }

    private static EntityType<FallenMob> register(String path, FallenKind kind) {
        var arch = FallenArchetypes.of(kind);
        float w = arch.width(), h = arch.height();
        int interval = 2; // smoother remote interpolation of the BetterModel base than the vanilla mob default 3
        var key = ResourceKey.create(Registries.ENTITY_TYPE, DestinyGuardians.id(path));
        // BetterModel mounts its displays on this entity and offsets them by -(server passenger attachment), while the
        // vanilla client seats them at the stand-in's attachment (FallenMob#getPolymerEntityType: zombie, y 2.0125).
        // Keep the two equal so every model origin sits on the entity's feet (W300 r9: Walker floated 1.01 blocks).
        float seat = (float) EntityTypes.ZOMBIE.getDimensions().attachments().get(EntityAttachment.PASSENGER, 0, 0).y;
        var builder = EntityType.Builder.<FallenMob>of(FallenMob::new, MobCategory.MONSTER)
                .sized(w, h).eyeHeight(h * .88f).passengerAttachments(seat)
                .clientTrackingRange(10).updateInterval(interval);
        if (kind == FallenKind.WALKER || kind == FallenKind.SHANK) builder = builder.fireImmune();
        var type = Registry.register(BuiltInRegistries.ENTITY_TYPE, key, builder.build(key));
        KINDS.put(type, kind);
        FabricDefaultAttributeRegistry.register(type, Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 20).add(Attributes.FOLLOW_RANGE, 48).add(Attributes.MOVEMENT_SPEED, .25)
                .add(Attributes.MAX_ABSORPTION, 0).add(Attributes.ARMOR, 0).add(Attributes.KNOCKBACK_RESISTANCE, 0)
                .add(Attributes.STEP_HEIGHT, .6));
        return type;
    }

    static FallenKind kindOf(EntityType<?> type) {
        var kind = KINDS.get(type);
        return kind == null ? FallenKind.DREG : kind;
    }

    static EntityType<FallenMob> typeOf(FallenKind kind) {
        return switch (kind) {
            case DREG -> DREG;
            case VANDAL -> VANDAL;
            case CAPTAIN -> CAPTAIN;
            case SHANK -> SHANK;
            case WALKER -> WALKER;
        };
    }

    // ------------------------------------------------------------------------------------------ service

    @Override
    public LivingEntity spawn(ServerLevel level, FallenKind kind, Vec3 pos, float yaw,
                              RisingServices.Difficulty tuning, RisingServices.FallenListener listener) {
        Objects.requireNonNull(level); Objects.requireNonNull(kind); Objects.requireNonNull(pos);
        if (!initialized || typeOf(kind) == null) throw new IllegalStateException("RisingFallen.init() was not called");
        var mob = typeOf(kind).create(level, EntitySpawnReason.EVENT);
        if (mob == null) throw new IllegalStateException("Could not create " + kind);
        Vec3 at = kind == FallenKind.SHANK ? pos.add(0, 2.5, 0) : pos;
        mob.snapTo(at.x, at.y, at.z, yaw, 0);
        mob.setYHeadRot(yaw);
        mob.setYBodyRot(yaw);
        mob.configure(FallenArchetypes.of(kind), tuning == null ? RisingServices.Difficulty.FIRST_MISSION : tuning, listener);
        if (!level.addFreshEntity(mob)) throw new IllegalStateException("Level rejected " + kind + " at " + pos);
        if (kind == FallenKind.WALKER) mob.walker().spawnParts();
        // Spawned active unless the AI budget is full; then it waits for a free slot.
        request(mob, true);
        return mob;
    }

    @Override
    public void setActive(LivingEntity entity, boolean active) {
        if (entity instanceof FallenMob mob && !mob.isWalkerPart()) request(mob, active);
    }

    private static void request(FallenMob mob, boolean active) {
        if (!(mob.level() instanceof ServerLevel level)) return;
        var budget = BUDGETS.computeIfAbsent(level, l -> new Budget());
        if (!active || !mob.isAlive() || mob.isRemoved()) {
            budget.running.remove(mob);
            budget.waiting.remove(mob);
            mob.setActiveState(false);
            promote(budget);
            return;
        }
        if (budget.running.contains(mob)) { mob.setActiveState(true); return; }
        if (budget.running.size() < MAX_ACTIVE_PER_LEVEL) {
            budget.running.add(mob);
            mob.setActiveState(true);
        } else {
            mob.setActiveState(false);
            if (!budget.waiting.contains(mob)) budget.waiting.addLast(mob);
        }
    }

    /** Death/removal frees the slot. */
    static void released(FallenMob mob) {
        if (!(mob.level() instanceof ServerLevel level)) return;
        var budget = BUDGETS.get(level);
        if (budget == null) return;
        budget.running.remove(mob);
        budget.waiting.remove(mob);
    }

    private static void promote(Budget budget) {
        budget.running.removeIf(m -> m.isRemoved() || !m.isAlive());
        while (budget.running.size() < MAX_ACTIVE_PER_LEVEL && !budget.waiting.isEmpty()) {
            var next = budget.waiting.pollFirst();
            if (next.isRemoved() || !next.isAlive()) continue;
            budget.running.add(next);
            next.setActiveState(true);
        }
    }

    public static int activeCount(ServerLevel level) {
        var b = BUDGETS.get(level);
        return b == null ? 0 : b.running.size();
    }
}
