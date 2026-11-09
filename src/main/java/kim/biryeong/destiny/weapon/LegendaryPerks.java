package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact base-trait socket additions; unsupported manifest options are not exposed to random rolls. */
public final class LegendaryPerks {
    public record Trait(String id, long hash, String name, String description, boolean damage, boolean added,
                        List<WeaponPerks.Roll> rolls) {}
    private record Data(List<Trait> traits) {}
    private static final Map<String, Trait> TRAITS = load();
    private LegendaryPerks() {}
    private static Map<String, Trait> load() {
        var in = LegendaryPerks.class.getResourceAsStream("/destiny/weapons/w327-traits.json");
        if (in == null) throw new IllegalStateException("Missing legendary trait pools");
        try (var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class); var out = new LinkedHashMap<String, Trait>();
            for (var t : d.traits) {
                if (t.id == null || t.hash <= 0 || t.rolls == null || t.name == null || out.putIfAbsent(t.id,t) != null)
                    throw new IllegalStateException("Invalid additional trait " + t);
                var keys = new HashSet<String>();
                for (var r : t.rolls) if (!LegendaryWeapons.exactRoll(r) || r.perkHash() != t.hash
                        || r.socket() < 0 || r.socket() > 63 || r.plugSetHash() <= 0 || !keys.add(r.id()+":"+r.socket()))
                    throw new IllegalStateException("Invalid additional socket " + r);
            }
            return Collections.unmodifiableMap(out);
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static Trait trait(String id) { return TRAITS.get(id); }
    public static List<String> addedIds() { return TRAITS.values().stream().filter(Trait::added).map(Trait::id).toList(); }
    public static List<WeaponPerks.Roll> extraRolls(String id) { var t = TRAITS.get(id); return t == null ? List.of() : t.rolls; }
    public static List<WeaponPerks.Roll> expandRolls(String id, List<WeaponPerks.Roll> legacy) {
        var out = new LinkedHashSet<>(legacy); out.addAll(extraRolls(id)); return List.copyOf(out);
    }
}
