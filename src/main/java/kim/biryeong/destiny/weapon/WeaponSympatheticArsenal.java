package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Main-thread paid final blows on original sources. No attachments or shared runtime writes. */
public final class WeaponSympatheticArsenal {
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
        final SympatheticArsenalCycle cycle = new SympatheticArsenalCycle();
        long observed, stowedAt = -1;
        Session(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry, WeaponPerks.Roll roll, int slot) {
            owner = p; level = p.level(); this.stack = stack; this.entry = entry; this.roll = roll;
            this.slot = slot; loadoutEnabled = WeaponLoadout.enabled(p);
            data = p.getAttachedOrElse(Guardians.DATA, null);
            runtime = Guardians.runtimeIfPresent(p).orElseThrow();
            guardianClass = data.guardianClass(); observed = now(p);
        }
    }
    public static final class PaidToken {
        public static final PaidToken NONE = new PaidToken(null, null);
        private final Session source;
        private final SympatheticArsenalCycle.PaidToken emission;
        private PaidToken(Session source, SympatheticArsenalCycle.PaidToken emission) {
            this.source = source; this.emission = emission;
        }
    }
    private WeaponSympatheticArsenal() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("SympatheticArsenal is main server thread owned");
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
            && WeaponPerks.selected(s.stack, SympatheticArsenalProfile.ID).filter(s.roll::equals).isPresent();
    }
    /** Writer only. Stow/expiry clears live benefits without revoking paid snapshots. */
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
            s.cycle.update(now(p), held(p, s)); s.observed = now(p);
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
        var roll = WeaponPerks.selected(stack, SympatheticArsenalProfile.ID).orElse(null);
        int slot = equippedSlot(p, stack);
        if (slot < 0 || p.getInventory().getSelectedSlot() != slot
            || !SympatheticArsenalProfile.supports(entry) || roll == null || !SympatheticArsenalProfile.rolls().contains(roll)
            || !entry.id().equals(roll.id())) return null;
        var sessions = SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new IdentityHashMap<>());
        var s = sessions.get(stack);
        if (s == null || !valid(p, s)) {
            if (s != null) s.cycle.clear();
            s = new Session(p, stack, entry, roll, slot);
            sessions.put(stack, s);
        }
        return held(p, s) ? s : null;
    }
    private static Session active(ServerPlayer p) {
        if (p == null) return null;
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(p.getMainHandItem());
        return s != null && valid(p, s) && held(p, s) ? s : null;
    }

    /** Accepted WeaponCycle reload authority, distinct from a paid damage emission. */
    public static final class ReloadToken {
        public static final ReloadToken NONE = new ReloadToken(null, null);
        private final Session source;
        private final SympatheticArsenalCycle.Reload reload;
        private ReloadToken(Session source, SympatheticArsenalCycle.Reload reload) {
            this.source = source; this.reload = reload;
        }
    }
    public static PaidToken capture(ServerPlayer p) {
        var s = bindHeld(p);
        if (s == null) return PaidToken.NONE;
        var paid = s.cycle.capture(now(p));
        return paid == null ? PaidToken.NONE : new PaidToken(s, paid);
    }
    /** AFTER positive actual loss AND attributable eligible enemy final blow. */
    public static void killed(ServerPlayer p, PaidToken token, LivingEntity target) {
        if (p == null || token == null || token.source == null || token.source.owner != p || target == null) return;
        update(p);
        var s = token.source;
        if (valid(p, s) && target != p && target.level() == s.level && !target.isAlive())
            s.cycle.killed(now(p), token.emission, target, held(p, s));
    }
    /** AFTER successful WeaponCycle.startReload, before credit. No kill-window test here. */
    public static ReloadToken acceptedReload(ServerPlayer p) {
        if (p == null || !WeaponRuntime.reloadOwnedBy(p, p.getMainHandItem())) return ReloadToken.NONE;
        var s = bindHeld(p);
        if (s == null) return ReloadToken.NONE;
        var reload = s.cycle.acceptedReload(now(p));
        return reload == null ? ReloadToken.NONE : new ReloadToken(s, reload);
    }
    /** First genuine positive ammo-credit boundary, even if recovery continues.
     * On true master calls refillStowedArsenal(p) once; no ammunition writes or nested procs here.
     * Instant ability reloads have no acceptedReload token. Zero-credit callbacks cannot trigger. */
    public static boolean reloaded(ServerPlayer p, ReloadToken token, int creditedRounds) {
        if (p == null || token == null || token.source == null || creditedRounds <= 0) return false;
        thread(p);
        var s = token.source;
        return valid(p, s) && held(p, s) && s.cycle.reloaded(now(p), token.reload, creditedRounds);
    }
    public static void reloadCancelled(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && s.owner == p) s.cycle.reloadCancelled();
    }
    /** PURE outermost accepted reload snapshot; sum raw colegal bonuses, clamp/round once.
     * Existing accepted reloads retain their plan. Same-socket alternatives never contribute. */
    public static WeaponReloadPolicy.Plan plan(ServerPlayer p, WeaponCatalog.Entry entry, WeaponReloadPolicy.Plan base) {
        if (p == null || base == null || base.incremental() || !ownerValid(p)
            || !WeaponLoadout.canUse(p) || WeaponRuntime.reloadOwnedBy(p, p.getMainHandItem())) return base;
        var stack = p.getMainHandItem();
        int slot = equippedSlot(p, stack);
        var selected = WeaponPerks.selected(stack, SympatheticArsenalProfile.ID).orElse(null);
        if (slot < 0 || p.getInventory().getSelectedSlot() != slot
            || !SympatheticArsenalProfile.supports(entry)
            || WeaponItems.entry(stack).filter(entry::equals).isEmpty()
            || selected == null || !SympatheticArsenalProfile.rolls().contains(selected)) return base;
        int bonus = SympatheticArsenalProfile.reloadBonus();
        double scalar = 1;
        for (String id : SympatheticArsenalProfile.reloadCompanions()) {
            if (WeaponPerks.selected(stack, id)
                    .filter(r -> SympatheticArsenalProfile.compatible(entry, id, r)).isEmpty()) continue;
            int tier = switch (id) {
                case "feeding_frenzy" -> WeaponFeedingFrenzy.stacks(p);
                case "rapid_hit" -> WeaponRapidHit.stacks(p);
                case "threat_detector" -> WeaponThreatDetector.stacks(p);
                case "surplus" -> WeaponSurplus.stacks(p);
                default -> throw new IllegalStateException("Unreviewed SA reload companion " + id);
            };
            bonus += SympatheticArsenalProfile.companionBonus(id, tier);
            scalar *= SympatheticArsenalProfile.companionScalar(id, tier);
        }
        return SympatheticArsenalProfile.reloadPlan(entry, bonus, scalar, base);
    }
    /** Accepted outgoing selection, before vanilla changes slots. Retain original paid tokens. */
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
