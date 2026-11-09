package kim.biryeong.destiny.weapon;

import com.google.gson.JsonArray;
import com.google.gson.JsonParser;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/**
 * W302 cosmetic weapon skins. A skin replaces only the client-facing geometry, texture, HUD silhouette and name of a
 * catalog weapon; the authoritative item keeps the base entry's ITEM_MODEL, stats, perks, timing and animation
 * routes. Every client route of the base weapon is mirrored at pack time ({@code WeaponSkinAssets}) by replacing the
 * base id token in the route path, so reload/ADS/inspect/first-person-arm graphs stay frame-identical.
 *
 * <p>W325: the Red War common/uncommon/rare weapons from the rip Drive are skins too, each over the catalog weapon with
 * the same D2 frame; their tier comes from {@code /destiny/weapon_skins/w325-registry.json}. A W325 skin is active only
 * when its authored parts json exists.
 */
public final class WeaponSkins {
    public static final String TAG = "destiny_weapon_skin";
    /**
     * @param texture weapon atlas, @param hud ammo-HUD silhouette texture, @param rarity item tier (null: base tier),
     * @param nameKo Korean UI name (Bungie ko manifest), @param bungieHash official item hash (0: none)
     */
    public record Skin(String base, String id, String name, String texture, String hud, WeaponRarity rarity,
                       String nameKo, long bungieHash) {
        public Skin(String base, String id, String name, String texture) {
            this(base, id, name, texture, "destiny:item/hud/w302/ammo_" + id, null, name, 0);
        }
        /** UI name: Korean when known. */
        public String display() { return nameKo == null || nameKo.isBlank() ? name : nameKo; }
    }
    /** Campaign weapons: the user's ripped Khvostov 7G-02 / Stubborn Oak over the catalog row with the same D2 frame
     * (Khvostov: Adaptive 600 RPM auto = gnawing_hunger; Stubborn Oak: Aggressive 55 RPM shotgun = mindbender). */
    public static final List<Skin> ALL = load();
    private static final Map<String, Skin> BY_ID = new HashMap<>();
    static { for (var s : ALL) BY_ID.put(s.id(), s); }
    private WeaponSkins() {}

    private static List<Skin> load() {
        var out = new LinkedHashMap<String, Skin>();
        out.put("khvostov_7g_02", new Skin("gnawing_hunger", "khvostov_7g_02", "Khvostov 7G-02",
                "destiny:item/weapon/w302/khvostov_7g_02", "destiny:item/hud/w302/ammo_khvostov_7g_02",
                WeaponRarity.COMMON, "크보스토브 7G-02", 1619016919L));
        out.put("stubborn_oak", new Skin("mindbender_s_ambition_adept", "stubborn_oak", "Stubborn Oak",
                "destiny:item/weapon/w302/stubborn_oak", "destiny:item/hud/w302/ammo_stubborn_oak",
                WeaponRarity.COMMON, "완고한 떡갈나무", 0));
        try (var in = WeaponSkins.class.getResourceAsStream("/destiny/weapon_skins/w325-registry.json")) {
            if (in != null) {
                JsonArray rows = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonArray();
                for (var el : rows) {
                    var o = el.getAsJsonObject();
                    String id = o.get("id").getAsString(), base = o.get("base").getAsString();
                    var rarity = WeaponRarity.parse(o.get("tier").getAsString()).orElseThrow();
                    long hash = o.get("bungie_hash").getAsLong();
                    String ko = o.get("name_ko").getAsString();
                    if (out.containsKey(id)) {   // a W302 skin reused by the registry: keep its assets, take tier/name
                        var s = out.get(id);
                        out.put(id, new Skin(s.base(), id, s.name(), s.texture(), s.hud(), rarity, ko, hash));
                        continue;
                    }
                    if (WeaponSkins.class.getResource("/destiny/weapon_skins/" + id + ".json") == null) continue;
                    if (WeaponCatalog.find(base).isEmpty()) throw new IllegalStateException("W325 skin " + id + " has unknown base " + base);
                    out.put(id, new Skin(base, id, o.get("name").getAsString(), "destiny:item/weapon/w325/" + id,
                            "destiny:item/hud/w325/ammo_" + id, rarity, ko, hash));
                }
            }
        } catch (java.io.IOException e) { throw new IllegalStateException("Unreadable W325 registry", e); }
        for (String id : LegendaryWeapons.ids()) {
            var catalog = LegendaryWeapons.field(id, "catalog");
            var meta = LegendaryWeapons.field(id, "characteristics");
            var skin = new Skin(LegendaryWeapons.baseId(id), id, catalog.get("name").getAsString(),
                    "destiny:item/weapon/w327/" + id, "destiny:item/hud/w327/ammo_" + id,
                    WeaponRarity.LEGENDARY, LegendaryWeapons.name(id), meta.get("bungieHash").getAsLong());
            if (out.putIfAbsent(id, skin) != null) throw new IllegalStateException("Duplicate legendary skin " + id);
        }
        return List.copyOf(out.values());
    }

