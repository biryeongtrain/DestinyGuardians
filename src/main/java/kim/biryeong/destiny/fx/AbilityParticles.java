package kim.biryeong.destiny.fx;

import kim.biryeong.destiny.crucible.CrucibleRuntime;
import net.minecraft.core.particles.DustColorTransitionOptions;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

/** Viewer-specific skill particles; never changes an owner's shared particle options.
 * Relationship follows teams, independent of combat protection and match phase.
 * Untintable vanilla accents (spark/flame/portal/smoke/etc.) become red dust for enemies;
 * their original shape/type survives unchanged for self, friendly and PvE viewers.
 */
public final class AbilityParticles {
    public static final int ENEMY_COLOR = 0xFF3030;
    private static final DustParticleOptions ENEMY_ACCENT = new DustParticleOptions(ENEMY_COLOR, 1.0f);

    private AbilityParticles() { }

    public static ParticleOptions forViewer(ServerPlayer owner, ServerPlayer viewer, ParticleOptions original) {
        return variant(original, CrucibleRuntime.enemies(owner, viewer));
    }

    /** Pure option selection; the original object is returned verbatim for non-enemies. */
    static ParticleOptions variant(ParticleOptions original, boolean enemy) {
        if (!enemy) return original;
        if (original instanceof DustParticleOptions dust) {
            return new DustParticleOptions(ENEMY_COLOR, dust.getScale());
        }
        if (original instanceof DustColorTransitionOptions dust) {
            return new DustColorTransitionOptions(ENEMY_COLOR, ENEMY_COLOR, dust.getScale());
        }
        return ENEMY_ACCENT;
    }

    /** Matches ServerLevel's simple broadcast: default randomization, ordinary range, no force. */
    public static int send(ServerPlayer owner, ServerLevel level, ParticleOptions original,
                           double x, double y, double z, int count,
                           double dx, double dy, double dz, double speed) {
        return send(owner, level, original, false, false, x, y, z, count, dx, dy, dz, speed);
    }

    /**
     * Retains both native flags: overrideLimiter controls native range (32/512 blocks),
     * alwaysShow is the packet visibility flag. Never bypasses native world/distance or
     * CameraViews routing with a direct connection packet. Returns recipients sent to.
     * A null owner is reserved for existing weapon cosmetics and preserves native broadcast.
     */
    public static int send(ServerPlayer owner, ServerLevel level, ParticleOptions original,
                           boolean overrideLimiter, boolean alwaysShow,
                           double x, double y, double z, int count,
                           double dx, double dy, double dz, double speed) {
        if (owner == null) {
            return level.sendParticles(original, overrideLimiter, alwaysShow,
                    x, y, z, count, dx, dy, dz, speed);
        }
        int sent = 0;
        // Build the hostile variant only when needed and at most once for this emission.
        ParticleOptions hostile = null;
        for (ServerPlayer viewer : level.players()) {
            ParticleOptions selected = original;
            if (CrucibleRuntime.enemies(owner, viewer)) {
                if (hostile == null) hostile = variant(original, true);
                selected = hostile;
            }
            if (level.sendParticles(viewer, selected, overrideLimiter, alwaysShow,
                    x, y, z, count, dx, dy, dz, speed)) sent++;
        }
        return sent;
    }

    /** One recipient, for effects with their own visibility exclusion (e.g. bow near-eye samples). */
    public static boolean sendTo(ServerPlayer owner, ServerLevel level, ServerPlayer viewer,
                                 ParticleOptions original, boolean overrideLimiter, boolean alwaysShow,
                                 double x, double y, double z, int count,
                                 double dx, double dy, double dz, double speed) {
        return level.sendParticles(viewer, forViewer(owner, viewer, original), overrideLimiter, alwaysShow,
                x, y, z, count, dx, dy, dz, speed);
    }
}
