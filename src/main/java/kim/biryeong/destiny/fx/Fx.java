package kim.biryeong.destiny.fx;

import kim.biryeong.destiny.guardian.Element;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.phys.Vec3;

/** 바닐라 파티클·사운드 VFX 헬퍼 (docs/design/06 1층). */
public final class Fx {
    private Fx() {
    }

    public static DustParticleOptions dust(int rgb, float size) {
        return new DustParticleOptions(rgb, size);
    }

    public static ParticleOptions accent(Element element) {
        return switch (element) {
            case ARC -> ParticleTypes.ELECTRIC_SPARK;
            case SOLAR -> ParticleTypes.FLAME;
            case VOID -> ParticleTypes.PORTAL;
            case KINETIC -> ParticleTypes.CRIT;
        };
    }

    /** Ownerless overload for non-skill weapon cosmetics. Abilities must pass their owner. */
    public static void burst(ServerLevel level, Vec3 pos, Element element, int count, double spread) {
        burst(null, level, pos, element, count, spread);
    }

    public static void burst(ServerPlayer owner, ServerLevel level, Vec3 pos, Element element, int count, double spread) {
        AbilityParticles.send(owner, level, dust(element.color(), 1.6f), pos.x, pos.y, pos.z, count, spread, spread, spread, 0.0);
        AbilityParticles.send(owner, level, accent(element), pos.x, pos.y, pos.z, count / 2, spread, spread, spread, 0.05);
    }

    /** Ownerless overload for non-skill weapon cosmetics. Abilities must pass their owner. */
    public static void line(ServerLevel level, Vec3 from, Vec3 to, int rgb, double step, float size) {
        line(null, level, from, to, rgb, step, size);
    }

    public static void line(ServerPlayer owner, ServerLevel level, Vec3 from, Vec3 to, int rgb, double step, float size) {
        Vec3 delta = to.subtract(from);
        double length = delta.length();
        if (length < 1.0E-4) {
            return;
        }
        Vec3 dir = delta.scale(1.0 / length);
        ParticleOptions dust = dust(rgb, size);
        for (double d = 0; d <= length; d += step) {
            Vec3 p = from.add(dir.scale(d));
            AbilityParticles.send(owner, level, dust, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
    }

    /** Ownerless overload for non-skill weapon cosmetics. Abilities must pass their owner. */
    public static void ring(ServerLevel level, Vec3 center, double radius, int rgb, int points) {
        ring(null, level, center, radius, rgb, points);
    }

    public static void ring(ServerPlayer owner, ServerLevel level, Vec3 center, double radius, int rgb, int points) {
        ParticleOptions dust = dust(rgb, 1.2f);
        for (int i = 0; i < points; i++) {
            double a = Math.PI * 2 * i / points;
            AbilityParticles.send(owner, level, dust, center.x + Math.cos(a) * radius, center.y, center.z + Math.sin(a) * radius, 1, 0, 0, 0, 0);
        }
    }

    public static void sound(ServerLevel level, Vec3 pos, SoundEvent sound, float volume, float pitch) {
        level.playSound(null, pos.x, pos.y, pos.z, sound, SoundSource.PLAYERS, volume, pitch);
    }
}
