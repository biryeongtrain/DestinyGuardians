package kim.biryeong.destiny.crucible;

/** W273 user policy: every life starts with two cartridges per equipped Special weapon,
 * except trace rifles (30). A paid death brick grants the same per-weapon units.
 * Special kill/assist meters and timed Special crates are disabled, including custom configs.
 * Heavy allocation/timing and the finite inventory anti-banking rules remain unchanged.
 */
public final class CrucibleAmmoRules {
    public static final int FIRST_CRATE_TICKS = 600, BRICK_TICKS = 1200;
    public static final int HEAVY_FIRST_TICKS = 1800, HEAVY_REPEAT_TICKS = 2400;
    public enum Credit { PRIMARY, SPECIAL, HEAVY, ABILITY, SUPER, GLAIVE_MELEE }
    public record Config(double kill, double assist, int repeatCrateTicks,
                         int assistTicks, int maxBricks, boolean heavyCrates) {
        public Config {
            if (!Double.isFinite(kill) || !Double.isFinite(assist) || kill < 0 || assist < 0
                    || kill > 1 || assist > 1 || repeatCrateTicks < 1 || assistTicks < 1
                    || maxBricks < 1 || maxBricks > 128) throw new IllegalArgumentException("Invalid local ammo policy");
        }
        /** Legacy meter fields remain accepted for config compatibility but cannot enable Special grants.
         * Heavy crates at 90s then every 120s retain the existing LOCAL policy. */
        public static Config localDefaults() { return new Config(
                Double.parseDouble(System.getProperty("destiny.crucible.ammo.kill", ".25")),
                Double.parseDouble(System.getProperty("destiny.crucible.ammo.assist", ".125")),
                Integer.getInteger("destiny.crucible.ammo.crateRepeatTicks",1200), 200, 24,
                Boolean.parseBoolean(System.getProperty("destiny.crucible.ammo.heavyCrates","true"))); }
    }
    private CrucibleAmmoRules() { }
    public static int starting(String family) { return "trace_rifle".equals(family) ? 30 : 2; }
    public static int brick(String family) { return starting(family); }
    public static int specialPayout(String family, boolean crate) { return starting(family); }
    /** Heavy-only integer split. Special grants are per weapon and never call this helper. */
    public static int split(int allotment, int count) {
        return allotment <= 0 || count <= 0 ? 0 : Math.max(1, allotment / count);
    }
    /** No finite ammo survives death; the next accepted life receives a fresh allocation. */
    public static long retained(long total, int allocatedStarting) { return 0; }
    /** Compatibility entry points: neither legacy configuration nor combat callbacks create Special. */
    public static double gain(Config c, Credit source, boolean assist) { return 0; }
    public static int crateWave(int playingTicks, Config c) { return -1; }
    /** Heavy payout is LOCAL porting tuning, unrelated to the PvE meter.
     * MG uses 22, at or below the supplied 9.7 normal/rapid maximums (22/62);
     * this is not a frame-specific official grant table. */
    public static int heavyBrick(String family) {
        return switch (family) {
            case "machine_gun" -> 22;
            case "sword" -> 8;
            case "heavy_grenade_launcher", "linear_fusion_rifle" -> 3;
            default -> 1;
        };
    }
}
