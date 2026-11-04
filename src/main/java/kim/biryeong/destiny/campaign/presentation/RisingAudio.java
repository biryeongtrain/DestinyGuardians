package kim.biryeong.destiny.campaign.presentation;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.campaign.RisingServices;
import net.minecraft.core.Holder;
import net.minecraft.network.protocol.game.ClientboundSoundEntityPacket;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.network.protocol.game.ClientboundStopSoundPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.phys.Vec3;

import java.util.*;

/**
 * Owner-private Guardian Rises audio: a per-player Ghost voice queue (lines never stack), one-shot
 * SFX and the Cosmodrome ambience loop. Voice follows the listener (entity sound on the player) so
 * sprinting or teleports never leave a line behind. All calls on the server thread.
 */
final class RisingAudio {
    /** Lines waiting behind the current one. Older queued lines are dropped first so speech stays current. */
    static final int MAX_QUEUED = 12; // W301: was 3 — the wake-up monologue alone queues 8 lines
    /** Breath between consecutive lines. */
    static final int GAP_TICKS = 6;
    static final String[] SFX = {"scan_loop", "revive", "ship_power", "ship_takeoff", "transmat", "ambient_cosmodrome"};
    private static final int AMBIENT_TICKS = 480; // ambient_cosmodrome.ogg is a 24.0 s seamless loop

    private static final class State {
        final ServerPlayer player;
        final ArrayDeque<RisingSubtitles.Line> queue = new ArrayDeque<>();
        RisingSubtitles.Line current;
        int endsAt;
        int ambientNext = -1;
        State(ServerPlayer player) { this.player = player; }
    }

    private static final Map<UUID, State> STATES = new HashMap<>();
    private static final Set<String> WARNED = new HashSet<>();

    private RisingAudio() {}

    private static State state(ServerPlayer p) {
        var s = STATES.get(p.getUUID());
        if (s == null || s.player != p) {
            if (s != null) stop(s);
            s = new State(p);
            STATES.put(p.getUUID(), s);
        }
        return s;
    }

    private static int now(ServerPlayer p) { return p.level().getServer().getTickCount(); }

    /**
     * Queues a Ghost line. Returns the ticks until that line has finished speaking (queue wait included),
     * so a caller can schedule after it; 0 when the id is unknown or the player cannot hear it.
     */
    static int voice(ServerPlayer p, String lineId) {
        if (p.hasDisconnected()) return 0;
        var line = RisingSubtitles.line(lineId).orElse(null);
        if (line == null) {
            if (WARNED.add(String.valueOf(lineId)))
                DestinyGuardians.LOGGER.warn("Guardian Rises: unknown voice line {}", lineId);
            return 0;
        }
        var s = state(p);
        int now = now(p);
        if (s.current != null && s.current.id().equals(line.id()) && now < s.endsAt) return s.endsAt - now;
        if (s.queue.stream().anyMatch(l -> l.id().equals(line.id()))) return finishOf(s, line, now);
        if (s.queue.isEmpty() && (s.current == null || now >= s.endsAt)) {
            start(s, line, now);
            return line.ticks();
        }
        while (s.queue.size() >= MAX_QUEUED) s.queue.pollFirst();
        s.queue.addLast(line);
        return finishOf(s, line, now);
    }

    private static int finishOf(State s, RisingSubtitles.Line target, int now) {
        int t = Math.max(0, s.endsAt - now);
        for (var l : s.queue) {
            t += GAP_TICKS + l.ticks();
            if (l == target) return t;
        }
        return t;
    }

    /** Id of the line currently being spoken, or null. */
    static String current(ServerPlayer p) {
        var s = STATES.get(p.getUUID());
        return s != null && s.player == p && s.current != null && now(p) < s.endsAt ? s.current.id() : null;
    }

    /** True while a line is audible or waiting. */
    static boolean speaking(ServerPlayer p) {
        var s = STATES.get(p.getUUID());
        return s != null && s.player == p && (s.current != null && now(p) < s.endsAt || !s.queue.isEmpty());
    }

