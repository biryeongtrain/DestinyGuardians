package kim.biryeong.destiny.weapon;

/** Pure, bounded W350 intrinsic rules. DDC Exotic Weapons rows 16/39/50/83/90/104/130/148/152.
 * Unspecified ranges, flight speeds, MC HP scaling and work budgets are local port policy. */
public final class ExoticCycleW350 {
    private ExoticCycleW350() {}
    public static final int WHITE_NAIL_WINDOW = 50;
    public static final int SOUL_INITIAL = 140, SOUL_MAX = 220;
    public static final int PACK_TICKS = 300, SCIENCE_TICKS = 100;
    public static final class PrecisionChain {
        private long last = Long.MIN_VALUE;
        private int hits;
        public boolean confirmed(long now, boolean precision, float actual) {
            if (!(actual > 0) || !Float.isFinite(actual)) return false;
            if (!precision) { clear(); return false; }
            if (now < last || last == Long.MIN_VALUE || now - last > WHITE_NAIL_WINDOW) hits = 0;
            last = now;
            if (++hits < 3) return false;
            clear(); return true;
        }
        public void clear() { last = Long.MIN_VALUE; hits = 0; }
        public int hits() { return hits; }
    }
    public static final class RapidHits {
        private long last = Long.MIN_VALUE;
        private int hits;
        /** DDC's 1? second gap is unverified; a 20-tick local bound, not an original constant. */
        public boolean confirmed(long now) {
            if (last == Long.MIN_VALUE || now < last || now-last > 20) hits = 0;
            last = now;
            if (++hits < 12) return false;
            hits = 0; return true;
        }
    }
    public static long extendSoul(long now, long previous) {
        return now + Math.min(SOUL_MAX, Math.max(0, previous-now) + SOUL_INITIAL);
    }
    public static float parasitism(int count, boolean pvp) {
        int n = Math.clamp(count,0,100);
        if (pvp) {
            // DDC values beyond four are unknown. Cap at the last sourced 75% PvP bonus.
            return 1 + switch (Math.min(n,4)) { case 1 -> .15f; case 2 -> .30f; case 3 -> .45f; case 4 -> .75f; default -> 0; };
        }
        return 1 + Math.min(3f, Math.min(n,5)*.30f + Math.max(0,n-5)*.021f);
    }
    /** Scalar ledger: refresh holds for2.3s, then decays25 stacks/s, 100 triggers ignition. */
    public static final class Scorch {
        private double stacks;
        private long last, decayAt, nextPulse, immuneUntil;
        private int pulses;
        public boolean add(long now,int amount) {
            advance(now);
            if(now<immuneUntil||amount<=0)return false;
            if(stacks<=0){nextPulse=now+10;pulses=0;}
            stacks=Math.min(100,stacks+amount);last=now;decayAt=now+46;
            if(stacks<100)return false;
            stacks=0;immuneUntil=now+32;return true;
        }
        private void advance(long now) {
            if(now<last){stacks=0;immuneUntil=0;}
            if(now>decayAt&&stacks>0)stacks=Math.max(0,stacks-(now-Math.max(last,decayAt))*1.25);
            last=now;
        }
        public boolean pulse(long now) {
            advance(now);
            if(stacks<=0||now<nextPulse)return false;
            nextPulse=now+(++pulses==1?19:12); // .93s second delay, .56s later: ceil20TPS.
            return true;
        }
        public int stacks(long now){advance(now);return (int)Math.ceil(stacks);}
        public boolean expired(long now){return stacks(now)<=0&&now>=immuneUntil;}
    }
    public static float gravitonBolt(int index) { return index == 0 ? .85f : 1.353f; }
    public static boolean packEligible(boolean sameLevel, boolean alive, boolean opponent, boolean allied, boolean legendaryRocket) {
        return sameLevel && alive && !opponent && allied && legendaryRocket;
    }
    public static boolean mulligan(boolean hit, int roll) { return !hit && roll >= 0 && roll < 20; }
}
