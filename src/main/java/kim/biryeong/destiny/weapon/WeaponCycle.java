package kim.biryeong.destiny.weapon;

/** Active-weapon tick state, fractional cadence, item-owned ammo. Cancellation preserves its cooldown. */
public final class WeaponCycle {
    private static final double EPSILON = 1e-7;
    private double readyAt;
    private long reloadAt = -1;
    private long reloadAmmoAt = -1;
    private int reloadDuration;
    private int reloadPhaseDuration, reloadBatch;
    private boolean reloadShell;
    private long chargeAt = -1;
    private double burstAt, burstSpacing;
    private int burstLeft, burstIndex;
    private boolean sharedBurstAmmo;

    public boolean ready(long tick) { return tick + EPSILON >= readyAt && reloadAt < 0 && burstLeft == 0; }
    /** Only the firing deadline crosses an item rebind; reload/charge/burst never do. */
    public double firingDeadline() { return readyAt; }
    public void restoreFiringDeadline(double deadline) {
        if (!Double.isFinite(deadline) || deadline < 0 || reloading() || charging() || bursting())
            throw new IllegalArgumentException("Cannot restore an unsafe or active cycle");
        readyAt = deadline;
    }
    public boolean startCharge(long tick) {
        if (!ready(tick) || chargeAt >= 0) return false;
        chargeAt = tick;
        return true;
    }
    public boolean charged(long tick, int duration) { return chargeAt >= 0 && tick - chargeAt >= duration; }
    /** -1 means no active draw; nock/reload time cannot count toward a later draw. */
    public long chargeElapsed(long tick) { return chargeAt < 0 ? -1 : Math.max(0,tick-chargeAt); }
    public boolean charging() { return chargeAt >= 0; }
    public void cancelCharge() { chargeAt = -1; }
    public boolean fire(long tick, WeaponProfile p, WeaponMagazine magazine) {
        return fire(tick,p,magazine,1);
    }
    /** W51 heavy melee charges its entire cost atomically; ranged behavior stays cost1. */
    public boolean fire(long tick, WeaponProfile p, WeaponMagazine magazine, int cost) {
        if (cost < 1 || cost > 16 || cost != 1 && (p.mode() != WeaponProfile.Mode.MELEE || p.burst() != 1)
                || !ready(tick) || !magazine.consume(cost)) return false;
        chargeAt = -1;
        // Carry sub-tick remainder only from an on-time call, not from idle time or a lag catch-up.
        // At most one trigger starts in a tick. A duplicate packet cannot exploit fractional cadence.
        double anchor = tick - readyAt >= 0 && tick - readyAt < 1 - EPSILON ? readyAt : tick;
        readyAt = anchor + p.cadenceTicks();
        sharedBurstAmmo = p.sharedBurstAmmo();
        burstLeft = sharedBurstAmmo ? p.burst() - 1 : Math.min(p.burst() - 1, magazine.rounds());
        burstIndex = 0;
        burstSpacing = p.burstSpacingTicks();
        burstAt = tick + burstSpacing;
        return true;
    }
    /** Empty-sword weak swing, not a free ranged trigger; retains the shared owner cooldown. */
    public boolean emptyMelee(long tick, WeaponProfile p) {
        if (p.mode() != WeaponProfile.Mode.MELEE || p.burst() != 1 || !ready(tick)) return false;
        chargeAt = -1;
        double anchor = tick-readyAt >= 0 && tick-readyAt < 1-EPSILON ? readyAt : tick;
        readyAt = anchor+p.cadenceTicks();
        return true;
    }
    /** Caller drains due bolts in a bounded loop: a sub-tick interval can place two bolts in one tick. */
    public boolean burst(long tick, WeaponMagazine magazine) {
        if (burstLeft == 0 || tick + EPSILON < burstAt) return false;
        burstAt += burstSpacing;
        burstLeft--;
        if (!sharedBurstAmmo && !magazine.consume()) { burstLeft = 0; return false; }
        burstIndex++;
        return true;
    }
    public int burstIndex() { return burstIndex; }
    public boolean bursting() { return burstLeft > 0; }
    public boolean startReload(long tick, WeaponProfile p, WeaponMagazine magazine) {
        return startReload(tick,p,magazine,new WeaponReloadPolicy.Plan(p.firstReloadTicks(),p.reloadTicks(),p.roundsPerInsert()));
    }
    /** Captured effective timings, with original granularity/cost. No live mutation of an active cycle. */
    public boolean startReload(long tick, WeaponProfile p, WeaponMagazine magazine, WeaponReloadPolicy.Plan plan) {
        return startReload(tick,p,magazine,plan,plan.firstTicks());
    }
    /** Whole-magazine credit can precede recovery. Shell insert phases remain atomic. */
    public boolean startReload(long tick, WeaponProfile p, WeaponMagazine magazine,
                               WeaponReloadPolicy.Plan plan, int ammoTicks) {
        if (plan.incremental()!=p.shellReload() || plan.roundsPerInsert()!=p.roundsPerInsert())
            throw new IllegalArgumentException("Reload modifiers may not change ammunition granularity");
        if(ammoTicks<1 || ammoTicks>plan.firstTicks() || plan.incremental()&&ammoTicks!=plan.firstTicks())
            throw new IllegalArgumentException("Unsafe ammunition credit deadline");
        if (reloadAt >= 0 || burstLeft > 0 || !magazine.canReload()) return false;
        chargeAt = -1;
        reloadShell = p.shellReload();
        reloadDuration = plan.intervalTicks();
        reloadBatch = plan.roundsPerInsert();
        reloadPhaseDuration = plan.firstTicks();
        reloadAt = tick + reloadPhaseDuration;
        reloadAmmoAt = tick + ammoTicks;
        return true;
    }
    /** Intrinsic transaction owns its ammunition credit. A full magazine may enter this
     * recovery, but finishReload must never also perform the ordinary magazine refill. */
    public boolean startExternalReload(long tick, int ticks) {
        if (tick < 0 || ticks < 1 || ticks > 1200 || tick > Long.MAX_VALUE - ticks)
            throw new IllegalArgumentException("Unsafe intrinsic reload deadline");
        if (reloadAt >= 0 || burstLeft > 0) return false;
        chargeAt = -1;
        reloadShell = false;
        reloadDuration = reloadPhaseDuration = ticks;
        reloadBatch = 0;
        reloadAt = tick + ticks;
        reloadAmmoAt = -1;
        return true;
    }
    /** Each insert is one atomic real transfer, including a two-cartridge insert or final odd round. */
    public boolean finishReload(long tick, WeaponMagazine magazine) {
        if (reloadAt < 0) return false;
        if(!reloadShell) {
            int transferred=0;
            if(reloadAmmoAt>=0 && tick>=reloadAmmoAt) {
                transferred=magazine.reload();
                // Even a no-op transfer is consumed: later pickups cannot be credited again.
                reloadAmmoAt=-1;
            }
            if(tick>=reloadAt)reloadAt=-1;
            return transferred>0;
        }
        if(tick<reloadAt)return false;
        int transferred = magazine.reloadRounds(reloadBatch);
        reloadPhaseDuration = reloadDuration;
        reloadAt = reloadShell && magazine.canReload() ? tick + reloadDuration : -1;
        reloadAmmoAt=reloadAt;
        return transferred > 0;
    }
    /** A new press may interrupt a shell reload after at least one shell; never creates ammunition. */
    public boolean interruptReloadForShot(long tick, WeaponMagazine magazine) {
        if (!reloadShell || reloadAt < 0 || magazine.rounds() == 0 || tick + EPSILON < readyAt) return false;
        reloadAt = -1;
        reloadAmmoAt = -1;
        return true;
    }
    public boolean reloading() { return reloadAt >= 0; }
    public long reloadRemaining(long tick) { return Math.max(0, reloadAt - tick); }
    /** Actual current phase duration, not the full magazine estimate or an invented initial delay. */
    public int reloadPhaseTicks() { return reloading() ? reloadPhaseDuration : 0; }
    public void cancelPending() { reloadAt = -1; reloadAmmoAt = -1; chargeAt = -1; burstLeft = 0; }
}
