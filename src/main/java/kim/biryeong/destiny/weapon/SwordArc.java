package kim.biryeong.destiny.weapon;

/** Authored Minecraft spatial tuning, not measured Destiny angles/ranges or animation frames. */
public final class SwordArc {
    public static final double LIGHT_RANGE=3.5, LIGHT_COS=Math.cos(Math.toRadians(65)), LIGHT_HEIGHT=1.5;
    public static final double LUNGE_RANGE=5.3, LUNGE_COS=Math.cos(Math.toRadians(35)), LUNGE_HEIGHT=1.25;
    public static final double LUNGE_MAX=1.8, LUNGE_STOP=1.1;
    /** Legacy short-step value retained for existing authored callers; live light attacks use attackStep. */
    public static final double STEP=0.9;
    /** W329 user-requested Minecraft tuning, not extracted Destiny displacement. */
    public static final double GROUND_STEP=2, AIR_STEP=5;
    public static double attackStep(boolean grounded) { return grounded ? GROUND_STEP : AIR_STEP; }
    public static final int MAX_CANDIDATES=64, MAX_HITS=16;
    private SwordArc() {}
    /** Yaw-based slash/acquisition cone plus independent body-height tolerance. */
    public static boolean inside(double forwardX,double forwardZ,double dx,double dy,double dz,
                                 double range,double cosine,double height) {
        if(!Double.isFinite(forwardX)||!Double.isFinite(forwardZ)||!Double.isFinite(dx)||!Double.isFinite(dy)
                ||!Double.isFinite(dz)||!Double.isFinite(range)||!Double.isFinite(cosine)||!Double.isFinite(height)
                ||range<=0||range>8||height<0||height>4||cosine<0||cosine>1||Math.abs(dy)>height)return false;
        double length=Math.hypot(forwardX,forwardZ),distance=Math.hypot(dx,dz);
        if(length<1e-8||distance>range+1e-8)return false;
        if(distance<1e-8)return true; // Co-located body contact, not an undefined angle.
        return forwardX/length*(dx/distance)+forwardZ/length*(dz/distance)+1e-8>=cosine;
    }
    public static double lungeDistance(double distance) {
        return !Double.isFinite(distance)||distance<0?0:Math.clamp(distance-LUNGE_STOP,0,LUNGE_MAX);
    }
}
