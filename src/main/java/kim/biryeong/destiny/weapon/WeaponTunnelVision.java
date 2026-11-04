package kim.biryeong.destiny.weapon;

/** Tunnel Vision (W320): finishing this weapon's reload within 3.6s of its final blow grants 5s of
 * faster ADS and lower cone growth (LOCAL placeholder values; DDC lists '?'). Aim assist +20 is
 * source-only because aim assist is not simulated. */
final class WeaponTunnelVision {
    private WeaponTunnelVision() {}
    static void killed(PerkBatchA.Slot slot, long tick) { if (slot.has(TunnelVisionProfile.ID)) slot.tunnel.killed(tick); }
    static void reloadFinished(PerkBatchA.Slot slot, long tick) {
        if (slot.has(TunnelVisionProfile.ID))
            slot.tunnel.reloadFinished(tick, TunnelVisionProfile.killWindowTicks(), TunnelVisionProfile.durationTicks());
    }
    private static boolean active(PerkBatchA.Slot slot, long tick) { return slot.has(TunnelVisionProfile.ID) && slot.tunnel.active(tick); }
    static double adsScalar(PerkBatchA.Slot slot, long tick) { return active(slot, tick) ? TunnelVisionProfile.adsScalar() : 1; }
    static double growthScalar(PerkBatchA.Slot slot, long tick) { return active(slot, tick) ? TunnelVisionProfile.growthScalar() : 1; }
}
