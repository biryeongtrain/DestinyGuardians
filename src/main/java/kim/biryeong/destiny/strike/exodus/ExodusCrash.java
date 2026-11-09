package kim.biryeong.destiny.strike.exodus;

import kim.biryeong.destiny.activity.strike.StrikeCoordinator;
import kim.biryeong.destiny.activity.strike.StrikeHost;
import kim.biryeong.destiny.activity.strike.StrikeInstances;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;

import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * Exodus Crash: a one-to-three-player strike through one continuous map (a Vex-infested crash site below Nessus).
 * Built entirely on the shared strike seam: host, instances, maps, roster, recovery and actors.
 */
public final class ExodusCrash {
    private static final StrikeHost<ExodusSession> HOST = new StrikeHost<>("ExodusCrash", "exodus_crash", "exodus_return",
            ExodusPlan.MIN_PLAYERS, ExodusPlan.PLAYERS,
            s -> new StrikeInstances(s, "exodus_crash", 2, ExodusPlan.MIN_PLAYERS, ExodusPlan.PLAYERS,
                    () -> new ExodusTemplateGenerator(s, ExodusMaps.maps().nbtTemplates())),
            s -> ExodusMaps.maps().preloadAsync(s).thenRun(ExodusPlan::data),
            ExodusSession::new, kim.biryeong.destiny.sound.ActivityMusic::devilsEnded);

    public static final StrikeCoordinator COORDINATOR = new StrikeCoordinator() {
        private final Info info = new Info("exodus_crash", "엑소더스의 추락", "공격전 · 네소스",
                "엑소더스 블랙의 추락 지점에 진입해 벡스와 구원의 가문 부관 파이키스를 처치하세요.", "fireteam/banner_devils_lair",
                "fireteam/icon_devils_lair", ExodusPlan.MIN_PLAYERS, ExodusPlan.PLAYERS, 20);
        @Override public Info info() { return info; }
        @Override public String check(List<ServerPlayer> fireteam) { return HOST.check(fireteam); }
        @Override public String start(List<ServerPlayer> fireteam) { return HOST.start(fireteam); }
        @Override public boolean entered(ServerPlayer p) { return HOST.active(p); }
        @Override public boolean participating(ServerPlayer p) { return HOST.participating(p); }
        @Override public float loadProgress(ServerPlayer p) { return HOST.loadProgress(p); }
        @Override public Object participationToken(ServerPlayer p) { return HOST.participationToken(p); }
        @Override public boolean leave(ServerPlayer p, Object expected) { return HOST.leave(p, expected); }
        @Override public boolean briefing(ServerPlayer p) { return HOST.briefing(p); }
        @Override public boolean allows(ServerPlayer p) { return HOST.allows(p); }
        @Override public boolean isLevel(Level level) { return HOST.isLevel(level); }
    };
    private static boolean initialized;
    private ExodusCrash() { }

    public static void init() {
        if (initialized) return;
        initialized = true;
        kim.biryeong.destiny.strike.devils.DevilsActors.init();
        HOST.install();
        CommandRegistrationCallback.EVENT.register((dispatcher, access, environment) -> dispatcher.register(
                Commands.literal("destiny").then(Commands.literal("exodus")
                        .then(Commands.literal("start").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .executes(c -> start(c.getSource(), List.of(c.getSource().getPlayerOrException())))
                                .then(Commands.argument("players", EntityArgument.players())
                                        .executes(c -> start(c.getSource(), List.copyOf(EntityArgument.getPlayers(c, "players"))))))
                        .then(Commands.literal("skip").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .executes(c -> {
                                    var s = HOST.run(c.getSource().getPlayerOrException());
                                    if (s == null || !s.qaSkip()) { c.getSource().sendFailure(Component.literal("건너뛸 수 없습니다.")); return 0; }
                                    return 1;
                                }))
                        .then(Commands.literal("inspect").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .executes(c -> {
                                    var s = HOST.run(c.getSource().getPlayerOrException());
                                    c.getSource().sendSuccess(() -> Component.literal(s == null ? "공격전 참가 중이 아닙니다." : s.diagnostics()), false); return 1;
                                }))
                        .then(Commands.literal("leave").executes(c -> { HOST.leave(c.getSource().getPlayerOrException()); return 1; }))
                        .then(Commands.literal("status").executes(c -> {
                            var s = HOST.run(c.getSource().getPlayerOrException());
                            c.getSource().sendSuccess(() -> Component.literal(s == null ? "공격전 참가 중이 아닙니다." : s.status()), false); return 1;
                        })))));
    }
    private static int start(net.minecraft.commands.CommandSourceStack source, List<ServerPlayer> players) {
        String error = HOST.start(players);
        if (error != null) { source.sendFailure(Component.literal(error)); return 0; }
        source.sendSuccess(() -> Component.literal("엑소더스의 추락: " + players.size() + "인 입장 준비 중"), true);
        return 1;
    }
    static void saveReturn(ServerPlayer p) { HOST.saveReturn(p); }
    static boolean restore(ServerPlayer p) { return HOST.restore(p); }
    static void cleanup(ServerPlayer p) { HOST.cleanup(p); }
}
