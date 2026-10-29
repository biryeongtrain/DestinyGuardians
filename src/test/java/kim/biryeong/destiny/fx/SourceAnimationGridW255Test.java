package kim.biryeong.destiny.fx;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import kr.toxicity.model.api.animation.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.nio.file.*;
import static org.junit.jupiter.api.Assertions.*;

class SourceAnimationGridW255Test {
    private JsonObject dense() {
        var clip=new JsonObject();clip.addProperty("name","dense");clip.addProperty("length",1.0);
        var animators=new JsonObject();var bone=new JsonObject();var keys=new JsonArray();
        for(int i=0;i<=120;i++) {var key=new JsonObject();key.addProperty("channel","rotation");key.addProperty("time",i/120d);key.addProperty("interpolation","linear");
            var data=new JsonArray();var p=new JsonObject();p.addProperty("x",i*1.5);p.addProperty("y",0);p.addProperty("z",0);data.add(p);key.add("data_points",data);keys.add(key);}
        bone.add("keyframes",keys);animators.add("arm",bone);clip.add("animators",animators);return clip;
    }
    private int engineFrames(JsonArray keys) {
        var sequence=new ArrayList<AnimationProgress>();double previous=0;
        for(var key:keys) {double t=key.getAsJsonObject().get("time").getAsDouble();sequence.add(AnimationProgress.empty((float)(t-previous)));previous=t;}
        var done=new AtomicBoolean();var state=new AnimationStateHandler<AnimationProgress>(null,(a,b)->{});
        state.addAnimation("probe",AnimationIterator.Type.PLAY_ONCE.create(TimedStorage.listOf(sequence)),
                AnimationModifier.builder().start(1).end(0).type(AnimationIterator.Type.PLAY_ONCE).build(),()->done.set(true));
        int frames=0;while(!done.get()&&frames<2000){state.tick();frames++;}return frames;
    }
    @Test void denseSourceDoesNotStretchInTheRealBetterModelStateMachine() {
        var source=dense();String original=source.toString();var compiled=SourceAnimationGrid.compile(source);
        assertEquals(original,source.toString());assertEquals(1,compiled.get("length").getAsDouble());
        var raw=source.getAsJsonObject("animators").getAsJsonObject("arm").getAsJsonArray("keyframes");
        var grid=compiled.getAsJsonObject("animators").getAsJsonObject("arm").getAsJsonArray("keyframes");
        assertEquals(123,engineFrames(raw),"Regression: sub-frame keys each consume a full engine evaluation");
        assertEquals(43,engineFrames(grid),"Source1s +2entry frames +1completion frame");
        for(var value:grid) {var k=value.getAsJsonObject();assertEquals(k.get("time").getAsDouble()*180,k.getAsJsonArray("data_points").get(0).getAsJsonObject().get("x").getAsDouble(),1e-8);}
    }
    @Test void allImportedSourceOneShotsKeepLengthAndBoundedEngineDuration() throws Exception {
        int checked=0;
        for(String file:List.of("hunter_w199.animation.json","class_ability_w255.animation.json","classes_w230.animation.json","grenade_w252.animation.json")) {
            var root=JsonParser.parseString(Files.readString(Path.of("src/main/resources/destiny/animation/"+file))).getAsJsonObject();
            for(var a:root.getAsJsonArray("animations")) {
                var raw=a.getAsJsonObject();var grid=SourceAnimationGrid.compile(raw);double length=raw.get("length").getAsDouble();
                assertEquals(length,grid.get("length").getAsDouble());
                for(var bone:grid.getAsJsonObject("animators").entrySet()) {
                    var channels=new HashMap<String,JsonArray>();
                    for(var k:bone.getValue().getAsJsonObject().getAsJsonArray("keyframes"))channels.computeIfAbsent(k.getAsJsonObject().get("channel").getAsString(),x->new JsonArray()).add(k);
                    for(var keys:channels.values())assertTrue(engineFrames(keys)<=(int)Math.ceil(length*40)+4,raw.get("name").getAsString());
                }checked++;
            }
        }assertEquals(93,checked);
    }
    @Test void classLifecycleUsesTheSameSourceSecondsAndEntryBlend() {
        assertEquals(new ClassAbilityTiming.Timing(14,28),ClassAbilityTiming.of("class_titan_towering"));
        assertEquals(new ClassAbilityTiming.Timing(17,35),ClassAbilityTiming.of("class_warlock_healing"));
    }
    @Test void effectsAndExpressionChannelsKeepTheirNativeKeys() {
        var source=dense();
        var bone=source.getAsJsonObject("animators").getAsJsonObject("arm");
        var effects=new JsonArray();
        var key=new JsonObject();key.addProperty("channel","sound");key.addProperty("time",.3);
        key.addProperty("interpolation","linear");
        var points=new JsonArray();var point=new JsonObject();point.addProperty("effect","sound");
        points.add(point);key.add("data_points",points);effects.add(key);bone.add("keyframes",effects);
        assertEquals(effects,SourceAnimationGrid.compile(source).getAsJsonObject("animators").getAsJsonObject("arm").get("keyframes"));
        key.addProperty("channel","rotation");point.remove("effect");
        point.addProperty("x","query.anim_time * 3");point.addProperty("y",0);point.addProperty("z",0);
        assertEquals(effects,SourceAnimationGrid.compile(source).getAsJsonObject("animators").getAsJsonObject("arm").get("keyframes"));
    }
}
