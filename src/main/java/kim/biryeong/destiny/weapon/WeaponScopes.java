package kim.biryeong.destiny.weapon;

import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;

import java.util.Set;

/** W45 packet routing: sniper first-person hides the gun; LFR retains a source-cloned 3D gun.
 * Never changes the real stack's model or grip; non-first-person views retain original ADS models.
 */
public final class WeaponScopes {
    private static final Set<String> IDS = Set.of(
            "bite_of_the_fox", "beloved", "apostate", "line_in_the_sand", "stormchaser",
            "izanagis_burden");

    private WeaponScopes() {}

    public static boolean supports(WeaponCatalog.Entry entry) {
        entry = LegendaryWeapons.base(entry);
        return entry != null && IDS.contains(entry.id())
                && (!"izanagis_burden".equals(entry.id()) || WeaponExotics.izanagi(entry));
    }

    /** Call only for supported entries from the live stack's Polymer model getter. */
    public static Identifier model(WeaponCatalog.Entry entry) {
        entry = LegendaryWeapons.base(entry);
        if (!supports(entry)) throw new IllegalArgumentException("Weapon has no W45 scope: " + entry);
        return Identifier.fromNamespaceAndPath("destiny", "weapon_scope_w45/" + entry.id());
    }

    /** Pose string index 0 is independent of the existing grip flag at boolean index 0. */
    public static boolean scoped(ItemStack stack) {
        var data = stack.get(DataComponents.CUSTOM_MODEL_DATA);
        return data != null && "scope".equals(data.getString(0))
                && WeaponItems.entry(stack).filter(WeaponScopes::supports).isPresent();
    }
}
