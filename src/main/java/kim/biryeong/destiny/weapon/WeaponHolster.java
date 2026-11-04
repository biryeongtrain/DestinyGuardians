package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Paid stowed reloads, bounded to three real equipped stacks. Separate from shot/Handling state. */
public final class WeaponHolster {
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final Map<ItemStack, WeaponHolsterCycle> clocks = new IdentityHashMap<>();
        Session(ServerPlayer owner) { this.owner = owner; this.level = owner.level(); }
    }
    private WeaponHolster() {}
    private static boolean eligible(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && !AbilityService.inSuper(p) && WeaponLoadout.enabled(p);
    }
    public static void update(ServerPlayer p) { observe(p, p.getMainHandItem()); }
    /** Native/command validated selection boundary, before the inventory changes. */
    public static void selecting(ServerPlayer p, int slot) {
        if (slot < 0 || slot >= 9 || slot == p.getInventory().getSelectedSlot()) return;
        update(p); // Pay an already-due stowed reload before drawing that weapon.
        observe(p, p.getInventory().getItem(slot));
    }
    private static void observe(ServerPlayer p, ItemStack held) {
        if (!eligible(p)) { cleanup(p); return; }
        var equipped = WeaponLoadout.equipped(p).stream()
                .filter(e -> WeaponPerks.selected(e.stack()).isPresent()).toList();
        if (equipped.isEmpty()) { cleanup(p); return; }
        Session s = SESSIONS.get(p.getUUID());
        if (s == null || s.owner != p || s.level != p.level()) {
            s = new Session(p); SESSIONS.put(p.getUUID(), s);
        }
        Set<ItemStack> present = Collections.newSetFromMap(new IdentityHashMap<>());
        equipped.forEach(e -> present.add(e.stack()));
        s.clocks.keySet().removeIf(stack -> !present.contains(stack));
        long tick = p.level().getServer().getTickCount();
        boolean changed = false;
        for (var item : equipped) {
            var clock = s.clocks.computeIfAbsent(item.stack(), ignored -> new WeaponHolsterCycle());
            if (!clock.observe(tick, item.stack() == held, WeaponPerks.stowedTicks())) continue;
            var ammo = WeaponItems.magazine(item.stack(), WeaponProfile.forEntry(item.weapon()));
            if (ammo.reload() > 0) {
                WeaponItems.save(item.stack(), ammo);
                changed = true;
            }
        }
        if (changed) { p.getInventory().setChanged(); p.containerMenu.broadcastChanges(); }
    }
    /** Actual trait edits restart only that stack, never other weapons' running timers. */
    public static void changed(ServerPlayer p, ItemStack stack) {
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) s.clocks.remove(stack);
    }
    public static void cleanup(ServerPlayer p) {
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) SESSIONS.remove(p.getUUID());
    }
    public static void clear() { SESSIONS.clear(); }
}
