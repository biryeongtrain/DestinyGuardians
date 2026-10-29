package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.input.GuardianAction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Main-thread selection transaction. Only selected creates sessions; timing/debug reads
 * never arm/extend, create attachments, or mutate item/cadence state. No passive HUD.
 */
public final class WeaponQuickdraw {
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack, outgoing;
        final int slot;
        final int incomingThreats;
        final long selectedAt;
        final WeaponCatalog.Entry entry;
        final WeaponPerks.Roll roll;
        final GuardianData data;
        final GuardianRuntime runtime;
        final GuardianClass guardianClass;
        final Map<GuardianAction,Integer> actions;
        final QuickdrawCycle cycle = new QuickdrawCycle();
        Session(ServerPlayer p, ItemStack incoming, int slot, WeaponCatalog.Entry entry, WeaponPerks.Roll roll, int incomingThreats) {
            owner=p;level=p.level();stack=incoming;outgoing=p.getMainHandItem();this.slot=slot;
            selectedAt=now(p);this.entry=entry;this.roll=roll;this.incomingThreats=incomingThreats;
            data=p.getAttachedOrElse(Guardians.DATA,null);runtime=Guardians.runtimeIfPresent(p).orElse(null);
            guardianClass=data == null ? null : data.guardianClass();
            actions=runtime == null ? Map.of() : Map.copyOf(runtime.lastActionTick);
            cycle.selected(incoming,selectedAt,true);
        }
    }
    private WeaponQuickdraw() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread()) throw new IllegalStateException("Quickdraw is main server thread owned");
    }
    private static boolean ownerValid(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
            && Guardians.runtimeIfPresent(p).map(r -> r.superSession == null).orElse(true);
    }
    /** Identity-only hotbar/loadout ownership; no detached, backpack, copied or offhand grant. */
    private static int ownedSlot(ServerPlayer p, ItemStack stack) {
        if (stack == null || stack.isEmpty()) return -1;
        if (WeaponLoadout.enabled(p) && WeaponLoadout.equipped(p).stream().noneMatch(e -> e.stack() == stack)) return -1;
        for (int i=0;i<9;i++) if (p.getInventory().getItem(i) == stack) return i;
        return -1;
    }
    private static boolean valid(ServerPlayer p, Session s, boolean heldOnly) {
        if (!ownerValid(p) || s.owner != p || s.level != p.level() || WeaponAiming.requested(p)
            || p.getInventory().getItem(s.slot) != s.stack || ownedSlot(p,s.stack) != s.slot) return false;
        var data=p.getAttachedOrElse(Guardians.DATA,null);var runtime=Guardians.runtimeIfPresent(p).orElse(null);
        if (data != s.data || runtime != s.runtime || (data == null ? null : data.guardianClass()) != s.guardianClass
            || (runtime != null && !runtime.lastActionTick.equals(s.actions))) return false;
        boolean held=p.getMainHandItem() == s.stack && p.getInventory().getSelectedSlot() == s.slot && WeaponLoadout.canUse(p);
        // Before vanilla mutates selection, the incoming duration belongs to this transaction.
        boolean incoming=!heldOnly && now(p) == s.selectedAt && p.getMainHandItem() == s.outgoing;
        return (held || incoming) && now(p) >= s.selectedAt
            && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
            && WeaponPerks.selected(s.stack,QuickdrawProfile.ID).filter(s.roll::equals).isPresent();
    }
    /** Master invokes ONLY on a genuine Handling source identity change, never initial bind.
     * Outgoing duration must already be accepted; incoming ready duration is evaluated next.
     */
    public static void selected(ServerPlayer p, ItemStack incoming) {
        if (p == null) return;
        thread(p);
        var previous=SESSIONS.get(p.getUUID());
        if (previous != null && previous.owner == p && previous.stack == incoming && valid(p,previous,false)) return;
        cleanup(p);
        if (!ownerValid(p) || WeaponAiming.requested(p)) return;
        int slot=ownedSlot(p,incoming);if (slot < 0) return;
        var entry=WeaponItems.entry(incoming).orElse(null);
        var roll=WeaponPerks.selected(incoming,QuickdrawProfile.ID).orElse(null);
        if (!QuickdrawProfile.supports(entry) || roll == null || !QuickdrawProfile.rolls().contains(roll) || !entry.id().equals(roll.id())) return;
        int incomingThreats=WeaponPerks.selected(incoming,ThreatDetectorProfile.ID)
            .filter(r -> QuickdrawProfile.compatible(entry,ThreatDetectorProfile.ID,r)).isPresent()
            ? WeaponThreatDetector.selectionSample(p,incoming) : 0;
        SESSIONS.put(p.getUUID(),new Session(p,incoming,slot,entry,roll,incomingThreats));
    }
    /** Accepted ADS toggle event, including requests during handling. Release cannot rearm. */
    public static void aimInput(ServerPlayer p, boolean pressed) {
        if (p == null) return;
        thread(p);var s=SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) s.cycle.aimInput(pressed);
    }
    public static void update(ServerPlayer p) {
        if (p == null) return;
        thread(p);var s=SESSIONS.get(p.getUUID());
        if (s == null || s.owner != p) return;
        s.cycle.update(now(p),valid(p,s,true),WeaponAiming.requested(p));
        if (!valid(p,s,true)) SESSIONS.remove(p.getUUID());
    }
    public static int remaining(ServerPlayer p) {
        if (p == null) return 0;
        var s=SESSIONS.get(p.getUUID());
        return s != null && valid(p,s,true) ? s.cycle.remaining(s.stack,now(p)) : 0;
    }
    /** Outermost after EC; active QD saturates raw handling and retains only proved TD scalar. */
    public static int handlingTicks(ServerPlayer p, ItemStack stack, boolean ready, int base) {
        if (p == null) return base;
        var s=SESSIONS.get(p.getUUID());
        if (s == null || s.stack != stack || !valid(p,s,false) || s.cycle.remaining(stack,now(p)) == 0) return base;
        double scalar=1;
        if (WeaponPerks.selected(stack,ThreatDetectorProfile.ID)
            .filter(r -> QuickdrawProfile.compatible(s.entry,ThreatDetectorProfile.ID,r)).isPresent())
            scalar=ThreatDetectorProfile.handlingScalar(p.getMainHandItem() == stack ? WeaponThreatDetector.stacks(p) : s.incomingThreats);
        return QuickdrawProfile.handlingTicks(s.entry,scalar,ready);
    }
    public static void edited(ItemStack stack) { SESSIONS.values().removeIf(s -> s.stack == stack); }
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);var s=SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p && s.stack == stack) SESSIONS.remove(p.getUUID());
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        thread(p);var s=SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) SESSIONS.remove(p.getUUID());
    }
    public static void clear() { SESSIONS.clear(); }
}
