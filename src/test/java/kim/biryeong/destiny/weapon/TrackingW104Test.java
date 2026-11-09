package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.util.Random;
import static org.junit.jupiter.api.Assertions.*;
import kim.biryeong.destiny.weapon.TrackingSteering.Vector;

/** Independent numeric oracles for authored bounded turning; no Minecraft bootstrap, fake
 * projectile or claim that this equation/rate was measured from Destiny 2. */
class TrackingW104Test {
    // Frozen pre-W327 roster assertions retain their original counts; new identities have separate coverage.
    private static final double EPS = 2e-10;
    private static final Vector ZERO = new Vector(0,0,0);
    private static double norm(Vector v) { return Math.hypot(Math.hypot(v.x(),v.y()),v.z()); }
    private static Vector scale(Vector v,double n) { return new Vector(v.x()*n,v.y()*n,v.z()*n); }
    private static Vector unit(Vector v) { return scale(v,1/norm(v)); }
    /** atan2(cross,dot), independent of production's acos/Rodrigues implementation. */
    private static double angle(Vector a,Vector b) {
        Vector x=unit(a), y=unit(b);
        double cx=x.y()*y.z()-x.z()*y.y(), cy=x.z()*y.x()-x.x()*y.z(), cz=x.x()*y.y()-x.y()*y.x();
        return Math.atan2(Math.hypot(Math.hypot(cx,cy),cz),x.x()*y.x()+x.y()*y.y()+x.z()*y.z());
    }
    private static void finite(Vector v) {
        assertNotNull(v); assertTrue(Double.isFinite(v.x())); assertTrue(Double.isFinite(v.y()));
        assertTrue(Double.isFinite(v.z())); assertTrue(Double.isFinite(norm(v)));
    }
    private static void vector(Vector expected,Vector actual,double epsilon) {
        finite(actual); assertEquals(expected.x(),actual.x(),epsilon);
        assertEquals(expected.y(),actual.y(),epsilon); assertEquals(expected.z(),actual.z(),epsilon);
    }
    private static void conserved(Vector before,Vector after) {
        finite(after); double speed=norm(before), tolerance=Math.max(1e-14,speed*4e-15);
        assertEquals(speed,norm(after),tolerance,"Steering preserves paid projectile speed");
        assertTrue(norm(after)<=speed+tolerance,"Never accelerates beyond floating-point tolerance");
    }

    @Test void vectorLengthUsesStableHypotAndLiteralAxisTurnIsNotAUnitSpeedRewrite() {
        assertEquals(13,new Vector(3,4,12).length(),0);
        assertTrue(Double.isFinite(new Vector(1e200,1e200,0).length()));
        Vector source=new Vector(2.2,0,0);
        Vector result=TrackingSteering.turn(source,new Vector(0,50,0),Math.PI/6);
        vector(new Vector(2.2*Math.sqrt(3)/2,1.1,0),result,EPS);
        conserved(source,result); assertEquals(Math.PI/6,angle(source,result),EPS);
    }

    @Test void clockwiseOtherPlanesHaveIndependentLiteralAnswers() {
        vector(new Vector(0,3,Math.sqrt(3)*3),TrackingSteering.turn(new Vector(0,6,0),new Vector(0,0,1),Math.PI/3),EPS);
        vector(new Vector(4/Math.sqrt(2),0,-4/Math.sqrt(2)),
                TrackingSteering.turn(new Vector(4,0,0),new Vector(0,0,-10),Math.PI/4),EPS);
    }

    @Test void alreadyAlignedOrShorterThanBudgetNeverOvershoots() {
        Vector v=new Vector(-2,3,6);
        vector(v,TrackingSteering.turn(v,scale(v,10),.4),EPS);
        Vector source=new Vector(7,0,0), target=new Vector(Math.cos(.01),Math.sin(.01),0);
        Vector out=TrackingSteering.turn(source,target,.1);
        vector(scale(target,7),out,EPS); assertEquals(0,angle(out,target),EPS); conserved(source,out);
    }

    @Test void antiparallelFallbackIsDeterministicBoundedAndPerpendicularAtQuarterTurn() {
        for (Vector v:new Vector[]{new Vector(2,0,0),new Vector(0,-3,0),new Vector(0,0,4),new Vector(1,2,3)}) {
            Vector desired=scale(v,-20), result=TrackingSteering.turn(v,desired,Math.PI/2);
            assertEquals(result,TrackingSteering.turn(v,desired,Math.PI/2));
            conserved(v,result); assertEquals(Math.PI/2,angle(v,result),EPS);
            assertEquals(Math.PI/2,angle(result,desired),EPS);
        }
    }

