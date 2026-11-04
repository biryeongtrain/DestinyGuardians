package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.combat.Combat;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import java.util.*;

/** Held-only LOCAL buff, with source-stack emission snapshots. Server thread owned. */
public final class WeaponSurrounded {
    private static final Map<UUID, IdentityHashMap<ItemStack, Session>> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final WeaponCatalog.Entry entry;
        final WeaponPerks.Roll roll;
        final SurroundedCycle cycle = new SurroundedCycle();
        long observed = -1;
        Session(ServerPlayer p, WeaponCatalog.Entry entry, WeaponPerks.Roll roll) {
            owner = p; level = p.level(); stack = p.getMainHandItem(); this.entry = entry; this.roll = roll;
        }
    }
    public static final class Token {
        public static final Token NONE = new Token(null, new SurroundedCycle.Snapshot(1));
        private final Session source;
        private final SurroundedCycle.Snapshot snapshot;
        private Token(Session source, SurroundedCycle.Snapshot snapshot) { this.source = source; this.snapshot = snapshot; }
        /** Pure: proximity/linger changes never retime an emission; revoked sources are inert. */
        public float multiplier() {
            return source != null && valid(source.owner, source) ? snapshot.multiplier() : 1;
        }
    }
    private WeaponSurrounded() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && !AbilityService.inSuper(p);
    }
    private static boolean possessed(ServerPlayer p, ItemStack stack) {
        for (int i = 0; i < p.getInventory().getContainerSize(); i++)
            if (p.getInventory().getItem(i) == stack) return true;
        return false;
    }
    private static boolean valid(ServerPlayer p, Session s) {
        var sessions = SESSIONS.get(p.getUUID());
        return sessions != null && sessions.get(s.stack) == s && s.owner == p && s.level == p.level()
                && ownerValid(p) && possessed(p, s.stack)
                // Stowed emissions retain their own equipped source, regardless of the new held gun.
                && (!WeaponLoadout.enabled(p) || WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == s.stack))
                && now(p) >= s.observed
                && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
                && WeaponPerks.selected(s.stack, SurroundedProfile.ID).filter(s.roll::equals).isPresent();
    }
    private static boolean enemy(ServerPlayer p, LivingEntity e) {
        return e.level() == p.level() && e.isAlive() && !e.isRemoved() && !e.isSpectator()
                && !(e instanceof Player) && !(e instanceof ArmorStand)
                && Combat.isEnemy(p, e) && !p.isAlliedTo(e)
                && !(e instanceof TamableAnimal tame && tame.isTame());
    }
    private static int nearby(ServerPlayer p) {
        var origin = p.position();
        if (!Double.isFinite(origin.x) || !Double.isFinite(origin.y) || !Double.isFinite(origin.z)) return 0;
        // Query loaded entity storage only. Padding admits exact foot-point boundary contacts;
        // the following sphere predicate still rejects every point beyond 15 metres.
        var bounds = new AABB(origin, origin).inflate(SurroundedProfile.radius() + 1e-6);
        int count = 0;
        for (var e : p.level().getEntitiesOfClass(LivingEntity.class, bounds, e -> enemy(p, e))) {
            var point = e.position();
            if (SurroundedCycle.withinRadius(point.x - origin.x, point.y - origin.y, point.z - origin.z)
                    && ++count >= SurroundedProfile.minimumEnemies()) break;
        }
        return count;
    }

    /** Tick only the held eligible selected source. Stow clears live proximity state, retaining
     * the still-owned source session so an already-paid projectile keeps its emission snapshot.
     */
    public static void update(ServerPlayer p) {
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions != null) {
            sessions.values().removeIf(s -> !valid(p, s));
            for (var s : sessions.values())
                if (s.stack != p.getMainHandItem() || !WeaponLoadout.canUse(p)) s.cycle.clear();
            if (sessions.isEmpty()) { SESSIONS.remove(p.getUUID()); sessions = null; }
        }
        if (!ownerValid(p) || !WeaponLoadout.canUse(p)) return;
        var stack = p.getMainHandItem();
        var entry = WeaponItems.entry(stack);
        var selected = WeaponPerks.selected(stack, SurroundedProfile.ID);
        if (entry.isEmpty() || selected.isEmpty() || !possessed(p, stack)
                || !SurroundedProfile.rolls().contains(selected.get())
                || !selected.get().id().equals(entry.get().id())) return;
        if (sessions == null) {
            sessions = new IdentityHashMap<>();
            SESSIONS.put(p.getUUID(), sessions);
        }
        var s = sessions.get(stack);
        if (s == null) {
            s = new Session(p, entry.get(), selected.get());
            sessions.put(stack, s);
        }
        s.cycle.update(now(p), nearby(p));
        s.observed = now(p);
    }

    /** Paid emission or paid melee contact only. Rechecks proximity even within the same tick. */
    public static Token capture(ServerPlayer p) {
        update(p);
        var s = held(p);
        if (s == null || !valid(p, s)) return Token.NONE;
        return new Token(s, s.cycle.capture(now(p), SurroundedProfile.multiplier(s.entry)));
    }
    private static Session held(ServerPlayer p) {
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(p.getMainHandItem());
        return s != null && valid(p, s) && WeaponLoadout.canUse(p) ? s : null;
    }
    /** Pure HUD queries: no binding, scanning, proc or timer refresh. */
    public static boolean active(ServerPlayer p) {
        var s = held(p);
        return s != null && s.cycle.active(now(p));
    }
    public static int remaining(ServerPlayer p) {
        var s = held(p);
        return s != null ? s.cycle.remaining(now(p)) : 0;
    }
    /** Accepted stow, including away-and-back in one tick; paid emissions remain valid. */
    public static void stowing(ServerPlayer p, ItemStack stack) {
        var sessions=SESSIONS.get(p.getUUID());
        var s=sessions==null?null:sessions.get(stack);
        if(s!=null && s.owner==p)s.cycle.clear();
    }
    /** Session identity is the edit epoch: even same-tick clear/reselect cannot revive old tokens. */
    public static void edited(ItemStack stack) {
        var it = SESSIONS.values().iterator();
        while (it.hasNext()) {
            var sessions = it.next(); sessions.remove(stack);
            if (sessions.isEmpty()) it.remove();
        }
    }
    /** Revokes a source for a real edit/drop/loadout removal. Ordinary stow uses update(). */
    public static void changed(ServerPlayer p, ItemStack stack) {
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && s.owner == p) {
            sessions.remove(stack);
            if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
        }
    }
    public static void cleanup(ServerPlayer p) {
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions != null) {
            sessions.values().removeIf(s -> s.owner == p);
            if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
        }
    }
    public static void clear() { SESSIONS.clear(); }
}
