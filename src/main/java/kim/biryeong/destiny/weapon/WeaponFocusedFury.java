package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Original equipped sources only. Stow/reload reset progress, not an earned buff.
 * Immutable paid damage survives source retirement; new credit cannot cross a counter epoch. */
public final class WeaponFocusedFury {
    private static final Map<UUID, IdentityHashMap<ItemStack,Session>> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner; final ServerLevel level; final ItemStack stack;
        final WeaponCatalog.Entry entry; final WeaponPerks.Roll roll;
        final GuardianData data; final GuardianRuntime runtime; final GuardianClass guardianClass;
        final FocusedFuryCycle cycle;
        long observed, epoch; boolean held;
        Session(ServerPlayer p,ItemStack stack,WeaponCatalog.Entry entry,WeaponPerks.Roll roll) {
            owner=p;level=p.level();this.stack=stack;this.entry=entry;this.roll=roll;
            data=Guardians.data(p);runtime=Guardians.runtimeIfPresent(p).orElse(null);
            guardianClass=data.guardianClass();
            cycle=new FocusedFuryCycle(FocusedFuryProfile.threshold(entry));observed=now(p);held=true;
        }
    }
    public static final class Token {
        public static final Token NONE=new Token(null,1f);
        private final Session source; private final float multiplier; private final long epoch;
        private boolean credited;
        private Token(Session source,float multiplier) { this.source=source;this.multiplier=multiplier;epoch=source==null?-1:source.epoch; }
        public float multiplier() { return multiplier; }
    }
    private WeaponFocusedFury() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) { return p!=null&&p.isAlive()&&!p.isRemoved()
            &&!p.isSpectator()&&!p.hasDisconnected()&&!AbilityService.inSuper(p); }
    private static boolean equipped(ServerPlayer p,ItemStack stack) {
        if(WeaponLoadout.enabled(p))return WeaponLoadout.equipped(p).stream().anyMatch(e->e.stack()==stack);
        for(int i=0;i<9;i++)if(p.getInventory().getItem(i)==stack)return true;
        return false;
    }
    private static boolean valid(ServerPlayer p,Session s) {
        if(!ownerValid(p))return false;
        var sessions=SESSIONS.get(p.getUUID());
        var data=p.getAttachedOrElse(Guardians.DATA,null);
        return sessions!=null&&sessions.get(s.stack)==s&&s.owner==p&&s.level==p.level()
                &&now(p)>=s.observed&&equipped(p,s.stack)&&data==s.data
                &&Guardians.runtimeIfPresent(p).orElse(null)==s.runtime
                &&(data==null?s.guardianClass==null:data.guardianClass()==s.guardianClass)
                &&WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
                &&WeaponPerks.selected(s.stack,FocusedFuryProfile.ID).filter(s.roll::equals).isPresent();
    }
    public static void update(ServerPlayer p) {
        if(p==null)return;var sessions=SESSIONS.get(p.getUUID());if(sessions==null)return;
        sessions.values().removeIf(s->!valid(p,s));
        for(var s:sessions.values()) {
            boolean held=p.getMainHandItem()==s.stack;
            if(s.held&&!held)reset(s,now(p));
            s.held=held;s.cycle.update(now(p));s.observed=now(p);
        }
        if(sessions.isEmpty())SESSIONS.remove(p.getUUID());
    }
    private static Session owned(ServerPlayer p,ItemStack stack) {
        if(p==null)return null;var sessions=SESSIONS.get(p.getUUID());
        var s=sessions==null?null:sessions.get(stack);return s!=null&&valid(p,s)?s:null;
    }
    private static Session bind(ServerPlayer p) {
        if(!ownerValid(p)||!WeaponLoadout.canUse(p)||!equipped(p,p.getMainHandItem()))return null;
        var stack=p.getMainHandItem();var entry=WeaponItems.entry(stack);var roll=WeaponPerks.selected(stack,FocusedFuryProfile.ID);
        if(entry.isEmpty()||roll.isEmpty()||!FocusedFuryProfile.supports(entry.get()))return null;
        return SESSIONS.computeIfAbsent(p.getUUID(),ignored->new IdentityHashMap<>())
                .computeIfAbsent(stack,ignored->new Session(p,stack,entry.get(),roll.get()));
    }
    public static Token capture(ServerPlayer p) {
        update(p);var s=bind(p);
        return s==null?Token.NONE:new Token(s,s.cycle.remaining(now(p))>0?FocusedFuryProfile.multiplier():1f);
    }
    /** Production damage calls only after actual positive loss; abilities/splash do not call this. */
    public static void confirmed(ServerPlayer p,Token token,boolean precision,float actualLoss) {
        if(token==null||!precision||!Float.isFinite(actualLoss)||actualLoss<=0||token.source==null||token.credited)return;
        token.credited=true;update(p);var s=token.source;
        if(valid(p,s)&&s.stack==p.getMainHandItem()&&s.epoch==token.epoch&&!WeaponRuntime.reloading(p))
            s.cycle.precision(now(p));
    }
    private static void reset(Session s,long tick) { s.cycle.resetCounter(tick);s.epoch++; }
    public static void stowing(ServerPlayer p,ItemStack stack) {
        var s=owned(p,stack);if(s!=null) {reset(s,now(p));s.held=false;}
    }
    /** Accepted timed reload or real instant reload, never a denied reload request. */
    public static void reloadStarted(ServerPlayer p,ItemStack stack) {
        var s=owned(p,stack);if(s!=null)reset(s,now(p));
    }
    public static int ownedRemaining(ServerPlayer p,ItemStack stack) { var s=owned(p,stack);return s==null?0:s.cycle.remaining(now(p)); }
    public static int remaining(ServerPlayer p) { return ownerValid(p)&&WeaponLoadout.canUse(p)?ownedRemaining(p,p.getMainHandItem()):0; }
    public static int progress(ServerPlayer p) { var s=ownerValid(p)&&WeaponLoadout.canUse(p)?owned(p,p.getMainHandItem()):null;return s==null?0:s.cycle.progress(now(p)); }
    public static void edited(ItemStack stack) { for(var sessions:SESSIONS.values())sessions.remove(stack); }
    public static void changed(ServerPlayer p,ItemStack stack) { if(p==null)return;var s=SESSIONS.get(p.getUUID());if(s!=null)s.remove(stack); }
    public static void cleanup(ServerPlayer p) { if(p==null)return;var s=SESSIONS.get(p.getUUID());if(s!=null) {s.values().removeIf(v->v.owner==p);if(s.isEmpty())SESSIONS.remove(p.getUUID());} }
    public static void clear() { SESSIONS.clear(); }
}
