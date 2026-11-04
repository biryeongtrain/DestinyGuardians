package kim.biryeong.destiny.down;

import net.minecraft.core.Holder;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.network.protocol.game.ClientboundStopSoundPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Direct player packets. Each concurrent rescue owns a distinct stop event. Server thread only. */
public final class FireteamReviveAudio implements AutoCloseable {
    private static final BitSet CHANNELS = new BitSet(64);
    private final int channel;
    private final Identifier event;
    private final List<ServerPlayer> listeners;
    private boolean closed;

    public static void announce(ServerPlayer fallen, Collection<ServerPlayer> fireteam) {
        for (var listener : new LinkedHashSet<>(fireteam))
            if (listener != fallen && listener.level() == fallen.level() && !listener.hasDisconnected())
                play(listener, Identifier.fromNamespaceAndPath("destiny_fireteam", "guardian_down"), listener.getEyePosition());
    }

    public static void complete(ServerPlayer revived, Collection<ServerPlayer> fireteam) {
        var event = Identifier.fromNamespaceAndPath("destiny_fireteam",
                "respawn_complete_" + (1 + revived.getRandom().nextInt(4)));
        var audience = new LinkedHashSet<>(fireteam);
        audience.add(revived);
        for (var listener : audience)
            if (!listener.hasDisconnected() && listener.level() == revived.level())
                play(listener, event, listener == revived ? listener.getEyePosition() : revived.position());
    }

    public FireteamReviveAudio(ServerPlayer fallen, Collection<ServerPlayer> fireteam, Vec3 body) {
        int free = CHANNELS.nextClearBit(0);
        channel = free < 64 ? free : -1;
        if (channel >= 0) CHANNELS.set(channel);
        event = Identifier.fromNamespaceAndPath("destiny_fireteam", channel < 0 ? "revive_progress" : "revive_progress_" + channel);
        var audience = new LinkedHashSet<>(fireteam); audience.add(fallen);
        listeners = audience.stream().filter(p -> !p.hasDisconnected() && p.level() == fallen.level()).toList();
        for (var listener : listeners) play(listener, event, listener == fallen ? listener.getEyePosition() : body);
    }

    private static void play(ServerPlayer listener, Identifier event, Vec3 at) {
        listener.connection.send(new ClientboundSoundPacket(Holder.direct(SoundEvent.createVariableRangeEvent(event)),
                SoundSource.PLAYERS, at.x, at.y, at.z, 1, 1, listener.getRandom().nextLong()));
    }

    @Override public void close() {
        if (closed) return;
        closed = true;
        // Overflow uses natural completion, never stops somebody else's shared event.
        if (channel < 0) return;
        for (var listener : listeners) if (!listener.hasDisconnected())
            listener.connection.send(new ClientboundStopSoundPacket(event, SoundSource.PLAYERS));
        CHANNELS.clear(channel);
    }
}
