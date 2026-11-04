package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Accepted melee -> confirmed actual HP/absorption loss. No generic kill/grenade/super callbacks.
 * LOCAL owner-wide cooldown survives source edits and stow, including zero-transfer activations.
 * All entry points are server-thread owned; master supplies actual damage/powered/final-blow facts.
 */
public final class WeaponGraveRobber {
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final GuardianRuntime runtime;
        final GuardianData data;
        final GuardianClass guardianClass;
        final GraveRobberCycle cycle = new GraveRobberCycle();
        final IdentityHashMap<ItemStack, Source> sources = new IdentityHashMap<>();
        Session(ServerPlayer p) {
            owner = p; level = p.level(); runtime = Guardians.runtime(p);
            data = Guardians.data(p); guardianClass = data.guardianClass();
        }
    }
    /** Source object identity is the selection epoch; removed sources are never reattached. */
    private record Source(Session session, ItemStack stack, WeaponCatalog.Entry entry, WeaponPerks.Roll roll) {}
    public static final class Token {
        public static final Token NONE = new Token(null, -1);
        private final Source source;
        private final long acceptedAt;
        private final Set<UUID> contacts = new HashSet<>();
        private Token(Source source, long acceptedAt) { this.source = source; this.acceptedAt = acceptedAt; }
    }
    private WeaponGraveRobber() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && Guardians.isGuardian(p) && !AbilityService.inSuper(p);
    }
    private static boolean lifecycleValid(ServerPlayer p, Session s) {
        return s.owner == p && s.level == p.level() && p.isAlive() && !p.isRemoved()
                && !p.hasDisconnected() && Guardians.isGuardian(p) && s.runtime == Guardians.runtime(p)
                && s.data == Guardians.data(p) && s.guardianClass == s.data.guardianClass();
    }
    private static boolean possessed(ServerPlayer p, ItemStack stack) {
        for (int i = 0; i < p.getInventory().getContainerSize(); i++)
            if (p.getInventory().getItem(i) == stack) return true;
        return false;
    }
    private static boolean currentSource(ServerPlayer p, Source source) {
        return ownerValid(p) && WeaponLoadout.canUse(p) && p.getMainHandItem() == source.stack
                && possessed(p, source.stack)
                && (!WeaponLoadout.enabled(p) || WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == source.stack))
                && WeaponItems.entry(source.stack).filter(source.entry::equals).isPresent()
                && GraveRobberProfile.supports(source.entry) && GraveRobberProfile.rolls().contains(source.roll)
                && source.entry.id().equals(source.roll.id())
                && WeaponPerks.selected(source.stack, GraveRobberProfile.ID).filter(source.roll::equals).isPresent();
    }
    private static boolean valid(ServerPlayer p, Source source) {
        if (p == null || source == null) return false;
        var s = source.session;
        return SESSIONS.get(p.getUUID()) == s && lifecycleValid(p, s)
                && s.sources.get(source.stack) == source && currentSource(p, source);
    }
    /** Observed stow, invalid owner, edits, removal and time regression revoke captured sources.
     * Temporary super/spectator/stow cannot reset the owner's already-paid cooldown.
     */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        var s = SESSIONS.get(p.getUUID());
        if (s == null || s.owner != p) return;
        if (!lifecycleValid(p, s)) { SESSIONS.remove(p.getUUID()); return; }
        if (!s.cycle.update(now(p))) { s.sources.clear(); return; }
        s.sources.values().removeIf(source -> !currentSource(p, source));
    }
    /** Capture the ORIGINAL held eligible selected exact socket at accepted melee cast. */
    public static Token accepted(ServerPlayer p) {
        update(p);
        if (!ownerValid(p) || !WeaponLoadout.canUse(p)) return Token.NONE;
        var stack = p.getMainHandItem();
        var entry = WeaponItems.entry(stack).filter(GraveRobberProfile::supports);
        var roll = WeaponPerks.selected(stack, GraveRobberProfile.ID);
        if (entry.isEmpty() || roll.isEmpty() || !GraveRobberProfile.rolls().contains(roll.get())
                || !entry.get().id().equals(roll.get().id()) || !possessed(p, stack)) return Token.NONE;
        var s = SESSIONS.get(p.getUUID());
        if (s == null || !lifecycleValid(p, s)) { s = new Session(p); SESSIONS.put(p.getUUID(), s); }
        long tick = now(p);
        if (!s.cycle.update(tick)) return Token.NONE;
        var source = s.sources.get(stack);
        if (source == null) {
            source = new Source(s, stack, entry.get(), roll.get());
            if (!currentSource(p, source)) return Token.NONE;
            s.sources.put(stack, source);
        }
        return new Token(source, tick);
    }
    /** Master calls only AFTER positive actual HP/absorption loss from this accepted melee.
     * Powered nonlethal hits qualify; unpowered melee must have killed a now-dead target.
     * Duplicate target contacts (including those denied by cooldown) never retry on this token.
     * No-transfer valid procs spend 60 ticks locally; pinned source does not prove that policy.
     * @return actual rounds moved from the existing reserve/legacy-overflow economy
     */
    public static int confirmed(ServerPlayer p, Token token, LivingEntity target, boolean powered, boolean killed) {
        if (p == null || token == null || target == null || token.source == null) return 0;
        update(p);
        if (!valid(p, token.source) || target == p || target.level() != p.level()
                || now(p) < token.acceptedAt || !token.contacts.add(target.getUUID())) return 0;
        if (!powered && (!killed || target.isAlive())) return 0;
        var source = token.source;
        if (!source.session.cycle.confirmed(now(p), powered, killed)) return 0;
        var ammo = WeaponItems.magazine(source.stack, WeaponProfile.forEntry(source.entry));
        int moved = ammo.reload();
        if (moved > 0) {
            // Generic original-stack cancellation preserves cadence and never calls reload perks/audio.
            WeaponRuntime.cancelForTraitRefill(p, source.stack);
            WeaponItems.save(source.stack, ammo);
            p.getInventory().setChanged(); p.containerMenu.broadcastChanges(); CombatHud.update(p);
        }
        return moved;
    }
    /** Every real selection edit, including away/back in one tick, must revoke its source epoch. */
    public static void edited(ItemStack stack) {
        if (stack != null) for (var s : SESSIONS.values()) s.sources.remove(stack);
    }
    /** Edit/drop/loadout removal/stow may revoke tokens, but never the owner-wide cooldown. */
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) s.sources.remove(stack);
    }
    /** True lifecycle cleanup resets both captured sources and the owner-wide cooldown. */
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) SESSIONS.remove(p.getUUID());
    }
    public static void clear() { SESSIONS.clear(); }
}
