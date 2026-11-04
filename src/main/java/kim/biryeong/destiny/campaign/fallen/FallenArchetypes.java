package kim.biryeong.destiny.campaign.fallen;

import kim.biryeong.destiny.campaign.RisingServices;
import kim.biryeong.destiny.campaign.RisingServices.FallenKind;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/**
 * Original mission tuning for the first-mission Fallen (W300). Destiny-inspired roles, NOT extracted numbers:
 * the extraction contains models only, so every value here is authored and documented in
 * docs/design/guardian-rises/fallen-runtime.md. Damage is a fraction of the victim's max health so
 * it stays readable whatever Guardian health scale the server uses.
 */
public final class FallenArchetypes {
    private FallenArchetypes() {}

    public enum Role { RUSHER, MARKSMAN, COMMANDER, DRONE, BOSS }

    /** One ranged/melee attack pattern. Ticks are server ticks (20/s). projectileSpeed 0 = melee. */
    public record Attack(double damageFraction, int telegraphTicks, int cooldownMin, int cooldownMax,
                         int burst, int burstGap, double projectileSpeed, double splashRadius,
                         double rangeMin, double rangeMax) {
        public Attack {
            if (!(damageFraction > 0 && damageFraction < 1)) throw new IllegalArgumentException("damageFraction");
            if (telegraphTicks < 4) throw new IllegalArgumentException("unreadable telegraph");
            if (cooldownMin <= 0 || cooldownMax < cooldownMin) throw new IllegalArgumentException("cooldown");
            if (burst < 1 || burstGap < 0) throw new IllegalArgumentException("burst");
            if (projectileSpeed < 0 || splashRadius < 0 || rangeMin < 0 || rangeMax <= rangeMin)
                throw new IllegalArgumentException("range");
        }
        public boolean melee() { return projectileSpeed == 0; }
        public Attack scaled(double damage) {
            return new Attack(Math.min(.95, damageFraction * damage), telegraphTicks, cooldownMin, cooldownMax,
                    burst, burstGap, projectileSpeed, splashRadius, rangeMin, rangeMax);
        }
    }

    /**
     * walkSpeed/runSpeed are movement-speed attribute values (vanilla zombie ~0.23). preferredMin/Max is the
     * distance band the brain holds. blinkCooldown is the Vandal-style short teleport (0 = never).
     * accuracy (0..1] is multiplied by mission Difficulty.accuracy.
     */
    public record Archetype(FallenKind kind, Role role, String model, List<String> clips,
                            float width, float height, boolean flying,
                            double health, double shield, double walkSpeed, double runSpeed,
                            double preferredMin, double preferredMax, double accuracy,
                            Attack primary, Attack secondary, int blinkCooldown, double knockbackResistance,
                            int arcColor) {
        public Archetype {
            if (width <= 0 || height <= 0 || health <= 0 || shield < 0) throw new IllegalArgumentException(kind + " body");
            if (preferredMin < 0 || preferredMax <= preferredMin) throw new IllegalArgumentException(kind + " band");
            if (accuracy <= 0 || accuracy > 1) throw new IllegalArgumentException(kind + " accuracy");
            clips = List.copyOf(clips);
        }
        /** Mission tuning. Health and shield scale together; accuracy is clamped to a readable band. */
        public Archetype tuned(RisingServices.Difficulty d) {
            double h = positive(d.health()), dmg = positive(d.damage()), acc = positive(d.accuracy());
            return new Archetype(kind, role, model, clips, width, height, flying, health * h, shield * h,
                    walkSpeed, runSpeed, preferredMin, preferredMax, Math.max(.15, Math.min(1, accuracy * acc)),
                    primary.scaled(dmg), secondary == null ? null : secondary.scaled(dmg), blinkCooldown,
                    knockbackResistance, arcColor);
        }
        /** Top quarter of the box is the precision zone (WeaponPrecision rule); drones and the boss have none. */
        public boolean hasPrecisionHead() { return !flying && role != Role.BOSS; }
    }

    static double positive(double v) { return Double.isFinite(v) && v > 0 ? v : 1; }

    public static final int ARC_BLUE = 0x7FD8FF;
    public static final int FALLEN_ARC = 0x9FE8FF;
    public static final int WALKER_ORANGE = 0xFF9A3C;

