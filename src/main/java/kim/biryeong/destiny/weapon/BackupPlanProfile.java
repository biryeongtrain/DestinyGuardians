package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

/** Base DDC row24 only. Initialization is JSON-only, with no catalog/perk registry cycle.
 * Current official sockets/stats and historical raw handling curves have separate provenance.
 */
public final class BackupPlanProfile {
    public static final String ID = "backup_plan";
    public static final long HASH = 1600092898L;
    private static final Gson GSON = new Gson();
    private static final String SHA256 = "1fd2e40fa62042635efaa3b86e79b3a6da9c9bdef2121533793c41975323603b";
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("hollow_words", 607191995L, 4, HASH, 1485010760L),
        new WeaponPerks.Roll("dream_breaker", 2931957300L, 4, HASH, 1206254527L),
        new WeaponPerks.Roll("line_in_the_sand", 946443267L, 4, HASH, 3257645194L));
    private record Perk(String id, long hash, double damageMultiplier, int handlingBonus,
                        double chargeTimeMultiplier, int durationTicks, int stowTicks) {}
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
        boolean valid() { return Double.isFinite(evpp) && Double.isFinite(vpp) && Double.isFinite(offset); }
    }
    private record Curve(String id, int baseHandlingStat, int chargeMillis, boolean linearFusion,
                         Double snapshotScalar, Double quickdrawReadyScalar,
                         Quadratic ready, Quadratic stow, Quadratic ads) {}
    private record Companion(String id, String perk, WeaponPerks.Roll roll) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons,
                        List<Curve> curves, List<Companion> coSelections) {}
    private static final Map<String, WeaponCatalog.Entry> CATALOG = catalog();
    private static final Data DATA = load();
    private BackupPlanProfile() {}

    private static byte[] bytes(String path) {
        var stream = BackupPlanProfile.class.getResourceAsStream(path);
        if (stream == null) throw new IllegalStateException("Missing Backup Plan resource " + path);
        try (stream) { return stream.readAllBytes(); }
        catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static <T> T read(String path, Class<T> type) {
        return GSON.fromJson(new String(bytes(path), StandardCharsets.UTF_8), type);
    }
    private static Map<String, WeaponCatalog.Entry> catalog() {
        var map = new HashMap<String, WeaponCatalog.Entry>();
        for (var e : read("/destiny/weapons/w30.json", WeaponCatalog.Entry[].class))
            check(map.putIfAbsent(e.id(), e) == null, "unique catalog");
        return Map.copyOf(map);
    }
    private static void check(boolean ok, String reason) {
        if (!ok) throw new IllegalStateException("Invalid W192 Backup Plan: " + reason);
    }
    private static Data load() {
        var raw = bytes("/destiny/weapons/w192-backup-plan.json");
        try { check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(SHA256), "resource checksum"); }
        catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
        var d = GSON.fromJson(new String(raw, StandardCharsets.UTF_8), Data.class);
        check(d != null && "W192".equals(d.stage) && d.perk != null, "definition");
        var p = d.perk;
        check(ID.equals(p.id) && p.hash == HASH && p.damageMultiplier == .8 && p.handlingBonus == 100
            && p.chargeTimeMultiplier == .7 && p.durationTicks == BackupPlanCycle.DURATION_TICKS
            && p.stowTicks == BackupPlanCycle.STOW_TICKS, "base perk");
        check(EXPECTED.equals(d.weapons) && d.curves != null && d.curves.size() == 3, "exact three rolls");
        var ids = new HashSet<String>();
        for (var c : d.curves) {
            check(c != null && ids.add(c.id) && EXPECTED.stream().anyMatch(r -> r.id().equals(c.id))
                && c.baseHandlingStat >= 0 && c.baseHandlingStat <= 100 && c.chargeMillis > 0
                && c.ready != null && c.ready.valid() && c.stow != null && c.stow.valid()
                && c.ads != null && c.ads.valid()
                && c.linearFusion == "linear_fusion_rifle".equals(CATALOG.get(c.id).family())
                && Objects.equals(c.snapshotScalar, "dream_breaker".equals(c.id) ? .8 : null)
                && Objects.equals(c.quickdrawReadyScalar, "hollow_words".equals(c.id) ? .95 : null), "raw curve");
        }
        check(d.coSelections != null && d.coSelections.size() == 14, "companions");
        var pairs = new HashSet<Companion>();
        for (var c : d.coSelections) {
            var r = EXPECTED.stream().filter(s -> s.id().equals(c.id)).findFirst().orElseThrow();
            check(c.roll != null && c.perk != null && pairs.add(c) && c.id.equals(c.roll.id())
                && r.hash() == c.roll.hash() && r.socket() != c.roll.socket()
                && c.roll.perkHash() > 0 && c.roll.plugSetHash() > 0, "other-socket companion");
        }
        return new Data(d.stage, p, List.copyOf(d.weapons), List.copyOf(d.curves), List.copyOf(d.coSelections));
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && entry.equals(CATALOG.get(entry.id()))
            && EXPECTED.stream().anyMatch(r -> r.id().equals(entry.id()));
    }
    public static double damageMultiplier() { return DATA.perk.damageMultiplier; }
    public static double chargeTimeMultiplier() { return DATA.perk.chargeTimeMultiplier; }
    public static int handlingBonus() { return DATA.perk.handlingBonus; }
    public static int durationTicks() { return DATA.perk.durationTicks; }
    public static int stowTicks() { return DATA.perk.stowTicks; }
    static boolean compatible(WeaponCatalog.Entry entry, String perk, WeaponPerks.Roll roll) {
        return supports(entry) && DATA.coSelections.stream().anyMatch(c -> c.id.equals(entry.id())
            && c.perk.equals(perk) && c.roll.equals(roll));
    }
    private static Curve curve(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("Noncanonical Backup Plan weapon");
        return DATA.curves.stream().filter(c -> c.id.equals(entry.id())).findFirst().orElseThrow();
    }
    public static boolean linearFusion(WeaponCatalog.Entry entry) { return curve(entry).linearFusion; }
    private static int ticks(double seconds) {
        check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "safe timing");
        return Math.max(1, (int)Math.ceil(seconds * 20));
    }
    /** +100 already caps handling at 100, preserving every legal positive stat companion.
     * Apply the distinct-socket TD and QD ready scalars to raw seconds, then ceil ONCE.
     */
    public static int handlingTicks(WeaponCatalog.Entry entry, double threatScalar, boolean quickdraw, boolean ready) {
        var c = curve(entry);
        if (!Double.isFinite(threatScalar) || (threatScalar != 1 && threatScalar != .9 && threatScalar != .81)
            || threatScalar != 1 && DATA.coSelections.stream().noneMatch(p -> p.id.equals(entry.id()) && p.perk.equals("threat_detector"))
            || quickdraw && c.quickdrawReadyScalar == null)
            throw new IllegalArgumentException("Unproved Backup Plan handling scalar");
        double raw = ready ? c.ready.seconds(100) : c.stow.seconds(100);
        if (ready && quickdraw) raw *= c.quickdrawReadyScalar;
        return ticks(raw * threatScalar);
    }
    public static int adsTicks(WeaponCatalog.Entry entry, boolean snapshotEntering) {
        var c = curve(entry);
        if (snapshotEntering && c.snapshotScalar == null) throw new IllegalArgumentException("No legal Snapshot pair");
        double raw = c.ads.seconds(100);
        if (snapshotEntering) raw *= c.snapshotScalar;
        return Math.clamp(ticks(raw), snapshotEntering ? 1 : 2, 20);
    }
    /** Raw official milliseconds, not a ratio of already-rounded ticks. Preserve all other fields.
     * Master retains this value at charge acceptance, including damage, throughout the paid burst.
     */
    public static WeaponProfile charge(WeaponCatalog.Entry entry, WeaponProfile base) {
        var c = curve(entry);
        Objects.requireNonNull(base, "accepted charge profile");
        if (base.chargeTicks() <= 0) throw new IllegalArgumentException("Expected charged weapon");
        int charge = (int)((c.chargeMillis * 7L + 499) / 500);
        return new WeaponProfile(base.mode(), base.damage() * (float)damageMultiplier(), base.intervalTicks(),
            base.magazine(), base.reserve(), base.reloadTicks(), base.range(), charge, base.burst(), base.pellets(),
            base.spread(), base.speed(), base.gravity(), base.blastRadius(), base.automatic(), base.infiniteReserve(),
            base.cadenceTicks(), base.burstSpacingTicks(), base.sharedBurstAmmo(), base.shellReload(),
            base.firstReloadTicks(), base.roundsPerInsert());
    }
}
