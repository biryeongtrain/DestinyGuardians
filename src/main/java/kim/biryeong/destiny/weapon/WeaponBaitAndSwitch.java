package kim.biryeong.destiny.weapon;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** Bait and Switch (W320): damage with every equipped weapon, each instance within 7s of the last,
 * gives this weapon +30% damage for 10s (captured at emission; persists through stow; no refresh). */
final class WeaponBaitAndSwitch {
    private WeaponBaitAndSwitch() {}
    static void damaged(ServerPlayer p, PerkBatchA.Session s, ItemStack source, long tick) {
        java.util.List<ItemStack> equipped = null;
        for (var slot : s.slots.values()) {
            if (!slot.has(BaitAndSwitchProfile.ID)) continue;
            if (equipped == null) equipped = PerkBatchA.equipped(p);
            slot.bait.damaged(tick, source, equipped, BaitAndSwitchProfile.chainTicks(), BaitAndSwitchProfile.durationTicks());
        }
    }
    static float multiplier(PerkBatchA.Slot slot, long tick) {
        return slot.has(BaitAndSwitchProfile.ID) && slot.bait.active(tick) ? (float) BaitAndSwitchProfile.damageMultiplier() : 1f;
    }
}
