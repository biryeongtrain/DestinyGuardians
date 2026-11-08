package kim.biryeong.destiny.strike.devils;

import eu.pb4.polymer.core.api.entity.PolymerEntityUtils;
import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.*;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import java.util.function.Supplier;

/** One world-owned actor runtime. Entity registration happens at mod init, worlds never register types. */
public final class DevilsActors implements AutoCloseable {
    public interface Environment {
        List<ServerPlayer> participants();
        /** Must validate collision, arena containment, >=12-block player distance, LoS and route. */
        Optional<Vec3> spawnPoint(DevilsPlan.Slot slot, DevilsMob probe);
        boolean contains(DevilsPlan.Zone zone, Vec3 feet);
        /** Already collision/ceiling/player validated, different from current anchor. Empty cancels warp. */
        Optional<Vec3> sepiksWarp(DevilsMob sepiks);
        /** Revalidate the same destination immediately before moving; failure cancels the move. */
        default boolean commitSepiksWarp(DevilsMob sepiks, Vec3 destination) { return false; }
        default void sound(DevilsMob mob, String event) { }
        default void sound(DevilsMob mob, String event, Vec3 at) { sound(mob,event); }
        /** Presentation-only observation of a fully accepted actor at its actual selected pad. */
        default void spawned(DevilsDirector.Spawn spawn, Vec3 at) { }
        default void problem(String message) { DestinyGuardians.LOGGER.warn("[DevilsActors] {}", message); }
    }
    static final Map<DevilsPlan.Kind, EntityType<DevilsMob>> TYPES = new EnumMap<>(DevilsPlan.Kind.class);
    static final Map<EntityType<?>, DevilsPlan.Kind> KINDS = new IdentityHashMap<>();
    static EntityType<DevilsMob> PART;
    private static boolean registered;
    public static synchronized void init() {
        if (registered) return;
        registered = true;
        for (var kind : DevilsPlan.Kind.values()) {
            var type = register("devils_" + kind.name().toLowerCase(Locale.ROOT), kind, width(kind), height(kind));
            TYPES.put(kind, type);
        }
        PART = register("devils_walker_part", DevilsPlan.Kind.WALKER, 1.4f, 1.4f);
    }
    private static EntityType<DevilsMob> register(String id, DevilsPlan.Kind kind, float width, float height) {
        var key = ResourceKey.create(Registries.ENTITY_TYPE, DestinyGuardians.id(id));
        float seat = (float) EntityTypes.ZOMBIE.getDimensions().attachments().get(EntityAttachment.PASSENGER, 0, 0).y;
        var type = Registry.register(BuiltInRegistries.ENTITY_TYPE, key,
                EntityType.Builder.<DevilsMob>of(DevilsMob::new, MobCategory.MONSTER).sized(width, height)
                        .eyeHeight(height * .8f).passengerAttachments(seat).clientTrackingRange(12).updateInterval(2).build(key));
        KINDS.put(type, kind);
        FabricDefaultAttributeRegistry.register(type, Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, kind.health()).add(Attributes.MAX_ABSORPTION, kind.shield())
                // Navigation limits walked path length as well as straight-line distance. Source-map
                // flanks need room for detours; DevilsMob retains its explicit 64-block target scan.
                .add(Attributes.MOVEMENT_SPEED, .25).add(Attributes.FOLLOW_RANGE, 128)
                .add(Attributes.FLYING_SPEED, .22)
                .add(Attributes.ARMOR, 0).add(Attributes.KNOCKBACK_RESISTANCE, kind.boss() ? 1 : .35)
                .add(Attributes.STEP_HEIGHT, 1));
        PolymerEntityUtils.registerType(type);
        return type;
    }
    public static float width(DevilsPlan.Kind kind) {
        return switch (kind) { case WALKER -> 4.2f; case BRIG -> 3.5f; case SEPIKS -> 6.5f;
            case SERVITOR, CYCLOPS -> 2.6f; case KNIGHT, MINOTAUR -> 1.25f; case WIZARD, HARPY -> 1.2f; case SHANK -> 1.1f; case PYKIS -> 1.4f; default -> .75f; };
    }
    public static float height(DevilsPlan.Kind kind) {
        return switch (kind) { case DREG -> 1.7f; case VANDAL, MARAUDER -> 2.3f; case CAPTAIN -> 2.7f;
            case SHANK -> .8f; case THRALL -> 1.9f; case ACOLYTE -> 2.05f; case KNIGHT -> 2.9f;
            case WIZARD, HARPY -> 2.4f; case SERVITOR, CYCLOPS -> 2.6f; case BRIG -> 5.5f; case WALKER -> 3.2f; case SEPIKS -> 6.5f;
            case GOBLIN -> 1.9f; case HOBGOBLIN -> 2.05f; case MINOTAUR -> 2.9f; case PYKIS -> 3.4f; };
    }
    static boolean flying(DevilsPlan.Kind kind) {
        return kind == DevilsPlan.Kind.SHANK || kind == DevilsPlan.Kind.WIZARD || kind == DevilsPlan.Kind.HARPY
                || kind == DevilsPlan.Kind.SERVITOR || kind == DevilsPlan.Kind.CYCLOPS || kind == DevilsPlan.Kind.SEPIKS;
    }
    static String model(DevilsPlan.Kind kind) {
        return switch (kind) { case DREG, VANDAL, CAPTAIN, SHANK, WALKER -> "rg_" + kind.name().toLowerCase(Locale.ROOT);
            // Exodus Crash stand-ins until the extracted Vex rigs are converted (same silhouette class, not the Vex look).
            case GOBLIN -> "dl_thrall"; case HOBGOBLIN -> "dl_acolyte"; case MINOTAUR -> "dl_knight";
            case HARPY -> "dl_wizard"; case CYCLOPS -> "dl_servitor"; case PYKIS -> "rg_captain";
            default -> "dl_" + kind.name().toLowerCase(Locale.ROOT); };
    }
    final ServerLevel level;
    final Environment environment;
    final Supplier<? extends ActorDirector> director;
    final Map<DevilsDirector.ActorRef, DevilsMob> active = new LinkedHashMap<>();
    private record WalkerKey(long generation, String slot) { }
    private final Map<WalkerKey, DevilsWalkerState> walkers = new HashMap<>();
    private record Reservation(UUID target, Vec3 at, int releaseAt, boolean heavy, boolean sniper, boolean melee) { }
    private final Map<DevilsMob, Reservation> attacks = new IdentityHashMap<>();
    private boolean closed, paused;
    int clock;
    public DevilsActors(ServerLevel level, Supplier<? extends ActorDirector> director, Environment environment) {
        this.level = Objects.requireNonNull(level); this.director = Objects.requireNonNull(director);
        this.environment = Objects.requireNonNull(environment);
    }
    public boolean spawn(DevilsDirector.Spawn spawn) {
        if (closed || active.containsKey(spawn.ref()) || !registered) return false;
        var kind = spawn.slot().kind();
        var mob = new DevilsMob(TYPES.get(kind), level);
        var at = environment.spawnPoint(spawn.slot(), mob);
        if (at.isEmpty()) return false; // Spatial host distinguishes deferred search from exhausted candidates.
        mob.bind(this, spawn, at.get(), kind == DevilsPlan.Kind.WALKER
                ? walkers.computeIfAbsent(new WalkerKey(spawn.ref().generation(), spawn.ref().slotId()), k -> new DevilsWalkerState()) : null);
        if (!level.noCollision(mob, mob.getBoundingBox()) || !level.addFreshEntity(mob)) {
            environment.problem("Entity insertion refused: " + spawn.slot().id()); return false;
        }
        // A missing model is a failed spawn, never an invisible combatant.
        if (!mob.attachModel()) {
            environment.problem("Required model unavailable: " + model(kind) + " for " + spawn.slot().id());
            mob.neutral = true; mob.discard(); return false;
        }
        active.put(spawn.ref(), mob);
        if (kind == DevilsPlan.Kind.WALKER && !mob.spawnParts()) {
            active.remove(spawn.ref()); mob.neutral = true; mob.discard(); return false;
        }
        // A visual failure cannot roll back an accepted spawn or make the director retry it.
        try { environment.spawned(spawn, mob.position()); }
        catch (RuntimeException error) {
            DestinyGuardians.LOGGER.warn("[DevilsActors] Spawn presentation failed for {}: {}", spawn.ref(), error.toString());
        }
        return true;
    }
    public void retire(DevilsDirector.ActorRef ref, DevilsDirector.Retirement reason) {
        var mob = active.remove(ref);
        if (mob != null) { mob.neutral = true; attacks.remove(mob); mob.discard(); }
        walkers.remove(new WalkerKey(ref.generation(), ref.slotId()));
    }
    /** Call once per server tick. Mob AI ticks itself; this clock only controls shared attack reservations. */
    public void tick(boolean paused) {
        this.paused = paused;
        if (closed || paused) return;
        clock++;
        attacks.entrySet().removeIf(e -> e.getKey().isRemoved() || e.getValue().releaseAt < clock - 16);
    }
    boolean paused() { return paused || closed; }
    boolean member(ServerPlayer p) { return p.level() == level && environment.participants().stream().anyMatch(v -> v == p); }
    List<ServerPlayer> targets() {
        return environment.participants().stream().filter(p -> p.level() == level && !p.hasDisconnected()
                && p.isAlive() && !p.isSpectator() && !p.isCreative()).toList();
    }
    static boolean hive(DevilsPlan.Kind kind) {
        return switch (kind) { case THRALL, ACOLYTE, KNIGHT, WIZARD, GOBLIN, HOBGOBLIN, HARPY, MINOTAUR, CYCLOPS -> true; default -> false; };
    }
    private boolean owns(DevilsMob mob) {
        return mob.runtime == this && !mob.walkerPart() && !mob.neutral && mob.isAlive()
                && mob.level() == level && active.get(mob.ref) == mob;
    }
    boolean validTarget(DevilsMob attacker, net.minecraft.world.entity.LivingEntity target) {
        if (!owns(attacker) || target == null || !target.isAlive() || target.level() != level) return false;
        if (target instanceof ServerPlayer p)
            return member(p) && !p.hasDisconnected() && !p.isSpectator() && !p.isCreative();
        return target instanceof DevilsMob mob && owns(mob) && attacker.slot.zone() == mob.slot.zone()
                && hive(attacker.kind) != hive(mob.kind);
    }
    List<net.minecraft.world.entity.LivingEntity> combatTargets(DevilsMob attacker) {
        var result = new ArrayList<net.minecraft.world.entity.LivingEntity>();
        for (var player : targets()) if (validTarget(attacker, player)) result.add(player);
        for (var mob : active.values()) if (validTarget(attacker, mob)) result.add(mob);
        return result;
    }
    void cancelAttack(DevilsMob mob) { attacks.remove(mob); }
    boolean reserve(DevilsMob mob, net.minecraft.world.entity.LivingEntity target, Vec3 at, int windup, boolean heavy, boolean sniper, boolean melee) {
        int impact = clock + windup;
        long sameMelee = 0, snipers = 0;
        for (var r : attacks.values()) {
            if (r.sniper) snipers++;
            if (r.target.equals(target.getUUID())) {
                if (sniper && r.sniper) return false;
                if (melee && r.melee) sameMelee++;
                if (mob.kind == DevilsPlan.Kind.MARAUDER && r.melee && Math.abs(impact - r.releaseAt) < 16) return false;
            }
            if (heavy && r.heavy && Math.abs(impact - r.releaseAt) < 16 && r.at.distanceToSqr(at) < 36) return false;
        }
        if (sniper && snipers >= 3 || melee && sameMelee >= 3) return false;
        attacks.put(mob, new Reservation(target.getUUID(), at, impact, heavy, sniper, melee));
        return true;
    }
    void removed(DevilsMob mob, boolean defeated) {
        if (!active.remove(mob.ref, mob)) return;
        attacks.remove(mob);
        if (closed || mob.neutral) return;
        if (defeated) director.get().defeated(mob.ref);
        else director.get().lost(mob.ref, Math.max(.001, mob.getHealth()), mob.getAbsorptionAmount());
    }
    public List<DevilsMob> actors() { return List.copyOf(active.values()); }
    @Override public void close() {
        if (closed) return; closed = true;
        for (var mob : List.copyOf(active.values())) { mob.neutral = true; mob.discard(); }
        active.clear(); attacks.clear(); walkers.clear();
    }
}
