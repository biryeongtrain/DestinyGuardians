package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.GuardianData;
import kim.biryeong.destiny.guardian.GuardianRuntime;
import kim.biryeong.destiny.guardian.Guardians;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Server-thread-only LOCAL held-source final blows. No generic ability-kill subscription.
 * Callers verify positive actual damage, a previously eligible enemy and the actual final blow.
 * The target must be dead; enemy eligibility is established by the caller before lethal damage.
 */
public final class WeaponMultikillClip {
    private static final Map<UUID, IdentityHashMap<ItemStack, Session>> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final WeaponCatalog.Entry entry;
        final WeaponPerks.Roll roll;
        final GuardianData data;
        final GuardianRuntime runtime;
        final GuardianClass guardianClass;
        final MultikillClipCycle cycle = new MultikillClipCycle();
        // Session identity revokes damage on edit/lifecycle; held epoch separately revokes kill rewards.
        final Set<LivingEntity> corpses = Collections.newSetFromMap(new WeakHashMap<>());
        Object heldEpoch = new Object();
        long observed;
        Session(ServerPlayer p, WeaponCatalog.Entry entry, WeaponPerks.Roll roll) {
            owner = p; level = p.level(); stack = p.getMainHandItem();
            this.entry = entry; this.roll = roll;
            data = Guardians.data(p);
            runtime = Guardians.runtimeIfPresent(p).orElse(null);
            guardianClass = data.guardianClass();
            observed = now(p);
        }
        void stow() { cycle.clear(); heldEpoch = new Object(); }
    }
    public static final class Token {
        public static final Token NONE = new Token(null, new MultikillClipCycle.Snapshot(1f));
        private final Session source;
        private final MultikillClipCycle.Snapshot snapshot;
        private final Object heldEpoch;
        private Token(Session source, MultikillClipCycle.Snapshot snapshot) {
            this.source = source; this.snapshot = snapshot;
            heldEpoch = source == null ? null : source.heldEpoch;
        }
        /** Live buff changes and ordinary stow preserve the value; source revocation makes it inert. */
        public float multiplier() {
            return source != null && valid(source.owner, source) ? snapshot.multiplier() : 1f;
        }
    }
    private WeaponMultikillClip() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && !AbilityService.inSuper(p);
    }
    private static boolean possessed(ServerPlayer p, ItemStack stack) {
        for (int i = 0; i < p.getInventory().getContainerSize(); i++)
            if (p.getInventory().getItem(i) == stack) return true;
        return false;
    }
    private static boolean equipped(ServerPlayer p, ItemStack stack) {
        return !WeaponLoadout.enabled(p)
                || WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == stack);
    }
    private static boolean valid(ServerPlayer p, Session s) {
        if (!ownerValid(p)) return false;
        var sessions = SESSIONS.get(p.getUUID());
        return sessions != null && sessions.get(s.stack) == s && s.owner == p && s.level == p.level()
                && now(p) >= s.observed && possessed(p, s.stack) && equipped(p, s.stack)
                && p.getAttachedOrElse(Guardians.DATA, null) == s.data
                && Guardians.runtimeIfPresent(p).orElse(null) == s.runtime
                && s.data.guardianClass() == s.guardianClass
                && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
                && WeaponPerks.selected(s.stack, MultikillClipProfile.ID).filter(s.roll::equals).isPresent();
    }
    public static void update(ServerPlayer p) {
        if (p == null) return;
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> !valid(p, s));
        for (var s : sessions.values()) {
            if (s.stack != p.getMainHandItem() || !WeaponLoadout.canUse(p)) s.stow();
            s.cycle.update(now(p));
            s.observed = now(p);
        }
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    private static Session held(ServerPlayer p) {
        if (p == null) return null;
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(p.getMainHandItem());
        return s != null && valid(p, s) && WeaponLoadout.canUse(p) ? s : null;
    }
    /** Pure HUD reads: no sessions, kills, or deadline changes. */
    public static int stacks(ServerPlayer p) {
        var s = held(p); return s == null ? 0 : s.cycle.stacks(now(p));
    }
    public static int remaining(ServerPlayer p) {
        var s = held(p); return s == null ? 0 : s.cycle.remaining(now(p));
    }
    private static Session bind(ServerPlayer p) {
        update(p);
        if (!ownerValid(p) || now(p) < 0 || !WeaponLoadout.canUse(p)) return null;
        var stack = p.getMainHandItem();
        var entry = WeaponItems.entry(stack);
        var selected = WeaponPerks.selected(stack, MultikillClipProfile.ID);
        if (entry.isEmpty() || selected.isEmpty() || !MultikillClipProfile.supports(entry.get())
                || !MultikillClipProfile.rolls().contains(selected.get())
                || !selected.get().id().equals(entry.get().id())
                || !possessed(p, stack) || !equipped(p, stack)) return null;
        var sessions = SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new IdentityHashMap<>());
        return sessions.computeIfAbsent(stack, ignored -> new Session(p, entry.get(), selected.get()));
    }
    /** Paid source-weapon emission only. The killing emission retains its pre-kill multiplier. */
    public static Token capture(ServerPlayer p) {
        var s = bind(p);
        return s == null ? Token.NONE : new Token(s, s.cycle.capture(now(p)));
    }
    private static boolean corpseSource(ServerPlayer p, Session s, LivingEntity corpse) {
        return s != null && corpse != null && corpse != p && !corpse.isAlive() && corpse.level() == s.level
                && valid(p, s);
    }
    /** After caller-confirmed positive damage AND final blow. A stowed source cannot gain live stacks. */
    public static void killed(ServerPlayer p, Token token, LivingEntity corpse) {
        if (p == null || token == null || token.source == null) return;
        update(p);
        var s = token.source;
        // Consume a confirmed corpse even while stowed; replaying that callback after re-equip cannot proc.
        if (corpseSource(p, s, corpse) && s.corpses.add(corpse)
                && token.heldEpoch == s.heldEpoch
                && p.getMainHandItem() == s.stack && WeaponLoadout.canUse(p)) s.cycle.killed(now(p));
    }
    /** Called only after positive real ammo insertion into this exact held source.
     * Ordinary reload and Marksman Dodge may call this; holster fill must not.
     */
    public static void reloaded(ServerPlayer p, ItemStack stack) {
        if (p == null || stack == null || p.getMainHandItem() != stack) return;
        var s = bind(p);
        if (s != null && s.stack == stack) s.cycle.reloaded(now(p));
    }
    /** Every accepted stow, even away-and-back in one tick. Existing damage snapshots survive. */
    public static void stowing(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && s.owner == p) s.stow();
    }
    /** Every real selection edit, including edit-away-and-back: revoke this exact source epoch. */
    public static void edited(ItemStack stack) {
        if (stack == null) return;
        var it = SESSIONS.values().iterator();
        while (it.hasNext()) {
            var sessions = it.next(); sessions.remove(stack);
            if (sessions.isEmpty()) it.remove();
        }
    }
    /** Drop, replacement or loadout removal; ordinary stow uses stowing(). */
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && s.owner == p) sessions.remove(stack);
        if (sessions != null && sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> s.owner == p);
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    public static void clear() { SESSIONS.clear(); }
}
