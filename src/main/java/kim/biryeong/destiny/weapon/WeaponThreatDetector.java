package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Main-thread held-source proximity sample. update before gameplay/HUD queries and accepted
 * reload/aim/swap decisions; getters never scan entities, bind a source, proc, or advance time.
 * No countdown, linger, damage token, damage bonus, range bonus or line-of-sight invention.
 * Radius and enemy filtering are explicitly local PvE policies, not measured Destiny geometry.
 */
public final class WeaponThreatDetector {
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
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
        int stacks;
        long observed;
        Session(ServerPlayer p, WeaponCatalog.Entry entry, WeaponPerks.Roll roll) {
            owner = p; level = p.level(); stack = p.getMainHandItem(); this.entry = entry; this.roll = roll;
            data = Guardians.data(p); runtime = Guardians.runtimeIfPresent(p).orElse(null);
            guardianClass = data.guardianClass(); slot = p.getInventory().getSelectedSlot(); observed = now(p);
        }
    }
    private WeaponThreatDetector() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
            && !AbilityService.inSuper(p);
    }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("Threat Detector is main server thread owned");
    }
    private static boolean valid(ServerPlayer p, Session s) {
        if (!ownerValid(p)) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        return s.owner == p && s.level == p.level() && p.getMainHandItem() == s.stack
            && p.getInventory().getSelectedSlot() == s.slot && s.slot >= 0 && s.slot < 9
            && p.getInventory().getItem(s.slot) == s.stack && WeaponLoadout.canUse(p)
            && data == s.data && Guardians.runtimeIfPresent(p).orElse(null) == s.runtime
            && data != null && data.guardianClass() == s.guardianClass && now(p) >= s.observed
            && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
            && WeaponPerks.selected(s.stack, ThreatDetectorProfile.ID).filter(s.roll::equals).isPresent();
    }
    private static boolean enemy(ServerPlayer p, LivingEntity e) {
        return e.level() == p.level() && e.isAlive() && !e.isRemoved() && !e.isSpectator()
            && !(e instanceof Player) && !(e instanceof ArmorStand) && Combat.isEnemy(p, e)
            && !p.isAlliedTo(e) && !(e instanceof TamableAnimal tame && tame.isTame());
    }
    private static int nearby(ServerPlayer p) {
        var origin = p.position();
        if (!Double.isFinite(origin.x) || !Double.isFinite(origin.y) || !Double.isFinite(origin.z)) return 0;
        int count = 0;
        // Loaded entity storage only: no chunk loads, sorted/materialized entity list, or wall test.
        // Iterate lazily and stop at the second qualifying enemy, including exact 15m footpoints.
        for (var entity : p.level().getAllEntities()) {
            if (!(entity instanceof LivingEntity e) || !enemy(p, e)) continue;
            var point = e.position();
            if (ThreatDetectorProfile.withinRadius(point.x - origin.x, point.y - origin.y, point.z - origin.z)
                && ++count == 2) return 2;
        }
        return count;
    }
    /** Explicit accepted-selection sample for an owned incoming weapon, before vanilla changes
     * the hotbar slot. This is not a getter: callers cache it in that selection transaction.
     * Reuse the ordinary loaded-entity radius/enemy policy without replacing the held session.
     */
    public static int selectionSample(ServerPlayer p, ItemStack stack) {
        if (p == null) return 0;
        thread(p);
        if (!ownerValid(p) || stack == null || stack.isEmpty()) return 0;
        boolean equipped = false;
        if (WeaponLoadout.enabled(p)) equipped = WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == stack);
        else for (int slot = 0; slot < 9; slot++) if (p.getInventory().getItem(slot) == stack) { equipped = true; break; }
        if (!equipped) return 0;
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, ThreatDetectorProfile.ID).orElse(null);
        return ThreatDetectorProfile.supports(entry) && roll != null && ThreatDetectorProfile.rolls().contains(roll)
            && entry.id().equals(roll.id()) ? nearby(p) : 0;
    }
    /** Rescan even within the same tick: an enemy entering before accepted reload must count.
     * Only this path creates sessions. Replacements never inherit the previous object's sample.
     */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var s = SESSIONS.get(p.getUUID());
        if (s != null && !valid(p, s)) { SESSIONS.remove(p.getUUID()); s = null; }
        if (!ownerValid(p) || !WeaponLoadout.canUse(p)) return;
        int slot = p.getInventory().getSelectedSlot();
        var stack = p.getMainHandItem();
        if (slot < 0 || slot >= 9 || p.getInventory().getItem(slot) != stack) return;
        var entry = WeaponItems.entry(stack);
        var roll = WeaponPerks.selected(stack, ThreatDetectorProfile.ID);
        if (entry.isEmpty() || roll.isEmpty() || !ThreatDetectorProfile.supports(entry.get())
            || !ThreatDetectorProfile.rolls().contains(roll.get()) || !entry.get().id().equals(roll.get().id())) return;
        if (s == null) { s = new Session(p, entry.get(), roll.get()); SESSIONS.put(p.getUUID(), s); }
        s.stacks = nearby(p);
        s.observed = now(p);
    }
    private static Session held(ServerPlayer p) {
        if (p == null) return null;
        var s = SESSIONS.get(p.getUUID());
        return s != null && valid(p, s) ? s : null;
    }
    public static int stacks(ServerPlayer p) { var s = held(p); return s == null ? 0 : s.stacks; }
    public static int stabilityBonus(ServerPlayer p) { return ThreatDetectorProfile.stabilityBonus(stacks(p)); }
    private static boolean co(Session s, String proof, String id) {
        return WeaponPerks.selected(s.stack, id).filter(r -> ThreatDetectorProfile.compatible(s.entry, proof, r)).isPresent();
    }
    private static int handlingBonus(ServerPlayer p, Session s) {
        // Only Frenzy can share a handling-stat pair in the current exact17. AJ/PM/SFA cannot:
        // official-sockets.json proves their empty distinct-pair sets (SFA is same socket).
        return ThreatDetectorProfile.handlingBonus(s.stacks)
            + (co(s, "frenzy", FrenzyProfile.ID) && WeaponFrenzy.ownedRemaining(p, s.stack) > 0 ? FrenzyProfile.handlingBonus() : 0);
    }
    public static int handlingTicks(ServerPlayer p, ItemStack stack, boolean ready, int base) {
        var s = held(p);
        if (s == null || s.stack != stack || s.stacks == 0) return base;
        return ThreatDetectorProfile.handlingTicks(s.entry, handlingBonus(p, s), ThreatDetectorProfile.handlingScalar(s.stacks), ready);
    }
    public static int adsTicks(ServerPlayer p, WeaponCatalog.Entry entry, int base, boolean entering) {
        var s = held(p);
        if (s == null || s.stacks == 0 || !s.entry.equals(entry)) return base;
        return ThreatDetectorProfile.adsTicks(entry, handlingBonus(p, s), entering && co(s, "snapshot", SnapshotAimProfile.ID));
    }
    /** Called after other reload wrappers. Query the actual profile's effective/base stat delta
     * rather than duplicate tier tables: positive bonuses still produce the same final capped sum.
     * Impossible Rapid Hit/PM/SFA pairs are not granted; compatible FF/Outlaw scalars survive.
     * This immutable accepted plan remains fixed if proximity changes during the reload.
     */
    public static WeaponReloadPolicy.Plan plan(ServerPlayer p, WeaponCatalog.Entry entry, WeaponReloadPolicy.Plan base) {
        var s = held(p);
        if (s == null || s.stacks == 0) return base;
        if (!s.entry.equals(entry)) throw new IllegalArgumentException("Foreign Threat Detector reload plan");
        int other = 0;
        double scalar = 1;
        if (co(s, "frenzy", FrenzyProfile.ID) && WeaponFrenzy.remaining(p) > 0) other += FrenzyProfile.reloadBonus();
        if (co(s, "outlaw", OutlawProfile.ID) && WeaponOutlaw.remaining(p) > 0) {
            other += OutlawProfile.perk().reloadBonus(); scalar *= OutlawProfile.perk().durationMultiplier();
        }
        if (co(s, "feeding_frenzy", FeedingFrenzyProfile.ID)) {
            int count = WeaponFeedingFrenzy.stacks(p);
            if (count > 0) {
                var reload = FeedingFrenzyProfile.reload(entry, count);
                other += reload.effectiveReloadStat() - reload.baseReloadStat();
                scalar *= FeedingFrenzyProfile.durationMultiplier(count);
            }
        }
        return ThreatDetectorProfile.reloadPlan(entry, other + ThreatDetectorProfile.reloadBonus(s.stacks), scalar, other, scalar, base);
    }
    /** Accepted stow removes live stacks, including same-tick away-and-back. Calculate stow first. */
    public static void stowing(ServerPlayer p, ItemStack stack) { changed(p, stack); }
    public static void edited(ItemStack stack) {
        SESSIONS.values().removeIf(s -> s.stack == stack);
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p && s.stack == stack) SESSIONS.remove(p.getUUID());
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) SESSIONS.remove(p.getUUID());
    }
    public static void clear() { SESSIONS.clear(); }
}
