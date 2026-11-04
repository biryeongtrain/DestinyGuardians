package kim.biryeong.destiny.weapon;

import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/**
 * W302 cosmetic weapon skins. A skin replaces only the client-facing geometry, texture, HUD silhouette and name of a
 * catalog weapon; the authoritative item keeps the base entry's ITEM_MODEL, stats, perks, timing and animation
 * routes. Every client route of the base weapon is mirrored at pack time ({@code WeaponSkinAssets}) by replacing the
 * base id token in the route path, so reload/ADS/inspect/first-person-arm graphs stay frame-identical.
 */
public final class WeaponSkins {
    public static final String TAG = "destiny_weapon_skin";
    public record Skin(String base, String id, String name, String texture) {}
    /** Campaign weapons: the user's ripped Khvostov 7G-02 / Stubborn Oak over the catalog row with the same D2 frame
     * (Khvostov: Adaptive 600 RPM auto = gnawing_hunger; Stubborn Oak: Aggressive 55 RPM shotgun = mindbender). */
    public static final List<Skin> ALL = List.of(
            new Skin("gnawing_hunger", "khvostov_7g_02", "Khvostov 7G-02", "destiny:item/weapon/w302/khvostov_7g_02"),
            new Skin("mindbender_s_ambition_adept", "stubborn_oak", "Stubborn Oak", "destiny:item/weapon/w302/stubborn_oak"));
    private static final Map<String, Skin> BY_ID = new HashMap<>();
    static { for (var s : ALL) BY_ID.put(s.id(), s); }
    private WeaponSkins() {}

    public static Optional<Skin> find(String id) { return Optional.ofNullable(BY_ID.get(id)); }

    /** The skin only applies to the weapon it was authored for. */
    public static Optional<Skin> of(ItemStack stack) {
        var data = stack.get(DataComponents.CUSTOM_DATA);
        if (data == null) return Optional.empty();
        var skin = data.copyTag().getString(TAG).flatMap(WeaponSkins::find);
        if (skin.isEmpty()) return skin;
        return WeaponModels.entry(stack).filter(e -> e.id().equals(skin.get().base())).isPresent() ? skin : Optional.empty();
    }

    public static void apply(ItemStack stack, String skinId) {
        var skin = find(skinId).orElseThrow(() -> new IllegalArgumentException("Unknown weapon skin " + skinId));
        var entry = WeaponModels.entry(stack).orElseThrow();
        if (!entry.id().equals(skin.base())) throw new IllegalArgumentException(skinId + " is not a skin of " + entry.id());
        var data = stack.get(DataComponents.CUSTOM_DATA);
        CompoundTag tag = data == null ? new CompoundTag() : data.copyTag();
        tag.putString(TAG, skin.id());
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        String name = WeaponItems.entry(stack).isPresent() ? "[전투] " + skin.name() : skin.name();
        stack.set(DataComponents.ITEM_NAME, net.minecraft.network.chat.Component.literal(name)
                .withStyle(net.minecraft.ChatFormatting.GOLD));
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
