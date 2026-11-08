package kim.biryeong.destiny.strike.devils;

import com.mojang.serialization.Codec;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.campaign.RisingCampaign;
import kim.biryeong.destiny.crucible.CrucibleRuntime;
import kim.biryeong.destiny.down.GuardianDown;
import kim.biryeong.destiny.inventory.WeaponScreen;
import kim.biryeong.destiny.tutorial.Tutorial;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import kim.biryeong.minigamelib.music.MusicPacks;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import java.util.concurrent.CompletableFuture;

/** Live one-to-three-player coordinator with fixed three-player encounter tuning. The sole owner of world construction and participant admission. */
public final class DevilsLair {
    private static final AttachmentType<String> RETURN = AttachmentRegistry.create(
            DestinyGuardians.id("devils_return"), b -> b.persistent(Codec.STRING).copyOnDeath());
    private static final Map<UUID, DevilsSession> SESSIONS = new LinkedHashMap<>();
    private static MinecraftServer server;
    private static DevilsInstances instances;
    private static CompletableFuture<Void> maps;
    private static boolean initialized;

    /** Presentation is installed by the integration layer; only a normal intro completion may release the boss. */
    public interface Presentation extends AutoCloseable {
        default void tick(DevilsSession session, boolean paused) { }
        default void phase(DevilsSession session, DevilsDirector.Snapshot snapshot) { }
        default void incoming(DevilsSession session, long generation, List<DevilsPlan.Slot> slots, int ticks) { }
        /** Observation after entity, model and multipart insertion succeed; never a spawn authorization. */
        default void spawned(DevilsSession session, DevilsDirector.Spawn spawn, net.minecraft.world.phys.Vec3 at) { }
        default void spawnTelegraph(DevilsSession session, long generation, String slot, net.minecraft.world.phys.Vec3 at, boolean flying) { }
        default void cancelSpawnTelegraph(long generation, String slot) { }
        default void cancelGeneration(long generation) { }
        default void disconnected(ServerPlayer player) { }
        default boolean hidden(ServerPlayer player) { return false; }
        @Override default void close() { }
    }
    private static java.util.function.Function<DevilsSession, Presentation> presentationFactory = s -> new Presentation() { };
    public static void presentation(java.util.function.Function<DevilsSession, Presentation> factory) {
        presentationFactory = Objects.requireNonNull(factory);
    }
    static Presentation presentationFor(DevilsSession session) { return Objects.requireNonNull(presentationFactory.apply(session)); }
    private DevilsLair() { }