    @Test void nearlyParallelAndAntiparallelRemainFiniteAndImproveWithoutOvershoot() {
        Vector v=new Vector(2.2,0,0);
        for (Vector desired:new Vector[]{new Vector(1,1e-8,0),new Vector(-1,1e-8,0),
                new Vector(-1,-1e-8,0),new Vector(-1,0,1e-14),new Vector(1,0,1e-14)}) {
            double limit=.03; Vector out=TrackingSteering.turn(v,desired,limit);
            conserved(v,out); assertTrue(angle(v,out)<=limit+EPS);
            assertTrue(angle(out,desired)<=angle(v,desired)+EPS);
            if(angle(v,desired)>limit+EPS) assertEquals(limit,angle(v,out),EPS);
        }
    }

    @Test void fiveHundredSeededDirectionsUseIndependentAngularOracleAndScaleInvariance() {
        Random random=new Random(0x1045eedL);
        for(int i=0;i<500;i++) {
            Vector direction=new Vector(random.nextDouble()*2-1,random.nextDouble()*2-1,random.nextDouble()*2-1);
            Vector desired=new Vector(random.nextDouble()*2-1,random.nextDouble()*2-1,random.nextDouble()*2-1);
            double speed=Math.pow(10,random.nextDouble()*8-4), limit=.0001+random.nextDouble()*.8;
            Vector v=scale(unit(direction),speed), out=TrackingSteering.turn(v,desired,limit);
            conserved(v,out);
            double before=angle(v,desired), turned=angle(v,out), remaining=angle(out,desired);
            assertEquals(Math.min(before,limit),turned,EPS,"Independent bounded turn case "+i);
            assertEquals(Math.max(0,before-limit),remaining,EPS,"Shortest arc without overshoot case "+i);
            Vector scaled=TrackingSteering.turn(v,scale(desired,317),limit);
            assertEquals(0,angle(out,scaled),EPS,"Target distance cannot change desired direction");
        }
    }

    @Test void repeatedTurnsConvergeAtFixedSpeedAndStopAtDirection() {
        Vector velocity=new Vector(0,0,2.2), desired=new Vector(-1,.5,-2);
        double initial=angle(velocity,desired), step=.047;
        for(int i=1;i<=100;i++) {
            Vector before=velocity; velocity=TrackingSteering.turn(velocity,desired,step);
            conserved(before,velocity); assertTrue(angle(before,velocity)<=step+EPS);
            assertEquals(Math.max(0,initial-i*step),angle(velocity,desired),EPS);
        }
        vector(scale(unit(desired),2.2),velocity,EPS);
    }

    @Test void zeroNegligibleOrInvalidVelocityFailsClosedWithoutNanFlight() {
        Vector good=new Vector(1,2,3);
        for(Vector v:new Vector[]{null,ZERO,new Vector(Double.MIN_VALUE,0,0),new Vector(1e-13,0,0),
                new Vector(Double.NaN,1,2),new Vector(1,Double.POSITIVE_INFINITY,2),
                new Vector(1,2,Double.NEGATIVE_INFINITY),new Vector(Double.MAX_VALUE,Double.MAX_VALUE,0)})
            assertEquals(ZERO,TrackingSteering.turn(v,good,.1));
        Vector threshold=new Vector(1e-12,0,0);
        vector(new Vector(0,1e-12,0),TrackingSteering.turn(threshold,new Vector(0,1,0),Math.PI),1e-26);
    }

    @Test void missingInvalidOrNegligibleDesiredDoesNotSteer() {
        Vector v=new Vector(2.2,-.25,.7);
        for(Vector desired:new Vector[]{null,ZERO,new Vector(Double.MIN_NORMAL,0,0),new Vector(0,1e-13,0),
                new Vector(Double.NaN,0,0),new Vector(0,Double.POSITIVE_INFINITY,0),
                new Vector(0,0,Double.NEGATIVE_INFINITY),new Vector(Double.MAX_VALUE,Double.MAX_VALUE,0)})
            assertEquals(v,TrackingSteering.turn(v,desired,.1));
    }

