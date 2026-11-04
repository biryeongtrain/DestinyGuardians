package kim.biryeong.destiny.weapon;

/** Refreshable precision-hit window. Read-only queries never extend or revive it. */
public final class ArcherTempoCycle {
    public static final int DURATION = 60;
    private long until = -1;
    public void precisionHit(long tick) {
        until = tick >= 0 && tick <= Long.MAX_VALUE-DURATION ? tick+DURATION : -1;
    }
    public int remaining(long tick) {
        return tick >= 0 && until > tick && until-tick <= DURATION ? (int)(until-tick) : 0;
    }
}
