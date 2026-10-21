package kim.biryeong.destiny.ability.hunter;

import kim.biryeong.destiny.guardian.Element;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/** Fresh resource-pack visuals for hunter grenades and thrown melee abilities. */
public final class HunterAbilityVisuals {
    private HunterAbilityVisuals() {
    }

    public static ItemStack grenade(Element element) {
        return item(switch (element) {
            case ARC -> HunterAbilities.ARC_FLASHBANG;
            case SOLAR -> HunterAbilities.SOLAR_INCENDIARY;
            default -> HunterAbilities.VOID_VORTEX;
        });
    }

    /** Combination blow is unarmed and has no projectile visual. */
    public static ItemStack melee(Element element) {
        return switch (element) {
            case ARC -> ItemStack.EMPTY;
            case SOLAR -> item(HunterAbilities.SOLAR_KNIFE);
            default -> item(HunterAbilities.VOID_SMOKE_BOMB);
        };
    }

    private static ItemStack item(Identifier model) {
        ItemStack stack = new ItemStack(Items.PAPER);
        stack.set(DataComponents.ITEM_MODEL, model);
        return stack;
    }
}
