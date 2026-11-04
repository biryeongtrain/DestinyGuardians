package kim.biryeong.destiny.hud;

import java.util.ArrayList;
import java.util.List;

/** Bounded world-position snapshots, not a radar or live attacker tracker.
 * Lifetime/merge distance/threshold/pulse are local authored HUD policy, not measured D2 constants. */
public final class IncomingDamageState {
    public static final int CAPACITY=4, HOLD_TICKS=6, LIFE_TICKS=20;
    public static final float CRITICAL_FRACTION=.30f;
    public record Cue(int slot,double x,double z,long tick) {}
    private final Cue[] cues=new Cue[CAPACITY];

    public boolean hit(long now,double victimX,double victimZ,double sourceX,double sourceZ) {
        if(!Double.isFinite(victimX)||!Double.isFinite(victimZ)||!Double.isFinite(sourceX)||!Double.isFinite(sourceZ))return false;
        double dx=sourceX-victimX,dz=sourceZ-victimZ,distance=dx*dx+dz*dz;
        if(!Double.isFinite(distance)||distance<.0001)return false; // No invented direction for co-located/vertical damage.
        expire(now);
        int slot=-1;
        for(int i=0;i<CAPACITY;i++)if(cues[i]!=null) {
            double x=cues[i].x-sourceX,z=cues[i].z-sourceZ;
            if(x*x+z*z<=4) {slot=i;break;}
        }
        if(slot<0)for(int i=0;i<CAPACITY;i++)if(cues[i]==null) {slot=i;break;}
        if(slot<0) {
            slot=0;
            for(int i=1;i<CAPACITY;i++)if(cues[i].tick<cues[slot].tick)slot=i;
        }
        cues[slot]=new Cue(slot,sourceX,sourceZ,now);
        return true;
    }
    private void expire(long now) {
        for(int i=0;i<CAPACITY;i++)if(cues[i]!=null && (now<cues[i].tick || now-cues[i].tick>=LIFE_TICKS))cues[i]=null;
    }
    public List<Cue> cues(long now) {
        expire(now);var result=new ArrayList<Cue>(CAPACITY);
        for(var cue:cues)if(cue!=null)result.add(cue);
        return List.copyOf(result);
    }
    public static int fadeFrame(long now,Cue cue) {
        if(now<cue.tick || now-cue.tick>=LIFE_TICKS)return -1;
        return Math.clamp((int)(now-cue.tick-HOLD_TICKS)*8/(LIFE_TICKS-HOLD_TICKS),0,7);
    }
    /** Clockwise screen bearing: front0, right90, behind180, left-90, using Minecraft yaw. */
    public static float bearing(double dx,double dz,float yaw) {
        if(!Double.isFinite(dx)||!Double.isFinite(dz)||!Float.isFinite(yaw)||(dx==0&&dz==0))return Float.NaN;
        double value=Math.toDegrees(Math.atan2(-dx,dz))-yaw;
        return (float)((value%360+540)%360-180);
    }
    /** Current native HP, not a fabricated Destiny shield pool or a recent-hit requirement. */
    public static int criticalFrame(long now,float healthFraction) {
        if(!Float.isFinite(healthFraction)||healthFraction<=0||healthFraction>CRITICAL_FRACTION)return -1;
        double severity=1-healthFraction/CRITICAL_FRACTION;
        double pulse=Math.sin(Math.floorMod(now/2,12)*Math.PI/6);
        return Math.clamp((int)Math.round(7*(.25+.55*severity+.20*pulse)),0,7);
    }
}
