package kim.biryeong.destiny.hud;

import org.junit.jupiter.api.Test;

import java.util.HashSet;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/** Pure layout regressions; live HUD/lifecycle integration belongs to the Ace GameTests. */
class AceReticleCounterW158Test {
    @Test void zeroAndNegativeCountsHideEverySlot() {
        for (int rounds : new int[]{Integer.MIN_VALUE, -6, -1, 0}) {
            assertTrue(AceReticleCounter.layout(rounds).isEmpty(), "rounds=" + rounds);
        }
    }

    @Test void everyEarnedCountHasSixSlotsAndExactlyThatManyBrightPips() {
        assertEquals(6, AceReticleCounter.MAX_NODES);
        for (int rounds = 1; rounds <= 6; rounds++) {
            var pips = AceReticleCounter.layout(rounds);
            assertEquals(6, pips.size());
            assertEquals(rounds, pips.stream().filter(p -> p.color() == 0xF1F3F5).count());
            assertEquals(6 - rounds, pips.stream().filter(p -> p.color() == AceReticleCounter.EMPTY_COLOR).count());
            for (int i = 0; i < pips.size(); i++) {
                assertEquals(i < rounds ? 0xF1F3F5 : AceReticleCounter.EMPTY_COLOR, pips.get(i).color());
            }
        }
    }

    @Test void oversizedCountsClampWithoutGrowingOrOverflowing() {
        var full = AceReticleCounter.layout(6);
        for (int rounds : new int[]{7, 99, Integer.MAX_VALUE}) {
            assertEquals(full, AceReticleCounter.layout(rounds));
        }
    }

    @Test void identitiesAreUniqueStableAndOwnedByTheExclusivePrefix() {
        assertEquals("destiny:ace_counter_w158_", AceReticleCounter.PREFIX);
        List<String> expected = AceReticleCounter.layout(6).stream().map(AceReticleCounter.Pip::id).toList();
        assertEquals(6, new HashSet<>(expected).size());
        assertTrue(expected.stream().allMatch(id -> id.startsWith(AceReticleCounter.PREFIX)));
        for (int rounds = 1; rounds <= 6; rounds++) {
            assertEquals(expected, AceReticleCounter.layout(rounds).stream().map(AceReticleCounter.Pip::id).toList());
        }
    }

    @Test void allGeometryIsFinitePositiveAndNarrow() {
        for (int rounds = 1; rounds <= 6; rounds++) {
            for (var pip : AceReticleCounter.layout(rounds)) {
                assertTrue(Float.isFinite(pip.x()));
                assertTrue(Float.isFinite(pip.y()));
                assertTrue(Float.isFinite(pip.width()));
                assertTrue(Float.isFinite(pip.height()));
                assertTrue(pip.width() > 0 && pip.width() <= 4);
                assertTrue(pip.height() > pip.width() && pip.height() <= 8);
                assertTrue(pip.x() - pip.width() / 2 > 0 && pip.x() + pip.width() / 2 < 1920);
                assertTrue(pip.y() - pip.height() / 2 > 0 && pip.y() + pip.height() / 2 < 1080);
            }
        }
    }

    @Test void slotsStayBelowTheSightAndSymmetricAroundTheAimAxis() {
        var pips = AceReticleCounter.layout(6);
        assertEquals(945f, pips.getFirst().x());
        assertEquals(975f, pips.getLast().x());
        for (int i = 0; i < pips.size(); i++) {
            var pip = pips.get(i);
            assertEquals(578f, pip.y());
            assertEquals(1920f, pip.x() + pips.get(pips.size() - 1 - i).x());
            // Keep a 48 x 48 target-centre square entirely unobstructed.
            assertTrue(pip.y() - pip.height() / 2 > 540 + 24);
        }
    }

    @Test void noTwoPipRectanglesOverlap() {
        var pips = AceReticleCounter.layout(6);
        for (int i = 0; i < pips.size(); i++) {
            for (int j = i + 1; j < pips.size(); j++) {
                var a = pips.get(i);
                var b = pips.get(j);
                assertTrue(Math.abs(a.x() - b.x()) > (a.width() + b.width()) / 2
                        || Math.abs(a.y() - b.y()) > (a.height() + b.height()) / 2);
            }
        }
    }

    @Test void earnedWhiteAndMutedEmptySlotsHaveReadableBrightnessContrast() {
        var pips = AceReticleCounter.layout(1);
        int bright = pips.getFirst().color();
        int empty = pips.getLast().color();
        assertEquals(0xF1F3F5, bright);
        assertEquals(0, bright >>> 24);
        assertEquals(0, empty >>> 24);
        assertTrue(luminance(bright) > .85);
        assertTrue(luminance(empty) < .15);
        assertTrue((luminance(bright) + .05) / (luminance(empty) + .05) > 6);
    }

    @Test void returnedLayoutsAreImmutableIncludingHiddenLayout() {
        var visible = AceReticleCounter.layout(3);
        var pip = visible.getFirst();
        assertThrows(UnsupportedOperationException.class, () -> visible.add(pip));
        assertThrows(UnsupportedOperationException.class, () -> visible.set(0, pip));
        assertThrows(UnsupportedOperationException.class, () -> visible.remove(0));
        assertThrows(UnsupportedOperationException.class, () -> AceReticleCounter.layout(0).add(pip));
    }

    @Test void roundChangesOnlyChangeColorsAndNeverMutateEarlierSnapshots() {
        var original = AceReticleCounter.layout(4);
        var expected = List.copyOf(original);
        for (int rounds : new int[]{3, 2, 1, 0, 6}) {
            var next = AceReticleCounter.layout(rounds);
            assertEquals(expected, original);
            for (int i = 0; i < next.size(); i++) {
                var a = original.get(i);
                var b = next.get(i);
                assertEquals(a.id(), b.id());
                assertEquals(a.x(), b.x());
                assertEquals(a.y(), b.y());
                assertEquals(a.width(), b.width());
                assertEquals(a.height(), b.height());
            }
        }
        assertEquals(original, AceReticleCounter.layout(4));
    }

    private static double luminance(int rgb) {
        return .2126 * linear((rgb >> 16) & 255) + .7152 * linear((rgb >> 8) & 255)
                + .0722 * linear(rgb & 255);
    }

    private static double linear(int component) {
        double value = component / 255.0;
        return value <= .04045 ? value / 12.92 : Math.pow((value + .055) / 1.055, 2.4);
    }
}
