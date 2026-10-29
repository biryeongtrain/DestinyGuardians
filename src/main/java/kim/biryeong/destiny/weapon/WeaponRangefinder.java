package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerPlayer;

/** Pure current-source queries. No attachment creation, session, proc, timer or flight mutation. */
public final class WeaponRangefinder {
    private WeaponRangefinder() {}

    private static WeaponCatalog.Entry held(ServerPlayer player) {
        if (player == null || !player.isAlive() || player.isRemoved() || player.isSpectator()
                || player.hasDisconnected() || AbilityService.inSuper(player)
                || !WeaponLoadout.canUse(player)) return null;
        var stack = player.getMainHandItem();
        int slot = player.getInventory().getSelectedSlot();
        if (slot < 0 || slot >= 9 || player.getInventory().getItem(slot) != stack || stack.getCount() != 1)
            return null;
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, RangefinderProfile.ID).orElse(null);
        return RangefinderProfile.supports(entry) && roll != null && entry.id().equals(roll.id())
            && RangefinderProfile.rolls().contains(roll) ? entry : null;
    }

    /** Selected trait on the actual inventory-held canonical weapon; ADS is not required here. */
    public static boolean selected(ServerPlayer player) { return held(player) != null; }

    private static boolean aiming(ServerPlayer player, WeaponCatalog.Entry entry) {
        return entry != null && entry.equals(held(player)) && WeaponAiming.aimInput(player)
            && !WeaponHandling.blocked(player) && !WeaponRuntime.reloading(player)
            && WeaponAiming.progress(player) >= RangefinderProfile.minAdsProgress();
    }

    /** Existing scoped ADS policy: progress >= .5, for scoped and ordinary ADS weapons alike.
     * WeaponAiming.progress matches the actual owner, level and held stack and checks eligibility.
     * Current release/reload/handling invalidates immediately, even before the next ADS tick.
     */
    public static int rangeBonus(ServerPlayer player) { return rangeBonus(player, held(player)); }
    public static int rangeBonus(ServerPlayer player, WeaponCatalog.Entry entry) {
        return aiming(player, entry) ? RangefinderProfile.rangeBonus() : 0;
    }

    /** Selected held weapon's visual target, independent of ADS progress. Native zoom progress
     * interpolates toward it from zero, avoiding a target jump at the .5 gameplay boundary.
     * Never multiply damage falloff by this scalar.
     */
    public static float zoomScalar(ServerPlayer player) { return zoomScalar(player, held(player)); }
    public static float zoomScalar(ServerPlayer player, WeaponCatalog.Entry entry) {
        return entry != null && entry.equals(held(player)) ? RangefinderProfile.zoomScalar() : 1f;
    }

    /** MASTER: sample ONCE from the accepted paid projectile Shot's launch speed, after bow draw
     * scaling. Store the result in its initial velocity. Never re-query while the shot is in flight,
     * nor apply again on impact/tracking/bounce. Entry must be that paid shot's exact source.
     * Hitscan/melee paths must not call this; nonpositive/nonfinite inputs are passed through.
     */
    public static double projectileSpeed(ServerPlayer player, WeaponCatalog.Entry entry, double launchSpeed) {
        return Double.isFinite(launchSpeed) && launchSpeed > 0 && aiming(player, entry)
            ? launchSpeed * RangefinderProfile.projectileSpeedScalar() : launchSpeed;
    }
}
