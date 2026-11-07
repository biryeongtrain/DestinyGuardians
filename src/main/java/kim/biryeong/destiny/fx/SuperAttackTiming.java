package kim.biryeong.destiny.fx;

/** Per-clip motion contracts; W330 contact beats are explicitly provisional source-kinematic cues. */
public final class SuperAttackTiming {
    public static final int ARC_DEPLOY = MeleeSuperAnimationTiming.durationTicks("h15_super_arc_start",11); // Full source cast plus entry blend
    public static final int ARC_DEPLOY_SWING = MeleeSuperAnimationTiming.arcDeploySwingTicks(4); // Provisional source flourish plus entry blend
    public static final int ARC_CONTACT = MeleeSuperAnimationTiming.contactTicks("h15_super_arc_attack",3); // Provisional first source sweep plus entry blend
    public static final int ARC_RECOVERY = MeleeSuperAnimationTiming.recoveryTicks("h15_super_arc_attack",8); // Full source recovery plus entry blend
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
