package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.Optional;
import java.util.function.Function;

/** Base EC passive: live read-only equipped SUPER element, no sessions/timer/lifecycle hooks.
 * Current Element lacks Stasis and Strand; neither is simulated or implemented here.
 * Getters never create attachment/runtime state. Master calls timing wrappers OUTERMOST after Surplus.
 */
public final class WeaponElementalCapacitor {
    private WeaponElementalCapacitor() {}
    private static boolean ownerValid(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
            && Guardians.runtimeIfPresent(p).map(r -> r.superSession == null).orElse(true);
    }
    /** Pure production selector. Only active-class loadout SUPER and exact registry identity count.
     * Cooldowns, super energy, other equipped abilities and weapon elements never select EC.
     */
    static Element equippedSuperElement(GuardianData data, Function<Identifier, Optional<Ability>> registry) {
        if (data == null || data.guardianClass() == null || data.guardianClass() == GuardianClass.NONE) return Element.KINETIC;
        var loadout = data.loadout().orElse(null);
        if (loadout == null) return Element.KINETIC;
        var id = loadout.get(AbilitySlot.SUPER);
        if (id == null) return Element.KINETIC;
        var ability = registry.apply(id).orElse(null);
        if (ability == null || !id.equals(ability.id()) || ability.slot() != AbilitySlot.SUPER
            || ability.guardianClass() != data.guardianClass() || ability.element() == null) return Element.KINETIC;
        return ability.element();
    }
    private static Element superElement(ServerPlayer p) {
        return ownerValid(p) ? equippedSuperElement(p.getAttachedOrElse(Guardians.DATA, null), AbilityRegistry::get) : Element.KINETIC;
    }
    /** Genuine equipped object identity permits incoming/outgoing before selection, including while
     * a nonweapon slot is selected. Backpack, offhand and detached copied objects are rejected.
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
        var roll = WeaponPerks.selected(stack, ElementalCapacitorProfile.ID).orElse(null);
        return ElementalCapacitorProfile.supports(entry) && roll != null && ElementalCapacitorProfile.rolls().contains(roll)
            && entry.id().equals(roll.id()) ? entry : null;
    }
    /** HUD/debug/stability authority is the genuinely held EC weapon. */
    public static Element element(ServerPlayer p) {
        return p != null && source(p, p.getMainHandItem(), true) != null ? superElement(p) : Element.KINETIC;
    }
    public static int stabilityBonus(ServerPlayer p) { return ElementalCapacitorProfile.stabilityBonus(element(p)); }
    private static boolean co(ItemStack stack, WeaponCatalog.Entry entry, String id) {
        return WeaponPerks.selected(stack, id).filter(r -> ElementalCapacitorProfile.compatible(entry, id, r)).isPresent();
    }
    /** Both genuine equipped incoming and outgoing objects, regardless of current selected slot. */
    public static int handlingTicks(ServerPlayer p, ItemStack stack, boolean ready, int base) {
        var entry = source(p, stack, false);
        if (entry == null) return base;
        int bonus = ElementalCapacitorProfile.handlingBonus(superElement(p));
        if (bonus == 0) return base;
        return ElementalCapacitorProfile.handlingTicks(entry, bonus, 1, ready);
    }
    public static int adsTicks(ServerPlayer p, WeaponCatalog.Entry entry, int base, boolean entering) {
        if (p == null) return base;
        var actual = source(p, p.getMainHandItem(), true);
        if (actual == null || !actual.equals(entry)) return base;
        int bonus = ElementalCapacitorProfile.handlingBonus(superElement(p));
        if (bonus == 0) return base;
        return ElementalCapacitorProfile.adsTicks(entry, bonus, false);
    }
    /** Acceptance snapshot. Sum raw capped stats and sourced companion scalar before one ceil.
     * If Solar is inapplicable, return previous Plan unchanged so legal companion bonuses survive.
     * EC has no reload scalar and no legal Surplus/Outlaw pair. Companions are exact distinct rolls.
     */
    public static WeaponReloadPolicy.Plan plan(ServerPlayer p, WeaponCatalog.Entry entry, WeaponReloadPolicy.Plan base) {
        if (p == null) return base;
        var stack = p.getMainHandItem();
        var actual = source(p, stack, true);
        if (actual == null || !actual.equals(entry)) return base;
        int bonus = ElementalCapacitorProfile.reloadBonus(superElement(p));
        if (bonus == 0) return base;
        double scalar = 1;
        if (co(stack, entry, RapidHitProfile.ID)) {
            int count = WeaponRapidHit.stacks(p);
            if (count > 0) {
                var reload = RapidHitProfile.reload(entry, count);
                bonus += reload.effectiveReloadStat() - reload.baseReloadStat();
                scalar *= RapidHitProfile.durationMultiplier(count);
            }
        }
        if (co(stack, entry, FeedingFrenzyProfile.ID)) {
            int count = WeaponFeedingFrenzy.stacks(p);
            if (count > 0) {
                var reload = FeedingFrenzyProfile.reload(entry, count);
                bonus += reload.effectiveReloadStat() - reload.baseReloadStat();
                scalar *= FeedingFrenzyProfile.durationMultiplier(count);
            }
        }
        return ElementalCapacitorProfile.reloadPlan(entry, bonus, scalar, base);
    }
}
