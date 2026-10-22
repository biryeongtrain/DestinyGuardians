package kim.biryeong.destiny.debug;

import com.google.gson.GsonBuilder;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.fx.HunterVfx;
import kim.biryeong.destiny.fx.SuperVfx;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Opt-in, console/operator-only bounded cosmetic fixtures. Never enabled by default. */
public final class HunterQa {
    private static final boolean ENABLED = Boolean.getBoolean("destiny.qa");
    private static long completedTickNanos;
    private static final com.google.gson.Gson JSON = new GsonBuilder().setPrettyPrinting().create();
    private static List<ServerPlayer> owners = List.of();
    private static Map<ServerPlayer, Vec3> origins = Map.of();
    private static Map<ServerPlayer, net.minecraft.server.level.ServerLevel> levels = Map.of();
    private static int loadUntil, loadStarted;
    private static boolean stress;
    private static Sample sample;

    private static final class Sample {
        final String label;
        final int ticks;
        final long started = System.nanoTime();
        final List<Long> nanos = new ArrayList<>();
        final List<Long> wholeNanos = new ArrayList<>();
        long firstObservation;
        int maxModels, maxBeams;
        Sample(String label, int seconds) { this.label = label; ticks = seconds * 20; }
    }

    private HunterQa() { }

    public static boolean enabled() { return ENABLED; }
    public static void completedTick(long nanos) { completedTickNanos = nanos; }

