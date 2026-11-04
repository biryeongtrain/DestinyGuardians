package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Base exact socket authority plus original raw curves for every current canonical weapon.
 * JSON-only loading avoids catalog/registry recursion. Current Destiny durations are not inferred. */
public final class SteadyHandsProfile {
    public static final String ID = "steady_hands";
    public static final long HASH = 509074078L;
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("mindbender_s_ambition_adept", 912150785L, 4, HASH, 4054654930L));
    private record Perk(String id, long hash, int initialTicks, int refreshTicks, int handlingBonus, double handlingScalar) {}
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
        boolean valid() { return Double.isFinite(evpp) && Double.isFinite(vpp) && Double.isFinite(offset) && seconds(100) > 0; }
    }
    private record Curve(String id, Integer baseHandlingStat, Quadratic ready, Quadratic stow, Quadratic ads) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons, List<Curve> curves,
                        List<WeaponPerks.Roll> snapshotRolls, double primarySnapshotScalar, double specialSnapshotScalar) {}
    private static final Map<String, WeaponCatalog.Entry> CATALOG = catalog();
    private static final Data DATA = load();
    private static final Map<String, Curve> CURVES = curves();
    private SteadyHandsProfile() {}
    private static <T> T read(String path, Class<T> type) {
        var in = SteadyHandsProfile.class.getResourceAsStream(path);
        if (in == null) throw new IllegalStateException("Missing Steady Hands resource " + path);
        try (var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) { return GSON.fromJson(reader, type); }
        catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static Map<String, WeaponCatalog.Entry> catalog() {
        var result = new HashMap<String, WeaponCatalog.Entry>();
        for (var e : WeaponExotics.append(read("/destiny/weapons/w30.json", WeaponCatalog.Entry[].class), "catalog", WeaponCatalog.Entry.class))
            if (result.putIfAbsent(e.id(), e) != null) throw new IllegalStateException("Duplicate canonical Steady Hands entry");
        return Map.copyOf(result);
    }
    private static void check(boolean ok, String detail) {
        if (!ok) throw new IllegalStateException("Invalid W202 Steady Hands: " + detail);
    }
    private static Data load() {
        var d = read("/destiny/weapons/w202-steady-hands.json", Data.class);
        check(d != null && "W202".equals(d.stage) && d.perk != null, "stage");
        var p = d.perk;
        check(ID.equals(p.id) && p.hash == HASH && p.initialTicks == 170 && p.refreshTicks == 130
            && p.handlingBonus == 100 && p.handlingScalar == .825, "base mechanics");
        check(EXPECTED.equals(d.weapons) && d.curves != null && d.snapshotRolls != null
            && d.primarySnapshotScalar == .5 && d.specialSnapshotScalar == .8, "exact source and Snapshot");
        return new Data(d.stage, p, List.copyOf(d.weapons), List.copyOf(d.curves), List.copyOf(d.snapshotRolls),
            d.primarySnapshotScalar, d.specialSnapshotScalar);
    }
    private static Map<String, Curve> curves() {
        var result = new HashMap<String, Curve>();
        for (var c : DATA.curves) {
            var entry = CATALOG.get(c.id);
            check(entry != null && result.putIfAbsent(c.id, c) == null, "canonical unique curve");
            boolean sword = entry.family().equals("sword"), glaive = entry.family().equals("glaive");
            check(sword ? c.baseHandlingStat == null && c.ready == null && c.stow == null && c.ads == null
                : c.baseHandlingStat != null && c.baseHandlingStat >= 0 && c.baseHandlingStat <= 100
                    && c.ready != null && c.ready.valid() && c.stow != null && c.stow.valid()
                    && (glaive ? c.ads == null : c.ads != null && c.ads.valid()), "supported curve policy");
        }
        check(result.keySet().equals(CATALOG.keySet()), "all canonical entries including exotic extensions");
        return Map.copyOf(result);
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return canonical(entry) && EXPECTED.stream().anyMatch(r -> r.id().equals(entry.id()));
    }
    private static boolean canonical(WeaponCatalog.Entry entry) {
        return entry != null && entry.equals(CATALOG.get(entry.id()));
    }
    public static boolean handlingSupported(WeaponCatalog.Entry entry) {
        return canonical(entry) && CURVES.get(entry.id()).ready != null;
    }
    public static boolean adsSupported(WeaponCatalog.Entry entry) {
        return canonical(entry) && CURVES.get(entry.id()).ads != null;
    }
    public static int initialTicks() { return DATA.perk.initialTicks; }
    public static int refreshTicks() { return DATA.perk.refreshTicks; }
    public static double handlingScalar() { return DATA.perk.handlingScalar; }
    private static int ticks(double seconds) {
        check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "safe seconds");
        return Math.max(1, (int)Math.ceil(seconds * 20));
    }
    /** Complete legal duration product supplied by live authorities. Positive raw bonuses are redundant at100. */
    public static int handlingTicks(WeaponCatalog.Entry entry, boolean ready, double companionScalar) {
        if (!handlingSupported(entry) || !Double.isFinite(companionScalar) || companionScalar <= 0 || companionScalar > 1)
            throw new IllegalArgumentException("Canonical supported curve and legal scalar required");
        var c = CURVES.get(entry.id());
        return ticks((ready ? c.ready : c.stow).seconds(100) * DATA.perk.handlingScalar * companionScalar);
    }
    /** No ready/stow scalar affects ADS. Exact legal Snapshot entry multiplies raw seconds before ceil. */
    public static int adsTicks(WeaponCatalog.Entry entry, WeaponPerks.Roll snapshotEntering) {
        if (!adsSupported(entry)) throw new IllegalArgumentException("Canonical supported ADS curve required");
        double scalar = 1;
        if (snapshotEntering != null) {
            if (!snapshotEntering.id().equals(entry.id()) || !DATA.snapshotRolls.contains(snapshotEntering))
                throw new IllegalArgumentException("Exact Snapshot roll required");
            scalar = WeaponCharacteristics.of(entry).ammo() == WeaponAmmoType.PRIMARY
                ? DATA.primarySnapshotScalar : DATA.specialSnapshotScalar;
        }
        return Math.clamp(ticks(CURVES.get(entry.id()).ads.seconds(100) * scalar), snapshotEntering != null ? 1 : 2, 20);
    }
}
