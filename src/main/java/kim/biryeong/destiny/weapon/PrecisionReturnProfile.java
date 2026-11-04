package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact base Triple Tap/FTTC sockets; enhanced and catalyst behavior is deliberately separate. */
public final class PrecisionReturnProfile {
    public static final String TRIPLE_TAP = "triple_tap", FOURTH_TIMES = "fourth_times_the_charm";
    public record Perk(String id, long hash, int hits, int returnRounds, int windowTicks,
                       List<WeaponPerks.Roll> weapons) {
        public Perk { weapons = List.copyOf(weapons); }
    }
    private record Data(String stage, List<Perk> perks) {}
    private static final List<Perk> PERKS = load();
    private PrecisionReturnProfile() {}
    private static List<Perk> load() {
        var input = PrecisionReturnProfile.class.getResourceAsStream("/destiny/weapons/w67-precision-return.json");
        if (input == null) throw new IllegalStateException("Missing W67 precision-return data");
        try (var reader = new InputStreamReader(input, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            if (d == null || !"W67".equals(d.stage) || d.perks == null || d.perks.size() != 2)
                throw new IllegalStateException("Invalid W67 precision-return profile");
            var ids = new HashSet<String>();
            for (var p : d.perks) {
                boolean triple = TRIPLE_TAP.equals(p.id);
                if (!(triple || FOURTH_TIMES.equals(p.id)) || !ids.add(p.id)
                        || p.hash != (triple ? 3400784728L : 1354429876L)
                        || p.hits != (triple ? 3 : 4) || p.returnRounds != (triple ? 1 : 2)
                        || p.windowTicks != 40 || p.weapons.isEmpty())
                    throw new IllegalStateException("Invalid precision-return trait " + p.id);
                var seen = new HashSet<String>();
                for (var r : p.weapons) {
                    var e = WeaponCatalog.find(r.id()).orElseThrow();
                    if (r.hash() != WeaponCharacteristics.of(e).bungieHash() || r.perkHash() != p.hash
                            || r.socket() < 0 || r.socket() > 63 || r.plugSetHash() <= 0
                            || WeaponCharacteristics.of(e).exotic() || !seen.add(r.id() + ":" + r.socket()))
                        throw new IllegalStateException("Invalid precision-return socket " + r);
                }
            }
            return List.copyOf(d.perks);
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static List<Perk> perks() { return PERKS; }
    public static Optional<Perk> find(String id) { return PERKS.stream().filter(p -> p.id.equals(id)).findFirst(); }
    public static List<WeaponPerks.Roll> rolls(String id) { return find(id).map(Perk::weapons).orElse(List.of()); }
}
