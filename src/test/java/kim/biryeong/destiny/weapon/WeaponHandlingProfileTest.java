package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WeaponHandlingProfileTest {
    @Test void allCatalogEntriesHaveExplicitTimingOrUnknownSwordState() {
        int supported = 0;
        for (var e : WeaponCatalog.all()) {
            var p = WeaponHandlingProfile.of(e);
            if (e.family().equals("sword")) {
                assertFalse(p.supported()); assertNull(p.handling()); assertNull(p.readyTicks()); assertNull(p.stowTicks());
            } else {
                supported++; assertTrue(p.supported());
                assertEquals(WeaponCharacteristics.of(e).stats().get("943549884"), p.handling());
                assertTrue(p.readyTicks() > 0); assertTrue(p.stowTicks() > 0);
            }
        }
        assertEquals(58, WeaponCatalogTest.originalW30Entries().stream()
                .filter(e -> !e.family().equals("sword")).count());
        assertEquals(60, WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id()))
                .filter(e -> WeaponHandlingProfile.of(e).supported()).count());
        assertEquals(60 + 24, supported);
    }
    @Test void actualSelectedItemStatsDriveDistinctReadyAndStowTimes() {
        var p = WeaponHandlingProfile.of(WeaponCatalog.find("austringer").orElseThrow());
        assertEquals(47, p.handling()); assertEquals(7, p.readyTicks()); assertEquals(8, p.stowTicks());
        var glaive = WeaponHandlingProfile.of(WeaponCatalog.find("nezarec_s_whisper").orElseThrow());
        assertEquals(42, glaive.handling()); assertEquals(7, glaive.readyTicks()); assertEquals(8, glaive.stowTicks());
    }
    @Test void lowAndHighHandlingWithinFamilyUseTheOriginalCurve() {
        var low = WeaponHandlingProfile.of(WeaponCatalog.find("antiope_d").orElseThrow());
        var high = WeaponHandlingProfile.of(WeaponCatalog.find("ikelos_smg_v1_0_1").orElseThrow());
        assertTrue(high.readyTicks() < low.readyTicks()); assertTrue(high.stowTicks() < low.stowTicks());
    }
    @Test void invalidDataCannotBecomeAZeroTimeOrPartlyKnownProfile() {
        assertThrows(IllegalArgumentException.class, () -> new WeaponHandlingProfile(true, null, 1, 1));
        assertThrows(IllegalArgumentException.class, () -> new WeaponHandlingProfile(true, 101, 1, 1));
        assertThrows(IllegalArgumentException.class, () -> new WeaponHandlingProfile(true, 50, 0, 1));
        assertThrows(IllegalArgumentException.class, () -> new WeaponHandlingProfile(false, null, 1, null));
    }
}
