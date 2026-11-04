package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Main-thread accepted events on original count-one canonical sources; pure token queries. */
public final class WeaponOpeningShot {
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
        final boolean loadoutEnabled;
        final OpeningShotCycle cycle = new OpeningShotCycle();
        long observed, stowedAt = -1;
        Session(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry, WeaponPerks.Roll roll, int slot) {
            owner = p; level = p.level(); this.stack = stack; this.entry = entry; this.roll = roll;
            this.slot = slot; loadoutEnabled = WeaponLoadout.enabled(p);
            data = p.getAttachedOrElse(Guardians.DATA, null);
            runtime = Guardians.runtimeIfPresent(p).orElseThrow();
            guardianClass = data.guardianClass(); observed = now(p);
        }
    }
    public static final class Token {
        public static final Token NONE = new Token(null, null);
        private final Session source;
        private final OpeningShotCycle.Emission emission;
        private Token(Session source, OpeningShotCycle.Emission emission) {
            this.source = source; this.emission = emission;
        }
    }
    private WeaponOpeningShot() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("OpeningShot is main server thread owned");
    }
    private static boolean ownerValid(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        var runtime = Guardians.runtimeIfPresent(p).orElse(null);
        return data != null && data.guardianClass() != null && data.guardianClass() != GuardianClass.NONE
            && runtime != null && runtime.superSession == null;
    }
    private static int equippedSlot(ServerPlayer p, ItemStack stack) {
        if (stack == null || stack.isEmpty() || stack.getCount() != 1) return -1;
        if (WeaponLoadout.enabled(p) && WeaponLoadout.equipped(p).stream().noneMatch(e -> e.stack() == stack)) return -1;
        for (int i = 0; i < 9; i++) if (p.getInventory().getItem(i) == stack) return i;
        return -1;
    }
    private static boolean held(ServerPlayer p, Session s) {
        // Selection hook runs before vanilla changes slots. Never resurrect the outgoing buff
        // from that transient observation, including a same-tick away/back transaction.
        return s.stowedAt != now(p) && p.getMainHandItem() == s.stack
            && p.getInventory().getSelectedSlot() == s.slot && WeaponLoadout.canUse(p);
    }
    private static boolean valid(ServerPlayer p, Session s) {
        if (!ownerValid(p)) return false;
        var sessions = SESSIONS.get(p.getUUID());
        return sessions != null && sessions.get(s.stack) == s && s.owner == p && s.level == p.level()
            && now(p) >= s.observed && equippedSlot(p, s.stack) == s.slot
            && WeaponLoadout.enabled(p) == s.loadoutEnabled
            && p.getAttachedOrElse(Guardians.DATA, null) == s.data && s.data.guardianClass() == s.guardianClass
            && Guardians.runtimeIfPresent(p).orElse(null) == s.runtime
            && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
            && WeaponPerks.selected(s.stack, OpeningShotProfile.ID).filter(s.roll::equals).isPresent();
    }
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
    /** Writer at an accepted event boundary, never called by passive queries. */
    private static Session bindHeld(ServerPlayer p) {
        if (p == null) return null;
        update(p);
        if (!ownerValid(p) || !WeaponLoadout.canUse(p) || now(p) < 0) return null;
        var stack = p.getMainHandItem();
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, OpeningShotProfile.ID).orElse(null);
        int slot = equippedSlot(p, stack);
        if (slot < 0 || p.getInventory().getSelectedSlot() != slot
            || !OpeningShotProfile.supports(entry) || roll == null || !OpeningShotProfile.rolls().contains(roll)
            || !entry.id().equals(roll.id())) return null;
        var sessions = SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new IdentityHashMap<>());
        sessions.values().removeIf(old -> {
            if (old.owner == p) return false;
            old.cycle.clear(); return true;
        });
        var s = sessions.get(stack);
        if (s == null || !valid(p, s)) {
            if (s != null) s.cycle.clear();
            s = new Session(p, stack, entry, roll, slot);
            sessions.put(stack, s);
        }
        return held(p, s) ? s : null;
    }
    /** AFTER each actual payment, BEFORE trace; firstOfBurst is false for all supplementals. */
    public static Token capture(ServerPlayer p, WeaponCatalog.Entry entry, boolean firstOfBurst) {
        if (p == null || entry == null || WeaponItems.entry(p.getMainHandItem()).filter(entry::equals).isEmpty())
            return Token.NONE;
        var s = bindHeld(p);
        if (s == null) return Token.NONE;
        var emission = s.cycle.capture(now(p), firstOfBurst);
        return emission == null ? Token.NONE : new Token(s, emission);
    }
    private static boolean boosted(ServerPlayer p, Token t) {
        return p != null && t != null && t.source != null && valid(p, t.source)
            && t.source.cycle.boosted(now(p), t.emission);
    }
    /** Master adds this to raw Range before the single existing stat clamp. */
    public static int rangeBonus(ServerPlayer p, Token t) {
        return boosted(p, t) ? OpeningShotProfile.rangeBonus(t.source.entry) : 0;
    }
    public static double accuracyScalar(ServerPlayer p, Token t) {
        return boosted(p, t) ? OpeningShotProfile.accuracyScalar(t.source.entry) : 1;
    }
    public static double growthScalar(ServerPlayer p, Token t) {
        return boosted(p, t) ? OpeningShotProfile.growthScalar(t.source.entry) : 1;
    }
    /** Sourced metadata only: server port does not simulate Aim Assist/magnetism. */
    public static int aimAssistBonus(ServerPlayer p, Token t) {
        return boosted(p, t) ? OpeningShotProfile.aimAssistBonus(t.source.entry) : 0;
    }
    public static void stowing(ServerPlayer p, ItemStack outgoing) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(outgoing);
        if (s == null || !valid(p, s)) return;
        s.cycle.stowing(now(p)); s.observed = s.stowedAt = now(p);
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
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && s.owner == p) { s.cycle.clear(); sessions.remove(stack); }
        if (sessions != null && sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
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
