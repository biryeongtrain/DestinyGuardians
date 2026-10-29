package kim.biryeong.destiny.weapon;

import org.joml.Matrix4f;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import org.junit.jupiter.api.Test;

import java.io.InputStreamReader;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/** Pure unit tests: source data, cosmetic clocks and matrices only; no server or GPU bootstrap. */
class WeaponFireMotionW242Test {
    private static final WeaponFireMotion.Pose IDLE = WeaponFireMotion.Pose.IDENTITY;
    private static final Object KEY = "fixture";
    private final Object owner = new Object(), stack = new Object(), level = new Object();

    @Test void realSourceCoversAllSixtyNonSwordWeaponsAndEightyOneFiniteUnitClips() throws Exception {
        try (var in = getClass().getResourceAsStream("/destiny/weapons/w242-fire-motion.json")) {
            assertNotNull(in);
            var library = WeaponFireMotion.Library.read(new InputStreamReader(in, StandardCharsets.UTF_8));
            var expected = new HashSet<String>();
            for (var entry : WeaponCatalog.all()) if (!entry.family().equals("sword")) expected.add(entry.id());
            assertEquals(60, expected.size());
            assertEquals(expected, library.weapons.keySet());
            assertEquals(32, library.groups.size());
            int clips = 0;
            for (var group : library.groups.values()) for (var clip : group.values()) {
                clips++;
                assertEquals(61, clip.samples().size());
                assertTrue(clip.samples().getFirst().neutral());
                assertTrue(clip.samples().getLast().neutral());
                for (var p : clip.samples()) {
                    assertTrue(Float.isFinite(p.x()) && Float.isFinite(p.y()) && Float.isFinite(p.z()));
                    assertEquals(1, p.rotation().lengthSquared(), 1e-5);
                }
            }
            assertEquals(81, clips);
            // Ace ADS starts from an already recoiled raw source frame; exported onset must
            // remain nonzero inside the clip instead of using that first raw frame as neutral.
            var ace = library.weapons.get("ace_of_spades").ads();
            assertTrue(ace.samples().stream().anyMatch(p -> p.rotation().angle() > .1f));
            assertEquals(IDLE, ace.sample(0));
            assertEquals(IDLE, ace.sample(ace.duration()));
        }
    }

    @Test void samplerUsesLinearTranslationAndShortestQuaternionArcWithNeutralEndpoints() {
        var samples = new ArrayList<>(java.util.Collections.nCopies(61, IDLE));
        samples.set(30, pose(.01f, 0, 0, new Quaternionf().rotationY((float)Math.toRadians(170))));
        samples.set(31, pose(.03f, 0, 0, new Quaternionf().rotationY((float)Math.toRadians(-170))));
        var clip = new WeaponFireMotion.Clip(1, samples);
        var halfway = clip.sample(30.5/60);
        assertEquals(.02f, halfway.x(), 1e-6);
        var forward = halfway.rotation().transform(new Vector3f(0, 0, 1));
        assertEquals(-1, forward.z, 1e-5); // Short path crosses 180 degrees, not zero.
        assertEquals(0, forward.x, 1e-5);
        assertEquals(IDLE, clip.sample(-1));
        assertEquals(IDLE, clip.sample(0));
        assertEquals(IDLE, clip.sample(1));
        assertEquals(IDLE, clip.sample(Double.NaN));
        assertTrue(samples.get(30).rotation().equals(clip.samples().get(30).rotation()));
    }

