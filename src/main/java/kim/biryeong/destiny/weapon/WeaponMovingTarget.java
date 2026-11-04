package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** Pure selected-source movement composition. Caller has already accepted its owned ADS input.
 * No ADS query, attribute mutation, retained session, aim assist or cached selection. */
public final class WeaponMovingTarget {
    private WeaponMovingTarget() {}

    /** Exact actual held object, ordinary locomotion and exact allowed base socket tuple. */
    public static boolean selected(ServerPlayer player, ItemStack stack) {
        if (player == null || stack == null || !player.isAlive() || player.isRemoved()
                || player.isSpectator() || player.hasDisconnected() || AbilityService.inSuper(player)
                || !WeaponLoadout.canUse(player) || !ordinaryLocomotion(player)) return false;
        int slot = player.getInventory().getSelectedSlot();
        if (slot < 0 || slot >= 9 || player.getMainHandItem() != stack
                || player.getInventory().getItem(slot) != stack || stack.getCount() != 1) return false;
        var entry = WeaponItems.entry(stack).orElse(null);
        return MovingTargetProfile.supports(entry)
                && WeaponPerks.selected(stack, MovingTargetProfile.ID)
                    .filter(r -> r.id().equals(entry.id()) && MovingTargetProfile.rolls().contains(r)).isPresent();
    }
    public static boolean selected(ServerPlayer player) {
        return player != null && selected(player, player.getMainHandItem());
    }
    private static boolean ordinaryLocomotion(ServerPlayer player) {
        return !player.isPassenger() && !player.getAbilities().flying && !player.isFallFlying()
                && !player.isSwimming() && !player.isInWater() && !player.isInLava()
                && !player.onClimbable() && !player.isVisuallyCrawling();
    }
    /** Apply once to the existing ADS scalar, including intrinsic precision-HC relief.
     * The caller owns ADS acceptance, native modifier identity and refresh/cleanup. */
    public static double movementScalar(ServerPlayer player, WeaponCatalog.Entry entry, double baseScalar) {
        if (entry == null || !selected(player)
                || WeaponItems.entry(player.getMainHandItem()).filter(entry::equals).isEmpty()) return baseScalar;
        return 1 - (1 - baseScalar) * MovingTargetProfile.adsMovementPenaltyScalar();
    }
}
