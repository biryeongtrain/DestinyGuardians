package kim.biryeong.destiny.fireteam;

import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundClearTitlesPacket;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

import java.util.*;
import net.minecraft.network.chat.FontDescription;
import net.minecraft.resources.Identifier;

/**
 * The leader pressed 플레이: countdown → fade to black → activity pre-processing ({@link ActivityCatalog.Launcher#launch})
 * under the black → per-player fade-in as the activity takes each Guardian, into its own cinematic. Activity-agnostic:
 * every finder activity launches through this. A member leaving, disconnecting or failing the activity check during
 * the countdown cancels it; a failed launch fades everyone back in where they stand.
 */
final class ActivityLaunch {
    enum Phase { COUNTDOWN, FADE_OUT, PREPARE, DONE }
    static final int LEAD_IN = 20, COUNTDOWN = 5 * 20, LAUNCH_AT = LEAD_IN + COUNTDOWN,
            FADE_OUT = 16, FADE_START = LAUNCH_AT - FADE_OUT, REVEAL = 24, PREPARE_TIMEOUT = kim.biryeong.destiny.compat.pack.ActivityPacks.LOAD_TIMEOUT_TICKS + 45 * 20,
            DROPPED_GRACE = 3 * 20, READY_HOLD = 14;

    /** Titles in Noto Sans KR (the economy UI font) instead of the pixel font. */
    private static final FontDescription.Resource NOTO = new FontDescription.Resource(Identifier.fromNamespaceAndPath("destiny", "econ_text"));
    final FireteamRoster.Team team;
    final ActivityCatalog.Activity activity;
    final List<UUID> members;
    private final MinecraftServer server;
    private final Map<UUID, LaunchCurtain> curtains = new LinkedHashMap<>();
    /** Per player: tick the fade-in started, or absent while still dark. */
    private final Map<UUID, Integer> revealing = new HashMap<>();
    /** Per player: the loading screen drawn over the black while the activity prepares. */
    private final Map<UUID, LaunchLoadingScreen> screens = new HashMap<>();
    /** Per player: tick the destination was confirmed loaded; the bar rests at 100% for {@link #READY_HOLD} before the fade-in. */
    private final Map<UUID, Integer> loaded = new HashMap<>();
    private Phase phase = Phase.COUNTDOWN;
    private final int started;
    private int phaseAt, launchedAt;
    private String outcome;
    private boolean accepted, launchInvoked;
    private int shownNumber;
    private record Bound(ServerPlayer player, net.minecraft.server.network.ServerGamePacketListenerImpl connection,
                         net.minecraft.server.level.ServerLevel level) { }
    private final Map<UUID, Bound> acceptedPlayers = new LinkedHashMap<>();
    private final Map<UUID, Object> preparationTokens = new HashMap<>();
    private final List<FinderSounds.Countdown> countdownAudio = new ArrayList<>();

    ActivityLaunch(MinecraftServer server, FireteamRoster.Team team, ActivityCatalog.Activity activity,
                   List<ServerPlayer> players) {
        this.server = server; this.team = team; this.activity = activity;
        this.members = team.members();
        this.started = this.phaseAt = server.getTickCount();
        for (var p : players) acceptedPlayers.put(p.getUUID(), new Bound(p, p.connection, p.level()));
        if (!acceptedPlayers.keySet().equals(new LinkedHashSet<>(members))) throw new IllegalArgumentException("Accepted fireteam differs from launch roster");
    }

