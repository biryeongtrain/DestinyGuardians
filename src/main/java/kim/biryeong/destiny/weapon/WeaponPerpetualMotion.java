package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Actual server displacement, including original stowed stacks. No packet flags, player velocity,
 * previews, HUD query or item data can grant stacks. Inventory membership uses object identity. */
public final class WeaponPerpetualMotion {
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final IdentityHashMap<ItemStack,PerpetualMotionCycle> weapons = new IdentityHashMap<>();
        final MotionSpeedWindow speed = new MotionSpeedWindow();
        Vec3 previous;
        long last = -1;
        Session(ServerPlayer p) { owner=p; level=p.level(); previous=p.position(); }
    }
    private WeaponPerpetualMotion() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected();
    }
    /** Stowed means equipped, not every backpack item. Legacy standalone supports its hotbar only. */
    private static boolean possessed(ServerPlayer p,ItemStack stack) {
        if (WeaponLoadout.enabled(p)) return WeaponLoadout.equipped(p).stream().anyMatch(e->e.stack()==stack);
        for (int i=0;i<9;i++) if (p.getInventory().getItem(i)==stack) return true;
        return false;
    }
    private static boolean selected(ItemStack stack) {
        return WeaponPerks.selected(stack,PerpetualMotionProfile.ID).isPresent();
    }
    /** Called by server ticks, at most once per tick even when tickPlayer is also invoked. */
    public static void update(ServerPlayer p) {
        if (!ownerValid(p)) { cleanup(p); return; }
        var s=SESSIONS.get(p.getUUID());
        if (s==null || s.owner!=p || s.level!=p.level()) { s=new Session(p);SESSIONS.put(p.getUUID(),s); }
        long tick=now(p);
        if (s.last==tick) return;
        Vec3 pos=p.position();double distance=pos.distanceToSqr(s.previous);
        // 2 blocks/tick is a local discontinuity guard, not an exact Destiny teleport detector.
        boolean continuous=s.last>=0 && tick>s.last && tick-s.last==1 && Double.isFinite(distance)
                && distance<=4 && !p.isPassenger();
        // Server ticks and client movement packets need not arrive in lockstep. Averaging the
        // last five actual travel samples prevents a 0/.4/0/.4 batch from losing half its time.
        // Discontinuities clear the window, and raw slow time keeps the .5s removal bound.
        if (!continuous) s.speed.reset();
        boolean moving=continuous && s.speed.sample(Math.sqrt(distance)); // >=2m/s at20Hz
        s.weapons.entrySet().removeIf(e->!possessed(p,e.getKey()) || !selected(e.getKey()));
        for (int i=0;i<p.getInventory().getContainerSize();i++) {
            var stack=p.getInventory().getItem(i);
            if (possessed(p,stack) && selected(stack) && !s.weapons.containsKey(stack)) s.weapons.put(stack,new PerpetualMotionCycle());
        }
        for (var cycle:s.weapons.values()) {
            if (!continuous || s.speed.stopGraceElapsed()) cycle.reset();
            cycle.sample(tick,moving);
        }
        s.previous=pos;s.last=tick;
        if (s.weapons.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    /** Pure inventory source query, also used for the outgoing stow part of a real swap. */
    public static int ownedStacks(ServerPlayer p,ItemStack stack) {
        var s=SESSIONS.get(p.getUUID());
        if (s==null || s.owner!=p || s.level!=p.level() || !ownerValid(p)
                || !possessed(p,stack) || !selected(stack)) return 0;
        var cycle=s.weapons.get(stack);return cycle==null?0:cycle.stacks();
    }
    public static int stacks(ServerPlayer p) {
        return WeaponLoadout.canUse(p) && !AbilityService.inSuper(p) ? ownedStacks(p,p.getMainHandItem()) : 0;
    }
    public static int stabilityBonus(ServerPlayer p) { return stacks(p)*10; }
    public static int movingTicks(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());var stack=p.getMainHandItem();
        if (s==null || s.owner!=p || s.level!=p.level() || !ownerValid(p)
                || !possessed(p,stack) || !selected(stack)) return 0;
        var cycle=s.weapons.get(stack);return cycle==null?0:cycle.movingTicks();
    }
    public static int adsTicks(ServerPlayer p,WeaponCatalog.Entry entry,int base) {
        int count=stacks(p);return count==0 ? base : PerpetualMotionProfile.timing(entry,count).adsTicks();
    }
    public static int handlingTicks(ServerPlayer p,ItemStack stack,boolean ready,int base) {
        int count=ownedStacks(p,stack);
        if (count==0) return base;
        var entry=WeaponItems.entry(stack).orElseThrow();var timing=PerpetualMotionProfile.timing(entry,count);
        return ready ? timing.readyTicks() : timing.stowTicks();
    }
    public static WeaponReloadPolicy.Plan plan(ServerPlayer p,WeaponCatalog.Entry entry,WeaponReloadPolicy.Plan base) {
        int count=stacks(p);
        if (count==0) return base;
        if (WeaponItems.entry(p.getMainHandItem()).filter(entry::equals).isEmpty())
            throw new IllegalArgumentException("Reload plan must belong to held weapon");
        int ticks=PerpetualMotionProfile.timing(entry,count).reloadTicks();
        return new WeaponReloadPolicy.Plan(ticks,ticks,base.roundsPerInsert());
    }
    public static void edited(ItemStack stack) {
        for (var s:SESSIONS.values()) s.weapons.remove(stack);
    }
    public static void changed(ServerPlayer p,ItemStack stack) {
        var s=SESSIONS.get(p.getUUID());if (s!=null && s.owner==p) s.weapons.remove(stack);
    }
    public static void cleanup(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());if (s!=null && s.owner==p) SESSIONS.remove(p.getUUID());
    }
    public static void clear() { SESSIONS.clear(); }
}
