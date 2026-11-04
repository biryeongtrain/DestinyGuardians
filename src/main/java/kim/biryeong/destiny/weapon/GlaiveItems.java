package kim.biryeong.destiny.weapon;

import net.minecraft.core.component.DataComponents;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;

/** Shield energy belongs to the original live item, never a player-global or copied reserve. */
public final class GlaiveItems {
    public static final String ENERGY="destiny_glaive_energy";
    private GlaiveItems() {}
    public static boolean isGlaive(ItemStack stack) {
        return WeaponItems.entry(stack).filter(e->e.family().equals("glaive")).isPresent();
    }
    public static int energy(ItemStack stack) {
        if(!isGlaive(stack))return 0;
        var data=stack.get(DataComponents.CUSTOM_DATA);
        return data==null?0:Math.clamp(data.copyTag().getIntOr(ENERGY,0),0,GlaiveCycle.CAPACITY);
    }
    public static void saveEnergy(ItemStack stack,int amount) {
        if(!isGlaive(stack))return;
        amount=Math.clamp(amount,0,GlaiveCycle.CAPACITY);
        if(energy(stack)==amount)return;
        var tag=stack.get(DataComponents.CUSTOM_DATA).copyTag();tag.putInt(ENERGY,amount);
        stack.set(DataComponents.CUSTOM_DATA,CustomData.of(tag));
    }
}
