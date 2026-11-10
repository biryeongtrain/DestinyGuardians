package kim.biryeong.destiny.test;

import com.google.gson.GsonBuilder;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.campaign.RisingCampaign;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.tutorial.Tutorial;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.music.MusicPacks;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.lang.management.ManagementFactory;
import java.net.InetAddress;
import java.nio.file.*;
import java.util.*;

/** Explicit opt-in, bounded native TCP fixture. This is not a graphical-client/WAN/production-host certification. */
public final class ServerScaleGameTests {
    private static Run active;
    static {
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            var run = active;
            if (run != null && run.server == server && run.ids.contains(handler.player.getUUID())) {
                // Returning accounts: do not launch a new-player campaign as an incidental benchmark side effect.
                handler.player.setAttached(Tutorial.COMPLETED_REVISION, Integer.MAX_VALUE);
                handler.player.setAttached(RisingCampaign.COMPLETED_REVISION, Integer.MAX_VALUE);
            }
        });
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=16000)
    public void loopbackClientsIdleAndCombatTransport(GameTestHelper h) throws Exception {
        h.assertTrue(Boolean.getBoolean("destiny.gametest.scale.enabled"), Component.literal("Explicit -Ddestiny.gametest.scale.enabled=true required"));
        var server = h.getLevel().getServer();
        h.assertTrue(server.getClass().getName().contains("GameTestServer") && active == null,
                Component.literal("Only an owned GameTest server may host this fixture"));
        int count = Math.clamp(Integer.getInteger("destiny.gametest.scale.clients", 30), 1, 40);
        h.assertTrue(server.getPlayerList().getMaxPlayers() >= count,
                Component.literal("GameTest player limit must cover the requested cohort"));
        var run = new Run(h, server, count); active = run;
        TestCleanup.register(h, run::close);
        run.start();
    }

    private static final class Run implements AutoCloseable {
        final GameTestHelper h;
        final MinecraftServer server;
        final int count, port = Integer.getInteger("destiny.gametest.scale.port", 25640);
        final List<ScaleLoopbackClient> clients = new ArrayList<>();
        final Set<UUID> ids = new HashSet<>();
        final Map<UUID, ServerPlayer> prepared = new HashMap<>();
        final Map<UUID, ExpectedChunks> expectedChunks = new HashMap<>();
        final Map<UUID, Integer> previousRounds = new HashMap<>();
        private record ExpectedChunks(net.minecraft.server.level.ChunkTrackingView view, long[] keys) { }
        final List<Map<String, Object>> phases = new ArrayList<>();
        final boolean wasAuthenticating;
        final long started = System.nanoTime();
        final String peerPrefix = "Sq" + UUID.randomUUID().toString().substring(0, 6);
        final int originalView, originalSimulation;
        boolean worldPolicy;
        jdk.jfr.Recording recording;
        String phaseStartUtc;
        long firstSteadyTick, lastSteadyTick, fullWindowsReadyNanos;
        int paidRoundDrops;
        List<Long> ticks = new ArrayList<>();
        int age, phaseAge, phase = -1, cleanupAge;
        long phaseStart, receivedStart, sentStart, gcStart;
        Map<String, Long> packetStart = Map.of();
        boolean closing, closed;

        Run(GameTestHelper h, MinecraftServer server, int count) {
            this.h = h; this.server = server; this.count = count;
            wasAuthenticating = server.usesAuthentication();
            originalView = server.getPlayerList().getViewDistance();
            originalSimulation = server.getPlayerList().getSimulationDistance();
        }

        void start() throws Exception {
            h.assertTrue(server.getConnection().getConnections().isEmpty(), Component.literal("No pre-existing connections permitted"));
            server.setUsesAuthentication(false);
            server.getPlayerList().setViewDistance(Integer.getInteger("destiny.gametest.scale.serverViewDistance", 32));
            server.getPlayerList().setSimulationDistance(10);
            try {
                var policy = Class.forName("kim.biryeong.destiny.world.DestinyWorldDistances");
                policy.getMethod("manage", net.minecraft.server.level.ServerLevel.class).invoke(null, h.getLevel());
                worldPolicy = true;
            } catch (ClassNotFoundException baselineWithoutPolicy) {
                worldPolicy = false;
            }
            server.getConnection().startTcpServerListener(InetAddress.getLoopbackAddress(), port);
            String pack = MusicPacks.published().hash();
            h.assertTrue(!pack.isEmpty(), Component.literal("Profile graph and pack must be published before the benchmark"));
            for (int z = 0; z < 12; z++) for (int x = 0; x < 12; x++)
                h.getLevel().setBlockAndUpdate(h.absolutePos(new BlockPos(x, 1, z)), Blocks.SMOOTH_STONE.defaultBlockState());
            // Staggered native logins, bounded to four new connections per test tick.
            next();
        }

        void next() { h.runAfterDelay(1, this::tick); }

        void tick() {
            if (closed) return;
            age++;
            if (closing) {
                if (clients.stream().noneMatch(c -> server.getPlayerList().getPlayer(c.uuid) != null)) {
                    save(); close(); h.succeed(); return;
                }
                h.assertTrue(++cleanupAge < 100, Component.literal("Owned loopback players must disconnect cleanly"));
                next(); return;
            }
            if (clients.size() < count && age % 2 == 0) {
                int limit = Math.min(count, clients.size() + 4);
                while (clients.size() < limit) {
                    String name = String.format(Locale.ROOT, "%s%02d", peerPrefix, clients.size());
                    var id = UUID.nameUUIDFromBytes(("OfflinePlayer:" + name).getBytes(java.nio.charset.StandardCharsets.UTF_8));
                    ids.add(id);
                    clients.add(new ScaleLoopbackClient(name, port, server.registryAccess(), MusicPacks.published().hash()));
                }
            }
            for (var client : clients) {
                h.assertTrue(client.failure == null, Component.literal("Native peer failed: " + client.name + " / " + client.failure));
                client.tick(phase == 1, phaseAge);
                var p = server.getPlayerList().getPlayer(client.uuid);
                if (p != null && p.connection.hasClientLoaded() && !prepared.containsKey(client.uuid)) prepare(client, p, prepared.size());
                if (phase == 1 && p != null) {
                    int rounds = WeaponItems.magazine(p.getMainHandItem(), WeaponProfile.forEntry(WeaponCatalog.find("austringer").orElseThrow())).rounds();
                    var before = previousRounds.put(client.uuid, rounds);
                    if (before != null) paidRoundDrops += Math.max(0, before - rounds);
                }
            }
            if (phase < 0) {
                if (age % 200 == 0) diagnostics();
                h.assertTrue(age < 2000, Component.literal("Native login/load deadline exceeded; prepared=" + prepared.size()));
                if (prepared.size() == count && prepared.values().stream().allMatch(p -> p.connection.hasClientLoaded())
                        && age % 20 == 0 && chunksReceived()) { fullWindowsReadyNanos = System.nanoTime(); begin(0); }
                next(); return;
            }
            h.assertTrue(prepared.values().stream().allMatch(p -> !p.hasDisconnected() && p.connection.hasClientLoaded() && p.isAlive()),
                    Component.literal("All cohort peers must stay connected/loaded"));
            phaseAge++;
            if (phaseAge > 60) {
                long observed = System.nanoTime(); if (ticks.isEmpty()) firstSteadyTick = observed;
                lastSteadyTick = observed; ticks.add(wholeTick());
            }
            int duration = Math.clamp(Integer.getInteger("destiny.gametest.scale.phaseTicks", 260), 100, 6000);
            if (phaseAge >= duration) {
                if (phase == 1) h.assertTrue(paidRoundDrops >= count, Component.literal("Transport phase must actually consume weapon ammunition"));
                finishPhase();
                if (phase == 0) begin(1);
                else { closing = true; clients.forEach(ScaleLoopbackClient::close); }
            }
            next();
        }

        void prepare(ScaleLoopbackClient client, ServerPlayer p, int index) {
            RisingCampaign.leave(p);
            var token = Tutorial.participationToken(p); if (token != null) Tutorial.leave(p, token);
            var data = Guardians.data(p);
            data.setGuardianClass(GuardianClass.HUNTER);
            data.setLoadout(GuardianClass.HUNTER, HunterAbilities.preset(Element.SOLAR));
            var at = h.absoluteVec(new Vec3(2.5 + index % 8, 2, 2.5 + index / 8));
            p.teleportTo(h.getLevel(), at.x, at.y, at.z, Set.of(), 0, 0, true);
            p.setGameMode(GameType.ADVENTURE); p.setNoGravity(true); p.setOnGround(false); p.getAbilities().invulnerable = true; p.onUpdateAbilities();
            p.setItemInHand(InteractionHand.MAIN_HAND, WeaponItems.create(WeaponCatalog.find("austringer").orElseThrow()));
            p.initInventoryMenu(); prepared.put(client.uuid, p);
        }

        boolean chunksReceived() {
            for (var client : clients) {
                var p = prepared.get(client.uuid); var view = p.getChunkTrackingView();
                var expected = expectedChunks.get(client.uuid);
                if (expected == null || expected.view != view) {
                    var keys = new it.unimi.dsi.fastutil.longs.LongArrayList();
                    view.forEach(c -> keys.add(c.pack()));
                    expected = new ExpectedChunks(view, keys.toLongArray()); expectedChunks.put(client.uuid, expected);
                }
                if (expected.keys.length == 0) return false;
                boolean center = false;
                for (long key : expected.keys) {
                    if (key == p.chunkPosition().pack()) center = true;
                    if (!client.receivedChunks.contains(key)) return false;
                }
                if (!center) return false;
            }
            return true;
        }

        void diagnostics() {
            var loaded = prepared.values().stream().filter(p -> p.connection.hasClientLoaded()).count();
            System.out.println("ScaleQA load age=" + age + " prepared=" + prepared.size() + " loaded=" + loaded);
            clients.stream().limit(2).forEach(client -> {
                var p = prepared.get(client.uuid); if (p == null) return;
                var keys = new it.unimi.dsi.fastutil.longs.LongArrayList(); p.getChunkTrackingView().forEach(c -> keys.add(c.pack()));
                long missing = keys.longStream().filter(k -> !client.receivedChunks.contains(k)).count();
                System.out.println("ScaleQA peer=" + client.name + " level=" + p.level().dimension().identifier()
                        + " server=" + p.position() + " peer=" + client.position
                        + " expected=" + keys.size() + " received=" + client.receivedChunks.size() + " missing=" + missing);
            });
        }

        void begin(int value) {
            phase = value; phaseAge = 0; phaseStart = System.nanoTime(); ticks = new ArrayList<>();
            firstSteadyTick = lastSteadyTick = 0; paidRoundDrops = 0; previousRounds.clear();
            if (value == 1) prepared.forEach((id, p) -> previousRounds.put(id,
                    WeaponItems.magazine(p.getMainHandItem(), WeaponProfile.forEntry(WeaponCatalog.find("austringer").orElseThrow())).rounds()));
            phaseStartUtc = java.time.Instant.now().toString();
            if (value == 0 && Boolean.getBoolean("destiny.gametest.scale.jfr")) {
                try {
                    recording = new jdk.jfr.Recording(jdk.jfr.Configuration.getConfiguration("profile"));
                    for (String event : List.of("jdk.JVMInformation", "jdk.InitialSystemProperty",
                            "jdk.InitialEnvironmentVariable", "jdk.SystemProcess", "jdk.ProcessStart")) recording.disable(event);
                    recording.enable("minecraft.PacketSent").withoutStackTrace();
                    recording.enable("minecraft.PacketReceived").withoutStackTrace();
                    recording.enable("minecraft.ServerTickTime").withoutStackTrace();
                    recording.setMaxSize(256L * 1024 * 1024); recording.start();
                } catch (Exception e) { throw new AssertionError(e); }
            }
            receivedStart = bytes(true); sentStart = bytes(false); gcStart = gcTime(); packetStart = packets();
        }

        void finishPhase() {
            var out = new LinkedHashMap<String, Object>();
            out.put("phase", phase == 0 ? "idle" : "rotate_ads_fire"); out.put("clients", count);
            out.put("start_utc", phaseStartUtc);
            out.put("ticks", phaseAge); out.put("warmup_ticks_excluded_from_mspt", 60);
            out.put("wall_seconds", (System.nanoTime() - phaseStart) / 1e9);
            out.put("steady_observed_tps", (ticks.size() - 1) / ((lastSteadyTick - firstSteadyTick) / 1e9));
            out.put("paid_round_drops_observed", paidRoundDrops);
            out.put("whole_tick_nanos", ticks);
            out.put("client_received_framed_bytes", bytes(true) - receivedStart);
            out.put("client_sent_framed_bytes", bytes(false) - sentStart);
            var now = packets(); var delta = new TreeMap<String, Long>();
            now.forEach((key, value) -> delta.put(key, value - packetStart.getOrDefault(key, 0L)));
            out.put("client_decoded_packets", delta); out.put("gc_collection_ms", gcTime() - gcStart);
            out.put("heap_used_bytes", ManagementFactory.getMemoryMXBean().getHeapMemoryUsage().getUsed());
            out.put("loaded_chunks", java.util.stream.StreamSupport.stream(server.getAllLevels().spliterator(), false)
                    .mapToLong(l -> l.getChunkSource().getLoadedChunksCount()).sum());
            phases.add(out);
        }

        long bytes(boolean received) { return clients.stream().mapToLong(c -> received ? c.receivedBytes.sum() : c.sentBytes.sum()).sum(); }
        Map<String, Long> packets() {
            var result = new TreeMap<String, Long>(); clients.forEach(c -> c.packetCounts().forEach((key, value) -> result.merge(key, value, Long::sum))); return result;
        }
        long gcTime() { return ManagementFactory.getGarbageCollectorMXBeans().stream().mapToLong(b -> Math.max(0, b.getCollectionTime())).sum(); }
        long wholeTick() {
            try {
                var f = kim.biryeong.destiny.debug.HunterQa.class.getDeclaredField("completedTickNanos"); f.setAccessible(true); return f.getLong(null);
            } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
        }
        void save() {
            try {
                var out = new LinkedHashMap<String, Object>();
                out.put("schema", 1); out.put("clients", count); out.put("phases", phases);
                out.put("world_policy_present", worldPolicy);
                out.put("requested_client_view_distance", Integer.getInteger("destiny.gametest.scale.requestedViewDistance", 32));
                out.put("server_global_view_distance", server.getPlayerList().getViewDistance());
                out.put("full_tracking_windows_received_before_sampling", true);
                out.put("full_tracking_windows_ready_seconds", (fullWindowsReadyNanos - started) / 1e9);
                out.put("server_heap_max_bytes", ManagementFactory.getMemoryMXBean().getHeapMemoryUsage().getMax());
                out.put("wall_seconds", (System.nanoTime() - started) / 1e9);
                out.put("limitations", List.of("Loopback peers share the server JVM/CPU and registry snapshot", "Warm verified server pack cache, no graphics/authentication/WAN or simultaneous pack downloads", "Framed Minecraft TCP application bytes include compression but exclude TCP/IP headers", "Single shared combat fixture world; no claim of full activity-instance/30-human capacity"));
                var path = Path.of(System.getProperty("destiny.gametest.scale.output", "qa/scale-" + count + ".json"));
                Files.createDirectories(path.toAbsolutePath().getParent());
                if (recording != null) { recording.stop(); recording.dump(path.resolveSibling(path.getFileName() + ".jfr")); }
                Files.writeString(path, new GsonBuilder().setPrettyPrinting().create().toJson(out) + "\n");
            } catch (java.io.IOException e) { throw new AssertionError(e); }
        }

        @Override public void close() {
            if (closed) return; closed = true;
            clients.forEach(ScaleLoopbackClient::close);
            if (active == this) active = null;
            server.getConnection().stopTcpServerListener();
            server.setUsesAuthentication(wasAuthenticating);
            server.getPlayerList().setViewDistance(originalView);
            server.getPlayerList().setSimulationDistance(originalSimulation);
            if (recording != null) recording.close();
        }
    }
}
