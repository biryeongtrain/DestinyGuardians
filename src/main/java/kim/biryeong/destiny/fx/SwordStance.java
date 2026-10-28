package kim.biryeong.destiny.fx;

/** Authored visual selector, not movement, guard eligibility or combat policy. */
public enum SwordStance {
    IDLE, MOVE, GUARD, AIR;

    /** Same threshold as Arc locomotion: more than 0.015 blocks resolved per tick.
     * Guard uses the authoritative active guard, never raw sneak input alone.
     * Large discontinuities are teleports, not a walk cycle. */
    public static SwordStance select(boolean guarding, boolean grounded, double movedSquared) {
        if (guarding) return GUARD;
        if (!grounded) return AIR;
        return Double.isFinite(movedSquared) && movedSquared > .000225 && movedSquared <= 64 ? MOVE : IDLE;
    }

    public String clip() {
        return "sword_" + name().toLowerCase(java.util.Locale.ROOT);
    }
}
