package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Main-server-thread held-original-source proximity observations. Only update scans/binds;
 * getters never create attachments/runtime, refresh time, scan entities or edit items.
 * Master samples on ticks and both accepted fusion starts, then freezes the full charge profile.
 */
public final class WeaponCornered {
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
        final boolean loadoutEnabled;
        final CorneredCycle cycle = new CorneredCycle();
        long observed;
        Session(ServerPlayer p, WeaponCatalog.Entry entry, WeaponPerks.Roll roll) {
            owner = p; level = p.level(); stack = p.getMainHandItem(); this.entry = entry; this.roll = roll;
            data = p.getAttachedOrElse(Guardians.DATA, null);
            runtime = Guardians.runtimeIfPresent(p).orElseThrow();
            guardianClass = data.guardianClass(); slot = p.getInventory().getSelectedSlot();
            loadoutEnabled = WeaponLoadout.enabled(p); observed = now(p);
        }
    }
    private WeaponCornered() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("Cornered is main server thread owned");
    }
    private static boolean ownerValid(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        var runtime = Guardians.runtimeIfPresent(p).orElse(null);
        return data != null && data.guardianClass() != null && data.guardianClass() != GuardianClass.NONE
            && runtime != null && runtime.superSession == null;
    }
    private static boolean heldSource(ServerPlayer p, ItemStack stack, int slot) {
        return stack != null && !stack.isEmpty() && stack.getCount() == 1 && slot >= 0 && slot < 9
            && p.getMainHandItem() == stack && p.getInventory().getSelectedSlot() == slot
            && p.getInventory().getItem(slot) == stack && WeaponLoadout.canUse(p)
            && (!WeaponLoadout.enabled(p) || WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == stack));
    }
    private static boolean valid(ServerPlayer p, Session s) {
        if (!ownerValid(p)) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        return s.owner == p && s.level == p.level() && data == s.data
            && data.guardianClass() == s.guardianClass && Guardians.runtimeIfPresent(p).orElse(null) == s.runtime
            && WeaponLoadout.enabled(p) == s.loadoutEnabled && heldSource(p, s.stack, s.slot)
            && now(p) >= s.observed && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
            && WeaponPerks.selected(s.stack, CorneredProfile.ID).filter(s.roll::equals).isPresent();
    }
    /** Keep the exact WeaponThreatDetector PvE policy, including excluding every tamed animal. */
    private static boolean enemy(ServerPlayer p, LivingEntity e) {
        return e.level() == p.level() && e.isAlive() && !e.isRemoved() && !e.isSpectator()
            && !(e instanceof Player) && !(e instanceof ArmorStand) && Combat.isEnemy(p, e)
            && !p.isAlliedTo(e) && !(e instanceof TamableAnimal tame && tame.isTame());
    }
    private static int nearby(ServerPlayer p) {
        var origin = p.position();
        if (!Double.isFinite(origin.x) || !Double.isFinite(origin.y) || !Double.isFinite(origin.z)) return 0;
        int count = 0;
        // Already-loaded entity storage only; no chunk loads, materialized list or wall test.
        for (var entity : p.level().getAllEntities()) {
            if (!(entity instanceof LivingEntity e) || !enemy(p, e)) continue;
            var point = e.position();
            if (CorneredProfile.withinRadius(point.x - origin.x, point.y - origin.y, point.z - origin.z)
                && ++count >= CorneredProfile.enemiesRequired()) return count;
        }
        return count;
    }

    /** Resample even in the same tick so accepted charge observes the latest enemy positions. */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var s = SESSIONS.get(p.getUUID());
        if (s != null && !valid(p, s)) { SESSIONS.remove(p.getUUID()); s = null; }
        if (!ownerValid(p)) return;
        var stack = p.getMainHandItem();
        if (!heldSource(p, stack, p.getInventory().getSelectedSlot())) return;
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, CorneredProfile.ID).orElse(null);
        if (!CorneredProfile.supports(entry) || roll == null || !CorneredProfile.rolls().contains(roll)
            || !entry.id().equals(roll.id())) return;
        if (s == null) { s = new Session(p, entry, roll); SESSIONS.put(p.getUUID(), s); }
        s.cycle.update(now(p), true, nearby(p));
        s.observed = now(p);
    }
    private static Session held(ServerPlayer p) {
        if (p == null) return null;
        var s = SESSIONS.get(p.getUUID());
        return s != null && valid(p, s) ? s : null;
    }
    public static boolean active(ServerPlayer p) { return remaining(p) > 0; }
    public static int remaining(ServerPlayer p) {
        var s = held(p);
        return s == null ? 0 : s.cycle.remaining(now(p));
    }
    /** Pure acceptance snapshot. Keep this entire profile through charge/burst continuation. */
    public static WeaponProfile charge(ServerPlayer p, WeaponCatalog.Entry entry, WeaponProfile base) {
        var s = held(p);
        return s != null && s.entry.equals(entry) && s.cycle.active(now(p))
            ? CorneredProfile.charge(entry, base) : base;
    }
    /** Actual stow revokes linger even on same-tick away-and-back selections. */
    public static void stowing(ServerPlayer p, ItemStack stack) { changed(p, stack); }
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p && s.stack == stack) SESSIONS.remove(p.getUUID());
    }
    public static void edited(ItemStack stack) { SESSIONS.values().removeIf(s -> s.stack == stack); }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) SESSIONS.remove(p.getUUID());
    }
    public static void clear() { SESSIONS.clear(); }
}
