package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** W321 batch B: twelve base traits with exact pinned official socket pools.
 * Mechanics are DDC PvE base values mapped to Minecraft units; each perk records its DDC row
 * text and explicit local policy in w321-batch-b.json (scripts/build_perk_batch_b_w321.py). */
public final class PerkBatchBProfile {
    public static final String TARGET_LOCK = "target_lock", ENVIOUS_ASSASSIN = "envious_assassin",
        ENVIOUS_ARSENAL = "envious_arsenal", HARMONY = "harmony", UNDER_OVER = "under_over",
        GOLDEN_TRICORN = "golden_tricorn", LASTING_IMPRESSION = "lasting_impression",
        TIMED_PAYLOAD = "timed_payload", RESERVOIR_BURST = "reservoir_burst",
        EXPLOSIVE_HEAD = "explosive_head", CLUSTER_BOMB = "cluster_bomb", CHAIN_REACTION = "chain_reaction";
    public static final List<String> IDS = List.of(TARGET_LOCK, ENVIOUS_ASSASSIN, ENVIOUS_ARSENAL, HARMONY,
        UNDER_OVER, GOLDEN_TRICORN, LASTING_IMPRESSION, TIMED_PAYLOAD, RESERVOIR_BURST, EXPLOSIVE_HEAD,
        CLUSTER_BOMB, CHAIN_REACTION);
    private static final Map<String, Long> HASHES = Map.ofEntries(
        Map.entry(TARGET_LOCK, 365154968L), Map.entry(ENVIOUS_ASSASSIN, 968510818L),
        Map.entry(ENVIOUS_ARSENAL, 3987942396L), Map.entry(HARMONY, 438098033L),
        Map.entry(UNDER_OVER, 1870851715L), Map.entry(GOLDEN_TRICORN, 2610012052L),
        Map.entry(LASTING_IMPRESSION, 3927722942L), Map.entry(TIMED_PAYLOAD, 1954620775L),
        Map.entry(RESERVOIR_BURST, 1427256713L), Map.entry(EXPLOSIVE_HEAD, 3365897133L),
        Map.entry(CLUSTER_BOMB, 1275731761L), Map.entry(CHAIN_REACTION, 2396489472L));
    /** Family guard: projectile/hitscan mechanics are only wired for these archetypes. */
    private static final Map<String, Set<String>> FAMILIES = Map.of(
        LASTING_IMPRESSION, Set.of("rocket_launcher"), CLUSTER_BOMB, Set.of("rocket_launcher"),
        EXPLOSIVE_HEAD, Set.of("bow"), TIMED_PAYLOAD, Set.of("hand_cannon"), RESERVOIR_BURST, Set.of("fusion_rifle"));
    public record Source(String authority, String url, int row, String text, String htmlSha256) {}
    public record Perk(long hash, String name, String koName, String koDescription, String description,
                       boolean damage, Map<String, Double> mechanics, Source source, String localPolicy) {}
    private record Row(String perk, String id, long hash, int socket, long perkHash, long plugSetHash) {}
    private record Data(String stage, String manifestVersion, Map<String, Perk> perks, List<Row> weapons) {}
    private static final Map<String, Perk> PERKS;
    private static final Map<String, List<WeaponPerks.Roll>> ROLLS;
    static {
        var data = load();
        PERKS = Map.copyOf(data.perks);
        var rolls = new LinkedHashMap<String, List<WeaponPerks.Roll>>();
        for (var id : IDS) rolls.put(id, new ArrayList<>());
        for (var r : data.weapons) rolls.get(r.perk).add(new WeaponPerks.Roll(r.id, r.hash, r.socket, r.perkHash, r.plugSetHash));
        var frozen = new LinkedHashMap<String, List<WeaponPerks.Roll>>();
        rolls.forEach((k, v) -> frozen.put(k, List.copyOf(v)));
        ROLLS = Collections.unmodifiableMap(frozen);
    }
    private PerkBatchBProfile() {}
    private static void check(boolean ok, String what) {
        if (!ok) throw new IllegalStateException("Invalid W321 batch B profile: " + what);
    }
    private static Data load() {
        var stream = PerkBatchBProfile.class.getResourceAsStream("/destiny/weapons/w321-batch-b.json");
        check(stream != null, "missing resource");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            check(d != null && "W321".equals(d.stage) && d.perks != null && d.weapons != null
                && d.perks.keySet().equals(new HashSet<>(IDS)), "header");
            for (var id : IDS) {
                var p = d.perks.get(id);
                check(p.hash == HASHES.get(id) && p.koName != null && !p.koName.isBlank()
                    && p.koDescription != null && p.mechanics != null && !p.mechanics.isEmpty()
                    && p.mechanics.values().stream().allMatch(v -> v != null && Double.isFinite(v) && v >= 0)
                    && p.source != null && p.source.row > 0 && p.source.text != null && !p.source.text.isBlank()
                    && p.localPolicy != null && !p.localPolicy.isBlank(), "perk " + id);
            }
            var seen = new HashSet<String>();
            var perPerk = new HashMap<String, Integer>();
            for (var r : d.weapons) {
                check(r != null && HASHES.containsKey(r.perk) && r.perkHash == HASHES.get(r.perk), "row perk " + r);
                var entry = WeaponCatalog.find(r.id).orElse(null);
                check(entry != null, "unknown weapon " + r.id);
                var c = WeaponCharacteristics.of(entry);
                check(r.hash == c.bungieHash() && !c.exotic() && r.socket >= 0 && r.socket <= 63
                    && r.plugSetHash > 0 && r.plugSetHash <= 0xffffffffL
                    && seen.add(r.perk + ":" + r.id)
                    && (!FAMILIES.containsKey(r.perk) || FAMILIES.get(r.perk).contains(entry.family())), "roll " + r);
                perPerk.merge(r.perk, 1, Integer::sum);
            }
            check(perPerk.keySet().equals(new HashSet<>(IDS)), "every trait has rolls");
            return d;
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static boolean owns(String id) { return id != null && HASHES.containsKey(id); }
    public static List<WeaponPerks.Roll> rolls(String id) { return ROLLS.getOrDefault(id, List.of()); }
    public static Perk perk(String id) { return PERKS.get(id); }
    public static String koName(String id) { var p = PERKS.get(id); return p == null ? id : p.koName(); }
    public static String koDescription(String id) { var p = PERKS.get(id); return p == null ? "" : p.koDescription(); }
    public static boolean damage(String id) { var p = PERKS.get(id); return p != null && p.damage(); }
    public static double value(String id, String key) {
        var v = PERKS.get(id).mechanics().get(key);
        if (v == null) throw new IllegalStateException("Missing W321 mechanic " + id + "." + key);
        return v;
    }
    public static int ticks(String id, String key) { return (int)Math.round(value(id, key)); }
}
