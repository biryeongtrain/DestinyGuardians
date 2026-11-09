package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Main-thread real combat events shared by actual equipped originals, including stowed weapons.
 * The source of damage can be a weapon, vanilla attack or ability; only paid weapon emissions
 * receive the captured damage multiplier. Backpack copies and persisted HUD selectors are inert. */
public final class WeaponFrenzy {
    private static final Map<UUID,Session> SESSIONS=new HashMap<>();
    private static final class Session {
        final ServerPlayer owner; final ServerLevel level;
        final IdentityHashMap<ItemStack,FrenzyCycle> weapons=new IdentityHashMap<>();
        Session(ServerPlayer p) { owner=p;level=p.level(); }
    }
    public record Token(float multiplier) { public static final Token NONE=new Token(1f); }
    private WeaponFrenzy() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        return p!=null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected();
    }
    private static boolean possessed(ServerPlayer p,ItemStack stack) {
        if (WeaponLoadout.enabled(p)) return WeaponLoadout.equipped(p).stream().anyMatch(e->e.stack()==stack);
        for(int i=0;i<9;i++) if(p.getInventory().getItem(i)==stack)return true;
        return false;
    }
    private static boolean selected(ItemStack stack) { return WeaponPerks.selected(stack,FrenzyProfile.ID).isPresent(); }
    public static void update(ServerPlayer p) {
        if(!ownerValid(p)){if(p!=null)cleanup(p);return;}
        var s=SESSIONS.get(p.getUUID());
        if(s==null || s.owner!=p || s.level!=p.level()){s=new Session(p);SESSIONS.put(p.getUUID(),s);}
        s.weapons.keySet().removeIf(stack->!possessed(p,stack)||!selected(stack));
        for(int i=0;i<p.getInventory().getContainerSize();i++) {
            var stack=p.getInventory().getItem(i);
            if(possessed(p,stack)&&selected(stack))s.weapons.computeIfAbsent(stack,ignored->
                    new FrenzyCycle(FrenzyProfile.activationTicks(),FrenzyProfile.combatGraceTicks(),FrenzyProfile.durationTicks()));
        }
        for(var cycle:s.weapons.values())cycle.update(now(p));
        if(s.weapons.isEmpty())SESSIONS.remove(p.getUUID(),s);
    }
    /** AFTER post-mitigation real damage to a non-player combat enemy. Dead victims still count.
     * This matches the project's PvE enemy set but never rechecks isAlive after a lethal hit. */
    public static void dealt(ServerPlayer p,LivingEntity target,DamageSource source,float loss) {
        if(!Float.isFinite(loss)||loss<=0||!ownerValid(p)||target==p||target.level()!=p.level()
                ||source.getEntity()!=p||!(target instanceof net.minecraft.world.entity.Mob))return;
        event(p);
    }
    /** Actual HP+absorption loss; source-less/environment/self hits do not prime or refresh. */
    public static void received(ServerPlayer p,DamageSource source,float loss) {
        if(!Float.isFinite(loss)||loss<=0||!ownerValid(p)||!(source.getEntity() instanceof LivingEntity attacker)
                ||attacker==p||attacker.level()!=p.level())return;
        event(p);
    }
    private static void event(ServerPlayer p) {
        update(p);var s=SESSIONS.get(p.getUUID());
        if(s!=null&&s.owner==p)for(var cycle:s.weapons.values())cycle.damage(now(p));
    }
    private static FrenzyCycle owned(ServerPlayer p,ItemStack stack) {
        var s=SESSIONS.get(p.getUUID());
        return s!=null&&s.owner==p&&s.level==p.level()&&ownerValid(p)&&possessed(p,stack)&&selected(stack)
                ?s.weapons.get(stack):null;
    }
    public static int ownedRemaining(ServerPlayer p,ItemStack stack) {
        var c=owned(p,stack);return c==null?0:c.remaining(now(p));
    }
    public static int remaining(ServerPlayer p) {
        return WeaponLoadout.canUse(p)&&!AbilityService.inSuper(p)?ownedRemaining(p,p.getMainHandItem()):0;
    }
    public static int combatTicks(ServerPlayer p) {
        var c=owned(p,p.getMainHandItem());return c==null?0:c.combatTicks(now(p));
    }
    /** Immutable firing-time snapshot; delayed projectiles cannot borrow the next gun's buff. */
    public static Token capture(ServerPlayer p) { return remaining(p)>0?new Token(FrenzyProfile.multiplier()):Token.NONE; }
    public static int handlingTicks(ServerPlayer p,ItemStack stack,boolean ready,int base) {
        if(ownedRemaining(p,stack)<=0)return base;
        var timing=FrenzyProfile.timing(WeaponItems.entry(stack).orElseThrow());
        return ready?timing.readyTicks():timing.stowTicks();
    }
    public static int adsTicks(ServerPlayer p,WeaponCatalog.Entry entry,int base,boolean entering) {
        if(remaining(p)<=0)return base;
        return FrenzyProfile.adsTicks(entry,entering && WeaponPerks.selected(p.getMainHandItem(),SnapshotAimProfile.ID).isPresent());
    }
    public static WeaponReloadPolicy.Plan plan(ServerPlayer p,WeaponCatalog.Entry entry,WeaponReloadPolicy.Plan base) {
        if(remaining(p)<=0)return base;
        if(WeaponItems.entry(p.getMainHandItem()).filter(entry::equals).isEmpty())throw new IllegalArgumentException("Foreign reload plan");
        double scalar=WeaponOutlaw.remaining(p)>0?OutlawProfile.perk().durationMultiplier():1;
        int feeding=WeaponFeedingFrenzy.stacks(p),rapid=WeaponRapidHit.stacks(p);
        if(feeding>0)scalar*=FeedingFrenzyProfile.durationMultiplier(feeding);
        if(rapid>0)scalar*=RapidHitProfile.durationMultiplier(rapid);
        if (LegendaryWeapons.contains(entry.id())) {
            var own = WeaponProfile.forEntry(entry);
            return new WeaponReloadPolicy.Plan(
                WeaponStatCurves.reloadTicks(entry.id(), own.firstReloadTicks(), FrenzyProfile.reloadBonus(), scalar),
                WeaponStatCurves.reloadTicks(entry.id(), own.reloadTicks(), FrenzyProfile.reloadBonus(), scalar), base.roundsPerInsert());
        }
        int ticks=FrenzyProfile.reloadTicks(entry,scalar);
        return new WeaponReloadPolicy.Plan(ticks,ticks,base.roundsPerInsert());
    }
    public static void edited(ItemStack stack) {for(var s:SESSIONS.values())s.weapons.remove(stack);}
    public static void changed(ServerPlayer p,ItemStack stack) {
        var s=SESSIONS.get(p.getUUID());if(s!=null&&s.owner==p)s.weapons.remove(stack);
    }
    public static void cleanup(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());if(s!=null&&s.owner==p)SESSIONS.remove(p.getUUID(),s);
    }
    public static void clear() {SESSIONS.clear();}
}