    private static final Map<FallenKind, Archetype> TABLE = new EnumMap<>(FallenKind.class);
    static {
        // Dreg: fragile rusher. Shock blades up close, a shock-pistol snap shot while closing in.
        TABLE.put(FallenKind.DREG, new Archetype(FallenKind.DREG, Role.RUSHER, RisingServices.Models.DREG,
                RisingServices.Models.INFANTRY_CLIPS, .8f, 1.9f, false,
                20, 0, .25, .36, 1.6, 7, .55,
                new Attack(.24, 9, 22, 34, 1, 0, 0, 0, 0, 2.6),
                new Attack(.06, 7, 40, 60, 1, 0, 1.15, 0, 5, 16), 0, .35, ARC_BLUE));
        // Vandal: tall wire-rifle marksman. Mid range, strafes, seeks cover, blinks when pressured.
        TABLE.put(FallenKind.VANDAL, new Archetype(FallenKind.VANDAL, Role.MARKSMAN, RisingServices.Models.VANDAL,
                RisingServices.Models.INFANTRY_CLIPS, .8f, 2.3f, false,
                34, 0, .22, .30, 9, 17, .7,
                new Attack(.075, 12, 38, 58, 3, 4, 1.55, 0, 4, 32),
                new Attack(.18, 9, 30, 40, 1, 0, 0, 0, 0, 2.4), 170, .5, FALLEN_ARC));
        // Captain: tanky commander with arc shield and a slow, dodgeable shock blast.
        TABLE.put(FallenKind.CAPTAIN, new Archetype(FallenKind.CAPTAIN, Role.COMMANDER, RisingServices.Models.CAPTAIN,
                RisingServices.Models.INFANTRY_CLIPS, 1.0f, 2.6f, false,
                70, 36, .2, .27, 6, 13, .65,
                new Attack(.28, 20, 60, 80, 1, 0, .72, 2.6, 3, 26),
                new Attack(.22, 10, 34, 44, 1, 0, 0, 0, 0, 2.8), 0, .8, FALLEN_ARC));
        // Shank: hovering drone, arc bursts, keeps distance and orbits.
        TABLE.put(FallenKind.SHANK, new Archetype(FallenKind.SHANK, Role.DRONE, RisingServices.Models.SHANK,
                RisingServices.Models.SHANK_CLIPS, .9f, .9f, true,
                14, 0, .32, .42, 7, 15, .5,
                new Attack(.045, 10, 46, 64, 4, 3, 1.2, 0, 3, 24),
                null, 0, .2, ARC_BLUE));
        // Walker: boss pools live in WalkerBoss.Tuning; this row is the anchor identity and its two guns.
        // primary = main cannon (slow arcing shell, ground warning), secondary = anti-personnel bursts.
        TABLE.put(FallenKind.WALKER, new Archetype(FallenKind.WALKER, Role.BOSS, RisingServices.Models.WALKER,
                RisingServices.Models.WALKER_CLIPS, 1.0f, 1.0f, false,
                1000, 0, .12, .12, 10, 40, .6,
                new Attack(.42, 30, 110, 140, 1, 0, .9, 3.4, 8, 48),
                new Attack(.07, 10, 50, 70, 5, 3, 1.4, 0, 3, 40), 0, 1, WALKER_ORANGE));
    }

    public static Archetype of(FallenKind kind) { return TABLE.get(kind); }
    public static Map<FallenKind, Archetype> all() { return Map.copyOf(TABLE); }

    /** Uniform 0..1 sample to cooldown ticks. */
    public static int cooldown(Attack attack, double unit) {
        double u = Math.max(0, Math.min(1, unit));
        return attack.cooldownMin() + (int) Math.round((attack.cooldownMax() - attack.cooldownMin()) * u);
    }

    /** Aim error cone (radians): accuracy 1 is 0.6 degrees, accuracy .15 about 7 degrees. */
    public static double spreadRadians(double accuracy) {
        double a = Math.max(.15, Math.min(1, accuracy));
        return Math.toRadians(.6 + (1 - a) * 7.5);
    }

    /** Lead fraction: accurate shooters lead more of the target's velocity; never perfect so strafing works. */
    public static double leadFraction(double accuracy) {
        double a = Math.max(.15, Math.min(1, accuracy));
        return .25 + .5 * a;
    }
}
