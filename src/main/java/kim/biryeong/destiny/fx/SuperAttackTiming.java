package kim.biryeong.destiny.fx;

/** Versioned clip contract: one transition tick plus the authored contact key. */
public final class SuperAttackTiming {
    public static final int ARC_DEPLOY = 11; // H26 .50s power flourish + transition
    public static final int ARC_DEPLOY_SWING = 4; // .15s hero sweep + transition
    public static final int ARC_CONTACT = 3; // H26 .10s + transition
    public static final int ARC_RECOVERY = 8; // H26 .35s + transition
    public static final int SOLAR_DEPLOY = 10; // .45s + transition
    public static final int SOLAR_CONTACT = 3; // .10s + transition
    public static final int SOLAR_RECOVERY = 8; // .35s + transition
    private int remaining;

    public boolean request(int contactTicks) {
        if (contactTicks < 1) throw new IllegalArgumentException("Contact must follow wind-up");
        if (remaining > 0) return false;
        remaining = contactTicks;
        return true;
    }

    public boolean advance() { return remaining > 0 && --remaining == 0; }
    public boolean pending() { return remaining > 0; }
    public void cancel() { remaining = 0; }
}
