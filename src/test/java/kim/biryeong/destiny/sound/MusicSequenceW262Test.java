package kim.biryeong.destiny.sound;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.sound.MusicSequence.Scene.*;
import java.util.List;

class MusicSequenceW262Test {
    final MusicSequence.Track a = new MusicSequence.Track("a", 10, .5f);
    final MusicSequence.Track b = new MusicSequence.Track("b", 5, .5f);
    final List<MusicSequence.Track> tracks = List.of(a, b);
    final MusicSequence state = new MusicSequence();
    @Test void waitsForPackAndStartsOnlyOnce() {
        assertNull(state.update(TOWER, tracks, false, false, 0).play());
        assertEquals(a, state.update(TOWER, tracks, true, false, 100).play());
        assertNull(state.update(TOWER, tracks, true, false, 101).play());
    }
    @Test void worldExitStopsAndReentryStartsFresh() {
        state.update(TOWER, tracks, true, false, 0);
        assertTrue(state.update(NONE, List.of(), true, false, 1).stop());
        assertFalse(state.update(NONE, List.of(), true, false, 2).stop());
        assertEquals(a, state.update(TOWER, tracks, true, false, 3).play());
    }
    @Test void matchTransitionReplacesThenStopsForCombat() {
        state.update(TOWER, tracks, true, false, 0);
        var intro = state.update(INTRO, List.of(b), true, false, 1);
        assertTrue(intro.stop()); assertEquals(b, intro.play());
        assertTrue(state.update(NONE, List.of(), true, false, 2).stop());
        assertEquals(b, state.update(RESULTS, List.of(b), true, false, 3).play());
    }
    @Test void towerWaitsForApiCompletionThenLoopsWithGap() {
        state.update(TOWER, tracks, true, false, 0);
        assertNull(state.update(TOWER, tracks, true, false, 9_999_999_999L).play());
        assertTrue(state.update(TOWER, tracks, true, true, 10_000_000_000L).stop());
        assertNull(state.update(TOWER, tracks, true, false, 12_999_999_999L).play());
        assertEquals(b,state.update(TOWER, tracks, true, false, 13_000_000_000L).play());
        assertTrue(state.update(TOWER, tracks, true, true, 18_000_000_000L).stop());
        assertEquals(a,state.update(TOWER, tracks, true, false, 21_000_000_000L).play());
    }
    @Test void oneShotNeverRepeatsWithinSameScene() {
        state.update(INTRO, tracks, true, false, 0);
        assertTrue(state.update(INTRO, tracks, true, true, 10_000_000_000L).stop());
        assertNull(state.update(INTRO, tracks, true, false, 100_000_000_000L).play());
    }
    @Test void packReplacementStopsUntilReadyAgain() {
        state.update(TOWER, tracks, true, false, 0);
        assertTrue(state.update(TOWER, tracks, false, false, 1).stop());
        assertNull(state.update(TOWER, tracks, false, false, 2).play());
        assertEquals(a,state.update(TOWER, tracks, true, false, 3).play());
    }
    @Test void packReloadDoesNotReplayStartedOrCompletedOneShot() {
        for (var scene : List.of(INTRO, RESULTS)) for (boolean completed : List.of(false, true)) {
            var oneShot = new MusicSequence();
            oneShot.update(scene, tracks, true, false, 0);
            if (completed) oneShot.update(scene, tracks, true, true, 10_000_000_000L);
            oneShot.update(scene, tracks, false, false, 11_000_000_000L);
            assertNull(oneShot.update(scene, tracks, true, false, 12_000_000_000L).play());
            oneShot.update(NONE, List.of(), true, false, 13_000_000_000L);
            assertEquals(a,oneShot.update(scene, tracks, true, false, 14_000_000_000L).play());
        }
    }
    @Test void invalidDurationCannotSpamPlayback() {
        assertThrows(IllegalArgumentException.class, () -> new MusicSequence.Track("a", Double.NaN, .5f));
        assertThrows(IllegalArgumentException.class, () -> new MusicSequence.Track("a", 0, .5f));
    }
}
