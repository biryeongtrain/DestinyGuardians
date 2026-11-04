package kim.biryeong.destiny.weapon;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Pulse Monitor's final raw-stat composition, before one clamp/curve/quantization.
 * Other wrappers remain authoritative when Pulse Monitor is inactive. The only incoming
 * proximity sample is taken in the accepted inventory selection transaction, never a getter.
 */
public final class WeaponRecoveryHandling {
    private record Incoming(ServerPlayer owner, ItemStack stack, ItemStack outgoing,
                            int fromSlot, long tick, int threats) {}
    private static final Map<UUID, Incoming> INCOMING = new HashMap<>();
    private WeaponRecoveryHandling() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }

    public static void selecting(ServerPlayer p, ItemStack stack) {
        if (WeaponPulseMonitor.handlingBonus(p, stack) <= 0) { cleanup(p); return; }
        int threats = selected(stack, ThreatDetectorProfile.ID)
                ? WeaponThreatDetector.selectionSample(p, stack) : 0;
        INCOMING.put(p.getUUID(), new Incoming(p, stack, p.getMainHandItem(),
                p.getInventory().getSelectedSlot(), now(p), threats));
    }
    private static boolean selected(ItemStack stack, String id) {
        return WeaponPerks.selected(stack, id).isPresent();
    }
    private static int threats(ServerPlayer p, ItemStack stack) {
        if (!selected(stack, ThreatDetectorProfile.ID)) return 0;
        if (stack == p.getMainHandItem()) return WeaponThreatDetector.stacks(p);
        var incoming = INCOMING.get(p.getUUID());
        return incoming != null && incoming.owner == p && incoming.stack == stack
                && incoming.outgoing == p.getMainHandItem() && incoming.fromSlot == p.getInventory().getSelectedSlot()
                && incoming.tick == now(p) ? incoming.threats : 0;
    }
    private static boolean backup(ServerPlayer p, ItemStack stack) {
        return selected(stack, BackupPlanProfile.ID)
                && WeaponBackupPlan.handlingTicks(p, stack, true, -1) != -1;
    }
    private static int rawBonus(ServerPlayer p, ItemStack stack, int pulse, int threats, boolean quickdraw) {
        int bonus = pulse + ThreatDetectorProfile.handlingBonus(threats);
        if (selected(stack, FrenzyProfile.ID) && WeaponFrenzy.ownedRemaining(p, stack) > 0)
            bonus += FrenzyProfile.handlingBonus();
        if (backup(p, stack)) bonus += BackupPlanProfile.handlingBonus();
        // Quickdraw saturates the raw stat; it does not supply an ADS bonus.
        return quickdraw ? Math.max(100, bonus) : bonus;
    }
    public static int handlingTicks(ServerPlayer p, ItemStack stack, boolean ready, int base) {
        int pulse = WeaponPulseMonitor.handlingBonus(p, stack);
        var entry = WeaponItems.entry(stack).orElse(null);
        if (pulse <= 0 || !PulseMonitorProfile.supports(entry)) return base;
        int threats = threats(p, stack);
        boolean quickdraw = selected(stack, QuickdrawProfile.ID)
                && WeaponQuickdraw.handlingTicks(p, stack, ready, -1) != -1;
        double scalar = WeaponPulseMonitor.handlingScalar(p, stack)
                * ThreatDetectorProfile.handlingScalar(threats)
                * (quickdraw && ready ? QuickdrawProfile.READY_SCALAR : 1);
        return PulseMonitorProfile.handlingTicks(entry, rawBonus(p, stack, pulse, threats, quickdraw), scalar, ready);
    }
    public static int adsTicks(ServerPlayer p, WeaponCatalog.Entry entry, int base, boolean entering) {
        var stack = p.getMainHandItem();
        int pulse = WeaponPulseMonitor.handlingBonus(p, stack);
        if (pulse <= 0 || !PulseMonitorProfile.supports(entry)
                || WeaponItems.entry(stack).filter(entry::equals).isEmpty()) return base;
        return PulseMonitorProfile.adsTicks(entry, rawBonus(p, stack, pulse, threats(p, stack), false),
                entering && selected(stack, SnapshotAimProfile.ID));
    }
    public static void cleanup(ServerPlayer p) {
        var incoming = INCOMING.get(p.getUUID());
        if (incoming != null && incoming.owner == p) INCOMING.remove(p.getUUID());
    }
    public static void clear() { INCOMING.clear(); }
}