    @Test void adsBlendsAtTheCurrentClockAndLetsDifferentDurationsReturnIndependently() {
        var hip = constant(1, pose(.1f, 0, 0, new Quaternionf().rotationX(.2f)));
        var ads = constant(2, pose(0, .2f, 0, new Quaternionf().rotationY(.4f)));
        var clips = new WeaponFireMotion.Clips(hip, ads);
        var middle = clips.sample(.5, .5f);
        assertEquals(.05f, middle.x(), 1e-6);
        assertEquals(.1f, middle.y(), 1e-6);
        assertTrue(middle.rotation().equals(hip.sample(.5).rotation().slerp(ads.sample(.5).rotation(), .5f), 1e-6f));
        assertEquals(hip.sample(.5), clips.sample(.5, 0));
        assertEquals(ads.sample(.5), clips.sample(.5, 1));
        assertEquals(0, clips.sample(1.2, .5f).x(), 1e-6);
        assertEquals(.1f, clips.sample(1.2, .5f).y(), 1e-6);
        assertEquals(IDLE, clips.sample(2, 1));
        assertEquals(hip.sample(.5), clips.sample(.5, Float.NaN));
    }

    @Test void repeatedEventsAreDeduplicatedButDistinctPaidBurstBulletsSurviveTheSameTick() {
        var c = new WeaponFireMotion.Controller(); var clips = pair(constant(1, pose(.01f, 0, 0, new Quaternionf())));
        emit(c, clips, 0, false, true, 0);
        emit(c, clips, 0, false, true, 0);
        assertEquals(1, c.count(KEY));
        emit(c, clips, 0, false, false, 1);
        emit(c, clips, 0, false, false, 1);
        assertEquals(2, c.count(KEY));
        c.clear(KEY, owner);
        emit(c, clips, 0, true, true, 0);
        emit(c, clips, 1, true, false, 1);
        emit(c, clips, 2, true, false, 2);
        assertEquals(1, c.count(KEY)); // A fusion cartridge, not three clip restarts.
        assertEquals(.01f, sample(c, 3, 0).x(), 1e-6);
        assertFalse(WeaponFireMotion.accepts(false, true, -1));
        assertFalse(WeaponFireMotion.accepts(false, false, 9));
    }

    @Test void automaticFireOverlapsInsteadOfRestartingAtZeroAndReturnsToNeutralAfterRelease() {
        var c = new WeaponFireMotion.Controller(); var clips = pair(constant(.6, pose(.01f, 0, .02f, new Quaternionf().rotationX(.02f))));
        for (int tick=0; tick<40; tick++) {
            emit(c, clips, tick, false, true, 0);
            if (tick>0) assertTrue(sample(c, tick, 0).z()>0, "A new onset cannot erase prior recoil");
            assertTrue(c.count(KEY)<=WeaponFireMotion.MAX_IMPULSES);
        }
        assertTrue(sample(c, 40, 0).z()>0); // Release is not a cancellation.
        assertEquals(IDLE, sample(c, 52, 0));
        assertTrue(c.count(KEY)>0); // Snapshots are read-only, including expired state.
        c.retire(KEY, owner, stack, level, 52);
        assertEquals(0, c.count(KEY));
    }

    @Test void localAccumulationPolicyBoundsImpulsesTranslationAndRotationWithoutAmplifyingASingleShot() {
        var c = new WeaponFireMotion.Controller();
        var clips = pair(constant(10, pose(.3f, 0, 0, new Quaternionf().rotationX((float)Math.toRadians(30)))));
        emit(c, clips, 0, false, true, 0);
        var single = sample(c, 5, 0);
        assertEquals(.3f, single.x(), 1e-6);
        assertEquals(Math.toRadians(30), single.rotation().angle(), 1e-5);
        for (int tick=1; tick<=60; tick++) emit(c, clips, tick, false, true, 0);
        assertEquals(24, c.count(KEY));
        var capped = sample(c, 65, 0);
        assertEquals(.35f, new Vector3f(capped.x(), capped.y(), capped.z()).length(), 1e-6);
        assertEquals(Math.toRadians(40), capped.rotation().angle(), 1e-5);
    }