    private static void start(State s, RisingSubtitles.Line line, int now) {
        var p = s.player;
        if (s.current != null && s.current.voice()) stopSound(p, voiceId(s.current.id()));
        s.current = line;
        s.endsAt = now + line.ticks();
        DestinyGuardians.LOGGER.info("[GuardianRises] voice {} ({} ticks, {} queued)", line.id(), line.ticks(), s.queue.size());
        if (line.voice()) followSound(p, voiceId(line.id()), 1f, 1f);
        RisingSubtitles.show(p, line, s.endsAt + 8, RisingPresentation.cinematic(p));
        GhostCompanion.existing(p).ifPresent(g -> {
            g.speak(s.endsAt);
            // "사라진 거 아니니까 걱정하지 마세요": the cinematic hands the Ghost back to the shoulder, then it transmats into its Guardian.
        });
    }

    static void tick(int now) {
        for (var s : List.copyOf(STATES.values())) {
            var p = s.player;
            if (p.hasDisconnected() || p.isRemoved()) { STATES.remove(p.getUUID(), s); continue; }
            if (s.current != null && now >= s.endsAt) {
                if (s.queue.isEmpty()) s.current = null;
                else if (now >= s.endsAt + GAP_TICKS) start(s, s.queue.pollFirst(), now);
            } else if (s.current == null && !s.queue.isEmpty()) start(s, s.queue.pollFirst(), now);
            if (s.ambientNext >= 0 && now >= s.ambientNext) {
                followSound(p, sfxId("ambient_cosmodrome"), .45f, 1f);
                s.ambientNext = now + AMBIENT_TICKS - 1;
            }
        }
    }

    /** Starts (or keeps) the quiet wind bed; it is re-triggered at its seamless loop length. */
    static void ambient(ServerPlayer p, boolean on) {
        var s = state(p);
        if (on && s.ambientNext < 0) s.ambientNext = now(p);
        if (!on && s.ambientNext >= 0) { s.ambientNext = -1; stopSound(p, sfxId("ambient_cosmodrome")); }
    }

    /** Non-positional SFX that follows the listener. */
    static void sfx(ServerPlayer p, String name, float volume, float pitch) {
        followSound(p, sfxId(name), volume, pitch);
    }

    /** Positional SFX heard only by {@code p}. */
    static void sfxAt(ServerPlayer p, String name, Vec3 at, float volume, float pitch, float range) {
        if (p.hasDisconnected()) return;
        p.connection.send(new ClientboundSoundPacket(Holder.direct(SoundEvent.createFixedRangeEvent(sfxId(name), range)),
                SoundSource.AMBIENT, at.x, at.y, at.z, volume, pitch, p.level().getRandom().nextLong()));
    }

    /** Vanilla sound by id (e.g. entity.warden.heartbeat), owner only, following the listener. */
    static void vanilla(ServerPlayer p, String id, float volume, float pitch) {
        if (p.hasDisconnected()) return;
        p.connection.send(new ClientboundSoundEntityPacket(Holder.direct(SoundEvent.createFixedRangeEvent(
                Identifier.withDefaultNamespace(id), 16f)), SoundSource.AMBIENT, p, volume, pitch, p.level().getRandom().nextLong()));
    }

    /** Stops speech, queue, subtitles, ambience and every Guardian Rises SFX for this player. */
    static void stopAll(ServerPlayer p) {
        var s = STATES.remove(p.getUUID());
        if (s != null) stop(s);
        else RisingSubtitles.hide(p);
        if (!p.hasDisconnected()) for (String name : SFX) stopSound(p, sfxId(name));
    }

    static void clearAll() {
        for (var s : List.copyOf(STATES.values())) stop(s);
        STATES.clear();
    }

    private static void stop(State s) {
        if (s.current != null && s.current.voice()) stopSound(s.player, voiceId(s.current.id()));
        if (s.ambientNext >= 0) stopSound(s.player, sfxId("ambient_cosmodrome"));
        s.current = null;
        s.queue.clear();
        s.ambientNext = -1;
        RisingSubtitles.hide(s.player);
    }

    static Identifier voiceId(String lineId) { return DestinyGuardians.id(RisingServices.Voice.soundEvent(lineId)); }
    static Identifier sfxId(String name) { return DestinyGuardians.id("guardian_rises.sfx." + name); }

    private static void followSound(ServerPlayer p, Identifier id, float volume, float pitch) {
        if (p.hasDisconnected()) return;
        p.connection.send(new ClientboundSoundEntityPacket(Holder.direct(SoundEvent.createFixedRangeEvent(id, 32f)),
                SoundSource.PLAYERS, p, volume, pitch, p.level().getRandom().nextLong()));
    }

    private static void stopSound(ServerPlayer p, Identifier id) {
        if (!p.hasDisconnected()) p.connection.send(new ClientboundStopSoundPacket(id, null));
    }
}
