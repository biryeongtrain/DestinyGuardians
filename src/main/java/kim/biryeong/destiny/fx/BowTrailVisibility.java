package kim.biryeong.destiny.fx;

/** Visual-only provisional Minecraft policy, not an original Destiny distance measurement. */
public final class BowTrailVisibility {
    public static final double OWNER_RADIUS = 1.25;
    private BowTrailVisibility() { }

    /** Exact boundary is retained. Invalid distances must not hide unrelated particles. */
    public static boolean hidesOwnerSample(double squaredDistance) {
        return Double.isFinite(squaredDistance) && squaredDistance >= 0
                && squaredDistance < OWNER_RADIUS * OWNER_RADIUS;
    }
}
