package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Successful grenade ability.activate on the original held weapon, never projectile release.
 * All mutations are server-thread owned. Damage/active queries never bind or prune state.
 * Shared registry, ability, lifecycle, HUD and paid-emission wiring belong to the coordinator. */
public final class WeaponOsmosis {
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
    /** Accepted stow can run before the inventory callback replaces the outgoing hand. */
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
        final OsmosisCycle cycle = new OsmosisCycle();
        Session(ServerPlayer p, WeaponCatalog.Entry entry, WeaponPerks.Roll roll) {
            owner = p; stack = p.getMainHandItem(); this.entry = entry; this.roll = roll;
            lease = new Lease(identity(p), now(p));
        }
        void revoke() { lease.revoke(); cycle.clear(); }
    }
    public static final class Token {
        public static final Token NONE = new Token(null, null, null, null);
        private final Session source;
        private final Ability grenade;
        private final WeaponCharacteristics.Damage element;
        private final OsmosisCycle.Token accepted;
        private boolean consumed;
        private Token(Session source, Ability grenade, WeaponCharacteristics.Damage element, OsmosisCycle.Token accepted) {
            this.source = source; this.grenade = grenade; this.element = element; this.accepted = accepted;
        }
    }
    private WeaponOsmosis() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("Osmosis is main server thread owned");
    }
    private static Identity identity(ServerPlayer p) {
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        return new Identity(p, p.level(), p.getMainHandItem(), data,
                Guardians.runtimeIfPresent(p).orElse(null), data == null ? null : data.guardianClass(),
                WeaponLoadout.enabled(p), p.getInventory().getSelectedSlot());
    }
    private static boolean ownerValid(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isDeadOrDying() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
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
                && WeaponPerks.selected(s.stack, OsmosisProfile.ID).filter(s.roll::equals).isPresent();
    }
    private static Ability grenade(ServerPlayer p) {
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        if (data == null) return null;
        var id = data.loadout().map(l -> l.get(AbilitySlot.GRENADE)).orElse(null);
        var ability = id == null ? null : AbilityRegistry.get(id).orElse(null);
        return ability != null && ability.slot() == AbilitySlot.GRENADE
                && ability.guardianClass() == data.guardianClass() ? ability : null;
    }
    private static WeaponCharacteristics.Damage element(Ability grenade) {
        if (grenade == null || grenade.element() == null) return null;
        return switch (grenade.element()) {
            case ARC -> WeaponCharacteristics.Damage.ARC;
            case SOLAR -> WeaponCharacteristics.Damage.SOLAR;
            case VOID -> WeaponCharacteristics.Damage.VOID;
            case KINETIC -> null;
        };
    }
    /** Observes existing episodes only. An old same-UUID player cannot prune a replacement owner. */
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
        else s.lease.observe(now(p));
    }
    /** BEFORE grenade ability.activate. Captures the original hand/roll/player/world/runtime/class
     * and equipped grenade element; failed input/activate must never call abilityUsed. */
    public static Token accepted(ServerPlayer p) {
        if (p == null) return Token.NONE;
        thread(p); update(p);
        var stack = p.getMainHandItem();
        if (!ownerValid(p) || !held(p, stack) || fenced(p, stack) || now(p) < 0) return Token.NONE;
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, OsmosisProfile.ID).orElse(null);
        var grenade = grenade(p);
        var element = element(grenade);
        if (!OsmosisProfile.supports(entry) || roll == null || !OsmosisProfile.rolls().contains(roll)
                || !entry.id().equals(roll.id()) || element == null) return Token.NONE;
        var previous = SESSIONS.get(p.getUUID());
        if (previous != null && previous.owner != p) {
            previous.revoke(); SESSIONS.remove(p.getUUID(), previous);
        }
        var s = SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new Session(p, entry, roll));
        return new Token(s, grenade, element, s.cycle.accepted(element));
    }
    /** Exactly once AFTER successful activate/resource payment, not grenade release.
     * A full/no-reserve attempt spends the sole refill until stow. Only a positive transfer
     * cancels pending reload, persists ammo and broadcasts inventory; conversion always updates HUD. */
    public static int abilityUsed(ServerPlayer p, Token token) {
        if (token == null || token == Token.NONE || token.consumed) return 0;
        token.consumed = true;
        if (p == null) return 0;
        thread(p); update(p);
        var s = token.source;
        if (!valid(p, s) || token.grenade != grenade(p) || token.element != element(token.grenade)) return 0;
        var profile = WeaponProfile.forEntry(s.entry);
        var ammo = WeaponItems.magazine(s.stack, profile);
        int moved = s.cycle.abilityUsed(token.accepted, ammo, profile.magazine());
        if (moved > 0) {
            WeaponRuntime.cancelForGrenadeRefill(p, s.stack);
            WeaponItems.save(s.stack, ammo);
            p.getInventory().setChanged(); p.containerMenu.broadcastChanges();
        }
        CombatHud.update(p);
        return moved;
    }
    /** Pure query, suitable for snapshotting each individually paid emission before its trace. */
    public static WeaponCharacteristics.Damage damage(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry) {
        var canonical = WeaponCharacteristics.of(entry).damage();
        if (p == null) return canonical;
        var s = SESSIONS.get(p.getUUID());
        return valid(p, s) && s.stack == stack && s.entry.equals(entry) ? s.cycle.damage(canonical) : canonical;
    }
    public static boolean active(ServerPlayer p) {
        if (p == null) return false;
        var s = SESSIONS.get(p.getUUID());
        return valid(p, s) && s.cycle.active();
    }
    /** Accepted stow revokes pending use and conversion, even while outgoing hand is still exposed. */
    public static void stowing(ServerPlayer p, ItemStack stack) {
        if (p == null || stack == null) return;
        thread(p);
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner != p) return;
        STOWED.computeIfAbsent(p.getUUID(), ignored -> new IdentityHashMap<>())
                .put(stack, new StowFence(p, stack, now(p)));
        if (s != null && s.stack == stack) { s.revoke(); SESSIONS.remove(p.getUUID(), s); }
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
