package kim.biryeong.destiny.activity.strike;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.compat.pack.ActivityPacks;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.campaign.RisingCampaign;
import kim.biryeong.destiny.crucible.CrucibleRuntime;
import kim.biryeong.destiny.down.GuardianDown;
import kim.biryeong.destiny.inventory.WeaponScreen;
import kim.biryeong.destiny.tutorial.Tutorial;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import kim.biryeong.minigamelib.music.MusicPacks;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;
import java.util.function.Function;

/**
 * Everything a strike needs around its runs that is not about the strike itself: the run registry, launch eligibility,
 * the per-tick drive, reconnect handling, return-to-origin and the "may this player act" rules inside run worlds.
 * A strike supplies its roster limits, its map preload, its world factory and a {@link StrikeRun} implementation;
 * state is per host, so strikes never share runs, worlds or return records.
 */
public final class StrikeHost<R extends StrikeRun> {
    @FunctionalInterface
    public interface RunFactory<R extends StrikeRun> {
        /** Builds the run for an already prepared world. Throwing aborts the launch and closes the world. */
        R create(MinecraftServer server, StrikeInstances instances, StrikeInstances.Instance instance, List<ServerPlayer> fireteam);
    }
    /** Shared launch-time ceiling for world-build work across all runs of this host. */
    private static final long TICK_BUDGET_NANOS = 2_000_000L;

    private final String logTag, resourcePack;
    private final int minPlayers, maxPlayers;
    private final Function<MinecraftServer, StrikeInstances> instanceFactory;
    private final Function<MinecraftServer, CompletableFuture<Void>> mapLoader;
    private final RunFactory<R> runFactory;
    private final Consumer<ServerPlayer> strikeCleanup;
    private final StrikeReturn origin;
    private final Map<UUID, R> runs = new LinkedHashMap<>();
    private final Map<UUID, ServerPlayer> pendingRestore = new HashMap<>();
    private MinecraftServer server;
    private StrikeInstances instances;
    private CompletableFuture<Void> maps;
    private boolean installed;

    /**
     * @param returnAttachmentId persistent id of the origin record; stable across versions
     * @param strikeCleanup      strike-specific teardown of one player's presentation (music, HUD, cameras of its own)
     */
    public StrikeHost(String logTag, String resourcePack, String returnAttachmentId, int minPlayers, int maxPlayers,
                      Function<MinecraftServer, StrikeInstances> instanceFactory,
                      Function<MinecraftServer, CompletableFuture<Void>> mapLoader,
                      RunFactory<R> runFactory, Consumer<ServerPlayer> strikeCleanup) {
        this.logTag = Objects.requireNonNull(logTag);
        this.resourcePack = Objects.requireNonNull(resourcePack);
        this.minPlayers = minPlayers; this.maxPlayers = maxPlayers;
        this.instanceFactory = Objects.requireNonNull(instanceFactory);
        this.mapLoader = Objects.requireNonNull(mapLoader);
        this.runFactory = Objects.requireNonNull(runFactory);
        this.strikeCleanup = Objects.requireNonNull(strikeCleanup);
        this.origin = new StrikeReturn(returnAttachmentId, logTag, this::isLevel);
    }

