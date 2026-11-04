package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** Pure live held-source query. No proc, item mutation, attachment creation or AA simulation. */
public final class WeaponIronGaze {
    private WeaponIronGaze() {}
    private static boolean held(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()
            || AbilityService.inSuper(p) || !WeaponLoadout.canUse(p)) return false;
        ItemStack stack = p.getMainHandItem();
        if (stack == null || stack.isEmpty() || stack.getCount() != 1) return false;
        int occurrences = 0, slot = -1;
        for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
            if (p.getInventory().getItem(i) == stack) { occurrences++; slot = i; }
        }
        if (occurrences != 1 || slot < 0 || slot >= 9 || slot != p.getInventory().getSelectedSlot()
            || (WeaponLoadout.enabled(p) && WeaponLoadout.equipped(p).stream().noneMatch(e -> e.stack() == stack)))
            return false;
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, IronGazeProfile.ID).orElse(null);
        return IronGazeProfile.supports(entry) && roll != null && IronGazeProfile.rolls().contains(roll)
            && entry.id().equals(roll.id());
    }
    /** Master adds this signed bonus to the existing raw Range sum before its single clamp. */
    public static int rangeBonus(ServerPlayer p) { return held(p) ? IronGazeProfile.rangeBonus() : 0; }
}