    /** Called once after the accepted launch occupies its registry slot and the director has closed. */
    void accept() {
        if (accepted || phase != Phase.COUNTDOWN) return;
        accepted = true;
        if (!validCountdown()) { cancel("화력팀 연결 상태가 바뀌었습니다."); return; }
        for (var bound : acceptedPlayers.values()) countdownAudio.add(FinderSounds.countdown(bound.player, this, started));
    }
    boolean owns(ServerPlayer p) {
        var bound = acceptedPlayers.get(p.getUUID());
        return bound != null && bound.player == p && bound.connection == p.connection;
    }
    boolean cancelable() {
        if (outcome != null || phase == Phase.DONE) return false;
        if (!launchInvoked) return phase == Phase.COUNTDOWN || phase == Phase.FADE_OUT;
        return phase == Phase.PREPARE && loaded.isEmpty() && revealing.isEmpty()
                && activity.launcher().canCancelPreparation(online(), preparationTokens);
    }
    /** No number during the click's first second, then5..1 on exact20tick boundaries; never0. */
    static int numberAt(int elapsed) { return elapsed < LEAD_IN || elapsed >= LAUNCH_AT ? 0 : 6 - elapsed / 20; }
    private boolean validCountdown() {
        if (!team.members().equals(members) || !team.activity().equals(activity.id())) return false;
        for (var bound : acceptedPlayers.values()) {
            var p = bound.player;
            if (server.getPlayerList().getPlayer(p.getUUID()) != p || p.connection != bound.connection
                    || p.hasDisconnected() || p.isRemoved() || !p.isAlive() || p.level() != bound.level) return false;
        }
        return true;
    }

    Phase phase() { return phase; }
    boolean dark(ServerPlayer p) { var c = curtains.get(p.getUUID()); return c != null && !c.released() && c.player == p; }
    /** Whole seconds left on the countdown, or -1 after it. */
    int secondsLeft() { return cancelable() ? numberAt(server.getTickCount() - started) : -1; }
    String outcome() { return outcome; }
    private int age() { return server.getTickCount() - phaseAt; }
    private void enter(Phase p) { phase = p; phaseAt = server.getTickCount(); }

    List<ServerPlayer> online() {
        var out = new ArrayList<ServerPlayer>();
        for (var bound : acceptedPlayers.values()) {
            var p = bound.player;
            if (server.getPlayerList().getPlayer(p.getUUID()) == p && p.connection == bound.connection && !p.hasDisconnected()) out.add(p);
        }
        return out;
    }

    /** Leader cancel or a roster change during the countdown. Fades back in if already dark. */
    void cancel(String reason) {
        if (phase == Phase.DONE || outcome != null) return;
        if (launchInvoked) {
            if (!cancelable()) return;
            activity.launcher().cancelPreparation(online(), preparationTokens);
            launchInvoked = false;
        }
        outcome = reason;
        for (var sound : countdownAudio) sound.cancel(this);
        for (var p : online()) {
            p.connection.send(new ClientboundClearTitlesPacket(true));
            p.sendSystemMessage(Component.literal("출발 취소: " + reason).withColor(0xE0645A));
        }
        if (curtains.isEmpty()) { phase = Phase.DONE; return; }
        float darkness = phase == Phase.FADE_OUT ? Math.clamp((server.getTickCount() - started - FADE_START) / (float) FADE_OUT, 0, 1) : 1f;
        int revealAt = server.getTickCount() - (int)((1f - darkness) * REVEAL);
        enter(Phase.PREPARE); launchedAt = -1;
        for (var id : curtains.keySet()) revealing.putIfAbsent(id, revealAt);
    }

