package kim.biryeong.destiny.campaign.fallen;

/**
 * Pure state for one Destiny-style enemy health bar (W300 r4, original design). Polled once per tick with the
 * entity's current health/shield fractions, so every damage source (hitscan, projectiles, abilities, splash) is
 * seen without hooks. Health that was just lost stays as a white "trail" for {@link #TRAIL_DELAY} ticks and then
 * shrinks toward the real value. {@link #frame()} is quantized so callers only send packets on visible change.
 */
final class HealthBarModel {
    /** Hide a normal enemy's bar this long after its last damage (unless it is in someone's sights). */
    static final int FADE_TICKS = 100;
    /** White trail holds still this long after a hit, then shrinks. */
    static final int TRAIL_DELAY = 12;
    /** Trail shrink per tick (fraction of the full bar). */
    static final double TRAIL_RATE = .035;
    /** Horizontal resolution of the rendered bar. */
    static final int RESOLUTION = 100;

    /** Quantized render state; equal frames render identically. */
    record Frame(int fill, int trail, int shield) {}

    private double health = 1, trail = 1, shield;
    private long lastDamage = Long.MIN_VALUE / 2;
    private boolean seeded;

    /** @param healthFraction 0..1 of max health, @param shieldFraction 0..1 of max shield (0 if none). */
    void update(long now, double healthFraction, double shieldFraction) {
        double h = clamp(healthFraction), s = clamp(shieldFraction);
        if (!seeded) { seeded = true; health = trail = h; shield = s; return; }
        if (h < health - 1e-9) { trail = Math.max(trail, health); lastDamage = now; }
        if (s < shield - 1e-9) lastDamage = now;
        health = h;
        shield = s;
        if (now - lastDamage > TRAIL_DELAY) trail -= TRAIL_RATE;
        if (trail < health) trail = health;
    }

    /** Explicit damage notification (e.g. a Walker part hit that did not change any polled value). */
    void touched(long now) { lastDamage = now; }

    /**
     * Bosses always show while the fight runs. Others show while recently damaged or while a nearby player has
     * them in their sights; dead enemies never show.
     */
    boolean visible(long now, boolean inSight, boolean boss, boolean alive) {
        if (!alive) return false;
        if (boss) return true;
        return inSight || now - lastDamage < FADE_TICKS;
    }

    boolean recentlyDamaged(long now) { return now - lastDamage < FADE_TICKS; }

    Frame frame() {
        int fill = (int) Math.round(health * RESOLUTION);
        int tr = Math.max(fill, (int) Math.round(trail * RESOLUTION));
        return new Frame(fill, tr, (int) Math.round(shield * RESOLUTION));
    }

    double health() { return health; }
    double trail() { return trail; }

    private static double clamp(double v) { return Double.isFinite(v) ? Math.max(0, Math.min(1, v)) : 0; }

    /** In-sight test (pure): within range and the view direction is within the cone around the target centre. */
    static boolean inSight(double dx, double dy, double dz, double lookX, double lookY, double lookZ,
                           double range, double cosCone) {
        double d2 = dx * dx + dy * dy + dz * dz;
        if (d2 > range * range || d2 < 1e-6) return d2 < 1e-6;
        double len = Math.sqrt(d2), l = Math.sqrt(lookX * lookX + lookY * lookY + lookZ * lookZ);
        if (l < 1e-9) return false;
        return (dx * lookX + dy * lookY + dz * lookZ) / (len * l) >= cosCone;
    }
}
