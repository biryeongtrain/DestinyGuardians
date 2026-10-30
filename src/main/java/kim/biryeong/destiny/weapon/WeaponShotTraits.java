package kim.biryeong.destiny.weapon;

import net.minecraft.server.level.ServerPlayer;

/** One accepted paid emission. Used by trace, precision damage and post-shot recoil together. */
final class WeaponShotTraits {
    record Snapshot(WeaponOpeningShot.Token opening, WeaponBoxBreathing.Token breathing,
                    WeaponDynamicSway.Token sway, WeaponHeadseeker.Token headseeker, WeaponSteadyHands.Token steadyHands,
                    WeaponCharacteristics.Damage damage, WeaponGutshot.Token gutshot) {}
    static final Snapshot NONE = new Snapshot(WeaponOpeningShot.Token.NONE,
            WeaponBoxBreathing.Token.NONE,WeaponDynamicSway.Token.NONE,WeaponHeadseeker.Token.NONE,WeaponSteadyHands.Token.NONE,WeaponCharacteristics.Damage.KINETIC,WeaponGutshot.Token.NONE);
    private WeaponShotTraits() {}
    static Snapshot paid(ServerPlayer p, WeaponCatalog.Entry entry, int roundsBefore, boolean firstOfBurst) {
        return new Snapshot(WeaponOpeningShot.capture(p,entry,firstOfBurst),
                firstOfBurst?WeaponBoxBreathing.capture(p,entry,roundsBefore,WeaponAiming.aimInput(p)):WeaponBoxBreathing.Token.NONE,
                WeaponDynamicSway.paid(p,entry),WeaponHeadseeker.capture(p),WeaponSteadyHands.capture(p),WeaponOsmosis.damage(p,p.getMainHandItem(),entry),WeaponGutshot.capture(p,entry));
    }
    static Snapshot damageOnly(Snapshot source) {
        return new Snapshot(WeaponOpeningShot.Token.NONE,WeaponBoxBreathing.Token.NONE,WeaponDynamicSway.Token.NONE,
                WeaponHeadseeker.Token.NONE,WeaponSteadyHands.Token.NONE,source.damage(),WeaponGutshot.Token.NONE);
    }
    static kim.biryeong.destiny.guardian.Element element(Snapshot source) {
        return switch(source.damage()) {
            case ARC -> kim.biryeong.destiny.guardian.Element.ARC;
            case SOLAR -> kim.biryeong.destiny.guardian.Element.SOLAR;
            case VOID -> kim.biryeong.destiny.guardian.Element.VOID;
            // Stasis/Strand keywords and combat rules are still absent from the guardian substrate.
            default -> kim.biryeong.destiny.guardian.Element.KINETIC;
        };
    }
    static int range(ServerPlayer p,Snapshot s) { return WeaponOpeningShot.rangeBonus(p,s.opening()); }
    static int stability(ServerPlayer p,Snapshot s) { return WeaponDynamicSway.stabilityBonus(p,s.sway()); }
    static double accuracy(ServerPlayer p,Snapshot s) {
        return WeaponOpeningShot.accuracyScalar(p,s.opening())*WeaponDynamicSway.accuracyScalar(p,s.sway());
    }
    static double growth(ServerPlayer p,Snapshot s) {
        return WeaponOpeningShot.growthScalar(p,s.opening())*WeaponDynamicSway.growthScalar(p,s.sway());
    }
    static float precisionDamage(ServerPlayer p,Snapshot s,float totalPrecision,net.minecraft.world.entity.LivingEntity target) {
        return WeaponHeadseeker.precisionDamage(p,s.headseeker(),totalPrecision,target);
    }
    static float bodyDamage(Snapshot s,float body) { return WeaponGutshot.bodyDamage(s.gutshot(),body); }
    static void confirmed(ServerPlayer p,Snapshot s,net.minecraft.world.entity.LivingEntity target,
                          boolean precision,float actual,boolean killed) {
        WeaponHeadseeker.confirmed(p,s.headseeker(),precision,actual);
        if(killed) WeaponSteadyHands.killed(p,s.steadyHands(),target);
    }
    static float precision(ServerPlayer p,Snapshot s) { return WeaponBoxBreathing.precisionMultiplier(p,s.breathing()); }
}