    void tick() {
        if (!accepted || phase == Phase.DONE) return;
        int now = server.getTickCount();
        switch (phase) {
            case COUNTDOWN, FADE_OUT -> {
                if (!validCountdown()) { cancel("화력팀 구성이 바뀌었습니다."); return; }
                int elapsed = now - started;
                var online = online();
                if (elapsed % 20 == 0) {
                    String error = activity.launcher().check(online);
                    if (error != null) { cancel(error); return; }
                }
                int left = numberAt(elapsed);
                if (left > 0 && left != shownNumber) {
                    shownNumber = left;
                    for (var p : online) {
                        p.connection.send(new ClientboundSetTitlesAnimationPacket(0, 20, 0));
                        p.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal(activity.name() + " · 출발 준비")
                                .withStyle(s -> s.withColor(0xC9D1D8).withFont(NOTO))));
                        p.connection.send(new ClientboundSetTitleTextPacket(Component.literal(String.valueOf(left))
                                .withStyle(s -> s.withColor(0xF2F2EE).withFont(NOTO))));
                    }
                }
                // Fade only in the final16ticks of1, with no extra delay after the requested6second timeline.
                if (elapsed >= FADE_START) {
                    if (curtains.isEmpty()) for (var p : online) {
                        FinderScreen.close(p); var curtain = new LaunchCurtain(p);
                        curtain.freeze(); curtains.put(p.getUUID(), curtain);
                    }
                    phase = Phase.FADE_OUT;
                    float darkness = Math.clamp((elapsed - FADE_START) / (float) FADE_OUT, 0, 1);
                    for (var curtain : curtains.values()) { curtain.level(darkness); curtain.freeze(); }
                }
                if (elapsed < LAUNCH_AT) return;
                // Enter a non-launching phase BEFORE calling external code: reentrant/duplicate ticks cannot launch twice.
                launchInvoked = true; enter(Phase.PREPARE); launchedAt = now;
                String error;
                try { error = activity.launcher().launch(online); }
                catch (RuntimeException e) { DestinyGuardians.LOGGER.error("[ActivityLaunch] {} failed", activity.id(), e); error = "활동을 시작하지 못했습니다."; }
                if (error != null) {
                    launchInvoked = false; cancel(error); return;
                }
                for (var p : online) preparationTokens.put(p.getUUID(), activity.launcher().preparationToken(p));
                // Success keeps the original cue's remaining~0.34seconds; no sound-stop at the launch boundary.
                // The title that follows is the loading screen (drawn each tick under the black), not a one-off card.
                for (var p : online) p.connection.send(new ClientboundClearTitlesPacket(true));
                DestinyGuardians.LOGGER.info("[ActivityLaunch] {} launched for {} after {} ticks", activity.id(), members.size(), elapsed);
            }
            case PREPARE -> {
                boolean timedOut = age() > PREPARE_TIMEOUT;
                for (var e : curtains.entrySet()) {
                    var c = e.getValue();
                    if (c.released()) continue;
                    var p = c.player;
                    if (!owns(p) || server.getPlayerList().getPlayer(p.getUUID()) != p || p.hasDisconnected()) { c.release(); screens.remove(e.getKey()); continue; }
                    if (!revealing.containsKey(e.getKey())) {
                        c.level(1f); c.freeze();
                        boolean entered = launchedAt >= 0 && activity.launcher().entered(p);
                        // The activity refused or ended for this player: return them to the light where they are.
                        boolean dropped = launchedAt >= 0 && now - launchedAt > DROPPED_GRACE && !activity.launcher().participating(p);
                        if (entered) c.unfreeze();
                        // clientReady() counts calm ticks, so it is polled every tick until the destination is confirmed.
                        if (entered && !loaded.containsKey(e.getKey()) && c.clientReady()) loaded.put(e.getKey(), now);
                        boolean ready = loaded.containsKey(e.getKey());
                        if (launchedAt >= 0 && !dropped && !timedOut) {
                            var screen = screens.computeIfAbsent(e.getKey(), k -> new LaunchLoadingScreen(p, activity.name(), activity.type()));
                            screen.render(now - launchedAt, activity.launcher().progress(p), ready,
                                    kim.biryeong.destiny.compat.pack.ActivityPacks.loadingStatus(p, activity.id()));
                        }
                        if (ready && now - loaded.get(e.getKey()) >= READY_HOLD || dropped || timedOut) {
                            revealing.put(e.getKey(), now);
                            var screen = screens.get(e.getKey());
                            if (screen != null) { if (dropped || timedOut) screen.clear(); else screen.fadeOut(REVEAL); }
                        }
                        continue;
                    }
                    int t = now - revealing.get(e.getKey());
                    c.level(1f - t / (float) REVEAL);
                    if (t >= REVEAL) c.release();
                }
                if (curtains.values().stream().allMatch(LaunchCurtain::released)) {
                    if (outcome == null) outcome = "launched";
                    phase = Phase.DONE;
                }
            }
            case DONE -> { }
        }
    }

    /** Server stop or forced cleanup: no layer may outlive the launch. */
    void abort() {
        if (cancelable() && shownNumber > 0) for (var p : online()) p.connection.send(new ClientboundClearTitlesPacket(true));
        for (var sound : countdownAudio) sound.cancel(this);
        for (var screen : screens.values()) screen.clear();
        screens.clear();
        for (var c : curtains.values()) c.release();
        phase = Phase.DONE;
    }
}
