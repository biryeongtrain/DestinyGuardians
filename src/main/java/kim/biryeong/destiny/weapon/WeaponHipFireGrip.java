package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** Stateless base Hip-Fire Grip on one exact selected main-hand source. No proc, cached
 * ownership, tick, ammo or aim-assist mutation; each query rechecks the held stack and ADS. */
public final class WeaponHipFireGrip {
    private WeaponHipFireGrip() {}
    private static WeaponCatalog.Entry held(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()
                || AbilityService.inSuper(p) || !WeaponLoadout.canUse(p)) return null;
        // Reject both entry input and residual exit progress: no Hip-Fire Grip during ADS transitions.
        if (WeaponAiming.aimInput(p) || WeaponAiming.progress(p) != 0) return null;
        ItemStack stack = p.getMainHandItem();
        if (stack.getCount() != 1) return null;
        var entry = WeaponItems.entry(stack).orElse(null);
        if (!HipFireGripProfile.supports(entry)) return null;
        var roll = WeaponPerks.selected(stack, HipFireGripProfile.ID).orElse(null);
        return roll != null && roll.id().equals(entry.id()) && HipFireGripProfile.rolls().contains(roll)
                ? entry : null;
    }
    public static int stabilityBonus(ServerPlayer p) {
        return held(p) == null ? 0 : HipFireGripProfile.stabilityBonus();
    }
    public static double accuracyScalar(ServerPlayer p) {
        return held(p) == null ? 1 : HipFireGripProfile.accuracyScalar();
    }
    public static double falloffScalar(ServerPlayer p, WeaponCatalog.Entry entry) {
        return entry != null && entry.equals(held(p)) ? HipFireGripProfile.falloffScalar(entry) : 1;
    }
}
