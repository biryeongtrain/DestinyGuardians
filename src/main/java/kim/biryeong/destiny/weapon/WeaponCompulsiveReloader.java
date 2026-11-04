package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.Guardians;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** Read-only reload-acceptance snapshot. No sessions, ammo writes, timer edits or lifecycle hooks. */
public final class WeaponCompulsiveReloader {
    private WeaponCompulsiveReloader() {}

    private static WeaponCatalog.Entry source(ServerPlayer player, ItemStack stack) {
        if (player == null || !player.isAlive() || player.isRemoved() || player.isSpectator()
                || player.hasDisconnected() || stack == null || stack.isEmpty()
                || Guardians.runtimeIfPresent(player).map(r -> r.superSession != null).orElse(false)
                || !WeaponLoadout.canUse(player)) return null;
        int slot = player.getInventory().getSelectedSlot();
        if (slot < 0 || slot >= 9 || player.getMainHandItem() != stack
                || player.getInventory().getItem(slot) != stack
                || WeaponLoadout.enabled(player)
                    && WeaponLoadout.equipped(player).stream().noneMatch(e -> e.stack() == stack)) return null;
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, CompulsiveReloaderProfile.ID).orElse(null);
        return CompulsiveReloaderProfile.supports(entry) && roll != null
            && entry.id().equals(roll.id()) && CompulsiveReloaderProfile.rolls().contains(roll) ? entry : null;
    }

    /** Master calls LAST among reload plan wrappers, immediately BEFORE cycle.startReload.
     * Read the exact held object's true current magazine before any reload credit. At/below half,
     * invalid/foreign sources and an already running reload return the incoming plan unchanged.
     * An accepted immutable plan remains frozen through later shots/inserts, stow or trait edits.
     */
    public static WeaponReloadPolicy.Plan plan(ServerPlayer player, WeaponCatalog.Entry entry,
                                               WeaponReloadPolicy.Plan base) {
        if (player == null) return base;
        var stack = player.getMainHandItem();
        var actual = source(player, stack);
        if (actual == null || !actual.equals(entry) || WeaponRuntime.reloadOwnedBy(player, stack)) return base;
        var profile = WeaponProfile.forEntry(entry);
        int roundsBefore = WeaponItems.magazine(stack, profile).rounds();
        if (!CompulsiveReloaderProfile.aboveThreshold(roundsBefore, profile.magazine())) return base;
        int bonus = CompulsiveReloaderProfile.reloadBonus();
        double scalar = CompulsiveReloaderProfile.durationMultiplier();
        // Only Austringer and Nezarec's Whisper have a distinct implemented reload companion.
        // Outlaw/Rapid Hit/PM/Stats for All/Surplus/etc. are absent or compete for socket 3.
        if (WeaponPerks.selected(stack, FrenzyProfile.ID)
                .filter(r -> CompulsiveReloaderProfile.compatible(entry, FrenzyProfile.ID, r)).isPresent()
                && WeaponFrenzy.remaining(player) > 0) bonus += FrenzyProfile.reloadBonus();
        return CompulsiveReloaderProfile.reloadPlan(entry, bonus, scalar, base);
    }
}
