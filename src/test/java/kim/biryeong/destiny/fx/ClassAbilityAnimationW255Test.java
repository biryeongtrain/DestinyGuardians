package kim.biryeong.destiny.fx;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Standalone asset contract; no server, native renderer, or SSD is needed. */
class ClassAbilityAnimationW255Test {
    private JsonObject read(String name) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(name))).getAsJsonObject();
    }

    @Test void fourSourceAssembledOneShotsKeepStageTimingAndCalibratedContacts() throws Exception {
        var pack = read("src/main/resources/destiny/animation/class_ability_w255.animation.json");
        var manifest = read("art/abilities/w255/class-motion-manifest.json");
        var timing = read("src/main/resources/destiny/animation/class_ability_w255.timing.json");
        assertEquals(1, timing.get("schemaVersion").getAsInt());
        var runtimeRecords = new HashMap<String, JsonObject>();
        for (var entry : timing.getAsJsonArray("clips")) {
            var record = entry.getAsJsonObject();
            assertNull(runtimeRecords.put(record.get("name").getAsString(), record));
        }
        var lengths = Map.of("h15_class_titan_towering", 40.0 / 30,
                "h15_class_titan_rally", 42.0 / 30,
                "h15_class_warlock_healing", 51.0 / 30,
                "h15_class_warlock_empowering", 54.0 / 30);
        var releases = Map.of("h15_class_titan_towering", 13, "h15_class_titan_rally", 8,
                "h15_class_warlock_healing", 16, "h15_class_warlock_empowering", 21);
        var records = new HashMap<String, JsonObject>();
        for (var entry : manifest.getAsJsonArray("clips")) {
            var record = entry.getAsJsonObject();
            assertNull(records.put(record.get("name").getAsString(), record));
        }
        var names = new HashSet<String>();
        for (var entry : pack.getAsJsonArray("animations")) {
            var clip = entry.getAsJsonObject();
            var name = clip.get("name").getAsString();
            assertTrue(names.add(name));
            assertTrue(lengths.containsKey(name));
            assertEquals("once", clip.get("loop").getAsString());
            assertFalse(clip.get("override").getAsBoolean());
            assertEquals(lengths.get(name), clip.get("length").getAsDouble(), 1e-8);
            var record = records.get(name);
            var runtime = runtimeRecords.get(name);
            assertNotNull(runtime);
            assertEquals(clip.get("length").getAsDouble(), runtime.get("durationSeconds").getAsDouble(), 1e-9);
            assertEquals(record.getAsJsonObject("contact").get("seconds").getAsDouble(),
                    runtime.get("contactSeconds").getAsDouble(), 1e-9);
            assertEquals(1, runtime.get("entryTicks").getAsInt());
            assertEquals(releases.get(name).intValue(),
                    (int) Math.ceil(runtime.get("contactSeconds").getAsDouble() * 20 - 1e-9));
            assertEquals(releases.get(name).intValue(), record.get("recommendedReleaseTicks").getAsInt());
            assertEquals(1, record.get("startModifierTicks").getAsInt());
            assertEquals(releases.get(name) + 1, record.get("elapsedReleaseTicks").getAsInt());
            assertEquals((int) Math.ceil(lengths.get(name) * 20) + 1,
                    record.get("lifecycleTicks").getAsInt());
            double offset = 0;
            var stages = record.getAsJsonArray("stages");
            assertEquals(name.contains("warlock") ? 3 : 2, stages.size());
            for (var stageEntry : stages) {
                var stage = stageEntry.getAsJsonObject();
                assertEquals(61, stage.get("evaluatedSamples").getAsInt());
                assertEquals(offset, stage.get("startSeconds").getAsDouble(), 1e-8);
                offset += stage.get("durationSeconds").getAsDouble();
            }
            assertEquals(lengths.get(name), offset, 1e-8);
            assertEquals(stages.size() * 60 + 1, record.get("assembledPoseCount").getAsInt());
            assertTrue(record.getAsJsonObject("contact").get("interpretation")
                    .getAsString().contains("not decoded source event"));
            assertTrue(record.get("maxInterpolatedFloorErrorModelUnits").getAsDouble() < .075);
            assertEquals(2, record.getAsJsonArray("renderReview").size());
        }
        assertEquals(lengths.keySet(), names);
        assertEquals(names, records.keySet());
        assertEquals(names, runtimeRecords.keySet());
        assertEquals(8, manifest.getAsJsonArray("auditOnly").size());
        assertEquals(18, manifest.getAsJsonArray("sourceActions").size());
        var scope = manifest.getAsJsonObject("runtimeScope");
        assertEquals(2, scope.getAsJsonArray("activeExistingAbilities").size());
        assertEquals(2, scope.getAsJsonArray("preparedAssetsOnly").size());
        assertFalse(scope.get("gameplayExpansion").getAsBoolean());
        assertTrue(manifest.getAsJsonObject("evaluatedSamples").get("autoexecDisabled").getAsBoolean());
    }

    @Test void fullBodyChannelsAreFiniteContinuousAndCompatibleWithCurrentRig() throws Exception {
        var pack = read("src/main/resources/destiny/animation/class_ability_w255.animation.json");
        var model = read("art/blockbench/animations/guardian_hunter_w199_r1.bbmodel");
        var rigBones = new HashSet<String>();
        for (var group : model.getAsJsonArray("groups"))
            rigBones.add(group.getAsJsonObject().get("name").getAsString());
        var movingBody = Set.of("phip_hip", "pw_waist", "pc_chest", "prl_right_leg",
                "prfl_right_foreleg", "pll_left_leg", "plfl_left_foreleg");
        for (var entry : pack.getAsJsonArray("animations")) {
            var clip = entry.getAsJsonObject();
            var animatedBones = new HashSet<String>();
            for (var entryAnimator : clip.getAsJsonObject("animators").entrySet()) {
                var animator = entryAnimator.getValue().getAsJsonObject();
                var bone = animator.get("name").getAsString();
                assertTrue(animatedBones.add(bone));
                assertTrue(rigBones.contains(bone));
                var times = new HashMap<String, Set<Double>>();
                double[] previous = null;
                double[] minimum = {Double.POSITIVE_INFINITY, Double.POSITIVE_INFINITY, Double.POSITIVE_INFINITY};
                double[] maximum = {Double.NEGATIVE_INFINITY, Double.NEGATIVE_INFINITY, Double.NEGATIVE_INFINITY};
                for (var keyEntry : animator.getAsJsonArray("keyframes")) {
                    var key = keyEntry.getAsJsonObject();
                    var channel = key.get("channel").getAsString();
                    double time = key.get("time").getAsDouble();
                    assertTrue(time >= 0 && time <= clip.get("length").getAsDouble());
                    assertTrue(times.computeIfAbsent(channel, ignored -> new HashSet<>()).add(time));
                    assertEquals("linear", key.get("interpolation").getAsString());
                    var point = key.getAsJsonArray("data_points").get(0).getAsJsonObject();
                    var axes = new String[]{"x", "y", "z"};
                    double[] values = new double[3];
                    for (int i = 0; i < 3; i++) {
                        values[i] = point.get(axes[i]).getAsDouble();
                        assertTrue(Double.isFinite(values[i]));
                        if (channel.equals("rotation")) {
                            minimum[i] = Math.min(minimum[i], values[i]);
                            maximum[i] = Math.max(maximum[i], values[i]);
                            if (previous != null) assertTrue(Math.abs(values[i] - previous[i]) < 120,
                                    clip.get("name").getAsString() + "/" + bone);
                        }
                    }
                    if (channel.equals("rotation")) {
                        previous = values;
                        if (bone.equals("prfl_right_foreleg") || bone.equals("plfl_left_foreleg")) {
                            assertTrue(values[0] <= 0 && values[0] >= -180, "Anatomical knee flex");
                            assertEquals(0, values[1]);
                            assertEquals(0, values[2]);
                        }
                    }
                    if (bone.equals("player_root") && channel.equals("position")) {
                        assertEquals(0, values[0]);
                        assertEquals(0, values[2]);
                    }
                }
                for (var channelTimes : times.values()) {
                    assertTrue(channelTimes.size() <= 256);
                    assertTrue(channelTimes.contains(0.0));
                    var ordered = channelTimes.stream().sorted().toList();
                    for (int i = 1; i < ordered.size(); i++)
                        assertTrue(ordered.get(i) - ordered.get(i - 1) > .001,
                                "BetterModel compares frame times with a 1ms epsilon");
                    assertTrue(channelTimes.stream().anyMatch(t -> Math.abs(t - clip.get("length").getAsDouble()) < 1e-8));
                }
                assertTrue(times.get("rotation").size() >= 121);
                if (movingBody.contains(bone)) {
                    boolean moved = false;
                    for (int i = 0; i < 3; i++) moved |= maximum[i] - minimum[i] > 3;
                    assertTrue(moved, "Source torso and legs must move: " + bone);
                }
            }
            assertTrue(animatedBones.containsAll(movingBody));
        }
    }
}
