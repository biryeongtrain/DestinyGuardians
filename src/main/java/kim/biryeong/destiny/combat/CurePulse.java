package kim.biryeong.destiny.combat;

/** Pure per-recipient Cure cooldown and deferred second pulse; owner/world held by adapter. */
public final class CurePulse {
    private long used = Long.MIN_VALUE;
    private float pending;
    public boolean accept(long now, float secondHalf) {
        if (secondHalf <= 0 || !Float.isFinite(secondHalf) || now < 0
                || used != Long.MIN_VALUE && now >= used && now-used < 20) return false;
        used = now; pending = secondHalf; return true;
    }
    public float pulse(long now) {
        if (used == Long.MIN_VALUE || now < used + 2) return 0;
        float value = pending; pending = 0; return value;
    }
    public boolean expired(long now) { return used != Long.MIN_VALUE && (now < used || now-used >= 20); }
}
