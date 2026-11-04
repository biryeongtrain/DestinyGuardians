package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Paid weapon final blows, original equipped source only. No generic ability-kill subscription.
 * Source-proven stow survival; reload clock survival and identity lifecycle are explicit local policy.
 * Pure HUD/stat queries never arm a session. Main server thread only. */
public final class WeaponHeatingUp {
    private static final Map<UUID, IdentityHashMap<ItemStack,Session>> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner; final ServerLevel level; final ItemStack stack;
        final WeaponCatalog.Entry entry; final WeaponPerks.Roll roll;
        final GuardianData data; final GuardianRuntime runtime; final GuardianClass guardianClass;
        final HeatingUpCycle cycle = new HeatingUpCycle();
        final Set<LivingEntity> corpses=Collections.newSetFromMap(new WeakHashMap<>());
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
    private WeaponHeatingUp() {}
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
                &&WeaponPerks.selected(s.stack,HeatingUpProfile.ID).filter(s.roll::equals).isPresent();
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
        var stack=p.getMainHandItem();var entry=WeaponItems.entry(stack);var roll=WeaponPerks.selected(stack,HeatingUpProfile.ID);
        if(entry.isEmpty()||roll.isEmpty()||!HeatingUpProfile.supports(entry.get()))return Token.NONE;
        var s=SESSIONS.computeIfAbsent(p.getUUID(),ignored->new IdentityHashMap<>())
                .computeIfAbsent(stack,ignored->new Session(p,stack,entry.get(),roll.get()));
        return new Token(s);
    }
    /** Only real paid-weapon positive damage followed by a final blow qualifies.
     * Corpse identity deduplicates across this source's multiple pellets/projectiles/callbacks. */
    public static void killed(ServerPlayer p,Token token,LivingEntity corpse) {
        if(token==null||token.source==null||corpse==null||corpse.isAlive()&&!corpse.isDeadOrDying())return;
        update(p); var s=token.source;
        if(valid(p,s)&&corpse!=p&&corpse.level()==s.level&&s.corpses.add(corpse))s.cycle.killed(now(p));
    }
    public static int ownedRemaining(ServerPlayer p,ItemStack stack) { var s=owned(p,stack);return s==null?0:s.cycle.remaining(now(p)); }
    public static int remaining(ServerPlayer p) { var s=held(p);return s==null?0:s.cycle.remaining(now(p)); }
    public static int ownedStacks(ServerPlayer p, ItemStack stack) { var s=owned(p,stack); return s==null?0:s.cycle.stacks(now(p)); }
    public static int stacks(ServerPlayer p) { var s=held(p); return s==null?0:s.cycle.stacks(now(p)); }
    public static int stabilityBonus(ServerPlayer p) { return HeatingUpProfile.stabilityBonus(stacks(p)); }
    public static int recoilDirectionBonus(ServerPlayer p) { return HeatingUpProfile.recoilDirectionBonus(stacks(p)); }
    public static float accuracyScalar(ServerPlayer p) { return (float)HeatingUpProfile.accuracyScalar(stacks(p)); }
    public static void edited(ItemStack stack) { for(var sessions:SESSIONS.values())sessions.remove(stack); }
    public static void changed(ServerPlayer p,ItemStack stack) { if(p==null)return;var s=SESSIONS.get(p.getUUID());if(s!=null)s.remove(stack); }
    public static void cleanup(ServerPlayer p) { if(p==null)return;var s=SESSIONS.get(p.getUUID());if(s!=null) {s.values().removeIf(v->v.owner==p);if(s.isEmpty())SESSIONS.remove(p.getUUID());} }
    public static void clear() { SESSIONS.clear(); }
}
