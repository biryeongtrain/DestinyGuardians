package kim.biryeong.destiny.weapon;

/** Five authoritative position samples smooth packet batching, not player velocity or input.
 * This bounded 250ms integration window is local policy, not extracted Destiny internals.
 * Ten raw below-threshold samples still revoke at .5s, without a trailing-window extension. */
public final class MotionSpeedWindow {
    private static final double MIN_DISTANCE = .1;
    private final double[] distances = new double[5];
    private int cursor, size, slowTicks;
    private double total;

    public boolean sample(double distance) {
        if (!Double.isFinite(distance) || distance < 0 || distance > 2)
            throw new IllegalArgumentException("Invalid continuous position distance");
        total -= distances[cursor];
        distances[cursor] = distance;
        total += distance;
        cursor = (cursor + 1) % distances.length;
        size = Math.min(distances.length, size + 1);
        slowTicks = distance + 1e-12 < MIN_DISTANCE ? Math.min(10, slowTicks + 1) : 0;
        return !stopGraceElapsed() && total + 1e-12 >= MIN_DISTANCE * size;
    }
    public boolean stopGraceElapsed() { return slowTicks >= 10; }
    public void reset() {
        java.util.Arrays.fill(distances, 0);
        cursor = size = slowTicks = 0;
        total = 0;
    }
}