    @Test void exactOwnerStackLevelAndExplicitClearPreventMotionFromSurvivingLifecycleBoundaries() {
        var c = new WeaponFireMotion.Controller(); var clips=pair(constant(1, pose(.01f, 0, 0, new Quaternionf())));
        emit(c, clips, 0, false, true, 0);
        c.stow(KEY, owner, new Object());
        c.clear(KEY, new Object());
        assertEquals(1, c.count(KEY));
        c.stow(KEY, owner, stack);
        assertEquals(0, c.count(KEY));
        emit(c, clips, 1, false, true, 0);
        assertEquals(IDLE, c.sample(KEY, owner, new Object(), level, 2, 0, false));
        c.retire(KEY, owner, new Object(), level, 2);
        assertEquals(0, c.count(KEY));
        emit(c, clips, 2, false, true, 0);
        assertEquals(IDLE, c.sample(KEY, owner, stack, new Object(), 3, 0, false));
        c.retire(KEY, owner, stack, new Object(), 3);
        assertEquals(0, c.count(KEY));
        emit(c, clips, 3, false, true, 0);
        var recipient = new Object(); var recipientStack = new Object();
        c.emit(KEY, recipient, recipientStack, level, "fixture", clips, 3, false, true, 0, 0);
        c.clear(KEY, owner); c.stow(KEY, owner, stack);
        assertEquals(.01f, c.sample(KEY, recipient, recipientStack, level, 4, 0, false).x(), 1e-6);
        c.clear(KEY, recipient); // Successful reload/suspend/death use this same retirement.
        assertEquals(IDLE, c.sample(KEY, recipient, recipientStack, level, 4, 0, false));
        assertEquals(0, c.count(KEY));
    }

    @Test void lastRocketShotSurvivesAutomaticReloadWithItsPaidAdsVariantButExplicitClearStillWins() throws Exception {
        try(var in=getClass().getResourceAsStream("/destiny/weapons/w242-fire-motion.json")) {
            assertNotNull(in);
            var clips=WeaponFireMotion.Library.read(new InputStreamReader(in,StandardCharsets.UTF_8)).weapons.get("bad_omens");
            for(float ads:List.of(0f,.5f,1f)) {
                var c=new WeaponFireMotion.Controller();
                c.emit(KEY,owner,stack,level,"bad_omens",clips,0,false,true,0,ads);
                assertEquals(IDLE,c.sample(KEY,owner,stack,level,0,0,true));
                // Reload starts at tick0 before the neutral onset has ever been displayed.
                c.retire(KEY,owner,stack,level,0,true);
                var early=c.sample(KEY,owner,stack,level,2,0,true);
                assertFalse(early.neutral());
                assertTrue(early.matrix(false).equals(clips.sample(.1,ads).matrix(false),1e-5f));
                assertEquals(1,c.count(KEY));
                // Also retain the variant if a short reload/nock ends before source recovery.
                assertTrue(c.sample(KEY,owner,stack,level,3,0,false).matrix(false)
                        .equals(clips.sample(.15,ads).matrix(false),1e-5f));
                int end=(int)Math.ceil(clips.duration()*20);
                assertEquals(IDLE,c.sample(KEY,owner,stack,level,end,0,true));
                c.retire(KEY,owner,stack,level,end,true);
                assertEquals(0,c.count(KEY));
                c.emit(KEY,owner,stack,level,"bad_omens",clips,end,false,true,0,ads);
                c.clear(KEY,owner); // Manual reload/skill remains an unconditional explicit clear.
                assertEquals(IDLE,c.sample(KEY,owner,stack,level,end+2,0,true));
                assertEquals(0,c.count(KEY));
                c.emit(KEY,owner,stack,level,"bad_omens",clips,end+3,false,true,0,ads);
                c.stow(KEY,owner,stack);
                assertEquals(0,c.count(KEY));
            }
        }
    }

