package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.activity.strike.StrikeRoster;

import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Difficulty;
import net.minecraft.world.level.dimension.BuiltinDimensionTypes;
import net.minecraft.world.level.gamerules.GameRules;
import xyz.nucleoid.fantasy.Fantasy;
import xyz.nucleoid.fantasy.RuntimeLevelConfig;
import xyz.nucleoid.fantasy.RuntimeLevelHandle;

import java.util.ArrayDeque;
import java.util.Collection;
import java.util.Deque;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

/** One temporary world per fixed fireteam. Never a separate personal campaign for each member. */
public final class DevilsInstances {
    public enum State { PREPARING, READY, RUNNING, DRAINING, CLOSED }
    public static final class Instance {
        private final UUID id;
        private final Set<UUID> members;
        private final RuntimeLevelHandle handle;
        private final Deque<Runnable> cleanup = new ArrayDeque<>();
        private State state = State.PREPARING;
        private Instance(UUID id, Set<UUID> members, RuntimeLevelHandle handle) {
            this.id = id; this.members = members; this.handle = handle;
        }
        public UUID id() { return id; }
        public Set<UUID> members() { return members; }
        public ServerLevel level() { return handle.asLevel(); }
        public State state() { return state; }
    }
    private final MinecraftServer server;
    private final int capacity;
    private final Map<UUID, Instance> instances = new LinkedHashMap<>();
    private final Map<UUID, Instance> participants = new LinkedHashMap<>();

    public DevilsInstances(MinecraftServer server, int capacity) {
        this.server = Objects.requireNonNull(server);
        if (capacity < 1) throw new IllegalArgumentException("Positive instance capacity required");
        this.capacity = capacity;
    }
    public Optional<Instance> prepare(Collection<UUID> ids) {
        thread();
        new StrikeRoster(ids, DevilsPlan.MIN_PLAYERS, DevilsPlan.PLAYERS); // validate one to three distinct members before acquiring any resources
        var members = Set.copyOf(ids);
        if (instances.size() >= capacity || members.stream().anyMatch(participants::containsKey)
                || instances.values().stream().anyMatch(i -> i.state == State.PREPARING)) return Optional.empty();
        var config = new RuntimeLevelConfig()
                .setDimensionType(BuiltinDimensionTypes.OVERWORLD)
                .setGenerator(new DevilsTemplateGenerator(server, DevilsMaps.nbtTemplates()))
                .setDifficulty(Difficulty.NORMAL)
                .setMirrorOverworldGameRules(false).setMirrorOverworldClocks(false).setMirrorOverworldDifficulty(false)
                .setShouldTickTime(true)
                .setClockTime(net.minecraft.world.clock.WorldClocks.OVERWORLD,
                        new net.minecraft.world.clock.ClockState(2000L, 0f, 1f, true))
                .setGameRule(GameRules.ADVANCE_TIME, false).setGameRule(GameRules.ADVANCE_WEATHER, false)
                .setGameRule(GameRules.SPAWN_MOBS, false).setGameRule(GameRules.SPAWN_MONSTERS, false)
                .setGameRule(GameRules.SPAWN_PATROLS, false).setGameRule(GameRules.SPAWN_PHANTOMS, false)
                .setGameRule(GameRules.SPAWN_WANDERING_TRADERS, false)
                .setGameRule(GameRules.MOB_GRIEFING, false).setGameRule(GameRules.TNT_EXPLODES, false)
                .setGameRule(GameRules.PROJECTILES_CAN_BREAK_BLOCKS, false)
                .setGameRule(GameRules.FIRE_SPREAD_RADIUS_AROUND_PLAYER, 0)
                .setGameRule(GameRules.RANDOM_TICK_SPEED, 0).setGameRule(GameRules.PVP, false)
                .setGameRule(GameRules.BLOCK_DROPS, false).setGameRule(GameRules.MOB_DROPS, false)
                .setGameRule(GameRules.ENTITY_DROPS, false).setGameRule(GameRules.KEEP_INVENTORY, true);
        var id = UUID.randomUUID();
        var handle = Fantasy.get(server).openTemporaryLevel(DestinyGuardians.id("devils_lair/" + id), config);
        // Fantasy must tick the empty level while the first template chunks are generated.
        handle.setTickWhenEmpty(true);
        var instance = new Instance(id, members, handle);
        instances.put(id, instance);
        members.forEach(member -> participants.put(member, instance));
        return Optional.of(instance);
    }
    public Optional<Instance> of(UUID member) { thread(); return Optional.ofNullable(participants.get(member)); }
    public List<Instance> all() { thread(); return List.copyOf(instances.values()); }
    public void ready(Instance instance) {
        require(instance);
        if (instance.state != State.PREPARING) throw new IllegalStateException("Instance not preparing");
        instance.state = State.READY;
        instance.handle.setTickWhenEmpty(false);
    }
    public void running(Instance instance) {
        require(instance);
        if (instance.state != State.READY) throw new IllegalStateException("Instance not ready");
        instance.state = State.RUNNING;
    }
    public void own(Instance instance, Runnable cleanup) {
        require(instance);
        if (instance.state == State.DRAINING) throw new IllegalStateException("Instance draining");
        instance.cleanup.push(Objects.requireNonNull(cleanup));
    }
    /** Return all players before calling. A failed cleanup remains queued for retry. */
    public boolean close(Instance instance) {
        thread();
        if (instance.state == State.CLOSED) return true;
        require(instance);
        instance.state = State.DRAINING;
        if (!instance.level().players().isEmpty()) return false;
        while (!instance.cleanup.isEmpty()) { instance.cleanup.peek().run(); instance.cleanup.pop(); }
        instance.handle.delete();
        instance.state = State.CLOSED;
        instances.remove(instance.id, instance);
        instance.members.forEach(member -> participants.remove(member, instance));
        return true;
    }
    private void thread() { if (!server.isSameThread()) throw new IllegalStateException("Strike worlds require server thread"); }
    private void require(Instance instance) {
        thread();
        if (instance == null || instances.get(instance.id) != instance) throw new IllegalArgumentException("Foreign strike instance");
    }
}
