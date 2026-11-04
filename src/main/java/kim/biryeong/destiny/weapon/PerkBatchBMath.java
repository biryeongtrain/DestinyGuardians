package kim.biryeong.destiny.weapon;

/** Pure W321 batch-B rules (no Minecraft state) so event ordering and numbers are unit-testable. */
public final class PerkBatchBMath {
    private PerkBatchBMath() {}

    /** Target Lock: consecutive confirmed direct hits, reset by any gap longer than {@code gap} ticks. */
    public static final class TargetLock {
        private int hits;
        private long last = Long.MIN_VALUE / 4;
        public int hits(long now, int gap) { return now - last > gap ? 0 : hits; }
        public void hit(long now, int gap) { hits = hits(now, gap) + 1; last = now; }
        public void reset() { hits = 0; last = Long.MIN_VALUE / 4; }
    }
    /** DDC ramp: no bonus at or below startFraction of the magazine, linear start..end up to endFraction. */
    public static float targetLockMultiplier(int hits, int magazine, double startFraction, double endFraction,
                                             double start, double end) {
        if (hits <= 0 || magazine <= 0) return 1f;
        double f = hits / (double)magazine;
        if (f <= startFraction) return 1f;
        double t = Math.min(1, (f - startFraction) / (endFraction - startFraction));
        return (float)(1 + start + (end - start) * t);
    }

    /** Envious Assassin desired loaded rounds: never lower than current, bounded by the cap. */
    public static int enviousTarget(int rounds, int magazine, int kills, double perKill, double activationCap,
                                    double totalCapMagazines) {
        if (kills <= 0 || magazine <= 0) return rounds;
        int add = (int)Math.ceil(magazine * Math.min(kills * perKill, activationCap) - 1e-9);
        int cap = (int)Math.floor(magazine * totalCapMagazines);
        return Math.max(rounds, Math.min(rounds + add, cap));
    }

    /** Envious Arsenal fires only when every required other weapon dealt damage. */
    public static boolean arsenalReady(int distinctOtherSources, int required) {
        return required > 0 && distinctOtherSources >= required;
    }

    /** Payload split for one direct transaction: returns the body-equivalent amount moved to the payload.
     * Precision hits keep (multiplier - fraction) body units of impact, per DDC's adjusted ratio. */
    public static float payloadMoved(float amount, boolean precision, double precisionMultiplier, double fraction) {
        if (!(amount > 0) || fraction <= 0) return 0;
        double body = precision && precisionMultiplier > 0 ? amount / precisionMultiplier : amount;
        return (float)Math.min(amount, body * fraction);
    }

    /** Explosive Head: distance-based fuse in ticks. */
    public static int explosiveHeadDelay(double travelled, double perBlock, int min, int max) {
        if (!Double.isFinite(travelled) || travelled < 0) return min;
        return (int)Math.clamp(Math.round(min + travelled * perBlock), min, max);
    }

    /** Linear radial falloff: full inside {@code full}, reaching {@code floor} at {@code max}, zero beyond. */
    public static float falloff(double distance, double full, double max, double floor) {
        if (!Double.isFinite(distance) || distance < 0 || distance > max) return 0;
        if (distance <= full || max <= full) return 1;
        return (float)Math.max(floor, 1 - (1 - floor) * (distance - full) / (max - full));
    }

    /** Golden Tricorn x1/x2 state, cleared on stow. */
    public static final class Tricorn {
        private int level;
        private long until = Long.MIN_VALUE / 4;
        public int level(long now) { return now < until ? level : 0; }
        public void weaponKill(long now, int ticks) {
            if (level(now) == 2) return; // x2 keeps its own longer window; local policy.
            level = 1; until = now + ticks;
        }
        /** Only promotes while a buff is already active. */
        public boolean abilityKill(long now, int ticks) {
            if (level(now) == 0) return false;
            level = 2; until = now + ticks; return true;
        }
        public void clear() { level = 0; until = Long.MIN_VALUE / 4; }
        public float multiplier(long now, double x1, double x2) {
            return switch (level(now)) { case 1 -> (float)x1; case 2 -> (float)x2; default -> 1f; };
        }
    }

    /** Harmony: readying within the window after a different weapon's final blow. */
    public static boolean harmonyActivates(long now, long lastOtherKill, int window) {
        return lastOtherKill > Long.MIN_VALUE / 4 && now >= lastOtherKill && now - lastOtherKill <= window;
    }
}