    /** Registers lifecycle, tick, connection and world-protection hooks. Idempotent. */
    public void install() {
        if (installed) return;
        installed = true;
        ServerLifecycleEvents.SERVER_STARTED.register(s -> { server = s; instances = instanceFactory.apply(s); maps = mapLoader.apply(s); });
        ServerLifecycleEvents.SERVER_STOPPING.register(s -> {
            for (var run : List.copyOf(runs.values())) run.stop("서버 종료");
            for (var run : List.copyOf(runs.values())) run.drain();
            runs.clear();
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(s -> { server = null; instances = null; });
        ServerTickEvents.END_SERVER_TICK.register(this::tick);
        ServerPlayConnectionEvents.DISCONNECT.register((handler, s) -> {
            var run = run(handler.getPlayer());
            if (run != null) run.disconnected(handler.getPlayer(), s.getTickCount());
        });
        ServerPlayConnectionEvents.JOIN.register((handler, sender, s) -> {
            var player = handler.getPlayer(); var run = run(player);
            // JOIN fires inside placeNewPlayer before the level registers the player. Teleporting here
            // registers one ServerPlayer in two levels (duplicate UUID, broken chunk tracking). Defer.
            if (run == null || !run.rejoin(player, s.getTickCount())) pendingRestore.put(player.getUUID(), player);
            else acquirePack(player, run);
        });
        GuardianDown.register((p, source) -> { var run = run(p); return run == null ? null : run.downed(p); });
        net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) ->
                !(entity instanceof ServerPlayer p) || !isLevel(p.level()) || allows(p));
        net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents.BEFORE.register((level, player, pos, block, entity) -> !isLevel(level));
        net.fabricmc.fabric.api.event.player.UseBlockCallback.EVENT.register((player, level, hand, hit) ->
                isLevel(level) && !kim.biryeong.destiny.weapon.WeaponItems.entry(player.getItemInHand(hand)).isPresent()
                        ? net.minecraft.world.InteractionResult.FAIL : net.minecraft.world.InteractionResult.PASS);
        net.fabricmc.fabric.api.event.player.AttackEntityCallback.EVENT.register((player, level, hand, entity, hit) ->
                player instanceof ServerPlayer p && !allows(p) ? net.minecraft.world.InteractionResult.FAIL : net.minecraft.world.InteractionResult.PASS);
    }

    public MinecraftServer server() { return server; }
    public List<R> runs() { return List.copyOf(runs.values()); }

    /** Null when {@link #start} would accept these players now. Read-only (the finder calls it every second). */
    public String check(List<ServerPlayer> players) {
        if (server == null || !server.isSameThread()) return "서버에서 다시 시도하세요.";
        if (players.isEmpty() || players.size() > maxPlayers || players.size() < minPlayers
                || players.stream().map(ServerPlayer::getUUID).distinct().count() != players.size())
            return minPlayers == maxPlayers ? "서로 다른 접속 플레이어 " + minPlayers + "명이 필요합니다."
                    : "서로 다른 접속 플레이어 " + minPlayers + "~" + maxPlayers + "명이 필요합니다.";
        if (maps == null || !maps.isDone()) return "공격전 맵을 준비 중입니다.";
        if (maps.isCompletedExceptionally()) return "공격전 맵을 읽지 못했습니다.";
        for (var p : players) {
            if (server.getPlayerList().getPlayer(p.getUUID()) != p || p.hasDisconnected() || !p.isAlive()
                    || p.isSpectator() || p.isCreative() || !p.connection.hasClientLoaded() || !MusicPacks.ready(p))
                return p.getGameProfile().name() + " 님의 생존 상태와 리소스 팩 로드가 필요합니다.";
            if (Strikes.participating(p) || RisingCampaign.participating(p) || Tutorial.active(p)
                    || CrucibleRuntime.participating(p) || AbilityService.inSuper(p) || GuardianDown.active(p))
                return p.getGameProfile().name() + " 님이 다른 활동 또는 궁극기 사용 중입니다.";
        }
        return null;
    }
    /** Null on success, otherwise a Korean reason. */
    public String start(List<ServerPlayer> players) {
        String error = check(players);
        if (error != null) return error;
        for (var p : players)
            if (origin.pending(p) && !restore(p)) return "이전 공격전 복귀를 먼저 완료해야 합니다.";
        var instance = instances.prepare(players.stream().map(ServerPlayer::getUUID).toList());
        if (instance.isEmpty()) return "공격전 인스턴스 준비가 진행 중이거나 정원이 가득 찼습니다.";
        R run = null;
        try {
            run = runFactory.create(server, instances, instance.get(), players);
            runs.put(instance.get().id(), run);
            for (var player : players) acquirePack(player, run);
        } catch (RuntimeException e) {
            if (run != null) { run.stop("리소스 팩 입장 준비 실패"); run.drain(); runs.remove(run.id()); }
            else instances.close(instance.get());
            DestinyGuardians.LOGGER.error("[{}] session construction failed", logTag, e);
            return "공격전을 준비하지 못했습니다.";
        }
        return null;
    }

