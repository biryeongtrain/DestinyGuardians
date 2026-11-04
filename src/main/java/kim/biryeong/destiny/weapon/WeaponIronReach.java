package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** Stateless modifier on the actual held source. No cached proc, animation or ammo mutation. */
public final class WeaponIronReach {
    private WeaponIronReach() {}
    private static WeaponCatalog.Entry held(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()
            || AbilityService.inSuper(p) || !WeaponLoadout.canUse(p)) return null;
        ItemStack stack = p.getMainHandItem();
        if (stack.getCount() != 1) return null;
        var e = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack,IronReachProfile.ID).orElse(null);
        return IronReachProfile.supports(e) && roll != null && IronReachProfile.rolls().contains(roll) ? e : null;
    }
    public static int stabilityBonus(ServerPlayer p) { return held(p) == null ? 0 : IronReachProfile.stabilityBonus(); }
    public static int rangeBonus(ServerPlayer p) { return held(p)==null?0:20; }
    public static WeaponBallistics.Profile ballistics(ServerPlayer p, WeaponCatalog.Entry entry,
                                                       WeaponBallistics.Profile base) {
        return entry != null && entry.equals(held(p)) ? IronReachProfile.ballistics(entry) : base;
    }
}
