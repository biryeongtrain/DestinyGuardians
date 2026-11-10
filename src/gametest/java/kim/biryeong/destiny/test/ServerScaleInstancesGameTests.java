package kim.biryeong.destiny.test;

import com.google.gson.GsonBuilder;
import eu.pb4.polymer.resourcepack.api.PolymerResourcePackUtils;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.activity.strike.StrikeCoordinator;
import kim.biryeong.destiny.activity.strike.StrikeRoster;
import kim.biryeong.destiny.activity.strike.Strikes;
import kim.biryeong.destiny.campaign.RisingCampaign;
import kim.biryeong.destiny.compat.pack.ActivityPackArchive;
import kim.biryeong.destiny.compat.pack.ActivityPackCatalog;
import kim.biryeong.destiny.compat.pack.ActivityPacks;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.strike.devils.DevilsLair;
import kim.biryeong.destiny.strike.exodus.ExodusCrash;
import kim.biryeong.destiny.tutorial.Tutorial;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import kim.biryeong.destiny.world.template.ArrivalChunks;
import kim.biryeong.minigamelib.music.MusicPacks;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ChunkTrackingView;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.TicketStorage;

import java.lang.management.ManagementFactory;
import java.lang.ref.WeakReference;
import java.net.InetAddress;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.CompletableFuture;