    private void tick(MinecraftServer s) {
        long deadline = System.nanoTime() + TICK_BUDGET_NANOS;
        for (var run : List.copyOf(runs.values())) {
            for (var p : List.copyOf(s.getPlayerList().getPlayers())) if (run.member(p.getUUID())) {
                String failure = ActivityPacks.failure(p, run);
                if (failure != null) {
                    if (!run.running()) { run.stop(failure); break; }
                    p.sendSystemMessage(net.minecraft.network.chat.Component.literal(failure)); run.leave(p);
                }
            }
            try { run.tick(s.getTickCount(), Math.max(0, deadline - System.nanoTime())); }
            catch (RuntimeException e) { DestinyGuardians.LOGGER.error("[{}] session failed", logTag, e); run.stop("공격전 오류"); }
            if (run.closed()) runs.remove(run.id());
        }
        for (var p : List.copyOf(pendingRestore.values())) {
            if (!placed(s, p)) { if (p.hasDisconnected()) pendingRestore.remove(p.getUUID(), p); continue; }
            pendingRestore.remove(p.getUUID(), p); restore(p);
        }
        // Persisted returns also cover a restart or expired reconnect after the temporary world was deleted.
        for (var p : s.getPlayerList().getPlayers())
            if (run(p) == null && origin.pending(p) && placed(s, p)) restore(p);
    }
    /** The exact connection's entity is fully registered in its current level. */
    private static boolean placed(MinecraftServer s, ServerPlayer p) {
        return !p.hasDisconnected() && !p.isRemoved() && s.getPlayerList().getPlayer(p.getUUID()) == p
                && p.level().getEntity(p.getId()) == p;
    }

    public R run(ServerPlayer p) {
        return runs.values().stream().filter(r -> r.member(p.getUUID()) && !r.closed()).findFirst().orElse(null);
    }
    public boolean participating(ServerPlayer p) { return run(p) != null; }
    /** Preparation progress for the launch loading screen, or -1 when this player has no run yet. */
    public float loadProgress(ServerPlayer p) {
        var r = run(p);
        if (r == null) return -1f;
        return .25f * ActivityPacks.progress(p, resourcePack) + .75f * r.loadProgress();
    }
    private void acquirePack(ServerPlayer p, R run) {
        ActivityPacks.acquire(p, resourcePack, run, () -> !run.closed() && run.member(p.getUUID()));
    }
    /** Opaque per-run identity, including preparation/admission. */
    public Object participationToken(ServerPlayer p) { return p == null ? null : run(p); }
    public boolean leave(ServerPlayer p, Object expected) {
        if (expected == null || participationToken(p) != expected) return false;
        leave(p); return true;
    }
    public void leave(ServerPlayer p) { var r = run(p); if (r != null) r.leave(p); else restore(p); }
    public boolean briefing(ServerPlayer p) {
        var r = run(p);
        return r != null && r.running() && p.level() == r.level() && r.briefing();
    }
    public boolean active(ServerPlayer p) { var r = run(p); return r != null && r.running() && p.level() == r.level(); }
    public boolean allows(ServerPlayer p) { var r = run(p); return r == null ? !isLevel(p.level()) : r.allows(p); }
    public boolean isLevel(Level level) { return runs.values().stream().anyMatch(r -> r.level() == level); }

    public void saveReturn(ServerPlayer p) { origin.save(p); }
    public boolean restore(ServerPlayer p) { return origin.restore(p, this::cleanup); }
    /** Stops everything the strike attached to the player so they can be moved or released safely. */
    public void cleanup(ServerPlayer p) {
        strikeCleanup.accept(p);
        AbilityService.cleanup(p); WeaponRuntime.cleanup(p);
        if (WeaponScreen.active(p)) WeaponScreen.close(p);
        CameraViews.stop(p); p.setCamera(p); p.stopRiding(); p.stopUsingItem(); p.closeContainer();
        p.resetFallDistance(); p.setDeltaMovement(Vec3.ZERO);
    }
}
