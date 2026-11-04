package kim.biryeong.destiny.inventory.gear;

import com.google.gson.Gson;
import kim.biryeong.destiny.guardian.GuardianClass;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.Optional;

/**
 * Display-only sample gear from the extracted Destiny character screen (one legendary armour set per class and a
 * ghost shell) plus original Korean weapon flavour text by Bungie hash. Armour has no gameplay effect yet.
 */
public final class GearSamples {
    public record Item(String name, String type, String flavour, String rarity, String icon, long hash) { }
    private record Data(Map<String, Map<String, Item>> armor, Item ghost, Map<String, String> weaponFlavour) { }
    private static final Data DATA = load();

    private GearSamples() { }

    private static Data load() {
        var in = GearSamples.class.getResourceAsStream("/destiny/gear/samples-ko.json");
        if (in == null) throw new IllegalStateException("Missing gear samples");
        try (var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
            return new Gson().fromJson(reader, Data.class);
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }

    /** The armour piece shown in {@code slot} for a class; empty for NONE or non-armour slots. */
    public static Optional<Item> armor(GuardianClass cls, GearSlot slot) {
        if (cls == null || cls == GuardianClass.NONE || !slot.armor()) return Optional.empty();
        var set = DATA.armor().get(cls.name());
        return set == null ? Optional.empty() : Optional.ofNullable(set.get(slot.name()));
    }

    public static Item ghost() { return DATA.ghost(); }

    public static String flavour(long bungieHash) { return DATA.weaponFlavour().getOrDefault(Long.toString(bungieHash), ""); }
}
