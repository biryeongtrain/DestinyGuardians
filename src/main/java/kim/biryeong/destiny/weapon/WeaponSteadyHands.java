package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Original count-one canonical source authority; main-thread events only, pure queries. */
public final class WeaponSteadyHands {
    private static final Map<UUID, IdentityHashMap<ItemStack, Session>> SESSIONS = new HashMap<>();
    private record Incoming(ServerPlayer owner, ItemStack stack, ItemStack outgoing, int fromSlot,
                            ServerLevel level, GuardianData data, GuardianRuntime runtime,
                            GuardianClass guardianClass, boolean loadoutEnabled,
                            WeaponPerks.Roll roll, long tick, int threats) {}
    private static final Map<UUID, Incoming> INCOMING = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final WeaponCatalog.Entry entry;
        final WeaponPerks.Roll roll;
        final GuardianData data;
        final GuardianRuntime runtime;
        final GuardianClass guardianClass;
        final int slot;
        final boolean loadoutEnabled;
        final SteadyHandsCycle cycle = new SteadyHandsCycle();
        long observed, stowedAt = -1;
        Session(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry, WeaponPerks.Roll roll, int slot) {
            owner = p; level = p.level(); this.stack = stack; this.entry = entry; this.roll = roll;
            this.slot = slot; loadoutEnabled = WeaponLoadout.enabled(p);
            data = p.getAttachedOrElse(Guardians.DATA, null);
            runtime = Guardians.runtimeIfPresent(p).orElseThrow();
            guardianClass = data.guardianClass(); observed = now(p);
        }
    }
    public static final class Token {
        public static final Token NONE = new Token(null, null);
        private final Session source;
        private final SteadyHandsCycle.Emission emission;
        private Token(Session source, SteadyHandsCycle.Emission emission) {
            this.source = source; this.emission = emission;
        }
    }
    private WeaponSteadyHands() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("SteadyHands is main server thread owned");
    }
    private static boolean ownerValid(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        var runtime = Guardians.runtimeIfPresent(p).orElse(null);
        return data != null && data.guardianClass() != null && data.guardianClass() != GuardianClass.NONE
            && runtime != null && runtime.superSession == null;
    }
    private static int equippedSlot(ServerPlayer p, ItemStack stack) {
        if (stack == null || stack.isEmpty() || stack.getCount() != 1) return -1;
        int occurrences = 0, slot = -1;
        for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
            if (p.getInventory().getItem(i) == stack) { occurrences++; slot = i; }
        }
        if (occurrences != 1 || slot < 0 || slot >= 9) return -1;
        return !WeaponLoadout.enabled(p) || WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == stack)
            ? slot : -1;
    }
    private static boolean held(ServerPlayer p, Session s) {
        // Selection hook runs before vanilla changes slots. Never resurrect the outgoing buff
        // from that transient observation, including a same-tick away/back transaction.
        return s.stowedAt != now(p) && p.getMainHandItem() == s.stack
            && p.getInventory().getSelectedSlot() == equippedSlot(p, s.stack) && WeaponLoadout.canUse(p);
    }
    private static boolean valid(ServerPlayer p, Session s) {
        if (!ownerValid(p)) return false;
        var sessions = SESSIONS.get(p.getUUID());
        return sessions != null && sessions.get(s.stack) == s && s.owner == p && s.level == p.level()
            && now(p) >= s.observed && equippedSlot(p, s.stack) >= 0
            && WeaponLoadout.enabled(p) == s.loadoutEnabled
            && p.getAttachedOrElse(Guardians.DATA, null) == s.data && s.data.guardianClass() == s.guardianClass
            && Guardians.runtimeIfPresent(p).orElse(null) == s.runtime
            && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
            && WeaponPerks.selected(s.stack, SteadyHandsProfile.ID).filter(s.roll::equals).isPresent();
    }
    /** Lifecycle/tick writer. Passive reads never call this method. */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> {
            if (s.owner != p || valid(p, s)) return false;
            s.cycle.clear(); return true;
        });
        for (var s : sessions.values()) {
            if (s.owner != p) continue;
            s.cycle.update(now(p)); s.observed = now(p);
        }
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    /** Writer at an accepted event boundary, never called by passive queries. */
    private static Session bindHeld(ServerPlayer p) {
        if (p == null) return null;
        update(p);
        if (!ownerValid(p) || !WeaponLoadout.canUse(p) || now(p) < 0) return null;
        var stack = p.getMainHandItem();
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, SteadyHandsProfile.ID).orElse(null);
        int slot = equippedSlot(p, stack);
        if (slot < 0 || p.getInventory().getSelectedSlot() != slot
            || !SteadyHandsProfile.supports(entry) || roll == null || !SteadyHandsProfile.rolls().contains(roll)
            || !entry.id().equals(roll.id())) return null;
        var sessions = SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new IdentityHashMap<>());
        sessions.values().removeIf(previous -> {
            if (previous.owner == p) return false;
            previous.cycle.clear(); return true;
        });
        var s = sessions.get(stack);
        if (s == null || !valid(p, s)) {
            if (s != null) s.cycle.clear();
            s = new Session(p, stack, entry, roll, slot);
            sessions.put(stack, s);
        }
        return held(p, s) ? s : null;
    }
    /** AFTER paid ranged acceptance, BEFORE own damage/final blow. Share across pellets and splash. */
    public static Token capture(ServerPlayer p) {
        var s = bindHeld(p);
        if (s == null) return Token.NONE;
        var emission = s.cycle.capture(now(p));
        return emission == null ? Token.NONE : new Token(s, emission);
    }
    /** ONLY after positive actual HP/absorption loss and an attributable eligible enemy final blow. */
    public static void killed(ServerPlayer p, Token token, LivingEntity target) {
        if (p == null || token == null || token.source == null || token.source.owner != p || target == null) return;
        update(p);
        var s = token.source;
        if (valid(p, s) && target != p && target.level() == s.level && !target.isAlive() && !target.isSpectator())
            s.cycle.killed(now(p), token.emission, target);
    }
    /** Pure aggregate across original still-owned canonical sources, including ordinary stow. */
    public static int remaining(ServerPlayer p) {
        if (p == null) return 0;
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return 0;
        int remaining = 0;
        for (var s : sessions.values()) if (valid(p, s)) remaining = Math.max(remaining, s.cycle.remaining(now(p)));
        return remaining;
    }
    public static boolean active(ServerPlayer p) { return remaining(p) > 0; }
    /** Accepted selection writer, before incoming duration and before vanilla changes selection.
     * No binding/scan occurs in handlingTicks; same-tick inventory/owner/roll changes fail closed. */
    public static void selecting(ServerPlayer p, ItemStack desired) {
        if (p == null) return;
        thread(p);
        INCOMING.remove(p.getUUID());
        if (!ownerValid(p) || remaining(p) <= 0 || equippedSlot(p, desired) < 0) return;
        var entry = WeaponItems.entry(desired).orElse(null);
        var roll = WeaponPerks.selected(desired, ThreatDetectorProfile.ID).orElse(null);
        if (!ThreatDetectorProfile.supports(entry) || roll == null || !ThreatDetectorProfile.rolls().contains(roll)
            || !entry.id().equals(roll.id())) return;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        INCOMING.put(p.getUUID(), new Incoming(p, desired, p.getMainHandItem(),
            p.getInventory().getSelectedSlot(), p.level(), data, Guardians.runtimeIfPresent(p).orElseThrow(),
            data.guardianClass(), WeaponLoadout.enabled(p), roll, now(p), WeaponThreatDetector.selectionSample(p, desired)));
    }
    private static int threats(ServerPlayer p, ItemStack stack) {
        if (WeaponPerks.selected(stack, ThreatDetectorProfile.ID).isEmpty()) return 0;
        if (p.getMainHandItem() == stack) return WeaponThreatDetector.stacks(p);
        var i = INCOMING.get(p.getUUID());
        return i != null && i.owner == p && i.stack == stack && i.outgoing == p.getMainHandItem()
            && i.fromSlot == p.getInventory().getSelectedSlot() && i.level == p.level() && i.tick == now(p)
            && i.loadoutEnabled == WeaponLoadout.enabled(p) && p.getAttachedOrElse(Guardians.DATA, null) == i.data
            && i.data.guardianClass() == i.guardianClass && Guardians.runtimeIfPresent(p).orElse(null) == i.runtime
            && WeaponPerks.selected(stack, ThreatDetectorProfile.ID).filter(i.roll::equals).isPresent() ? i.threats : 0;
    }
    /** Final outer wrapper after RecoveryHandling. Never derive scalars from rounded prior ticks. */
    public static int handlingTicks(ServerPlayer p, ItemStack stack, boolean ready, int base) {
        if (p == null || remaining(p) <= 0 || equippedSlot(p, stack) < 0) return base;
        var entry = WeaponItems.entry(stack).orElse(null);
        if (!SteadyHandsProfile.handlingSupported(entry)) return base;
        double scalar = ThreatDetectorProfile.handlingScalar(threats(p, stack));
        if (WeaponPerks.selected(stack, PulseMonitorProfile.ID).isPresent())
            scalar *= WeaponPulseMonitor.handlingScalar(p, stack);
        if (ready && WeaponPerks.selected(stack, QuickdrawProfile.ID).isPresent()
            && WeaponQuickdraw.handlingTicks(p, stack, true, -1) != -1)
            scalar *= QuickdrawProfile.READY_SCALAR;
        return SteadyHandsProfile.handlingTicks(entry, ready, scalar);
    }
    /** +100 Handling affects ADS; .825/TD/Pulse/QD time scalars are ready/stow-only. */
    public static int adsTicks(ServerPlayer p, WeaponCatalog.Entry entry, int base, boolean entering) {
        if (p == null || entry == null || remaining(p) <= 0 || !WeaponLoadout.canUse(p)) return base;
        var stack = p.getMainHandItem();
        if (equippedSlot(p, stack) != p.getInventory().getSelectedSlot()
            || WeaponItems.entry(stack).filter(entry::equals).isEmpty() || !SteadyHandsProfile.adsSupported(entry)) return base;
        var snapshot = entering ? WeaponPerks.selected(stack, SnapshotAimProfile.ID).orElse(null) : null;
        return SteadyHandsProfile.adsTicks(entry, snapshot);
    }
    /** Retains buff; only blocks transient outgoing damage queries before vanilla selection. */
    public static void stowing(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && valid(p, s)) s.stowedAt = now(p);
    }
    public static void edited(ItemStack stack) {
        if (stack == null) return;
        INCOMING.values().removeIf(i -> i.stack == stack || i.outgoing == stack);
        var it = SESSIONS.values().iterator();
        while (it.hasNext()) {
            var sessions = it.next();
            var s = sessions.remove(stack);
            if (s != null) s.cycle.clear();
            if (sessions.isEmpty()) it.remove();
        }
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var incoming = INCOMING.get(p.getUUID());
        if (incoming != null && incoming.owner == p && (incoming.stack == stack || incoming.outgoing == stack))
            INCOMING.remove(p.getUUID());
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && s.owner == p) { s.cycle.clear(); sessions.remove(stack); }
        if (sessions != null && sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var incoming = INCOMING.get(p.getUUID());
        if (incoming != null && incoming.owner == p) INCOMING.remove(p.getUUID());
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> {
            if (s.owner != p) return false;
            s.cycle.clear(); return true;
        });
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    public static void clear() {
        INCOMING.clear();
        for (var sessions : SESSIONS.values()) for (var s : sessions.values()) s.cycle.clear();
        SESSIONS.clear();
    }
}
