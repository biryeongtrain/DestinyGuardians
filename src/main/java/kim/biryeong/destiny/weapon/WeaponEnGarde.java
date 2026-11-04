package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Main-thread actual sword readiness and opaque paid snapshots. No attachments or shared runtime writes. */
public final class WeaponEnGarde {
    private static final Map<UUID, IdentityHashMap<ItemStack, Session>> SESSIONS = new HashMap<>();
    private static final Map<UUID, ReadyOwner> OWNERS = new HashMap<>();
    private static final class ReadyOwner {
        final ServerPlayer owner;
        final EnGardeCycle.Readiness readiness = new EnGardeCycle.Readiness();
        ItemStack outgoing;
        long stowedAt = -1;
        ReadyOwner(ServerPlayer p) { owner = p; }
    }
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
        final EnGardeCycle cycle;
        long observed, stowedAt = -1;
        Session(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry, WeaponPerks.Roll roll, int slot) {
            owner = p; level = p.level(); this.stack = stack; this.entry = entry; this.roll = roll;
            this.slot = slot; loadoutEnabled = WeaponLoadout.enabled(p);
            data = p.getAttachedOrElse(Guardians.DATA, null);
            runtime = Guardians.runtimeIfPresent(p).orElseThrow();
            guardianClass = data.guardianClass(); observed = now(p);
            cycle = new EnGardeCycle(OWNERS.get(p.getUUID()).readiness);
        }
    }
    public static final class Token {
        public static final Token NONE = new Token(null, null);
        private final Session source;
        private final EnGardeCycle.Contact contact;
        private Token(Session source, EnGardeCycle.Contact contact) {
            this.source = source; this.contact = contact;
        }
    }
    private WeaponEnGarde() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("EnGarde is main server thread owned");
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
        if (WeaponLoadout.enabled(p) && WeaponLoadout.equipped(p).stream().noneMatch(e -> e.stack() == stack)) return -1;
        int count = 0, slot = -1;
        for (int i = 0; i < p.getInventory().getContainerSize(); i++)
            if (p.getInventory().getItem(i) == stack) { count++; slot = i; }
        return count == 1 && slot >= 0 && slot < 9 ? slot : -1;
    }
    private static boolean held(ServerPlayer p, Session s) {
        // Selection hook runs before vanilla changes slots. Never resurrect the outgoing buff
        // from that transient observation, including a same-tick away/back transaction.
        return s.stowedAt != now(p) && p.getMainHandItem() == s.stack
            && p.getInventory().getSelectedSlot() == s.slot && WeaponLoadout.canUse(p);
    }
    private static boolean valid(ServerPlayer p, Session s) {
        if (!ownerValid(p)) return false;
        var sessions = SESSIONS.get(p.getUUID());
        return sessions != null && sessions.get(s.stack) == s && s.owner == p && s.level == p.level()
            && now(p) >= s.observed && equippedSlot(p, s.stack) == s.slot
            && WeaponLoadout.enabled(p) == s.loadoutEnabled
            && p.getAttachedOrElse(Guardians.DATA, null) == s.data && s.data.guardianClass() == s.guardianClass
            && Guardians.runtimeIfPresent(p).orElse(null) == s.runtime
            && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
            && WeaponPerks.selected(s.stack, EnGardeProfile.ID).filter(s.roll::equals).isPresent();
    }
    /** Actual held-ready writer, also called by master before swordAttack. Observes every
     * incoming identity even when this trait is absent, so selecting it cannot invent a ready.
     * Blocked handling waits for the first genuine unblocked ready; duplicate updates do nothing.
     */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions != null) {
            sessions.values().removeIf(s -> {
                if (s.owner != p || valid(p, s)) return false;
                s.cycle.changed(now(p)); return true;
            });
            for (var s : sessions.values()) {
                if (s.owner != p) continue;
                s.cycle.update(now(p), held(p, s), false); s.observed = now(p);
            }
            if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
        }
        if (!ownerValid(p)) return;
        var owner = OWNERS.get(p.getUUID());
        if (owner == null || owner.owner != p) {
            var old = SESSIONS.remove(p.getUUID());
            if (old != null) old.values().forEach(s -> s.cycle.clear());
            owner = new ReadyOwner(p); OWNERS.put(p.getUUID(), owner);
        }
        var stack = p.getMainHandItem();
        // Explicit preselection stow must not be undone by observing outgoing before vanilla.
        if (owner.stowedAt == now(p) && owner.outgoing == stack) return;
        boolean ready = WeaponLoadout.canUse(p) && !WeaponHandling.blocked(p);
        boolean newlyReady = owner.readiness.observe(now(p), stack, ready);
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, EnGardeProfile.ID).orElse(null);
        int slot = equippedSlot(p, stack);
        if (slot < 0 || p.getInventory().getSelectedSlot() != slot
            || !EnGardeProfile.supports(entry) || roll == null || !EnGardeProfile.rolls().contains(roll)
            || !entry.id().equals(roll.id())) return;
        sessions = SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new IdentityHashMap<>());
        var s = sessions.get(stack);
        if (s == null || !valid(p, s)) {
            if (s != null) s.cycle.changed(now(p));
            s = new Session(p, stack, entry, roll, slot); sessions.put(stack, s);
        }
        s.cycle.update(now(p), held(p, s), newlyReady && ready); s.observed = now(p);
    }
    private static Session active(ServerPlayer p) {
        if (p == null) return null;
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(p.getMainHandItem());
        return s != null && valid(p, s) && held(p, s) ? s : null;
    }

    /** AFTER successful payment, BEFORE any powered sword cleave/direct/splash damage. Master excludes empty swords/glaives. */
    public static Token capture(ServerPlayer p) {
        if (p == null) return Token.NONE;
        thread(p);
        // Readiness is established ONLY by update, never by this accepted-contact writer.
        var s = active(p);
        if (s == null) return Token.NONE;
        var contact = s.cycle.capture(now(p));
        return contact == null ? Token.NONE : new Token(s, contact);
    }
    /** Pure paid stack snapshot, shared across cleave/direct/splash. */
    public static float multiplier(ServerPlayer p, Token token) {
        if (p == null || token == null || token.source == null || !valid(p, token.source)) return 1f;
        return EnGardeProfile.multiplier(token.source.cycle.capturedActive(now(p), token.contact));
    }
    public static int remaining(ServerPlayer p) {
        var s = active(p); return s == null ? 0 : s.cycle.remaining(now(p));
    }
    /** Accepted outgoing selection, before vanilla changes slots. Retain original paid tokens. */
    public static void stowing(ServerPlayer p, ItemStack outgoing) {
        if (p == null) return;
        thread(p);
        var owner = OWNERS.get(p.getUUID());
        if (owner != null && owner.owner == p) {
            owner.readiness.stowing(outgoing); owner.outgoing = outgoing; owner.stowedAt = now(p);
        }
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(outgoing);
        if (s == null || !valid(p, s)) return;
        s.cycle.stowing(now(p)); s.observed = s.stowedAt = now(p);
    }
    public static void edited(ItemStack stack) {
        if (stack == null) return;
        var it = SESSIONS.values().iterator();
        while (it.hasNext()) {
            var sessions = it.next();
            var s = sessions.remove(stack);
            if (s != null) s.cycle.changed(now(s.owner));
            if (sessions.isEmpty()) it.remove();
        }
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && s.owner == p) { s.cycle.changed(now(p)); sessions.remove(stack); }
        if (sessions != null && sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var readyOwner = OWNERS.get(p.getUUID());
        if (readyOwner != null && readyOwner.owner == p) OWNERS.remove(p.getUUID());
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> {
            if (s.owner != p) return false;
            s.cycle.clear(); return true;
        });
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    public static void clear() {
        for (var sessions : SESSIONS.values()) for (var s : sessions.values()) s.cycle.clear();
        SESSIONS.clear(); OWNERS.clear();
    }
}
