package kim.biryeong.destiny.fx;

import com.google.gson.*;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import org.junit.jupiter.api.Test;
import kr.toxicity.model.api.animation.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;
import static org.junit.jupiter.api.Assertions.*;

class MeleeSuperAnimationW330Test {
    private static JsonObject wrap(boolean optIn) {
        var clip=new JsonObject();clip.addProperty("name","w330_wrap_probe");clip.addProperty("length",.05);
        clip.addProperty("destiny_quaternion_sampling",optIn);
        var animators=new JsonObject();var bone=new JsonObject();bone.addProperty("name","pc_chest");
        bone.addProperty("rotation_global",true);var keys=new JsonArray();
        for(int i=0;i<2;i++) {
            double z=i==0?179:-179;var key=new JsonObject();key.addProperty("channel","rotation");
            key.addProperty("time",i*.05);key.addProperty("interpolation","linear");
            var point=new JsonObject();point.addProperty("x",0);point.addProperty("y",0);point.addProperty("z",z);
            var points=new JsonArray();points.add(point);key.add("data_points",points);
            var q=new Quaternionf().rotationZYX((float)Math.toRadians(z),0,0);var quaternion=new JsonArray();
            quaternion.add(q.x);quaternion.add(q.y);quaternion.add(q.z);quaternion.add(q.w);key.add("destiny_quaternion",quaternion);keys.add(key);
        }
        bone.add("keyframes",keys);animators.add("chest",bone);clip.add("animators",animators);return clip;
    }
    private static JsonArray keys(JsonObject clip) {return clip.getAsJsonObject("animators").getAsJsonObject("chest").getAsJsonArray("keyframes");}
    @Test void optInQuaternionWrapUsesShortRotationAndPreservesGlobalFlag() {
        var raw=wrap(true);String before=raw.toString();var compiled=SourceAnimationGrid.compile(raw);
        assertEquals(before,raw.toString());assertEquals(.05,compiled.get("length").getAsDouble());
        var key=keys(compiled).get(1).getAsJsonObject();var value=key.getAsJsonArray("data_points").get(0).getAsJsonObject();
        assertEquals(180,Math.abs(value.get("z").getAsDouble()),.001);
        assertTrue(compiled.getAsJsonObject("animators").getAsJsonObject("chest").get("rotation_global").getAsBoolean());
        assertFalse(key.has("destiny_quaternion"));assertEquals(40,compiled.get("destiny_quaternion_baked_hz").getAsInt());
    }
    @Test void nonOptInLegacyEulerBehaviorIsUnchanged() {
        var compiled=SourceAnimationGrid.compile(wrap(false));
        assertEquals(0,keys(compiled).get(1).getAsJsonObject().getAsJsonArray("data_points").get(0).getAsJsonObject().get("z").getAsDouble(),1e-8);
    }
    @Test void bakedEulerRoundTripsThroughBetterModelZyxRotationOrder() {
        var previous=new Vector3f(22,88,34);
        for(float y:new float[]{88,89,89.9f,90.1f,91,92}) {
            var expected=new Quaternionf().rotationZYX((float)Math.toRadians(34),(float)Math.toRadians(y),(float)Math.toRadians(22));
            var euler=SourceAnimationGrid.continuousEuler(expected,previous);
            var actual=kr.toxicity.model.api.util.MathUtil.toQuaternion(new Vector3f(euler));
            assertEquals(1,Math.abs(actual.dot(expected)),2e-5,"Actual BetterModel toQuaternion must reconstruct the source orientation");
            assertTrue(euler.distance(previous)<5,"Equivalent Euler branch must stay continuous at the pitch singularity");
            previous=euler;
        }
    }
    @Test void malformedOptInCannotSilentlyFallBackToEulerInterpolation() {
        var source=wrap(true);keys(source).get(0).getAsJsonObject().remove("destiny_quaternion");
        assertThrows(IllegalArgumentException.class,()->SourceAnimationGrid.compile(source));
    }
    @Test void requiredOverlaysExposeFullSourceDurationAirHeavyAndIndependentBlendContracts() {
        MeleeSuperAnimationTiming.require(MeleeSuperAnimationTiming.ARC_RESOURCE);
        MeleeSuperAnimationTiming.require(MeleeSuperAnimationTiming.SPECTRAL_RESOURCE);
        assertEquals(30,SuperAttackTiming.ARC_DEPLOY);
        assertEquals("h15_super_arc_attack_weak_3",MeleeSuperAnimationTiming.arcAttack(true,2));
        assertEquals("h15_super_arc_attack_air",MeleeSuperAnimationTiming.arcAttack(false,0));
        assertEquals("attack3",MeleeSuperAnimationTiming.spectralAttack(true,false,2));
        assertEquals("heavy",MeleeSuperAnimationTiming.spectralAttack(true,true,0));
        assertEquals("heavy_air",MeleeSuperAnimationTiming.spectralAttack(false,true,0));
        assertEquals("attack_air",MeleeSuperAnimationTiming.spectralAttack(false,false,1));
        String clip="w230_hunter_spectral_blades_heavy_air";
        assertEquals(19,MeleeSuperAnimationTiming.durationTicks(clip,0));
        assertEquals(21,MeleeSuperAnimationTiming.playbackTicks(clip,0));
        assertTrue(MeleeSuperAnimationTiming.contactTicks(clip,0)<MeleeSuperAnimationTiming.recoveryTicks(clip,0));
        assertTrue(HunterModelAssets.MODEL_NAME.endsWith(MeleeSuperAnimationTiming.revision(MeleeSuperAnimationTiming.ARC_RESOURCE)));
        assertTrue(ClassSuperModelAssets.MODEL_NAME.endsWith(MeleeSuperAnimationTiming.revision(MeleeSuperAnimationTiming.SPECTRAL_RESOURCE)));
    }
    @Test void newQuaternionOverlaysStayOnOneBetterModelFramePerGridPose() {
        for(String path:List.of(MeleeSuperAnimationTiming.ARC_RESOURCE,MeleeSuperAnimationTiming.SPECTRAL_RESOURCE)) {
            var overlay=MeleeSuperAnimationTiming.overlay(new JsonArray(),path);
            for(var value:overlay) {
                var raw=value.getAsJsonObject();double length=raw.get("length").getAsDouble();var compiled=SourceAnimationGrid.compile(raw);
                assertEquals(length,compiled.get("length").getAsDouble());
                for(var bone:compiled.getAsJsonObject("animators").entrySet()) {
                    var channels=new HashMap<String,List<Double>>();
                    for(var entry:bone.getValue().getAsJsonObject().getAsJsonArray("keyframes")) {
                        var key=entry.getAsJsonObject();channels.computeIfAbsent(key.get("channel").getAsString(),k->new ArrayList<>()).add(key.get("time").getAsDouble());
                    }
                    for(var times:channels.values())assertTrue(engineFrames(times)<=(int)Math.ceil(length*40)+8,raw.get("name").getAsString());
                }
            }
        }
    }
    private static int engineFrames(List<Double> times) {
        var sequence=new ArrayList<AnimationProgress>();double previous=0;
        for(double time:times){sequence.add(AnimationProgress.empty((float)(time-previous)));previous=time;}
        var done=new AtomicBoolean();var state=new AnimationStateHandler<AnimationProgress>(null,(a,b)->{});
        state.addAnimation("probe",AnimationIterator.Type.PLAY_ONCE.create(TimedStorage.listOf(sequence)),
                AnimationModifier.builder().start(1).end(2).type(AnimationIterator.Type.PLAY_ONCE).build(),()->done.set(true));
        int frames=0;while(!done.get()&&frames<2000){state.tick();frames++;}return frames;
    }
}
