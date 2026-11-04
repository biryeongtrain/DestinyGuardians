package kim.biryeong.destiny.activity.presentation;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ColorParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/**
 * Shared Destiny-style transmat-in for a Guardian materialising at {@code feet}: a cold light column gathers
 * and spirals down the body silhouette, then a white flash and spark burst reveal the body. Delivered directly
 * to each viewer (inside {@link CameraViews#sending}) so it renders through cinematic camera filters too.
 */
public final class TransmatArrival {
    /** Effect lead before the body becomes visible. */
    public static final int LEAD_TICKS = 12;
    private static final Holder<SoundEvent> SOUND = Holder.direct(SoundEvent.createVariableRangeEvent(
            DestinyGuardians.id("guardian_rises.sfx.transmat")));
    private static final ParticleOptions COLD = new DustParticleOptions(0xBFE8FF, 1.1f);
    private TransmatArrival() { }

    /** {@code untilReveal} counts down from {@link #LEAD_TICKS} to 0 (the reveal tick). */
    public static void tick(ServerLevel level, Vec3 feet, int untilReveal, List<ServerPlayer> viewers) {
        if (untilReveal < 0 || untilReveal > LEAD_TICKS) return;
        double progress = 1 - untilReveal / (double) LEAD_TICKS; // 0 → 1
        for (var viewer : viewers) {
            if (viewer.hasDisconnected() || viewer.level() != level) continue;
            CameraViews.sending(() -> {
                if (untilReveal == LEAD_TICKS) viewer.connection.send(new ClientboundSoundPacket(SOUND, SoundSource.PLAYERS,
                        feet.x, feet.y + 1, feet.z, .85f, 1.05f, viewer.getRandom().nextLong()));
                if (untilReveal > 0) {
                    // Column: faint full-height glow that tightens as the body forms.
                    double radius = .55 - .3 * progress;
                    level.sendParticles(viewer, ParticleTypes.END_ROD, true, false, feet.x, feet.y + 1, feet.z,
                            2, radius * .5, .85, radius * .5, .004);
                    // Two counter-rotating scan rings descending head → feet.
                    double y = feet.y + 2.0 - 1.9 * progress;
                    for (int i = 0; i < 6; i++) {
                        double a = progress * Math.PI * 3 + i * Math.PI / 3;
                        level.sendParticles(viewer, COLD, true, false, feet.x + Math.cos(a) * radius, y, feet.z + Math.sin(a) * radius,
                                1, 0, 0, 0, 0);
                    }
                    if (untilReveal % 3 == 0) level.sendParticles(viewer, ParticleTypes.GLOW, true, false,
                            feet.x, feet.y + .05, feet.z, 3, .45, .01, .45, 0);
                } else {
                    level.sendParticles(viewer, ColorParticleOption.create(ParticleTypes.FLASH, 0xFFE6F6FF), true, false,
                            feet.x, feet.y + 1, feet.z, 1, 0, 0, 0, 0);
                    level.sendParticles(viewer, ParticleTypes.END_ROD, true, false, feet.x, feet.y + 1, feet.z, 28, .25, .7, .25, .05);
                    level.sendParticles(viewer, ParticleTypes.ELECTRIC_SPARK, true, false, feet.x, feet.y + 1, feet.z, 14, .3, .8, .3, .2);
                }
            });
        }
    }
}
