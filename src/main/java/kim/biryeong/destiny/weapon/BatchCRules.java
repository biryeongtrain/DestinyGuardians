package kim.biryeong.destiny.weapon;

/** Pure W322 batch C state machines and arithmetic, independent of Minecraft objects. */
public final class BatchCRules {
    private BatchCRules() {}

    /** Adaptive Munitions: stacks only on non-matching (or barrier) shield damage; reset by a
     * matching shield hit or an unshielded combatant hit. Bonus applies only against shields. */
    public static final class Adaptive {
        private int hits;
        public double multiplier(boolean shielded, double perHit, double cap) {
            return shielded ? 1 + Math.min(cap, hits * perHit) : 1;
        }
        public void hit(boolean shielded, boolean matching) {
            if (shielded && !matching) hits = Math.min(hits + 1, 1000); else hits = 0;
        }
        public int hits() { return hits; }
        public void clear() { hits = 0; }
    }

    /** Redirection: rank-and-file hits bank stacks; powerful hits consume up to N before damage. */
    public static final class Redirection {
        private int stacks;
        public int stacks() { return stacks; }
        public void gain(int amount, int max) { if (amount > 0) stacks = Math.min(max, stacks + amount); }
        /** @return consumed stack count; consumption happens even if the hit is later immune. */
        public int consume(int max) { int n = Math.min(max, stacks); stacks -= n; return n; }
        /** DDC: 33% per stack, 100% at the full consumption count (3 x 33% is reported as 100%). */
        public static double multiplier(int consumed, int full, double perStack, double maxBonus) {
            if (consumed <= 0) return 1;
            return 1 + (consumed >= full ? maxBonus : Math.min(maxBonus, consumed * perStack));
        }
        public void clear() { stacks = 0; }
    }

    /** One-Two Punch: next powered melee within the window; removed on stow. */
    public static final class OneTwoPunch {
        private long until = Long.MIN_VALUE;
        public static boolean qualifies(int pelletsOnTarget, int weaponPellets, int requirement) {
            return weaponPellets > 0 && pelletsOnTarget >= Math.min(requirement, weaponPellets);
        }
        public void grant(long now, int ticks) { until = now + ticks; }
        public boolean active(long now) { return now < until; }
        /** Consume at an accepted melee. @return true if the buff applied. */
        public boolean consume(long now) { boolean a = active(now); until = Long.MIN_VALUE; return a; }
        public void clear() { until = Long.MIN_VALUE; }
    }

    /** Crystalline Corpsebloom: a weapon kill grants/refreshes the window; kills inside an
     * already-active window release a seeker. */
    public static final class Corpsebloom {
        private long until = Long.MIN_VALUE;
        public boolean kill(long now, int window) {
            boolean seeker = now < until;
            until = now + window;
            return seeker;
        }
        public boolean active(long now) { return now < until; }
        public void clear() { until = Long.MIN_VALUE; }
    }

    /** Energy Transfer percent of a full class ability for one damage event while guarding.
     * @param loss actual Minecraft health+absorption loss
     * @param blocked frontal guarded hit (loss already scaled by blockedFraction)
     */
    public static double energyTransferPercent(float loss, boolean blocked, boolean melee, float maxHealth,
                                               PerkBatchCProfile.EnergyTransferRule r) {
        if (!Float.isFinite(loss) || loss <= 0 || !Float.isFinite(maxHealth) || maxHealth <= 0) return 0;
        double raw = blocked ? loss / r.blockedFraction() : loss;
        double points = raw * r.guardianHp() / maxHealth;
        double percent = points * (blocked ? (melee ? r.blockedMeleePercent() : r.blockedPercent()) : r.unblockedPercent());
        return Math.min(100, percent);
    }
    /** Remaining cooldown after crediting a percentage of the FULL cooldown (ceil grant). */
    public static int cooldownAfter(int fullTicks, int remainingTicks, double percent) {
        if (fullTicks <= 0 || remainingTicks <= 0 || !Double.isFinite(percent) || percent <= 0) return remainingTicks;
        long grant = (long) Math.ceil(fullTicks * Math.min(100, percent) / 100.0);
        return (int) Math.max(0, remainingTicks - grant);
    }
    /** Destiny damage points normalised by Guardian health onto a Minecraft health pool. */
    public static float points(double destinyPoints, double guardianHp, float maxHealth) {
        return (float) (destinyPoints * maxHealth / guardianHp);
    }
}
