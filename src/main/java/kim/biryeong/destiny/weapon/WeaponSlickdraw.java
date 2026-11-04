package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** Stateless live ownership authority. No selection hook, cached incoming stack or stored proc. */
public final class WeaponSlickdraw {
    private WeaponSlickdraw() {}
    private static boolean ownerValid(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
            && !AbilityService.inSuper(p);
    }
    /** Count-one original reference, uniquely present in the actual inventory, in a usable hotbar slot. */
    private static int ownedSlot(ServerPlayer p, ItemStack stack) {
        if (stack == null || stack.isEmpty() || stack.getCount() != 1) return -1;
        int occurrences = 0, slot = -1;
        for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
            if (p.getInventory().getItem(i) == stack) { occurrences++; slot = i; }
        }
        if (occurrences != 1 || slot < 0 || slot >= 9) return -1;
        return !WeaponLoadout.enabled(p) || WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == stack)
            ? slot : -1;
    }
    private static WeaponCatalog.Entry source(ServerPlayer p, ItemStack stack, boolean incomingAllowed) {
        if (!ownerValid(p)) return null;
        int slot = ownedSlot(p, stack);
        if (slot < 0) return null;
        boolean held = p.getMainHandItem() == stack && p.getInventory().getSelectedSlot() == slot
            && WeaponLoadout.canUse(p);
        // Master passes the real desired item before vanilla changes selection for ready only.
        boolean incoming = incomingAllowed && slot != p.getInventory().getSelectedSlot()
            && p.getMainHandItem() != stack;
        if (!held && !incoming) return null;
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, SlickdrawProfile.ID).orElse(null);
        return SlickdrawProfile.supports(entry) && roll != null && SlickdrawProfile.rolls().contains(roll)
            && entry.id().equals(roll.id()) ? entry : null;
    }
    /** Master wraps outermost. Ready permits owned incoming; stow requires current selected source. */
    public static int handlingTicks(ServerPlayer p, ItemStack stack, boolean ready, int base) {
        var entry = source(p, stack, ready);
        return entry == null ? base : SlickdrawProfile.handlingTicks(entry, ready);
    }
    /** Held source only, on both transitions. entering does not introduce an ADS scalar. */
    public static int adsTicks(ServerPlayer p, WeaponCatalog.Entry entry, int base, boolean entering) {
        if (p == null || entry == null) return base;
        var held = source(p, p.getMainHandItem(), false);
        return entry.equals(held) ? SlickdrawProfile.adsTicks(entry) : base;
    }
}
