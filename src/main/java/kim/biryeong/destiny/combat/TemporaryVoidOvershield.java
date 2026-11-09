package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import java.util.IdentityHashMap;
import java.util.Map;

/** Independently owned non-recharging Void shield. DDC Void row8:45HP,70% combatant DR.
 * Repulsor Brace overrides duration to160ticks. MC normalization is maxHealth/230.
 * Shared vanilla absorption cannot identify foreign removals; conservatively charge observed
 * loss to our layer first. This preserves foreign absorption on expiry, with local own-first
 * ordering rather than claiming DDC's global FIFO ordering across unrelated shield providers.
 */
public final class TemporaryVoidOvershield {
    private static final Identifier ID = DestinyGuardians.id("temporary_void_overshield");
    private static final Map<ServerPlayer, State> STATES = new IdentityHashMap<>();
    private static final class State {
        final ServerLevel level;
        long expires;
        final VoidOvershieldPool pool;
        State(ServerPlayer p) { level = p.level(); pool = new VoidOvershieldPool(p.getAbsorptionAmount()); }
    }
    private TemporaryVoidOvershield() {}
    private static void reconcile(ServerPlayer p, State s) {
        s.pool.observe(p.getAbsorptionAmount());
    }
    public static void grant(ServerPlayer p, int ticks) {
        if (p == null || !p.isAlive() || p.isRemoved() || ticks <= 0) return;
        tick(p);
        var attribute = p.getAttribute(Attributes.MAX_ABSORPTION);
        if (attribute == null) return;
        State s = STATES.computeIfAbsent(p, ignored -> new State(p));
        reconcile(p, s);
        float cap = p.getMaxHealth() * 45f / 230f;
        attribute.removeModifier(ID);
        attribute.addTransientModifier(new AttributeModifier(ID, cap, AttributeModifier.Operation.ADD_VALUE));
        float before = p.getAbsorptionAmount();
        p.setAbsorptionAmount(before + Math.max(0, cap - s.pool.owned()));
        s.pool.granted(before, p.getAbsorptionAmount()); s.expires = p.level().getGameTime() + ticks;
    }
    /** Call on final incoming damage AFTER armor and other mitigation, BEFORE absorption consumes it.
     * combatant means actual hostile PvE entity source, not player/environment. Health and foreign
     * shield remainder receive full damage; this is never a blanket player resistance multiplier. */
    public static float incoming(ServerPlayer p, float amount, boolean combatant) {
        State s = STATES.get(p);
        if (!combatant || s == null || s.level != p.level() || p.level().getGameTime() >= s.expires) return amount;
        reconcile(p, s);
        return VoidOvershieldPool.resisted(amount, s.pool.owned());
    }
    /** Pure HUD query: no reconciliation, grant, cleanup or deadline change. */
    public static int remaining(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return 0;
        State s = STATES.get(p);
        if (s == null || s.level != p.level() || s.pool.ownedAt(p.getAbsorptionAmount()) <= 0) return 0;
        return (int)Math.clamp(s.expires - p.level().getGameTime(), 0, Integer.MAX_VALUE);
    }
    public static void tick(ServerPlayer p) {
        State s = STATES.get(p);
        if (s == null) return;
        if (s.level != p.level() || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()
                || p.level().getGameTime() >= s.expires) { cleanup(p); return; }
        reconcile(p, s);
    }
    public static void cleanup(ServerPlayer p) {
        State s = STATES.remove(p);
        if (s == null) return;
        reconcile(p, s);
        p.setAbsorptionAmount(Math.max(0, s.pool.withoutOwned(p.getAbsorptionAmount())));
        var attribute = p.getAttribute(Attributes.MAX_ABSORPTION);
        if (attribute != null) attribute.removeModifier(ID);
    }
    public static void clear() { for (var p : java.util.List.copyOf(STATES.keySet())) cleanup(p); }
}
