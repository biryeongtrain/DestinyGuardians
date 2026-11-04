package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Base DDC row170. Load only JSON here: no catalog/perk registry initialization calls. */
public final class PugilistProfile {
    public static final String ID = "pugilist";
    public static final long HASH = 691659142L;
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("ammit_ar2", 2119346509L, 4, HASH, 560115158L),
        new WeaponPerks.Roll("mindbender_s_ambition_adept", 912150785L, 3, HASH, 1732284294L),
        new WeaponPerks.Roll("dimensional_hypotrochoid", 1311684613L, 4, HASH, 1092097342L));
    private record Perk(String id, long hash, int energyPercent, int specialEnergyPercent,
                        int handlingBonus, int durationTicks) {}
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
        boolean valid() { return Double.isFinite(evpp) && Double.isFinite(vpp) && Double.isFinite(offset); }
    }
    private record Curve(String id, int baseHandlingStat, Double snapshotScalar,
                         Quadratic ready, Quadratic stow, Quadratic ads) {}
    private record Companion(String id, String perk, WeaponPerks.Roll roll) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons,
                        List<Curve> curves, List<Companion> coSelections) {}
    private static final Map<String, WeaponCatalog.Entry> CATALOG = catalog();
    private static final Data DATA = load();
    private PugilistProfile() {}

    private static <T> T read(String path, Class<T> type) {
        var stream = PugilistProfile.class.getResourceAsStream(path);
        if (stream == null) throw new IllegalStateException("Missing Pugilist resource " + path);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return GSON.fromJson(reader, type);
        } catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static Map<String, WeaponCatalog.Entry> catalog() {
        var map = new HashMap<String, WeaponCatalog.Entry>();
        for (var entry : read("/destiny/weapons/w30.json", WeaponCatalog.Entry[].class))
            map.put(entry.id(), entry);
        return Map.copyOf(map);
    }
    private static void check(boolean ok, String reason) {
        if (!ok) throw new IllegalStateException("Invalid W191 Pugilist: " + reason);
    }
    private static Data load() {
        var d = read("/destiny/weapons/w191-pugilist.json", Data.class);
        check(d != null && "W191".equals(d.stage) && d.perk != null, "definition");
        var p = d.perk;
        check(ID.equals(p.id) && p.hash == HASH && p.energyPercent == 10 && p.specialEnergyPercent == 20
            && p.handlingBonus == 35 && p.durationTicks == PugilistCycle.DURATION_TICKS, "base perk");
        check(EXPECTED.equals(d.weapons) && d.curves != null && d.curves.size() == 3, "exact three rolls");
        var ids = new HashSet<String>();
        for (var c : d.curves) {
            check(c != null && ids.add(c.id) && EXPECTED.stream().anyMatch(r -> r.id().equals(c.id))
                && c.baseHandlingStat >= 0 && c.baseHandlingStat <= 100
                && c.ready != null && c.ready.valid() && c.stow != null && c.stow.valid()
                && c.ads != null && c.ads.valid() && c.snapshotScalar == null, "raw curve");
        }
        check(d.coSelections != null && d.coSelections.size() == 6, "companions");
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
    public static int handlingBonus() { return DATA.perk.handlingBonus; }
    public static int durationTicks() { return DATA.perk.durationTicks; }
    public static int energyPercent(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("Unsupported Pugilist weapon");
        return switch (entry.family()) {
            case "fusion_rifle", "glaive", "shotgun", "sniper_rifle" -> DATA.perk.specialEnergyPercent;
            default -> DATA.perk.energyPercent;
        };
    }
    static boolean compatible(WeaponCatalog.Entry entry, String perk, WeaponPerks.Roll roll) {
        return supports(entry) && DATA.coSelections.stream().anyMatch(c -> c.id.equals(entry.id())
            && c.perk.equals(perk) && c.roll.equals(roll));
    }
    private static Curve curve(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("Noncanonical Pugilist weapon");
        return DATA.curves.stream().filter(c -> c.id.equals(entry.id())).findFirst().orElseThrow();
    }
    private static int stat(Curve c, int bonus) {
        return (int)Math.clamp((long)c.baseHandlingStat + bonus, 0L, 100L);
    }
    private static int ticks(double seconds) {
        check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "safe timing");
        return Math.max(1, (int)Math.ceil(seconds * 20));
    }
    /** Sum all legal active handling bonuses, clamp stat, evaluate raw seconds, scale, ceil ONCE. */
    public static int handlingTicks(WeaponCatalog.Entry entry, int totalBonus, double scalar, boolean ready) {
        var c = curve(entry);
        if (!Double.isFinite(scalar) || (scalar != 1 && scalar != .9 && scalar != .81)
            || scalar != 1 && DATA.coSelections.stream().noneMatch(p -> p.id.equals(entry.id()) && p.perk.equals("threat_detector")))
            throw new IllegalArgumentException("Unproved handling scalar");
        int h = stat(c, totalBonus);
        double raw = ready ? c.ready.seconds(h) : Math.max(c.stow.seconds(h), c.stow.seconds(100));
        return ticks(raw * scalar);
    }
    /** There is no legal Snapshot companion in these three pools; it is same-socket on Mindbender. */
    public static int adsTicks(WeaponCatalog.Entry entry, int totalBonus, boolean snapshotEntering) {
        var c = curve(entry);
        if (snapshotEntering && c.snapshotScalar == null) throw new IllegalArgumentException("No legal Snapshot pair");
        double raw = c.ads.seconds(stat(c, totalBonus));
        if (snapshotEntering) raw *= c.snapshotScalar;
        return Math.clamp(ticks(raw), snapshotEntering ? 1 : 2, 20);
    }
}
