package kim.biryeong.destiny.weapon;

import java.math.BigInteger;
import java.util.Random;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Pure migration/conservation tests; real component/NBT serialization is covered by GameTests. */
class WeaponAmmoMigrationW47Test {
    private static WeaponProfile profile(int capacity, int reserves, boolean infinite, boolean shell) {
        return new WeaponProfile(WeaponProfile.Mode.HITSCAN, 5, 10, capacity, reserves,
                10, 40, 0, 1, 1, 0, 0, 0, 0, false, infinite, 10, 1, false, shell);
    }
    private static WeaponMagazine finite(long rounds, long reserve, long overflow) {
        return new WeaponMagazine(profile(4, 10, false, false), rounds, reserve, overflow);
    }
    private static void counts(WeaponMagazine ammo, int rounds, int reserve, long overflow, long total) {
        assertEquals(rounds, ammo.rounds()); assertEquals(reserve, ammo.reserve());
        assertEquals(overflow, ammo.overflow()); assertEquals(total, ammo.total());
    }

    @Test void excessLoadedAmmoFirstUsesAvailableReserveRoomWithoutGrantingAnything() {
        counts(finite(9, 3, 0), 4, 8, 0, 12);
        counts(finite(9, 8, 0), 4, 10, 3, 17);
        counts(finite(0, 0, 8), 0, 8, 0, 8); // No automatic magazine refill.
        counts(new WeaponMagazine(profile(20, 10, false, false), 3, 1), 3, 1, 0, 4);
    }

    @Test void fullReserveAndOversizedReserveNeverDestroyLegacyAmmo() {
        counts(finite(9, 10, 0), 4, 10, 5, 19);
        counts(finite(9, 15, 0), 4, 10, 10, 24);
        var ammo = finite(Integer.MAX_VALUE, Integer.MAX_VALUE, 0);
        counts(ammo, 4, 10, 2L * Integer.MAX_VALUE - 14, 2L * Integer.MAX_VALUE);
        assertEquals(0, ammo.addReserve(Integer.MAX_VALUE));
        assertEquals(2L * Integer.MAX_VALUE, ammo.total());
    }

    @Test void everyActualShotIsTheOnlyFiniteLossAndOverflowEventuallyBecomesUsable() {
        var ammo = finite(9, 15, 7);
        long original = ammo.total(), fired = 0;
        while (ammo.rounds() > 0 || ammo.canReload()) {
            assertEquals(original, fired + ammo.total());
            if (ammo.rounds() == 0) {
                long before = ammo.total();
                assertTrue(ammo.reload() > 0);
                assertEquals(before, ammo.total());
            }
            assertTrue(ammo.consume()); fired++;
            assertEquals(original, fired + ammo.total());
        }
        assertEquals(original, fired);
        counts(ammo, 0, 0, 0, 0);
        assertFalse(ammo.consume()); assertEquals(0, ammo.reload());
    }

    @Test void reserveOnlyPickupsCannotBypassOverflowOrReloadTheMagazine() {
        var ammo = finite(8, 10, 0);
        assertEquals(0, ammo.addReserve(3));
        assertTrue(ammo.consume());
        assertEquals(0, ammo.addReserve(3)); // A shot is not reserve room.
        assertEquals(1, ammo.reload());
        counts(ammo, 4, 10, 3, 17);
        assertEquals(0, ammo.addReserve(Integer.MAX_VALUE));
        assertEquals(0, ammo.addReserve(-1));
        var ordinary = finite(1, 8, 0);
        assertEquals(2, ordinary.addReserve(Integer.MAX_VALUE));
        counts(ordinary, 1, 10, 0, 11);
    }

    @Test void zeroReserveCapacityDoesNotStrandSavedOverflow() {
        var ammo = new WeaponMagazine(profile(4, 0, false, false), 0, 7, 2);
        counts(ammo, 0, 0, 9, 9);
        assertTrue(ammo.canReload()); assertEquals(4, ammo.reload());
        counts(ammo, 4, 0, 5, 9);
        assertEquals(0, ammo.addReserve(5));
    }

