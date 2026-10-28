package kim.biryeong.destiny.weapon;

import net.minecraft.core.component.DataComponents;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;

/** W51 item-owned energy and remaining held-time recharge delay; no offline/stowed catch-up. */
public final class SwordItems {
    public static final String ENERGY = "destiny_sword_energy", DELAY = "destiny_sword_recharge_delay";
    private SwordItems() {}
    public static boolean isSword(ItemStack stack) {
        return WeaponItems.entry(stack).filter(e -> e.family().equals("sword")).isPresent();
    }
    public static int energy(ItemStack stack) {
        if (!isSword(stack)) return 0;
        return Math.clamp(stack.get(DataComponents.CUSTOM_DATA).copyTag().getIntOr(ENERGY,0),0,SwordCycle.CAPACITY);
    }
    public static int delay(ItemStack stack) {
        if (!isSword(stack)) return 0;
        return Math.clamp(stack.get(DataComponents.CUSTOM_DATA).copyTag().getIntOr(DELAY,0),0,SwordCycle.RECHARGE_DELAY);
    }
    public static void save(ItemStack stack, int energy, int delay) {
        if (!isSword(stack)) return;
        energy = Math.clamp(energy,0,SwordCycle.CAPACITY);
        delay = Math.clamp(delay,0,SwordCycle.RECHARGE_DELAY);
        if (energy(stack) == energy && delay(stack) == delay) return;
        var tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putInt(ENERGY,energy); tag.putInt(DELAY,delay);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
    }
}
