package kim.biryeong.destiny.fx;

/** Implemented only on BetterModel trackers by our 3.5.1-specific mixin.
 * Taking ownership leaves unrelated BetterModel models on their normal scheduler.
 */
public interface ServerAnimationClock {
    void destiny$claimServerClock();
    void destiny$primeAnimation();
    void destiny$advanceServerTick();
    long destiny$serverFrames();
}
