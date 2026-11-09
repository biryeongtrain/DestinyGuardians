package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class SnapshotCoverageW327Test {
    @Test void expandedCatalogDoesNotBreakLegacySnapshotInitialization() {
        assertEquals(24, LegendaryWeapons.ids().size());
        assertFalse(SnapshotAimProfile.rolls().isEmpty());
        for (var entry : WeaponCatalog.all()) {
            if (!WeaponAimProfile.supports(entry)) continue;
            assertTrue(WeaponAimProfile.of(entry).transitionTicks() > 0, entry.id());
            if (LegendaryWeapons.contains(entry.id())) {
                assertTrue(LegendaryPerks.extraRolls(SnapshotAimProfile.ID).stream()
                        .noneMatch(r -> r.id().equals(entry.id())), "No unimplemented Snapshot socket " + entry.id());
            } else if (!WeaponCharacteristics.of(entry).exotic()) {
                assertNotNull(SnapshotAimProfile.timing(entry), entry.id());
            }
        }
    }
}
