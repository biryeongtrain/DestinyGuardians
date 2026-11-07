package kim.biryeong.destiny.campaign;

import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Difficulty;
import net.minecraft.world.level.dimension.BuiltinDimensionTypes;
import net.minecraft.world.level.gamerules.GameRules;
import xyz.nucleoid.fantasy.Fantasy;
import xyz.nucleoid.fantasy.RuntimeLevelConfig;
import xyz.nucleoid.fantasy.RuntimeLevelHandle;
import kim.biryeong.destiny.campaign.map.RisingZones;
import kim.biryeong.destiny.campaign.RisingServices.Zone;
import kim.biryeong.destiny.world.template.NbtTemplateChunkGenerator;
import xyz.nucleoid.map_templates.MapTemplate;
import java.util.concurrent.CompletableFuture;
import java.util.*;

/** Owned by one server. Admission happens only after the scene builder marks an instance ready. */
public final class GuardianRisesInstances {
    public enum State { PREPARING, READY, RUNNING, DRAINING, CLOSED }
    public static final class Instance {
        private final UUID id;
        private UUID owner;
        private final RuntimeLevelHandle handle;
        private State state = State.PREPARING;
        private final Deque<Runnable> cleanup = new ArrayDeque<>();
        private Instance(UUID id, UUID owner, RuntimeLevelHandle handle) {
            this.id = id; this.owner = owner; this.handle = handle;
        }
        public UUID id() { return id; }
        public UUID owner() { return owner; }
        public ServerLevel level() { return handle.asLevel(); }
        public State state() { return state; }
    }
    private final MinecraftServer server;
    private final int capacity;
    private final CompletableFuture<List<MapTemplate>> templates;
    static final long MORNING_TICKS = 2000L;
    private final Map<UUID, Instance> byOwner = new HashMap<>();
    public GuardianRisesInstances(MinecraftServer server, int capacity) {
        this.server = Objects.requireNonNull(server);
        if (capacity < 1) throw new IllegalArgumentException("Positive capacity required");
        this.capacity = capacity;
        this.templates = RisingZones.preloadAsync(server);
    }
    /** Fixed map coordinates shared by the NBT export, markers, and every personal instance. */
    public static BlockPos origin(Zone zone) {
        return new BlockPos(RisingCampaign.ZONE_SPACING / 2 + zone.ordinal() * RisingCampaign.ZONE_SPACING,
                RisingCampaign.ZONE_Y, RisingCampaign.ZONE_SPACING / 2);
    }
    private void thread() {
        if (!server.isSameThread()) throw new IllegalStateException("Campaign worlds require server thread");
    }
    public Optional<Instance> prepare(UUID owner) {
        thread(); Objects.requireNonNull(owner);
        if (byOwner.containsKey(owner)) return Optional.of(byOwner.get(owner));
        if (!templates.isDone()) return Optional.empty(); // never join an unfinished disk/NBT load on the server thread
        if (byOwner.size() >= capacity || byOwner.values().stream().anyMatch(i -> i.state == State.PREPARING))
            return Optional.empty();
        var config = new RuntimeLevelConfig()
                .setDimensionType(BuiltinDimensionTypes.OVERWORLD)
                .setGenerator(new NbtTemplateChunkGenerator(server, templates.join()))
                .setDifficulty(Difficulty.NORMAL)
                .setMirrorOverworldGameRules(false).setMirrorOverworldClocks(false).setMirrorOverworldDifficulty(false)
                .setShouldTickTime(true) // gameplay timers use level game time
                // The sky is authored lighting: pin a morning sun so long runs never fall into night.
                .setClockTime(net.minecraft.world.clock.WorldClocks.OVERWORLD,
                        new net.minecraft.world.clock.ClockState(MORNING_TICKS, 0f, 1f, true))
                .setGameRule(GameRules.ADVANCE_TIME, false)
                .setGameRule(GameRules.ADVANCE_WEATHER, false)
                .setGameRule(GameRules.SPAWN_MOBS, false).setGameRule(GameRules.SPAWN_MONSTERS, false)
                .setGameRule(GameRules.SPAWN_PATROLS, false).setGameRule(GameRules.SPAWN_PHANTOMS, false)
                .setGameRule(GameRules.SPAWN_WANDERING_TRADERS, false)
                .setGameRule(GameRules.MOB_GRIEFING, false).setGameRule(GameRules.TNT_EXPLODES, false)
                .setGameRule(GameRules.PROJECTILES_CAN_BREAK_BLOCKS, false)
                .setGameRule(GameRules.FIRE_SPREAD_RADIUS_AROUND_PLAYER, 0)
                .setGameRule(GameRules.RANDOM_TICK_SPEED, 0).setGameRule(GameRules.PVP, false)
                .setGameRule(GameRules.BLOCK_DROPS, false).setGameRule(GameRules.MOB_DROPS, false)
                .setGameRule(GameRules.ENTITY_DROPS, false).setGameRule(GameRules.KEEP_INVENTORY, true);
        UUID id = UUID.randomUUID();
        var handle = Fantasy.get(server).openTemporaryLevel(DestinyGuardians.id("guardian_rises/" + id), config);
        handle.setTickWhenEmpty(false); // Assign the generator only; no idle pre-generation or spare world.
        var instance = new Instance(id, owner, handle);
        byOwner.put(owner, instance);
        return Optional.of(instance);
    }
    /**
     * Hands a pre-built spare (still PREPARING, owned by {@code spareOwner}) to a Guardian who has no instance.
     * Returns false when either side does not qualify; the spare then stays as it was.
     */
    public boolean adopt(Instance spare, UUID spareOwner, UUID owner) {
        thread(); Objects.requireNonNull(owner);
        if (spare == null || byOwner.get(spareOwner) != spare || spare.state != State.PREPARING || byOwner.containsKey(owner)) return false;
        byOwner.remove(spareOwner);
        spare.owner = owner;
        byOwner.put(owner, spare);
        return true;
    }
    public void ready(Instance instance) {
        require(instance);
        if (instance.state != State.PREPARING) throw new IllegalStateException("Not preparing");
        instance.state = State.READY;
        instance.handle.setTickWhenEmpty(false);
    }
    /** Temporarily service the single asynchronous arrival request before a player has entered. */
    public void tickForArrival(Instance instance, boolean enabled) {
        require(instance);
        instance.handle.setTickWhenEmpty(enabled);
    }
    public void running(Instance instance) {
        require(instance);
        if (instance.state != State.READY) throw new IllegalStateException("Scene not ready");
        instance.state = State.RUNNING;
    }
    public void own(Instance instance, Runnable cleanup) {
        require(instance);
        if (instance.state == State.DRAINING) throw new IllegalStateException("Instance draining");
        instance.cleanup.push(Objects.requireNonNull(cleanup));
    }
    /** Caller first returns all players safely. Failed cleanup remains queued for a later retry. */
    public boolean close(Instance instance) {
        thread();
        if (instance.state == State.CLOSED) return true;
        require(instance);
        instance.state = State.DRAINING;
        if (!instance.level().players().isEmpty()) return false;
        while (!instance.cleanup.isEmpty()) {
            instance.cleanup.peek().run();
            instance.cleanup.pop();
        }
        instance.handle.delete();
        instance.state = State.CLOSED;
        byOwner.remove(instance.owner, instance);
        return true;
    }
    public List<Instance> instances() { thread(); return List.copyOf(byOwner.values()); }
    private void require(Instance instance) {
        thread();
        if (byOwner.get(instance.owner) != instance) throw new IllegalArgumentException("Foreign instance");
    }
}
