package kim.biryeong.destiny.campaign.fallen;

import kim.biryeong.destiny.campaign.RisingServices;
import kim.biryeong.destiny.campaign.RisingServices.FallenKind;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/** Stat sanity for the authored first-mission Fallen tuning (W300). Pure data, no Minecraft bootstrap. */
class FallenArchetypesTest {
    private static final RisingServices.Difficulty FIRST = RisingServices.Difficulty.FIRST_MISSION;

    @Test void everyKindHasAnArchetypeWithItsContractModelAndClips() {
        for (FallenKind kind : FallenKind.values()) {
            var a = FallenArchetypes.of(kind);
            assertNotNull(a, kind.name());
            assertEquals(kind, a.kind());
        }
        assertEquals(RisingServices.Models.DREG, FallenArchetypes.of(FallenKind.DREG).model());
        assertEquals(RisingServices.Models.VANDAL, FallenArchetypes.of(FallenKind.VANDAL).model());
        assertEquals(RisingServices.Models.CAPTAIN, FallenArchetypes.of(FallenKind.CAPTAIN).model());
        assertEquals(RisingServices.Models.SHANK, FallenArchetypes.of(FallenKind.SHANK).model());
        assertEquals(RisingServices.Models.WALKER, FallenArchetypes.of(FallenKind.WALKER).model());
        for (var k : new FallenKind[]{FallenKind.DREG, FallenKind.VANDAL, FallenKind.CAPTAIN})
            assertEquals(RisingServices.Models.INFANTRY_CLIPS, FallenArchetypes.of(k).clips());
        assertEquals(RisingServices.Models.SHANK_CLIPS, FallenArchetypes.of(FallenKind.SHANK).clips());
        assertEquals(RisingServices.Models.WALKER_CLIPS, FallenArchetypes.of(FallenKind.WALKER).clips());
    }

    @Test void everyModelActionResolvesToAContractClip() {
        // FallenModels picks the first available name; each action must have at least one name the
        // contract guarantees for the kinds that use it.
        for (var kind : new FallenKind[]{FallenKind.DREG, FallenKind.VANDAL, FallenKind.CAPTAIN}) {
            var clips = FallenArchetypes.of(kind).clips();
            for (var action : new FallenModels.Action[]{FallenModels.Action.IDLE, FallenModels.Action.MOVE,
                    FallenModels.Action.RUN, FallenModels.Action.SHOOT, FallenModels.Action.MELEE, FallenModels.Action.HIT,
                    FallenModels.Action.STAGGER, FallenModels.Action.DEATH, FallenModels.Action.SPAWN})
                assertTrue(FallenModels.CLIPS.get(action).stream().anyMatch(clips::contains), kind + " " + action);
        }
        var shank = FallenArchetypes.of(FallenKind.SHANK).clips();
        for (var action : new FallenModels.Action[]{FallenModels.Action.IDLE, FallenModels.Action.MOVE,
                FallenModels.Action.SHOOT, FallenModels.Action.HIT, FallenModels.Action.DEATH})
            assertTrue(FallenModels.CLIPS.get(action).stream().anyMatch(shank::contains), "shank " + action);
        var walker = FallenArchetypes.of(FallenKind.WALKER).clips();
        for (var action : new FallenModels.Action[]{FallenModels.Action.IDLE, FallenModels.Action.MOVE,
                FallenModels.Action.FIRE, FallenModels.Action.LEG_BREAK, FallenModels.Action.STAGGER,
                FallenModels.Action.WEAKPOINT_OPEN, FallenModels.Action.RECOVER, FallenModels.Action.DEATH})
            assertTrue(FallenModels.CLIPS.get(action).stream().anyMatch(walker::contains), "walker " + action);
    }

