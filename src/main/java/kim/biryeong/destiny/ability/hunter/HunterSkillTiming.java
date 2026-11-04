package kim.biryeong.destiny.ability.hunter;

/** H20 ordinary-skill contacts, measured from the accepted server tick (not Tasks age). */
public final class HunterSkillTiming {
    public static final int THROW_CONTACT_TICKS = 4;
    public static final int ARC_LUNGE_TICKS = 2;
    public static final int ARC_CONTACT_TICKS = 4;
    public static final int DODGE_CONTACT_TICKS = 2;

    private final int acceptedTick;
    private final int delay;
    private boolean finished;

    public HunterSkillTiming(int acceptedTick, int delay) {
        if (delay < 0) throw new IllegalArgumentException("Negative contact delay");
        this.acceptedTick = acceptedTick;
        this.delay = delay;
    }

    /** At most one delivery, even if Tasks is ticked twice in the same server tick. */
    public boolean poll(int serverTick, boolean valid) {
        if (finished) return false;
        if (!valid) {
            cancel();
            return false;
        }
        // Subtraction also handles the signed tick counter wrapping during a short cast.
        if (serverTick - acceptedTick < delay) return false;
        finished = true;
        return true;
    }

    public void cancel() { finished = true; }
    public boolean finished() { return finished; }
}
