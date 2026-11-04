package kim.biryeong.destiny.weapon;

/** LOCAL POLICY (W320): Minecraft has no slide. A slide starts on the server tick where the player
 * begins crouching on the ground within 2 ticks of having sprinted, while still moving at
 * >= 0.15 blocks/tick (sprint is ~0.28). The sprint streak before that crouch is retained for
 * "after sprinting for N seconds" traits. Pure; the caller supplies authoritative server samples.
 */
public final class SlideDetector {
    public static final int SPRINT_GRACE_TICKS = 2;
    public static final double MIN_SPEED = .15;
    private long last = Long.MIN_VALUE, lastSprint = Long.MIN_VALUE;
    private int streak, slideStreak;
    private boolean wasCrouching;
    /** @return true only on the slide-start tick. Duplicate/out-of-order ticks are ignored. */
    public boolean sample(long tick, boolean onGround, boolean sprinting, boolean crouching, double horizontalSpeed) {
        if (tick <= last) return false;
        boolean contiguous = last != Long.MIN_VALUE && tick - last == 1;
        last = tick;
        if (sprinting) {
            streak = lastSprint != Long.MIN_VALUE && tick - lastSprint <= SPRINT_GRACE_TICKS ? streak + 1 : 1;
            lastSprint = tick;
        } else if (lastSprint == Long.MIN_VALUE || tick - lastSprint > SPRINT_GRACE_TICKS) streak = 0;
        boolean start = contiguous && crouching && !wasCrouching && onGround && !sprinting
            && lastSprint != Long.MIN_VALUE && tick - lastSprint <= SPRINT_GRACE_TICKS
            && Double.isFinite(horizontalSpeed) && horizontalSpeed >= MIN_SPEED;
        wasCrouching = crouching;
        if (start) { slideStreak = streak; streak = 0; lastSprint = Long.MIN_VALUE; }
        return start;
    }
    /** Sprint ticks accumulated before the most recent slide start. */
    public int sprintTicksAtSlide() { return slideStreak; }
    public void reset() { last = Long.MIN_VALUE; lastSprint = Long.MIN_VALUE; streak = 0; slideStreak = 0; wasCrouching = false; }
}