    @Test void invalidAndNonPositiveAnglesCannotSteerWhilePiOrLargerAligns() {
        Vector v=new Vector(2.2,0,0), desired=new Vector(-1,2,-3);
        for(double bad:new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY,
                -Double.MAX_VALUE,-.01,-0.0,0}) assertEquals(v,TrackingSteering.turn(v,desired,bad));
        for(double large:new double[]{Math.PI,2*Math.PI,Double.MAX_VALUE}) {
            Vector out=TrackingSteering.turn(v,desired,large);
            conserved(v,out); vector(scale(unit(desired),2.2),out,EPS);
        }
        assertTrue(angle(v,TrackingSteering.turn(v,desired,Double.MIN_VALUE))<=EPS);
    }

    @Test void veryLargeFiniteAndVerySmallAdmittedSpeedsStayFiniteAndBounded() {
        for(double speed:new double[]{1e-12,1e-9,1e150,1e300}) {
            Vector v=new Vector(speed,0,0), out=TrackingSteering.turn(v,new Vector(0,0,-1),.2);
            conserved(v,out); assertEquals(.2,angle(v,out),EPS);
        }
    }

    @Test void exactOfficialIntrinsicAndOptionalSocketRosterIsImmutableAndNotBlanketRocketTracking() {
        assertEquals("tracking_module",TrackingProfile.ID);
        assertEquals(3977735242L,TrackingProfile.HASH);
        assertEquals(3419274965L,TrackingProfile.INTRINSIC_HASH);
        var expected=java.util.List.of(
                new WeaponPerks.Roll("bad_omens",991314988L,3,3977735242L,457210958L),
                new WeaponPerks.Roll("bellowing_giant",2186258845L,3,3977735242L,2605036073L));
        assertEquals(expected,TrackingProfile.rolls());
        assertThrows(UnsupportedOperationException.class,()->TrackingProfile.rolls().clear());
        assertFalse(TrackingProfile.supportsIntrinsic(null));
        for(var e:WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id()) && !WeaponExotics.expanded(e)).toList())
            assertEquals(e.id().equals("pyroclastic_flow"),TrackingProfile.supportsIntrinsic(e),e.id());
        assertEquals(4,WeaponCatalog.family("rocket_launcher").stream().filter(e -> !LegendaryWeapons.contains(e.id()) && !WeaponExotics.expanded(e)).count());
        assertTrue(TrackingProfile.rolls().stream().noneMatch(r->r.perkHash()==406461158L));
    }

    @Test void authoredTuningIsExplicitAndIndependentOfUnknownSourceNumbers() throws Exception {
        assertEquals(20,TrackingProfile.ACQUIRE_TICKS);
        assertEquals(64d,TrackingProfile.RANGE,0);
        assertEquals(8d,TrackingProfile.CONE_DEGREES,0);
        assertEquals(Math.PI/60,TrackingProfile.TURN_RADIANS,1e-16);
        assertEquals(.95f,TrackingProfile.MIN_ADS,0);
        var d=com.google.gson.JsonParser.parseString(java.nio.file.Files.readString(
                java.nio.file.Path.of("src/main/resources/destiny/weapons/w104-tracking.json"))).getAsJsonObject();
        var rules=d.getAsJsonObject("sourceRules");
        assertTrue(rules.get("requiresAim").getAsBoolean());
        assertTrue(rules.get("continuousAimAfterLaunchRequired").isJsonNull());
        var unknown=rules.getAsJsonObject("unknownSourceRules");
        var names=java.util.Set.of("acquireSeconds","acquireTicks","acquireConeDegrees","acquireRangeMetres",
                "turnDegreesPerSecond","turnDegreesPerTick","releaseAimGraceSeconds","releaseAimGraceTicks",
                "breakTrackingOnMidflightLineOfSightLoss","midflightLossConeDegrees","midflightLossTimeoutSeconds",
                "reacquireAfterDeadOrInvalidTarget","lockSnapshotAtLaunch","trackingPersistsAfterWeaponStow",
                "trackingPersistsAfterTraitEdit","precisionAndModuleUseIdenticalTuning","pvpTrackingMultiplier");
        assertEquals(names,unknown.keySet());
        for(String key:names)assertTrue(unknown.get(key).isJsonNull(),key+" remains unmeasured, not a numeric source default");
        assertTrue(d.getAsJsonObject("intrinsic").get("requiresAim").getAsBoolean());
        assertTrue(d.getAsJsonObject("perk").get("requiresAim").getAsBoolean());
        assertFalse(d.getAsJsonObject("perk").get("enhancedImplemented").getAsBoolean());
    }

}
