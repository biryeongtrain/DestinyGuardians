package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Main-thread accepted events on original count-one canonical sources; pure token queries. */
public final class WeaponBoxBreathing {
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
        final BoxBreathingCycle cycle = new BoxBreathingCycle();
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
        private final BoxBreathingCycle.Emission emission;
        private Token(Session source, BoxBreathingCycle.Emission emission) {
            this.source = source; this.emission = emission;
        }
    }
    private WeaponBoxBreathing() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("BoxBreathing is main server thread owned");
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
            && WeaponPerks.selected(s.stack, BoxBreathingProfile.ID).filter(s.roll::equals).isPresent();
    }
    /** Read-only HUD/debug observation of an already earned live ADS cycle.
     * Never binds, prunes, updates or creates a source, and never consumes a paid emission. */
    public static boolean ready(ServerPlayer p) {
        if (p == null) return false;
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(p.getMainHandItem());
        return s != null && valid(p, s) && held(p, s)
            && WeaponAiming.aimInput(p) && !WeaponHandling.blocked(p) && !WeaponRuntime.reloading(p)
            && WeaponItems.magazine(s.stack, WeaponProfile.forEntry(s.entry)).rounds() > 0
            && s.cycle.ready(now(p));
    }
    public static void update(ServerPlayer p, boolean actualAds) {
        if (p == null) return;
        thread(p);
        prune(p);
        var s = bindHeld(p);
        if (s == null) return;
        // Master supplies validated input after its FOV/handling ownership tick.
        boolean ads = actualAds && !WeaponHandling.blocked(p) && !WeaponRuntime.reloading(p);
        s.cycle.update(now(p), ads, WeaponItems.magazine(s.stack, WeaponProfile.forEntry(s.entry)).rounds() > 0);
        s.observed = now(p);
    }
    private static void prune(ServerPlayer p) {
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> {
            if (s.owner != p || valid(p, s) && held(p, s)) return false;
            s.cycle.clear(); return true;
        });
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    /** Writer at an accepted event boundary, never called by passive queries. */
    private static Session bindHeld(ServerPlayer p) {
        if (p == null) return null;
        prune(p);
        if (!ownerValid(p) || !WeaponLoadout.canUse(p) || now(p) < 0) return null;
        var stack = p.getMainHandItem();
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, BoxBreathingProfile.ID).orElse(null);
        int slot = equippedSlot(p, stack);
        if (slot < 0 || p.getInventory().getSelectedSlot() != slot
            || !BoxBreathingProfile.supports(entry) || roll == null || !BoxBreathingProfile.rolls().contains(roll)
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
    /** AFTER actual ammo payment, before trace. Do not call update here: last round is valid.
     * Master assigns NONE to supplemental emissions and every perkSplash (including Dragonfly). */
    public static Token capture(ServerPlayer p, WeaponCatalog.Entry entry, int roundsBefore, boolean actualAds) {
        if (p == null || entry == null || roundsBefore <= 0
            || WeaponItems.entry(p.getMainHandItem()).filter(entry::equals).isEmpty()) return Token.NONE;
        var s = bindHeld(p);
        if (s == null) return Token.NONE;
        boolean ads = actualAds && !WeaponHandling.blocked(p) && !WeaponRuntime.reloading(p);
        var emission = s.cycle.capture(now(p), roundsBefore, ads);
        s.observed = now(p);
        return emission == null ? Token.NONE : new Token(s, emission);
    }
    /** Pure paid weakspot snapshot; master applies only on precision hits, never body/splash. */
    public static float precisionMultiplier(ServerPlayer p, Token t) {
        return p != null && t != null && t.source != null && valid(p, t.source)
            && t.source.cycle.boosted(now(p), t.emission) ? BoxBreathingProfile.perk().precisionMultiplier() : 1f;
    }
    /** Sourced metadata only: no AA simulation in this server port. */
    public static double aimAssistFalloffScalar(ServerPlayer p, Token t) {
        return precisionMultiplier(p, t) > 1 ? BoxBreathingProfile.perk().aimAssistFalloffScalar() : 1;
    }
    public static void released(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s == null || !valid(p, s)) return;
        s.cycle.released(now(p)); s.observed = now(p);
    }
    public static void stowing(ServerPlayer p, ItemStack stack) {
        released(p, stack);
        if (p == null) return;
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && s.owner == p) s.stowedAt = now(p);
    }
    /** Accepted reload or aim suspension; called before input can resume. */
    public static void suspend(ServerPlayer p, ItemStack stack) { released(p, stack); }
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