    public static void init() {
        if (initialized) return;
        initialized = true;
        presentation(kim.biryeong.destiny.campaign.presentation.DevilsPresentation::new);
        var combatHidden = kim.biryeong.destiny.hud.CombatHud.cinematic;
        kim.biryeong.destiny.hud.CombatHud.cinematic = combatHidden.or(
                kim.biryeong.destiny.campaign.presentation.DevilsPresentation::hudHidden);
        var weaponHidden = kim.biryeong.destiny.weapon.ProfileWeaponView.suppressed;
        kim.biryeong.destiny.weapon.ProfileWeaponView.suppressed = weaponHidden.or(
                kim.biryeong.destiny.campaign.presentation.DevilsPresentation::hudHidden);
        DevilsActors.init();
        ServerLifecycleEvents.SERVER_STARTED.register(s -> {
            server = s; instances = new DevilsInstances(s, 4); maps = DevilsMaps.preloadAsync(s);
        });
        ServerLifecycleEvents.SERVER_STOPPING.register(s -> {
            for (var session : List.copyOf(SESSIONS.values())) session.stop("서버 종료");
            for (var session : List.copyOf(SESSIONS.values())) session.drain();
            SESSIONS.clear();
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(s -> { server = null; instances = null; });
        ServerTickEvents.END_SERVER_TICK.register(DevilsLair::tick);
        ServerPlayConnectionEvents.DISCONNECT.register((handler, s) -> {
            var session = session(handler.getPlayer());
            if (session != null) session.disconnected(handler.getPlayer(), s.getTickCount());
        });
        ServerPlayConnectionEvents.JOIN.register((handler, sender, s) -> {
            var player = handler.getPlayer(); var session = session(player);
            // JOIN fires inside placeNewPlayer before the level registers the player. Teleporting here
            // registers one ServerPlayer in two levels (duplicate UUID, broken chunk tracking). Defer.
            if (session == null || !session.rejoin(player, s.getTickCount())) PENDING_RESTORE.put(player.getUUID(), player);
        });
        GuardianDown.register((p, source) -> { var s = session(p); return s == null ? null : s.downed(p); });
        net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) ->
                !(entity instanceof ServerPlayer p) || !isLevel(p.level()) || allows(p));
        net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents.BEFORE.register((level, player, pos, block, entity) -> !isLevel(level));
        net.fabricmc.fabric.api.event.player.UseBlockCallback.EVENT.register((player, level, hand, hit) ->
                isLevel(level) && !kim.biryeong.destiny.weapon.WeaponItems.entry(player.getItemInHand(hand)).isPresent()
                        ? net.minecraft.world.InteractionResult.FAIL : net.minecraft.world.InteractionResult.PASS);
        net.fabricmc.fabric.api.event.player.AttackEntityCallback.EVENT.register((player, level, hand, entity, hit) ->
                player instanceof ServerPlayer p && !allows(p) ? net.minecraft.world.InteractionResult.FAIL : net.minecraft.world.InteractionResult.PASS);

        CommandRegistrationCallback.EVENT.register((dispatcher, access, environment) -> dispatcher.register(
                Commands.literal("destiny").then(Commands.literal("devils")
                        .then(Commands.literal("start").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .executes(c -> startCommand(c.getSource(), List.of(c.getSource().getPlayerOrException())))
                                .then(Commands.argument("players", EntityArgument.players()).executes(c -> {
                                    return startCommand(c.getSource(), List.copyOf(EntityArgument.getPlayers(c, "players")));
                                })))
                        .then(Commands.literal("qa_complete").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .then(Commands.argument("player", EntityArgument.player()).executes(c -> {
                                    var s = session(EntityArgument.getPlayer(c, "player"));
                                    if (s == null) { c.getSource().sendFailure(Component.literal("공격전 참가 중이 아닙니다.")); return 0; }
                                    s.qaComplete(); return 1;
                                })))
                        .then(Commands.literal("qa_restriction").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .executes(c -> qaFailure(c.getSource(), c.getSource().getPlayerOrException(), "restriction"))
                                .then(Commands.argument("player", EntityArgument.player()).executes(c ->
                                        qaFailure(c.getSource(), EntityArgument.getPlayer(c, "player"), "restriction"))))
                        .then(Commands.literal("qa_wipe").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .executes(c -> qaFailure(c.getSource(), c.getSource().getPlayerOrException(), "wipe"))
                                .then(Commands.argument("player", EntityArgument.player()).executes(c ->
                                        qaFailure(c.getSource(), EntityArgument.getPlayer(c, "player"), "wipe"))))
                        .then(Commands.literal("qa_failure_status").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .executes(c -> qaFailure(c.getSource(), c.getSource().getPlayerOrException(), "status"))
                                .then(Commands.argument("player", EntityArgument.player()).executes(c ->
                                        qaFailure(c.getSource(), EntityArgument.getPlayer(c, "player"), "status"))))
                        .then(Commands.literal("qa_stats_target").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .executes(c -> qaFailure(c.getSource(), c.getSource().getPlayerOrException(), "stats_target"))
                                .then(Commands.argument("player", EntityArgument.player()).executes(c ->
                                        qaFailure(c.getSource(), EntityArgument.getPlayer(c, "player"), "stats_target"))))
                        .then(Commands.literal("leave").executes(c -> { leave(c.getSource().getPlayerOrException()); return 1; }))
                        .then(Commands.literal("status").executes(c -> {
                            var s = session(c.getSource().getPlayerOrException());
                            c.getSource().sendSuccess(() -> Component.literal(s == null ? "공격전 참가 중이 아닙니다." : s.status()), false); return 1;
                        })))));
    }
    private static int qaFailure(net.minecraft.commands.CommandSourceStack source, ServerPlayer player, String action) {
        var s = session(player);
        if (s == null) { source.sendFailure(Component.literal("공격전 참가 중이 아닙니다.")); return 0; }
        if (action.equals("status")) {
            source.sendSuccess(() -> Component.literal(s.failureStatus()), false); return 1;
        }
        boolean success = switch (action) {
            case "restriction" -> s.qaRestriction(); case "stats_target" -> s.qaStatsTarget(player); default -> s.qaWipe();
        };
        if (!success) { source.sendFailure(Component.literal("활동/팩 준비 또는 제한 구역 상태를 확인하세요.")); return 0; }
        source.sendSuccess(() -> Component.literal(s.failureStatus()), false); return 1;
    }

