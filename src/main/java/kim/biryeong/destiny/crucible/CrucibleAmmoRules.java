package kim.biryeong.destiny.crucible;

/** Pure normal-Control policy. Coordinator-supplied post-July-2025 / 9.7 research:
 * one starting kill once per match, no respawn refill, death retains up to 3x starting,
 * first Special crates at 30s, personal meter bricks expire at 60s; trace starts at 29,
 * sniper brick grants 2. Other family allotments below are PORTING DEFAULTS.
 * Absolute meter gains are unknown: LOCAL values, never the official 2024 table.
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
        /** LOCAL: four primary kills per meter, half-credit assists, 60s repeat,
         * ten-second assist window, 24 pickups; Heavy crates at 90s then every 120s are LOCAL. */
        public static Config localDefaults() { return new Config(
                Double.parseDouble(System.getProperty("destiny.crucible.ammo.kill", ".25")),
                Double.parseDouble(System.getProperty("destiny.crucible.ammo.assist", ".125")),
                Integer.getInteger("destiny.crucible.ammo.crateRepeatTicks",1200), 200, 24,
                Boolean.parseBoolean(System.getProperty("destiny.crucible.ammo.heavyCrates","true"))); }
    }
    private CrucibleAmmoRules() { }
    public static int starting(String family) {
        return switch (family) {
            case "trace_rifle" -> 29;
            case "glaive" -> 2;
            default -> 1;
        };
    }
    public static int brick(String family) { return family.equals("sniper_rifle") ? 2 : starting(family); }
    public static int specialPayout(String family, boolean crate) { return crate ? starting(family) : brick(family); }
    /** LOCAL integer split: floor each family allotment/count, minimum one cartridge.
     * This indivisibility exception can give two one-round weapons one round each. */
    public static int split(int allotment, int count) {
        return allotment <= 0 || count <= 0 ? 0 : Math.max(1, allotment / count);
    }
    public static long retained(long total, int allocatedStarting) {
        return Math.min(Math.max(0, total), 3L * Math.max(0, allocatedStarting));
    }
    /** 9.7 relative reductions: Special/Heavy kills AND assists -33%; Super kills
     * -33%; glaive melee -20%. Super assists keep LOCAL base assist credit. */
    public static double gain(Config c, Credit source, boolean assist) {
        double multiplier = switch (source) {
            case SPECIAL, HEAVY -> .67;
            case SUPER -> assist ? 1 : .67;
            case GLAIVE_MELEE -> .80;
            default -> 1;
        };
        return (assist ? c.assist() : c.kill()) * multiplier;
    }
    public static int crateWave(int playingTicks, Config c) {
        return playingTicks < FIRST_CRATE_TICKS ? -1 : (playingTicks - FIRST_CRATE_TICKS) / c.repeatCrateTicks();
    }
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
