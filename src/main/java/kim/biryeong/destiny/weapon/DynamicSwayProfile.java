package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Pinned W195 base Trait only; exact canonical pools, enhanced/exotic/default selection excluded. */
public final class DynamicSwayProfile {
    public static final String ID = "dynamic_sway_reduction";
    public static final long HASH = 1359896290L;
    public record Perk(String id, long hash, int maxStacks, int stabilityPerShot, float growthReductionPerShot,
                       String intermediateAccuracyConeSize, float maximumAccuracyScalar, boolean requiresHeldTrigger) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Data DATA = load();
    private DynamicSwayProfile() {}
    private static void check(boolean ok) {
        if (!ok) throw new IllegalStateException("Invalid W195 DynamicSway profile");
    }
    private static Data load() {
        var stream = DynamicSwayProfile.class.getResourceAsStream("/destiny/weapons/w195-dynamic-sway.json");
        check(stream != null);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            check(d != null && "W195".equals(d.stage) && d.perk != null
                && ID.equals(d.perk.id) && d.perk.hash == HASH
                && d.perk.maxStacks == 10 && d.perk.stabilityPerShot == 1
                && d.perk.growthReductionPerShot == 0.1f && "?".equals(d.perk.intermediateAccuracyConeSize)
                && d.perk.maximumAccuracyScalar == 0f && d.perk.requiresHeldTrigger
                && List.of(new WeaponPerks.Roll("ammit_ar2", 2119346509L, 3, HASH, 1723759242L),
                    new WeaponPerks.Roll("hammerhead", 603242241L, 3, HASH, 2515290473L)).equals(d.weapons));
            return new Data(d.stage, d.perk, List.copyOf(d.weapons));
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static Perk perk() { return DATA.perk; }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && !WeaponCharacteristics.of(entry).exotic()
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id())
                && r.hash() == WeaponCharacteristics.of(entry).bungieHash());
    }
    public static int maxStacks() { return DATA.perk.maxStacks; }
    public static int stabilityBonus(int stacks) { return bounded(stacks) * DATA.perk.stabilityPerShot; }
    public static float growthScalar(int stacks) { return Math.max(0f, 1f - bounded(stacks) * DATA.perk.growthReductionPerShot); }
    /** Intermediate DDC cone size is UNKNOWN: preserve incoming cone until explicit no-spread maximum. */
    public static float accuracyScalar(int stacks) { return bounded(stacks) == maxStacks() ? DATA.perk.maximumAccuracyScalar : 1f; }
    private static int bounded(int stacks) { return Math.max(0, Math.min(maxStacks(), stacks)); }
}
