package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Accepted grenade/super use and real powered melee contact. Timers survive ordinary stow/super.
 * No generic damage listener, fabricated ability activation, or query-side attachment creation. */
public final class WeaponWellRounded {
    private static final Map<UUID,IdentityHashMap<ItemStack,Session>> SESSIONS=new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;final ServerLevel level;final ItemStack stack;
        final WeaponCatalog.Entry entry;final WeaponPerks.Roll roll;
        final GuardianData data;final GuardianRuntime runtime;final GuardianClass guardianClass;
        final WellRoundedCycle cycle=new WellRoundedCycle();long observed;
        int selectionThreats;long selectionTick=Long.MIN_VALUE;
        Session(ServerPlayer p,WeaponCatalog.Entry e,WeaponPerks.Roll r) {
            owner=p;level=p.level();stack=p.getMainHandItem();entry=e;roll=r;
            data=p.getAttachedOrElse(Guardians.DATA,null);runtime=Guardians.runtimeIfPresent(p).orElseThrow();
            guardianClass=data.guardianClass();observed=now(p);
        }
    }
    public static final class Token {
        public static final Token NONE=new Token(null,null);
        private final Session source;private final Ability ability;
        private final Set<UUID> contacts=new HashSet<>();private boolean consumed;
        private Token(Session source,Ability ability) { this.source=source;this.ability=ability; }
    }
    private WeaponWellRounded() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        if(p==null||!p.isAlive()||p.isRemoved()||p.isSpectator()||p.hasDisconnected())return false;
        var data=p.getAttachedOrElse(Guardians.DATA,null);
        return data!=null&&data.guardianClass()!=null&&data.guardianClass()!=GuardianClass.NONE&&Guardians.runtimeIfPresent(p).isPresent();
    }
    private static boolean owned(ServerPlayer p,ItemStack stack) {
        if(WeaponLoadout.enabled(p)&&WeaponLoadout.equipped(p).stream().noneMatch(e->e.stack()==stack))return false;
        for(int i=0;i<p.getInventory().getContainerSize();i++)if(p.getInventory().getItem(i)==stack)return true;
        return false;
    }
    private static boolean valid(ServerPlayer p,Session s) {
        if(!ownerValid(p))return false;
        var sessions=SESSIONS.get(p.getUUID());
        return sessions!=null&&sessions.get(s.stack)==s&&s.owner==p&&s.level==p.level()&&now(p)>=s.observed
            &&owned(p,s.stack)&&p.getAttachedOrElse(Guardians.DATA,null)==s.data&&s.data.guardianClass()==s.guardianClass
            &&Guardians.runtimeIfPresent(p).orElse(null)==s.runtime&&WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
            &&WeaponPerks.selected(s.stack,WellRoundedProfile.ID).filter(s.roll::equals).isPresent();
    }
    private static boolean held(ServerPlayer p,Session s) {
        int slot=p.getInventory().getSelectedSlot();
        return s.stack==p.getMainHandItem()&&slot>=0&&slot<9&&p.getInventory().getItem(slot)==s.stack
            &&WeaponLoadout.canUse(p)&&s.runtime.superSession==null;
    }
    private static Ability ability(GuardianData data,AbilitySlot slot) {
        if(data==null)return null;
        var id=data.loadout().map(l->l.get(slot)).orElse(null);
        var a=id==null?null:AbilityRegistry.get(id).orElse(null);
        return a!=null&&a.slot()==slot&&a.guardianClass()==data.guardianClass()?a:null;
    }
    public static void update(ServerPlayer p) {
        if(p==null)return;var sessions=SESSIONS.get(p.getUUID());if(sessions==null)return;
        sessions.values().removeIf(s->s.owner==p&&!valid(p,s));
        for(var s:sessions.values())if(s.owner==p)s.observed=now(p);
        if(sessions.isEmpty())SESSIONS.remove(p.getUUID());
    }
    /** Capture before Ability.activate can replace the hand/camera with a super presentation. */
    public static Token accepted(ServerPlayer p,AbilitySlot slot) {
        if(slot!=AbilitySlot.GRENADE&&slot!=AbilitySlot.MELEE&&slot!=AbilitySlot.SUPER)return Token.NONE;
        update(p);if(!ownerValid(p)||!WeaponLoadout.canUse(p)||Guardians.runtimeIfPresent(p).orElseThrow().superSession!=null)return Token.NONE;
        var stack=p.getMainHandItem();var e=WeaponItems.entry(stack).orElse(null);
        var r=WeaponPerks.selected(stack,WellRoundedProfile.ID).orElse(null);
        var a=ability(p.getAttachedOrElse(Guardians.DATA,null),slot);
        int index=p.getInventory().getSelectedSlot();
        if(a==null||r==null||!WellRoundedProfile.supports(e)||!owned(p,stack)||index<0||index>=9||p.getInventory().getItem(index)!=stack)return Token.NONE;
        var s=SESSIONS.computeIfAbsent(p.getUUID(),ignored->new IdentityHashMap<>()).computeIfAbsent(stack,ignored->new Session(p,e,r));
        return new Token(s,a);
    }
    /** Only after successful activate and resource payment. Rejected/cooldown input never reaches here. */
    public static void abilityUsed(ServerPlayer p,Token token,AbilitySlot slot) {
        if(p==null||token==null||token.source==null||token.consumed||slot==AbilitySlot.MELEE)return;
        update(p);var s=token.source;
        if(valid(p,s)&&token.ability==ability(s.data,slot)&&token.ability.slot()==slot) {
            token.consumed=true;s.cycle.used(now(p),slot==AbilitySlot.SUPER?2:1);
        }
    }
    /** Caller already measured positive HP/absorption loss from an eligible direct powered melee. */
    public static void meleeConfirmed(ServerPlayer p,Token token,LivingEntity target) {
        if(p==null||token==null||token.source==null||target==null||token.ability.slot()!=AbilitySlot.MELEE)return;
        update(p);var s=token.source;
        if(valid(p,s)&&target!=p&&target.level()==s.level&&token.ability==ability(s.data,AbilitySlot.MELEE)
            &&token.contacts.size()<64&&token.contacts.add(target.getUUID()))s.cycle.used(now(p),1);
    }
    private static Session active(ServerPlayer p,ItemStack stack) {
        if(p==null)return null;var sessions=SESSIONS.get(p.getUUID());var s=sessions==null?null:sessions.get(stack);
        return s!=null&&valid(p,s)&&s.cycle.stacks(now(p))>0?s:null;
    }
    public static int ownedStacks(ServerPlayer p,ItemStack stack) { var s=active(p,stack);return s==null?0:s.cycle.stacks(now(p)); }
    public static int stacks(ServerPlayer p) { var s=p==null?null:active(p,p.getMainHandItem());return s!=null&&held(p,s)?s.cycle.stacks(now(p)):0; }
    public static int remaining(ServerPlayer p) { var s=p==null?null:active(p,p.getMainHandItem());return s!=null&&held(p,s)?s.cycle.remaining(now(p)):0; }
    public static int rangeBonus(ServerPlayer p) { return 10*stacks(p); }
    public static int stabilityBonus(ServerPlayer p) { return 10*stacks(p); }
    private static boolean co(Session s,String id) { return WeaponPerks.selected(s.stack,id).filter(r->WellRoundedProfile.compatible(s.entry,id,r)).isPresent(); }
    /** Sample the real incoming source at the accepted selection boundary, before ready is paid. */
    public static void selecting(ServerPlayer p,ItemStack stack) {
        var s=active(p,stack);if(s==null)return;
        s.selectionTick=now(p);s.selectionThreats=co(s,ThreatDetectorProfile.ID)?WeaponThreatDetector.selectionSample(p,stack):0;
    }
    private static int threats(ServerPlayer p,Session s) {
        if(!co(s,ThreatDetectorProfile.ID))return 0;
        return held(p,s)?WeaponThreatDetector.stacks(p):s.selectionTick==now(p)?s.selectionThreats:0;
    }
    private static int totalBonus(ServerPlayer p,Session s,int threats) {
        int bonus=10*s.cycle.stacks(now(p));
        if(co(s,FrenzyProfile.ID)&&WeaponFrenzy.ownedRemaining(p,s.stack)>0)bonus+=100;
        if(co(s,AdrenalineJunkieProfile.ID)&&WeaponAdrenalineJunkie.ownedRemaining(p,s.stack)>0)bonus+=20;
        if(held(p,s)&&co(s,PugilistProfile.ID))bonus+=WeaponPugilist.handlingBonus(p);
        if(threats>0)bonus+=ThreatDetectorProfile.handlingBonus(threats);
        return bonus;
    }
    /** Outermost wrapper: total raw Handling before one ceil, preserving legal TD scalar. */
    public static int handlingTicks(ServerPlayer p,ItemStack stack,boolean ready,int base) {
        var s=active(p,stack);if(s==null||s.runtime.superSession!=null)return base;
        int threats=threats(p,s);
        return WellRoundedProfile.handlingTicks(s.entry,totalBonus(p,s,threats),ThreatDetectorProfile.handlingScalar(threats),ready);
    }
    public static int adsTicks(ServerPlayer p,WeaponCatalog.Entry entry,int base,boolean entering) {
        var s=p==null?null:active(p,p.getMainHandItem());if(s==null||!held(p,s)||!s.entry.equals(entry))return base;
        return WellRoundedProfile.adsTicks(entry,totalBonus(p,s,threats(p,s)),entering&&co(s,SnapshotAimProfile.ID));
    }
    public static void edited(ItemStack stack) { for(var s:SESSIONS.values())s.remove(stack); }
    public static void changed(ServerPlayer p,ItemStack stack) { if(p!=null){var s=SESSIONS.get(p.getUUID());if(s!=null)s.remove(stack);} }
    public static void cleanup(ServerPlayer p) { if(p!=null){var s=SESSIONS.get(p.getUUID());if(s!=null){s.values().removeIf(v->v.owner==p);if(s.isEmpty())SESSIONS.remove(p.getUUID());}} }
    public static void clear() { SESSIONS.clear(); }
}
