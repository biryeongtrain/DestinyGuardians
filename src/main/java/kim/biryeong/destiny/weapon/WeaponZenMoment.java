package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Main-thread paid source tokens. A confirmed hit may affect only its original held session.
 * No HUD row, stability, accuracy, actual shot recoil, ammo mutation or persistent counter.
 * capture is a trusted integration boundary: only the successful paid emission hook may call it. */
public final class WeaponZenMoment {
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    /** Pure identity boundary used by the actual session and standalone ownership tests. */
    record Identity(Object owner, Object world, Object stack, Object data, Object runtime,
                    Object guardianClass, boolean loadout, int selectedSlot) {
        boolean same(Identity other) {
            return other != null && owner == other.owner && world == other.world && stack == other.stack
                    && data == other.data && runtime == other.runtime && guardianClass == other.guardianClass
                    && loadout == other.loadout && selectedSlot == other.selectedSlot;
        }
    }
    static final class Lease {
        private final Identity identity;
        private long observed;
        private boolean revoked;
        Lease(Identity identity, long tick) { this.identity = identity; observed = tick; }
        boolean valid(Identity current, long tick) {
            return !revoked && tick >= 0 && tick >= observed && identity.same(current);
        }
        void observe(long tick) { observed = tick; }
        void revoke() { revoked = true; }
    }
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final WeaponCatalog.Entry entry;
        final WeaponPerks.Roll roll;
        final Lease lease;
        final ZenMomentCycle cycle = new ZenMomentCycle();
        Session(ServerPlayer p, WeaponCatalog.Entry entry, WeaponPerks.Roll roll) {
            owner = p; level = p.level(); stack = p.getMainHandItem(); this.entry = entry; this.roll = roll;
            lease = new Lease(identity(p), now(p));
        }
    }
    public static final class Token {
        public static final Token NONE = new Token(null);
        private final Session source;
        private Token(Session source) { this.source = source; }
    }
    private WeaponZenMoment() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static Identity identity(ServerPlayer p) {
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        return new Identity(p, p.level(), p.getMainHandItem(), data,
                Guardians.runtimeIfPresent(p).orElse(null), data == null ? null : data.guardianClass(),
                WeaponLoadout.enabled(p), p.getInventory().getSelectedSlot());
    }
    private static boolean ownerValid(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && Guardians.runtimeIfPresent(p).map(r -> r.superSession == null).orElse(true)
                && WeaponLoadout.canUse(p);
    }
    private static boolean held(ServerPlayer p, ItemStack stack) {
        int slot = p.getInventory().getSelectedSlot();
        return stack != null && stack.getCount() == 1 && slot >= 0 && slot < 9
                && p.getMainHandItem() == stack && p.getInventory().getItem(slot) == stack;
    }
    private static boolean valid(ServerPlayer p, Session s) {
        return s != null && s.owner == p && ownerValid(p) && SESSIONS.get(p.getUUID()) == s
                && s.level == p.level() && held(p, s.stack) && s.lease.valid(identity(p), now(p))
                && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
                && WeaponPerks.selected(s.stack, ZenMomentProfile.ID).filter(s.roll::equals).isPresent();
    }
    public static void update(ServerPlayer p) {
        if (p == null) return;
        var s = SESSIONS.get(p.getUUID());
        if (s == null) return;
        if (!valid(p, s)) { s.lease.revoke(); SESSIONS.remove(p.getUUID(), s); }
        else s.lease.observe(now(p));
    }
    /** Returns NONE for unsupported/preview/invalid source. Never starts or refreshes the buff. */
    public static Token capture(ServerPlayer p) {
        update(p);
        if (!ownerValid(p) || !held(p, p.getMainHandItem())) return Token.NONE;
        var entry = WeaponItems.entry(p.getMainHandItem()).orElse(null);
        var roll = WeaponPerks.selected(p.getMainHandItem(), ZenMomentProfile.ID).orElse(null);
        if (!ZenMomentProfile.supports(entry) || roll == null || !ZenMomentProfile.rolls().contains(roll)
                || !entry.id().equals(roll.id())) return Token.NONE;
        var s = SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new Session(p, entry, roll));
        return new Token(s);
    }
    /** Real accepted direct weapon transactions only. No positive credit from miss, immune, blocked,
     * ability or secondary perk splash hooks. Each actual transaction may credit a hit, including
     * a lethal hit: do not test target liveness after its damage has already been applied.
     * No per-target dedup: successive paid bullets against the same enemy are separate real hits. */
    public static void confirmed(ServerPlayer p, Token token, LivingEntity target, float actualPositiveDamage) {
        if (p == null || token == null || token.source == null || target == null
                || !Float.isFinite(actualPositiveDamage) || actualPositiveDamage <= 0) return;
        update(p); var s = token.source;
        if (valid(p, s) && target != p && target.level() == s.level
                && !(target instanceof Player) && !(target instanceof ArmorStand)
                && (target instanceof Enemy || target instanceof Mob) && !p.isAlliedTo(target)
                && !(target instanceof TamableAnimal tame && tame.isTame()))
            s.cycle.confirmed(now(p), ZenMomentProfile.hitUnits(s.entry), actualPositiveDamage);
    }
    private static Session active(ServerPlayer p) {
        if (p == null) return null;
        var s = SESSIONS.get(p.getUUID()); return valid(p, s) ? s : null;
    }
    /** Read-only diagnostics; half-stack units preserve 1.5-stack hit weights. */
    public static int stackUnits(ServerPlayer p) { var s = active(p); return s == null ? 0 : s.cycle.stackUnits(now(p)); }
    public static float stacks(ServerPlayer p) { return stackUnits(p) / 2f; }
    public static int remaining(ServerPlayer p) { var s = active(p); return s == null ? 0 : s.cycle.remaining(now(p)); }
    public static float flinchScalar(ServerPlayer p) { var s = active(p); return s == null ? 1f : s.cycle.flinchScalar(now(p)); }
    /** Exact successful edit revokes old tokens, even same-tick clear/reselect on the same object. */
    public static void edited(ItemStack stack) {
        SESSIONS.values().removeIf(s -> { if (s.stack != stack) return false; s.lease.revoke(); return true; });
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p && s.stack == stack) { s.lease.revoke(); SESSIONS.remove(p.getUUID(), s); }
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) { s.lease.revoke(); SESSIONS.remove(p.getUUID(), s); }
    }
    public static void clear() { SESSIONS.values().forEach(s -> s.lease.revoke()); SESSIONS.clear(); }
}
