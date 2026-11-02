package kim.biryeong.destiny.weapon;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Stateless mutation boundary. Master invokes once inside a real Heavy pickup transaction.
 * Returns actual accepted Special ammo; caller aggregates brick consumption and one broadcast.
 */
public final class WeaponLeadFromGold {
    private WeaponLeadFromGold() {}

    public static int grant(ServerPlayer player) {
        if (player == null || !player.isAlive() || player.isRemoved() || player.isSpectator()
                || !WeaponLoadout.enabled(player)) return 0;
        // Count every genuine equipped Special, including a second weapon without this trait.
        // Identity deduplication also prevents a corrupt aliased stack receiving two awards.
        Set<ItemStack> seen = Collections.newSetFromMap(new IdentityHashMap<>());
        var specials = WeaponLoadout.equipped(player).stream().filter(e -> {
            var stack = e.stack();
            return stack.getCount() == 1
                    && player.getInventory().getItem(e.slot().hotbar()) == stack
                    && WeaponLoadout.slot(player, stack, e.weapon()) == e.slot()
                    && e.characteristics().ammo() == WeaponAmmoType.SPECIAL
                    && WeaponCatalog.find(e.weapon().id()).filter(e.weapon()::equals).isPresent()
                    && seen.add(stack);
        }).toList();
        int accepted = 0;
        for (var equipped : specials) {
            var entry = equipped.weapon();
            var stack = equipped.stack();
            if (!LeadFromGoldProfile.supports(entry)
                    || WeaponPerks.selected(stack, LeadFromGoldProfile.ID)
                        .filter(LeadFromGoldProfile.rolls()::contains).isEmpty()) continue;
            var profile = WeaponProfile.forEntry(entry);
            var ammo = WeaponItems.magazine(stack, profile);
            int gained = ammo.addReserve(LeadFromGoldProfile.amount(entry, specials.size()));
            if (gained > 0) {
                WeaponItems.save(stack, ammo);
                accepted += gained;
            }
        }
        if (accepted > 0) player.getInventory().setChanged();
        return accepted;
    }
}
