package kim.biryeong.destiny.fx;

import net.minecraft.world.phys.Vec3;
import java.util.List;

/** Six open energy strands, in raw item model units. Never a solid screen-facing disc. */
final class SuperEnergyGeometry {
    record Strand(Vec3 from, Vec3 to, boolean spark) { }
    private SuperEnergyGeometry() { }
    private static Vec3 p(double x, double y, double z) { return new Vec3(x,y,z); }

    static List<Strand> arc(int tick) {
        double wave = Math.sin(tick * 1.9), spin = Math.cos(tick * 1.3);
        return List.of(
                new Strand(p(9.4,-14,8.8),p(8+wave*2,5,8+spin*2),false),
                new Strand(p(6.6,13,7.2),p(8-wave*2,30,8-spin*2),false),
                new Strand(p(8,-13,8),p(8+1.6*spin,-10,9.6+wave),false),
                new Strand(p(8,28,8),p(8-1.6*spin,25,6.4-wave),false),
                new Strand(p(8,-15.7,8),p(8+wave*1.6,-13.5,8+spin*2.1),false),
                new Strand(p(8,31.7,8),p(8-wave*1.6,29.5,8-spin*2.1),false));
    }

    static List<Strand> bow(int tick) {
        double flutter = .45*Math.sin(tick*.8);
        Vec3 nock = p(16.24,8,8), top = p(11.27,20,8), bottom = p(11.27,-4,8);
        return List.of(
                new Strand(p(7.35,13,8+flutter),top,false),
                new Strand(p(7.35,3,8-flutter),bottom,false),
                new Strand(top,nock,false), new Strand(bottom,nock,false),
                new Strand(nock,nock,true),
                new Strand(p(14+.5*Math.sin(tick*.5),8+2*Math.cos(tick*.4),8+1.7*Math.sin(tick*.4)),nock,false));
    }

    /** Local right/up/forward blocks, six broken shock edges leave the exact shot axis empty. */
    static List<Strand> release(int age) {
        double radius = .23+Math.clamp(age,0,7)*.085, forward = Math.max(0,age)*.045;
        var result = new java.util.ArrayList<Strand>();
        for(int side : new int[]{-1,1}) for(int i=0;i<3;i++) {
            double a = -.85+i*.55, b=a+.36;
            result.add(new Strand(p(side*(.12+radius*Math.cos(a)),radius*Math.sin(a),forward),
                    p(side*(.12+radius*Math.cos(b)),radius*Math.sin(b),forward+.035),false));
        }
        return List.copyOf(result);
    }
}
