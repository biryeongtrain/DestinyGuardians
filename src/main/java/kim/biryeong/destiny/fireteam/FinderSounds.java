package kim.biryeong.destiny.fireteam;

import net.minecraft.core.Holder;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.network.protocol.game.ClientboundStopSoundPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import java.util.*;

/** Owner-only interface sounds. Countdown leases bind one accepted launch and exact connection. */
final class FinderSounds {
    static final int COUNTDOWN_AUDIO_TICKS = 127, COUNTDOWN_CHANNELS = 8;
    private static final Map<ServerGamePacketListenerImpl, Map<Integer, Countdown>> COUNTDOWNS = new IdentityHashMap<>();
    private FinderSounds() { }
    static void play(ServerPlayer p, Holder<SoundEvent> sound, float volume, float pitch) {
        if (p.hasDisconnected()) return;
        p.connection.send(new ClientboundSoundPacket(sound, SoundSource.MASTER, p.getX(), p.getY(), p.getZ(), volume, pitch, p.getRandom().nextLong()));
    }
    static void play(ServerPlayer p, SoundEvent sound, float volume, float pitch) { play(p, Holder.direct(sound), volume, pitch); }

    /** The user-selected Select Mission one-shot, committed changes only; separate from launch/countdown. */
    static boolean activityChanged(ServerPlayer player, String previous, String next) {
        if (next == null || Objects.equals(previous, next) || player.hasDisconnected() || player.isRemoved()
                || !player.level().getServer().isSameThread()) return false;
        var event = Identifier.fromNamespaceAndPath("destiny_activity_transition", "select_mission");
        play(player, SoundEvent.createVariableRangeEvent(event), 1f, 1f);
        return true;
    }

    static Countdown countdown(ServerPlayer player, Object launch, int now) {
        if (!player.level().getServer().isSameThread()) throw new IllegalStateException("Countdown audio requires server thread");
        var slots = COUNTDOWNS.computeIfAbsent(player.connection, key -> new HashMap<>());
        int channel = 0; while (slots.containsKey(channel)) channel++;
        if (channel >= COUNTDOWN_CHANNELS) throw new IllegalStateException("Too many overlapping countdowns for one connection");
        var sound = new Countdown(player, launch, channel, now); slots.put(channel, sound);
        var at = player.getEyePosition();
        player.connection.send(new ClientboundSoundPacket(Holder.direct(SoundEvent.createVariableRangeEvent(sound.event)),
                SoundSource.MASTER, at.x, at.y, at.z, 1f, 1f, player.getRandom().nextLong()));
        return sound;
    }
    static void tick(MinecraftServer server) {
        for (var slots : List.copyOf(COUNTDOWNS.values())) for (var sound : List.copyOf(slots.values())) {
            if (sound.player.level().getServer() != server) continue;
            if (sound.player.hasDisconnected() || sound.player.connection != sound.connection) sound.release(false);
            else if (server.getTickCount() - sound.started >= COUNTDOWN_AUDIO_TICKS) sound.release(false);
        }
    }
    static void reset(MinecraftServer server) {
        for (var slots : List.copyOf(COUNTDOWNS.values())) for (var sound : List.copyOf(slots.values()))
            if (sound.player.level().getServer() == server) sound.release(true);
    }
    static final class Countdown {
        final ServerPlayer player;
        final ServerGamePacketListenerImpl connection;
        final Object launch;
        final Identifier event;
        final int started, channel;
        private boolean finished;
        Countdown(ServerPlayer player, Object launch, int channel, int started) {
            this.player = player; this.connection = player.connection; this.launch = launch; this.channel = channel; this.started = started;
            event = Identifier.fromNamespaceAndPath("destiny_activity_launch", "countdown_" + channel);
        }
        void cancel(Object owner) { if (owner == launch) release(true); }
        private void release(boolean stop) {
            if (finished) return;
            finished = true;
            var slots = COUNTDOWNS.get(connection);
            if (slots == null || !slots.remove(channel, this)) return;
            if (slots.isEmpty()) COUNTDOWNS.remove(connection);
            if (stop && player.connection == connection && !player.hasDisconnected())
                connection.send(new ClientboundStopSoundPacket(event, SoundSource.MASTER));
        }
    }
}
