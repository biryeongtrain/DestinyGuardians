package kim.biryeong.destiny.fireteam;

import net.minecraft.core.Holder;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;

/** Owner-only interface sounds (menu clicks, countdown ticks), played at the player. */
final class FinderSounds {
    private FinderSounds() { }
    static void play(ServerPlayer p, Holder<SoundEvent> sound, float volume, float pitch) {
        if (p.hasDisconnected()) return;
        p.connection.send(new ClientboundSoundPacket(sound, SoundSource.MASTER, p.getX(), p.getY(), p.getZ(), volume, pitch, p.getRandom().nextLong()));
    }
    static void play(ServerPlayer p, SoundEvent sound, float volume, float pitch) { play(p, Holder.direct(sound), volume, pitch); }
}
