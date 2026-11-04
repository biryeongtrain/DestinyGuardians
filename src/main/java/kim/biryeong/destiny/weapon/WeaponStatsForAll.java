package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Real paid damage to distinct enemies, tied to the original equipped source.
 * Stow/reload do not pause or refresh the ten-second window. Queries never grant credit.
 * Main server thread only; target geometry/positive HP loss is checked by WeaponRuntime. */
public final class WeaponStatsForAll {
    private static final Map<UUID, IdentityHashMap<ItemStack,Session>> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner; final ServerLevel level; final ItemStack stack;
        final WeaponCatalog.Entry entry; final WeaponPerks.Roll roll;
        final GuardianData data; final GuardianRuntime runtime; final GuardianClass guardianClass;
        final StatsForAllCycle cycle = new StatsForAllCycle();
        long observed;
        Session(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry, WeaponPerks.Roll roll) {
            owner=p; level=p.level(); this.stack=stack; this.entry=entry; this.roll=roll;
            data=Guardians.data(p); runtime=Guardians.runtimeIfPresent(p).orElse(null);
            guardianClass=data.guardianClass(); observed=now(p);
        }
    }
    public static final class Token {
        public static final Token NONE=new Token(null);
        private final Session source;
        private Token(Session source) { this.source=source; }
    }
    private WeaponStatsForAll() {}
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
        var sessions=SESSIONS.get(p.getUUID());var data=p.getAttachedOrElse(Guardians.DATA,null);
        return sessions!=null&&sessions.get(s.stack)==s&&s.owner==p&&s.level==p.level()
                &&now(p)>=s.observed&&equipped(p,s.stack)&&data==s.data
                &&Guardians.runtimeIfPresent(p).orElse(null)==s.runtime
                &&(data==null?s.guardianClass==null:data.guardianClass()==s.guardianClass)
                &&WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
                &&WeaponPerks.selected(s.stack,StatsForAllProfile.ID).filter(s.roll::equals).isPresent();
    }
    public static void update(ServerPlayer p) {
        if(p==null)return;var sessions=SESSIONS.get(p.getUUID());if(sessions==null)return;
        sessions.values().removeIf(s->!valid(p,s));
        for(var s:sessions.values())s.observed=now(p);
        if(sessions.isEmpty())SESSIONS.remove(p.getUUID());
    }
    private static Session owned(ServerPlayer p,ItemStack stack) {
        if(p==null)return null;var sessions=SESSIONS.get(p.getUUID());
        var s=sessions==null?null:sessions.get(stack);return s!=null&&valid(p,s)?s:null;
    }
    private static Session held(ServerPlayer p) {
        return ownerValid(p)&&WeaponLoadout.canUse(p)?owned(p,p.getMainHandItem()):null;
    }
    public static Token capture(ServerPlayer p) {
        update(p);
        if(!ownerValid(p)||!WeaponLoadout.canUse(p)||!equipped(p,p.getMainHandItem()))return Token.NONE;
        var stack=p.getMainHandItem();var entry=WeaponItems.entry(stack);var roll=WeaponPerks.selected(stack,StatsForAllProfile.ID);
        if(entry.isEmpty()||roll.isEmpty()||!StatsForAllProfile.supports(entry.get()))return Token.NONE;
        var s=SESSIONS.computeIfAbsent(p.getUUID(),ignored->new IdentityHashMap<>())
                .computeIfAbsent(stack,ignored->new Session(p,stack,entry.get(),roll.get()));
        return new Token(s);
    }
    /** Distinct targets, not hits. A paid area projectile may count multiple actual enemies.
     * Dead enemies still count. No positive credit from ability damage or HUD/persistent data. */
    public static void confirmed(ServerPlayer p,Token token,LivingEntity target,float actualLoss) {
        if(token==null||token.source==null||target==null||!Float.isFinite(actualLoss)||actualLoss<=0)return;
        update(p);var s=token.source;
        if(valid(p,s)&&target!=p&&target.level()==s.level)
            s.cycle.confirmed(now(p),target.getUUID());
    }
    public static int ownedRemaining(ServerPlayer p,ItemStack stack) { var s=owned(p,stack);return s==null?0:s.cycle.remaining(now(p)); }
    public static int remaining(ServerPlayer p) { var s=held(p);return s==null?0:s.cycle.remaining(now(p)); }
    public static int progress(ServerPlayer p) { var s=held(p);return s==null?0:s.cycle.progress(now(p)); }
    public static int stabilityBonus(ServerPlayer p) { return remaining(p)>0?10:0; }
    public static int rangeBonus(ServerPlayer p) { return remaining(p)>0?10:0; }
    /** Sum stat bonuses before clamping/one tick rounding; avoid overwriting a coexisting Frenzy. */
    private static int handlingBonus(ServerPlayer p,ItemStack stack) {
        return 35+(WeaponFrenzy.ownedRemaining(p,stack)>0?100:0)
                +(WeaponAdrenalineJunkie.ownedRemaining(p,stack)>0?20:0)
                +10*WeaponPerpetualMotion.ownedStacks(p,stack);
    }
    public static int handlingTicks(ServerPlayer p,ItemStack stack,boolean ready,int base) {
        if(ownedRemaining(p,stack)<=0)return base;
        return StatsForAllProfile.handlingTicks(WeaponItems.entry(stack).orElseThrow(),handlingBonus(p,stack),ready);
    }
    public static int adsTicks(ServerPlayer p,WeaponCatalog.Entry entry,int base,boolean entering) {
        if(remaining(p)<=0||WeaponItems.entry(p.getMainHandItem()).filter(entry::equals).isEmpty())return base;
        return StatsForAllProfile.adsTicks(entry,handlingBonus(p,p.getMainHandItem()),
                entering&&WeaponPerks.selected(p.getMainHandItem(),SnapshotAimProfile.ID).isPresent());
    }
    /** Snapshot the sourced curve and scalar at accepted reload start, never retime a running reload. */
    public static WeaponReloadPolicy.Plan plan(ServerPlayer p,WeaponCatalog.Entry entry,WeaponReloadPolicy.Plan base) {
        if(remaining(p)<=0)return base;
        if(WeaponItems.entry(p.getMainHandItem()).filter(entry::equals).isEmpty())throw new IllegalArgumentException("Foreign reload plan");
        int bonus=35+(WeaponFrenzy.remaining(p)>0?100:0)+10*WeaponPerpetualMotion.stacks(p);
        // Of the current exact four pools only Frenzy can share a reload-speed column.
        // Outlaw, Feeding Frenzy, Rapid Hit and Perpetual Motion cannot coexist here.
        double scalar=.95;
        int ticks=StatsForAllProfile.reloadTicks(entry,bonus,scalar);
        return new WeaponReloadPolicy.Plan(ticks,ticks,base.roundsPerInsert());
    }
    public static WeaponBallistics.Profile ballistics(ServerPlayer p,WeaponCatalog.Entry entry) {
        return remaining(p)>0&&WeaponItems.entry(p.getMainHandItem()).filter(entry::equals).isPresent()
                ?StatsForAllProfile.ballistics(entry):WeaponBallistics.of(entry);
    }
    public static void edited(ItemStack stack) { for(var sessions:SESSIONS.values())sessions.remove(stack); }
    public static void changed(ServerPlayer p,ItemStack stack) { if(p==null)return;var s=SESSIONS.get(p.getUUID());if(s!=null)s.remove(stack); }
    public static void cleanup(ServerPlayer p) { if(p==null)return;var s=SESSIONS.get(p.getUUID());if(s!=null) {s.values().removeIf(v->v.owner==p);if(s.isEmpty())SESSIONS.remove(p.getUUID());} }
    public static void clear() { SESSIONS.clear(); }
}
