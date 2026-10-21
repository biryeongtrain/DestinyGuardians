package kim.biryeong.destiny.fx;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.guardian.Element;
import net.minecraft.core.component.DataComponents;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/** Resource-pack item models, carried by vanilla stacks (no client registry required). */
public final class SuperVisuals {
    private SuperVisuals() { }

    public static ItemStack item(Element element) {
        ItemStack stack = new ItemStack(Items.STICK);
        String name = switch (element) {
            case ARC -> "arc_staff";
            case SOLAR -> "golden_gun";
            default -> "shadow_bow";
        };
        stack.set(DataComponents.ITEM_MODEL, DestinyGuardians.id(name));
        return stack;
    }
}