    public static Optional<Skin> find(String id) { return Optional.ofNullable(BY_ID.get(id)); }

    /** Skins of a tier, in registry order. */
    public static List<Skin> ofRarity(WeaponRarity rarity) {
        var out = new ArrayList<Skin>();
        for (var s : ALL) if (s.rarity() == rarity && !LegendaryWeapons.contains(s.id())) out.add(s);
        return out;
    }

    /** The skin only applies to the weapon it was authored for. */
    public static Optional<Skin> of(ItemStack stack) {
        var identity = WeaponModels.entry(stack);
        if (identity.isPresent() && LegendaryWeapons.contains(identity.get().id())) return find(identity.get().id());
        var data = stack.get(DataComponents.CUSTOM_DATA);
        if (data == null) return Optional.empty();
        var skin = data.copyTag().getString(TAG).flatMap(WeaponSkins::find);
        if (skin.isEmpty()) return skin;
        if (LegendaryWeapons.contains(skin.get().id())) return Optional.empty();
        return WeaponModels.entry(stack).filter(e -> e.id().equals(skin.get().base())).isPresent() ? skin : Optional.empty();
    }

    public static void apply(ItemStack stack, String skinId) {
        var skin = find(skinId).orElseThrow(() -> new IllegalArgumentException("Unknown weapon skin " + skinId));
        var entry = WeaponModels.entry(stack).orElseThrow();
        if (LegendaryWeapons.contains(skinId)) {
            if (!entry.id().equals(skinId)) throw new IllegalArgumentException("Legendary identity is not a cosmetic skin: " + skinId);
            return;
        }
        if (!entry.id().equals(skin.base())) throw new IllegalArgumentException(skinId + " is not a skin of " + entry.id());
        var data = stack.get(DataComponents.CUSTOM_DATA);
        CompoundTag tag = data == null ? new CompoundTag() : data.copyTag();
        tag.putString(TAG, skin.id());
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        String name = WeaponItems.entry(stack).isPresent() ? "[전투] " + skin.display() : skin.display();
        int color = skin.rarity() == null ? 0xFFAA00 : skin.rarity().color();
        stack.set(DataComponents.ITEM_NAME, net.minecraft.network.chat.Component.literal(name)
                .withStyle(s -> s.withColor(color)));
    }

    /** Swap the base id token of a client route. Unknown/foreign routes stay unchanged. */
    public static Identifier route(Skin skin, Identifier route) {
        if (route == null || !route.getNamespace().equals("destiny")) return route;
        String path = rename(skin, route.getPath());
        return path.equals(route.getPath()) ? route : Identifier.fromNamespaceAndPath("destiny", path);
    }

    public static Identifier route(ItemStack stack, Identifier route) {
        var skin = of(stack);
        return skin.isPresent() ? route(skin.get(), route) : route;
    }

    /** Token replacement on path segments: "halfdan_d", "halfdan_d_*", "*_halfdan_d" — never a substring of another id. */
    public static String rename(Skin skin, String path) {
        return path.replaceAll("(?<![a-z0-9])" + java.util.regex.Pattern.quote(skin.base()) + "(?![a-z0-9])", skin.id());
    }

    /** Pack roots of all skins, derived from the base weapon's active roots. */
    public static Set<Identifier> roots(Set<Identifier> baseRoots) {
        var out = new java.util.HashSet<Identifier>();
        for (var skin : ALL) for (var root : baseRoots) {
            var r = route(skin, root);
            if (!r.equals(root)) out.add(r);
        }
        return out;
    }

    public static String hudIcon(ItemStack stack, WeaponCatalog.Entry entry) {
        return "ammo_weapon_w112_" + of(stack).map(Skin::id).orElse(entry.id());
    }
}
