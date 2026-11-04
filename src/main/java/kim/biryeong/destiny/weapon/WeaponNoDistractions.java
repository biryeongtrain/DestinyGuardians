package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.Guardians;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** Pure held-source queries; no second clock, resistance multiplier, attachments or retained owners. */
public final class WeaponNoDistractions {
    private WeaponNoDistractions() {}

    /** Current usable canonical weapon, independently of whether this trait is selected. */
    public static boolean eligible(ServerPlayer player, ItemStack stack) {
        if (player == null || stack == null || !player.isAlive() || player.isRemoved()
                || player.isSpectator() || player.hasDisconnected()
                || Guardians.runtimeIfPresent(player).map(r -> r.superSession != null).orElse(false)
                || !WeaponLoadout.canUse(player)) return false;
        int slot = player.getInventory().getSelectedSlot();
        return slot >= 0 && slot < 9 && player.getMainHandItem() == stack
            && player.getInventory().getItem(slot) == stack && stack.getCount() == 1
            && WeaponItems.entry(stack).filter(NoDistractionsProfile::supports).isPresent();
    }

    /** Exact actual held object and exact allowed base hash/socket/weapon/plug-set tuple. */
    public static boolean selected(ServerPlayer player, ItemStack stack) {
        if (!eligible(player, stack)) return false;
        var entry = WeaponItems.entry(stack).orElseThrow();
        return WeaponPerks.selected(stack, NoDistractionsProfile.ID)
            .filter(r -> r.id().equals(entry.id()) && NoDistractionsProfile.rolls().contains(r)).isPresent();
    }

    public static boolean selected(ServerPlayer player) {
        return player != null && selected(player, player.getMainHandItem());
    }

    /* MASTER: register the profile, then update the existing Aiming Session.flinch with
     * (exactIza || selected(s.owner, s.stack)) && aimingInput(s). Use its active flag once
     * in WeaponFlinchState.magnitude; no additional .65 scalar. Preserve paid-shot ordering.
     * Call master-owned WeaponAiming.perksEdited(stack) after every real WeaponPerks.select/
     * clear tag change to reset only matching Session.stack flinch clocks, including same-tick
     * edit-away/back. No reset on a no-op select or pure query; see SOURCE.md.
     */
}