    @Test void toughnessOrderMatchesRoles() {
        double shank = ehp(FallenKind.SHANK), dreg = ehp(FallenKind.DREG),
                vandal = ehp(FallenKind.VANDAL), captain = ehp(FallenKind.CAPTAIN);
        assertTrue(shank < dreg && dreg < vandal && vandal < captain);
        // Captain is the only shielded infantry; shield regen gives a reason to focus it.
        assertTrue(FallenArchetypes.of(FallenKind.CAPTAIN).shield() > 0);
        for (var k : new FallenKind[]{FallenKind.DREG, FallenKind.VANDAL, FallenKind.SHANK})
            assertEquals(0, FallenArchetypes.of(k).shield());
    }

    @Test void primaryAutoRifleKillsInfantryInReadableTimes() {
        // Auto rifle reference: 3 body damage every 3 ticks (WeaponProfile "auto_rifle").
        double dps = 3 * 20 / 3.0;
        assertTrue(ehp(FallenKind.DREG) / dps <= 1.5, "dreg");
        assertTrue(ehp(FallenKind.VANDAL) / dps <= 2.5, "vandal");
        assertTrue(ehp(FallenKind.CAPTAIN) / dps <= 6, "captain");
        assertTrue(ehp(FallenKind.SHANK) / dps <= 1, "shank");
    }

    @Test void telegraphsAreReadableAndProjectilesDodgeable() {
        for (var kind : FallenKind.values()) {
            var a = FallenArchetypes.of(kind);
            for (var attack : new FallenArchetypes.Attack[]{a.primary(), a.secondary()}) {
                if (attack == null) continue;
                assertTrue(attack.telegraphTicks() >= 7, kind + " telegraph");
                assertTrue(attack.projectileSpeed() <= 1.6, kind + " speed");
                if (attack.splashRadius() > 0) {
                    assertTrue(attack.projectileSpeed() <= 1.0, kind + " splash must be slow");
                    assertTrue(attack.telegraphTicks() >= 20, kind + " splash telegraph");
                }
            }
        }
    }

    @Test void noSingleInfantryCanBurstAGuardianQuickly() {
        for (var kind : new FallenKind[]{FallenKind.DREG, FallenKind.VANDAL, FallenKind.CAPTAIN, FallenKind.SHANK}) {
            var a = FallenArchetypes.of(kind).tuned(FIRST);
            for (var attack : new FallenArchetypes.Attack[]{a.primary(), a.secondary()}) {
                if (attack == null) continue;
                double volley = attack.damageFraction() * attack.burst();
                assertTrue(volley < .35, kind + " volley " + volley);
                double cycle = attack.telegraphTicks() + attack.burst() * attack.burstGap()
                        + (attack.cooldownMin() + attack.cooldownMax()) / 2.0;
                double perSecond = volley / (cycle / 20);
                // Even with every shot landing, a full-health Guardian survives ten seconds against one enemy.
                assertTrue(perSecond < .1, kind + " dps " + perSecond);
            }
        }
    }

    @Test void tuningScalesAndSanitises() {
        var base = FallenArchetypes.of(FallenKind.CAPTAIN);
        var hard = base.tuned(new RisingServices.Difficulty(2, 1.5, 3));
        assertEquals(base.health() * 2, hard.health(), 1e-9);
        assertEquals(base.shield() * 2, hard.shield(), 1e-9);
        assertEquals(base.primary().damageFraction() * 1.5, hard.primary().damageFraction(), 1e-9);
        assertEquals(1.0, hard.accuracy(), 1e-9);
        var broken = base.tuned(new RisingServices.Difficulty(Double.NaN, -1, 0));
        assertEquals(base.health(), broken.health(), 1e-9);
        assertEquals(base.primary().damageFraction(), broken.primary().damageFraction(), 1e-9);
        var sloppy = base.tuned(new RisingServices.Difficulty(1, 1, .01));
        assertTrue(sloppy.accuracy() >= .15);
    }

