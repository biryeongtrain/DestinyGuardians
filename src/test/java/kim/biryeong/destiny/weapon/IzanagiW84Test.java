package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Set;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/** Pure W84 identity, funding and rounded source-multiplier contracts. No server or fake reload grants. */
class IzanagiW84Test {
    private static WeaponCatalog.Entry entry() { return WeaponCatalog.find("izanagis_burden").orElseThrow(); }
    private static WeaponProfile profile() { return WeaponProfile.forEntry(entry()); }
    private static void unchanged(WeaponMagazine ammo, int rounds, int reserve, long overflow) {
        assertEquals(rounds, ammo.rounds()); assertEquals(reserve, ammo.reserve()); assertEquals(overflow, ammo.overflow());
    }

    @Test void exactSecondExoticKeepsAllOriginalSixtyThreeAndAceCanonical() {
        WeaponCatalogTest.assertExpandedCatalog();
        assertEquals(65, WeaponCatalog.all().size());
        assertEquals(Set.of("ace_of_spades", "izanagis_burden"), WeaponCatalog.all().stream()
                .filter(e -> WeaponCharacteristics.of(e).exotic()).map(WeaponCatalog.Entry::id).collect(Collectors.toSet()));
        for (var e : WeaponCatalog.all()) assertEquals(e.equals(entry()), WeaponExotics.izanagi(e), e.id());
        assertTrue(WeaponExotics.ace(WeaponCatalog.find("ace_of_spades").orElseThrow()));
        for (var e : WeaponCatalogTest.originalW30Entries()) assertFalse(WeaponExotics.izanagi(e), e.id());
        var c = WeaponCharacteristics.of(entry());
        assertEquals(3211806999L, c.bungieHash()); assertEquals("sniper_rifle", entry().family());
        assertEquals("exotic", entry().frame()); assertTrue(c.exotic());
        assertEquals(WeaponSlot.KINETIC, c.slot()); assertEquals(WeaponAmmoType.SPECIAL, c.ammo());
        assertEquals(WeaponCharacteristics.Damage.KINETIC, c.damage());
        assertEquals(58, c.stats().get("1240592695")); assertEquals(56, c.stats().get("155624089"));
        assertEquals(47, c.stats().get("943549884")); assertEquals(83, c.stats().get("2715839340"));
        assertTrue(WeaponPerks.rolls().stream().noneMatch(r -> r.id().equals(entry().id())),
                "No legendary sockets, optional catalyst or No Distractions implementation inferred from the name");
    }

    @Test void finiteFourRoundNinetyRpmProfileKeepsSixtyOneFullRecoveryAndNoEarlyCredit() {
        var p = profile();
        assertEquals(4, p.magazine()); assertEquals(20, p.reserve()); assertFalse(p.infiniteReserve());
        assertEquals(90, WeaponTiming.of(entry()).rpm().orElseThrow()); assertEquals(1200d / 90, p.cadenceTicks(), 1e-10);
        assertEquals(16, p.damage()); assertEquals(2.5, WeaponBallistics.of(entry()).precision());
        assertEquals(WeaponProfile.Mode.HITSCAN, p.mode()); assertEquals(1, p.burst()); assertEquals(1, p.pellets());
        assertEquals(0, p.chargeTicks()); assertFalse(p.automatic()); assertFalse(p.shellReload());
        assertEquals(61, WeaponIzanagi.RELOAD_TICKS); assertEquals(61, p.firstReloadTicks()); assertEquals(61, p.reloadTicks());
        assertTrue(ReloadCreditProfile.find(entry()).isEmpty());
        assertEquals(61, ReloadCreditProfile.ammoTicks(entry(), new WeaponReloadPolicy.Plan(61, 61, 0)));
        assertEquals(9, WeaponAimProfile.of(entry()).transitionTicks()); assertEquals(4.5f, WeaponAimProfile.of(entry()).zoom());
        assertEquals(8, WeaponHandlingProfile.of(entry()).readyTicks()); assertEquals(7, WeaponHandlingProfile.of(entry()).stowTicks());
        assertEquals(WeaponModels.Grip.TWO_HAND, WeaponModels.defaultGrip(entry()));
        assertEquals(.75, WeaponAimMovementProfile.scalar(entry()));
        assertTrue(WeaponScopes.supports(entry()),
                "W162 adds an explicitly authored approximate scope; sourced zoom and funding above remain unchanged");
    }

