package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Pinned base Trait557221067, exact Fixed Odds socket4; enhanced magazine stat excluded. */
public final class KillingTallyProfile {
    public static final String ID = "killing_tally";
    public static final long HASH = 557221067L;
    public record Perk(String id, long hash, int maxStacks, List<Float> pveMultipliers,
                       List<Float> pvpMultipliers, boolean clearsOnStow, boolean clearsOnReload) {
        public Perk { pveMultipliers = List.copyOf(pveMultipliers); pvpMultipliers = List.copyOf(pvpMultipliers); }
    }
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Data DATA = load();
    private KillingTallyProfile() {}
    private static void check(boolean ok) {
        if (!ok) throw new IllegalStateException("Invalid W194 Killing Tally profile");
    }
    private static Data load() {
        var stream = KillingTallyProfile.class.getResourceAsStream("/destiny/weapons/w194-killing-tally.json");
        check(stream != null);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            check(d != null && "W194".equals(d.stage) && d.perk != null
                && ID.equals(d.perk.id) && d.perk.hash == HASH && d.perk.maxStacks == 3
                && d.perk.clearsOnStow && d.perk.clearsOnReload
                && d.perk.pveMultipliers.equals(List.of(1f, 1.1f, 1.2f, 1.3f))
                && d.perk.pvpMultipliers.equals(List.of(1f, 1.05f, 1.1f, 1.15f))
                && List.of(new WeaponPerks.Roll("fixed_odds", 2194955522L, 4, HASH, 1686775256L)).equals(d.weapons));
            return new Data(d.stage, d.perk, List.copyOf(d.weapons));
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static Perk perk() { return DATA.perk; }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id())
                && r.hash() == WeaponCharacteristics.of(entry).bungieHash());
    }
    public static float multiplier(int stacks, boolean pvp) {
        if (stacks < 0 || stacks > DATA.perk.maxStacks) throw new IllegalArgumentException("Invalid KT stacks");
        return (pvp ? DATA.perk.pvpMultipliers : DATA.perk.pveMultipliers).get(stacks);
    }
}