    private static int startCommand(net.minecraft.commands.CommandSourceStack source, List<ServerPlayer> players) {
        String error = start(players);
        if (error != null) { source.sendFailure(Component.literal(error)); return 0; }
        source.sendSuccess(() -> Component.literal("악마의 소굴: " + players.size() + "인 입장 준비 중 · 전투 난이도는 3인 기준 고정"), true);
        return 1;
    }
    /** Null when {@link #start} would accept these players now. Read-only (the finder calls it every second). */
    public static String check(List<ServerPlayer> players) {
        if (server == null || !server.isSameThread()) return "서버에서 다시 시도하세요.";
        if (players.isEmpty() || players.size() > 3 || players.stream().map(ServerPlayer::getUUID).distinct().count() != players.size())
            return "서로 다른 접속 플레이어 1~3명이 필요합니다.";
        if (maps == null || !maps.isDone()) return "공격전 맵을 준비 중입니다.";
        if (maps.isCompletedExceptionally()) return "공격전 맵을 읽지 못했습니다.";
        for (var p : players) {
            if (server.getPlayerList().getPlayer(p.getUUID()) != p || p.hasDisconnected() || !p.isAlive()
                    || p.isSpectator() || p.isCreative() || !p.connection.hasClientLoaded() || !MusicPacks.ready(p))
                return p.getGameProfile().name() + " 님의 생존 상태와 리소스 팩 로드가 필요합니다.";
            if (participating(p) || RisingCampaign.participating(p) || Tutorial.active(p)
                    || CrucibleRuntime.participating(p) || AbilityService.inSuper(p) || GuardianDown.active(p))
                return p.getGameProfile().name() + " 님이 다른 활동 또는 궁극기 사용 중입니다.";
        }
        return null;
    }
    /** The strike has placed this player in its world and the run (briefing first) is live. */
    public static boolean entered(ServerPlayer p) { return active(p); }

    public static String start(List<ServerPlayer> players) {
        if (server == null || !server.isSameThread()) return "서버에서 다시 시도하세요.";
        if (players.isEmpty() || players.size() > 3 || players.stream().map(ServerPlayer::getUUID).distinct().count() != players.size())
            return "서로 다른 접속 플레이어 1~3명이 필요합니다.";
        if (maps == null || !maps.isDone()) return "공격전 맵을 준비 중입니다.";
        if (maps.isCompletedExceptionally()) return "공격전 맵을 읽지 못했습니다.";
        for (var p : players) {
            if (server.getPlayerList().getPlayer(p.getUUID()) != p || p.hasDisconnected() || !p.isAlive()
                    || p.isSpectator() || p.isCreative() || !p.connection.hasClientLoaded() || !MusicPacks.ready(p))
                return "참가자 모두 생존 상태와 리소스 팩 로드가 필요합니다.";
            if (participating(p) || RisingCampaign.participating(p) || Tutorial.active(p)
                    || CrucibleRuntime.participating(p) || AbilityService.inSuper(p) || GuardianDown.active(p))
                return "다른 활동 또는 궁극기 사용을 마친 뒤 시작하세요.";
            if (p.getAttached(RETURN) != null && !restore(p)) return "이전 공격전 복귀를 먼저 완료해야 합니다.";
        }
        var instance = instances.prepare(players.stream().map(ServerPlayer::getUUID).toList());
        if (instance.isEmpty()) return "공격전 인스턴스 준비가 진행 중이거나 정원이 가득 찼습니다.";
        try {
            var session = new DevilsSession(server, instances, instance.get(), players);
            SESSIONS.put(instance.get().id(), session);
        } catch (RuntimeException e) {
            instances.close(instance.get());
            DestinyGuardians.LOGGER.error("[DevilsLair] session construction failed", e);
            return "공격전을 준비하지 못했습니다.";
        }
        return null;
    }
    private static void tick(MinecraftServer s) {
        long deadline = System.nanoTime() + 2_000_000L;
        for (var session : List.copyOf(SESSIONS.values())) {
            try { session.tick(s.getTickCount(), Math.max(0, deadline - System.nanoTime())); }
            catch (RuntimeException e) { DestinyGuardians.LOGGER.error("[DevilsLair] session failed", e); session.stop("공격전 오류"); }
            if (session.closed()) SESSIONS.remove(session.id());
        }
        for (var p : List.copyOf(PENDING_RESTORE.values())) {
            if (!placed(s, p)) { if (p.hasDisconnected()) PENDING_RESTORE.remove(p.getUUID(), p); continue; }
            PENDING_RESTORE.remove(p.getUUID(), p); restore(p);
        }
        // Persisted returns also cover a restart or expired reconnect after the temporary world was deleted.
        for (var p : s.getPlayerList().getPlayers())
            if (session(p) == null && p.getAttached(RETURN) != null && placed(s, p)) restore(p);
    }
    private static final java.util.Map<java.util.UUID, ServerPlayer> PENDING_RESTORE = new java.util.HashMap<>();
    /** The exact connection's entity is fully registered in its current level. */
    private static boolean placed(MinecraftServer s, ServerPlayer p) {
        return !p.hasDisconnected() && !p.isRemoved() && s.getPlayerList().getPlayer(p.getUUID()) == p
                && p.level().getEntity(p.getId()) == p;
    }
    static DevilsSession session(ServerPlayer p) {
        return SESSIONS.values().stream().filter(s -> s.member(p.getUUID()) && !s.closed()).findFirst().orElse(null);
    }
    public static boolean participating(ServerPlayer p) { return session(p) != null; }
    /** Preparation progress for the launch loading screen, or -1 when this player has no run yet. */
    public static float loadProgress(ServerPlayer p) { var s = session(p); return s == null ? -1f : s.loadProgress(); }
    /** Opaque per-run identity, including preparation/admission. */
    public static Object participationToken(ServerPlayer p) { return p == null ? null : session(p); }
    public static boolean leave(ServerPlayer p, Object expected) {
        if (expected == null || participationToken(p) != expected) return false;
        leave(p); return true;
    }
    public static boolean briefing(ServerPlayer p) {
        var s = session(p);
        return s != null && s.running() && p.level() == s.level()
                && s.director().phase() == DevilsDirector.Phase.BRIEFING;
    }
    public static boolean active(ServerPlayer p) { var s = session(p); return s != null && s.running() && p.level() == s.level(); }
    public static boolean allows(ServerPlayer p) { var s = session(p); return s == null ? !isLevel(p.level()) : s.allows(p); }
    public static boolean isLevel(Level level) { return SESSIONS.values().stream().anyMatch(s -> s.level() == level); }
    public static void leave(ServerPlayer p) { var s = session(p); if (s != null) s.leave(p); else restore(p); }

