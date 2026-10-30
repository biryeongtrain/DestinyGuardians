package kim.biryeong.destiny.crucible;

import org.junit.jupiter.api.Test;

import static kim.biryeong.destiny.crucible.CrucibleUiTimeline.*;
import static org.junit.jupiter.api.Assertions.*;

class CrucibleUiTimelineTest {
    @Test void segmentsAdvanceInOrder() {
        assertEquals(Segment.LETTERBOX_IN, segment(0, 400));
        assertEquals(Segment.TITLE, segment(TITLE_START, 400));
        assertEquals(Segment.ROSTER, segment(ROSTER_START, 400));
        assertEquals(Segment.COUNTDOWN, segment(400 - COUNTDOWN_TICKS, 400));
    }
    @Test void countdownDigitsCountDownToGo() {
        assertEquals(5, countdownDigit(100));
        assertEquals(1, countdownDigit(20));
        assertEquals(1, countdownDigit(1));
        assertEquals(0, countdownDigit(0));
    }
    @Test void barAndDiamondMath() {
        assertEquals(0f, fillWidth(0, 150));
        assertEquals(BAR_W, fillWidth(150, 150));
        assertEquals(BAR_W, fillWidth(999, 150));
        assertEquals(0, diamondFrame(0));
        assertEquals(10, diamondFrame(1));
        assertTrue(barX(-1) < SCREEN_W / 2 && barX(1) > SCREEN_W / 2);
        assertEquals(zoneX(1), SCREEN_W / 2);
    }
    @Test void textWidthEstimateGrowsWithHangul() {
        assertTrue(CrucibleUi.estimateWidth("가나", 20) > CrucibleUi.estimateWidth("ab", 20));
    }
}
