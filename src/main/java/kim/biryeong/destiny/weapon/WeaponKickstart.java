package kim.biryeong.destiny.weapon;

/** Kickstart (W320): a slide after >=1.5s of sprinting grants +15% damage (captured at emission)
 * and x0.8 charge time for a LOCAL 2s window (DDC duration '?'). */
final class WeaponKickstart {
    private WeaponKickstart() {}
    static void slide(PerkBatchA.Slot slot, long tick, int sprintTicks) {
        if (slot.has(KickstartProfile.ID))
            slot.kickstart.slide(tick, sprintTicks, KickstartProfile.sprintTicks(), KickstartProfile.durationTicks());
    }
    private static boolean active(PerkBatchA.Slot slot, long tick) { return slot.has(KickstartProfile.ID) && slot.kickstart.active(tick); }
    static float multiplier(PerkBatchA.Slot slot, long tick) { return active(slot, tick) ? (float) KickstartProfile.damageMultiplier() : 1f; }
    static WeaponProfile charge(PerkBatchA.Slot slot, long tick, WeaponProfile base) {
        if (!active(slot, tick) || base.chargeTicks() <= 0) return base;
        int charge = Math.max(1, (int) Math.ceil(base.chargeTicks() * KickstartProfile.chargeScalar() - 1e-9));
        return new WeaponProfile(base.mode(), base.damage(), base.intervalTicks(), base.magazine(), base.reserve(),
            base.reloadTicks(), base.range(), charge, base.burst(), base.pellets(), base.spread(), base.speed(),
            base.gravity(), base.blastRadius(), base.automatic(), base.infiniteReserve(), base.cadenceTicks(),
            base.burstSpacingTicks(), base.sharedBurstAmmo(), base.shellReload(), base.firstReloadTicks(), base.roundsPerInsert());
    }
}
