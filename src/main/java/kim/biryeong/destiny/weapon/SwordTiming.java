package kim.biryeong.destiny.weapon;

import java.util.Objects;

/**
 * Pure W54 deadlines for the authored W53 contact/release cues.
 * Source: art/weapons/w53/manifest.json, authoredContactOrReleaseSeconds.
 * These are local animation choices, not measured Destiny 2 timings.
 * No animation engine, catalog loading, scheduling or gameplay state is needed.
 */
public final class SwordTiming {
    /** One tick of animation start blending, before the clip's own timeline. */
    public static final int START_TICKS = 1;

    private SwordTiming() {}

    /**
     * Ticks after attack acceptance: ceil(authored clip seconds * 20) + start blend.
     * Caster uses its release cue; the other shapes use their contact cue.
     */
    public static int contactTicks(SwordProfile.Shape shape, boolean heavy, int combo) {
        return (int) Math.ceil(contactSeconds(shape, heavy, combo) * 20.0) + START_TICKS;
    }

    /**
     * Authored seconds on the clip timeline, excluding the start blend.
     * Lights ignore shape (including null) and clamp combo to 1..3.
     * Heavies ignore combo and require a non-null shape.
     *
     * @throws NullPointerException if heavy is true and shape is null
     */
    public static double contactSeconds(SwordProfile.Shape shape, boolean heavy, int combo) {
        if (!heavy) {
            return switch (Math.max(1, Math.min(3, combo))) {
                case 1 -> 0.15;
                default -> 0.20;
            };
        }
        return switch (Objects.requireNonNull(shape, "shape is required for a heavy sword attack")) {
            case UPPERCUT -> 0.35;
            case DASH -> 0.25;
            case SLAM -> 0.40;
            case VORTEX -> 0.45;
            case CASTER -> 0.30;
        };
    }
}
