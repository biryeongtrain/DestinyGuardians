package kim.biryeong.destiny.weapon;

import net.minecraft.server.level.ServerPlayer;

/** Fragile Focus (W320): +20 Range while Guardian shields are up; off at critical health, back 1s
 * after shields are full (ShieldTraitCycle). */
final class WeaponFragileFocus {
    private WeaponFragileFocus() {}
    static int rangeBonus(ServerPlayer p, PerkBatchA.Slot slot) {
        if (!slot.has(FragileFocusProfile.ID)) return 0;
        var cycle = PerkBatchA.shieldCycle(p);
        return cycle != null && cycle.fragileActive() ? FragileFocusProfile.rangeBonus() : 0;
    }
}
