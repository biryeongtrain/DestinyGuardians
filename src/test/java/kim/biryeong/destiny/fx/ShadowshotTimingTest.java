package kim.biryeong.destiny.fx;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ShadowshotTimingTest {
    @Test void noArrowBeforeRequest() {
        var draw = new ShadowshotTiming();
        for (int i = 0; i < 100; i++) assertFalse(draw.advance());
        assertFalse(draw.drawn());
    }

    @Test void releaseHappensOnceAtContactNotAtButtonPress() {
        var draw = new ShadowshotTiming();
        assertTrue(draw.request());
        assertFalse(draw.request(), "Repeated input cannot restart or duplicate the shot");
        for (int tick = 1; tick < ShadowshotTiming.RELEASE_TICKS; tick++) {
            assertFalse(draw.advance());
            assertEquals(tick >= ShadowshotTiming.DRAW_TICKS, draw.drawn());
        }
        assertTrue(draw.advance());
        assertFalse(draw.drawn(), "Nocked arrow must vanish at release");
        for (int i = 0; i < 100; i++) assertFalse(draw.advance());
        assertFalse(draw.request());
    }

    @Test void independentDrawsDoNotShareProgress() {
        var first = new ShadowshotTiming();
        var second = new ShadowshotTiming();
        first.request(); second.request();
        for (int i = 0; i < ShadowshotTiming.RELEASE_TICKS; i++) first.advance();
        assertFalse(second.drawn());
        for (int i = 1; i < ShadowshotTiming.RELEASE_TICKS; i++) assertFalse(second.advance());
        assertTrue(second.advance());
    }
}
