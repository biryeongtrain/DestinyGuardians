package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Precision-hit credit belongs to this exact equipped bow and ownership generation, not saved NBT.
 * Stowing invalidates even in-flight tokens. HUD queries are pure; no ammo/damage/reload bonus.
 */
public final class WeaponArcherTempo {
    private static final Map<UUID,Session> SESSIONS=new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;final ServerLevel level;final ItemStack stack;
        final ArcherTempoCycle cycle=new ArcherTempoCycle();
        Session(ServerPlayer p) {owner=p;level=p.level();stack=p.getMainHandItem();}
    }
    public static final class Token {
        public static final Token NONE=new Token(null);
        private final Session session;private boolean consumed;
        private Token(Session session) {this.session=session;}
    }
    private WeaponArcherTempo() {}
    private static long now(ServerPlayer p) {return p.level().getServer().getTickCount();}
    private static boolean eligible(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && !AbilityService.inSuper(p) && WeaponLoadout.canUse(p)
                && WeaponItems.entry(p.getMainHandItem()).filter(e->e.family().equals("bow")).isPresent()
                && WeaponPerks.selected(p.getMainHandItem(),ArcherTempoProfile.ID).isPresent();
    }
    public static void update(ServerPlayer p) {
        if(!eligible(p)) {cleanup(p);return;}
        var s=SESSIONS.get(p.getUUID());
        if(s==null || s.owner!=p || s.level!=p.level() || s.stack!=p.getMainHandItem())SESSIONS.put(p.getUUID(),new Session(p));
    }
    public static void selecting(ServerPlayer p,int slot) {
        if(slot>=0 && slot<9 && slot!=p.getInventory().getSelectedSlot())cleanup(p);
    }
    public static int remaining(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());
        return eligible(p) && s!=null && s.owner==p && s.level==p.level() && s.stack==p.getMainHandItem()
                ?s.cycle.remaining(now(p)):0;
    }
    public static Token capture(ServerPlayer p) {
        update(p);var s=SESSIONS.get(p.getUUID());return s==null?Token.NONE:new Token(s);
    }
    /** Called only after a real emitted arrow caused positive actual precision damage. No kill required. */
    public static void confirmed(ServerPlayer p,Token token,boolean precision) {
        var s=token.session;
        if(token.consumed || s==null)return;
        token.consumed=true;
        if(precision && s.owner==p && SESSIONS.get(p.getUUID())==s && eligible(p)
                && s.level==p.level() && s.stack==p.getMainHandItem())s.cycle.precisionHit(now(p));
    }
    /** Project policy: snapshot once at actual draw start, including buffered nock completion.
     * Mid-draw expiry/proc does not retime an accepted draw. This is not proven original-engine behavior.
     */
    public static WeaponProfile draw(ServerPlayer p,WeaponCatalog.Entry e,WeaponProfile base) {
        if(remaining(p)<=0)return base;
        if(!WeaponItems.entry(p.getMainHandItem()).filter(e::equals).isPresent())
            throw new IllegalArgumentException("Draw plan must belong to held bow");
        return ArcherTempoProfile.accelerated(e,base);
    }
    public static void changed(ServerPlayer p,ItemStack stack) {
        var s=SESSIONS.get(p.getUUID());if(s!=null && s.owner==p && s.stack==stack)cleanup(p);
    }
    public static void cleanup(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());if(s!=null && s.owner==p)SESSIONS.remove(p.getUUID());
    }
    public static void clear() {SESSIONS.clear();}
}
