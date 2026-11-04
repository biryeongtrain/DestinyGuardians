package kim.biryeong.destiny.weapon;

/** Partial draw foundation: early release fires a weaker/slower/more curved arrow.
 * The interpolation is authored Minecraft tuning, NOT an extracted Destiny damage/velocity curve.
 * Full draw retains the original profile exactly. Perfect-draw/overdraw perks are not simulated.
 */
public final class WeaponBowDraw {
    private WeaponBowDraw() {}

    public static WeaponProfile shot(WeaponProfile base,long drawTicks) {
        if(base.mode()!=WeaponProfile.Mode.PROJECTILE||base.chargeTicks()<1||drawTicks<0)
            throw new IllegalArgumentException("A released drawn projectile is required");
        if(drawTicks>=base.chargeTicks())return base;
        double progress=drawTicks/(double)base.chargeTicks();
        return new WeaponProfile(base.mode(),(float)(base.damage()*(.35+.65*progress)),
                base.intervalTicks(),base.magazine(),base.reserve(),base.reloadTicks(),base.range(),
                base.chargeTicks(),base.burst(),base.pellets(),base.spread(),
                base.speed()*(.25+.75*progress),base.gravity()*(3-2*progress),base.blastRadius(),
                base.automatic(),base.infiniteReserve(),base.cadenceTicks(),base.burstSpacingTicks(),
                base.sharedBurstAmmo(),base.shellReload(),base.firstReloadTicks(),base.roundsPerInsert());
    }
}
