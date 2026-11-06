package kim.biryeong.destiny.weapon;

import net.minecraft.core.component.DataComponents;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;

/**
 * Destiny item lock: a flag on the weapon stack itself, so it travels through the vault, mail and saves. A locked
 * weapon cannot be dismantled or listed on the auction house; everything else (equip, vault, mail) still works.
 */
public final class WeaponLock {
    private static final String TAG = "destiny_locked";
    private WeaponLock() { }

    public static boolean locked(ItemStack stack) {
        var data = stack.get(DataComponents.CUSTOM_DATA);
        return data != null && data.copyTag().getBooleanOr(TAG, false);
    }

    /** Flips the flag in place and returns the new state. */
    public static boolean toggle(ItemStack stack) {
        boolean next = !locked(stack);
        CustomData.update(DataComponents.CUSTOM_DATA, stack, tag -> { if (next) tag.putBoolean(TAG, true); else tag.remove(TAG); });
        return next;
    }
}
