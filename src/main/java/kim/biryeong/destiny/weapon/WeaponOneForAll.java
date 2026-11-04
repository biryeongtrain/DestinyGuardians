package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Server-thread-only, identity-bound source sessions. Stowed, still-owned projectiles may credit.
 * Runtime must capture only paid weapon emissions/sword contacts and confirm only positive HP damage.
 */
public final class WeaponOneForAll {
    private static final Map<UUID, IdentityHashMap<ItemStack, Session>> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final WeaponPerks.Roll selection;
        // A new session creates a new selection edit epoch. Removed sessions can never be reattached.
        final Object editEpoch = new Object();
        final OneForAllCycle cycle = new OneForAllCycle(
                OneForAllProfile.hitWindowTicks(), OneForAllProfile.durationTicks());
        Session(ServerPlayer p, WeaponPerks.Roll selection) {
            owner = p; level = p.level(); stack = p.getMainHandItem(); this.selection = selection;
        }
    }
    public static final class Token {
        public static final Token NONE = new Token(null, 1f);
        private final Session session;
        private final Object editEpoch;
        private final float multiplier;
        private Token(Session session, float multiplier) {
            this.session = session;
            this.editEpoch = session == null ? null : session.editEpoch;
            this.multiplier = multiplier;
        }
        public float multiplier() { return multiplier; }
    }
    private WeaponOneForAll() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && !AbilityService.inSuper(p);
    }
    private static boolean allowed(ServerPlayer p) { return ownerValid(p) && WeaponLoadout.canUse(p); }
    private static boolean possessed(ServerPlayer p, ItemStack stack) {
        for (int i = 0; i < p.getInventory().getContainerSize(); i++)
            if (p.getInventory().getItem(i) == stack) return true;
        return false;
    }
    private static boolean valid(ServerPlayer p, Session session) {
        return ownerValid(p) && session.owner == p && session.level == p.level()
                && possessed(p, session.stack)
                && (!WeaponLoadout.enabled(p) || WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == session.stack))
                && WeaponItems.entry(session.stack).filter(OneForAllProfile::supports)
                    .filter(e -> e.id().equals(session.selection.id())).isPresent()
                && WeaponPerks.selected(session.stack, OneForAllProfile.ID)
                    .filter(session.selection::equals).isPresent();
    }
    public static void update(ServerPlayer p) {
        if (p == null) return;
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> !valid(p, s));
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    private static Session held(ServerPlayer p) {
        if (p == null) return null;
        var sessions = SESSIONS.get(p.getUUID());
        var session = sessions == null ? null : sessions.get(p.getMainHandItem());
        return session != null && allowed(p) && valid(p, session) ? session : null;
    }
    /** Pure HUD reads: never create a session, collect a target, or move a deadline. Hidden while stowed. */
    public static int progress(ServerPlayer p) {
        var session = held(p); return session == null ? 0 : session.cycle.progress(now(p));
    }
    public static int remaining(ServerPlayer p) {
        var session = held(p); return session == null ? 0 : session.cycle.remaining(now(p));
    }
    public static Token capture(ServerPlayer p) {
        update(p);
        if (!allowed(p)) return Token.NONE;
        var stack = p.getMainHandItem();
        var selection = WeaponPerks.selected(stack, OneForAllProfile.ID);
        if (selection.isEmpty() || !OneForAllProfile.rolls().contains(selection.get())
                || WeaponItems.entry(stack).filter(OneForAllProfile::supports).isEmpty()
                || !possessed(p, stack)) return Token.NONE;
        var sessions = SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new IdentityHashMap<>());
        var session = sessions.computeIfAbsent(stack, ignored -> new Session(p, selection.get()));
        return new Token(session, session.cycle.remaining(now(p)) > 0 ? OneForAllProfile.multiplier() : 1f);
    }
    /** AFTER positive actual HP damage to a previously validated enemy. Lethal hits count by UUID;
     * never recheck isAlive/Combat.isEnemy here. Direct/splash and paid sword light/heavy share this API.
     */
    public static void confirmed(ServerPlayer p, Token token, LivingEntity target) {
        if (p == null || token == null || target == null || token.session == null) return;
        update(p);
        var session = token.session;
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions != null && sessions.get(session.stack) == session
                && token.editEpoch == session.editEpoch && valid(p, session)
                && target != p && target.level() == session.level)
            session.cycle.confirmed(now(p), target.getUUID());
    }
    /** Every real trait selection edit must call this, including edit-away-and-back within one tick. */
    public static void edited(ItemStack stack) {
        if (stack == null) return;
        SESSIONS.values().forEach(sessions -> sessions.remove(stack));
        SESSIONS.values().removeIf(Map::isEmpty);
    }
    /** Drop/source replacement hook; removal invalidates all captured epochs for this exact reference. */
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        var session = sessions.get(stack);
        if (session != null && session.owner == p) sessions.remove(stack);
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
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
