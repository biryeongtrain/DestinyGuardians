package kim.biryeong.destiny.sound;

import kim.biryeong.destiny.crucible.CrucibleRuntime;
import net.minecraft.core.Holder;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.phys.Vec3;

/** One accepted super's cast cue, not its repeated attacks, impacts or ready notification. */
public final class SuperCastSounds {
    private SuperCastSounds() { }

    public static void play(ServerPlayer owner, Vec3 position, String key,
                            SoundEvent fallback, float volume, float fallbackPitch) {
        boolean match = CrucibleRuntime.participating(owner);
        boolean mapped = DestinySounds.has(key);
        long seed = owner.level().getRandom().nextLong();
        for (var listener : owner.level().players()) {
            if (listener.hasDisconnected()) continue;
            boolean hostile = match && CrucibleRuntime.enemies(owner, listener);
            if (!hostile) {
                if (match && listener != owner && !CrucibleRuntime.friendly(owner, listener)) continue;
                if (!DestinySounds.canHear(listener, owner.level(), position)) continue;
            }
            // Merely broadcasting the original distant position is still inaudible on vanilla.
            // Enemy cast alerts are personal; friendly casts retain normal spatial attenuation.
            Vec3 origin = hostile ? listener.getEyePosition() : position;
            var packet = mapped ? DestinySounds.packet(key, origin, SoundSource.PLAYERS, volume, seed)
                    : new ClientboundSoundPacket(Holder.direct(SoundEvent.createFixedRangeEvent(
                            fallback.location(), (float) DestinySounds.AUDIBLE_RADIUS)), SoundSource.PLAYERS,
                            origin.x, origin.y, origin.z, volume, fallbackPitch, seed);
            DestinySounds.send(listener, packet);
        }
    }
}
