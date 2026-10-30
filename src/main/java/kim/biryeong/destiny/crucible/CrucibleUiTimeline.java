package kim.biryeong.destiny.crucible;

/** Pure layout/timing rules for the Crucible UI (ticks at 20 TPS, 1920x1080 reference pixels). */
public final class CrucibleUiTimeline {
    public static final int TITLE_START = 8, TITLE_END = 96, ROSTER_START = 104, COUNTDOWN_TICKS = 100;
    public static final float SCREEN_W = 1920f;
    public static final float BAR_W = 566f, BAR_GAP = 8f, PLATE_W = 230f;
    private CrucibleUiTimeline() { }

    public enum Segment { LETTERBOX_IN, TITLE, ROSTER, COUNTDOWN }

    /** @param elapsed ticks since the INTRO phase began; @param total INTRO length */
    public static Segment segment(int elapsed, int total) {
        if (elapsed >= Math.max(ROSTER_START + 40, total - COUNTDOWN_TICKS)) return Segment.COUNTDOWN;
        if (elapsed >= ROSTER_START) return Segment.ROSTER;
        if (elapsed >= TITLE_START) return Segment.TITLE;
        return Segment.LETTERBOX_IN;
    }

    /** Big number shown during the countdown; 0 means "go". */
    public static int countdownDigit(int remainingTicks) {
        return remainingTicks <= 0 ? 0 : Math.min(5, (remainingTicks + 19) / 20);
    }

    /** Filled width of a team's score bar. */
    public static float fillWidth(int score, int limit) {
        if (limit <= 0) return 0;
        float f = Math.max(0, Math.min(1, score / (float) limit));
        return Math.round(f * BAR_W);
    }

    /** 0..10 fill frame of a zone diamond for capture progress. */
    public static int diamondFrame(double progress) {
        return (int) Math.max(0, Math.min(10, Math.round(progress * 10)));
    }

    /** Horizontal centre of the zone diamond for index 0..2. */
    public static float zoneX(int index) { return SCREEN_W / 2 + (index - 1) * 74f; }

    /** Centre of the friendly (-1) or enemy (+1) score bar. */
    public static float barX(int side) { return SCREEN_W / 2 + side * (PLATE_W / 2 + BAR_GAP + BAR_W / 2 + 6); }
}
