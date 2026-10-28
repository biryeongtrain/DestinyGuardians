package kim.biryeong.destiny.ability.warlock;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.fx.ClassAbilityEffects;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Finite airborne budget; cancellation never toggles flying or noGravity. */
public final class WarlockJump extends Ability {
    private static final Map<ServerPlayer, Glide> ACTIVE = new IdentityHashMap<>();
    private static final class Glide {
        final WarlockAbilities.Lease lease; final WarlockJump ability; final int limit;
        int spent; boolean active = true;
        Glide(WarlockAbilities.Lease lease, WarlockJump ability) {
            this.lease = lease; this.ability = ability;
            limit = WarlockAbilities.ticks(ability, "duration_ticks", 60, 1, 100);
        }
    }
    public WarlockJump(Identifier id) { super(id, GuardianClass.WARLOCK, AbilitySlot.JUMP, Element.KINETIC, 0, "활공"); }
    /** Jump must remain callable at any point in its airborne budget, including cancellation. */
    @Override public boolean activate(ServerPlayer player) {
        Glide old = ACTIVE.get(player);
        if (old != null && old.active && old.lease.valid()) { old.active = false; return true; }
        var lease = WarlockAbilities.acquire(player, this);
        if (lease == null || !airborne(player) || old != null || lease.runtime.airJumpsUsed > 0) return false;
        lease.runtime.airJumpsUsed++;
        ACTIVE.put(player, new Glide(lease, this));
        ClassAbilityEffects.sound(player, Element.KINETIC, "jump");
        return true;
    }
    private static boolean airborne(ServerPlayer p) {
        return !p.onGround() && !p.getAbilities().flying && !p.isNoGravity() && !p.isInWater()
                && !p.isPassenger() && !p.onClimbable() && !p.isFallFlying();
    }
    static void tick() {
        for (Glide g : List.copyOf(ACTIVE.values())) {
            ServerPlayer p = g.lease.owner;
            if (!g.lease.valid() || p.onGround()) { ACTIVE.remove(p); continue; }
            if (!g.active) continue; // Keep spent air budget until landing; no repeated hover resets.
            if (!airborne(p) || g.spent++ >= g.limit) { g.active = false; continue; }
            Vec3 v = p.getDeltaMovement();
            double fall = WarlockAbilities.value(g.ability, "descent_speed", .12, .06, .5);
            // Carry an existing ascent; never synthesize an upward hover impulse.
            if (v.y < -fall) Motion.setVelocity(p, new Vec3(v.x, -fall, v.z));
            p.resetFallDistance();
        }
    }
    static void cleanup(ServerPlayer p) { ACTIVE.remove(p); }
    public static boolean active(ServerPlayer p) { Glide g = ACTIVE.get(p); return g != null && g.active && g.lease.valid(); }
}
