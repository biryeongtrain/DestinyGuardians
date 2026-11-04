package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Main-thread paid weapon final blows. No generic kill listener, attachments, HUD writes,
 * handling or reload. Original owned equipped sources survive ordinary stow.
 */
public final class WeaponAmbitiousAssassin {
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
        final AmbitiousAssassinCycle cycle = new AmbitiousAssassinCycle();
        long observed;
        Session(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry, WeaponPerks.Roll roll) {
            owner = p; level = p.level(); this.stack = stack; this.entry = entry; this.roll = roll;
            data = p.getAttachedOrElse(Guardians.DATA, null);
            runtime = Guardians.runtimeIfPresent(p).orElseThrow();
            guardianClass = data.guardianClass(); observed = now(p);
        }
    }
    public static final class Token {
        public static final Token NONE = new Token(null, null);
        private final Session source;
        private final AmbitiousAssassinCycle.Emission emission;
        private Token(Session source, AmbitiousAssassinCycle.Emission emission) {
            this.source = source; this.emission = emission;
        }
    }
    private WeaponAmbitiousAssassin() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("Ambitious Assassin is main server thread owned");
    }
    private static boolean ownerValid(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        var runtime = Guardians.runtimeIfPresent(p).orElse(null);
        return data != null && data.guardianClass() != null && data.guardianClass() != GuardianClass.NONE
            && runtime != null && runtime.superSession == null;
    }
    private static boolean owned(ServerPlayer p, ItemStack stack) {
        if (stack == null || stack.isEmpty()) return false;
        if (WeaponLoadout.enabled(p) && WeaponLoadout.equipped(p).stream().noneMatch(e -> e.stack() == stack)) return false;
        for (int i = 0; i < p.getInventory().getContainerSize(); i++)
            if (p.getInventory().getItem(i) == stack) return true;
        return false;
    }
    private static boolean held(ServerPlayer p, Session s) {
        int slot = p.getInventory().getSelectedSlot();
        return slot >= 0 && slot < 9 && p.getMainHandItem() == s.stack
            && p.getInventory().getItem(slot) == s.stack && WeaponLoadout.canUse(p);
    }
    private static boolean valid(ServerPlayer p, Session s) {
        if (!ownerValid(p)) return false;
        var sessions = SESSIONS.get(p.getUUID());
        return sessions != null && sessions.get(s.stack) == s && s.owner == p && s.level == p.level()
            && now(p) >= s.observed && owned(p, s.stack)
            && p.getAttachedOrElse(Guardians.DATA, null) == s.data && s.data.guardianClass() == s.guardianClass
            && Guardians.runtimeIfPresent(p).orElse(null) == s.runtime
            && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
            && WeaponPerks.selected(s.stack, AmbitiousAssassinProfile.ID).filter(s.roll::equals).isPresent();
    }
    /** Tick/lifecycle writer. Stow and natural expiry do not invalidate an in-flight paid source. */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> {
            // A delayed callback from a replaced player object cannot revoke its successor.
            if (s.owner != p || valid(p, s)) return false;
            s.cycle.clear();
            return true;
        });
        for (var s : sessions.values()) {
            if (s.owner != p) continue;
            s.cycle.update(now(p)); s.observed = now(p);
        }
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    /** Caller captures only after the cartridge was paid. Denied input/queries must not call this. */
    public static Token capture(ServerPlayer p) {
        if (p == null) return Token.NONE;
        update(p);
        if (!ownerValid(p) || !WeaponLoadout.canUse(p) || now(p) < 0) return Token.NONE;
        var stack = p.getMainHandItem();
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, AmbitiousAssassinProfile.ID).orElse(null);
        int slot = p.getInventory().getSelectedSlot();
        if (slot < 0 || slot >= 9 || p.getInventory().getItem(slot) != stack || !owned(p, stack)
            || !AmbitiousAssassinProfile.supports(entry) || roll == null || !AmbitiousAssassinProfile.rolls().contains(roll)
            || !entry.id().equals(roll.id())) return Token.NONE;
        var s = SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new IdentityHashMap<>())
            .computeIfAbsent(stack, ignored -> new Session(p, stack, entry, roll));
        var emission = s.cycle.capture(now(p));
        return emission == null ? Token.NONE : new Token(s, emission);
    }
    /** AFTER positive actual HP/absorption loss AND an attributable final blow on an eligible
     * enemy. Share the same token across direct/payload contacts.
     */
    public static void killed(ServerPlayer p, Token token, LivingEntity target) {
        if (p == null || token == null || token.source == null || token.source.owner != p || target == null) return;
        update(p);
        var s = token.source;
        if (valid(p, s) && target != p && target.level() == s.level && !target.isAlive())
            s.cycle.killed(now(p), token.emission, target);
    }
    private static Session active(ServerPlayer p) {
        if (p == null) return null;
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(p.getMainHandItem());
        return s != null && valid(p, s) && held(p, s) ? s : null;
    }
    public static final class ReloadToken {
        public static final ReloadToken NONE = new ReloadToken(null,null);
        private final Session source;
        private final AmbitiousAssassinCycle.Reload reload;
        private ReloadToken(Session s, AmbitiousAssassinCycle.Reload r) { source=s; reload=r; }
    }
    /** Only after WeaponCycle accepts a real timed reload. Cancellation never calls target. */
    public static ReloadToken acceptedReload(ServerPlayer p) {
        var token=capture(p);
        if (token.source==null) return ReloadToken.NONE;
        return new ReloadToken(token.source,token.source.cycle.acceptedReload(now(p)));
    }
    /** One-time target at real ammo credit; caller funds the additional rounds from reserves. */
    public static int target(ServerPlayer p, ReloadToken token) {
        if (p==null || token==null || token.source==null || token.source.owner!=p) return 0;
        update(p);
        var s=token.source;
        if (!valid(p,s) || !held(p,s)) return 0;
        int kills=s.cycle.finish(now(p),token.reload);
        return AmbitiousAssassinProfile.target(s.entry,kills);
    }
    public static int kills(ServerPlayer p) { var s=active(p); return s==null?0:s.cycle.kills(now(p)); }
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
