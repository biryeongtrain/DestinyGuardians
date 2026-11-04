package kim.biryeong.destiny.sound;

/** Pure edge gate for bounded guard one-shots, not a looping audio source.
 * Authored eight-tick retrigger limit prevents rapid sneak/slot-toggle spam. */
public final class SwordGuardAudio {
    public static final int RETRIGGER_TICKS=8;
    private boolean held,played;
    private long lastSample=Long.MIN_VALUE,lastPlayed;

    public boolean sample(long tick,boolean guarding) {
        if(tick<lastSample)return false;
        lastSample=tick;
        boolean rising=guarding&&!held;
        held=guarding;
        if(!rising)return false;
        long elapsed=tick-lastPlayed;
        if(played&&(tick<lastPlayed||(elapsed>=0&&elapsed<RETRIGGER_TICKS)))return false;
        played=true;lastPlayed=tick;return true;
    }

    /** Cancellation releases the edge but retains the owner's anti-spam deadline. */
    public void release() {held=false;}
}
