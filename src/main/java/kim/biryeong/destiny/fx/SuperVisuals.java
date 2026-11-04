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
            case ARC -> "arc_staff_h28";
            case SOLAR -> "golden_gun_h29";
            default -> "shadow_bow_h28_drawn";
        };
        stack.set(DataComponents.ITEM_MODEL, DestinyGuardians.id(name));
        return stack;
    }

    public static ItemStack drawnBow() {
        ItemStack stack = new ItemStack(Items.STICK);
        stack.set(DataComponents.ITEM_MODEL, DestinyGuardians.id("shadow_bow_h28_drawn"));
        return stack;
    }

    public static ItemStack bowStage(int stage) {
        if (stage < 0 || stage > 3) throw new IllegalArgumentException("Unknown H20 draw stage");
        // H22: the user chose a visibly taut bow from ready, rather than a brief stage swap.
        return drawnBow();
    }

    /** Release removes the nocked arrow and relaxes the string during follow-through. */
    public static ItemStack releasedBow() {
        ItemStack stack = new ItemStack(Items.STICK);
        stack.set(DataComponents.ITEM_MODEL, DestinyGuardians.id("shadow_bow_h28"));
        return stack;
    }
}
