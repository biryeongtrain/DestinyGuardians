package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Ace's intrinsic, never an editable legendary socket or a saved counter granting free ammunition. */
public final class WeaponAce {
    public static final float PVE_MULTIPLIER = 1.68f;
    public static final double MORI_FALLOFF = .85;
    private static final Map<UUID, IdentityHashMap<ItemStack, Session>> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final AceCycle cycle = new AceCycle();
        boolean reloadPending, reloadInserted;
        int generation;
        Session(ServerPlayer p) { owner = p; level = p.level(); stack = p.getMainHandItem(); }
    }
    public static final class Token {
        public static final Token NONE = new Token(null, false);
        private final Session session;
        private final boolean empowered;
        private final int generation;
        private final Set<LivingEntity> kills = Collections.newSetFromMap(new IdentityHashMap<>());
        private Token(Session s, boolean empowered) { session = s; this.empowered = empowered; generation = s == null ? -1 : s.generation; }
        public boolean empowered() { return empowered; }
        public float multiplier(boolean pvp) { return empowered ? (pvp ? 1.29f : PVE_MULTIPLIER) : 1; }
    }
    private WeaponAce() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean eligible(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && !AbilityService.inSuper(p) && WeaponLoadout.canUse(p)
                && WeaponItems.entry(p.getMainHandItem()).filter(WeaponExotics::ace).isPresent();
    }
    private static boolean ownerValid(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected() && !AbilityService.inSuper(p);
    }
    private static Session matching(ServerPlayer p) {
        var owned = SESSIONS.get(p.getUUID());
        var s = owned == null ? null : owned.get(p.getMainHandItem());
        return eligible(p) && s != null && s.owner == p && s.level == p.level() ? s : null;
    }
    private static boolean stillOwned(ServerPlayer p, ItemStack stack) {
        for (int i=0; i<p.getInventory().getContainerSize(); i++) if (p.getInventory().getItem(i)==stack) return true;
        return false;
    }
    private static void stow(Session s) {
        s.cycle.stowed(); s.reloadPending = s.reloadInserted = false; s.generation++;
    }
    public static void update(ServerPlayer p) {
        if (!ownerValid(p)) { cleanup(p); return; }
        var owned = SESSIONS.get(p.getUUID());
        if (owned != null) {
            owned.values().removeIf(s -> s.owner != p || s.level != p.level() || !stillOwned(p,s.stack)
                    || WeaponItems.entry(s.stack).filter(WeaponExotics::ace).isEmpty());
            for (var s : owned.values()) if (s.stack != p.getMainHandItem()) stow(s);
            owned.values().removeIf(s -> s.stack != p.getMainHandItem() && !s.cycle.killEligible(now(p))
                    && s.cycle.fireflyRemaining(now(p)) == 0);
        }
        if (!eligible(p)) return;
        owned = SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new IdentityHashMap<>());
        owned.computeIfAbsent(p.getMainHandItem(), ignored -> new Session(p));
    }
    public static void stowing(ServerPlayer p) {
        var owned = SESSIONS.get(p.getUUID());
        if (owned != null) for (var s : owned.values()) if (s.owner == p) stow(s);
    }
    /** A validated mutation can stow and restore the same object before the next tick. */
    public static void inventoryStowing(ServerPlayer p, ItemStack previous) {
        var owned = SESSIONS.get(p.getUUID());
        var s = owned == null ? null : owned.get(previous);
        if (s != null && s.owner == p) stow(s);
    }
    /** Called ONCE only after WeaponCycle has paid for a real Ace emission. Misses spend a Mori round too. */
    public static Token shot(ServerPlayer p, WeaponCatalog.Entry entry) {
        if (!WeaponExotics.ace(entry)) return Token.NONE;
        update(p);
        var s = matching(p);
        return s == null ? Token.NONE : new Token(s, s.cycle.shot());
    }
    public static WeaponBallistics.Profile ballistics(WeaponBallistics.Profile base, Token token) {
        return token.empowered ? new WeaponBallistics.Profile(base.start() * MORI_FALLOFF,
                base.end() * MORI_FALLOFF, base.floor(), base.precision()) : base;
    }
    /** Caller has observed positive actual HP/absorption loss from this exact paid direct shot. */
    public static void confirmedKill(ServerPlayer p, Token token, LivingEntity target, boolean precision) {
        var s = token.session;
        if (s == null || matching(p) != s || token.generation != s.generation || target.isAlive() || target.level() != s.level || !token.kills.add(target)) return;
        s.cycle.killed(now(p), precision);
        if (precision) WeaponFirefly.explode(p, target);
    }
    public static int rounds(ServerPlayer p) { var s = matching(p); return s == null ? 0 : s.cycle.rounds(); }
    public static int fireflyRemaining(ServerPlayer p) { var s = matching(p); return s == null ? 0 : s.cycle.fireflyRemaining(now(p)); }
    /** +50 Reload Speed, captured at reload start using the same pinned historical HC curve. */
    public static WeaponReloadPolicy.Plan plan(ServerPlayer p, WeaponCatalog.Entry entry, WeaponReloadPolicy.Plan base) {
        if (!WeaponExotics.ace(entry) || fireflyRemaining(p) <= 0) return base;
        int ticks = fireflyReloadTicks(entry);
        return new WeaponReloadPolicy.Plan(ticks, ticks, 0);
    }
    public static int fireflyReloadTicks(WeaponCatalog.Entry entry) {
        if (!WeaponExotics.ace(entry)) throw new IllegalArgumentException("Not canonical Ace");
        int stat = Math.clamp(WeaponCharacteristics.of(entry).stats().get("4188031367") + 50, 0, 100);
        return (int)Math.ceil((.00006137590643 * stat * stat - .02385522011 * stat + 3.600042253) * 20);
    }
    public static void reloadStarted(ServerPlayer p, ItemStack stack) {
        update(p); var s = matching(p);
        if (s != null && s.stack == stack) { s.reloadPending = true; s.reloadInserted = false; }
    }
    /** Early W65 credit does not grant Mori until full ready/recovery finishes. */
    public static void reloadTick(ServerPlayer p, ItemStack stack, boolean inserted, boolean reloading) {
        var s = matching(p);
        if (s == null || s.stack != stack || !s.reloadPending) return;
        s.reloadInserted |= inserted;
        if (!reloading) {
            if (s.reloadInserted) s.cycle.reloaded(now(p));
            s.reloadPending = s.reloadInserted = false;
        }
    }
    /** Marksman's real instant reload is a completion too; holster fills never call this. */
    public static void instantReload(ServerPlayer p, ItemStack stack) {
        update(p); var s = matching(p);
        if (s != null && s.stack == stack) { s.reloadPending = s.reloadInserted = false; s.cycle.reloaded(now(p)); }
    }
    public static void cancelReload(ServerPlayer p) {
        var owned = SESSIONS.get(p.getUUID());
        if (owned != null) for (var s : owned.values()) if (s.owner == p) s.reloadPending = s.reloadInserted = false;
    }
    public static void selecting(ServerPlayer p, int slot) {
        if (slot >= 0 && slot < 9 && slot != p.getInventory().getSelectedSlot()) stowing(p);
    }
    public static void cleanup(ServerPlayer p) {
        var owned = SESSIONS.get(p.getUUID());
        if (owned != null) { owned.values().removeIf(s -> s.owner == p); if (owned.isEmpty()) SESSIONS.remove(p.getUUID()); }
    }
    public static void clear() { SESSIONS.clear(); }
}