    @Test void cancelledMagazineReloadMovesNothingAndDoesNotReapplyMigration() {
        var p = profile(4, 10, false, false);
        var ammo = new WeaponMagazine(p, 0, 10, 5);
        var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(0, p, ammo));
        counts(ammo, 0, 10, 5, 15);
        assertFalse(cycle.finishReload(9, ammo));
        cycle.cancelPending();
        assertFalse(cycle.finishReload(100, ammo));
        counts(ammo, 0, 10, 5, 15);
        assertTrue(cycle.startReload(101, p, ammo));
        assertTrue(cycle.finishReload(111, ammo));
        counts(ammo, 4, 10, 1, 15);
    }

    @Test void cancelledShellReloadKeepsExactlyTheActualInsertAndAllOverflow() {
        var p = profile(4, 10, false, true);
        var ammo = new WeaponMagazine(p, 0, 10, 5);
        var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(0, p, ammo));
        assertTrue(cycle.finishReload(10, ammo));
        counts(ammo, 1, 10, 4, 15);
        cycle.cancelPending();
        assertFalse(cycle.finishReload(1000, ammo));
        counts(ammo, 1, 10, 4, 15);
        assertTrue(ammo.consume());
        counts(ammo, 0, 10, 4, 14);
    }

    @Test void repeatedSerializedStateRestoreIsIdempotentAcrossCapacityChanges() {
        var p = profile(4, 10, false, false);
        var ammo = new WeaponMagazine(p, 9, 15, 7);
        long total = ammo.total();
        for (int i = 0; i < 100; i++) {
            ammo = new WeaponMagazine(p, ammo.rounds(), ammo.reserve(), ammo.overflow());
            counts(ammo, 4, 10, 17, total);
        }
        ammo = new WeaponMagazine(profile(2, 3, false, false), ammo.rounds(), ammo.reserve(), ammo.overflow());
        counts(ammo, 2, 3, 26, total);
        ammo = new WeaponMagazine(profile(20, 30, false, false), ammo.rounds(), ammo.reserve(), ammo.overflow());
        counts(ammo, 2, 29, 0, total); // Growing capacity never automatically loads rounds.
    }

    @Test void primaryReserveSentinelIsNotFiniteAmmoAndExcessLoadedRoundsSurvive() {
        var p = profile(4, 0, true, false);
        var ammo = new WeaponMagazine(p, 9, Integer.MAX_VALUE, 2);
        counts(ammo, 4, 0, 7, 11);
        assertEquals(0, ammo.addReserve(100));
        assertTrue(ammo.consume()); assertEquals(1, ammo.reload());
        counts(ammo, 4, 0, 6, 10); // Retire saved excess before infinite supply.
        var empty = new WeaponMagazine(p, -1, Long.MAX_VALUE, 0);
        counts(empty, 0, 0, 0, 0);
        assertEquals(4, empty.reload()); // Only an explicit primary reload supplies ammo.
        counts(empty, 4, 0, 0, 4);
    }

    @Test void corruptNegativesAndUnrepresentableLongTotalsHaveExplicitSaturatingPolicy() {
        counts(finite(-1, -5, -100), 0, 0, 0, 0);
        var ammo = finite(Long.MAX_VALUE, Long.MAX_VALUE, Long.MAX_VALUE);
        counts(ammo, 4, 10, Long.MAX_VALUE - 14, Long.MAX_VALUE);
        assertEquals(0, ammo.addReserve(Integer.MAX_VALUE));
        assertTrue(ammo.consume()); assertEquals(Long.MAX_VALUE - 1, ammo.total());
        assertEquals(1, ammo.reload()); assertEquals(Long.MAX_VALUE - 1, ammo.total());
        assertThrows(IllegalArgumentException.class, () -> new WeaponAmmoMigration.Allocation(1, 1, Long.MAX_VALUE));
    }

    @Test void randomizedNormalizationMatchesBoundedBigIntegerTotalAndIsIdempotent() {
        var random = new Random(47);
        var ceiling = BigInteger.valueOf(Long.MAX_VALUE);
        for (int i = 0; i < 2000; i++) {
            long rounds = random.nextLong(), reserve = random.nextLong(), overflow = random.nextLong();
            int cap = 1 + random.nextInt(100), reserves = random.nextInt(300);
            var a = WeaponAmmoMigration.normalize(cap, reserves, false, rounds, reserve, overflow);
            var expected = BigInteger.valueOf(Math.max(0, rounds)).add(BigInteger.valueOf(Math.max(0, reserve)))
                    .add(BigInteger.valueOf(Math.max(0, overflow))).min(ceiling);
            assertEquals(expected.longValueExact(), a.total());
            assertTrue(a.rounds() <= cap && a.reserve() <= reserves);
            assertEquals(a, WeaponAmmoMigration.normalize(cap, reserves, false, a.rounds(), a.reserve(), a.overflow()));
        }
    }
}
