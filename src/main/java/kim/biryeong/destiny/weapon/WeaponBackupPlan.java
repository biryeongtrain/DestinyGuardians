package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Main-thread, original-stack ready/stow observations. Master owns dispatch/integrations.
 * Every query is pure: no binding, attachments, scans, time advancement, or item writes.
 * Charge damage/timing are accepted together; expiry never retimes an accepted profile.
 */
public final class WeaponBackupPlan {
    private static final Map<UUID, IdentityHashMap<ItemStack, Session>> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final int slot;
        final WeaponCatalog.Entry entry;
        final WeaponPerks.Roll roll;
        final GuardianData data;
        final GuardianRuntime runtime;
        final GuardianClass guardianClass;
        final boolean loadoutEnabled;
        final BackupPlanCycle cycle = new BackupPlanCycle();
        long observed;
        long selectionTick = -1;
        ItemStack selectionFrom;
        int selectionFromSlot = -1;
        int incomingThreats;
        Session(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry, int slot) {
            owner = p; level = p.level(); this.stack = stack; this.entry = entry; this.slot = slot;
            roll = WeaponPerks.selected(stack, BackupPlanProfile.ID).orElseThrow();
            data = p.getAttachedOrElse(Guardians.DATA, null);
            runtime = Guardians.runtimeIfPresent(p).orElseThrow();
            guardianClass = data.guardianClass(); loadoutEnabled = WeaponLoadout.enabled(p); observed = now(p);
        }
    }
    private WeaponBackupPlan() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("Backup Plan is main server thread owned");
    }
    private static boolean ownerValid(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        var runtime = Guardians.runtimeIfPresent(p).orElse(null);
        return data != null && data.guardianClass() != null && data.guardianClass() != GuardianClass.NONE
            && runtime != null && runtime.superSession == null;
    }
    /** Only the actual hotbar object, restricted to canonical loadout slots when enabled. */
    private static int equippedSlot(ServerPlayer p, ItemStack stack) {
        if (stack == null || stack.isEmpty()) return -1;
        if (WeaponLoadout.enabled(p) && WeaponLoadout.equipped(p).stream().noneMatch(e -> e.stack() == stack)) return -1;
        for (int i = 0; i < 9; i++) if (p.getInventory().getItem(i) == stack) return i;
        return -1;
    }
    private static WeaponCatalog.Entry source(ServerPlayer p, ItemStack stack) {
        if (!ownerValid(p) || equippedSlot(p, stack) < 0) return null;
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, BackupPlanProfile.ID).orElse(null);
        return BackupPlanProfile.supports(entry) && roll != null && BackupPlanProfile.rolls().contains(roll)
            && entry.id().equals(roll.id()) ? entry : null;
    }
    private static boolean held(ServerPlayer p, Session s) {
        return p.getMainHandItem() == s.stack && p.getInventory().getSelectedSlot() == s.slot && WeaponLoadout.canUse(p);
    }
    private static boolean valid(ServerPlayer p, Session s) {
        if (!ownerValid(p)) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        return s.owner == p && s.level == p.level() && data == s.data && data.guardianClass() == s.guardianClass
            && Guardians.runtimeIfPresent(p).orElse(null) == s.runtime && now(p) >= s.observed
            && WeaponLoadout.enabled(p) == s.loadoutEnabled && equippedSlot(p, s.stack) == s.slot
            && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
            && WeaponPerks.selected(s.stack, BackupPlanProfile.ID).filter(s.roll::equals).isPresent();
    }
    private static boolean pending(ServerPlayer p, Session s) {
        return s.selectionTick == now(p) && s.selectionFrom == p.getMainHandItem()
            && s.selectionFromSlot == p.getInventory().getSelectedSlot();
    }
    private static Session bind(ServerPlayer p, ItemStack stack) {
        var entry = source(p, stack);
        if (entry == null) return null;
        var sessions = SESSIONS.computeIfAbsent(p.getUUID(), id -> new IdentityHashMap<>());
        var s = sessions.get(stack);
        if (s == null || !valid(p, s)) {
            s = new Session(p, stack, entry, equippedSlot(p, stack));
            sessions.put(stack, s);
        }
        return s;
    }
    /** Observe ALL eligible equipped stacks. A newly observed stowed object starts at now.
     * Session replacement/lifecycle invalidation loses all old stow credit and active duration.
     */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions != null) {
            sessions.values().removeIf(s -> !valid(p, s)
                || s.selectionTick >= 0 && !held(p, s) && !pending(p, s));
            if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
        }
        if (!ownerValid(p)) return;
        for (int slot = 0; slot < 9; slot++) {
            var s = bind(p, p.getInventory().getItem(slot));
            if (s == null) continue;
            // Accepted incoming is observable for this transaction until vanilla changes selection.
            if (!held(p, s) && pending(p, s)) continue;
            s.cycle.update(now(p), held(p, s));
            s.observed = now(p);
            s.selectionTick = -1;
            s.selectionFrom = null;
        }
    }
    /** AFTER accepting outgoing stow duration, BEFORE incoming ready calculation. No update here:
     * the still-held outgoing object has already been stowed by the selection transaction.
     * This event alone samples incoming TD; timing getters never scan or reuse outgoing TD.
     */
    public static void selecting(ServerPlayer p, ItemStack incoming) {
        if (p == null) return;
        thread(p);
        var s = bind(p, incoming);
        if (s == null) return;
        s.cycle.selecting(now(p));
        s.observed = now(p);
        s.selectionTick = now(p);
        s.selectionFrom = p.getMainHandItem();
        s.selectionFromSlot = p.getInventory().getSelectedSlot();
        s.incomingThreats = co(s, ThreatDetectorProfile.ID) ? WeaponThreatDetector.selectionSample(p, incoming) : 0;
    }
    /** Keep the actual stow origin, including same-tick away/back and duplicated hooks.
     * A newly seen outgoing stack starts its stow NOW; it receives no historical credit.
     */
    public static void stowing(ServerPlayer p, ItemStack outgoing) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(outgoing);
        if (s == null && outgoing == p.getMainHandItem()) s = bind(p, outgoing);
        if (s == null || !valid(p, s)) return;
        s.cycle.stowing(now(p));
        s.observed = now(p);
        s.selectionTick = -1;
        s.selectionFrom = null;
    }
    private static Session session(ServerPlayer p, ItemStack stack, boolean requireHeld) {
        if (p == null) return null;
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s == null || !valid(p, s)) return null;
        return held(p, s) || !requireHeld && pending(p, s) ? s : null;
    }
    public static int remaining(ServerPlayer p) {
        var s = p == null ? null : session(p, p.getMainHandItem(), true);
        return s == null ? 0 : s.cycle.remaining(now(p));
    }
    public static int handlingBonus(ServerPlayer p) { return remaining(p) > 0 ? BackupPlanProfile.handlingBonus() : 0; }
    /** Pure charge-acceptance snapshot. Store and reuse the whole returned profile through
     * continuation, charged gate and delayed shared paid burst; never requery it mid-charge.
     */
    public static WeaponProfile charge(ServerPlayer p, WeaponCatalog.Entry entry, WeaponProfile base) {
        var s = p == null ? null : session(p, p.getMainHandItem(), true);
        return s != null && s.entry.equals(entry) && s.cycle.remaining(now(p)) > 0
            ? BackupPlanProfile.charge(entry, base) : base;
    }
    /** Immediately AFTER successful cycle.fire, once per paid emission. No bind/update/input
     * refresh, no dry-fire refresh, no fusion refresh, no revival of an expired LFR window.
     */
    public static void paidEmission(ServerPlayer p, WeaponCatalog.Entry entry) {
        if (p == null) return;
        thread(p);
        var s = session(p, p.getMainHandItem(), true);
        if (s != null && s.entry.equals(entry)) s.cycle.paidEmission(now(p), BackupPlanProfile.linearFusion(entry));
    }
    private static boolean co(Session s, String id) {
        return WeaponPerks.selected(s.stack, id).filter(r -> BackupPlanProfile.compatible(s.entry, id, r)).isPresent();
    }
    /** OUTERMOST. +100 saturates all legal numeric handling bonuses. Keep legal TD/QD scalars
     * against raw curves rather than scaling or replacing a previous wrapper's rounded ticks.
     */
    public static int handlingTicks(ServerPlayer p, ItemStack stack, boolean ready, int base) {
        var s = session(p, stack, false);
        if (s == null || s.cycle.remaining(now(p)) == 0) return base;
        int threats = co(s, ThreatDetectorProfile.ID)
            ? pending(p, s) ? s.incomingThreats : WeaponThreatDetector.stacks(p) : 0;
        // Pure query with a sentinel: the existing QD authority validates its selection epoch,
        // including incoming-before-vanilla. This detects activation, never derives a timing ratio.
        boolean quickdraw = co(s, QuickdrawProfile.ID) && WeaponQuickdraw.handlingTicks(p, stack, ready, -1) != -1;
        return BackupPlanProfile.handlingTicks(s.entry, ThreatDetectorProfile.handlingScalar(threats), quickdraw, ready);
    }
    public static int adsTicks(ServerPlayer p, WeaponCatalog.Entry entry, int base, boolean entering) {
        var s = p == null ? null : session(p, p.getMainHandItem(), true);
        if (s == null || !s.entry.equals(entry) || s.cycle.remaining(now(p)) == 0) return base;
        return BackupPlanProfile.adsTicks(entry, entering && co(s, SnapshotAimProfile.ID));
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && s.owner == p) {
            sessions.remove(stack);
            if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
        }
    }
    public static void edited(ItemStack stack) {
        var iterator = SESSIONS.values().iterator();
        while (iterator.hasNext()) {
            var sessions = iterator.next();
            sessions.remove(stack);
            if (sessions.isEmpty()) iterator.remove();
        }
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> s.owner == p);
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    public static void clear() { SESSIONS.clear(); }
}