/** Opt-in native transport plus actual production activity ownership/admission/exit; no alternate world manager. */
public final class ServerScaleInstancesGameTests {
    private static Run active;
    static {
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            var run = active;
            if (run != null && run.server == server && run.ids.contains(handler.player.getUUID())) {
                handler.player.setAttached(Tutorial.COMPLETED_REVISION, Integer.MAX_VALUE);
                handler.player.setAttached(RisingCampaign.COMPLETED_REVISION, Integer.MAX_VALUE);
            }
        });
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            var run = active;
            if (run != null && run.server == server && run.ids.contains(handler.player.getUUID()))
                run.disconnectEvents.add(new DisconnectEvent(handler.player.getUUID(), System.identityHashCode(handler),
                        server.isSameThread(), Thread.currentThread().getName(), server.getTickCount()));
        });
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=36000)
    public void fortyNativePeersAcrossProductionInstancesAndCleanExit(GameTestHelper h) throws Exception {
        check(h, Boolean.getBoolean("destiny.gametest.scale.enabled")
                && Boolean.getBoolean("destiny.gametest.scale.instances.enabled"), "Explicit scale and instance fixture flags required");
        var server = h.getLevel().getServer();
        check(h, server.getClass().getName().contains("GameTestServer") && active == null, "Owned GameTest server only");
        check(h, server.getPlayerList().getPlayers().isEmpty() && server.getConnection().getConnections().isEmpty(), "No pre-existing players/connections");
        check(h, java.util.stream.StreamSupport.stream(server.getAllLevels().spliterator(), false)
                .noneMatch(l -> Strikes.isLevel(l) || RisingCampaign.isCampaignLevel(l)), "No pre-existing production activity worlds");
        check(h, server.getPlayerList().getMaxPlayers() >= 40, "GameTestScalePacingMixin must permit forty peers");
        check(h, Boolean.parseBoolean(System.getProperty("destiny.guardianRises", "true")), "Instance scenario requires production campaign enabled; legacy GameTest default disables it");
        check(h, TowerSpawnWorld.enabled(), "Actual tower must be enabled for the ten-player tower cohort");
        check(h, kim.biryeong.destiny.debug.HunterQa.enabled(), "Whole-tick measurement requires -Ddestiny.qa=true");
        var run = new Run(h, server); active = run;
        TestCleanup.register(h, run::close);
        run.start();
    }

    private static void check(GameTestHelper h, boolean valid, String message) {
        h.assertTrue(valid, Component.literal(message));
    }

    private enum Phase { VERIFY_PACKS, ADMITTING, STEADY, RECONNECT, EXITING, POST_CLEANUP, DISCONNECTING, DONE }
    private record Owned(StrikeCoordinator strike, Object token) { }
    private record WorldProbe(ResourceKey<Level> key, WeakReference<TicketStorage> tickets) { }
    private record Packs(String base, Set<String> accepted, Map<String, Object> evidence) { }
    private record DisconnectEvent(UUID player, int connection, boolean serverThread, String thread, int tick) { }

    private static final class Run implements AutoCloseable {
        final GameTestHelper h;
        final MinecraftServer server;
        final int port = Integer.getInteger("destiny.gametest.scale.instances.port", 25641);
        final boolean wasAuthenticating;
        final int originalView, originalSimulation;
        final long started = System.nanoTime();
        final String prefix = "Si" + UUID.randomUUID().toString().substring(0, 6);
        final List<ScaleLoopbackClient> clients = new ArrayList<>();
        final Set<UUID> ids = new HashSet<>();
        final Map<UUID, ServerPlayer> prepared = new LinkedHashMap<>();
        final Map<UUID, Owned> owned = new LinkedHashMap<>();
        final Set<UUID> skippedCampaign = new HashSet<>();
        final Map<UUID, Boolean> campaignJumps = new HashMap<>();
        final Map<UUID, Integer> observedArrivalColumns = new HashMap<>();
        final Map<ResourceKey<Level>, WorldProbe> worlds = new LinkedHashMap<>();
        final Map<String, Object> report = new LinkedHashMap<>();
        final Map<UUID, Integer> previousRounds = new HashMap<>();
        final Map<UUID, Integer> paidDrops = new HashMap<>();
        final List<Long> wholeTicks = new ArrayList<>();
        final boolean lifecycle = Boolean.getBoolean("destiny.gametest.scale.instances.lifecycle");
        final Set<UUID> intentionallyOffline = new HashSet<>();
        final Map<UUID, ResourceKey<Level>> rejoinWorlds = new HashMap<>();
        final Map<UUID, Integer> oldEntityIds = new HashMap<>();
        final Set<ResourceKey<Level>> expiryWorlds = new HashSet<>();
        final List<Long> lifecycleTicks = new ArrayList<>();
        final List<Map<String, Object>> cycles = new ArrayList<>();
        final java.util.concurrent.ConcurrentLinkedQueue<DisconnectEvent> disconnectEvents = new java.util.concurrent.ConcurrentLinkedQueue<>();
        final Map<Integer, UUID> expectedDisconnects = new LinkedHashMap<>();
        CompletableFuture<Packs> verifiedPacks;
        Packs packs;
        Phase phase = Phase.VERIFY_PACKS;
        int age, phaseAge, nextDevils, nextExodus;
        int admittedActivityPlayers, observedWorldCount;
        long steadyStarted, firstSteady, lastSteady, receivedStart, sentStart, gcStart;
        Map<String, Long> packetsStart = Map.of();
        boolean listenerStarted, closed, passed;
        int cycle, offlineObservedAt = -1, minimumConnected = 40, exodusDropAt = -1;
        long reconnectStarted;
        boolean replacementsStarted, devilsRejoined, exodusReplacementsStarted, rejoined;

        Run(GameTestHelper h, MinecraftServer server) {
            this.h = h; this.server = server;
            wasAuthenticating = server.usesAuthentication();
            originalView = server.getPlayerList().getViewDistance();
            originalSimulation = server.getPlayerList().getSimulationDistance();
        }

        void start() {
            GameTestScaleSaveTrace.start(server);
            server.setUsesAuthentication(false);
            server.getPlayerList().setViewDistance(Math.clamp(Integer.getInteger("destiny.gametest.scale.instances.globalView", 32), 2, 32));
            server.getPlayerList().setSimulationDistance(Math.clamp(Integer.getInteger("destiny.gametest.scale.instances.globalSimulation", 10), 2, 32));
            TowerSpawnWorld.open(server);
            String base = MusicPacks.published().hash();
            check(h, !base.isEmpty(), "Published base pack required before instance test");
            // SHA/file validation stays outside the server thread and completes before any peer can ACK a pack.
            verifiedPacks = CompletableFuture.supplyAsync(() -> {
                try {
                    ActivityPacks.validateCached(PolymerResourcePackUtils.getMainPath(), base);
                    var archives = ActivityPackArchive.read(ActivityPacks.directory(), base, ActivityPackCatalog.load());
                    var accepted = new HashSet<String>(); accepted.add(base);
                    var evidence = new TreeMap<String, Object>();
                    for (String id : List.of("devils_lair", "exodus_crash")) {
                        var archive = Objects.requireNonNull(archives.get(id)); accepted.add(archive.sha1());
                        evidence.put(id, Map.of("sha1", archive.sha1(), "bytes", archive.size()));
                    }
                    return new Packs(base, Set.copyOf(accepted), Map.copyOf(evidence));
                } catch (java.io.IOException failure) { throw new java.util.concurrent.CompletionException(failure); }
            });
            report.put("schema", 1); report.put("clients", 40);
            report.put("cohort", "4 Devils parties x3 +2 Exodus parties x3 +12 personal campaign +10 tower");
            report.put("start_utc", java.time.Instant.now().toString());
            report.put("global_view_distance", server.getPlayerList().getViewDistance());
            report.put("global_simulation_distance", server.getPlayerList().getSimulationDistance());
            report.put("reconnect_grace_exercised", false);
            report.put("production_strike_reconnect_grace_ticks", StrikeRoster.RECONNECT_TICKS);
            report.put("reconnect_grace_elapsed_ticks", 0);
            report.put("cleanup_policy", lifecycle ? "Two real admission/exit cycles; first includes native reconnect and unmodified120s all-offline expiry"
                    : "Explicit normal leave before disconnect; cleanup deadline exceeds production reconnect grace without changing it");
            report.put("requested_cycles", lifecycle ? 2 : 1);
            report.put("campaign_qa_stage", "breach_fight via registered administrator command, with real stage/encounter placement");
            report.put("arrival_metric", "Maximum observed pending ArrivalChunks.requestedColumns per campaign; zero means no request persisted to an observation boundary, not zero terrain/view generation");
            report.put("limitations", List.of("Loopback peers share server JVM/CPU and registry snapshot", "Verified warm base/activity ZIP cache; no pack download/render/authentication/WAN acceptance", "Invulnerable automated players send movement/ADS/fire; no graphical or human-combat certification", "Production capacities, reconnect grace and world generation/admission remain unchanged"));
            next();
        }

        void next() { h.runAfterDelay(1, this::tick); }

        void tick() {
            if (closed) return;
            age++; phaseAge++;
            try {
                if (phase == Phase.VERIFY_PACKS) {
                    check(h, phaseAge < 2400, "Verified pack cache deadline exceeded");
                    if (!verifiedPacks.isDone()) { next(); return; }
                    packs = verifiedPacks.join();
                    check(h, packs.base.equals(MusicPacks.published().hash()), "Base pack changed during verification");
                    try { server.getConnection().startTcpServerListener(InetAddress.getLoopbackAddress(), port); }
                    catch (java.io.IOException failure) { throw new AssertionError(failure); }
                    listenerStarted = true;
                    report.put("verified_pack_cache", packs.evidence);
                    report.put("base_pack_sha1", packs.base);
                    phase = Phase.ADMITTING; phaseAge = 0;
                    save();
                }
                if (phase == Phase.ADMITTING && clients.size() < 40 && age % 2 == 0) {
                    int limit = Math.min(40, clients.size() + 4);
                    while (clients.size() < limit) {
                        var name = String.format(Locale.ROOT, "%s%02d", prefix, clients.size());
                        ids.add(UUID.nameUUIDFromBytes(("OfflinePlayer:" + name).getBytes(StandardCharsets.UTF_8)));
                        // Requires the helper's verified Set<String> overload, preserving its fail-closed hash check.
                        clients.add(new ScaleLoopbackClient(name, port, server.registryAccess(), packs.accepted));
                    }
                }
                for (var client : clients) {
                    if (phase != Phase.DISCONNECTING && !intentionallyOffline.contains(client.uuid))
                        check(h, client.failure == null, "Peer failed: " + client.name + " / " + client.failure);
                    client.tick(phase == Phase.STEADY || phase == Phase.RECONNECT, phaseAge);
                    var player = server.getPlayerList().getPlayer(client.uuid);
                    if (phase == Phase.ADMITTING && player != null && player.connection.hasClientLoaded()
                            && MusicPacks.ready(player) && !prepared.containsKey(client.uuid)) prepare(player);
                }
                switch (phase) {
                    case ADMITTING -> admit();
                    case STEADY -> sample();
                    case RECONNECT -> reconnect();
                    case EXITING -> awaitWorldDeletion();
                    case POST_CLEANUP -> postCleanupSample();
                    case DISCONNECTING -> awaitDisconnect();
                    default -> { }
                }
                if (!closed) next();
            } catch (RuntimeException | Error failure) {
                report.put("failure", failure.getClass().getName() + ": " + failure.getMessage());
                save(); throw failure;
            }
        }

        void prepare(ServerPlayer p) {
            var tutorial = Tutorial.participationToken(p); if (tutorial != null) Tutorial.leave(p, tutorial);
            RisingCampaign.leave(p);
            var data = Guardians.data(p); data.setGuardianClass(GuardianClass.HUNTER);
            data.setLoadout(GuardianClass.HUNTER, HunterAbilities.preset(Element.SOLAR));
            p.setGameMode(GameType.SURVIVAL);
            p.getAbilities().invulnerable = true; p.onUpdateAbilities();
            p.setItemInHand(InteractionHand.MAIN_HAND, WeaponItems.create(WeaponCatalog.find("austringer").orElseThrow()));
            // Safe-spawn terrain may still be loading; leave this peer unprepared and retry normally.
            if (!TowerSpawnWorld.teleport(p)) return;
            p.initInventoryMenu(); prepared.put(p.getUUID(), p);
        }

        List<ServerPlayer> group(int from, int count) {
            if (clients.size() < from + count) return List.of();
            return clients.subList(from, from + count).stream().map(c -> prepared.get(c.uuid)).filter(Objects::nonNull).toList();
        }
        boolean entered(StrikeCoordinator coordinator, int from) {
            var members = group(from, 3);
            return members.size() == 3 && members.stream().allMatch(coordinator::entered);
        }
        void launch(StrikeCoordinator coordinator, int from) {
            var group = group(from, 3);
            if (group.size() != 3 || coordinator.check(group) != null) return;
            var error = coordinator.start(group);
            check(h, error == null, "Production strike start rejected after check: " + error);
            for (var p : group) {
                var token = coordinator.participationToken(p);
                check(h, token != null, "Launch must own every member"); owned.put(p.getUUID(), new Owned(coordinator, token));
            }
            if (coordinator == DevilsLair.COORDINATOR) nextDevils++; else nextExodus++;
        }
        void admit() {
            int deadline = Math.clamp(Integer.getInteger("destiny.gametest.scale.instances.admissionTicks", 14000), 2400, 24000);
            check(h, phaseAge < deadline, "Production admission deadline exceeded: prepared=" + prepared.size() + " owned=" + owned.size());
            // Public entered() is a conservative boundary after PREPARING/READY/ADMITTING, never bypassed.
            if (nextDevils < 4 && (nextDevils == 0 || entered(DevilsLair.COORDINATOR, (nextDevils - 1) * 3)))
                launch(DevilsLair.COORDINATOR, nextDevils * 3);
            if (nextExodus < 2 && (nextExodus == 0 || entered(ExodusCrash.COORDINATOR, 12 + (nextExodus - 1) * 3)))
                launch(ExodusCrash.COORDINATOR, 12 + nextExodus * 3);
            for (var p : group(18, 12)) {
                if (!owned.containsKey(p.getUUID()) && RisingCampaign.check(p) == null) {
                    var error = RisingCampaign.start(p, true);
                    check(h, error == null, "Production campaign start rejected: " + error);
                    owned.put(p.getUUID(), new Owned(null, RisingCampaign.participationToken(p)));
                }
                if (RisingCampaign.entered(p) && skippedCampaign.add(p.getUUID()))
                    server.getCommands().performPrefixedCommand(server.createCommandSourceStack().withEntity(p).withLevel(p.level())
                                    .withCallback((success, result) -> campaignJumps.put(p.getUUID(), success && result > 0)),
                            "destiny rising skip breach_fight");
            }
            check(h, campaignJumps.values().stream().allMatch(Boolean::booleanValue), "Registered campaign QA stage jump failed");
            observeCampaignArrivals();
            captureWorlds();
            if (phaseAge % 200 == 0) {
                report.put("latest_admission_worlds", worldSnapshot());
                report.put("latest_admission_heap_bytes", heap()); save();
            }
            if (prepared.size() != 40 || owned.size() != 30 || worlds.size() != 18 || campaignJumps.size() != 12 || !allEntered(true) || !chunksReceived()) return;
            report.put("admission_wall_seconds", (System.nanoTime() - started) / 1e9);
            report.put("admission_ticks", phaseAge);
            admittedActivityPlayers = owned.size();
            report.put("worlds_at_steady", worldSnapshot());
            int maximum = Math.clamp(Integer.getInteger("destiny.gametest.scale.instances.expectedMaximumOwnedView", 8), 2, 32);
            for (var p : prepared.values()) {
                var view = (ChunkTrackingView.Positioned) p.getChunkTrackingView();
                check(h, view.viewDistance() <= maximum, "Owned world tracking cap not applied: " + p.getScoreboardName() + " view=" + view.viewDistance());
            }
            report.put("full_tracking_windows_received_before_sampling", true);
            phase = Phase.STEADY; phaseAge = 0; steadyStarted = System.nanoTime();
            receivedStart = bytes(true); sentStart = bytes(false); gcStart = gcTime(); packetsStart = packets();
            for (var p : prepared.values()) previousRounds.put(p.getUUID(), rounds(p));
            save();
        }

        boolean allEntered(boolean requireActionable) {
            if (clients.size() != 40) return false;
            var keys = new HashSet<ResourceKey<Level>>();
            for (int party = 0; party < 6; party++) {
                int from = party * 3; var coordinator = party < 4 ? DevilsLair.COORDINATOR : ExodusCrash.COORDINATOR;
                var members = group(from, 3);
                if (members.size() != 3 || members.stream().anyMatch(p -> !coordinator.entered(p) || (requireActionable && !coordinator.allows(p)))) return false;
                var key = members.getFirst().level().dimension();
                if (!keys.add(key) || members.stream().anyMatch(p -> !p.level().dimension().equals(key))) return false;
            }
            for (var p : group(18, 12))
                if (!RisingCampaign.entered(p) || (requireActionable && !RisingCampaign.allows(p, AbilitySlot.MELEE)) || !keys.add(p.level().dimension())) return false;
            return keys.size() == 18 && group(30, 10).stream().allMatch(p -> TowerSpawnWorld.isTower(p.level()))
                    && prepared.values().stream().allMatch(p -> !p.hasDisconnected() && p.isAlive() && p.connection.hasClientLoaded());
        }

        void captureWorlds() {
            for (var p : prepared.values()) if (Strikes.participating(p) || RisingCampaign.entered(p)) {
                if (TowerSpawnWorld.isTower(p.level())) continue;
                var level = p.level();
                // Only capture after actual transfer, not the tower occupied while a session is queued.
                if (!DevilsLair.entered(p) && !ExodusCrash.COORDINATOR.entered(p) && !RisingCampaign.entered(p)) continue;
                worlds.computeIfAbsent(level.dimension(), key -> new WorldProbe(key,
                        new WeakReference<>(Objects.requireNonNull(level.getChunkSource().getDataStorage().get(TicketStorage.TYPE), "Active world ticket storage"))));
            }
            observedWorldCount = Math.max(observedWorldCount, worlds.size());
        }
        void observeCampaignArrivals() {
            for (var entry : owned.entrySet()) if (entry.getValue().strike == null) {
                try {
                    // Test-only observation of the public ArrivalChunks metric on the exact owned session token.
                    var field = entry.getValue().token.getClass().getDeclaredField("arrival"); field.setAccessible(true);
                    var arrival = (ArrivalChunks) field.get(entry.getValue().token);
                    int columns = arrival == null ? 0 : arrival.requestedColumns();
                    check(h, columns <= 1, "Campaign arrival must not prefetch an entire map/view window");
                    observedArrivalColumns.merge(entry.getKey(), columns, Math::max);
                } catch (ReflectiveOperationException failure) { throw new AssertionError(failure); }
            }
        }
        boolean chunksReceived() {
            for (var client : clients) {
                var p = prepared.get(client.uuid);
                if (!trackingReceived(client, p)) return false;
            }
            return true;
        }
        boolean trackingReceived(ScaleLoopbackClient client, ServerPlayer p) {
            if (p == null || !p.connection.hasClientLoaded() || !(p.getChunkTrackingView() instanceof ChunkTrackingView.Positioned view)) return false;
            var expected = new it.unimi.dsi.fastutil.longs.LongArrayList(); view.forEach(c -> expected.add(c.pack()));
            if (expected.isEmpty() || !client.receivedChunks.contains(p.chunkPosition().pack())) return false;
            for (long key : expected) if (!client.receivedChunks.contains(key)) return false;
            return true;
        }

        void sample() {
            if (phaseAge == 100 && Boolean.getBoolean("destiny.gametest.scale.instances.probeSave")) {
                report.put("explicit_periodic_save_probe_server_tick", server.getTickCount());
                server.saveEverything(true, false, false); // Exact native autosave flags in this owned fixture only.
            }
            check(h, allEntered(false), "All forty peers must remain in their real admitted activities/tower");
            for (var p : prepared.values()) {
                int now = rounds(p), previous = previousRounds.put(p.getUUID(), now);
                if (now >= 0 && previous >= 0) paidDrops.merge(p.getUUID(), Math.max(0, previous - now), Integer::sum);
            }
            if (phaseAge > 60) {
                long now = System.nanoTime(); if (wholeTicks.isEmpty()) firstSteady = now;
                lastSteady = now; wholeTicks.add(wholeTick());
            }
            int duration = Math.clamp(Integer.getInteger("destiny.gametest.scale.instances.steadyTicks", 300), 100, 6000);
            if (phaseAge < duration) return;
            for (var p : group(30, 10)) check(h, paidDrops.getOrDefault(p.getUUID(), 0) > 0, "Tower cohort must actually fire paid rounds");
            var steady = new LinkedHashMap<String, Object>();
            steady.put("ticks", phaseAge); steady.put("mspt_warmup_ticks_excluded", 60);
            steady.put("wall_seconds", (System.nanoTime() - steadyStarted) / 1e9);
            steady.put("observed_steady_tps", (wholeTicks.size() - 1) / ((lastSteady - firstSteady) / 1e9));
            steady.put("whole_tick_nanos", List.copyOf(wholeTicks));
            steady.put("client_received_framed_bytes", bytes(true) - receivedStart);
            steady.put("client_sent_framed_bytes", bytes(false) - sentStart);
            var delta = new TreeMap<String, Long>(); packets().forEach((k, v) -> delta.put(k, v - packetsStart.getOrDefault(k, 0L)));
            steady.put("client_decoded_packets", delta); steady.put("gc_collection_ms", gcTime() - gcStart);
            steady.put("heap_used_bytes", heap()); steady.put("worlds", worldSnapshot());
            var drops = new TreeMap<String, Integer>(); clients.forEach(c -> drops.put(c.name, paidDrops.getOrDefault(c.uuid, 0)));
            steady.put("observed_paid_round_drops", drops);
            report.put("steady", steady);
            report.put("save_trace", GameTestScaleSaveTrace.drain(server));
            if (lifecycle && cycle == 0) { beginReconnect(); return; }
            finishActivities();
        }

        void finishActivities() {
            leaveOwned(); owned.clear();
            report.put("strong_session_tokens_released_before_cleanup_wait", true);
            phase = Phase.EXITING; phaseAge = 0; save();
        }

        void beginReconnect() {
            // Nine native disconnects leave31 peers online. Party0 returns; parties1/5 expire naturally.
            for (int i : new int[]{0, 1, 2, 3, 4, 5, 15, 16, 17}) {
                dropPeer(i, i < 3);
            }
            check(h, expiryWorlds.size() == 2, "Expected one Devils and one Exodus world for all-offline expiry");
            phase = Phase.RECONNECT; phaseAge = 0; reconnectStarted = System.nanoTime(); save();
        }

        void dropPeer(int index, boolean returns) {
            var c = clients.get(index); var p = prepared.get(c.uuid);
            intentionallyOffline.add(c.uuid);
            expectedDisconnects.put(System.identityHashCode(p.connection), p.getUUID());
            if (returns) { rejoinWorlds.put(c.uuid, p.level().dimension()); oldEntityIds.put(c.uuid, p.getId()); }
            else expiryWorlds.add(p.level().dimension());
            c.close();
        }

        void replacePeer(int index) {
            var old = clients.get(index);
            check(h, server.getPlayerList().getPlayer(old.uuid) == null, "Old connection must be removed before reconnect");
            prepared.remove(old.uuid);
            clients.set(index, new ScaleLoopbackClient(old.name, port, server.registryAccess(), packs.accepted));
            intentionallyOffline.remove(old.uuid);
        }

        void reconnect() {
            check(h, phaseAge < StrikeRoster.RECONNECT_TICKS + 2000, "Native reconnect/expiry deadline exceeded");
            int connected = (int) clients.stream().filter(c -> c.playing && c.connection.isConnected()).count();
            minimumConnected = Math.min(minimumConnected, connected);
            check(h, connected >= 31, "At least31 native peers must stay connected during lifecycle verification");
            if (phaseAge > 60) lifecycleTicks.add(wholeTick());
            boolean allExpiredPeersGone = java.util.stream.IntStream.of(3, 4, 5, 15, 16, 17)
                    .allMatch(i -> server.getPlayerList().getPlayer(clients.get(i).uuid) == null);
            if (allExpiredPeersGone && offlineObservedAt < 0) offlineObservedAt = server.getTickCount();
            if (phaseAge >= 100 && !replacementsStarted) {
                for (int i = 0; i < 3; i++) replacePeer(i);
                replacementsStarted = true;
            }
            if (exodusDropAt >= 0 && phaseAge - exodusDropAt >= 100 && !exodusReplacementsStarted) {
                for (int i = 12; i < 15; i++) replacePeer(i);
                exodusReplacementsStarted = true;
            }
            if (replacementsStarted && !rejoined) {
                boolean ready = true;
                for (int i : new int[]{0, 1, 2, 12, 13, 14}) {
                    if (i >= 12 && !exodusReplacementsStarted) continue;
                    var client = clients.get(i); var p = server.getPlayerList().getPlayer(client.uuid);
                    var coordinator = i < 3 ? DevilsLair.COORDINATOR : ExodusCrash.COORDINATOR;
                    if (p == null || !MusicPacks.ready(p) || !coordinator.entered(p)
                            || !coordinator.allows(p) || !trackingReceived(client, p)) { ready = false; continue; }
                    check(h, p.getId() != oldEntityIds.get(client.uuid), "Reconnect must create a new native player entity");
                    check(h, coordinator.participationToken(p) == owned.get(client.uuid).token,
                            "Reconnect must preserve the exact existing production run");
                    check(h, p.level().dimension().equals(rejoinWorlds.get(client.uuid)), "Reconnect must return to the same world");
                    if (prepared.put(client.uuid, p) != p) { p.getAbilities().invulnerable = true; p.onUpdateAbilities(); }
                }
                if (ready && !devilsRejoined) {
                    devilsRejoined = true; report.put("devils_rejoin_completed_at_phase_tick", phaseAge);
                    for (int i = 12; i < 15; i++) dropPeer(i, true);
                    exodusDropAt = phaseAge; save();
                }
                if (ready && exodusReplacementsStarted) {
                    rejoined = true; report.put("rejoined_same_run_peers", 6); report.put("rejoined_at_phase_tick", phaseAge); save();
                }
            }
            if (offlineObservedAt < 0) return;
            int elapsed = server.getTickCount() - offlineObservedAt;
            if (elapsed < StrikeRoster.RECONNECT_TICKS - 10)
                check(h, expiryWorlds.stream().allMatch(k -> server.getLevel(k) != null), "Offline worlds deleted before production grace elapsed");
            if (phaseAge % 200 == 0) {
                report.put("latest_lifecycle_elapsed_ticks", elapsed);
                report.put("latest_reconnect_peers", reconnectReadiness());
                report.put("latest_expiry_runs", expiryReadiness());
                report.put("expiry_worlds_still_registered", expiryWorlds.stream().filter(k -> server.getLevel(k) != null)
                        .map(k -> k.identifier().toString()).sorted().toList());
                save();
            }
            if (elapsed < StrikeRoster.RECONNECT_TICKS || !rejoined
                    || expiryWorlds.stream().anyMatch(k -> server.getLevel(k) != null)) return;
            var result = new LinkedHashMap<String, Object>();
            result.put("minimum_connected_native_peers", minimumConnected);
            result.put("same_run_rejoined_peers", 6);
            result.put("all_offline_expired_worlds", expiryWorlds.stream().map(k -> k.identifier().toString()).sorted().toList());
            result.put("offline_elapsed_server_ticks", elapsed);
            result.put("phase_ticks", phaseAge); result.put("wall_seconds", (System.nanoTime() - reconnectStarted) / 1e9);
            result.put("whole_tick_nanos_after_first60", List.copyOf(lifecycleTicks));
            result.put("worlds_after_expiry", worldSnapshot()); result.put("heap_used_bytes", heap());
            for (var entry : expectedDisconnects.entrySet()) {
                var events = disconnectEvents.stream().filter(e -> e.connection == entry.getKey() && e.player.equals(entry.getValue())).toList();
                check(h, events.size() == 1 && events.getFirst().serverThread, "Every dropped connection needs exactly one server-thread disconnect event");
            }
            result.put("verified_once_only_server_thread_disconnects", expectedDisconnects.size());
            report.put("lifecycle", result); report.put("reconnect_grace_exercised", true);
            report.put("reconnect_grace_elapsed_ticks", elapsed);
            finishActivities();
        }

        List<Map<String, Object>> reconnectReadiness() {
            var result = new ArrayList<Map<String, Object>>();
            for (int i : new int[]{0, 1, 2, 12, 13, 14}) {
                var c = clients.get(i); var p = server.getPlayerList().getPlayer(c.uuid);
                if (!rejoinWorlds.containsKey(c.uuid)) continue;
                var coordinator = i < 3 ? DevilsLair.COORDINATOR : ExodusCrash.COORDINATOR;
                var row = new LinkedHashMap<String, Object>(); row.put("name", c.name); row.put("server_player", p != null);
                row.put("peer_connected", c.connection.isConnected()); row.put("received_chunks", c.receivedChunks.size());
                row.put("client_position", c.position.toString()); row.put("packets", c.packetCounts());
                if (p != null) {
                    row.put("client_loaded", p.connection.hasClientLoaded()); row.put("base_pack_ready", MusicPacks.ready(p));
                    row.put("activity_pack_ready", ActivityPacks.ready(p, coordinator.info().id())); row.put("entered", coordinator.entered(p));
                    row.put("allows", coordinator.allows(p)); row.put("tracking_received", trackingReceived(c, p));
                    row.put("world", p.level().dimension().identifier().toString()); row.put("server_position", p.position().toString());
                    row.put("alive", p.isAlive()); row.put("health", p.getHealth()); row.put("invulnerable", p.getAbilities().invulnerable);
                    row.put("guardian_down", kim.biryeong.destiny.down.GuardianDown.active(p));
                    if (p.getChunkTrackingView() instanceof ChunkTrackingView.Positioned view) {
                        int[] counts = {0, 0}; view.forEach(chunk -> { counts[0]++; if (!c.receivedChunks.contains(chunk.pack())) counts[1]++; });
                        row.put("tracking_view", view.viewDistance()); row.put("expected_chunks", counts[0]); row.put("missing_chunks", counts[1]);
                    }
                }
                result.add(row);
            }
            return result;
        }

        List<Map<String, Object>> expiryReadiness() {
            var result = new ArrayList<Map<String, Object>>();
            for (int index : new int[]{3, 15}) {
                var token = owned.get(clients.get(index).uuid).token;
                var run = (kim.biryeong.destiny.activity.strike.StrikeRun) token;
                var row = new LinkedHashMap<String, Object>();
                row.put("implementation", token.getClass().getName()); row.put("running", run.running()); row.put("closed", run.closed());
                row.put("server_tick", server.getTickCount()); row.put("registered", server.getLevel(run.level().dimension()) != null);
                row.put("world_players", run.level().players().stream().map(p -> Map.of("id", p.getUUID().toString(),
                        "entity", p.getId(), "removed", p.isRemoved(), "disconnected", p.hasDisconnected())).toList());
                try {
                    var f = token.getClass().getDeclaredField("roster"); f.setAccessible(true); var roster = (StrikeRoster) f.get(token);
                    row.put("members", roster.members()); row.put("connected", roster.connected()); row.put("abandoned", roster.abandoned(server.getTickCount()));
                    var at = StrikeRoster.class.getDeclaredField("allOfflineAt"); at.setAccessible(true); row.put("all_offline_at", at.getLong(roster));
                } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
                result.add(row);
            }
            return result;
        }

        void leaveOwned() {
            for (var entry : owned.entrySet()) {
                var p = prepared.get(entry.getKey()); if (p == null) continue;
                var token = entry.getValue();
                if (token.strike == null) RisingCampaign.leave(p, token.token);
                else token.strike.leave(p, token.token);
            }
        }
        void awaitWorldDeletion() {
            // Normal explicit leave should be fast. This bound still exceeds unmodified120s reconnect grace.
            int limit = Math.clamp(Integer.getInteger("destiny.gametest.scale.instances.cleanupTicks", 2600), 2401, 6000);
            check(h, phaseAge < limit, "Owned activity worlds did not unload within bounded cleanup/grace window");
            if (worlds.keySet().stream().anyMatch(k -> server.getLevel(k) != null)) return;
            check(h, prepared.values().stream().noneMatch(p -> Strikes.participating(p) || RisingCampaign.participating(p)), "Activity ownership must be released");
            var released = new LinkedHashMap<String, Object>();
            for (var probe : worlds.values()) {
                var tickets = probe.tickets.get();
                released.put(probe.key.identifier().toString(), tickets == null
                        ? Map.of("removed_from_server", true, "ticket_storage_collected", true)
                        : Map.of("removed_from_server", true, "has_retained_ticket_records", tickets.hasTickets(),
                                "keeps_dimension_active", tickets.shouldKeepDimensionActive(), "forced_columns", tickets.getForceLoadedChunks().size(), "remaining_ticket_types", ticketTypes(tickets)));
            }
            report.put("world_cleanup_ticks", phaseAge); report.put("released_worlds", released);
            report.put("cleanup_deadline_ticks", limit);
            save(); // Preserve every remaining type/flag; Fantasy closing deliberately retains native UNKNOWN tickets.
            for (var probe : worlds.values()) {
                var tickets = probe.tickets.get();
                check(h, tickets == null || !tickets.shouldKeepDimensionActive()
                        && tickets.getForceLoadedChunks().isEmpty() && ticketTypes(tickets).keySet().stream().allMatch("UNKNOWN"::equals), "Deleted world retains an unexpected live/forced ticket: " + probe.key.identifier()
                        + " / " + (tickets == null ? "collected" : ticketTypes(tickets)));
            }
            worlds.clear(); // Only scalar report data remains; WorldProbe held weak TicketStorage references.
            phase = Phase.POST_CLEANUP; phaseAge = 0;
        }
        Map<String, Integer> ticketTypes(TicketStorage tickets) {
            try {
                var field = TicketStorage.class.getDeclaredField("tickets"); field.setAccessible(true);
                var types = new TreeMap<String, Integer>();
                for (var values : ((Map<?, ?>) field.get(tickets)).values()) for (var raw : (List<?>) values) {
                    var ticket = (net.minecraft.server.level.Ticket) raw;
                    String name = ticket.getType() == net.minecraft.server.level.TicketType.UNKNOWN ? "UNKNOWN" : ticket.getType().toString();
                    types.merge(name, 1, Integer::sum);
                }
                return types;
            } catch (ReflectiveOperationException failure) { throw new AssertionError(failure); }
        }

        void postCleanupSample() {
            // Separate callback: ticket/level locals from cleanup are gone, and no session tokens are retained.
            report.put("heap_used_after_world_unload_bytes", heap());
            report.put("heap_sample_note", "Unforced heap-used after logical registry/ticket cleanup, not GC-live bytes or a long-run memory certification");
            var result = new LinkedHashMap<String, Object>();
            result.put("cycle", cycle + 1); result.put("steady", report.get("steady"));
            result.put("released_worlds", report.get("released_worlds")); result.put("world_cleanup_ticks", report.get("world_cleanup_ticks"));
            result.put("heap_used_after_world_unload_bytes", heap()); result.put("worlds_after_cleanup", worldSnapshot());
            cycles.add(result); report.put("cycle_results", cycles);
            if (lifecycle && cycle == 0) {
                for (int i : new int[]{3, 4, 5, 15, 16, 17}) replacePeer(i);
                cycle++; nextDevils = 0; nextExodus = 0;
                skippedCampaign.clear(); campaignJumps.clear(); observedArrivalColumns.clear();
                previousRounds.clear(); paidDrops.clear(); wholeTicks.clear();
                rejoinWorlds.clear(); oldEntityIds.clear(); expiryWorlds.clear(); lifecycleTicks.clear();
                phase = Phase.ADMITTING; phaseAge = 0; save(); return;
            }
            clients.forEach(ScaleLoopbackClient::close); phase = Phase.DISCONNECTING; phaseAge = 0;
        }
        void awaitDisconnect() {
            check(h, phaseAge < 200, "Owned native peers must disconnect cleanly");
            if (clients.stream().anyMatch(c -> server.getPlayerList().getPlayer(c.uuid) != null)) return;
            phase = Phase.DONE; passed = true; save(); close(); h.succeed();
        }

        int rounds(ServerPlayer p) {
            var entry = WeaponItems.entry(p.getMainHandItem());
            return entry.map(e -> WeaponItems.magazine(p.getMainHandItem(), WeaponProfile.forEntry(e)).rounds()).orElse(-1);
        }
        List<Map<String, Object>> worldSnapshot() {
            var result = new ArrayList<Map<String, Object>>();
            for (var level : server.getAllLevels()) {
                var row = new LinkedHashMap<String, Object>();
                row.put("key", level.dimension().identifier().toString()); row.put("players", level.players().size());
                row.put("loaded_chunks", level.getChunkSource().getLoadedChunksCount());
                row.put("pending_chunk_tasks", level.getChunkSource().getPendingTasksCount());
                row.put("active_tickets", level.getChunkSource().hasActiveTickets());
                row.put("forced_columns", level.getChunkSource().getForceLoadedChunks().size());
                row.put("generator", level.getChunkSource().getGenerator().getClass().getName());
                row.put("level_implementation", level.getClass().getName()); row.put("no_save_flag", level.noSave());
                row.put("living_nonplayer_entities", java.util.stream.StreamSupport.stream(level.getAllEntities().spliterator(), false)
                        .filter(e -> e instanceof net.minecraft.world.entity.LivingEntity && !(e instanceof ServerPlayer) && e.isAlive()).count());
                var actual = new TreeMap<String, Integer>();
                for (var p : level.players()) if (ids.contains(p.getUUID()) && p.getChunkTrackingView() instanceof ChunkTrackingView.Positioned view)
                    actual.put(p.getScoreboardName(), view.viewDistance());
                row.put("actual_player_tracking_view_distances", actual); result.add(row);
            }
            return result;
        }
        long wholeTick() {
            try {
                var f = kim.biryeong.destiny.debug.HunterQa.class.getDeclaredField("completedTickNanos");
                f.setAccessible(true); return f.getLong(null);
            } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
        }
        long bytes(boolean receive) { return clients.stream().mapToLong(c -> receive ? c.receivedBytes.sum() : c.sentBytes.sum()).sum(); }
        long gcTime() { return ManagementFactory.getGarbageCollectorMXBeans().stream().mapToLong(b -> Math.max(0, b.getCollectionTime())).sum(); }
        long heap() { return ManagementFactory.getMemoryMXBean().getHeapMemoryUsage().getUsed(); }
        Map<String, Long> packets() {
            var counts = new TreeMap<String, Long>(); clients.forEach(c -> c.packetCounts().forEach((k, v) -> counts.merge(k, v, Long::sum))); return counts;
        }
        void save() {
            report.put("phase", phase.toString()); report.put("passed", passed);
            report.put("current_cycle", cycle + 1);
            report.put("disconnect_events", List.copyOf(disconnectEvents));
            report.put("wall_seconds", (System.nanoTime() - started) / 1e9);
            report.put("prepared_peers", prepared.size()); report.put("owned_activity_players", Math.max(admittedActivityPlayers, owned.size()));
            report.put("current_session_token_references", owned.size());
            report.put("successful_campaign_stage_jumps", campaignJumps.values().stream().filter(Boolean::booleanValue).count());
            var arrivals = new TreeMap<String, Integer>(); clients.forEach(c -> {
                if (observedArrivalColumns.containsKey(c.uuid)) arrivals.put(c.name, observedArrivalColumns.get(c.uuid));
            });
            report.put("maximum_observed_pending_campaign_arrival_columns", arrivals);
            report.put("observed_temporary_worlds", observedWorldCount);
            report.put("server_heap_max_bytes", ManagementFactory.getMemoryMXBean().getHeapMemoryUsage().getMax());
            try {
                var path = Path.of(System.getProperty("destiny.gametest.scale.instances.output", "qa/scale-instances-40.json"));
                Files.createDirectories(path.toAbsolutePath().getParent());
                Files.writeString(path, new GsonBuilder().setPrettyPrinting().create().toJson(report) + "\n");
            } catch (java.io.IOException failure) { throw new AssertionError(failure); }
        }

        @Override public void close() {
            if (closed) return; closed = true;
            try { leaveOwned(); clients.forEach(ScaleLoopbackClient::close); }
            finally {
                if (listenerStarted) server.getConnection().stopTcpServerListener();
                server.setUsesAuthentication(wasAuthenticating);
                server.getPlayerList().setViewDistance(originalView); server.getPlayerList().setSimulationDistance(originalSimulation);
                if (verifiedPacks != null && !verifiedPacks.isDone()) verifiedPacks.cancel(true);
                owned.clear(); worlds.clear(); prepared.clear(); clients.clear();
                GameTestScaleSaveTrace.stop(server);
                if (active == this) active = null;
            }
        }
    }
}
