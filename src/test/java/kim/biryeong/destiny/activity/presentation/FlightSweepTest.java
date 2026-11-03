package kim.biryeong.destiny.activity.presentation;

import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaterniond;
import org.joml.Vector3d;
import org.junit.jupiter.api.Test;
import java.util.List;
import java.util.Random;
import static org.junit.jupiter.api.Assertions.*;

class FlightSweepTest {
    private static FlightSweep.Pose pose(Vec3 at, Quaterniond q) { return new FlightSweep.Pose(at,q); }

    @Test void catchesTurningNoseBetweenClearEndpoints() {
        var hull=new AABB(-.2,-.2,0,.2,.2,10);
        var a=pose(Vec3.ZERO,new Quaterniond().rotationY(-Math.PI/4));
        var b=pose(Vec3.ZERO,new Quaterniond().rotationY(Math.PI/4));
        // At either endpoint z<=7.22; at mid-turn the nose reaches z=10.
        var obstacle=new AABB(-.1,-.1,9.5,.1,.1,10.5);
        assertTrue(FlightSweep.between(hull,a,b).intersects(obstacle));
    }

    @Test void boundsInterpolatedCornersIncludingOffCenterHullAndTranslation() {
        var random=new Random(26);
        var hull=new AABB(-3,-2,-18,7,5,2);
        for(int trial=0;trial<80;trial++) {
            var a=pose(new Vec3(random.nextDouble()*20,2,-10),
                    new Quaterniond().rotationXYZ(random.nextDouble()*6,random.nextDouble()*6,random.nextDouble()*6));
            var b=pose(new Vec3(-20,random.nextDouble()*20,40),
                    new Quaterniond().rotationXYZ(random.nextDouble()*6,random.nextDouble()*6,random.nextDouble()*6));
            var sweep=FlightSweep.between(hull,a,b);
            for(int step=0;step<=100;step++) {
                double t=step/100.;var q=a.rotation().slerp(b.rotation(),t);var at=a.position().lerp(b.position(),t);
                for(double x:new double[]{hull.minX,hull.maxX})
                    for(double y:new double[]{hull.minY,hull.maxY})
                        for(double z:new double[]{hull.minZ,hull.maxZ}) {
                            var p=q.transform(new Vector3d(x,y,z));
                            assertTrue(sweep.contains(p.x+at.x,p.y+at.y,p.z+at.z),"Escaped sweep at t="+t);
                        }
            }
        }
    }

    @Test void equivalentQuaternionSignsDoNotInflateStraightFlight() {
        var q=new Quaterniond().rotationY(.9);var negative=new Quaterniond(-q.x,-q.y,-q.z,-q.w);
        var hull=new AABB(-1,-1,-1,1,1,1);
        var same=FlightSweep.between(hull,pose(Vec3.ZERO,q),pose(new Vec3(0,10,0),q));
        var opposite=FlightSweep.between(hull,pose(Vec3.ZERO,q),pose(new Vec3(0,10,0),negative));
        assertEquals(same,opposite);
        assertEquals(12,same.getYsize(),1e-6);
    }

    @Test void halfTurnAndStationaryCasesStayBounded() {
        var hull=new AABB(-1,-1,-5,1,1,5);
        var first=pose(Vec3.ZERO,new Quaterniond());
        var second=pose(Vec3.ZERO,new Quaterniond().rotationY(Math.PI));
        assertTrue(FlightSweep.between(hull,first,second).contains(5,0,0));
        var stationary=FlightSweep.corridor(hull,List.of(first));
        assertEquals(1,stationary.size());assertTrue(stationary.getFirst().contains(1,1,5));
        assertThrows(UnsupportedOperationException.class,()->stationary.clear());
    }

    @Test void rejectsInvalidDataAndDefensivelyCopiesRotations() {
        var q=new Quaterniond();var p=pose(Vec3.ZERO,q);q.rotationX(2);
        p.rotation().rotationY(2);assertEquals(new Quaterniond(),p.rotation());
        assertThrows(IllegalArgumentException.class,()->pose(new Vec3(Double.NaN,0,0),new Quaterniond()));
        assertThrows(IllegalArgumentException.class,()->pose(Vec3.ZERO,new Quaterniond(0,0,0,0)));
        assertThrows(IllegalArgumentException.class,()->FlightSweep.corridor(new AABB(0,0,0,0,1,1),List.of(p)));
        assertThrows(IllegalArgumentException.class,()->FlightSweep.corridor(new AABB(0,0,0,1,1,1),List.of()));
    }
}
