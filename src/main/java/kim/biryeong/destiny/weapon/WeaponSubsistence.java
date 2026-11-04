package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.AmmoHud;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Paid weapon final blows transfer reserve rounds to the ORIGINAL source, never reload perks.
 * An owned/equipped projectile source survives ordinary stow locally; edits, source loss and
 * Guardian/world lifecycle changes revoke it. No generic ability-kill subscription.
 */
public final class WeaponSubsistence {
    private static final Map<UUID, IdentityHashMap<ItemStack, Source>> SOURCES = new HashMap<>();
    private static final class Source {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final WeaponCatalog.Entry entry;
        final WeaponPerks.Roll roll;
        final GuardianData data;
        final GuardianRuntime runtime;
        final GuardianClass guardianClass;
        final Set<LivingEntity> corpses = Collections.newSetFromMap(new WeakHashMap<>());
        long observed;
        Source(ServerPlayer p, WeaponCatalog.Entry e, WeaponPerks.Roll r) {
            owner=p; level=p.level(); stack=p.getMainHandItem(); entry=e; roll=r;
            data=Guardians.data(p); runtime=Guardians.runtimeIfPresent(p).orElse(null); guardianClass=data.guardianClass();
            observed=now(p);
        }
    }
    public static final class Token {
        public static final Token NONE = new Token(null);
        private final Source source;
        private Token(Source source) { this.source=source; }
    }
    private WeaponSubsistence() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        return p!=null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && !AbilityService.inSuper(p);
    }
    private static boolean possesses(ServerPlayer p, ItemStack stack) {
        for(int i=0;i<p.getInventory().getContainerSize();i++)
            if(p.getInventory().getItem(i)==stack)return true;
        return false;
    }
    private static boolean valid(ServerPlayer p, Source s) {
        return ownerValid(p) && s.owner==p && s.level==p.level() && now(p)>=s.observed
                && s.data==p.getAttachedOrElse(Guardians.DATA,null) && s.runtime==Guardians.runtimeIfPresent(p).orElse(null)
                && s.guardianClass==s.data.guardianClass() && possesses(p,s.stack)
                && (!WeaponLoadout.enabled(p) || WeaponLoadout.equipped(p).stream().anyMatch(e->e.stack()==s.stack))
                && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
                && SubsistenceProfile.supports(s.entry)
                && WeaponPerks.selected(s.stack,SubsistenceProfile.ID).filter(s.roll::equals).isPresent();
    }
    public static void update(ServerPlayer p) {
        if(p==null)return;
        var sources=SOURCES.get(p.getUUID());
        if(sources==null)return;
        sources.values().removeIf(s->s.owner==p&&!valid(p,s));
        for(var s:sources.values())if(s.owner==p)s.observed=now(p);
        if(sources.isEmpty())SOURCES.remove(p.getUUID());
    }
    /** Caller captures only after paying the emission's cartridge. Reads/denied attacks never bind. */
    public static Token capture(ServerPlayer p) {
        update(p);
        if(!ownerValid(p)||!WeaponLoadout.canUse(p))return Token.NONE;
        var stack=p.getMainHandItem();
        var e=WeaponItems.entry(stack).filter(SubsistenceProfile::supports);
        var r=WeaponPerks.selected(stack,SubsistenceProfile.ID);
        if(e.isEmpty()||r.isEmpty()||!SubsistenceProfile.rolls().contains(r.get())
                ||!e.get().id().equals(r.get().id())||!possesses(p,stack))return Token.NONE;
        var sources=SOURCES.computeIfAbsent(p.getUUID(),ignored->new IdentityHashMap<>());
        var source=sources.computeIfAbsent(stack,ignored->new Source(p,e.get(),r.get()));
        return valid(p,source)?new Token(source):Token.NONE;
    }
    /** Only after positive actual damage AND a confirmed final blow against a prevalidated enemy.
     * Corpse identity is shared across this source's projectiles, not one reward per pellet/callback.
     * No reload cycle, cadence cancellation, reload sound or Kill Clip/MKC/Ace activation is invoked.
     */
    public static int killed(ServerPlayer p, Token token, LivingEntity corpse) {
        if(p==null||token==null||token.source==null||corpse==null)return 0;
        update(p);
        var s=token.source;
        var sources=SOURCES.get(p.getUUID());
        if(sources==null||sources.get(s.stack)!=s||!valid(p,s)||corpse==p
                ||corpse.level()!=s.level||corpse.isAlive()||!s.corpses.add(corpse))return 0;
        var profile=WeaponProfile.forEntry(s.entry);
        var ammo=WeaponItems.magazine(s.stack,profile);
        int moved=ammo.reloadRounds(SubsistenceProfile.refillRounds(s.entry,profile.magazine()));
        if(moved>0) {
            WeaponItems.save(s.stack,ammo);
            p.getInventory().setChanged();p.containerMenu.broadcastChanges();AmmoHud.update(p);
        }
        return moved;
    }
    public static void edited(ItemStack stack) {
        if(stack==null)return;
        var it=SOURCES.values().iterator();
        while(it.hasNext()) {var sources=it.next();sources.remove(stack);if(sources.isEmpty())it.remove();}
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        if(p==null)return;
        var sources=SOURCES.get(p.getUUID());
        if(sources!=null) {var s=sources.get(stack);if(s!=null&&s.owner==p)sources.remove(stack);
            if(sources.isEmpty())SOURCES.remove(p.getUUID());}
    }
    public static void cleanup(ServerPlayer p) {
        if(p==null)return;
        var sources=SOURCES.get(p.getUUID());
        if(sources!=null) {sources.values().removeIf(s->s.owner==p);if(sources.isEmpty())SOURCES.remove(p.getUUID());}
    }
    public static void clear() { SOURCES.clear(); }
}
