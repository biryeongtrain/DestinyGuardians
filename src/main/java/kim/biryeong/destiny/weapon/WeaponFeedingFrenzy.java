package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Source-item final-blow credit; an emitted projectile never rewards a replacement weapon. */
public final class WeaponFeedingFrenzy {
    private static final Map<UUID, IdentityHashMap<ItemStack, Session>> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final FeedingFrenzyCycle cycle = new FeedingFrenzyCycle();
        Session(ServerPlayer p) { owner=p; level=p.level(); stack=p.getMainHandItem(); }
    }
    public static final class Token {
        public static final Token NONE = new Token(null);
        private final Session session;
        private Token(Session session) { this.session=session; }
    }
    private WeaponFeedingFrenzy() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected();
    }
    private static boolean possessed(ServerPlayer p, ItemStack stack) {
        for (int i=0; i<p.getInventory().getContainerSize(); i++)
            if (p.getInventory().getItem(i)==stack) return true;
        return false;
    }
    private static boolean valid(ServerPlayer p, Session s) {
        return s.owner==p && s.level==p.level() && ownerValid(p) && possessed(p,s.stack)
                && WeaponPerks.selected(s.stack,FeedingFrenzyProfile.ID).isPresent();
    }
    public static void update(ServerPlayer p) {
        if (!ownerValid(p)) { cleanup(p); return; }
        var sessions=SESSIONS.get(p.getUUID());
        if (sessions==null) return;
        sessions.values().removeIf(s -> !valid(p,s));
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    private static Session held(ServerPlayer p) {
        var sessions=SESSIONS.get(p.getUUID());
        var s=sessions==null ? null : sessions.get(p.getMainHandItem());
        return s!=null && valid(p,s) && WeaponLoadout.canUse(p) && !AbilityService.inSuper(p) ? s : null;
    }
    /** Pure HUD/reload queries: never bind, tick, reload, or refresh a deadline. */
    public static int stacks(ServerPlayer p) {
        var s=held(p); return s==null ? 0 : s.cycle.stacks(now(p),FeedingFrenzyProfile.durationTicks());
    }
    public static int remaining(ServerPlayer p) {
        var s=held(p); return s==null ? 0 : s.cycle.remaining(now(p),FeedingFrenzyProfile.durationTicks());
    }
    public static Token capture(ServerPlayer p) {
        update(p);
        if (!ownerValid(p) || !WeaponLoadout.canUse(p) || AbilityService.inSuper(p)
                || WeaponPerks.selected(p.getMainHandItem(),FeedingFrenzyProfile.ID).isEmpty()) return Token.NONE;
        var sessions=SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new IdentityHashMap<>());
        return new Token(sessions.computeIfAbsent(p.getMainHandItem(), ignored -> new Session(p)));
    }
    /** Called only after a paid source transaction confirms an actual final blow. */
    public static void killed(ServerPlayer p, Token token) {
        var s=token.session;
        var sessions=SESSIONS.get(p.getUUID());
        if (s!=null && sessions!=null && sessions.get(s.stack)==s && valid(p,s))
            s.cycle.killed(now(p),FeedingFrenzyProfile.durationTicks());
    }
    /** Snapshot once at real reload start; later expiry/kills do not retime an in-flight reload. */
    public static WeaponReloadPolicy.Plan plan(ServerPlayer p, WeaponCatalog.Entry entry, WeaponProfile base) {
        return plan(p,entry,new WeaponReloadPolicy.Plan(base.firstReloadTicks(),base.reloadTicks(),base.roundsPerInsert()));
    }
    public static WeaponReloadPolicy.Plan plan(ServerPlayer p, WeaponCatalog.Entry entry, WeaponReloadPolicy.Plan base) {
        int count=stacks(p);
        if (count==0) return base;
        if (WeaponItems.entry(p.getMainHandItem()).filter(entry::equals).isEmpty())
            throw new IllegalArgumentException("Reload plan must belong to the held weapon");
        var boost=FeedingFrenzyProfile.reload(entry,count);
        return new WeaponReloadPolicy.Plan(boost.firstTicks(),boost.intervalTicks(),base.roundsPerInsert());
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        var sessions=SESSIONS.get(p.getUUID());
        var s=sessions==null ? null : sessions.get(stack);
        if (s!=null && s.owner==p) {
            sessions.remove(stack);
            if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
        }
    }
    /** Exact successful trait edits invalidate even an unobserved same-tick clear/reselect. */
    public static void edited(ItemStack stack) {
        var it=SESSIONS.values().iterator();
        while (it.hasNext()) {
            var sessions=it.next(); sessions.remove(stack);
            if (sessions.isEmpty()) it.remove();
        }
    }
    public static void cleanup(ServerPlayer p) {
        var sessions=SESSIONS.get(p.getUUID());
        if (sessions!=null) {
            sessions.values().removeIf(s -> s.owner==p);
            if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
        }
    }
    public static void clear() { SESSIONS.clear(); }
}
