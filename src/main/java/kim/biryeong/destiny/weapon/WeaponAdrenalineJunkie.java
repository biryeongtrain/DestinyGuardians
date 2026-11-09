package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Actual original equipped sources, not persisted stacks or generic ability-kill credit.
 * Stow preserves the running window; grenade acceptance captures all equipped originals.
 * Backpack items, future replacements and later edits cannot borrow a released grenade. */
public final class WeaponAdrenalineJunkie {
    private static final Map<UUID, IdentityHashMap<ItemStack,Session>> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner; final ServerLevel level; final ItemStack stack;
        final WeaponCatalog.Entry entry; final WeaponPerks.Roll roll;
        final GuardianData data; final GuardianRuntime runtime; final GuardianClass guardianClass;
        final AdrenalineJunkieCycle cycle = new AdrenalineJunkieCycle();
        long observed;
        Session(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry, WeaponPerks.Roll roll) {
            owner=p;level=p.level();this.stack=stack;this.entry=entry;this.roll=roll;
            data=Guardians.data(p);runtime=Guardians.runtimeIfPresent(p).orElse(null);
            guardianClass=data.guardianClass();observed=now(p);
        }
    }
    public static final class Token {
        public static final Token NONE = new Token(null,1f);
        private final Session source; private final float multiplier;
        private final Set<UUID> corpses=new HashSet<>();
        private Token(Session source,float multiplier){this.source=source;this.multiplier=multiplier;}
        /** A paid emission keeps its firing-time damage; source revocation only denies new credit. */
        public float multiplier(){return multiplier;}
    }
    public static final class GrenadeToken {
        public static final GrenadeToken NONE = new GrenadeToken(null,List.of());
        private final ServerPlayer owner; private final List<Session> originals;
        private final PerkExpansionCombat.AbilityToken desperate;
        private final Identifier grenade; private final Set<UUID> corpses=new HashSet<>();
        private GrenadeToken(ServerPlayer owner,List<Session> originals){
            this.owner=owner;this.originals=List.copyOf(originals);
            desperate=owner==null?PerkExpansionCombat.AbilityToken.NONE:PerkExpansionCombat.acceptedAbility(owner,AbilitySlot.GRENADE);
            grenade=owner==null?null:equippedGrenade(Guardians.data(owner));
        }
    }
    private WeaponAdrenalineJunkie(){}
    private static long now(ServerPlayer p){return p.level().getServer().getTickCount();}
    private static boolean ownerValid(ServerPlayer p){return p!=null&&p.isAlive()&&!p.isRemoved()
            &&!p.isSpectator()&&!p.hasDisconnected()&&!AbilityService.inSuper(p);}
    private static boolean equipped(ServerPlayer p,ItemStack stack){
        if(WeaponLoadout.enabled(p))return WeaponLoadout.equipped(p).stream().anyMatch(e->e.stack()==stack);
        for(int i=0;i<9;i++)if(p.getInventory().getItem(i)==stack)return true;
        return false;
    }
    private static boolean valid(ServerPlayer p,Session s){
        if(!ownerValid(p))return false;
        var sessions=SESSIONS.get(p.getUUID());
        return sessions!=null&&sessions.get(s.stack)==s&&s.owner==p&&s.level==p.level()
                &&now(p)>=s.observed&&equipped(p,s.stack)
                &&p.getAttachedOrElse(Guardians.DATA,null)==s.data
                &&Guardians.runtimeIfPresent(p).orElse(null)==s.runtime&&s.data.guardianClass()==s.guardianClass
                &&WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
                &&WeaponPerks.selected(s.stack,AdrenalineJunkieProfile.ID).filter(s.roll::equals).isPresent();
    }
    /** Updates existing epochs only; HUD reads never create an armed source. */
    public static void update(ServerPlayer p){
        if(p==null)return;var sessions=SESSIONS.get(p.getUUID());if(sessions==null)return;
        sessions.values().removeIf(s->!valid(p,s));
        for(var s:sessions.values()){s.cycle.update(now(p));s.observed=now(p);}
        if(sessions.isEmpty())SESSIONS.remove(p.getUUID());
    }
    private static Session bind(ServerPlayer p,ItemStack stack){
        if(!ownerValid(p)||now(p)<0||!equipped(p,stack))return null;
        var entry=WeaponItems.entry(stack);var roll=WeaponPerks.selected(stack,AdrenalineJunkieProfile.ID);
        if(entry.isEmpty()||roll.isEmpty()||!AdrenalineJunkieProfile.supports(entry.get())
                ||!AdrenalineJunkieProfile.rolls().contains(roll.get()))return null;
        var sessions=SESSIONS.computeIfAbsent(p.getUUID(),ignored->new IdentityHashMap<>());
        return sessions.computeIfAbsent(stack,ignored->new Session(p,stack,entry.get(),roll.get()));
    }
    private static Session owned(ServerPlayer p,ItemStack stack){
        if(p==null)return null;var sessions=SESSIONS.get(p.getUUID());
        var s=sessions==null?null:sessions.get(stack);return s!=null&&valid(p,s)?s:null;
    }
    public static int ownedStacks(ServerPlayer p,ItemStack stack){var s=owned(p,stack);return s==null?0:s.cycle.stacks(now(p));}
    public static int ownedRemaining(ServerPlayer p,ItemStack stack){var s=owned(p,stack);return s==null?0:s.cycle.remaining(now(p));}
    public static int stacks(ServerPlayer p){return ownerValid(p)&&WeaponLoadout.canUse(p)?ownedStacks(p,p.getMainHandItem()):0;}
    public static int remaining(ServerPlayer p){return ownerValid(p)&&WeaponLoadout.canUse(p)?ownedRemaining(p,p.getMainHandItem()):0;}
    public static Token capture(ServerPlayer p){
        update(p);if(!ownerValid(p)||!WeaponLoadout.canUse(p))return Token.NONE;
        var s=bind(p,p.getMainHandItem());return s==null?Token.NONE:new Token(s,s.cycle.multiplier(now(p)));
    }
    /** Called only after a live eligible enemy took positive actual paid-weapon damage and died. */
    public static void killed(ServerPlayer p,Token token,LivingEntity corpse){
        if(token==null||token.source==null||corpse==null||corpse.isAlive()&&!corpse.isDeadOrDying())return;
        update(p);var s=token.source;
        if(corpse!=p&&corpse.level()==s.level&&valid(p,s)&&token.corpses.add(corpse.getUUID()))s.cycle.killed(now(p));
    }
    private static Identifier equippedGrenade(GuardianData data){return data.loadout().map(l->l.get(AbilitySlot.GRENADE)).orElse(null);}
    /** Accepted class-owned grenade, before windup/release; captures stowed loadout originals too. */
    public static GrenadeToken grenadeAccepted(ServerPlayer p){
        update(p);
        if(!ownerValid(p)||kim.biryeong.destiny.ability.AbilityService.equipped(p,AbilitySlot.GRENADE).isEmpty()
                ||Guardians.runtimeIfPresent(p).isEmpty()||equippedGrenade(Guardians.data(p))==null)return GrenadeToken.NONE;
        var originals=new ArrayList<Session>();
        for(int i=0;i<p.getInventory().getContainerSize();i++){
            var s=bind(p,p.getInventory().getItem(i));if(s!=null&&!originals.contains(s))originals.add(s);
        }
        return new GrenadeToken(p,originals);
    }
    /** Dedicated grenade damage boundary; melee/super/Dragonfly/generic Combat.damage cannot proc. */
    public static boolean grenadeDamage(ServerPlayer p,GrenadeToken token,ServerLevel level,LivingEntity target,float amount,Element element){
        boolean eligible=target.level()==level&&Combat.isEnemy(p,target);
        float before=target.getHealth()+target.getAbsorptionAmount();
        boolean killed=Combat.damage(level,p,target,amount,element);
        float loss=before-target.getHealth()-target.getAbsorptionAmount();
        if(eligible&&killed&&Float.isFinite(loss)&&loss>0)grenadeKilled(p,token,target);
        return killed;
    }
    /** Also called at actual fire death for attributed grenade scorch; distinct corpses, once each. */
    public static void grenadeKilled(ServerPlayer p,GrenadeToken token,LivingEntity corpse){
        if(token!=null && token.owner==p) PerkExpansionCombat.abilityKilled(p,token.desperate,corpse);
        if(token==null||token.owner!=p||!ownerValid(p)||corpse==null||corpse==p||corpse.isAlive()&&!corpse.isDeadOrDying()
                ||!(corpse instanceof net.minecraft.world.entity.Mob)||corpse.level()!=p.level())return;
        update(p);
        if(token.grenade==null||!token.grenade.equals(equippedGrenade(Guardians.data(p)))
                ||!token.corpses.add(corpse.getUUID()))return;
        for(var s:token.originals)if(valid(p,s)&&s.runtime!=null&&s.guardianClass!=GuardianClass.NONE)s.cycle.grenadeKilled(now(p));
    }
    public static int handlingTicks(ServerPlayer p,ItemStack stack,boolean ready,int base){
        if(ownedRemaining(p,stack)<=0)return base;
        var timing=AdrenalineJunkieProfile.timing(WeaponItems.entry(stack).orElseThrow());
        if(!timing.supported())return base;
        return ready?timing.readyTicks():timing.stowTicks();
    }
    public static int adsTicks(ServerPlayer p,WeaponCatalog.Entry entry,int base,boolean entering){
        if(remaining(p)<=0||WeaponItems.entry(p.getMainHandItem()).filter(entry::equals).isEmpty()
                ||!AdrenalineJunkieProfile.timing(entry).supported())return base;
        return AdrenalineJunkieProfile.adsTicks(entry,entering&&WeaponPerks.selected(p.getMainHandItem(),SnapshotAimProfile.ID).isPresent());
    }
    public static void edited(ItemStack stack){for(var sessions:SESSIONS.values())sessions.remove(stack);}
    public static void changed(ServerPlayer p,ItemStack stack){if(p==null)return;var s=SESSIONS.get(p.getUUID());if(s!=null)s.remove(stack);}
    public static void cleanup(ServerPlayer p){if(p==null)return;var s=SESSIONS.get(p.getUUID());if(s!=null){s.values().removeIf(v->v.owner==p);if(s.isEmpty())SESSIONS.remove(p.getUUID());}}
    public static void clear(){SESSIONS.clear();}
}
