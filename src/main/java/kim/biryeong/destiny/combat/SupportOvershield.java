package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.titan.TitanExpandedSupers;
import kim.biryeong.destiny.ability.warlock.WarlockExpandedSupers;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;

import java.util.IdentityHashMap;
import java.util.Map;

/** A single rechargeable support shield pool. Well is an explicit custom gameplay extension.
 * DDC Ward: 45 HP cap, 15 HP/s, base Void overshield lifetime 10s after refresh.
 * This owns absorption only; it does not implement the separate Void-shield PvE resistance perk.
 */
public final class SupportOvershield {
    private static final Identifier CAPACITY = DestinyGuardians.id("support_overshield");
    private static final Map<ServerPlayer, State> STATES = new IdentityHashMap<>();
    private static final int LINGER_TICKS = 200;
    private static final class State {
        final ServerLevel level;
        long lastTick = Long.MIN_VALUE, refreshed;
        float owned, observed, capacity;
        State(ServerPlayer p) { level = p.level(); observed = p.getAbsorptionAmount(); }
    }
    private SupportOvershield() { }

    /** One call per player tick, before the health HUD. Same-tick duplicate calls never recharge twice. */
    public static void tick(ServerPlayer p) {
        State s = STATES.get(p);
        if (!p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()
                || s != null && s.level != p.level()) { cleanup(p); return; }
        boolean inside = TitanExpandedSupers.inWard(p) || WarlockExpandedSupers.inWell(p);
        if (s == null) {
            if (!inside) return;
            s = new State(p); STATES.put(p, s);
        }
        long now = p.level().getGameTime();
        if (s.lastTick == now) return;
        s.lastTick = now;
        reconcile(p, s);
        if (!inside && now - s.refreshed >= LINGER_TICKS) { cleanup(p); return; }
        // Match the existing 230 Destiny HP -> max MC health conversion used by CrucibleHealth.
        float cap = p.getMaxHealth() * 45f / 230f;
        var attr = p.getAttribute(Attributes.MAX_ABSORPTION);
        if (attr == null) { cleanup(p); return; }
        if (s.capacity != cap || !attr.hasModifier(CAPACITY)) {
            if (s.owned > cap) {
                p.setAbsorptionAmount(Math.max(0, p.getAbsorptionAmount() - (s.owned - cap)));
                s.owned = cap;
            }
            attr.removeModifier(CAPACITY);
            attr.addTransientModifier(new AttributeModifier(CAPACITY, cap, AttributeModifier.Operation.ADD_VALUE));
            s.capacity = cap;
        }
        if (inside) {
            s.refreshed = now;
            float before = p.getAbsorptionAmount();
            float charge = Math.min(Math.max(0, cap - s.owned), p.getMaxHealth() * 15f / 230f / 20f);
            p.setAbsorptionAmount(before + charge);
            s.owned += Math.max(0, p.getAbsorptionAmount() - before);
        }
        s.observed = p.getAbsorptionAmount();
    }

    private static void reconcile(ServerPlayer p, State s) {
        // Account for actual damage/reset since the last tick; do not remove unrelated absorption.
        s.owned = Math.max(0, s.owned - Math.max(0, s.observed - p.getAbsorptionAmount()));
        s.observed = p.getAbsorptionAmount();
    }

    public static void cleanup(ServerPlayer p) {
        State s = STATES.remove(p);
        if (s == null) return;
        reconcile(p, s);
        p.setAbsorptionAmount(Math.max(0, p.getAbsorptionAmount() - s.owned));
        var attr = p.getAttribute(Attributes.MAX_ABSORPTION);
        if (attr != null) attr.removeModifier(CAPACITY);
    }
}
