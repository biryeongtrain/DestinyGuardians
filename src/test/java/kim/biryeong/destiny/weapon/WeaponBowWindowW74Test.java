package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;

import java.util.List;

import static kim.biryeong.destiny.weapon.WeaponBowWindow.Phase.*;
import static org.junit.jupiter.api.Assertions.*;

/** Sourced timing and informational phases; feedback does not authorize a different shot. */
class WeaponBowWindowW74Test {
    private static WeaponCatalog.Entry bow(String id) {
        return WeaponCatalog.find(id).orElseThrow();
    }

    @Test void officialW40StabilityAndMicrosecondsProduceNineAndFourteenTickWindows() {
        var precision = bow("biting_winds");
        var lightweight = bow("whispering_slab");
        assertEquals("precision", precision.frame());
        assertEquals("lightweight", lightweight.frame());
        assertEquals(43, WeaponCharacteristics.of(precision).stats().get("155624089").intValue());
        assertEquals(53, WeaponCharacteristics.of(lightweight).stats().get("155624089").intValue());
        assertEquals(407_500, WeaponBowWindow.windowMicros("precision", 43));
        assertEquals(659_000, WeaponBowWindow.windowMicros("lightweight", 53));
        assertEquals(9, WeaponBowWindow.windowTicks(precision));
        assertEquals(14, WeaponBowWindow.windowTicks(lightweight));
    }

    @Test void sourceFormulaRetainsFractionalMillisecondsAcrossTheWholeStatRange() {
        for (int stability = 0; stability <= 100; stability++) {
            assertEquals(300_000 + 2_500 * stability,
                    WeaponBowWindow.windowMicros("precision", stability), "precision " + stability);
            assertEquals(500_000 + 3_000 * stability,
                    WeaponBowWindow.windowMicros("lightweight", stability), "lightweight " + stability);
        }
    }

    @Test void idleAndNegativeElapsedHaveNoDrawAgeOrProgress() {
        var idle = WeaponBowWindow.idle();
        assertEquals(IDLE, idle.phase());
        assertEquals(0f, idle.progress());
        assertEquals(0, idle.windowTicks());
        assertEquals(-1L, idle.fullDrawAge());
        for (String id : List.of("biting_winds", "whispering_slab")) {
            var entry = bow(id);
            int accepted = WeaponProfile.forEntry(entry).chargeTicks();
            assertEquals(idle, WeaponBowWindow.state(entry, accepted, -1));
            assertEquals(idle, WeaponBowWindow.state(entry, accepted, Long.MIN_VALUE));
        }
    }

    @Test void bothNativeDrawDurationsHaveExactHalfOpenPerfectBoundaries() {
        for (String id : List.of("biting_winds", "whispering_slab")) {
            var entry = bow(id);
            int accepted = WeaponProfile.forEntry(entry).chargeTicks();
            int window = id.equals("biting_winds") ? 9 : 14;
            for (int elapsed = 0; elapsed < accepted; elapsed++) {
                var state = WeaponBowWindow.state(entry, accepted, elapsed);
                assertEquals(DRAWING, state.phase(), id + " elapsed=" + elapsed);
                assertEquals(elapsed / (float) accepted, state.progress(), 1e-6f);
                assertEquals(window, state.windowTicks());
                assertEquals(-1L, state.fullDrawAge());
            }
            for (int age = 0; age < window; age++) {
                var state = WeaponBowWindow.state(entry, accepted, accepted + age);
                assertEquals(PERFECT, state.phase(), id + " fullDrawAge=" + age);
                assertEquals(1f, state.progress());
                assertEquals(window, state.windowTicks());
                assertEquals((long) age, state.fullDrawAge());
            }
            for (long elapsed : new long[]{accepted + window, accepted + window + 1L, Long.MAX_VALUE}) {
                var state = WeaponBowWindow.state(entry, accepted, elapsed);
                assertEquals(LATE, state.phase(), id + " elapsed=" + elapsed);
                assertEquals(1f, state.progress());
                assertEquals(window, state.windowTicks());
                assertEquals(elapsed - accepted, state.fullDrawAge());
            }
        }
    }

    @Test void acceptedNineTickTempoDrawChangesFullDrawOriginButNotStabilityWindow() {
        var entry = bow("whispering_slab");
        assertEquals(12, WeaponProfile.forEntry(entry).chargeTicks());
        var before = WeaponBowWindow.state(entry, 9, 8);
        assertEquals(DRAWING, before.phase());
        assertEquals(8 / 9f, before.progress(), 1e-6f);
        assertEquals(-1L, before.fullDrawAge());
        assertEquals(PERFECT, WeaponBowWindow.state(entry, 9, 9).phase());
        assertEquals(0L, WeaponBowWindow.state(entry, 9, 9).fullDrawAge());
        assertEquals(PERFECT, WeaponBowWindow.state(entry, 9, 22).phase());
        assertEquals(LATE, WeaponBowWindow.state(entry, 9, 23).phase());
        assertEquals(14, WeaponBowWindow.state(entry, 9, 23).windowTicks());
        assertEquals(DRAWING, WeaponBowWindow.state(entry, 12, 9).phase());
    }

    @Test void invalidAcceptedDurationAndUnsupportedCatalogEntriesCannotProducePhases() {
        var entry = bow("biting_winds");
        for (int accepted : new int[]{0, -1, Integer.MIN_VALUE})
            assertThrows(IllegalArgumentException.class, () -> WeaponBowWindow.state(entry, accepted, 0));
        for (var other : WeaponCatalog.all()) {
            if (other.id().equals("biting_winds") || other.id().equals("whispering_slab")) continue;
            assertThrows(IllegalArgumentException.class, () -> WeaponBowWindow.windowTicks(other), other.id());
            assertThrows(IllegalArgumentException.class, () -> WeaponBowWindow.state(other, 12, 0), other.id());
        }
        var invented = new WeaponCatalog.Entry("unselected_bow", "bow", "precision",
                "Unselected Bow", "Precision Frame", "destiny:weapon/unselected_bow");
        var wrongFamily = new WeaponCatalog.Entry(entry.id(), "hand_cannon", entry.frame(),
                entry.name(), entry.source_frame_label(), entry.item_model());
        var wrongFrame = new WeaponCatalog.Entry(entry.id(), "bow", "lightweight",
                entry.name(), entry.source_frame_label(), entry.item_model());
        for (var unsupported : List.of(invented, wrongFamily, wrongFrame))
            assertThrows(IllegalArgumentException.class, () -> WeaponBowWindow.windowTicks(unsupported));
    }
}
