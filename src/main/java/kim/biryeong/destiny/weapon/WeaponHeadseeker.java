package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Paid direct-emission tokens on the original held source. All mutations run on the server
 * thread. Queries never bind, prune, repair identities, refresh or create guardian state. */
public final class WeaponHeadseeker {
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final Map<UUID, IdentityHashMap<ItemStack, StowFence>> STOWED = new HashMap<>();
    record Identity(Object owner, Object level, Object stack, Object data, Object runtime,
                    Object guardianClass, boolean loadout, int slot) {
        boolean same(Identity other) {
            return other != null && owner == other.owner && level == other.level && stack == other.stack
                    && data == other.data && runtime == other.runtime && guardianClass == other.guardianClass
                    && loadout == other.loadout && slot == other.slot;
        }
    }
    static final class Lease {
        private final Identity identity;
        private long observed;
        private boolean revoked;
        Lease(Identity identity, long tick) { this.identity = identity; observed = tick; }
        boolean valid(Identity current, long tick) {
            return !revoked && tick >= 0 && tick >= observed && identity.same(current);
        }
        void observe(long tick) { observed = tick; }
        void revoke() { revoked = true; }
    }
    /** Survives session pruning while the selection callback still exposes the outgoing hand. */
    record StowFence(Object owner, Object stack, long tick) {
        boolean blocks(Object currentOwner, Object currentStack, long now) {
            return owner == currentOwner && stack == currentStack && now <= tick;
        }
    }
    private static final class Session {
        final ServerPlayer owner;
        final ItemStack stack;
        final WeaponCatalog.Entry entry;
        final WeaponPerks.Roll roll;
        final Lease lease;
        final HeadseekerCycle cycle = new HeadseekerCycle();
        Session(ServerPlayer p, WeaponCatalog.Entry entry, WeaponPerks.Roll roll) {
            owner = p; stack = p.getMainHandItem(); this.entry = entry; this.roll = roll;
            lease = new Lease(identity(p), now(p));
        }
        void revoke() { lease.revoke(); cycle.clear(); }
    }
    public static final class Token {
        public static final Token NONE = new Token(null, null);
        private final Session source;
        private final HeadseekerCycle.Emission emission;
        private Token(Session source, HeadseekerCycle.Emission emission) {
            this.source = source; this.emission = emission;
        }
    }
    private WeaponHeadseeker() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("Headseeker is main server thread owned");
    }
    private static Identity identity(ServerPlayer p) {
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        return new Identity(p, p.level(), p.getMainHandItem(), data,
                Guardians.runtimeIfPresent(p).orElse(null), data == null ? null : data.guardianClass(),
                WeaponLoadout.enabled(p), p.getInventory().getSelectedSlot());
    }
    private static boolean ownerValid(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        var runtime = Guardians.runtimeIfPresent(p).orElse(null);
        return data != null && data.guardianClass() != null && data.guardianClass() != GuardianClass.NONE
                && runtime != null && runtime.superSession == null && WeaponLoadout.canUse(p);
    }
    private static boolean held(ServerPlayer p, ItemStack stack) {
        int slot = p.getInventory().getSelectedSlot();
        return stack != null && !stack.isEmpty() && stack.getCount() == 1 && slot >= 0 && slot < 9
                && p.getMainHandItem() == stack && p.getInventory().getItem(slot) == stack
                && (!WeaponLoadout.enabled(p) || WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == stack));
    }
    private static boolean fenced(ServerPlayer p, ItemStack stack) {
        var fences = STOWED.get(p.getUUID());
        var fence = fences == null ? null : fences.get(stack);
        return fence != null && fence.blocks(p, stack, now(p));
    }
    private static boolean valid(ServerPlayer p, Session s) {
        return s != null && s.owner == p && ownerValid(p) && SESSIONS.get(p.getUUID()) == s
                && held(p, s.stack) && !fenced(p, s.stack) && s.lease.valid(identity(p), now(p))
                && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
                && WeaponPerks.selected(s.stack, HeadseekerProfile.ID).filter(s.roll::equals).isPresent();
    }
    /** Prunes invalid originals and observes event time; never creates a session. */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var fences = STOWED.get(p.getUUID());
        if (fences != null) {
            fences.values().removeIf(f -> f.owner == p && now(p) > f.tick);
            if (fences.isEmpty()) STOWED.remove(p.getUUID(), fences);
        }
        var s = SESSIONS.get(p.getUUID());
        if (s == null || s.owner != p) return;
        if (!valid(p, s)) { s.revoke(); SESSIONS.remove(p.getUUID(), s); }
        else { s.cycle.update(now(p)); s.lease.observe(now(p)); }
    }
    /** Exactly once AFTER successful ammo payment and BEFORE direct trace for this emission.
     * Unsupported, unpaid/preview and unpaid supplemental/splash paths use Token.NONE.
     * Individually paid later burst bullets capture their own current window. */
    public static Token capture(ServerPlayer p) {
        if (p == null) return Token.NONE;
        thread(p); update(p);
        var stack = p.getMainHandItem();
        if (!ownerValid(p) || !held(p, stack) || fenced(p, stack) || now(p) < 0) return Token.NONE;
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, HeadseekerProfile.ID).orElse(null);
        if (!HeadseekerProfile.supports(entry) || roll == null || !HeadseekerProfile.rolls().contains(roll)
                || !entry.id().equals(roll.id())) return Token.NONE;
        var previous = SESSIONS.get(p.getUUID());
        if (previous != null && previous.owner != p) {
            previous.revoke(); SESSIONS.remove(p.getUUID(), previous);
        }
        var s = SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new Session(p, entry, roll));
        var emission = s.cycle.capture(now(p));
        s.lease.observe(now(p));
        return emission == null ? Token.NONE : new Token(s, emission);
    }
    /** ONLY after positive actual direct-hit loss. Precision never arms or refreshes this window.
     * No target-liveness test: a lethal body hit is still actual nonprecision weapon damage. */
    public static void confirmed(ServerPlayer p, Token token, boolean precision, float actual) {
        if (p == null || token == null || token.source == null || precision
                || !Float.isFinite(actual) || actual <= 0) return;
        thread(p); update(p);
        var s = token.source;
        if (valid(p, s)) s.cycle.confirmed(now(p), token.emission, false, actual);
    }
    /** Pure pre-trace snapshot. Apply only on direct precision damage, using the known source's
     * base precision multiplier. The same emission's body hit cannot boost its precision hit. */
    public static float precisionDamage(ServerPlayer p, Token token, float totalPrecision) {
        return precisionDamage(p, token, totalPrecision, null);
    }
    public static float precisionDamage(ServerPlayer p, Token token, float totalPrecision,
                                        net.minecraft.world.entity.LivingEntity target) {
        if (p == null || token == null || token.source == null || !valid(p, token.source)) return totalPrecision;
        var s = token.source;
        return HeadseekerCycle.precisionDamage(totalPrecision,
                CrucibleDamage.precision(s.entry,target,WeaponBallistics.of(s.entry).precision()),
                s.cycle.boosted(now(p), token.emission));
    }
    /** Pure held-original HUD/debug query; no state is created or repaired. */
    public static int remaining(ServerPlayer p) {
        if (p == null) return 0;
        var s = SESSIONS.get(p.getUUID());
        return valid(p, s) ? s.cycle.remaining(now(p)) : 0;
    }
    /** Accepted stow only. Fence even a source that has not captured a shot yet. */
    public static void stowing(ServerPlayer p, ItemStack stack) {
        if (p == null || stack == null) return;
        thread(p);
        STOWED.computeIfAbsent(p.getUUID(), ignored -> new IdentityHashMap<>())
                .put(stack, new StowFence(p, stack, now(p)));
        changed(p, stack);
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p && s.stack == stack) { s.revoke(); SESSIONS.remove(p.getUUID(), s); }
    }
    public static void edited(ItemStack stack) {
        if (stack == null) return;
        SESSIONS.values().removeIf(s -> {
            if (s.stack != stack) return false;
            thread(s.owner); s.revoke(); return true;
        });
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) { s.revoke(); SESSIONS.remove(p.getUUID(), s); }
        var fences = STOWED.get(p.getUUID());
        if (fences != null) {
            fences.values().removeIf(f -> f.owner == p);
            if (fences.isEmpty()) STOWED.remove(p.getUUID(), fences);
        }
    }
    public static void clear() {
        SESSIONS.values().forEach(s -> { thread(s.owner); s.revoke(); });
        SESSIONS.clear(); STOWED.clear();
    }
}
