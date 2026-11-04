package kim.biryeong.destiny.weapon;

import net.minecraft.server.level.ServerPlayer;

/** Eye of the Storm (W320): scales linearly with missing shield (see ShieldTraitCycle):
 * up to +30 Handling, x0.6 accuracy cone and x0.83 cone growth. */
final class WeaponEyeOfTheStorm {
    private WeaponEyeOfTheStorm() {}
    static double fraction(ServerPlayer p, PerkBatchA.Slot slot) {
        if (!slot.has(EyeOfTheStormProfile.ID)) return 0;
        var cycle = PerkBatchA.shieldCycle(p);
        return cycle == null ? 0 : cycle.eyeFraction(PerkBatchA.shield(p), EyeOfTheStormProfile.fullShield());
    }
    static double handlingBonus(ServerPlayer p, PerkBatchA.Slot slot) {
        return EyeOfTheStormProfile.handlingBonus() * fraction(p, slot);
    }
    static double coneScalar(ServerPlayer p, PerkBatchA.Slot slot) {
        return 1 - (1 - EyeOfTheStormProfile.coneScalar()) * fraction(p, slot);
    }
    static double growthScalar(ServerPlayer p, PerkBatchA.Slot slot) {
        return 1 - (1 - EyeOfTheStormProfile.growthScalar()) * fraction(p, slot);
    }
}
