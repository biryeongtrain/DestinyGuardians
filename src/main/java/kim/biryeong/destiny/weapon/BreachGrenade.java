package kim.biryeong.destiny.weapon;

/** W82 exact Lightweight GL admission and bounded Minecraft remote-fuse policy.
 * The official intrinsic establishes release-to-detonate, not these simulation constants.
 * Arming/early-release policy is documented separately from the six-tick crossbow input approximation.
 * A fuse belongs to one already-paid projectile; it never spends ammunition or finds a target.
 */
public final class BreachGrenade {
    public static final String WEAPON_ID = "salvager_s_salvo";
    public static final long WEAPON_HASH = 2060863616L, INTRINSIC_HASH = 474269988L;
    public static final int ARM_TICKS = 10;
    public static final int MAX_BOUNCES = 16;
    public static final double RESTITUTION = .65;
    private boolean controlled = true;
    private boolean detonate;

    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WEAPON_ID.equals(entry.id())
                && "grenade_launcher".equals(entry.family()) && "lightweight".equals(entry.frame())
                && WeaponCharacteristics.of(entry).bungieHash() == WEAPON_HASH;
    }
    /** Only this shot's original input session calls release. Early release is consumed, not queued. */
    public void release(long age) {
        if (!controlled) return;
        controlled = false;
        detonate = age >= ARM_TICKS;
    }
    /** Cancellation is NOT a trigger release: reload/swap/skill never requests an explosion. */
    public void detach() { controlled = false; }
    public boolean controlled() { return controlled; }
    public boolean detonate() { return detonate; }

    public record Velocity(double x, double y, double z) {}
    /** Reflect about one native block face and offset the position separately at runtime.
     * The restitution and bounce cap are authored safety/feel choices, not original Destiny physics.
     */
    public static Velocity reflect(double x, double y, double z, int nx, int ny, int nz) {
        if (!Double.isFinite(x) || !Double.isFinite(y) || !Double.isFinite(z)
                || (long)nx*nx + (long)ny*ny + (long)nz*nz != 1)
            throw new IllegalArgumentException("Expected finite velocity and one unit block face");
        double dot=x*nx+y*ny+z*nz;
        return new Velocity((x-2*dot*nx)*RESTITUTION,(y-2*dot*ny)*RESTITUTION,(z-2*dot*nz)*RESTITUTION);
    }
}
