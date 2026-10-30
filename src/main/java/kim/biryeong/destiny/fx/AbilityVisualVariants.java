package kim.biryeong.destiny.fx;

import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;

/** Presentation-only choices used by the Crucible per-viewer team resolver. */
public final class AbilityVisualVariants {
    private AbilityVisualVariants() { }

    /** Returns a separate stack only when a packaged enemy variant exists. Alpha/UV live in its asset. */
    public static ItemStack item(ItemStack original, boolean hostile) {
        if (!hostile || original.isEmpty()) return original;
        Identifier model = original.get(DataComponents.ITEM_MODEL);
        if (model == null || !model.getNamespace().equals("destiny") || model.getPath().endsWith("_enemy")) return original;
        Identifier enemy = Identifier.fromNamespaceAndPath(model.getNamespace(), model.getPath() + "_enemy");
        if (AbilityVisualVariants.class.getResource("/assets/destiny/items/" + enemy.getPath() + ".json") == null) return original;
        ItemStack copy = original.copy();
        copy.set(DataComponents.ITEM_MODEL, enemy);
        return copy;
    }

    /** BetterModel enemy assets are installed alongside originals, never by recoloring a shared tracker. */
    public static String model(String original, boolean hostile) {
        if (!hostile || original.endsWith("_enemy")) return original;
        String enemy = original + "_enemy";
        return AbilityVisualVariants.class.getResource("/destiny/vfx/" + enemy + ".bbmodel") == null ? original : enemy;
    }
}
