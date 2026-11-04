package kim.biryeong.destiny.weapon;

import net.minecraft.server.level.ServerPlayer;

/** Field Prep (W320): passive +20 Ammo Generation on this weapon's emissions; while the server
 * reports the player crouching, +50 Reload with x0.8 reload and x0.8 ready/stow durations. */
final class WeaponFieldPrep {
    private WeaponFieldPrep() {}
    static int ammoGenerationBonus(PerkBatchA.Slot slot) {
        return slot.has(FieldPrepProfile.ID) ? FieldPrepProfile.ammoGenerationBonus() : 0;
    }
    static double handlingScalar(ServerPlayer p, PerkBatchA.Slot slot) {
        return slot.has(FieldPrepProfile.ID) && p.isCrouching() ? FieldPrepProfile.crouchHandlingScalar() : 1;
    }
    static WeaponReloadPolicy.Plan plan(ServerPlayer p, PerkBatchA.Slot slot, WeaponReloadPolicy.Plan plan) {
        if (!slot.has(FieldPrepProfile.ID) || !p.isCrouching()) return plan;
        var id = slot.entry.id();
        int bonus = FieldPrepProfile.crouchReloadBonus();
        double scalar = FieldPrepProfile.crouchReloadScalar();
        return new WeaponReloadPolicy.Plan(WeaponStatCurves.reloadTicks(id, plan.firstTicks(), bonus, scalar),
            WeaponStatCurves.reloadTicks(id, plan.intervalTicks(), bonus, scalar), plan.roundsPerInsert());
    }
}
