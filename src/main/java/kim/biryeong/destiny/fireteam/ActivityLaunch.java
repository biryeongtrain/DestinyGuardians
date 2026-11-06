package kim.biryeong.destiny.fireteam;

import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundClearTitlesPacket;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;

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
    static final int COUNTDOWN = 5 * 20, FADE_OUT = 16, BLACK_HOLD = 10, REVEAL = 24, PREPARE_TIMEOUT = 45 * 20,
            DROPPED_GRACE = 3 * 20;

    /** Titles in Noto Sans KR (the economy UI font) instead of the pixel font. */
    private static final FontDescription.Resource NOTO = new FontDescription.Resource(Identifier.fromNamespaceAndPath("destiny", "econ_text"));
    final FireteamRoster.Team team;
    final ActivityCatalog.Activity activity;
    final List<UUID> members;
    private final MinecraftServer server;
    private final Map<UUID, LaunchCurtain> curtains = new LinkedHashMap<>();
    /** Per player: tick the fade-in started, or absent while still dark. */
    private final Map<UUID, Integer> revealing = new HashMap<>();
    private Phase phase = Phase.COUNTDOWN;
    private final int started;
    private int phaseAt, launchedAt;
    private String outcome;

    ActivityLaunch(MinecraftServer server, FireteamRoster.Team team, ActivityCatalog.Activity activity) {
        this.server = server; this.team = team; this.activity = activity;
        this.members = team.members();
        this.started = this.phaseAt = server.getTickCount();
    }

    Phase phase() { return phase; }
    boolean dark(ServerPlayer p) { var c = curtains.get(p.getUUID()); return c != null && !c.released() && c.player == p; }
    /** Whole seconds left on the countdown, or -1 after it. */
    int secondsLeft() { return phase == Phase.COUNTDOWN ? Math.max(1, (COUNTDOWN - age() + 19) / 20) : -1; }
    String outcome() { return outcome; }
    private int age() { return server.getTickCount() - phaseAt; }
    private void enter(Phase p) { phase = p; phaseAt = server.getTickCount(); }

    List<ServerPlayer> online() {
        var out = new ArrayList<ServerPlayer>();
        for (var id : members) { var p = server.getPlayerList().getPlayer(id); if (p != null && !p.hasDisconnected()) out.add(p); }
        return out;
    }

    /** Leader cancel or a roster change during the countdown. Fades back in if already dark. */
    void cancel(String reason) {
        if (phase == Phase.DONE) return;
        outcome = reason;
        for (var p : online()) {
            p.connection.send(new ClientboundClearTitlesPacket(true));
            p.sendSystemMessage(Component.literal("출발 취소: " + reason).withColor(0xE0645A));
        }
        if (curtains.isEmpty()) { phase = Phase.DONE; return; }
        enter(Phase.PREPARE); launchedAt = -1;
        for (var id : curtains.keySet()) revealing.putIfAbsent(id, server.getTickCount());
    }

    void tick() {
        if (phase == Phase.DONE) return;
        int now = server.getTickCount();
        switch (phase) {
            case COUNTDOWN -> {
                var online = online();
                if (online.size() != members.size() || !team.members().equals(members)) { cancel("화력팀 구성이 바뀌었습니다."); return; }
                if (age() % 20 == 0) {
                    String error = activity.launcher().check(online);
                    if (error != null) { cancel(error); return; }
                    int left = (COUNTDOWN - age()) / 20;
                    for (var p : online) {
                        p.connection.send(new ClientboundSetTitlesAnimationPacket(0, 22, 4));
                        p.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal(activity.name() + " · 출발 준비")
                                .withStyle(s -> s.withColor(0xC9D1D8).withFont(NOTO))));
                        p.connection.send(new ClientboundSetTitleTextPacket(Component.literal(String.valueOf(left))
                                .withStyle(s -> s.withColor(0xF2F2EE).withFont(NOTO))));
                        FinderSounds.play(p, SoundEvents.NOTE_BLOCK_HAT, .7f, left <= 1 ? 1.6f : 1.2f);
                    }
                }
                if (age() >= COUNTDOWN) {
                    for (var p : online) {
                        FinderScreen.close(p);
                        var c = new LaunchCurtain(p); c.freeze(); curtains.put(p.getUUID(), c);
                        p.connection.send(new ClientboundSetTitlesAnimationPacket(10, FADE_OUT + BLACK_HOLD + 60, 20));
                        p.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal(activity.type()).withStyle(s -> s.withColor(0xA9B2BC).withFont(NOTO))));
                        p.connection.send(new ClientboundSetTitleTextPacket(Component.literal(activity.name()).withStyle(s -> s.withColor(0xF2F2EE).withFont(NOTO))));
                        FinderSounds.play(p, SoundEvents.BEACON_POWER_SELECT, .6f, 1.3f);
                    }
                    enter(Phase.FADE_OUT);
                }
            }
            case FADE_OUT -> {
                float k = Math.min(1f, (age() + 1) / (float) FADE_OUT);
                for (var c : curtains.values()) { c.level(k); if (!c.player.hasDisconnected()) c.freeze(); }
                if (age() < FADE_OUT + BLACK_HOLD) return;
                // Activity pre-processing runs only once the whole fireteam is in the dark.
                var online = online();
                String error = online.size() != members.size() ? "화력팀원이 접속을 종료했습니다." : activity.launcher().check(online);
                if (error == null) {
                    try { error = activity.launcher().launch(online); }
                    catch (RuntimeException e) { DestinyGuardians.LOGGER.error("[ActivityLaunch] {} failed", activity.id(), e); error = "활동을 시작하지 못했습니다."; }
                }
                if (error != null) { cancel(error); return; }
                DestinyGuardians.LOGGER.info("[ActivityLaunch] {} launched for {} after {} ticks", activity.id(), members.size(), now - started);
                enter(Phase.PREPARE); launchedAt = now;
            }
            case PREPARE -> {
                boolean timedOut = age() > PREPARE_TIMEOUT;
                for (var e : curtains.entrySet()) {
                    var c = e.getValue();
                    if (c.released()) continue;
                    var p = c.player;
                    if (p.hasDisconnected()) { c.release(); continue; }
                    if (!revealing.containsKey(e.getKey())) {
                        c.level(1f); c.freeze();
                        boolean entered = launchedAt >= 0 && activity.launcher().entered(p);
                        // The activity refused or ended for this player: return them to the light where they are.
                        boolean dropped = launchedAt >= 0 && now - launchedAt > DROPPED_GRACE && !activity.launcher().participating(p);
                        if (entered) c.unfreeze();
                        if ((entered && c.clientReady()) || dropped || timedOut) revealing.put(e.getKey(), now);
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
        for (var c : curtains.values()) c.release();
        phase = Phase.DONE;
    }
}
