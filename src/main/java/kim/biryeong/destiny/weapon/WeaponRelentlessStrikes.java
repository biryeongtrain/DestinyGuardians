package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Paid, nonempty sword contacts only. Master owns attribution and shared lifecycle wiring.
 * Event methods generate finite ammunition in the ORIGINAL source, including after stow.
 * Main server thread only; no attachment creation, reserve transfer, generic death or HUD write.
 */
public final class WeaponRelentlessStrikes {
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
        final RelentlessStrikesCycle cycle;
        long observed;
        Session(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry, WeaponPerks.Roll roll) {
            owner = p; level = p.level(); this.stack = stack; this.entry = entry; this.roll = roll;
            data = p.getAttachedOrElse(Guardians.DATA, null);
            runtime = Guardians.runtimeIfPresent(p).orElseThrow();
            guardianClass = data.guardianClass(); loadoutEnabled = WeaponLoadout.enabled(p);
            observed = now(p); cycle = new RelentlessStrikesCycle();
        }
    }
    /** Opaque paid-contact authority; share this exact token across cleave/direct/explosion. */
    public static final class Token {
        public static final Token NONE = new Token(null, null);
        private final Session source;
        private final RelentlessStrikesCycle.Contact contact;
        private Token(Session source, RelentlessStrikesCycle.Contact contact) { this.source = source; this.contact = contact; }
    }
    private WeaponRelentlessStrikes() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("RelentlessStrikes is main server thread owned");
    }
    private static boolean ownerValid(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        var runtime = Guardians.runtimeIfPresent(p).orElse(null);
        return data != null && data.guardianClass() != null && data.guardianClass() != GuardianClass.NONE
            && runtime != null && runtime.superSession == null;
    }
    /** Unique original count-one hotbar object; loadout mode additionally requires canonical slot. */
    private static boolean owned(ServerPlayer p, ItemStack stack) {
        if (stack == null || stack.isEmpty() || stack.getCount() != 1) return false;
        int count = 0, slot = -1;
        for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
            if (p.getInventory().getItem(i) == stack) { count++; slot = i; }
        }
        return count == 1 && slot >= 0 && slot < 9 && (!WeaponLoadout.enabled(p)
            || WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == stack));
    }
    private static boolean valid(ServerPlayer p, Session s) {
        if (!ownerValid(p)) return false;
        var sessions = SESSIONS.get(p.getUUID());
        return sessions != null && sessions.get(s.stack) == s && s.owner == p && s.level == p.level()
            && now(p) >= s.observed && owned(p, s.stack)
            && p.getAttachedOrElse(Guardians.DATA, null) == s.data && s.data.guardianClass() == s.guardianClass
            && Guardians.runtimeIfPresent(p).orElse(null) == s.runtime
            && WeaponLoadout.enabled(p) == s.loadoutEnabled
            && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
            && WeaponPerks.selected(s.stack, RelentlessStrikesProfile.ID).filter(s.roll::equals).isPresent();
    }
    /** Tick/lifecycle writer. Ordinary stow retains counters and in-flight source authority. */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        thread(p);

        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> {
            if (s.owner != p || valid(p, s)) return false;
            s.cycle.clear(); return true;
        });
        for (var s : sessions.values()) {
            if (s.owner != p) continue;
            s.cycle.update(now(p)); s.observed = now(p);
        }
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    /** Call ONLY after a paid, nonempty sword contact is accepted. Never from queries or input.
     * Abilities, glaives, empty swords and generic enemy deaths must never capture this token. */
    public static Token capture(ServerPlayer p) {
        if (p == null) return Token.NONE;
        update(p);
        if (!ownerValid(p) || !WeaponLoadout.canUse(p) || now(p) < 0) return Token.NONE;
        var stack = p.getMainHandItem();
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, RelentlessStrikesProfile.ID).orElse(null);
        int slot = p.getInventory().getSelectedSlot();
        if (slot < 0 || slot >= 9 || p.getInventory().getItem(slot) != stack || !owned(p, stack)
            || !RelentlessStrikesProfile.supports(entry) || roll == null || !RelentlessStrikesProfile.rolls().contains(roll)
            || !entry.id().equals(roll.id())) return Token.NONE;

        var sessions = SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new IdentityHashMap<>());
        // Only an accepted capture can bind a successor owner object. Delayed callbacks cannot.
        sessions.values().removeIf(previous -> {
            if (previous.owner == p) return false;
            previous.cycle.clear(); return true;
        });
        var s = sessions.computeIfAbsent(stack, ignored -> new Session(p, stack, entry, roll));
        var contact = s.cycle.capture(now(p));
        return contact == null ? Token.NONE : new Token(s, contact);
    }
    /** Only AFTER eligible target positive actual HP/absorption loss, never nominal damage.
     * Returns ammunition actually generated, not merely the theoretical threshold reward. */
    public static int confirmed(ServerPlayer p, Token token, LivingEntity target, double actualLoss) {
        if (p == null || token == null || token.source == null || token.source.owner != p || target == null
            || !Double.isFinite(actualLoss) || actualLoss <= 0) return 0;
        update(p);
        var s = token.source;
        if (!valid(p, s) || target == p || target.level() != s.level) return 0;
        return generate(p, s, s.cycle.confirmed(now(p), token.contact, target, actualLoss));
    }
    /** Reward execution is private and reachable only from a newly accepted confirmed event. */
    private static int generate(ServerPlayer p, Session s, int reward) {
        if (reward <= 0) return 0;
        var ammo = WeaponItems.magazine(s.stack, WeaponProfile.forEntry(s.entry));
        int generated = ammo.generateLoaded(reward);
        if (generated > 0) {
            WeaponItems.save(s.stack, ammo);
            p.getInventory().setChanged(); p.containerMenu.broadcastChanges();
        }
        return generated;
    }
    /** Pure held-source diagnostic; cannot accept contact, reset counter or grant ammo. */
    public static int progress(ServerPlayer p) {
        if (p == null) return 0;
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(p.getMainHandItem());
        return s != null && valid(p, s) && WeaponLoadout.canUse(p) ? s.cycle.progress(now(p)) : 0;
    }
    /** Explicit edit/removal boundary, including edit-away-and-back in the same server tick.
     * Do not call for normal stow.  */
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && s.owner == p) { s.cycle.clear(); sessions.remove(stack); }
        if (sessions != null && sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    public static void edited(ItemStack stack) {
        if (stack == null) return;
        var it = SESSIONS.values().iterator();
        while (it.hasNext()) {
            var sessions = it.next();
            var s = sessions.remove(stack);
            if (s != null) s.cycle.clear();
            if (sessions.isEmpty()) it.remove();
        }
    }
    /** Actual death/disconnect/world/class/runtime/loadout/Super lifecycle boundary, never stow. */
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        thread(p);

        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> {
            if (s.owner != p) return false;
            s.cycle.clear(); return true;
        });
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    public static void clear() {
        for (var sessions : SESSIONS.values()) for (var s : sessions.values()) s.cycle.clear();
        SESSIONS.clear();
    }
}