    static void saveReturn(ServerPlayer p) {
        if (p.getAttached(RETURN) != null) return;
        p.setAttached(RETURN, String.join("|", p.level().dimension().identifier().toString(),
                Double.toString(p.getX()), Double.toString(p.getY()), Double.toString(p.getZ()),
                Float.toString(p.getYRot()), Float.toString(p.getXRot()), p.gameMode.getGameModeForPlayer().getName()));
    }
    static boolean restore(ServerPlayer p) {
        String saved = p.getAttached(RETURN); if (saved == null) return true;
        if (p.hasDisconnected()) return false;
        cleanup(p);
        try {
            String[] a = saved.split("\\|", -1);
            ServerLevel target = p.level().getServer().getLevel(ResourceKey.create(Registries.DIMENSION, Identifier.parse(a[0])));
            if (target == null || isLevel(target)) target = p.level().getServer().overworld();
            Vec3 at = new Vec3(Double.parseDouble(a[1]), Double.parseDouble(a[2]), Double.parseDouble(a[3]));
            if (target == p.level().getServer().overworld() && !target.dimension().identifier().toString().equals(a[0]))
                at = Vec3.atBottomCenterOf(target.getRespawnData().pos());
            if (!Double.isFinite(at.x) || !Double.isFinite(at.y) || !Double.isFinite(at.z)) return false;
            if (!p.teleportTo(target, at.x, at.y, at.z, Set.of(), Float.parseFloat(a[4]), Float.parseFloat(a[5]), true)) return false;
            p.setGameMode(GameType.byName(a[6], GameType.SURVIVAL));
            p.removeAttached(RETURN); return true;
        } catch (RuntimeException e) {
            DestinyGuardians.LOGGER.warn("[DevilsLair] return failed for {}", p.getUUID(), e); return false;
        }
    }
    static void cleanup(ServerPlayer p) {
        kim.biryeong.destiny.sound.ActivityMusic.devilsEnded(p);
        AbilityService.cleanup(p); WeaponRuntime.cleanup(p);
        if (WeaponScreen.active(p)) WeaponScreen.close(p);
        CameraViews.stop(p); p.setCamera(p); p.stopRiding(); p.stopUsingItem(); p.closeContainer();
        p.resetFallDistance(); p.setDeltaMovement(Vec3.ZERO);
    }
}
