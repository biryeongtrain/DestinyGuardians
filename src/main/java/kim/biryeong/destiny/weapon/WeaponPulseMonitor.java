package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Original equipped objects, main-thread episode writers, pure benefit readers. No reload events. */
public final class WeaponPulseMonitor {
    private static final Map<UUID, IdentityHashMap<ItemStack, Session>> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final WeaponCatalog.Entry entry;
        final WeaponPerks.Roll roll;
        final GuardianData data;
        final GuardianRuntime runtime;
        final GuardianClass guardianClass;
        final boolean loadoutEnabled;
        final int slot;
        final PulseMonitorCycle cycle = new PulseMonitorCycle();
        long observed;
        Session(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry, WeaponPerks.Roll roll, int slot) {
            owner=p; level=p.level(); this.stack=stack; this.entry=entry; this.roll=roll; this.slot=slot;
            data=p.getAttachedOrElse(Guardians.DATA,null); runtime=Guardians.runtimeIfPresent(p).orElseThrow();
            guardianClass=data.guardianClass(); loadoutEnabled=WeaponLoadout.enabled(p); observed=now(p);
        }
    }
    private WeaponPulseMonitor() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (!p.level().getServer().isSameThread()) throw new IllegalStateException("Pulse Monitor is server-thread owned");
    }
    private static boolean ownerValid(ServerPlayer p) {
        if (p==null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
        var data=p.getAttachedOrElse(Guardians.DATA,null);
        var runtime=Guardians.runtimeIfPresent(p).orElse(null);
        return data!=null && data.guardianClass()!=null && data.guardianClass()!=GuardianClass.NONE
            && runtime!=null && runtime.superSession==null;
    }
    private static int equippedSlot(ServerPlayer p, ItemStack stack) {
        if (stack==null || stack.isEmpty() || stack.getCount()!=1) return -1;
        if (WeaponLoadout.enabled(p) && WeaponLoadout.equipped(p).stream().noneMatch(e->e.stack()==stack)) return -1;
        for (int i=0;i<9;i++) if (p.getInventory().getItem(i)==stack) return i;
        return -1;
    }
    private static boolean valid(ServerPlayer p, Session s) {
        return ownerValid(p) && s.owner==p && s.level==p.level() && now(p)>=s.observed
            && p.getAttachedOrElse(Guardians.DATA,null)==s.data && s.data.guardianClass()==s.guardianClass
            && Guardians.runtimeIfPresent(p).orElse(null)==s.runtime
            && WeaponLoadout.enabled(p)==s.loadoutEnabled && equippedSlot(p,s.stack)==s.slot
            && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
            && WeaponPerks.selected(s.stack,PulseMonitorProfile.ID).filter(s.roll::equals).isPresent();
    }
    /** First tick may observe low health. Never bind from a timing/HUD getter. */
    public static void update(ServerPlayer p) { observe(p); }
    /** Invoke AFTER actual positive health loss. Denied, absorbed and invalid damage are inert. */
    public static void damaged(ServerPlayer p, float actualLoss) {
        if (!Float.isFinite(actualLoss) || actualLoss<=0) return;
        observe(p);
    }
    private static void observe(ServerPlayer p) {
        if (p==null) return;
        thread(p);
        var sessions=SESSIONS.get(p.getUUID());
        if (sessions!=null) {
            // New player object may replace a stale same-UUID owner; old cleanup is identity-scoped.
            sessions.values().removeIf(s->{ if (s.owner!=p || valid(p,s)) return false; s.cycle.clear(); return true; });
            if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
        }
        if (!ownerValid(p)) return;
        boolean transferred=false;
        for (int slot=0;slot<9;slot++) {
            var stack=p.getInventory().getItem(slot);
            if (equippedSlot(p,stack)!=slot) continue;
            var entry=WeaponItems.entry(stack).orElse(null);
            var roll=WeaponPerks.selected(stack,PulseMonitorProfile.ID).orElse(null);
            if (!PulseMonitorProfile.supports(entry) || roll==null || !PulseMonitorProfile.rolls().contains(roll)
                    || !entry.id().equals(roll.id())) continue;
            sessions=SESSIONS.computeIfAbsent(p.getUUID(),id->new IdentityHashMap<>());
            var s=sessions.get(stack);
            if (s==null || !valid(p,s)) {
                if (s!=null) s.cycle.clear();
                s=new Session(p,stack,entry,roll,slot); sessions.put(stack,s);
            }
            boolean entered=s.cycle.update(now(p),p.getHealth(),p.getMaxHealth()); s.observed=now(p);
            if (entered) transferred |= refill(p,s);
        }
        if (transferred) { p.getInventory().setChanged(); p.containerMenu.broadcastChanges(); }
    }
    private static boolean refill(ServerPlayer p, Session s) {
        var profile=WeaponProfile.forEntry(s.entry);
        // Preserve existing Primary infinite reserves; Special/Heavy transfer real reserve/overflow.
        if (WeaponIzanagi.charge(s.stack)>0 || SwordItems.isSword(s.stack)) return false;
        var ammo=WeaponItems.magazine(s.stack,profile);
        if (ammo.reload()<=0) return false;
        WeaponRuntime.cancelForTraitRefill(p,s.stack);
        WeaponItems.save(s.stack,ammo);
        return true;
    }
    private static Session session(ServerPlayer p, ItemStack stack) {
        if (p==null) return null;
        var sessions=SESSIONS.get(p.getUUID()); var s=sessions==null?null:sessions.get(stack);
        return s!=null && valid(p,s) && s.cycle.active(now(p)) ? s : null;
    }
    /** Observe the actual buff on any still-equipped original, including a stowed source.
     * Pure HUD query: never binds, prunes, transfers ammo or refreshes an episode. */
    public static boolean active(ServerPlayer p) {
        if (p==null) return false;
        var sessions=SESSIONS.get(p.getUUID());
        return sessions!=null && sessions.values().stream()
            .anyMatch(s->valid(p,s) && s.cycle.active(now(p)));
    }
    /** Pure original hotbar object query, including incoming/outgoing selection timing. */
    public static int handlingBonus(ServerPlayer p, ItemStack stack) {
        return session(p,stack)==null?0:PulseMonitorProfile.handlingBonus();
    }
    public static double handlingScalar(ServerPlayer p, ItemStack stack) {
        return session(p,stack)==null?1:PulseMonitorProfile.handlingScalar();
    }
    /** Actual identity/equipment replacement only. Stowing alone MUST NOT call changed. */
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p==null) return; thread(p);
        var sessions=SESSIONS.get(p.getUUID());var s=sessions==null?null:sessions.get(stack);
        if (s!=null && s.owner==p) { s.cycle.clear(); sessions.remove(stack); }
        if (sessions!=null && sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    public static void edited(ItemStack stack) {
        var it=SESSIONS.values().iterator();
        while (it.hasNext()) { var sessions=it.next();var s=sessions.remove(stack);
            if (s!=null) s.cycle.clear(); if (sessions.isEmpty()) it.remove(); }
    }
    public static void cleanup(ServerPlayer p) {
        if (p==null) return; thread(p);
        var sessions=SESSIONS.get(p.getUUID()); if (sessions==null) return;
        sessions.values().removeIf(s->{if(s.owner!=p)return false;s.cycle.clear();return true;});
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    public static void clear() {
        for(var sessions:SESSIONS.values())for(var s:sessions.values())s.cycle.clear();SESSIONS.clear();
    }
}
