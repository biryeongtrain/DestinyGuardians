package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Actual held-weapon session. Emitted damage keeps its snapshot; kill rewards never follow a new gun. */
public final class WeaponKillClip {
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final KillClipCycle cycle = new KillClipCycle();
        Session(ServerPlayer p) { owner = p; level = p.level(); stack = p.getMainHandItem(); }
    }
    public static final class Token {
        public static final Token NONE = new Token(null, 1);
        private final Session session;
        private final float multiplier;
        private Token(Session session, float multiplier) { this.session = session; this.multiplier = multiplier; }
        public float multiplier() { return multiplier; }
    }
    private WeaponKillClip() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean eligible(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && !AbilityService.inSuper(p) && WeaponLoadout.canUse(p)
                && WeaponPerks.selected(p.getMainHandItem(), KillClipProfile.ID).isPresent();
    }
    public static void update(ServerPlayer p) {
        if (!eligible(p)) { cleanup(p); return; }
        var s = SESSIONS.get(p.getUUID());
        if (s == null || s.owner != p || s.level != p.level() || s.stack != p.getMainHandItem())
            SESSIONS.put(p.getUUID(), new Session(p));
    }
    public static void selecting(ServerPlayer p, int slot) {
        if (slot >= 0 && slot < 9 && slot != p.getInventory().getSelectedSlot()) cleanup(p);
    }
    /** Damage-time reads and HUD do not create sessions or advance the cycle. */
    public static int remaining(ServerPlayer p) {
        var s = SESSIONS.get(p.getUUID());
        return eligible(p) && s != null && s.owner == p && s.level == p.level() && s.stack == p.getMainHandItem()
                ? s.cycle.remaining(now(p), KillClipProfile.perk().durationTicks()) : 0;
    }
    public static Token capture(ServerPlayer p) {
        update(p); var s = SESSIONS.get(p.getUUID());
        return s == null || s.owner != p ? Token.NONE : new Token(s, remaining(p) > 0 ? KillClipProfile.perk().multiplier() : 1);
    }
    /** Called only after an actual weapon-damage transaction confirmed this final blow. */
    public static void killed(ServerPlayer p, Token token) {
        var s = token.session;
        if (s != null && s.owner == p && SESSIONS.get(p.getUUID()) == s && eligible(p)
                && s.level == p.level() && s.stack == p.getMainHandItem()) s.cycle.killed(now(p));
    }
    /** Manual/automatic real reload, or Marksman Dodge. Holster fill is deliberately not this event. */
    public static void reloaded(ServerPlayer p, ItemStack stack) {
        update(p); var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p && s.stack == stack)
            s.cycle.reloaded(now(p), KillClipProfile.perk().killWindowTicks(), KillClipProfile.perk().durationTicks());
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p && s.stack == stack) cleanup(p);
    }
    public static void cleanup(ServerPlayer p) {
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) SESSIONS.remove(p.getUUID());
    }
    public static void clear() { SESSIONS.clear(); }
}
