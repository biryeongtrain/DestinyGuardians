package kim.biryeong.destiny.inventory.gear;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * Official Bungie manifest icons imported as HUD sprites (scripts/gear/import_bungie_icons.py). Values are
 * HUD icon names for {@link kim.biryeong.destiny.inventory.HudPainter#icon}; anything missing falls back to the
 * caller's own presentation (the weapon's GUI model, a dot for perks).
 */
public final class GearIcons {
    private static final Map<String, String> WEAPONS = new HashMap<>(), PERKS = new HashMap<>(), ENGRAMS = new HashMap<>();
    static {
        var in = GearIcons.class.getResourceAsStream("/destiny/gear/bungie-icons.json");
        if (in != null) try (var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            read(root, "weapons", WEAPONS); read(root, "perks", PERKS); read(root, "engrams", ENGRAMS);
        } catch (java.io.IOException | RuntimeException e) { throw new IllegalStateException("Unreadable bungie-icons.json", e); }
    }
    private GearIcons() { }

    private static void read(JsonObject root, String key, Map<String, String> into) {
        if (!root.has(key)) return;
        for (var e : root.getAsJsonObject(key).entrySet())
            into.put(e.getKey(), e.getValue().getAsJsonObject().get("icon").getAsString());
    }

    public static Optional<String> weapon(String weaponId) { return Optional.ofNullable(WEAPONS.get(weaponId)); }
    public static Optional<String> perk(long perkHash) { return Optional.ofNullable(PERKS.get(Long.toString(perkHash))); }
    /** {@code legendary}, {@code exotic}, {@code rare} or {@code prime}. */
    public static Optional<String> engram(String tier) { return Optional.ofNullable(ENGRAMS.get(tier)); }
}
