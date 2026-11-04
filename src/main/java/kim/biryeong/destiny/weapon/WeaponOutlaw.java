package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Source-bound precision credit. Stow/owner/level/actual-stack changes never transfer the proc. */
public final class WeaponOutlaw {
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final OutlawCycle cycle = new OutlawCycle();
        Session(ServerPlayer p) { owner=p; level=p.level(); stack=p.getMainHandItem(); }
    }
    public static final class Token {
        public static final Token NONE = new Token(null);
        private final Session session;
        private Token(Session session) { this.session=session; }
    }
    private WeaponOutlaw() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean eligible(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && !AbilityService.inSuper(p) && WeaponLoadout.canUse(p)
                && WeaponPerks.selected(p.getMainHandItem(),OutlawProfile.ID).isPresent();
    }
    public static void update(ServerPlayer p) {
        if (!eligible(p)) { cleanup(p); return; }
        var s=SESSIONS.get(p.getUUID());
        if (s==null || s.owner!=p || s.level!=p.level() || s.stack!=p.getMainHandItem()) SESSIONS.put(p.getUUID(),new Session(p));
    }
    public static void selecting(ServerPlayer p,int slot) {
        if (slot>=0 && slot<9 && slot!=p.getInventory().getSelectedSlot()) cleanup(p);
    }
    /** Pure HUD/reload-plan query. Does not bind, tick or touch ammo. */
    public static int remaining(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());
        return eligible(p) && s!=null && s.owner==p && s.level==p.level() && s.stack==p.getMainHandItem()
                ? s.cycle.remaining(now(p),OutlawProfile.perk().durationTicks()) : 0;
    }
    public static Token capture(ServerPlayer p) {
        update(p); var s=SESSIONS.get(p.getUUID()); return s==null ? Token.NONE : new Token(s);
    }
    public static void killed(ServerPlayer p,Token token,boolean precision) {
        var s=token.session;
        if (precision && s!=null && s.owner==p && SESSIONS.get(p.getUUID())==s && eligible(p)
                && s.level==p.level() && s.stack==p.getMainHandItem()) s.cycle.precisionKilled(now(p),OutlawProfile.perk().durationTicks());
    }
    /** Sample once at real reload start. An in-progress animation never jumps when a buff expires. */
    public static WeaponReloadPolicy.Plan plan(ServerPlayer p,WeaponCatalog.Entry entry,WeaponProfile base) {
        if (remaining(p)<=0) return new WeaponReloadPolicy.Plan(base.firstReloadTicks(),base.reloadTicks(),base.roundsPerInsert());
        if (!WeaponItems.entry(p.getMainHandItem()).filter(entry::equals).isPresent())
            throw new IllegalArgumentException("Reload plan must belong to held weapon");
        var boost=OutlawProfile.reload(entry);
        return new WeaponReloadPolicy.Plan(boost.firstTicks(),boost.intervalTicks(),base.roundsPerInsert());
    }
    public static void changed(ServerPlayer p,ItemStack stack) {
        var s=SESSIONS.get(p.getUUID()); if (s!=null && s.owner==p && s.stack==stack) cleanup(p);
    }
    public static void cleanup(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID()); if (s!=null && s.owner==p) SESSIONS.remove(p.getUUID());
    }
    public static void clear() { SESSIONS.clear(); }
}