    @Test void commonViewRootPreservesRelativeGripAndNeutralFramingForBothHands() {
        var motion=pose(.07f, -.02f, .03f, new Quaternionf().rotationXYZ(.2f, .1f, -.15f));
        var gunPose=new Matrix4f().translation(.1f, .2f, -.3f).rotateY(.3f);
        var armPoses=List.of(new Matrix4f().translation(.2f, -.1f, .2f),
                new Matrix4f().translation(-.2f, -.3f, .5f), new Matrix4f().rotationX(.4f), new Matrix4f().rotationY(-.2f));
        for(boolean left:List.of(false,true)) for(boolean two:List.of(false,true)) for(float ads:List.of(0f,.5f,1f)) {
            var base=ProfileWeaponView.handMatrix(left,two,ads);
            assertEquals(base, ProfileWeaponView.motionRoot(base,IDLE,left));
            var root=ProfileWeaponView.motionRoot(base,motion,left);
            assertEquals(left?-.07f:.07f, root.m30()-base.m30(), 1e-6); // View axes, not crossbow-rotated axes.
            assertEquals(-.02f, root.m31()-base.m31(), 1e-6);
            for(var arm:armPoses) {
                var relative=new Matrix4f(root).mul(gunPose).invert().mul(new Matrix4f(root).mul(arm));
                assertTrue(relative.equals(new Matrix4f(gunPose).invert().mul(arm),1e-5f));
            }
            assertEquals(base,ProfileWeaponView.motionRoot(base,IDLE,left)); // Explicit neutral return.
        }
        var reflection=new Matrix4f().scaling(-1,1,1);
        assertTrue(motion.matrix(true).equals(new Matrix4f(reflection).mul(motion.matrix(false)).mul(reflection),1e-6f));
    }

    @Test void fixtureLoaderRejectsUnknownCalibrationBrokenRoutesAndNonNeutralEndpoints() {
        String sample="{\"translation\":[0,0,0],\"rotation\":[0,0,0,1]}";
        String samples=String.join(",",java.util.Collections.nCopies(61,sample));
        String json="{\"schemaVersion\":1,\"samplesPerClip\":61,\"sourceUnitToView\":1,"
                +"\"weapons\":{\"fixture\":{\"group\":\"group\",\"hip\":\"tag\",\"ads\":\"tag\"}},"
                +"\"groups\":{\"group\":{\"tag\":{\"duration\":1,\"samples\":["+samples+"]}}}}";
        assertEquals(IDLE,WeaponFireMotion.Library.read(new StringReader(json)).weapons.get("fixture").hip().sample(.5));
        assertThrows(IllegalArgumentException.class,()->WeaponFireMotion.Library.read(new StringReader(json.replace("sourceUnitToView\":1","sourceUnitToView\":2"))));
        assertThrows(IllegalArgumentException.class,()->WeaponFireMotion.Library.read(new StringReader(json.replace("\"ads\":\"tag\"","\"ads\":\"missing\""))));
        assertThrows(IllegalArgumentException.class,()->WeaponFireMotion.Library.read(new StringReader(json.replaceFirst("0,0,0", "1,0,0"))));
    }

    private static WeaponFireMotion.Pose pose(float x,float y,float z,Quaternionf q) {
        return new WeaponFireMotion.Pose(x,y,z,q.x,q.y,q.z,q.w);
    }
    private static WeaponFireMotion.Clip constant(double seconds,WeaponFireMotion.Pose pose) {
        var samples=new ArrayList<>(java.util.Collections.nCopies(61,pose));
        samples.set(0,IDLE); samples.set(60,IDLE);
        return new WeaponFireMotion.Clip(seconds,samples);
    }
    private static WeaponFireMotion.Clips pair(WeaponFireMotion.Clip clip) { return new WeaponFireMotion.Clips(clip,clip); }
    private void emit(WeaponFireMotion.Controller c,WeaponFireMotion.Clips clips,long tick,boolean shared,boolean first,int bolt) {
        c.emit(KEY,owner,stack,level,"fixture",clips,tick,shared,first,bolt,0);
    }
    private WeaponFireMotion.Pose sample(WeaponFireMotion.Controller c,long tick,float ads) {
        return c.sample(KEY,owner,stack,level,tick,ads,false);
    }
}
