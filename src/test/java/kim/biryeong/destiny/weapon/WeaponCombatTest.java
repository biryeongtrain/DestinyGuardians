package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.util.Set;
import java.util.stream.Collectors;
import static org.junit.jupiter.api.Assertions.*;

class WeaponCombatTest {
    private static WeaponProfile profile(String id) { return WeaponProfile.forEntry(WeaponCatalog.find(id).orElseThrow()); }
    @Test void all63ModelsHaveImplementedBoundedProfilesAcross18Families() {
        WeaponCatalogTest.assertExpandedCatalog();
        assertEquals(18, WeaponCatalog.all().stream().map(WeaponCatalog.Entry::family).distinct().count());
        for (var entry : WeaponCatalog.all()) {
            var p = WeaponProfile.forEntry(entry);
            assertTrue(p.damage() > 0 && p.damage() <= 35, entry.id());
            assertTrue(p.intervalTicks() >= 1 && p.range() <= 96 && p.magazine() > 0, entry.id());
            boolean historicalTwelve=Set.of("mindbender_s_ambition_adept","dust_rock_blues",
                    "parcel_of_stardust_fell_to_earth","ikelos_sg_v1_0_1").contains(entry.id());
            assertTrue(p.reserve() <= 240 && p.blastRadius() <= 4
                    && (historicalTwelve?p.pellets()==12:p.pellets()<=8), entry.id());
        }
        assertEquals(Set.of(WeaponProfile.Mode.HITSCAN, WeaponProfile.Mode.MELEE, WeaponProfile.Mode.PROJECTILE),
                WeaponCatalog.all().stream().map(WeaponProfile::forEntry).map(WeaponProfile::mode).collect(Collectors.toSet()));
    }
    @Test void familiesUseTravelChargeBurstPelletsAndAutomaticAsAdvertised() {
        for (String id : new String[]{"biting_winds", "bad_omens", "salvager_s_salvo", "edge_transit", "nezarec_s_whisper"})
            assertEquals(WeaponProfile.Mode.PROJECTILE, profile(id).mode());
        assertEquals(WeaponProfile.Mode.MELEE, profile("goldtusk").mode());
        assertEquals(1, profile("first_in_last_out").pellets());
        assertEquals(12, profile("dust_rock_blues").pellets());
        assertEquals(4, profile("blast_furnace").burst());
        assertEquals(2, profile("brass_attacks").burst());
        assertEquals(3, profile("stormchaser").burst());
        assertTrue(profile("erentil_fr4").chargeTicks() > 0);
        assertTrue(profile("retraced_path").automatic());
        assertFalse(profile("austringer").automatic());
        assertTrue(profile("steelfeather_repeater").intervalTicks() <= profile("halfdan_d").intervalTicks());
    }
    @Test void specialAndHeavyHaveFiniteAmmunitionAndReloadConservesIt() {
        for (var entry : WeaponCatalog.all()) {
            var p = WeaponProfile.forEntry(entry);
            var ammo = new WeaponMagazine(p, p.magazine(), p.reserve());
            if(p.infiniteReserve())continue;
            int expected = p.magazine() + p.reserve(), fired = 0;
            while (ammo.rounds() > 0 || ammo.reserve() > 0) {
                if (ammo.consume()) fired++;
                else assertTrue(ammo.reload() > 0);
                assertEquals(expected, fired + ammo.rounds() + ammo.reserve(), entry.id());
            }
            assertEquals(expected, fired);
            assertFalse(ammo.consume()); assertFalse(ammo.canReload()); assertEquals(0, ammo.reload());
        }
    }
    @Test void corruptAmmunitionIsClampedWithoutCreatingReserve() {
        var p = profile("austringer");
        var negative = new WeaponMagazine(p, -100, -5);
        assertEquals(0, negative.rounds()); assertEquals(0, negative.reserve());
        var oversized = new WeaponMagazine(p, Integer.MAX_VALUE, Integer.MAX_VALUE);
        assertEquals(p.magazine(), oversized.rounds()); assertEquals(p.reserve(), oversized.reserve());
    }
    @Test void duplicateAndSwapCannotBypassServerCadence() {
        var p = profile("austringer"); var ammo = new WeaponMagazine(p, p.magazine(), p.reserve());
        var cycle = new WeaponCycle();
        assertTrue(cycle.fire(100, p, ammo));
        for (int i = 0; i < 100; i++) assertFalse(cycle.fire(100, p, ammo));
        cycle.cancelPending();
        assertFalse(cycle.fire(101, profile("the_recluse"), ammo));
        assertTrue(cycle.fire(100 + p.intervalTicks(), p, ammo));
        assertEquals(p.magazine() - 2, ammo.rounds());
    }
    @Test void reloadTransfersOnlyAtDeadlineAndCancellationTransfersNothing() {
        var p = profile("beloved"); var ammo = new WeaponMagazine(p, 1, 3); var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(10, p, ammo));
        assertFalse(cycle.startReload(11, p, ammo));
        assertFalse(cycle.fire(1000, p, ammo));
        assertFalse(cycle.finishReload(10 + p.reloadTicks() - 1, ammo));
        assertEquals(1, ammo.rounds()); assertEquals(3, ammo.reserve());
        cycle.cancelPending();
        assertFalse(cycle.finishReload(1000, ammo));
        assertEquals(1, ammo.rounds()); assertEquals(3, ammo.reserve());
        assertTrue(cycle.startReload(1000, p, ammo));
        assertTrue(cycle.finishReload(1000 + p.reloadTicks(), ammo));
        assertEquals(4, ammo.rounds()); assertEquals(0, ammo.reserve());
        assertFalse(cycle.finishReload(2000, ammo));
    }
    @Test void chargeRequiresElapsedServerTicksAndCancelsOnReleaseOrSwap() {
        var p = profile("line_in_the_sand"); var cycle = new WeaponCycle();
        assertTrue(cycle.startCharge(20)); assertFalse(cycle.startCharge(21));
        assertFalse(cycle.charged(20 + p.chargeTicks() - 1, p.chargeTicks()));
        assertTrue(cycle.charged(20 + p.chargeTicks(), p.chargeTicks()));
        cycle.cancelCharge(); assertFalse(cycle.charged(1000, p.chargeTicks()));
        assertTrue(cycle.startCharge(1001)); cycle.cancelPending(); assertFalse(cycle.charging());
    }
    @Test void burstConsumesPerBulletAndCannotRefireOrReloadMidBurst() {
        var p = profile("blast_furnace"); var ammo = new WeaponMagazine(p, 4, 5); var cycle = new WeaponCycle();
        assertTrue(cycle.fire(10, p, ammo));
        int first=10+(int)Math.ceil(p.burstSpacingTicks());
        assertFalse(cycle.burst(first-1, ammo));
        assertFalse(cycle.fire(first, p, ammo)); assertFalse(cycle.startReload(first, p, ammo));
        for(int i=1;i<p.burst();i++)assertTrue(cycle.burst(10+(int)Math.ceil(i*p.burstSpacingTicks()),ammo));
        assertFalse(cycle.burst(100, ammo)); assertEquals(0, ammo.rounds());
        assertEquals(0, ammo.reserve()); // Primary reserve is a policy, not a fabricated finite stack.
    }
    @Test void burstStopsAtLastRoundAndCancellationCannotSpendQueuedRounds() {
        var p = profile("bygones"); var ammo = new WeaponMagazine(p, 2, 0); var cycle = new WeaponCycle();
        assertTrue(cycle.fire(10, p, ammo)); cycle.cancelPending();
        assertFalse(cycle.burst(12, ammo)); assertEquals(1, ammo.rounds());
        assertTrue(cycle.fire(100, p, ammo));
        assertFalse(cycle.burst(102, ammo)); assertEquals(0, ammo.rounds());
    }
}
