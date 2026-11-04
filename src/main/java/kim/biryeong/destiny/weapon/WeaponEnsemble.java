package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Server-thread proximity observations; queries never scan, bind, create attachments/runtime,
 * refresh linger, or mutate the stack. Stowing revokes live state, including same-tick swaps.
 * Call selecting only inside an accepted selection, before calculating the incoming ready time.
 */
public final class WeaponEnsemble {
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
        final int slot;
        final EnsembleCycle cycle = new EnsembleCycle();
        long observed;
        long selectionTick = -1;
        int selectionFrom = -1;
        Session(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry, int slot) {
            owner = p; level = p.level(); this.stack = stack; this.entry = entry; this.slot = slot;
            roll = WeaponPerks.selected(stack, EnsembleProfile.ID).orElseThrow();
            data = p.getAttachedOrElse(Guardians.DATA, null);
            runtime = Guardians.runtimeIfPresent(p).orElseThrow();
            guardianClass = data.guardianClass(); observed = now(p);
        }
    }
    private WeaponEnsemble() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("Ensemble is main server thread owned");
    }
    private static boolean eligiblePlayer(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected();
    }
    private static boolean ownerValid(ServerPlayer p) {
        if (!eligiblePlayer(p)) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        var runtime = Guardians.runtimeIfPresent(p).orElse(null);
        return data != null && data.guardianClass() != null && data.guardianClass() != GuardianClass.NONE
            && runtime != null && runtime.superSession == null;
    }
    /** Actual hotbar object, additionally constrained to the loadout's canonical equipment slots. */
    private static int equippedSlot(ServerPlayer p, ItemStack stack) {
        if (stack == null || stack.isEmpty()) return -1;
        if (WeaponLoadout.enabled(p) && WeaponLoadout.equipped(p).stream().noneMatch(e -> e.stack() == stack)) return -1;
        for (int i = 0; i < 9; i++) if (p.getInventory().getItem(i) == stack) return i;
        return -1;
    }
    private static WeaponCatalog.Entry source(ServerPlayer p, ItemStack stack) {
        if (!ownerValid(p) || equippedSlot(p, stack) < 0) return null;
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, EnsembleProfile.ID).orElse(null);
        return EnsembleProfile.supports(entry) && roll != null && EnsembleProfile.rolls().contains(roll) ? entry : null;
    }
    private static boolean held(ServerPlayer p, Session s) {
        return p.getMainHandItem() == s.stack && p.getInventory().getSelectedSlot() == s.slot && WeaponLoadout.canUse(p);
    }
    private static boolean valid(ServerPlayer p, Session s) {
        if (!ownerValid(p)) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        return s.owner == p && s.level == p.level() && data == s.data && data.guardianClass() == s.guardianClass
            && Guardians.runtimeIfPresent(p).orElse(null) == s.runtime && now(p) >= s.observed
            && equippedSlot(p, s.stack) == s.slot
            && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
            && WeaponPerks.selected(s.stack, EnsembleProfile.ID).filter(s.roll::equals).isPresent();
    }
    /** Existing PvE policy admits other players; vanilla scoreboard teams can restrict it.
     * Pets, armor stands, arbitrary non-enemies and the owner never count as player allies.
     */
    private static boolean ally(ServerPlayer p, ServerPlayer other) {
        return other != p && eligiblePlayer(other) && other.level() == p.level()
            && (p.getTeam() == null && other.getTeam() == null || p.isAlliedTo(other));
    }
    private static boolean nearby(ServerPlayer p) {
        var origin = p.position();
        if (!Double.isFinite(origin.x) || !Double.isFinite(origin.y) || !Double.isFinite(origin.z)) return false;
        // Already loaded players in this level. No chunks, LOS, entities list, or runtime creation.
        for (var other : p.level().players()) {
            if (!ally(p, other)) continue;
            var point = other.position();
            if (EnsembleProfile.withinRadius(point.x - origin.x, point.y - origin.y, point.z - origin.z)) return true;
        }
        return false;
    }
    private static Session sample(ServerPlayer p, ItemStack stack, boolean selecting) {
        var entry = source(p, stack);
        if (entry == null) return null;
        var sessions = SESSIONS.computeIfAbsent(p.getUUID(), id -> new IdentityHashMap<>());
        var s = sessions.get(stack);
        if (s == null || !valid(p, s)) {
            s = new Session(p, stack, entry, equippedSlot(p, stack));
            sessions.put(stack, s);
        }
        s.cycle.update(now(p), true, nearby(p));
        s.observed = now(p);
        s.selectionTick = selecting ? now(p) : -1;
        s.selectionFrom = selecting ? p.getInventory().getSelectedSlot() : -1;
        return s;
    }
    /** Tick and accepted aim/reload boundary. Resamples even within the same tick. */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions != null) {
            sessions.values().removeIf(s -> !valid(p, s) || !held(p, s));
            if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
        }
        if (!ownerValid(p) || !WeaponLoadout.canUse(p)) return;
        var stack = p.getMainHandItem();
        int slot = p.getInventory().getSelectedSlot();
        if (slot >= 0 && slot < 9 && p.getInventory().getItem(slot) == stack) sample(p, stack, false);
    }
    /** Accepted incoming object before vanilla changes the selected slot. No speculative getter.
     * Never imports the outgoing weapon's linger. An unselected preparation expires this tick.
     */
    public static void selecting(ServerPlayer p, ItemStack incoming) {
        if (p == null) return;
        thread(p);
        if (ownerValid(p)) sample(p, incoming, true);
    }
    private static Session session(ServerPlayer p, ItemStack stack, boolean requireHeld) {
        if (p == null) return null;
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s == null || !valid(p, s)) return null;
        if (held(p, s)) return s;
        return !requireHeld && s.selectionTick == now(p) && s.selectionFrom == p.getInventory().getSelectedSlot() ? s : null;
    }
    public static boolean active(ServerPlayer p) { return remaining(p) > 0; }
    public static int remaining(ServerPlayer p) {
        var s = p == null ? null : session(p, p.getMainHandItem(), true);
        return s == null ? 0 : s.cycle.remaining(now(p));
    }
    public static int handlingBonus(ServerPlayer p) { return active(p) ? EnsembleProfile.handlingBonus() : 0; }
    public static int reloadBonus(ServerPlayer p) { return active(p) ? EnsembleProfile.reloadBonus() : 0; }

    /** OUTERMOST wrapper. Exact Canis Major companions are Kill Clip/Rampage/Vorpal: no stat
     * providers or scalars. Surplus occupies the SAME socket3, not a legal ability-charge bonus.
     * If official pools change, update both the proof and composition before expanding support.
     */
    public static int handlingTicks(ServerPlayer p, ItemStack stack, boolean ready, int base) {
        var s = session(p, stack, false);
        if (s == null || !s.cycle.active(now(p))) return base;
        return EnsembleProfile.handlingTicks(s.entry, EnsembleProfile.handlingBonus(), ready);
    }
    public static int adsTicks(ServerPlayer p, WeaponCatalog.Entry entry, int base, boolean entering) {
        var s = p == null ? null : session(p, p.getMainHandItem(), true);
        if (s == null || !s.entry.equals(entry) || !s.cycle.active(now(p))) return base;
        return EnsembleProfile.adsTicks(entry, EnsembleProfile.handlingBonus());
    }
    /** Pure acceptance snapshot, raw stat curve then one ceil. No later ally change retimes it. */
    public static WeaponReloadPolicy.Plan plan(ServerPlayer p, WeaponCatalog.Entry entry, WeaponReloadPolicy.Plan base) {
        var s = p == null ? null : session(p, p.getMainHandItem(), true);
        if (s == null || !s.entry.equals(entry) || !s.cycle.active(now(p))) return base;
        return EnsembleProfile.reloadPlan(entry, EnsembleProfile.reloadBonus(), base);
    }
    /** Calculate outgoing stow first, then revoke even on same-tick away-and-back selection. */
    public static void stowing(ServerPlayer p, ItemStack stack) { changed(p, stack); }
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && s.owner == p) {
            sessions.remove(stack);
            if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
        }
    }
    public static void edited(ItemStack stack) {
        var iterator = SESSIONS.values().iterator();
        while (iterator.hasNext()) {
            var sessions = iterator.next();
            sessions.remove(stack);
            if (sessions.isEmpty()) iterator.remove();
        }
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> s.owner == p);
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    public static void clear() { SESSIONS.clear(); }
}
