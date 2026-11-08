package kim.biryeong.destiny.strike.devils;

/**
 * Holds the briefing (landing cast, music and Zavala's opening line) until the fireteam can actually see it.
 * <p>
 * The finder's launch curtain keeps each Guardian in the dark until the instance is loaded, then fades in over about a
 * second. The run is already {@code RUNNING} while that happens, so starting the briefing at once spoke the first
 * seconds of Zavala's 22-second line into a black screen. The gate waits for the curtain to lift, then a short beat,
 * and a run that was never dark (operator command) starts immediately. A curtain that never lifts cannot hold the run
 * forever: {@link #TIMEOUT} ticks after the run began the briefing starts anyway.
 */
final class DevilsBriefingGate {
    /** Silence between the picture returning and the first note/word. */
    static final int BEAT = 20;
    static final int TIMEOUT = 400;

    private final long since;
    private boolean sawDark;
    private long litSince = -1;

    DevilsBriefingGate(long now) { since = now; }

    /** @param dark any member is still under the launch curtain this tick. */
    boolean ready(long now, boolean dark) {
        if (now - since >= TIMEOUT) return true;
        if (dark) { sawDark = true; litSince = -1; return false; }
        if (!sawDark) return true;
        if (litSince < 0) litSince = now;
        return now - litSince >= BEAT;
    }
}
