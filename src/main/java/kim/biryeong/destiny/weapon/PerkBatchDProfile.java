package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** W323 batch D trait pools and DDC PvE base values. JSON-only; see scripts/build_batch_d_w323.py. */
public final class PerkBatchDProfile {
    public static final String TURNABOUT = "turnabout", COUNTERATTACK = "counterattack", FLASH_COUNTER = "flash_counter",
            TILTING = "tilting_at_windmills", VALIANT_CHARGE = "valiant_charge", DUELISTS_TRANCE = "duelists_trance",
            COLD_STEEL = "cold_steel", UNSTOPPABLE_FORCE = "unstoppable_force", MASTER_OF_ARMS = "master_of_arms";
    public static final List<String> IDS = List.of(TURNABOUT, COUNTERATTACK, FLASH_COUNTER, TILTING, VALIANT_CHARGE,
            DUELISTS_TRANCE, COLD_STEEL, UNSTOPPABLE_FORCE, MASTER_OF_ARMS);
    private static final Map<String, String> FAMILY = Map.of(COUNTERATTACK, "sword", FLASH_COUNTER, "sword",
            VALIANT_CHARGE, "sword", DUELISTS_TRANCE, "sword", COLD_STEEL, "sword",
            TILTING, "glaive", UNSTOPPABLE_FORCE, "glaive");
    private record Perk(String id, String name, long hash, int ddcRow, String ddc, JsonObject values,
                        String localPolicy, List<WeaponPerks.Roll> rolls) {}
    private record Data(String stage, String manifestVersion, List<Perk> perks) {}
    private static final Map<String, Perk> PERKS = load();
    private PerkBatchDProfile() {}

    private static void check(boolean valid, String reason) {
        if (!valid) throw new IllegalStateException("Invalid W323 batch D: " + reason);
    }
    private static Map<String, Perk> load() {
        var stream = PerkBatchDProfile.class.getResourceAsStream("/destiny/weapons/w323-batch-d.json");
        check(stream != null, "missing resource");
        Data d;
        try (stream) { d = new Gson().fromJson(new String(stream.readAllBytes(), StandardCharsets.UTF_8), Data.class); }
        catch (IOException e) { throw new IllegalStateException(e); }
        check(d != null && "W323".equals(d.stage) && d.perks != null, "stage");
        var map = new LinkedHashMap<String, Perk>();
        for (var p : d.perks) {
            check(p != null && IDS.contains(p.id) && p.values != null && p.rolls != null && !p.rolls.isEmpty()
                    && map.putIfAbsent(p.id, p) == null, "perk " + (p == null ? null : p.id));
            var sockets = new HashSet<String>();
            for (var r : p.rolls) {
                var entry = WeaponCatalog.find(r.id()).orElse(null);
                check(entry != null && r.hash() == WeaponCharacteristics.of(entry).bungieHash() && r.perkHash() == p.hash
                        && r.socket() >= 0 && r.socket() <= 63 && r.plugSetHash() > 0 && sockets.add(r.id() + ":" + r.socket())
                        && (!FAMILY.containsKey(p.id) || FAMILY.get(p.id).equals(entry.family())), "roll " + r);
            }
        }
        check(map.keySet().equals(new HashSet<>(IDS)), "complete perk set");
        return Map.copyOf(map);
    }
    public static boolean owns(String id) { return id != null && PERKS.containsKey(id); }
    public static List<WeaponPerks.Roll> rolls(String id) { var p = PERKS.get(id); return p == null ? List.of() : List.copyOf(p.rolls); }
    public static String name(String id) { var p = PERKS.get(id); return p == null ? id : p.name; }
    public static long hash(String id) { return PERKS.get(id).hash; }
    public static double value(String id, String key) {
        var p = PERKS.get(id);
        check(p != null && p.values.has(key), id + "." + key);
        return p.values.get(key).getAsDouble();
    }
    public static int ticks(String id, String key) { return (int) value(id, key); }
}
