package kim.biryeong.destiny.weapon;

import java.util.*;

/** Deterministic local geometry for source-backed qualitative frame shapes.
 * Image-informed estimated coordinates/aspect ratios remain local Minecraft tuning, not recovered D2 engine coordinates. */
public final class ShotgunSpread {
    public enum Shape { CONE, VERTICAL_OVAL, DIAMOND, SQUARE, SLUG }
    public record Point(double x,double y) {}
    public record Vector(double x,double y,double z) {
        public double length() {return Math.hypot(Math.hypot(x,y),z);}
        private boolean finite() {return Double.isFinite(x)&&Double.isFinite(y)&&Double.isFinite(z);}
        private Vector scale(double s) {return new Vector(x*s,y*s,z*s);}
        private Vector cross(Vector b) {return new Vector(y*b.z-z*b.y,z*b.x-x*b.z,x*b.y-y*b.x);}
    }
    private static final Vector ZERO=new Vector(0,0,0);
    private static final Map<Shape,List<Point>> OFFSETS=create();
    private ShotgunSpread() {}
    private static Map<Shape,List<Point>> create() {
        var result=new EnumMap<Shape,List<Point>>(Shape.class);
        // Symmetrized estimates of impact centers in Bungie's S19 250px illustrations,
        // using a common authored 80px normalization. These are NOT exact engine coordinates.
        result.put(Shape.CONE,List.of(new Point(0,0),
                new Point(-.35,.35),new Point(.35,.35),new Point(.35,-.35),new Point(-.35,-.35),
                new Point(0,1),new Point(.78,.62),new Point(.97,-.22),new Point(.43,-.90),
                new Point(-.43,-.90),new Point(-.97,-.22),new Point(-.78,.62)));
        result.put(Shape.VERTICAL_OVAL,List.of(new Point(-.22,1),new Point(.22,1),
                new Point(.48,.48),new Point(.61,0),new Point(.48,-.48),new Point(.22,-1),
                new Point(-.22,-1),new Point(-.48,-.48),new Point(-.61,0),new Point(-.48,.48),
                new Point(0,.32),new Point(0,-.32)));
        result.put(Shape.DIAMOND,List.of(new Point(0,.85),new Point(1,0),new Point(0,-.85),new Point(-1,0),
                new Point(.49,.49),new Point(.49,-.49),new Point(-.49,-.49),new Point(-.49,.49),
                new Point(0,.38),new Point(.38,0),new Point(0,-.38),new Point(-.38,0)));
        result.put(Shape.SQUARE,List.of(new Point(-.60,.60),new Point(0,.60),new Point(.60,.60),
                new Point(.60,0),new Point(.60,-.60),new Point(0,-.60),new Point(-.60,-.60),new Point(-.60,0),
                new Point(-.32,.32),new Point(.32,.32),new Point(.32,-.32),new Point(-.32,-.32)));
        result.put(Shape.SLUG,List.of(new Point(0,0)));
        return Collections.unmodifiableMap(result);
    }
    public static List<Point> offsets(Shape shape) {return OFFSETS.get(Objects.requireNonNull(shape));}
    /** Stable local right/up basis, including a defined exact-vertical fallback. No random yaw/roll. */
    public static Vector direction(Vector forward,Point offset,double tangentSpread) {
        if(forward==null||!forward.finite())return ZERO;
        double n=forward.length();if(!Double.isFinite(n)||n<1e-12)return ZERO;
        var f=forward.scale(1/n);
        if(offset==null||!Double.isFinite(offset.x)||!Double.isFinite(offset.y)
                ||!Double.isFinite(tangentSpread)||tangentSpread<=0)return f;
        var right=f.cross(new Vector(0,1,0));double width=right.length();
        right=width<1e-12?new Vector(1,0,0):right.scale(1/width);
        var up=right.cross(f);double x=offset.x*tangentSpread,y=offset.y*tangentSpread;
        var d=new Vector(f.x+right.x*x+up.x*y,f.y+right.y*x+up.y*y,f.z+right.z*x+up.z*y);
        double length=d.length();return d.finite()&&Double.isFinite(length)&&length>0?d.scale(1/length):f;
    }
}
