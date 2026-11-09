package kim.biryeong.destiny.weapon;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** W327 base-trait clocks. One instance per genuine equipped weapon, never serialized or shared. */
final class PerkExpansionCombatCycle {
    static final int RECONSTRUCTION_TICKS = 120, REWIND_EXCLUSION_TICKS = 20;
    static final int MAX_FLIGHT_TICKS = 600;
    private static final double[] PRECISION = {1, 1.0417, 1.0834, 1.125, 1.167, 1.2083, 1.25};
    private final Set<Emission> pending = Collections.newSetFromMap(new IdentityHashMap<>());
    private long generation, burst, precisionBurst = -1, precisionUntil, warmUntil, desperateUntil;
    private long reconstructionAt, rewindIgnoreUntil;
    private int fired, hits, precisionStacks, precisionHalf, desperateStacks;

    PerkExpansionCombatCycle(long now) { reconstructionAt = now + RECONSTRUCTION_TICKS; }

    static final class Emission {
        final long generation, burst, accepted;
        final boolean precisionEligible;
        boolean hit, resolved;
        Emission(long generation, long burst, long accepted, boolean precisionEligible) {
            this.generation = generation; this.burst = burst; this.accepted = accepted;
            this.precisionEligible = precisionEligible;
        }
    }

    Emission paid(long now, boolean spentAmmo, boolean firstOfBurst, boolean precisionEligible) {
        if (firstOfBurst) burst++;
        if (spentAmmo) fired = Math.min(1_000_000, fired + 1);
        reconstructionAt = now + RECONSTRUCTION_TICKS;
        var shot = new Emission(generation, burst, now, precisionEligible);
        pending.add(shot);
        return shot;
    }

    /** Each emitted bullet/bolt counts at most once, irrespective of pellets, pierces or splash targets. */
    boolean hit(Emission shot, long now, boolean adaptiveLfr, boolean heavyBurst, boolean charged) {
        if (!current(shot, now) || shot.hit) return false;
        shot.hit = true;
        if (shot.generation == generation && now >= rewindIgnoreUntil) hits = Math.min(1_000_000, hits + 1);
        if (shot.precisionEligible) {
            if (now >= precisionUntil) { precisionStacks = 0; precisionHalf = 0; }
            if (!heavyBurst || precisionBurst != shot.burst) {
                if (!adaptiveLfr || ++precisionHalf >= 2) {
                    precisionHalf = 0;
                    precisionStacks = Math.min(6, precisionStacks + 1);
                }
                precisionBurst = shot.burst;
            }
            precisionUntil = now + (charged ? 42 : 22);
        }
        return true;
    }

    boolean resolved(Emission shot, long now) {
        if (!current(shot, now)) return false;
        shot.resolved = true;
        pending.remove(shot);
        if (!shot.hit && shot.precisionEligible) { precisionStacks = 0; precisionHalf = 0; precisionUntil = 0; }
        return true;
    }

    private boolean current(Emission shot, long now) {
        return shot != null && !shot.resolved && pending.contains(shot)
                && now >= shot.accepted && now - shot.accepted <= MAX_FLIGHT_TICKS;
    }

    /** Bounded defensive retirement if the caller loses a projectile terminal callback. Late hits stay inert. */
    void expire(long now) {
        pending.removeIf(shot -> {
            if (now >= shot.accepted && now - shot.accepted <= MAX_FLIGHT_TICKS) return false;
            shot.resolved = true;
            if (!shot.hit && shot.precisionEligible) { precisionStacks = 0; precisionHalf = 0; precisionUntil = 0; }
            return true;
        });
    }

    double precisionMultiplier(long now) { return PRECISION[precisionStacks(now)]; }
    int precisionStacks(long now) { return now < precisionUntil ? precisionStacks : 0; }
    int precisionRemaining(long now) { return remaining(precisionUntil, now); }
    private boolean magazinePending() { return pending.stream().anyMatch(shot -> shot.generation == generation); }
    boolean awaitingRewind(int capacity) { return magazinePending() && fired >= (int)Math.ceil(capacity * .285); }

    /** Consume one empty-magazine accounting window, only after its last projectile has resolved. */
    int rewind(long now, int capacity, int loaded, boolean adaptiveLfr) {
        expire(now);
        if (loaded != 0 || magazinePending() || fired < (int)Math.ceil(capacity * .285) || hits == 0) return 0;
        int amount = Math.min(capacity, (int)Math.ceil(hits * (adaptiveLfr ? .14 : .60)));
        resetMagazine();
        rewindIgnoreUntil = now + REWIND_EXCLUSION_TICKS;
        return amount;
    }

    /** A real manual/dodge reload starts another magazine; old projectiles cannot earn into it. */
    void resetMagazine() {
        generation++; fired = 0; hits = 0;
        // In-flight rounds still earn Precision Instrument, but cannot enter the new magazine's Rewind count.
    }

    int reconstruction(long now, int capacity, int loaded, boolean reloading) {
        if (now < reconstructionAt || reloading) return 0;
        // No catch-up burst after a pause. Exactly one reserve transaction per observed six-second deadline.
        reconstructionAt = now + RECONSTRUCTION_TICKS;
        return reconstructionTarget(capacity, loaded);
    }
    static int reconstructionTarget(int capacity, int loaded) {
        long maximum = Math.min(Integer.MAX_VALUE, (long)capacity * 2);
        return (int)Math.max(loaded, Math.min(maximum, loaded + (long)Math.ceil(capacity * .25)));
    }
    static int fund(WeaponMagazine ammo, int capacity, int target) {
        return target <= ammo.rounds() ? 0 : target <= capacity
                ? ammo.reloadRounds(target - ammo.rounds()) : ammo.reloadOverflow(target);
    }

    void weaponKill(long now, boolean warm, boolean desperate) {
        if (warm) warmUntil = now + Math.min(400, warmUntil > now ? warmUntil - now + 80 : 120);
        if (desperate) {
            desperateStacks = Math.max(desperateStacks(now), 1);
            desperateUntil = now + 140;
        }
    }
    void abilityKill(long now) {
        desperateStacks = desperateStacks(now) >= 2 ? 3 : 2;
        desperateUntil = now + 140;
    }
    int desperateStacks(long now) { return now < desperateUntil ? desperateStacks : 0; }
    int desperateRemaining(long now) { return remaining(desperateUntil, now); }
    double damageMultiplier(long now) { return 1 + .1 * desperateStacks(now); }
    int warmRemaining(long now) { return remaining(warmUntil, now); }
    int chargeTicks(long now, int base) { return base <= 0 || warmUntil <= now ? base : Math.max(1, (int)Math.ceil(base * .625)); }
    void stow() { warmUntil = 0; }
    private static int remaining(long until, long now) { return (int)Math.clamp(until - now, 0, Integer.MAX_VALUE); }
}
