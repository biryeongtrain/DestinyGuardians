package kim.biryeong.destiny.fx;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Saved-asset contracts only; authoring Euler data is NOT BetterModel engine contact proof. */
class H20AnimationTest {
    private static final double EPS = 1e-6;
    private static final Set<String> BONES = Set.of("player_root", "phip_hip", "pw_waist", "pc_chest", "h_ph_head",
            "pra_right_arm", "prfa_right_forearm", "pri_right_item", "pla_left_arm", "plfa_left_forearm", "pli_left_item",
            "prl_right_leg", "prfl_right_foreleg", "pll_left_leg", "plfl_left_foreleg", "cape_cape");

    private static JsonObject resource(String version) throws Exception {
        try (var stream = H20AnimationTest.class.getResourceAsStream("/destiny/animation/hunter_" + version + ".animation.json")) {
            assertNotNull(stream);
            return JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }

    private static Map<String, JsonObject> clips(JsonObject pack) {
        var result = new LinkedHashMap<String, JsonObject>();
        for (var value : pack.getAsJsonArray("animations")) {
            var clip = value.getAsJsonObject();
            assertNull(result.put(clip.get("name").getAsString(), clip), "No duplicate logical names");
        }
        return result;
    }

    private static JsonObject animator(JsonObject clip, String bone) {
        for (var value : clip.getAsJsonObject("animators").asMap().values()) {
            var animator = value.getAsJsonObject();
            if (animator.get("name").getAsString().equals(bone)) return animator;
        }
        throw new AssertionError("Missing bone " + bone);
    }

    private static List<JsonObject> keys(JsonObject clip, String bone, String channel) {
        var result = new ArrayList<JsonObject>();
        for (var value : animator(clip, bone).getAsJsonArray("keyframes")) {
            var key = value.getAsJsonObject();
            if (key.get("channel").getAsString().equals(channel)) result.add(key);
        }
        result.sort(Comparator.comparingDouble(k -> k.get("time").getAsDouble()));
        return result;
    }

    private static double[] sample(JsonObject clip, String bone, String channel, double time) {
        var keys = keys(clip, bone, channel);
        assertFalse(keys.isEmpty());
        JsonObject lo = keys.getFirst(), hi = keys.getLast();
        for (var key : keys) {
            if (key.get("time").getAsDouble() <= time + 1e-9) lo = key;
            if (key.get("time").getAsDouble() >= time - 1e-9) { hi = key; break; }
        }
        double span = hi.get("time").getAsDouble() - lo.get("time").getAsDouble();
        double fraction = span == 0 ? 0 : (time - lo.get("time").getAsDouble()) / span;
        var a = lo.getAsJsonArray("data_points").get(0).getAsJsonObject();
        var b = hi.getAsJsonArray("data_points").get(0).getAsJsonObject();
        var result = new double[3];
        for (int i = 0; i < 3; i++) {
            String axis = List.of("x", "y", "z").get(i);
            result[i] = a.get(axis).getAsDouble() + fraction * (b.get(axis).getAsDouble() - a.get(axis).getAsDouble());
        }
        return result;
    }

    private static void samePose(JsonObject a, double aTime, JsonObject b, double bTime) {
        for (String bone : BONES) assertArrayEquals(sample(a, bone, "rotation", aTime), sample(b, bone, "rotation", bTime), EPS, bone);
        assertArrayEquals(sample(a, "player_root", "position", aTime), sample(b, "player_root", "position", bTime), EPS);
    }

    @Test void exportsNineteenCompatibleClipsOnDistinctH20Model() throws Exception {
        var pack = resource("h20");
        assertEquals("guardian_hunter_h20", pack.get("model").getAsString());
        var expected = new HashSet<>(Set.of("h15_grenade", "h15_melee", "h15_throw", "h15_melee_solar", "h15_melee_void"));
        for (String element : List.of("arc", "solar", "void")) {
            expected.add("h15_super_" + element);
            expected.add("h15_super_" + element + "_attack");
        }
        for (String element : List.of("arc", "solar")) for (String suffix : List.of("start", "end"))
            expected.add("h15_super_" + element + "_" + suffix);
        for (String direction : List.of("forward", "back", "left", "right")) expected.add("h15_roll_" + direction);
        assertEquals(expected, clips(pack).keySet());
    }

    @Test void superAndSkillDurationsMatchAcceptedTickTimingIncludingOneTickTransition() throws Exception {
        var clips = clips(resource("h20"));
        var elapsed = Map.of("h15_super_arc_start", 11, "h15_super_arc_attack", 13,
                "h15_super_solar_start", 10, "h15_super_solar_attack", 8,
                "h15_super_arc_end", 8, "h15_super_solar_end", 8,
                "h15_super_void_attack", 19, "h15_grenade", 12, "h15_melee", 9, "h15_throw", 9);
        for (var entry : elapsed.entrySet()) {
            var clip = clips.get(entry.getKey());
            assertEquals(entry.getValue().doubleValue(), clip.get("length").getAsDouble() * 20 + 1, EPS, entry.getKey());
            assertEquals("once", clip.get("loop").getAsString());
        }
        for (String name : List.of("h15_melee_solar", "h15_melee_void"))
            assertEquals(.40, clips.get(name).get("length").getAsDouble(), EPS);
    }

    @Test void contactsAreExplicitFullBodyKeysAndThrownVariantsAreDistinct() throws Exception {
        var clips = clips(resource("h20"));
        var contacts = Map.of("h15_super_arc_attack", .20, "h15_super_solar_attack", .10,
                "h15_super_void_attack", .30, "h15_grenade", .15, "h15_melee", .15,
                "h15_throw", .15, "h15_melee_solar", .15, "h15_melee_void", .15);
        for (var entry : contacts.entrySet()) for (String bone : BONES)
            assertTrue(keys(clips.get(entry.getKey()), bone, "rotation").stream()
                    .anyMatch(k -> Math.abs(k.get("time").getAsDouble() - entry.getValue()) < EPS), entry.getKey() + ":" + bone);
        assertFalse(java.util.Arrays.equals(sample(clips.get("h15_melee_solar"), "pra_right_arm", "rotation", .05),
                sample(clips.get("h15_melee_void"), "pra_right_arm", "rotation", .05)), "High knife and low smoke casts are not one recolored pose");
    }

    @Test void completeFiniteChannelsHaveUniqueTimesAndUuidsAndNoHorizontalRootMotion() throws Exception {
        var uuids = new HashSet<String>();
        for (var clip : clips(resource("h20")).values()) {
            assertTrue(uuids.add(clip.get("uuid").getAsString()));
            var seenBones = new HashSet<String>();
            for (var value : clip.getAsJsonObject("animators").asMap().values()) {
                var animator = value.getAsJsonObject();
                String bone = animator.get("name").getAsString();
                assertTrue(seenBones.add(bone));
                assertFalse(animator.get("quaternion_interpolation").getAsBoolean());
                var byChannel = new LinkedHashMap<String, List<Double>>();
                for (var k : animator.getAsJsonArray("keyframes")) {
                    var key = k.getAsJsonObject();
                    assertTrue(uuids.add(key.get("uuid").getAsString()));
                    String channel = key.get("channel").getAsString();
                    byChannel.computeIfAbsent(channel, ignored -> new ArrayList<>()).add(key.get("time").getAsDouble());
                    var point = key.getAsJsonArray("data_points").get(0).getAsJsonObject();
                    for (String axis : List.of("x", "y", "z")) assertTrue(Double.isFinite(point.get(axis).getAsDouble()));
                    if (bone.equals("player_root") && channel.equals("position")) {
                        assertEquals(0, point.get("x").getAsDouble(), EPS);
                        assertEquals(0, point.get("z").getAsDouble(), EPS);
                        assertTrue(Math.abs(point.get("y").getAsDouble()) < 32);
                    }
                }
                for (var times : byChannel.values()) {
                    assertEquals(times.size(), new HashSet<>(times).size());
                    assertTrue(times.size() <= 256);
                    assertEquals(0, times.stream().mapToDouble(Double::doubleValue).min().orElseThrow(), EPS);
                    assertEquals(clip.get("length").getAsDouble(), times.stream().mapToDouble(Double::doubleValue).max().orElseThrow(), EPS);
                }
            }
            assertEquals(BONES, seenBones);
        }
    }

    @Test void readyLoopsAndSuperAttackRecoveryJoinWithoutPoseDiscontinuity() throws Exception {
        var clips = clips(resource("h20"));
        for (String element : List.of("arc", "solar", "void")) {
            var ready = clips.get("h15_super_" + element);
            var attack = clips.get("h15_super_" + element + "_attack");
            assertEquals("loop", ready.get("loop").getAsString());
            samePose(ready, 0, ready, ready.get("length").getAsDouble());
            samePose(ready, 0, attack, 0);
            samePose(ready, 0, attack, attack.get("length").getAsDouble());
            if (!element.equals("void")) {
                var start = clips.get("h15_super_" + element + "_start");
                var end = clips.get("h15_super_" + element + "_end");
                samePose(start, start.get("length").getAsDouble(), ready, 0);
                samePose(end, 0, ready, 0);
            }
        }
    }

    @Test void arcAttackAuthorsEveryFortyHzLocalSampleIncludingFormerSupportGaps() throws Exception {
        var clip = clips(resource("h20")).get("h15_super_arc_attack");
        assertEquals(40, clip.get("snapping").getAsInt());
        assertEquals(.60, clip.get("length").getAsDouble(), EPS);
        for (String bone : BONES) {
            var rotations = keys(clip, bone, "rotation");
            assertEquals(25, rotations.size(), bone);
            for (int frame = 0; frame <= 24; frame++) {
                assertEquals(frame / 40.0, rotations.get(frame).get("time").getAsDouble(), EPS, bone);
                assertEquals("linear", rotations.get(frame).get("interpolation").getAsString(), bone);
            }
        }
        // The former .125s support miss must get its own solved pose, not a duplicated linear midpoint.
        for (String bone : List.of("pla_left_arm", "plfa_left_forearm")) {
            var before = sample(clip, bone, "rotation", .10);
            var after = sample(clip, bone, "rotation", .15);
            var solved = sample(clip, bone, "rotation", .125);
            boolean differs = false;
            for (int axis = 0; axis < 3; axis++)
                differs |= Math.abs(solved[axis] - (before[axis] + after[axis]) / 2) > .001;
            assertTrue(differs, bone + " has a re-solved support pose");
        }
    }

    @Test void solarHoldsAimUntilReleaseAndOnlyThenRecoilChangesThePose() throws Exception {
        var clip = clips(resource("h20")).get("h15_super_solar_attack");
        samePose(clip, 0, clip, .05);
        samePose(clip, 0, clip, .10);
        assertFalse(java.util.Arrays.equals(sample(clip, "pra_right_arm", "rotation", .10),
                sample(clip, "pra_right_arm", "rotation", .15)));
    }

    @Test void voidKeepsH19ReadyAndKeysEveryServerTickThroughTheReleaseHold() throws Exception {
        var h20 = clips(resource("h20"));
        assertEquals(clips(resource("h19")).get("h15_super_void"), h20.get("h15_super_void"));
        var attack = h20.get("h15_super_void_attack");
        for (int tick = 0; tick <= 6; tick++) {
            double time = tick / 20.0;
            for (String bone : BONES) assertTrue(keys(attack, bone, "rotation").stream()
                    .anyMatch(k -> Math.abs(k.get("time").getAsDouble() - time) < EPS));
        }
        samePose(attack, .25, attack, .30);
        assertFalse(java.util.Arrays.equals(sample(attack, "prfa_right_forearm", "rotation", .15),
                sample(attack, "prfa_right_forearm", "rotation", .20)));
    }

    @Test void itemScaleLifecycleIsBoundedAndReadyAndAttackResetToUnitScale() throws Exception {
        var clips = clips(resource("h20"));
        for (String element : List.of("arc", "solar")) {
            var start = clips.get("h15_super_" + element + "_start");
            var end = clips.get("h15_super_" + element + "_end");
            assertArrayEquals(new double[]{.001, .001, .001}, sample(start, "pri_right_item", "scale", 0), EPS);
            assertArrayEquals(new double[]{.001, .001, .001}, sample(end, "pri_right_item", "scale", .25), EPS);
            for (String suffix : List.of("", "_attack")) {
                var clip = clips.get("h15_super_" + element + suffix);
                for (double t : new double[]{0, clip.get("length").getAsDouble()})
                    assertArrayEquals(new double[]{1, 1, 1}, sample(clip, "pri_right_item", "scale", t), EPS);
            }
        }
    }

    @Test void fourRollsPreserveFullTurnDirectionAndFourteenClipTicks() throws Exception {
        var clips = clips(resource("h20"));
        for (String direction : List.of("forward", "back", "left", "right")) {
            var clip = clips.get("h15_roll_" + direction);
            assertEquals(.70, clip.get("length").getAsDouble(), EPS);
            int axis = direction.equals("forward") || direction.equals("back") ? 0 : 2;
            int sign = direction.equals("back") || direction.equals("left") ? 1 : -1;
            assertEquals(sign * 360, sample(clip, "player_root", "rotation", .70)[axis], EPS);
            assertEquals(0, sample(clip, "player_root", "rotation", .70)[1], EPS);
        }
    }
}
