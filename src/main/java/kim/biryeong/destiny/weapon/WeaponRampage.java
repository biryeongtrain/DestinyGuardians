package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Item-identity buffs keep decaying through stow; emitted damage and kill credit retain their source. */
public final class WeaponRampage {
    private static final Map<UUID,IdentityHashMap<ItemStack,Session>> SESSIONS=new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final RampageCycle cycle=new RampageCycle();
        Session(ServerPlayer p) {owner=p;level=p.level();stack=p.getMainHandItem();}
    }
    public static final class Token {
        public static final Token NONE=new Token(null,1);
        private final Session session;
        private final float multiplier;
        private Token(Session s,float multiplier) {session=s;this.multiplier=multiplier;}
        public float multiplier() {return multiplier;}
    }
    private WeaponRampage() {}
    private static long now(ServerPlayer p) {return p.level().getServer().getTickCount();}
    private static boolean ownerValid(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected();
    }
    private static boolean possessed(ServerPlayer p,ItemStack stack) {
        for(int i=0;i<p.getInventory().getContainerSize();i++)
            if(p.getInventory().getItem(i)==stack)return true;
        return false;
    }
    private static boolean valid(ServerPlayer p,Session s) {
        return s.owner==p && s.level==p.level() && ownerValid(p) && possessed(p,s.stack)
                && WeaponPerks.selected(s.stack,RampageProfile.ID).isPresent();
    }
    public static void update(ServerPlayer p) {
        if(!ownerValid(p)) {cleanup(p);return;}
        var sessions=SESSIONS.get(p.getUUID());
        if(sessions==null)return;
        sessions.values().removeIf(s->!valid(p,s));
        if(sessions.isEmpty())SESSIONS.remove(p.getUUID());
    }
    private static Session held(ServerPlayer p) {
        var sessions=SESSIONS.get(p.getUUID());
        var s=sessions==null?null:sessions.get(p.getMainHandItem());
        return s!=null && valid(p,s) && WeaponLoadout.canUse(p) && !AbilityService.inSuper(p)?s:null;
    }
    /** Pure HUD reads: returning to the same still-owned stack does not refresh its clock. */
    public static int stacks(ServerPlayer p) {
        var s=held(p);return s==null?0:s.cycle.stacks(now(p),RampageProfile.perk().decayTicks());
    }
    public static int remaining(ServerPlayer p) {
        var s=held(p);return s==null?0:s.cycle.remaining(now(p),RampageProfile.perk().decayTicks());
    }
    public static Token capture(ServerPlayer p) {
        update(p);
        if(!ownerValid(p) || !WeaponLoadout.canUse(p) || AbilityService.inSuper(p)
                || WeaponPerks.selected(p.getMainHandItem(),RampageProfile.ID).isEmpty())return Token.NONE;
        var sessions=SESSIONS.computeIfAbsent(p.getUUID(),ignored->new IdentityHashMap<>());
        var s=sessions.computeIfAbsent(p.getMainHandItem(),ignored->new Session(p));
        return new Token(s,RampageProfile.multiplier(s.cycle.stacks(now(p),RampageProfile.perk().decayTicks())));
    }
    /** Actual paid source-weapon final blows only, including a still-owned projectile's stowed source. */
    public static void killed(ServerPlayer p,Token token) {
        var s=token.session;var sessions=SESSIONS.get(p.getUUID());
        if(s!=null && sessions!=null && sessions.get(s.stack)==s && valid(p,s))
            s.cycle.killed(now(p),RampageProfile.perk().decayTicks());
    }
    public static void changed(ServerPlayer p,ItemStack stack) {
        var sessions=SESSIONS.get(p.getUUID());
        var s=sessions==null?null:sessions.get(stack);
        if(s!=null && s.owner==p) {sessions.remove(stack);if(sessions.isEmpty())SESSIONS.remove(p.getUUID());}
    }
    public static void cleanup(ServerPlayer p) {
        var sessions=SESSIONS.get(p.getUUID());
        if(sessions!=null) {sessions.values().removeIf(s->s.owner==p);if(sessions.isEmpty())SESSIONS.remove(p.getUUID());}
    }
    public static void clear() {SESSIONS.clear();}
}
