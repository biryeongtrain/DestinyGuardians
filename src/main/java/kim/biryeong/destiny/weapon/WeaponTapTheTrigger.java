package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Main-thread held-original state. Read-only queries cannot arm, spend ammo or start windows. */
public final class WeaponTapTheTrigger {
    private static final Map<UUID,Session> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final WeaponCatalog.Entry entry;
        final TapTheTriggerCycle cycle = new TapTheTriggerCycle();
        Session(ServerPlayer p, WeaponCatalog.Entry entry) {
            owner=p;level=p.level();stack=p.getMainHandItem();this.entry=entry;
        }
    }
    private WeaponTapTheTrigger() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean eligible(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && WeaponLoadout.canUse(p) && !AbilityService.inSuper(p);
    }
    private static boolean valid(ServerPlayer p,Session s) {
        return s!=null && s.owner==p && s.level==p.level() && s.stack==p.getMainHandItem()
                && eligible(p) && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
                && WeaponPerks.selected(s.stack,TapTheTriggerProfile.ID).isPresent();
    }
    public static void update(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());
        if(s!=null && s.owner==p && !valid(p,s))SESSIONS.remove(p.getUUID());
    }
    /** Called only after WeaponCycle.fire succeeds and the cartridge has actually been saved. */
    public static void paidEmission(ServerPlayer p,WeaponCatalog.Entry entry) {
        update(p);
        if(!eligible(p) || WeaponItems.entry(p.getMainHandItem()).filter(entry::equals).isEmpty()
                || WeaponPerks.selected(p.getMainHandItem(),TapTheTriggerProfile.ID).isEmpty())return;
        var s=SESSIONS.get(p.getUUID());
        if(!valid(p,s)){s=new Session(p,entry);SESSIONS.put(p.getUUID(),s);}
        s.cycle.paid(now(p),entry.family().equals("fusion_rifle"));
    }
    public static void released(ServerPlayer p,ItemStack stack) {
        var s=SESSIONS.get(p.getUUID());
        if(s!=null && s.owner==p && s.stack==stack)s.cycle.released();
    }
    private static Session active(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());return valid(p,s) && s.cycle.remaining(now(p))>0?s:null;
    }
    public static int remaining(ServerPlayer p) {
        var s=active(p);return s==null?0:s.cycle.remaining(now(p));
    }
    public static int stabilityBonus(ServerPlayer p) {
        var s=active(p);return s==null?0:TapTheTriggerProfile.stabilityBonus(s.entry);
    }
    public static float recoilScalar(ServerPlayer p) {
        var s=active(p);return s==null?1:TapTheTriggerProfile.recoilScalar(s.entry);
    }
    public static float accuracyScalar(ServerPlayer p) {
        var s=active(p);return s==null?1:TapTheTriggerProfile.accuracyScalar(s.entry);
    }
    public static void edited(ItemStack stack) { SESSIONS.values().removeIf(s->s.stack==stack); }
    public static void changed(ServerPlayer p,ItemStack stack) {
        var s=SESSIONS.get(p.getUUID());if(s!=null && s.owner==p && s.stack==stack)SESSIONS.remove(p.getUUID());
    }
    public static void cleanup(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());if(s!=null && s.owner==p)SESSIONS.remove(p.getUUID());
    }
    public static void clear() { SESSIONS.clear(); }
}