    public static void init() {
        if (!ENABLED) return;
        CommandRegistrationCallback.EVENT.register((dispatcher, registry, environment) -> dispatcher.register(
                Commands.literal("destiny").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.literal("qa")
                                .then(Commands.literal("scene").then(Commands.argument("player", EntityArgument.player())
                                        .executes(c -> start(c.getSource().getServer(), List.of(EntityArgument.getPlayer(c, "player")), false))))
                                .then(Commands.literal("load").executes(c -> start(c.getSource().getServer(),
                                        c.getSource().getServer().getPlayerList().getPlayers().stream().limit(6).toList(), true))
                                        .then(Commands.argument("player", EntityArgument.player()).executes(c -> start(
                                                c.getSource().getServer(), List.of(EntityArgument.getPlayer(c, "player")), true))))
                                .then(Commands.literal("stop").executes(c -> { stop(); return 1; }))
                                .then(Commands.literal("status").executes(c -> {
                                    c.getSource().sendSuccess(() -> Component.literal(JSON.toJson(HunterVfx.snapshots())), false);
                                    return HunterVfx.activeCount();
                                }))
                                .then(Commands.literal("sample").then(Commands.argument("label", StringArgumentType.word())
                                        .then(Commands.argument("seconds", IntegerArgumentType.integer(5, 60)).executes(c -> {
                                            String label = StringArgumentType.getString(c, "label");
                                            if (!label.matches("[a-zA-Z0-9_-]{1,48}") || sample != null) return 0;
                                            sample = new Sample(label, IntegerArgumentType.getInteger(c, "seconds"));
                                            return 1;
                                        })))))));
        // Vanilla records tickCount % 100 before Fabric END. Read the completed previous invocation at START.
        ServerTickEvents.START_SERVER_TICK.register(HunterQa::sampleTick);
        ServerTickEvents.END_SERVER_TICK.register(HunterQa::loadTick);
        ServerLifecycleEvents.SERVER_STOPPING.register(s -> { stop(); sample = null; });
        DestinyGuardians.LOGGER.warn("H16 QA fixtures enabled explicitly (-Ddestiny.qa=true); not a production workload");
    }

    private static int start(MinecraftServer server, List<ServerPlayer> players, boolean saturate) {
        stop();
        owners = List.copyOf(players);
        var positions = new LinkedHashMap<ServerPlayer, Vec3>();
        owners.forEach(p -> positions.put(p, p.position().add(Vec3.directionFromRotation(0, p.getYRot()).scale(6))));
        origins = positions;
        var worlds = new LinkedHashMap<ServerPlayer, net.minecraft.server.level.ServerLevel>();
        owners.forEach(p -> worlds.put(p, p.level()));
        levels = worlds;
        stress = saturate;
        loadStarted = server.getTickCount();
        loadUntil = loadStarted + 2400; // hard 120 second limit at 20 TPS; stop never changes inventory/gameplay.
        return owners.size();
    }

    private static void loadTick(MinecraftServer server) {
        if (owners.isEmpty()) return;
        int tick = server.getTickCount();
        if (tick >= loadUntil) { stop(); return; }
        for (ServerPlayer p : owners) {
            if (p.hasDisconnected() || !p.isAlive() || p.isRemoved() || p.level() != levels.get(p)) continue;
            Vec3 origin = origins.get(p);
            int age = tick - loadStarted;
            if (age % 160 == 0) {
                for (int i = 0; i < (stress ? 4 : 1); i++) {
                    Vec3 pos = origin.add(0, 0, stress ? (i - 1.5) * 2.5 : 0);
                    HunterVfx.play(p, p.level(), pos, HunterVfx.Kind.VOID_ANCHOR, 1.3, 200);
                }
            }
            if (stress && age % 8 == 0) {
                for (int i = 0; i < 4; i++) {
                    Vec3 from = origin.add(0, 1 + i * 0.3, -4);
                    SuperVfx.trail(p, from, from.add(0, 0, 8), 10);
                }
            }
        }
    }

    private static void sampleTick(MinecraftServer server) {
        if (sample == null) return;
        Sample s = sample;
        long observedAt = System.nanoTime();
        if (s.nanos.isEmpty()) s.firstObservation = observedAt;
        long[] times = server.getTickTimesNanos();
        s.nanos.add(times[Math.floorMod(server.getTickCount() - 1, times.length)]);
        s.wholeNanos.add(completedTickNanos);
        s.maxModels = Math.max(s.maxModels, HunterVfx.activeCount());
        s.maxBeams = Math.max(s.maxBeams, SuperVfx.activeCount());
        if (s.nanos.size() < s.ticks) return;
        var out = new LinkedHashMap<String, Object>();
        out.put("label", s.label);
        out.put("tick_time_source", "MinecraftServer.getTickTimesNanos previous completed tick");
        out.put("tick_nanos", s.nanos);
        out.put("whole_tick_source", "WrapMethod around entire MinecraftServer.tickServer including Fabric END listeners; excludes outer wait and asynchronous work");
        out.put("whole_tick_nanos", s.wholeNanos);
        double interval = (observedAt - s.firstObservation) / 1e9;
        out.put("observed_tick_start_interval_seconds", interval);
        out.put("observed_tick_start_rate", (s.nanos.size() - 1) / interval);
        double seconds = (System.nanoTime() - s.started) / 1e9;
        out.put("wall_seconds", seconds);
        out.put("observed_ticks_per_wall_second", s.nanos.size() / seconds);
        out.put("connected_players", server.getPlayerList().getPlayers().stream().map(p -> p.getName().getString()).toList());
        out.put("max_bm_trackers", s.maxModels);
        out.put("max_beam_holders", s.maxBeams);
        try {
            Path dir = Path.of("qa");
            Files.createDirectories(dir);
            Files.writeString(dir.resolve("h16-" + s.label + ".json"), JSON.toJson(out) + "\n");
            DestinyGuardians.LOGGER.info("H16 sample {}: {} ticks / {} wall seconds, BM={} beams={}",
                    s.label, s.nanos.size(), seconds, s.maxModels, s.maxBeams);
        } catch (java.io.IOException e) {
            DestinyGuardians.LOGGER.warn("H16 QA sample save failed", e);
        }
        sample = null;
    }

    private static void stop() {
        owners.forEach(p -> { HunterVfx.cancelOwned(p); SuperVfx.cancelOwned(p); });
        owners = List.of();
        origins = Map.of();
        levels = Map.of();
    }
}
