package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.Optional;
import java.util.function.Function;

/** Read-only live server authority: no session, timer, packets, charge counters or lifecycle hooks.
 * Current abilities have one charge per slot. Registered + equipped + matching class/slot is the
 * existing enabled state; the ability API has no separate enabled flag. SUPER/JUMP never count.
 * Getters never create GuardianData/runtime or write item/ability state. Plans are immutable values.
 */
public final class WeaponSurplus {
    private WeaponSurplus() {}

    private static boolean ownerValid(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
            && Guardians.runtimeIfPresent(p).map(r -> r.superSession == null).orElse(true);
    }
    /** Pure ability projection; registry lookup must resolve the exact equipped ID. It does not
     * use AbilityService.equipped, whose getter creates data and accepts foreign class/slot IDs.
     */
    static int chargedAbilities(GuardianData data, Function<Identifier, Optional<Ability>> registry) {
        if (data == null || data.guardianClass() == null || data.guardianClass() == GuardianClass.NONE) return 0;
        var loadout = data.loadout().orElse(null);
        if (loadout == null) return 0;
        int count = 0;
        for (var slot : new AbilitySlot[]{AbilitySlot.GRENADE, AbilitySlot.MELEE, AbilitySlot.CLASS_ABILITY}) {
            var id = loadout.get(slot);
            if (id == null || data.cooldown(slot) > 0) continue;
            var ability = registry.apply(id).orElse(null);
            if (ability != null && id.equals(ability.id()) && ability.slot() == slot
                && ability.guardianClass() == data.guardianClass()) count++;
        }
        return count;
    }
    private static int chargedAbilities(ServerPlayer p) {
        return ownerValid(p) ? chargedAbilities(p.getAttachedOrElse(Guardians.DATA, null), AbilityRegistry::get) : 0;
    }
    /** Object identity is required. Real loadout slots or explicit standalone hotbar compatibility
     * match the existing PM handling policy; backpack/offhand/copied objects cannot escape it.
     */
    private static boolean equipped(ServerPlayer p, ItemStack stack) {
        if (WeaponLoadout.enabled(p)) return WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == stack);
        for (int i = 0; i < 9; i++) if (p.getInventory().getItem(i) == stack) return true;
        return false;
    }
    private static WeaponCatalog.Entry source(ServerPlayer p, ItemStack stack, boolean held) {
        if (!ownerValid(p) || stack == null || stack.isEmpty() || !equipped(p, stack)) return null;
        if (held) {
            int slot = p.getInventory().getSelectedSlot();
            if (slot < 0 || slot >= 9 || p.getMainHandItem() != stack || p.getInventory().getItem(slot) != stack
                || !WeaponLoadout.canUse(p)) return null;
        }
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, SurplusProfile.ID).orElse(null);
        return SurplusProfile.supports(entry) && roll != null && SurplusProfile.rolls().contains(roll)
            && entry.id().equals(roll.id()) ? entry : null;
    }
    public static int stacks(ServerPlayer p) {
        return p != null && source(p, p.getMainHandItem(), true) != null ? chargedAbilities(p) : 0;
    }
    public static int stabilityBonus(ServerPlayer p) { return SurplusProfile.stabilityBonus(stacks(p)); }
    private static boolean co(ItemStack stack, WeaponCatalog.Entry entry, String id) {
        return WeaponPerks.selected(stack, id).filter(r -> SurplusProfile.compatible(entry, id, r)).isPresent();
    }
    private static int threatStacks(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry) {
        return stack == p.getMainHandItem() && co(stack, entry, ThreatDetectorProfile.ID) ? WeaponThreatDetector.stacks(p) : 0;
    }
    private static int handlingBonus(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry, int count) {
        int total = SurplusProfile.handlingBonus(count);
        if (co(stack, entry, FrenzyProfile.ID) && WeaponFrenzy.ownedRemaining(p, stack) > 0)
            total += FrenzyProfile.handlingBonus();
        if (co(stack, entry, AdrenalineJunkieProfile.ID) && WeaponAdrenalineJunkie.ownedRemaining(p, stack) > 0)
            total += AdrenalineJunkieProfile.handlingBonus();
        return total + ThreatDetectorProfile.handlingBonus(threatStacks(p, stack, entry));
    }
    /** May run before selection for either genuine equipped incoming or outgoing object. */
    public static int handlingTicks(ServerPlayer p, ItemStack stack, boolean ready, int base) {
        var entry = source(p, stack, false);
        if (entry == null) return base;
        int count = chargedAbilities(p);
        if (count == 0) return base;
        return SurplusProfile.handlingTicks(entry, handlingBonus(p, stack, entry, count),
            ThreatDetectorProfile.handlingScalar(threatStacks(p, stack, entry)), ready);
    }
    public static int adsTicks(ServerPlayer p, WeaponCatalog.Entry entry, int base, boolean entering) {
        if (p == null) return base;
        var stack = p.getMainHandItem();
        var actual = source(p, stack, true);
        if (actual == null || !actual.equals(entry)) return base;
        int count = chargedAbilities(p);
        if (count == 0) return base;
        return SurplusProfile.adsTicks(entry, handlingBonus(p, stack, entry, count),
            entering && co(stack, entry, SnapshotAimProfile.ID));
    }
    /** Called after previous wrappers. Compose actual active companions on proved distinct sockets;
     * recompute RAW total stat/scalar before one ceil. Later ability changes cannot retime this value.
     */
    public static WeaponReloadPolicy.Plan plan(ServerPlayer p, WeaponCatalog.Entry entry, WeaponReloadPolicy.Plan base) {
        if (p == null) return base;
        var stack = p.getMainHandItem();
        var actual = source(p, stack, true);
        if (actual == null) return base;
        int count = chargedAbilities(p);
        if (count == 0) return base;
        if (!actual.equals(entry)) throw new IllegalArgumentException("Foreign Surplus reload plan");
        int bonus = SurplusProfile.reloadBonus(count);
        double scalar = 1;
        if (co(stack, entry, FrenzyProfile.ID) && WeaponFrenzy.remaining(p) > 0) bonus += FrenzyProfile.reloadBonus();
        bonus += ThreatDetectorProfile.reloadBonus(threatStacks(p, stack, entry));
        if (co(stack, entry, RapidHitProfile.ID)) {
            int rapid = WeaponRapidHit.stacks(p);
            if (rapid > 0) {
                var reload = RapidHitProfile.reload(entry, rapid);
                bonus += reload.effectiveReloadStat() - reload.baseReloadStat();
                scalar *= RapidHitProfile.durationMultiplier(rapid);
            }
        }
        return SurplusProfile.reloadPlan(entry, bonus, scalar, base);
    }
}