    @Test void officialBaseStatsRemainSeparateFromFixedPlugDerivedStats() throws Exception {
        var official = JsonParser.parseString(Files.readString(Path.of("art/weapons/w84/data/bungie-izanagi.json"))).getAsJsonObject();
        assertEquals(3211806999L, official.get("hash").getAsLong());
        var stats = official.getAsJsonObject("stats").getAsJsonObject("stats");
        assertEquals(48, stats.getAsJsonObject("1240592695").get("value").getAsInt());
        assertEquals(41, stats.getAsJsonObject("155624089").get("value").getAsInt());
        assertEquals(47, stats.getAsJsonObject("943549884").get("value").getAsInt());
        var extraction = JsonParser.parseString(Files.readString(Path.of("art/weapons/w84/data/extraction.json"))).getAsJsonObject();
        var evidence = extraction.getAsJsonObject("official");
        assertEquals(3211806999L, evidence.get("weaponHash").getAsLong());
        var fixed = evidence.getAsJsonObject("fixedPlugBonuses");
        assertEquals(10, fixed.get("1240592695").getAsInt()); assertEquals(15, fixed.get("155624089").getAsInt());
        assertEquals(0, fixed.get("943549884").getAsInt());
        assertFalse(evidence.getAsJsonObject("catalyst").get("defaultEnabled").getAsBoolean());
        assertTrue(extraction.getAsJsonObject("reload").get("honedDurationTicks").isJsonNull(),
                "61 ticks is the local captured transaction policy, not an established exact original animation");
    }

    @Test void unknownAndAlteredCatalogIdentityCannotBorrowHonedEdge() {
        assertFalse(WeaponExotics.izanagi(null));
        var real = entry();
        assertFalse(WeaponExotics.izanagi(new WeaponCatalog.Entry(real.id(), "hand_cannon", real.frame(),
                real.name(), real.source_frame_label(), real.item_model())));
        assertFalse(WeaponExotics.izanagi(new WeaponCatalog.Entry(real.id(), real.family(), "adaptive",
                real.name(), real.source_frame_label(), real.item_model())));
        assertFalse(WeaponExotics.izanagi(new WeaponCatalog.Entry("w84_unknown", real.family(), real.frame(),
                real.name(), real.source_frame_label(), real.item_model())));
    }

    @Test void roundedPveAndPvpMultipliersAreRelativeToTheSameBodyOrPrecisionHitWithoutCatalyst() {
        float[][] expected = {{1.12f, 1.79f, 1.20f, 1.91f}, {1.25f, 2.31f, 1.45f, 2.67f}, {2.12f, 3.91f, 2.65f, 4.89f}};
        for (int n = 2; n <= 4; n++) {
            assertEquals(expected[n - 2][0], WeaponIzanagi.multiplier(n, false, false));
            assertEquals(expected[n - 2][1], WeaponIzanagi.multiplier(n, true, false));
            assertEquals(expected[n - 2][2], WeaponIzanagi.multiplier(n, false, true));
            assertEquals(expected[n - 2][3], WeaponIzanagi.multiplier(n, true, true));
        }
        for (int n : new int[]{Integer.MIN_VALUE, -1, 0, 1, 5, Integer.MAX_VALUE})
            for (boolean precision : new boolean[]{false, true}) for (boolean pvp : new boolean[]{false, true})
                assertEquals(1, WeaponIzanagi.multiplier(n, precision, pvp));
    }

