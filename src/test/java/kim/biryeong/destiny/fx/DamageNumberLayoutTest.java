package kim.biryeong.destiny.fx;

import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.fx.DamageNumberLayout.*;

class DamageNumberLayoutTest {
    private static final View FRONT=new View(new Point(0,0,0),0,0);
    private static Projected front(double z,boolean crit,int age,double lift,int digits) {
        return project(FRONT,new Point(0,0,z),crit,age,lift,digits).orElseThrow();
    }
    private static boolean overlaps(Box a,Box b,double gap) {
        return Math.abs(a.x()-b.x()) < a.halfWidth()+b.halfWidth()+gap-1e-10
                && Math.abs(a.y()-b.y()) < a.halfHeight()+b.halfHeight()+gap-1e-10;
    }
    @Test void literalFrontProjectionIncludesNativeTextOriginAndConservativeShadowEnvelope() {
        var p=front(7,false,0,0,1);var b=p.box();
        assertEquals(1,p.angularScale());
        assertEquals(-.16375,b.x(),1e-12);assertEquals(.185,b.y(),1e-12);
        assertEquals(.065,b.halfWidth(),1e-12);assertEquals(.08125,b.halfHeight(),1e-12);
        assertEquals(.50375,front(7,false,0,0,10).box().halfWidth(),1e-12);
    }
    @Test void twoIdenticalBodyNumbersGetLiteralSeparateRowsWithoutMergingTheirValues() {
        var b=front(7,false,0,0,1).box();var next=packUp(b,List.of(b),.035);
        assertEquals(b.x(),next.x());assertEquals(.3825,next.y(),1e-12);
        assertEquals(.1975,next.y()-b.y(),1e-12);assertFalse(overlaps(next,b,.035));
        assertEquals(b,front(7,false,0,0,1).box());
    }
    @Test void precisionAndBodyKeepOriginalColumnsWhenTheyAlreadyFit() {
        var white=front(7,false,0,0,1).box();var yellow=front(7,true,0,0,1).box();
        assertEquals(.36,yellow.x()-white.x(),1e-12);
        assertEquals(yellow,packUp(yellow,List.of(white),.035));
        assertEquals(white,packUp(white,List.of(yellow),.035));
    }
    @Test void longSaturatedTenDigitStringsReserveTheirWholeWidthAcrossColumns() {
        var white=front(7,false,0,0,10).box();var yellow=front(7,true,0,0,10).box();
        assertTrue(overlaps(white,yellow,.035));
        var packed=packUp(yellow,List.of(white),.035);
        assertTrue(packed.y()>yellow.y());assertFalse(overlaps(white,packed,.035));
    }
    @Test void differentWorldRangesOnSameSightLineShareLogicalScreenReservations() {
        var near=front(7,false,0,0,1);var far=front(70,false,0,0,1);
        assertEquals(near,far);assertTrue(packUp(far.box(),List.of(near.box()),.035).y()>far.box().y());
        assertEquals(2,front(2,false,0,0,1).angularScale(),1e-12);
        assertEquals(.8,front(120,false,0,0,1).angularScale(),1e-12);
    }
    @Test void currentAgeChangesOccupancyAndLaterLowVacancyIsReused() {
        var base=front(7,false,0,0,1).box();var twoTicks=front(7,false,2,0,1).box();
        assertEquals(.05,twoTicks.y()-base.y(),1e-12);
        assertEquals(.4325,packUp(base,List.of(twoTicks),.035).y(),1e-12);
        var aged=front(7,false,15,0,1).box();assertEquals(base,packUp(base,List.of(aged),.035));
        assertTrue(project(FRONT,new Point(0,0,7),false,16,0,1).isEmpty());
        assertEquals(base,packUp(base,List.of(),.035));
    }
    @Test void sortedSweepFindsLowestGapAndDoesNotMutateOrDependOnInputOrder() {
        var desired=new Box(0,0,.1,.1);var low=new Box(0,.4,.1,.1);var high=new Box(0,1,.1,.1);
        var inputs=new ArrayList<>(List.of(high,low));var copy=List.copyOf(inputs);
        assertEquals(desired,packUp(desired,inputs,.05));assertEquals(copy,inputs);
        var colliding=new Box(0,.35,.1,.1);
        assertEquals(.65,packUp(colliding,inputs,.05).y(),1e-12);
        Collections.reverse(inputs);assertEquals(packUp(colliding,copy,.05),packUp(colliding,inputs,.05));
        assertEquals(colliding,packUp(colliding,List.of(new Box(4,.35,.1,.1)),.05));
    }
    @Test void arbitrarySortedDenseIntervalsNeverRetainAnOverlapOrMoveDownwards() {
        var random=new Random(8100263);
        for(int run=0;run<1000;run++) {
            var desired=new Box(random.nextDouble()-.5,random.nextDouble()-.5,.04+random.nextDouble(),.02+random.nextDouble()*.2);
            var boxes=new ArrayList<Box>();
            for(int i=0;i<23;i++)boxes.add(new Box(random.nextDouble()*3-1.5,random.nextDouble()*5-1,.02+random.nextDouble(),.02+random.nextDouble()*.2));
            var placed=packUp(desired,boxes,.035);
            assertEquals(desired.x(),placed.x());assertTrue(placed.y()>=desired.y());
            for(var other:boxes)assertFalse(overlaps(placed,other,.035));
        }
    }
    @Test void twoComponentRapidHitsRemainSeparatedThroughoutNormalLifetimeAndReuseSlots() {
        record Live(int born,double lift,boolean crit) {}
        var live=new ArrayList<Live>();double maximumLift=0;
        for(int tick=0;tick<1000;tick++) {
            final int now=tick;live.removeIf(n->now-n.born>=16);
            if(tick%2==0)for(int component=0;component<2;component++) {
                boolean crit=component==0&&tick%4==0;
                var desired=front(7,crit,0,0,1);
                var occupied=live.stream().map(n->front(7,n.crit,now-n.born,n.lift,1).box()).toList();
                var placed=packUp(desired.box(),occupied,.035);
                double lift=placed.y()-desired.box().y();maximumLift=Math.max(maximumLift,lift);
                live.add(new Live(tick,lift,crit));
            }
            assertTrue(live.size()<=16);
            for(int i=0;i<live.size();i++)for(int j=i+1;j<live.size();j++) {
                var a=live.get(i);var b=live.get(j);
                assertFalse(overlaps(front(7,a.crit,tick-a.born,a.lift,1).box(),front(7,b.crit,tick-b.born,b.lift,1).box(),.035));
            }
        }
        assertTrue(maximumLift<4,"A long stationary stream does not monotonically climb forever");
    }
    @Test void cameraYawAndPitchProjectionMatchIndependentForwardAndRightGeometry() {
        var normal=front(7,false,0,0,1);
        var west=project(new View(new Point(0,0,0),90,0),new Point(-7,0,0),false,0,0,1).orElseThrow();
        assertEquals(normal.box().x(),west.box().x(),1e-12);assertEquals(normal.box().y(),west.box().y(),1e-12);
        var up=project(new View(new Point(0,0,0),0,-90),new Point(0,7,0),false,0,0,1).orElseThrow();
        assertEquals(normal.box().x(),up.box().x(),1e-12);assertEquals(normal.box().y(),up.box().y(),1e-12);
        var right=project(FRONT,new Point(-1,0,7),false,0,0,1).orElseThrow();
        assertTrue(right.box().x()>.8);
    }
    @Test void invalidOrInvisibleProjectionCreatesNoReservation() {
        for(var point:List.of(new Point(0,0,-7),new Point(0,0,0),new Point(7,0,0),new Point(0,0,.05),new Point(Double.MAX_VALUE,0,Double.MAX_VALUE)))
            assertTrue(project(FRONT,point,false,0,0,1).isEmpty());
        assertTrue(project(null,new Point(0,0,7),false,0,0,1).isEmpty());
        assertTrue(project(FRONT,null,false,0,0,1).isEmpty());
        for(int age:new int[]{-1,16,Integer.MAX_VALUE})assertTrue(project(FRONT,new Point(0,0,7),false,age,0,1).isEmpty());
        for(double lift:new double[]{-1,Double.NaN,Double.POSITIVE_INFINITY})assertTrue(project(FRONT,new Point(0,0,7),false,0,lift,1).isEmpty());
        for(int digits:new int[]{0,11})assertTrue(project(FRONT,new Point(0,0,7),false,0,0,digits).isEmpty());
    }
    @Test void publicValueTypesAndPackingRejectNonfiniteOrUnsafeInputs() {
        assertThrows(IllegalArgumentException.class,()->new Point(Double.NaN,0,0));
        assertThrows(IllegalArgumentException.class,()->new View(null,0,0));
        assertThrows(IllegalArgumentException.class,()->new View(new Point(0,0,0),0,91));
        assertThrows(IllegalArgumentException.class,()->new View(new Point(0,0,0),Double.POSITIVE_INFINITY,0));
        assertThrows(IllegalArgumentException.class,()->new Box(0,0,0,1));
        assertThrows(IllegalArgumentException.class,()->new Box(0,Double.MAX_VALUE,1,Double.MAX_VALUE));
        var box=new Box(0,0,1,1);
        assertThrows(IllegalArgumentException.class,()->packUp(box,List.of(),Double.NaN));
        assertThrows(IllegalArgumentException.class,()->packUp(box,List.of(),-.1));
        assertThrows(IllegalArgumentException.class,()->packUp(null,List.of(),0));
        assertThrows(IllegalArgumentException.class,()->packUp(box,null,0));
    }
    @Test void nearClampFasterRiseCannotCatchAnInitiallyPackedFarNumberBeforeExpiry() {
        // Review regression: existing2blocks(age1) vs new7blocks can be caught later. Age4 already has a lower vacancy.
        var existing=front(2,false,1,0,1);var desired=front(7,false,0,0,1);
        var swept=relativeSweep(existing,1,desired.angularScale());
        assertEquals(.42,existing.box().y(),1e-12);
        assertEquals(.595,swept.y(),1e-12);assertEquals(.3375,swept.halfHeight(),1e-12);
        var placed=packUp(desired.box(),List.of(swept),.035);
        assertEquals(1.04875,placed.y(),1e-12);
        var instantaneous=packUp(desired.box(),List.of(existing.box()),.035);
        double oldLift=instantaneous.y()-desired.box().y();
        assertTrue(overlaps(front(2,false,6,0,1).box(),front(7,false,5,oldLift,1).box(),0));
        double lift=(placed.y()-desired.box().y())/desired.angularScale();
        for(int future=0;future<=14;future++)
            assertFalse(overlaps(front(2,false,1+future,0,1).box(),front(7,false,future,lift,1).box(),.035));
    }
    @Test void mixedNearFarAndBeyondClampStreamsReserveRelativeLifetimeSweeps() {
        record Live(int born,double z,double lift,boolean crit,int digits) {}
        var random=new Random(812001);var live=new ArrayList<Live>();
        double[] ranges={2,3,7,70,120};
        for(int tick=0;tick<500;tick++) {
            final int now=tick;live.removeIf(n->now-n.born>=16);
            for(int component=0;component<2;component++) {
                double z=ranges[random.nextInt(ranges.length)];boolean crit=random.nextBoolean();int digits=1+random.nextInt(4);
                var desired=front(z,crit,0,0,digits);
                var occupied=live.stream().map(n->relativeSweep(front(n.z,n.crit,now-n.born,n.lift,n.digits),now-n.born,desired.angularScale())).toList();
                var placed=packUp(desired.box(),occupied,.035*desired.angularScale());
                live.add(new Live(tick,z,(placed.y()-desired.box().y())/desired.angularScale(),crit,digits));
                if(live.size()>24)live.removeFirst();
            }
            for(int i=0;i<live.size();i++)for(int j=i+1;j<live.size();j++) {
                var a=live.get(i);var b=live.get(j);
                assertFalse(overlaps(front(a.z,a.crit,tick-a.born,a.lift,a.digits).box(),front(b.z,b.crit,tick-b.born,b.lift,b.digits).box(),0));
            }
        }
    }
    @Test void relativeSweepSameVelocityAndLastLiveTickNeedNoExtraEnvelopeAndValidateInputs() {
        var p=front(7,false,0,0,1);
        assertEquals(p.box(),relativeSweep(p,0,1));
        assertEquals(p.box(),relativeSweep(p,15,2));
        assertThrows(IllegalArgumentException.class,()->relativeSweep(null,0,1));
        assertThrows(IllegalArgumentException.class,()->relativeSweep(p,16,1));
        assertThrows(IllegalArgumentException.class,()->relativeSweep(p,0,0));
        assertThrows(IllegalArgumentException.class,()->relativeSweep(p,0,Double.NaN));
        assertThrows(IllegalArgumentException.class,()->relativeSweep(new Projected(p.box(),-1),0,1));
    }

}
