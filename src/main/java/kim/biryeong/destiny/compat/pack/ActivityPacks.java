package kim.biryeong.destiny.compat.pack;

import eu.pb4.polymer.autohost.api.AutoHostUtils;
import eu.pb4.polymer.autohost.impl.AutoHost;
import eu.pb4.polymer.resourcepack.api.*;
import kim.biryeong.R2ResourcePackUpload;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.minigamelib.music.MusicPacks;
import net.fabricmc.fabric.api.event.lifecycle.v1.*;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.context.*;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.common.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerCommonPacketListenerImpl;
import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.BooleanSupplier;

/** Server-scoped publication and connection/run-owned client pack leases, reusable by any activity. */
public final class ActivityPacks {
    public static final int LOAD_TIMEOUT_TICKS = 180 * 20;
    private static final long TIMEOUT_NANOS = TimeUnit.SECONDS.toNanos(180);
    private static final ActivityPackCatalog CATALOG = ActivityPackCatalog.load();
    private static volatile Session current;
    private static boolean initialized;
    private record Published(ActivityPackArchive.Archive archive, String url) { }
    private static final class Session {
        final MinecraftServer server;
        final ExecutorService worker = Executors.newFixedThreadPool(2, r -> {
            var t = new Thread(r, "destiny-activity-packs"); t.setDaemon(true); return t;
        });
        final Map<String, CompletableFuture<Published>> publications = new HashMap<>();
        final Map<UUID, Lease> leases = new HashMap<>();
        volatile ActivityPackArchive build;
        Session(MinecraftServer server) { this.server = server; }
    }
    private static final class Lease {
        final ServerPlayer player;
        final ServerCommonPacketListenerImpl connection;
        final Object owner;
        final BooleanSupplier retained;
        final String activity;
        long deadline = System.nanoTime() + TIMEOUT_NANOS;
        CompletableFuture<Published> publication;
        ActivityPackLoad load;
        String baseHash = "", failure;
        Lease(ServerPlayer player, String activity, Object owner, BooleanSupplier retained) {
            this.player = player; this.connection = player.connection; this.activity = activity;
            this.owner = owner; this.retained = retained;
        }
    }
    private ActivityPacks() { }
    public static Path directory() { return FabricLoader.getInstance().getGameDir().resolve("polymer/destiny-activity-packs"); }
    public static void validateCached(Path baseZip, String baseSha1) throws java.io.IOException {
        ActivityPackArchive.validateBase(baseZip, CATALOG);
        ActivityPackArchive.read(directory(), baseSha1, CATALOG);
    }
    /** Install after the lossless compression pass, so archives contain the final client bytes. */
    public static synchronized void init() {
        if (initialized) return;
        initialized = true;
        ServerLifecycleEvents.SERVER_STARTING.register(server -> current = new Session(server));
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            var s = current;
            if (s == null || s.server != server) return;
            for (var lease : List.copyOf(s.leases.values())) release(s, lease);
            current = null; s.worker.shutdownNow();
        });
        ServerTickEvents.END_SERVER_TICK.register(ActivityPacks::tick);
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            var s = current;
            if (s == null || s.server != server) return;
            var lease = s.leases.get(handler.getPlayer().getUUID());
            if (lease != null && lease.connection == handler) s.leases.remove(handler.getPlayer().getUUID(), lease);
        });
        PolymerResourcePackUtils.RESOURCE_PACK_CREATION_EVENT.register(builder -> {
            var s = current;
            if (s == null) throw new IllegalStateException("No server owns the activity pack build");
            var capture = new ActivityPackArchive(CATALOG); s.build = capture;
            builder.addPreFinishTask(output -> {
                var exclusiveInputs = new LinkedHashMap<String, byte[]>();
                output.forEachResource((path, data) -> {
                    if (capture.selects(path)) exclusiveInputs.put(path, data.readAllBytes());
                });
                output.addData("destiny/activity-pack-inputs.json", PackResource.of(ActivityPackArchive.inputFingerprint(CATALOG, exclusiveInputs)));
                output.addResourceConverter((path, data) -> {
                    if (data == null || !capture.selects(path)) return data;
                    byte[] rest = capture.convert(path, data.readAllBytes());
                    return rest == null ? null : PackResource.of(rest);
                });
            });
        });
        PolymerResourcePackUtils.RESOURCE_PACK_FINISHED_EVENT.register(result -> {
            var s = current;
            if (s == null || !(result instanceof OutputGenerator.Result zip)) return;
            var capture = s.build; s.build = null;
            if (capture == null || zip.hadIssues()) return;
            try {
                var archives = capture.finish(zip.path(), zip.hash(), directory());
                for (var archive : archives.values()) DestinyGuardians.LOGGER.info(
                        "Activity pack built: {} / {} bytes / {}", archive.id(), archive.size(), archive.sha1());
            } catch (Exception e) {
                // The base ZIP deliberately omits these assets. Admission stays closed until a valid set exists.
                DestinyGuardians.LOGGER.error("Activity resource packs could not be finalized; strike entry is unavailable", e);
            }
        });
    }
    public static void acquire(ServerPlayer player, String activity, Object owner, BooleanSupplier retained) {
        CATALOG.activity(activity);
        var s = current;
        if (s == null || s.server != player.level().getServer() || !s.server.isSameThread())
            throw new IllegalStateException("Activity pack acquisition needs its server thread");
        // A corrected R2 configuration or recovered network may be retried by a new launch.
        String key = MusicPacks.published().hash() + "/" + activity;
        var publication = s.publications.get(key);
        if (publication != null && publication.isCompletedExceptionally()) s.publications.remove(key, publication);
        var old = s.leases.get(player.getUUID());
        if (old != null && old.owner == owner && old.connection == player.connection) return;
        if (old != null) release(s, old);
        s.leases.put(player.getUUID(), new Lease(player, activity, owner, retained));
    }
    public static boolean ready(ServerPlayer player, String activity) {
        var s = current;
        var lease = s == null ? null : s.leases.get(player.getUUID());
        return matches(lease, player, activity) && lease.failure == null && lease.load != null && lease.load.ready()
                && MusicPacks.ready(player) && lease.baseHash.equals(MusicPacks.published().hash());
    }
    public static String failure(ServerPlayer player, Object owner) {
        var s = current;
        var lease = s == null ? null : s.leases.get(player.getUUID());
        return lease != null && lease.owner == owner && lease.connection == player.connection ? lease.failure : null;
    }
    public static String loadingStatus(ServerPlayer player, String activity) {
        var s = current;
        var lease = s == null ? null : s.leases.get(player.getUUID());
        if (!matches(lease, player, activity) || ready(player, activity)) return null;
        if (lease.failure != null) return "리소스 팩을 불러오지 못했습니다";
        if (lease.load == null) return "공격전 리소스를 준비하는 중";
        return switch (lease.load.stage()) {
            case DOWNLOADED -> "공격전 리소스 팩을 적용하는 중";
            case READY -> "공용 리소스를 확인하는 중";
            default -> "공격전 리소스 팩을 다운로드하는 중";
        };
    }
    public static float progress(ServerPlayer player, String activity) {
        if (ready(player, activity)) return 1;
        var s = current; var lease = s == null ? null : s.leases.get(player.getUUID());
        if (!matches(lease, player, activity) || lease.load == null) return 0;
        return switch (lease.load.stage()) { case REQUESTED -> .15f; case ACCEPTED -> .25f; case DOWNLOADED -> .8f; default -> 0; };
    }
    private static boolean matches(Lease lease, ServerPlayer player, String activity) {
        return lease != null && lease.player == player && lease.connection == player.connection && lease.activity.equals(activity);
    }
    private static CompletableFuture<Published> publication(Session s, String activity, String baseHash) {
        boolean external = "polymer:external".equals(AutoHost.config.type);
        return s.publications.computeIfAbsent(baseHash + "/" + activity, key -> CompletableFuture.supplyAsync(() -> {
            try {
                ActivityPackArchive.validateBase(PolymerResourcePackUtils.getMainPath(), CATALOG);
                var archive = ActivityPackArchive.read(directory(), baseHash, CATALOG).get(activity);
                if (!external) return new Published(archive, null);
                var result = R2ResourcePackUpload.uploadPack("destiny:" + activity, archive.path());
                if (!result.sha1().equals(archive.sha1()) || result.size() != archive.size())
                    throw new java.io.IOException("Published activity pack does not match its local archive");
                DestinyGuardians.LOGGER.info("Activity pack published to R2: {} / {}", activity, result.publicUrl());
                return new Published(archive, result.publicUrl());
            } catch (Exception e) { throw new CompletionException(e); }
        }, s.worker));
    }
    private static void tick(MinecraftServer server) {
        var s = current;
        if (s == null || s.server != server) return;
        for (var lease : List.copyOf(s.leases.values())) {
            var p = lease.player;
            if (p.hasDisconnected() || server.getPlayerList().getPlayer(p.getUUID()) != p || p.connection != lease.connection || !lease.retained.getAsBoolean()) {
                release(s, lease); continue;
            }
            if (lease.failure != null) continue;
            if (!MusicPacks.ready(p)) {
                // Reloading the base invalidates this request. A late ACK cannot approve its replacement.
                if (lease.load != null) {
                    if (lease.load.ready()) lease.deadline = System.nanoTime() + TIMEOUT_NANOS;
                    pop(lease); lease.load = null;
                }
                if (System.nanoTime() > lease.deadline) fail(lease, "공용 리소스 팩 확인 시간이 초과되었습니다.");
                continue;
            }
            String baseHash = MusicPacks.published().hash();
            if (!baseHash.equals(lease.baseHash)) {
                if (lease.load != null) {
                    if (lease.load.ready()) lease.deadline = System.nanoTime() + TIMEOUT_NANOS;
                    pop(lease);
                }
                lease.load = null; lease.publication = null; lease.baseHash = baseHash;
            }
            if (!ready(p, lease.activity) && System.nanoTime() > lease.deadline) {
                fail(lease, "리소스 팩 다운로드 또는 적용 시간이 초과되었습니다."); continue;
            }
            if (lease.load != null) continue;
            if (lease.publication == null) lease.publication = publication(s, lease.activity, baseHash);
            if (!lease.publication.isDone()) continue;
            try {
                var published = lease.publication.join();
                String url = published.url();
                if (url == null) {
                    // Local/in-process AutoHost remains usable for isolated QA and non-R2 servers.
                    var id = DestinyGuardians.id("activity_packs/" + lease.activity + "/" + published.archive().sha1() + ".zip");
                    AutoHostUtils.registerHostedFile(id, published.archive().path());
                    url = PacketContext.supplyWithContext((PacketContextProvider)(Object)p.connection,
                            () -> AutoHost.provider.getFilePath(PacketContext.orElseThrow(), id));
                }
                lease.load = new ActivityPackLoad(UUID.randomUUID());
                p.connection.send(new ClientboundResourcePackPushPacket(lease.load.request(), url, published.archive().sha1(), false,
                        Optional.of(Component.literal(CATALOG.activity(lease.activity).name() + " 전용 리소스 팩"))));
                DestinyGuardians.LOGGER.info("Activity pack requested: {} / {} / {} / origin {}", p.getGameProfile().name(),
                        lease.activity, lease.load.request(), p.level().dimension().identifier());
            } catch (Exception e) {
                DestinyGuardians.LOGGER.error("Activity pack publication failed for {}", lease.activity, e);
                fail(lease, "공격전 리소스 팩을 준비하지 못했습니다.");
            }
        }
    }
    private static void fail(Lease lease, String reason) { lease.failure = reason; if (lease.load != null) lease.load.fail(reason); }
    public static void response(ServerCommonPacketListenerImpl connection, ServerboundResourcePackPacket packet) {
        var s = current;
        if (s == null) return;
        s.server.execute(() -> {
            if (current != s) return;
            var lease = s.leases.get(connection.getOwner().id());
            if (lease == null || lease.connection != connection || lease.load == null || !lease.load.request().equals(packet.id())) return;
            lease.load.response(packet.id(), packet.action().name());
            DestinyGuardians.LOGGER.info("Activity pack response: {} / {} / {}", lease.activity, packet.id(), packet.action());
            if (lease.load.failure() != null) fail(lease, "공격전 리소스 팩 다운로드 또는 적용에 실패했습니다.");
        });
    }
    public static void removed(ServerCommonPacketListenerImpl connection, Optional<UUID> id) {
        var s = current;
        if (s == null) return;
        s.server.execute(() -> {
            if (current != s) return;
            var lease = s.leases.get(connection.getOwner().id());
            if (lease != null && lease.connection == connection && lease.load != null
                    && (id.isEmpty() || id.get().equals(lease.load.request())))
                fail(lease, "공격전 리소스 팩이 해제되었습니다.");
        });
    }
    private static void pop(Lease lease) {
        var load = lease.load;
        lease.load = null;
        if (load != null && !lease.player.hasDisconnected() && lease.player.connection == lease.connection)
            lease.player.connection.send(new ClientboundResourcePackPopPacket(Optional.of(load.request())));
    }
    private static void release(Session s, Lease lease) {
        if (!s.leases.remove(lease.player.getUUID(), lease)) return;
        pop(lease);
    }
}
