package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.ability.AbilityRegistry;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** Base trait, read directly from authoritative crouching pose and genuine equipped objects.
 * No sessions, proc timers, HUD rows or attachment writes. Shift also drives this port's ADS,
 * but pressing shift or selecting a cosmetic ADS model alone is not a crouch grant.
 */
public final class WeaponFirmlyPlanted {
    private WeaponFirmlyPlanted() {}
    private static boolean ownerValid(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
            && Guardians.runtimeIfPresent(p).map(r -> r.superSession == null).orElse(true);
    }
    private static boolean equipped(ServerPlayer p, ItemStack stack) {
        if (WeaponLoadout.enabled(p)) return WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == stack);
        for (int i=0; i<9; i++) if (p.getInventory().getItem(i) == stack) return true;
        return false;
    }
    private static WeaponCatalog.Entry source(ServerPlayer p, ItemStack stack, boolean held) {
        if (!ownerValid(p) || !p.isCrouching() || stack == null || stack.getCount() != 1
            || !equipped(p, stack)) return null;
        if (held) {
            int slot = p.getInventory().getSelectedSlot();
            if (slot < 0 || slot >= 9 || p.getInventory().getItem(slot) != stack
                || p.getMainHandItem() != stack || !WeaponLoadout.canUse(p)) return null;
        }
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, FirmlyPlantedProfile.ID).orElse(null);
        return FirmlyPlantedProfile.supports(entry) && roll != null
            && FirmlyPlantedProfile.rolls().contains(roll) && entry.id().equals(roll.id()) ? entry : null;
    }
    private static WeaponCatalog.Entry held(ServerPlayer p) {
        return p == null ? null : source(p, p.getMainHandItem(), true);
    }
    public static boolean active(ServerPlayer p) { return held(p) != null; }
    public static int stabilityBonus(ServerPlayer p) {
        var e=held(p);return e == null ? 0 : FirmlyPlantedProfile.stabilityBonus(e);
    }
    public static int handlingBonus(ServerPlayer p) {
        var e=held(p);return e == null ? 0 : FirmlyPlantedProfile.handlingBonus(e);
    }
    public static double accuracyScalar(ServerPlayer p) {
        var e=held(p);return e == null ? 1 : FirmlyPlantedProfile.accuracyScalar(e);
    }
    public static double growthScalar(ServerPlayer p) {
        var e=held(p);return e == null ? 1 : FirmlyPlantedProfile.growthScalar(e);
    }
    public static double yawScalar(ServerPlayer p) {
        var e=held(p);return e == null ? 1 : FirmlyPlantedProfile.yawScalar(e);
    }
    private static boolean co(ItemStack stack, WeaponCatalog.Entry entry, String id) {
        return WeaponPerks.selected(stack,id).filter(r -> FirmlyPlantedProfile.compatible(entry,id,r)).isPresent();
    }
    private static int totalHandling(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry e) {
        int bonus=FirmlyPlantedProfile.handlingBonus(e);
        if (co(stack,e,FrenzyProfile.ID) && WeaponFrenzy.ownedRemaining(p,stack)>0)
            bonus+=FrenzyProfile.handlingBonus();
        // source() already proved genuine equipped FP object/owner/crouch. Exact compatible EC
        // Roll above plus the existing pure active-class SUPER selector also works before a swap.
        if (co(stack,e,ElementalCapacitorProfile.ID))
            bonus+=ElementalCapacitorProfile.handlingBonus(WeaponElementalCapacitor.equippedSuperElement(
                p.getAttachedOrElse(Guardians.DATA,null),AbilityRegistry::get));
        return bonus;
    }
    /** Actual incoming/outgoing equipped source before selection. Outer Quickdraw keeps its policy.
     * Sum raw stats before one curve evaluation/ceil, never multiply rounded companion durations.
     */
    public static int handlingTicks(ServerPlayer p, ItemStack stack, boolean ready, int base) {
        var e=source(p,stack,false);
        return e == null ? base : FirmlyPlantedProfile.handlingTicks(e,totalHandling(p,stack,e),1,ready);
    }
    public static int adsTicks(ServerPlayer p, WeaponCatalog.Entry entry, int base, boolean entering) {
        var e=held(p);
        if (e == null || !e.equals(entry)) return base;
        var stack=p.getMainHandItem();
        return FirmlyPlantedProfile.adsTicks(e,totalHandling(p,stack,e),entering && co(stack,e,SnapshotAimProfile.ID));
    }
}
