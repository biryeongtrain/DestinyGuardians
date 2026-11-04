package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Stateless original equipped-stack queries. Master calls only in a real Special/Heavy
 * brick transaction and owns all reserve-funded transfer, item saves and brick consumption.
 */
public final class WeaponOverflow {
    private WeaponOverflow() {}
    private static boolean ownerValid(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        var runtime = Guardians.runtimeIfPresent(p).orElse(null);
        return data != null && data.guardianClass() != null && data.guardianClass() != GuardianClass.NONE
            && runtime != null && runtime.superSession == null;
    }
    private static boolean equipped(ServerPlayer p, ItemStack stack) {
        if (stack == null || stack.isEmpty() || stack.getCount() != 1) return false;
        int slot = -1, identities = 0;
        for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
            if (p.getInventory().getItem(i) == stack) { identities++; slot = i; }
        }
        return identities == 1 && slot >= 0 && slot < 9 && (!WeaponLoadout.enabled(p)
            || WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == stack));
    }

    /** Pure exact original-stack predicate. Held/stowed and current weapon selection are
     * irrelevant. No reserve-full check: a real brick can be consumed for Primary loaded gain.
     */
    public static boolean selected(ServerPlayer p, ItemStack stack) {
        if (!ownerValid(p) || !equipped(p, stack)) return false;
        var entry = WeaponItems.entry(stack).orElse(null);
        return OverflowProfile.supports(entry) && WeaponCharacteristics.of(entry).ammo() == WeaponAmmoType.PRIMARY
            && WeaponPerks.selected(stack, OverflowProfile.ID).filter(OverflowProfile.rolls()::contains)
                .filter(r -> r.id().equals(entry.id())).isPresent();
    }

    /** Immutable list of actual references in deterministic slot order, no copied items.
     * Loadout mode admits its canonical slots; standalone mode admits the actual hotbar.
     * Recheck selected immediately before transfer if the caller crosses an event boundary.
     */
    public static List<ItemStack> eligible(ServerPlayer p) {
        if (!ownerValid(p)) return List.of();
        var result = new ArrayList<ItemStack>();
        for (int slot = 0; slot < 9; slot++) {
            var stack = p.getInventory().getItem(slot);
            if (selected(p, stack)) result.add(stack);
        }
        return List.copyOf(result);
    }

    /** Pure 2x base target (0 for unsupported/noncanonical entry), never an ammo grant.
     * Eligibility must come from selected/eligible; an entry alone proves no ownership.
     */
    public static int target(WeaponCatalog.Entry entry) { return OverflowProfile.target(entry); }
}
