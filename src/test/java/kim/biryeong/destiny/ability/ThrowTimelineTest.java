package kim.biryeong.destiny.ability;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class ThrowTimelineTest {
 @Test void delayedReleaseHappensOnceEvenWithDuplicateTicks() {
  var t=new ThrowTimeline(100,6,20);assertFalse(t.release(105,true));assertTrue(t.release(106,true));
  assertFalse(t.release(106,true));assertFalse(t.release(107,true));assertFalse(t.finished(119));assertTrue(t.finished(120));
 }
 @Test void cancelledWindupNeverEmitsWhenOldCallbackBecomesValidAgain() {
  var t=new ThrowTimeline(0,6,20);assertFalse(t.release(3,false));assertFalse(t.release(6,true));assertTrue(t.finished(6));
 }
 @Test void expiredWindupDoesNotFireOnStaleTick() {
  var t=new ThrowTimeline(0,6,20);assertFalse(t.release(22,true));assertFalse(t.emitted());assertTrue(t.finished(22));
 }
 @Test void catchesUpMissedReleaseBeforeRecoveryEnds() {
  var t=new ThrowTimeline(0,6,20);assertTrue(t.release(9,true));assertFalse(t.release(7,true));
 }
}
