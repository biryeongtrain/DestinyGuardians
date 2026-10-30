package kim.biryeong.destiny.sound;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.jump.JumpPhysics.Kind;
import net.minecraft.core.Holder;
import net.minecraft.network.protocol.game.ClientboundSoundEntityPacket;
import net.minecraft.network.protocol.game.ClientboundStopSoundPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;

import java.util.ArrayList;
import java.util.BitSet;
import java.util.List;

/** Finite, entity-following jump cues. Vanilla stop packets target an event, not a source entity. */
public final class JumpSounds {
    public static final int VOICES = 32;
    private static final BitSet USED = new BitSet(VOICES);
    private static final boolean QA_TRACE = Boolean.getBoolean("destiny.sound.qa");
    private JumpSounds() { }

    public static Playback start(ServerPlayer player, Kind kind) {
        String root = switch (kind) {
            case LIFT -> "jump.titan.lift";
            case GLIDE -> "jump.warlock.glide";
            default -> throw new IllegalArgumentException("Not a continuous jump: " + kind);
        };
        int voice = USED.nextClearBit(0);
        // Do not steal another caster's event or emit a sound we cannot later stop.
        if (voice >= VOICES || !DestinySounds.has(root)) return null;
        List<Identifier> events = new ArrayList<>();
        for (String layer : List.of(root)) {
            String key = layer + ".voice." + voice;
            if (DestinySounds.has(key)) events.add(DestinyGuardians.id(key));
        }
        if (events.isEmpty()) return null;
        USED.set(voice);
        Playback playback = new Playback(voice, List.copyOf(events));
        try {
            for (ServerPlayer listener : player.level().players()) {
                if (!DestinySounds.canHear(listener, player.level(), player.position())) continue;
                playback.listeners.add(listener);
                for (Identifier event : events) {
                    var packet = new ClientboundSoundEntityPacket(Holder.direct(SoundEvent.createFixedRangeEvent(
                            event, (float) DestinySounds.AUDIBLE_RADIUS)), SoundSource.PLAYERS,
                            player, .6f, 1f,
                            player.level().getRandom().nextLong());
                    listener.connection.send(packet);
                    if (QA_TRACE) DestinyGuardians.LOGGER.info("[W270 jump audio] start receiver={} owner={} event={}",
                            listener.getScoreboardName(), player.getScoreboardName(), event);
                }
            }
            return playback;
        } catch (RuntimeException error) {
            playback.stop();
            throw error;
        }
    }

    public static final class Playback {
        private final int voice;
        private final List<Identifier> events;
        private final List<ServerPlayer> listeners = new ArrayList<>();
        private boolean stopped;
        private Playback(int voice, List<Identifier> events) { this.voice = voice; this.events = events; }

        /** Stop only this activation's aliases, even when listeners moved away or changed dimension. */
        public void stop() {
            if (stopped) return;
            stopped = true;
            try {
                for (ServerPlayer listener : listeners) {
                    if (listener.hasDisconnected()) continue;
                    for (Identifier event : events) {
                        listener.connection.send(new ClientboundStopSoundPacket(event, SoundSource.PLAYERS));
                        if (QA_TRACE) DestinyGuardians.LOGGER.info("[W270 jump audio] stop receiver={} event={}",
                                listener.getScoreboardName(), event);
                    }
                }
            } finally { listeners.clear(); USED.clear(voice); }
        }
    }
}
