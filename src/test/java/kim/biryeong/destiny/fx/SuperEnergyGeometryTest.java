package kim.biryeong.destiny.fx;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class SuperEnergyGeometryTest {
    @Test void sixFiniteStrandsStayBoundedAndArcActuallyFlickers() {
        for(int t=0;t<420;t++) for(var frame:java.util.List.of(SuperEnergyGeometry.arc(t),SuperEnergyGeometry.bow(t))) {
            assertEquals(6,frame.size());
            for(var strand:frame) for(var p:java.util.List.of(strand.from(),strand.to())) {
                assertTrue(Double.isFinite(p.x)&&Double.isFinite(p.y)&&Double.isFinite(p.z));
                assertTrue(p.x>=-16&&p.x<=32&&p.y>=-16&&p.y<=32&&p.z>=-16&&p.z<=32);
            }
        }
        assertNotEquals(SuperEnergyGeometry.arc(0),SuperEnergyGeometry.arc(1));
        // Long strands stand outside the opaque shaft rather than hiding inside its core.
        for(int i=0;i<2;i++) {
            var p=SuperEnergyGeometry.arc(0).get(i).from();
            assertTrue(Math.hypot(p.x-8,p.z-8)>1.5);
        }
    }
    @Test void voidTautStringsMeetActualH22NockAndPulseDoesNotReplaceGeometry() {
        for(int t=0;t<40;t++) {
            var frame=SuperEnergyGeometry.bow(t);
            assertEquals(new net.minecraft.world.phys.Vec3(16.24,8,8),frame.get(2).to());
            assertEquals(frame.get(2).to(),frame.get(3).to());
            assertEquals(frame.get(4).from(),frame.get(2).to());
            assertTrue(frame.get(4).spark());
            assertEquals(new net.minecraft.world.phys.Vec3(11.27,20,8),frame.get(2).from());
            assertEquals(new net.minecraft.world.phys.Vec3(11.27,-4,8),frame.get(3).from());
        }
    }
    @Test void releaseExpandsButLeavesTheShotAxisOpen() {
        for(int age=0;age<8;age++) {
            var frame=SuperEnergyGeometry.release(age);assertEquals(6,frame.size());
            for(var strand:frame) for(var p:java.util.List.of(strand.from(),strand.to())) {
                assertTrue(Math.abs(p.x)>.1);assertTrue(p.length()<1.3);
                assertFalse(strand.spark());
            }
        }
        assertTrue(SuperEnergyGeometry.release(7).getFirst().from().length()>SuperEnergyGeometry.release(0).getFirst().from().length());
    }
}