    @Test void precisionZonesAndHitboxes() {
        for (var k : new FallenKind[]{FallenKind.DREG, FallenKind.VANDAL, FallenKind.CAPTAIN}) {
            var a = FallenArchetypes.of(k);
            assertTrue(a.hasPrecisionHead(), k.name());
            // WeaponPrecision uses the top quarter of the box: at least ~0.45 block tall.
            assertTrue(a.height() * .25 >= .45, k + " head zone");
            assertTrue(a.width() >= .7 && a.width() <= 1.2, k + " width");
        }
        assertFalse(FallenArchetypes.of(FallenKind.SHANK).hasPrecisionHead());
        assertFalse(FallenArchetypes.of(FallenKind.WALKER).hasPrecisionHead());
        assertTrue(FallenArchetypes.of(FallenKind.SHANK).flying());
        assertTrue(FallenArchetypes.of(FallenKind.VANDAL).blinkCooldown() > 0);
    }

    @Test void aimSpreadAndLeadAreBounded() {
        assertTrue(FallenArchetypes.spreadRadians(1) < FallenArchetypes.spreadRadians(.3));
        assertEquals(FallenArchetypes.spreadRadians(.01), FallenArchetypes.spreadRadians(.15), 1e-12);
        assertTrue(FallenArchetypes.leadFraction(1) < 1, "never perfect lead");
        var a = FallenArchetypes.of(FallenKind.VANDAL).primary();
        assertEquals(a.cooldownMin(), FallenArchetypes.cooldown(a, -3));
        assertEquals(a.cooldownMax(), FallenArchetypes.cooldown(a, 9));
    }

    @Test void modelLightFloorKeepsSilhouettesWithoutBrighteningLitAreas() {
        assertEquals(FallenModels.LIGHT_FLOOR, FallenModels.flooredBlockLight(0));
        assertEquals(FallenModels.LIGHT_FLOOR, FallenModels.flooredBlockLight(-4));
        assertEquals(12, FallenModels.flooredBlockLight(12));
        assertEquals(15, FallenModels.flooredBlockLight(99));
        assertTrue(FallenModels.LIGHT_FLOOR >= 4 && FallenModels.LIGHT_FLOOR <= 6, "dim, not lamp-bright");
    }

    @Test void fallenDamageCannotOneShotAndHasARollingBudget() {
        double[] w = new double[2];
        assertEquals(FallenWeapons.MAX_HIT_FRACTION, FallenWeapons.guarded(w, 100, .9), 1e-9);
        double second = FallenWeapons.guarded(w, 101, .9);
        assertEquals(FallenWeapons.WINDOW_BUDGET - FallenWeapons.MAX_HIT_FRACTION, second, 1e-9);
        assertEquals(0, FallenWeapons.guarded(w, 110, .1), 1e-9);
        assertTrue(FallenWeapons.MAX_HIT_FRACTION + 0 < 1 && FallenWeapons.WINDOW_BUDGET < 1, "never a full bar in one second");
        assertEquals(.1, FallenWeapons.guarded(w, 100 + FallenWeapons.WINDOW_TICKS, .1), 1e-9);
        assertEquals(0, FallenWeapons.guarded(new double[2], 5, Double.NaN), 1e-9);
        // Walker cannon after first-mission tuning stays under the per-hit cap.
        var walker = FallenArchetypes.of(FallenKind.WALKER).tuned(FIRST);
        assertTrue(walker.primary().damageFraction() <= FallenWeapons.MAX_HIT_FRACTION);
    }

    @Test void invalidAttacksRejected() {
        assertThrows(IllegalArgumentException.class, () -> new FallenArchetypes.Attack(0, 10, 10, 20, 1, 0, 1, 0, 0, 5));
        assertThrows(IllegalArgumentException.class, () -> new FallenArchetypes.Attack(.1, 2, 10, 20, 1, 0, 1, 0, 0, 5));
        assertThrows(IllegalArgumentException.class, () -> new FallenArchetypes.Attack(.1, 10, 20, 10, 1, 0, 1, 0, 0, 5));
    }

    private static double ehp(FallenKind k) {
        var a = FallenArchetypes.of(k).tuned(FIRST);
        return a.health() + a.shield();
    }
}
