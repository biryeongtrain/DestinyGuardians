package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.boss.wither.WitherBoss;
import net.minecraft.world.entity.boss.enderdragon.EnderDragon;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Original count-one canonical source authority; main-thread events only, pure queries. */
public final class WeaponUnrelenting {
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
        final UnrelentingCycle cycle = new UnrelentingCycle();
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
        private final UnrelentingCycle.Emission emission;
        private Token(Session source, UnrelentingCycle.Emission emission) {
            this.source = source; this.emission = emission;
        }
    }
    private WeaponUnrelenting() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("Unrelenting is main server thread owned");
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
        int occurrences = 0, slot = -1;
        for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
            if (p.getInventory().getItem(i) == stack) { occurrences++; slot = i; }
        }
        if (occurrences != 1 || slot < 0 || slot >= 9) return -1;
        return !WeaponLoadout.enabled(p) || WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == stack)
            ? slot : -1;
    }
    private static boolean held(ServerPlayer p, Session s) {
        // Selection hook runs before vanilla changes slots. Never resurrect the outgoing buff
        // from that transient observation, including a same-tick away/back transaction.
        return s.stowedAt != now(p) && p.getMainHandItem() == s.stack
            && p.getInventory().getSelectedSlot() == equippedSlot(p, s.stack) && WeaponLoadout.canUse(p);
    }
    private static boolean valid(ServerPlayer p, Session s) {
        if (!ownerValid(p)) return false;
        var sessions = SESSIONS.get(p.getUUID());
        return sessions != null && sessions.get(s.stack) == s && s.owner == p && s.level == p.level()
            && now(p) >= s.observed && equippedSlot(p, s.stack) >= 0
            && WeaponLoadout.enabled(p) == s.loadoutEnabled
            && p.getAttachedOrElse(Guardians.DATA, null) == s.data && s.data.guardianClass() == s.guardianClass
            && Guardians.runtimeIfPresent(p).orElse(null) == s.runtime
            && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
            && WeaponPerks.selected(s.stack, UnrelentingProfile.ID).filter(s.roll::equals).isPresent();
    }
    /** Lifecycle/tick writer. Passive reads never call this method. */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> {
            if (s.owner != p || valid(p, s)) return false;
            s.cycle.clear(); return true;
        });
        float heal = 0;
        for (var s : sessions.values()) {
            if (s.owner != p) continue;
            heal = Math.max(heal, s.cycle.regeneration(now(p), p.getHealth(), p.getMaxHealth()));
            s.observed = now(p);
        }
        // Multiple original sources never stack periodic rates or write another healing system.
        if (heal > 0) p.heal(heal);
        if (p.getHealth() >= p.getMaxHealth())
            for (var s : sessions.values()) if (s.owner == p) s.cycle.full();
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    /** Writer at an accepted event boundary, never called by passive queries. */
    private static Session bindHeld(ServerPlayer p) {
        if (p == null) return null;
        update(p);
        if (!ownerValid(p) || !WeaponLoadout.canUse(p) || now(p) < 0) return null;
        var stack = p.getMainHandItem();
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, UnrelentingProfile.ID).orElse(null);
        int slot = equippedSlot(p, stack);
        if (slot < 0 || p.getInventory().getSelectedSlot() != slot
            || !UnrelentingProfile.supports(entry) || roll == null || !UnrelentingProfile.rolls().contains(roll)
            || !entry.id().equals(roll.id())) return null;
        var sessions = SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new IdentityHashMap<>());
        sessions.values().removeIf(previous -> {
            if (previous.owner == p) return false;
            previous.cycle.clear(); return true;
        });
        var s = sessions.get(stack);
        if (s == null || !valid(p, s)) {
            if (s != null) s.cycle.clear();
            s = new Session(p, stack, entry, roll, slot);
            sessions.put(stack, s);
        }
        return held(p, s) ? s : null;
    }
    /** AFTER paid ranged/projectile/nonempty sword acceptance, BEFORE own damage. Share across splash. */
    public static Token capture(ServerPlayer p) {
        var s = bindHeld(p);
        if (s == null) return Token.NONE;
        var emission = s.cycle.capture(now(p));
        return emission == null ? Token.NONE : new Token(s, emission);
    }
    /** ONLY after positive actual HP/absorption loss and an attributable eligible enemy final blow. */
    public static void killed(ServerPlayer p, Token token, LivingEntity target) {
        if (p == null || token == null || token.source == null || token.source.owner != p || target == null) return;
        update(p);
        var s = token.source;
        if (valid(p, s) && target != p && target.level() == s.level && !target.isAlive()
            && !target.isSpectator()) {
            var rank = rank(target);
            if (rank != null && s.cycle.killed(now(p), token.emission, target, rank)) {
                p.heal(p.getMaxHealth() * UnrelentingProfile.healFraction());
                if (p.getHealth() >= p.getMaxHealth()) s.cycle.full();
            }
        }
    }
    /** Explicit local rank mapping, consistent with the existing tagged Vorpal policy. */
    private static UnrelentingCycle.Rank rank(LivingEntity target) {
        if (target instanceof Player) return UnrelentingCycle.Rank.GUARDIAN;
        if (target instanceof WitherBoss || target instanceof EnderDragon
            || target instanceof Mob && (target.entityTags().contains("destiny_boss")
                || target.entityTags().contains("destiny_vehicle")))
            return UnrelentingCycle.Rank.POWERFUL;
        return target instanceof Mob ? UnrelentingCycle.Rank.RANK_AND_FILE : null;
    }
    /** Pure own-regeneration HUD observer, across original still-owned stowed sources. */
    public static boolean active(ServerPlayer p) {
        if (p == null || !(p.getHealth() > 0) || !(p.getHealth() < p.getMaxHealth())) return false;
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return false;
        for (var s : sessions.values()) if (valid(p, s) && s.cycle.active(now(p))) return true;
        return false;
    }
    /** Only positive actual HP/absorption loss interrupts; denial and zero damage do not. */
    public static void damaged(ServerPlayer p, float actualLoss) {
        if (p == null || !Float.isFinite(actualLoss) || actualLoss <= 0) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions != null) for (var s : sessions.values()) if (s.owner == p) s.cycle.damaged(actualLoss);
    }
    /** Retains regen and paid authority; blocks transient outgoing captures before vanilla selection. */
    public static void stowing(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && valid(p, s)) s.stowedAt = now(p);
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
