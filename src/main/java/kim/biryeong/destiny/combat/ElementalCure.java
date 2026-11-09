package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.crucible.CrucibleRuntime;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import java.util.IdentityHashMap;
import java.util.Map;

/** Shared Cure: DDC Solar row6, 60 PvE/30 PvP HP per stack over .1s, 1s cooldown.
 * Explicit MC conversion: max health /230, matching CrucibleHealth and SupportOvershield.
 * Two equal pulses separated by two server ticks implement the .1s restoration, bounded by missing health.
 */
public final class ElementalCure {
    private record State(ServerLevel level, CurePulse pulse) {}
    private static final Map<ServerPlayer, State> STATES = new IdentityHashMap<>();
    private ElementalCure() {}
    public static boolean apply(ServerPlayer p, int stacks) {
        if (!usable(p) || stacks <= 0) return false;
        long now = p.level().getGameTime();
        State state = STATES.get(p);
        if (state == null || state.level != p.level()) state = new State(p.level(), new CurePulse());
        float half = p.getMaxHealth() / 230f * (CrucibleRuntime.participating(p) ? 30 : 60) * stacks / 2f;
        if (!state.pulse.accept(now, half)) return false;
        p.heal(half); STATES.put(p, state);
        return true;
    }
    private static boolean usable(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected();
    }
    public static void tick(ServerPlayer p) {
        State s = STATES.get(p);
        if (s == null) return;
        long now = p.level().getGameTime();
        if (!usable(p) || s.level != p.level() || s.pulse.expired(now)) { cleanup(p); return; }
        float pulse = s.pulse.pulse(now);
        if (pulse > 0) p.heal(pulse);
    }
    public static void cleanup(ServerPlayer p) { STATES.remove(p); }
    public static void clear() { STATES.clear(); }
}
