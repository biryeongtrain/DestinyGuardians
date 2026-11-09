package kim.biryeong.destiny.strike.devils;

import com.mojang.serialization.Codec;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.activity.strike.StrikeCoordinator;
import kim.biryeong.destiny.activity.strike.StrikeHost;
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
    private static final StrikeHost<DevilsSession> HOST = new StrikeHost<>("DevilsLair", "devils_lair", "devils_return",
            DevilsPlan.MIN_PLAYERS, DevilsPlan.PLAYERS, s -> new DevilsInstances(s, 4), DevilsMaps::preloadAsync,
            DevilsSession::new, kim.biryeong.destiny.sound.ActivityMusic::devilsEnded);

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
    /** What the rest of the mod sees of this strike. Finder text lives here, next to the strike it describes. */
    public static final StrikeCoordinator COORDINATOR = new StrikeCoordinator() {
        private final Info info = new Info("devils_lair", "악마의 소굴", "공격전 · 우주선 발사 기지",
                "악마의 소굴로 들어가 발사 기지의 몰락자 세력을 약화시키세요.", "fireteam/banner_devils_lair",
                "fireteam/icon_devils_lair", DevilsPlan.MIN_PLAYERS, DevilsPlan.PLAYERS, 10);
        @Override public Info info() { return info; }
        @Override public String check(List<ServerPlayer> fireteam) { return DevilsLair.check(fireteam); }
        @Override public String start(List<ServerPlayer> fireteam) { return DevilsLair.start(fireteam); }
        @Override public boolean entered(ServerPlayer p) { return DevilsLair.entered(p); }
        @Override public boolean participating(ServerPlayer p) { return DevilsLair.participating(p); }
        @Override public float loadProgress(ServerPlayer p) { return DevilsLair.loadProgress(p); }
        @Override public Object participationToken(ServerPlayer p) { return DevilsLair.participationToken(p); }
        @Override public boolean leave(ServerPlayer p, Object expected) { return DevilsLair.leave(p, expected); }
        @Override public boolean briefing(ServerPlayer p) { return DevilsLair.briefing(p); }
        @Override public boolean allows(ServerPlayer p) { return DevilsLair.allows(p); }
        @Override public boolean isLevel(Level level) { return DevilsLair.isLevel(level); }
    };
    private static boolean initialized;
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
        HOST.install();

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
    public static String check(List<ServerPlayer> players) { return HOST.check(players); }
    /** The strike has placed this player in its world and the run (briefing first) is live. */
    public static boolean entered(ServerPlayer p) { return HOST.active(p); }
    public static String start(List<ServerPlayer> players) { return HOST.start(players); }
    static DevilsSession session(ServerPlayer p) { return HOST.run(p); }
    public static boolean participating(ServerPlayer p) { return HOST.participating(p); }
    /** Preparation progress for the launch loading screen, or -1 when this player has no run yet. */
    public static float loadProgress(ServerPlayer p) { return HOST.loadProgress(p); }
    /** Opaque per-run identity, including preparation/admission. */
    public static Object participationToken(ServerPlayer p) { return HOST.participationToken(p); }
    public static boolean leave(ServerPlayer p, Object expected) { return HOST.leave(p, expected); }
    public static boolean briefing(ServerPlayer p) { return HOST.briefing(p); }
    public static boolean active(ServerPlayer p) { return HOST.active(p); }
    public static boolean allows(ServerPlayer p) { return HOST.allows(p); }
    public static boolean isLevel(Level level) { return HOST.isLevel(level); }
    public static void leave(ServerPlayer p) { HOST.leave(p); }
    static void saveReturn(ServerPlayer p) { HOST.saveReturn(p); }
    static boolean restore(ServerPlayer p) { return HOST.restore(p); }
    static void cleanup(ServerPlayer p) { HOST.cleanup(p); }
}
