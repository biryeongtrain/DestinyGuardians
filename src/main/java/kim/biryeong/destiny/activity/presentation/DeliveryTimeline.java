package kim.biryeong.destiny.activity.presentation;

/** Presentation clock only. Timeout/close never authorizes a spawn, kill or encounter completion. */
public final class DeliveryTimeline {
    public enum Phase { APPROACH, HOLD, DEPART, CLOSED }
    private final int approach, maxHold, settle, departure;
    private int age, deliveredAt = -1, departAt = -1;
    private boolean closed;
    public DeliveryTimeline(int approach, int maxHold, int settle, int departure) {
        if (approach < 1 || maxHold < 1 || settle < 0 || settle > maxHold || departure < 1)
            throw new IllegalArgumentException("Invalid transport timing");
        this.approach = approach; this.maxHold = maxHold; this.settle = settle; this.departure = departure;
    }
    public void delivered() { if (!closed && deliveredAt < 0) deliveredAt = age; }
    public void tick(boolean paused) {
        if (closed || paused) return;
        age++;
        if (departAt < 0 && age >= approach && (age >= approach + maxHold
                || deliveredAt >= 0 && age >= Math.max(approach, deliveredAt) + settle)) departAt = age;
        if (departAt >= 0 && age - departAt >= departure) closed = true;
    }
    public Phase phase() {
        return closed ? Phase.CLOSED : departAt >= 0 ? Phase.DEPART : age < approach ? Phase.APPROACH : Phase.HOLD;
    }
    public double fraction() {
        return switch (phase()) {
            case APPROACH -> age / (double) approach;
            case DEPART -> (age - departAt) / (double) departure;
            case HOLD, CLOSED -> 1;
        };
    }
    public void close() { closed = true; }
}
