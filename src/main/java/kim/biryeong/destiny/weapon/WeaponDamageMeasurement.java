package kim.biryeong.destiny.weapon;

import java.util.ArrayDeque;

/** Per-victim call stack: exclude nested actual-damage deltas from their outer call.
 * Signed child deltas also account for nested healing without attributing a child's loss twice. */
public final class WeaponDamageMeasurement {
    private static final class Frame { final float before; float children; Frame(float before) { this.before=before; } }
    private final ArrayDeque<Frame> frames = new ArrayDeque<>();
    public void begin(float total) { frames.push(new Frame(total)); }
    public float finish(float total) {
        var f=frames.pop(); float inclusive=f.before-total;
        if (!frames.isEmpty()) frames.peek().children+=inclusive;
        float exclusive=inclusive-f.children;
        return Float.isFinite(exclusive) ? Math.max(0,exclusive) : 0;
    }
}
