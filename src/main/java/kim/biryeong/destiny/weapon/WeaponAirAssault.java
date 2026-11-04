package kim.biryeong.destiny.weapon;

import net.minecraft.server.level.ServerPlayer;

/** Air Assault (W320): passive +10 Airborne Effectiveness while held; held final blows add +30 AE
 * stacks (max 2, airborne kill = 2) for 5s, refreshed by kills; stowing removes stacks. */
final class WeaponAirAssault {
    private WeaponAirAssault() {}
    static void killed(ServerPlayer p, PerkBatchA.Slot slot, long tick) {
        if (slot.has(AirAssaultProfile.ID))
            slot.air.killed(tick, WeaponAccuracy.airborne(p), AirAssaultProfile.airborneKillStacks(),
                AirAssaultProfile.maxStacks(), AirAssaultProfile.durationTicks());
    }
    static int airborneBonus(PerkBatchA.Slot slot, long tick) {
        if (!slot.has(AirAssaultProfile.ID)) return 0;
        return AirAssaultProfile.passiveAirborne() + AirAssaultProfile.airbornePerStack() * slot.air.stacks(tick);
    }
}
