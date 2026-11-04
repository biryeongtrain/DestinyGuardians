package kim.biryeong.destiny.weapon;

/** Observation-owned threshold/linger clock. Reads cannot acquire enemies or refresh expiry. */
public final class CorneredCycle {
    public static final int ENEMIES_REQUIRED = 2;
    public static final int LINGER_TICKS = 30;
    private long observed = -1;
    private long lostAt = -1;
    private boolean surrounded;

    /** First below-threshold sample starts linger, including same-tick loss. Invalid/rewound
     * observations revoke the old state without crediting the incoming sample.
     */
    public void update(long tick, boolean eligible, int enemies) {
        if (!eligible || tick < 0 || enemies < 0 || observed >= 0 && tick < observed) {
            clear();
            return;
        }
        observed = tick;
        boolean nearby = enemies >= ENEMIES_REQUIRED;
        if (nearby) lostAt = -1;
        else if (surrounded) lostAt = tick;
        surrounded = nearby;
    }

    /** While surrounded, report available linger. Expiry is exclusive; repeated negative
     * samples and out-of-order reads never move the deadline. Subtraction avoids overflow.
     */
    public int remaining(long tick) {
        if (observed < 0 || tick < observed) return 0;
        if (surrounded) return LINGER_TICKS;
        if (lostAt < 0 || tick - lostAt >= LINGER_TICKS) return 0;
        return LINGER_TICKS - (int)(tick - lostAt);
    }

    public boolean active(long tick) { return remaining(tick) > 0; }
    public void clear() { observed = -1; lostAt = -1; surrounded = false; }
}
