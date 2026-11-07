package kim.biryeong.destiny.strike.devils;

import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

/** Strike-only Walker pools. Damage arrives already balanced by Combat; no ammo multiplier here. */
public final class DevilsWalkerState {
    public enum Phase { ARMORED, STAGGER, EXPOSED, RECOVER, DEAD }
    public enum Region { FRONT_LEFT, FRONT_RIGHT, MIDDLE_LEFT, MIDDLE_RIGHT, REAR_LEFT, REAR_RIGHT, HULL, CORE;
        public boolean leg() { return ordinal() < 6; }
    }
    public record Hit(double applied, boolean legBroken, boolean killed, Phase phase) { }
    public static final double MAX_CORE = 200, MAX_LEG = 12.5;
    public static final int STAGGER_TICKS = 16, EXPOSED_TICKS = 240, RECOVER_TICKS = 20;
    private final double[] legs = new double[6];
    private final ArrayDeque<Region> broken = new ArrayDeque<>();
    private final Map<Object, Long> shots = new HashMap<>();
    private double core = MAX_CORE;
    private long tick;
    private int age;
    private Phase phase = Phase.ARMORED;

    public DevilsWalkerState() { Arrays.fill(legs, MAX_LEG); }
    public double core() { return core; }
    /** Damage accounting includes independent leg pools; leg breaks are not boss kills. */
    public double damagePool() { return core + Arrays.stream(legs).sum(); }
    public double fraction() { return core / MAX_CORE; }
    public double leg(Region region) { return region.leg() ? legs[region.ordinal()] : 0; }
    public Phase phase() { return phase; }
    public int phaseAge() { return age; }

    /** One accepted region per shot identity per server tick; a rejected part never consumes the shot. */
    public Hit hit(Region region, double amount, Object shotIdentity) {
        if (region == null || phase == Phase.DEAD || !(amount > 0) || !Double.isFinite(amount)
                || shotIdentity != null && shots.containsKey(shotIdentity)) return rejected();
        if (region.leg()) {
            if (phase != Phase.ARMORED || leg(region) <= 0) return rejected();
            credit(shotIdentity);
            double applied = Math.min(amount, leg(region));
            legs[region.ordinal()] -= applied;
            boolean broke = legs[region.ordinal()] <= 0;
            if (broke) { broken.addLast(region); enter(Phase.STAGGER); }
            return new Hit(applied, broke, false, phase);
        }
        // Exposed core takes normal damage; armor still permits slow progress at one tenth damage.
        if (phase == Phase.STAGGER || phase == Phase.RECOVER) return rejected();
        credit(shotIdentity);
        double applied = Math.min(core, amount * (region == Region.CORE && phase == Phase.EXPOSED ? 1 : .1));
        core -= applied;
        if (core <= 0) { core = 0; enter(Phase.DEAD); }
        return new Hit(applied, false, phase == Phase.DEAD, phase);
    }
    public void tick() {
        tick++;
        shots.values().removeIf(t -> t < tick);
        age++;
        switch (phase) {
            case STAGGER -> { if (age >= STAGGER_TICKS) enter(Phase.EXPOSED); }
            case EXPOSED -> { if (age >= EXPOSED_TICKS) enter(Phase.RECOVER); }
            case RECOVER -> {
                if (age >= RECOVER_TICKS) {
                    if (Arrays.stream(legs).noneMatch(h -> h > 0)) legs[broken.removeFirst().ordinal()] = MAX_LEG;
                    enter(Phase.ARMORED);
                }
            }
            default -> { }
        }
    }
    private void credit(Object key) { if (key != null) shots.put(key, tick); }
    private Hit rejected() { return new Hit(0, false, false, phase); }
    private void enter(Phase next) { phase = next; age = 0; }
}