    @Test void everyBoundedFiniteFundingCombinationIsAtomicAndConservesExactlyCountMinusOne() {
        for (int loaded = 0; loaded <= 4; loaded++) for (int reserve = 0; reserve <= 20; reserve++)
            for (long overflow : new long[]{0, 1, 11, 1_000_000}) for (int n = 2; n <= 4; n++) {
                var ammo = new WeaponMagazine(profile(), loaded, reserve, overflow);
                int beforeRounds = ammo.rounds(), beforeReserve = ammo.reserve(); long beforeOverflow = ammo.overflow(), before = ammo.total();
                boolean expected = beforeRounds <= n && before >= n;
                assertEquals(expected, ammo.compressRounds(n), "funding " + loaded + "/" + reserve + "/" + overflow + " x" + n);
                if (expected) {
                    assertEquals(1, ammo.rounds()); assertEquals(before - n + 1, ammo.total());
                    assertTrue(ammo.reserve() >= 0 && ammo.reserve() <= 20 && ammo.overflow() >= 0);
                    assertTrue(ammo.consume()); assertEquals(before - n, ammo.total());
                    assertFalse(ammo.consume(), "The compressed shot is one finite projectile, not n emitted rounds");
                } else unchanged(ammo, beforeRounds, beforeReserve, beforeOverflow);
            }
    }

    @Test void fullLoadedPoolPaysNoReserveWhileEmptyAndPartialTopUpUseRealFiniteCartridges() {
        var full = new WeaponMagazine(profile(), 4, 20, 11); assertTrue(full.compressRounds(4)); unchanged(full, 1, 20, 11);
        var empty = new WeaponMagazine(profile(), 0, 20, 11); assertTrue(empty.compressRounds(4)); unchanged(empty, 1, 20, 7);
        var partial = new WeaponMagazine(profile(), 1, 2); assertTrue(partial.compressRounds(3)); unchanged(partial, 1, 0, 0);
        var two = new WeaponMagazine(profile(), 2, 0); assertTrue(two.compressRounds(2)); unchanged(two, 1, 0, 0);
    }

    @Test void insufficientUnsupportedOrInvalidFundingNeverPartiallySpends() {
        for (int total = 0; total < 2; total++) {
            var ammo = new WeaponMagazine(profile(), total, 0);
            assertFalse(ammo.compressRounds(2)); unchanged(ammo, total, 0, 0);
        }
        for (int n : new int[]{Integer.MIN_VALUE, -1, 0, 1, 5, Integer.MAX_VALUE}) {
            var ammo = new WeaponMagazine(profile(), 4, 20); assertFalse(ammo.compressRounds(n)); unchanged(ammo, 4, 20, 0);
        }
        var loaded = new WeaponMagazine(profile(), 4, 0); assertFalse(loaded.compressRounds(2)); unchanged(loaded, 4, 0, 0);
        var primary = new WeaponMagazine(WeaponProfile.forEntry(WeaponCatalog.find("austringer").orElseThrow()), 2, 0);
        assertFalse(primary.compressRounds(2)); assertEquals(2, primary.rounds());
    }

    @Test void capturedTwoCannotBeUpgradedByLaterReserveArrivalsAndLostFundsCannotBeInvented() {
        var ammo = new WeaponMagazine(profile(), 2, 0); int captured = (int) Math.min(4, ammo.total());
        assertEquals(2, captured); assertEquals(4, ammo.addReserve(4));
        assertTrue(ammo.compressRounds(captured)); unchanged(ammo, 1, 4, 0);
        var lost = new WeaponMagazine(profile(), 1, 1);
        assertFalse(lost.compressRounds(4)); unchanged(lost, 1, 1, 0);
    }

    @Test void saturatingLegacyOverflowStillDebitsExactlyFourWithoutWraparound() {
        var ammo = new WeaponMagazine(profile(), Long.MAX_VALUE, Long.MAX_VALUE, Long.MAX_VALUE);
        assertEquals(Long.MAX_VALUE, ammo.total()); assertTrue(ammo.compressRounds(4));
        assertEquals(1, ammo.rounds()); assertEquals(20, ammo.reserve());
        assertEquals(Long.MAX_VALUE - 3, ammo.total()); assertTrue(ammo.consume());
        assertEquals(Long.MAX_VALUE - 4, ammo.total()); assertFalse(ammo.consume());
    }
}
