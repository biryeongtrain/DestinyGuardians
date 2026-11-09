package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;

import java.util.Set;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/** Pure catalog/profile tests. Ratios are relative ADS movement, never absolute D2 speed. */
class WeaponAimMovementW75Test {
    private static final double EPS = 1e-12;
    private static final Set<String> SIDEARMS = Set.of(
            "allied_demand", "farewell", "lonesome", "dead_man_walking_xx7463", "high_albedo", "brass_attacks");
    private static final String PRECISION_HC = "seventh_seraph_officer_revolver";

    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }

    @Test
    void exactly57NormalW44WeaponsHaveMovementProfiles() {
        var supported = WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id())).filter(WeaponAimProfile::supports).toList();
        assertEquals(57, WeaponCatalogTest.originalW30Entries().stream().filter(WeaponAimProfile::supports).count());
        assertEquals(59, supported.size());
        var legacyIds = new java.util.HashSet<>(WeaponCatalogTest.originalW30Entries().stream().map(WeaponCatalog.Entry::id).toList());
        legacyIds.add("ace_of_spades"); legacyIds.add("izanagis_burden");
        assertEquals(legacyIds,WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id()))
                .map(WeaponCatalog.Entry::id).collect(Collectors.toSet()));
        for (var e : supported) assertDoesNotThrow(() -> WeaponAimMovementProfile.scalar(e), e.id());
    }

    @Test
    void allSixPinnedSidearmsUseTheFifteenPercentPenalty() {
        assertEquals(SIDEARMS, WeaponCatalog.family("sidearm").stream().filter(e -> !LegendaryWeapons.contains(e.id()))
                .map(WeaponCatalog.Entry::id).collect(Collectors.toSet()));
        for (String id : SIDEARMS) assertEquals(.85, WeaponAimMovementProfile.scalar(entry(id)), EPS, id);
    }

    @Test
    void precisionHandCannonReducesTheOrdinaryPenaltyByTenPercent() {
        var precision = WeaponCatalog.family("hand_cannon").stream()
                .filter(e -> e.frame().equals("precision")).toList();
        assertEquals(Set.of(PRECISION_HC), precision.stream().map(WeaponCatalog.Entry::id).collect(Collectors.toSet()));
        assertEquals(1 - .25 * .9, WeaponAimMovementProfile.scalar(entry(PRECISION_HC)), EPS);
        assertEquals(.775, WeaponAimMovementProfile.scalar(entry(PRECISION_HC)), EPS);
    }

    @Test
    void remaining50SupportedWeaponsUseTheOrdinaryQuarterPenalty() {
        var ordinary = WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id())).filter(WeaponAimProfile::supports)
                .filter(e -> !SIDEARMS.contains(e.id()) && !e.id().equals(PRECISION_HC)).toList();
        assertEquals(50, WeaponCatalogTest.originalW30Entries().stream().filter(WeaponAimProfile::supports)
                .filter(e -> !SIDEARMS.contains(e.id()) && !e.id().equals(PRECISION_HC)).count());
        assertEquals(52, ordinary.size());
        for (var e : ordinary) assertEquals(.75, WeaponAimMovementProfile.scalar(e), EPS, e.id());
    }

    @Test
    void everySwordAndGlaiveIsRejectedRatherThanAssignedASpeculativeScalar() {
        var excluded = WeaponCatalog.all().stream().filter(e -> !WeaponAimProfile.supports(e)).toList();
        assertEquals(6, excluded.size());
        assertEquals(Set.of("sword", "glaive"), excluded.stream().map(WeaponCatalog.Entry::family).collect(Collectors.toSet()));
        for (var e : excluded) assertThrows(IllegalArgumentException.class,
                () -> WeaponAimMovementProfile.scalar(e), e.id());
    }

    @Test
    void unknownAndAlteredCatalogRowsCannotBorrowAKnownIdsRatio() {
        var real = entry("austringer");
        var unknown = new WeaponCatalog.Entry("w75_unknown", real.family(), real.frame(), real.name(),
                real.source_frame_label(), real.item_model());
        var altered = new WeaponCatalog.Entry(real.id(), "sidearm", real.frame(), real.name(),
                real.source_frame_label(), real.item_model());
        assertThrows(IllegalArgumentException.class, () -> WeaponAimMovementProfile.scalar(unknown));
        assertThrows(IllegalArgumentException.class, () -> WeaponAimMovementProfile.scalar(altered));
    }

    @Test
    void movementModifierUsesTheRatioDirectlyWithoutDividingBySneakBase() {
        double[] scalars = {.75, .85, .775, 1, .3, .01};
        double[] amounts = {-.25, -.15, -.225, 0, -.7, -.99};
        for (int i = 0; i < scalars.length; i++) {
            assertEquals(amounts[i], WeaponAimMovementProfile.modifierAmount(scalars[i]), EPS);
            assertEquals(scalars[i], 1 + WeaponAimMovementProfile.modifierAmount(scalars[i]), EPS);
        }
    }

    @Test
    void independentNeutralizerLiftsDefaultSneakToOneForEveryMovementRatio() {
        assertEquals(.3, WeaponAimMovementProfile.NATIVE_SNEAK_BASE, EPS);
        assertEquals(7d / 3, WeaponAimMovementProfile.neutralizerAmount(), EPS);
        assertEquals(1, .3 * (1 + WeaponAimMovementProfile.neutralizerAmount()), EPS);
        for (double scalar : new double[]{.75, .85, .775}) {
            assertEquals(scalar, .3 * (1 + WeaponAimMovementProfile.neutralizerAmount())
                    * (1 + WeaponAimMovementProfile.modifierAmount(scalar)), EPS);
        }
    }

    @Test
    void movementModifierRejectsNonfiniteNonpositiveAndAboveOneRatios() {
        for (double bad : new double[]{Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY,
                0, -0d, -1, Math.nextUp(1d)}) {
            assertThrows(IllegalArgumentException.class, () -> WeaponAimMovementProfile.modifierAmount(bad), "ratio=" + bad);
        }
    }
}
