package kim.biryeong.destiny.fx;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.joml.Matrix4d;
import org.joml.Vector3d;
import org.junit.jupiter.api.Test;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Saved-asset/FK regressions only. Does not claim native transmitted-pose or real hover proof. */
class H21AnimationTest {
    private static final double EPS = 1e-6;
    private static final String READY = "h15_super_void", ATTACK = READY + "_attack";
    private static final Set<String> LEGS = Set.of("prl_right_leg", "prfl_right_foreleg", "pll_left_leg", "plfl_left_foreleg");

    private static JsonObject resource(String version) throws Exception {
        try (var stream = H21AnimationTest.class.getResourceAsStream("/destiny/animation/hunter_" + version + ".animation.json")) {
            assertNotNull(stream);
            return JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }

    private static JsonObject art(String version) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of("art/blockbench/animations/guardian_hunter_" + version + ".bbmodel"))).getAsJsonObject();
    }

    private static Map<String, JsonObject> clips(JsonObject pack) {
        var result = new HashMap<String, JsonObject>();
        for (var a : pack.getAsJsonArray("animations")) {
            var clip = a.getAsJsonObject();
            assertNull(result.put(clip.get("name").getAsString(), clip));
        }
        return result;
    }

    private static Map<String, JsonObject> animators(JsonObject clip) {
        var result = new HashMap<String, JsonObject>();
        for (var a : clip.getAsJsonObject("animators").asMap().values()) {
            var animator = a.getAsJsonObject();
            result.put(animator.get("name").getAsString(), animator);
        }
        return result;
    }

    private static List<JsonObject> keys(JsonObject clip, String bone, String channel) {
        var result = new ArrayList<JsonObject>();
        for (var v : animators(clip).get(bone).getAsJsonArray("keyframes")) {
            var key = v.getAsJsonObject();
            if (key.get("channel").getAsString().equals(channel)) result.add(key);
        }
        result.sort(Comparator.comparingDouble(k -> k.get("time").getAsDouble()));
        assertFalse(result.isEmpty(), bone + ":" + channel);
        return result;
    }

    private static Vector3d sample(JsonObject clip, String bone, String channel, double time) {
        var keys = keys(clip, bone, channel);
        var lo = keys.getFirst(); var hi = keys.getLast();
        for (var key : keys) {
            if (key.get("time").getAsDouble() <= time + 1e-9) lo = key;
            if (key.get("time").getAsDouble() >= time - 1e-9) { hi = key; break; }
        }
        var a = lo.getAsJsonArray("data_points").get(0).getAsJsonObject();
        var b = hi.getAsJsonArray("data_points").get(0).getAsJsonObject();
        double span = hi.get("time").getAsDouble() - lo.get("time").getAsDouble();
        double t = span == 0 ? 0 : (time - lo.get("time").getAsDouble()) / span;
        return new Vector3d(a.get("x").getAsDouble(), a.get("y").getAsDouble(), a.get("z").getAsDouble())
                .lerp(new Vector3d(b.get("x").getAsDouble(), b.get("y").getAsDouble(), b.get("z").getAsDouble()), t);
    }

    private static Vector3d vector(JsonArray a) {
        return new Vector3d(a.get(0).getAsDouble(), a.get(1).getAsDouble(), a.get(2).getAsDouble());
    }

    private static Map<String, Matrix4d> fk(JsonObject model, JsonObject clip, double time) {
        var groups = new HashMap<String, JsonObject>();
        for (var g : model.getAsJsonArray("groups")) groups.put(g.getAsJsonObject().get("uuid").getAsString(), g.getAsJsonObject());
        var result = new HashMap<String, Matrix4d>();
        walk(model.getAsJsonArray("outliner"), new Matrix4d(), new Vector3d(), groups, result, clip, time);
        return result;
    }

    private static void walk(JsonArray nodes, Matrix4d parent, Vector3d parentOrigin,
                             Map<String, JsonObject> groups, Map<String, Matrix4d> result, JsonObject clip, double time) {
        var allAnimators = animators(clip);
        for (var value : nodes) {
            if (!value.isJsonObject()) continue;
            var node = value.getAsJsonObject();
            var group = groups.get(node.get("uuid").getAsString());
            String bone = group.get("name").getAsString();
            var origin = vector(group.getAsJsonArray("origin"));
            var offset = new Vector3d(origin).sub(parentOrigin);
            if (bone.equals("player_root")) offset.add(sample(clip, bone, "position", time));
            var angles = vector(group.getAsJsonArray("rotation"));
            if (allAnimators.containsKey(bone)) angles.add(sample(clip, bone, "rotation", time));
            var matrix = new Matrix4d(parent).translate(offset)
                    .rotateZ(Math.toRadians(angles.z)).rotateY(Math.toRadians(angles.y)).rotateX(Math.toRadians(angles.x));
            result.put(bone, matrix);
            walk(node.getAsJsonArray("children"), matrix, origin, groups, result, clip, time);
        }
    }

    private static Vector3d point(Matrix4d matrix, double x, double y, double z) {
        return matrix.transformPosition(new Vector3d(x, y, z));
    }

    private static void samePose(JsonObject a, double ta, JsonObject b, double tb) {
        for (String bone : animators(a).keySet()) assertTrue(sample(a, bone, "rotation", ta).distance(sample(b, bone, "rotation", tb)) < EPS, bone);
        assertTrue(sample(a, "player_root", "position", ta).distance(sample(b, "player_root", "position", tb)) < EPS);
    }

    @Test void distinctModelRetainsNineteenLogicalClipsAndSeventeenVerbatim() throws Exception {
        var h20 = clips(resource("h20")); var h21Pack = resource("h21"); var h21 = clips(h21Pack);
        assertEquals("guardian_hunter_h21", h21Pack.get("model").getAsString());
        assertEquals(19, h21.size()); assertEquals(h20.keySet(), h21.keySet());
        int unchanged = 0;
        for (String name : h20.keySet()) if (!Set.of(READY, ATTACK).contains(name)) {
            assertEquals(h20.get(name), h21.get(name), name); unchanged++;
        }
        assertEquals(17, unchanged);
    }

    @Test void artistRigSkinHierarchyAndAllOtherClipDataArePreserved() throws Exception {
        var old = art("h20"); var next = art("h21");
        for (var e : old.entrySet()) if (!Set.of("name", "model_identifier", "animations").contains(e.getKey()))
            assertEquals(e.getValue(), next.get(e.getKey()), e.getKey());
        assertEquals("guardian_hunter_h21", next.get("name").getAsString());
        assertEquals("guardian_hunter_h21", next.get("model_identifier").getAsString());
        for (var e : clips(old).entrySet()) if (!Set.of(READY, ATTACK).contains(e.getKey()))
            assertEquals(e.getValue(), clips(next).get(e.getKey()), e.getKey());
        var artClips = clips(next); var packClips = clips(resource("h21"));
        for (var e : packClips.entrySet()) assertEquals(artClips.get(e.getKey()), e.getValue());
    }

    @Test void upperBodyChannelsAndNativeEquipmentPivotsAreNotReauthored() throws Exception {
        var old = clips(resource("h20")); var next = clips(resource("h21"));
        for (String name : Set.of(READY, ATTACK)) {
            var before = animators(old.get(name)); var after = animators(next.get(name));
            assertEquals(before.keySet(), after.keySet());
            for (String bone : before.keySet()) {
                if (LEGS.contains(bone)) continue;
                if (bone.equals("player_root")) assertEquals(keys(old.get(name), bone, "rotation"), keys(next.get(name), bone, "rotation"));
                else assertEquals(before.get(bone), after.get(bone), name + ":" + bone);
            }
        }
    }

    @Test void lowerBodyAndFloorFitAreAuthoredAtEveryFortyHzSampleWithoutFlightOffset() throws Exception {
        var clips = clips(resource("h21")); var ids = new java.util.HashSet<String>();
        for (String name : Set.of(READY, ATTACK)) {
            var clip = clips.get(name); assertEquals(40, clip.get("snapping").getAsInt());
            int count = (int) Math.round(clip.get("length").getAsDouble() * 40) + 1;
            for (String bone : Set.of("player_root", "prl_right_leg", "prfl_right_foreleg", "pll_left_leg", "plfl_left_foreleg")) {
                var samples = keys(clip, bone, bone.equals("player_root") ? "position" : "rotation");
                assertEquals(count, samples.size());
                for (int i = 0; i < count; i++) {
                    var key = samples.get(i);
                    assertEquals(i / 40.0, key.get("time").getAsDouble(), EPS);
                    assertEquals("linear", key.get("interpolation").getAsString());
                    assertTrue(ids.add(key.get("uuid").getAsString()));
                    var data = key.getAsJsonArray("data_points").get(0).getAsJsonObject();
                    for (String axis : List.of("x", "y", "z")) assertTrue(Double.isFinite(data.get(axis).getAsDouble()));
                    if (bone.equals("player_root")) {
                        assertEquals(0, data.get("x").getAsDouble(), EPS); assertEquals(0, data.get("z").getAsDouble(), EPS);
                        assertTrue(data.get("y").getAsDouble() <= 0, "Entity supplies lift; asset lowers only");
                        assertTrue(data.get("y").getAsDouble() > -4);
                    }
                }
            }
        }
    }

    @Test void asymmetricalForwardKneesHoldThroughReleaseAndRecoverToCrouchedReady() throws Exception {
        var clips = clips(resource("h21")); var attack = clips.get(ATTACK); var ready = clips.get(READY);
        assertEquals(.90, attack.get("length").getAsDouble(), EPS); assertEquals("once", attack.get("loop").getAsString());
        assertEquals(2.4, ready.get("length").getAsDouble(), EPS); assertEquals("loop", ready.get("loop").getAsString());
        samePose(attack, 0, ready, 0); samePose(attack, .90, ready, 0); samePose(ready, 0, ready, 2.4);
        samePose(attack, .25, attack, .30);
        assertEquals(58, sample(attack, "prl_right_leg", "rotation", .25).x, EPS);
        assertEquals(82, sample(attack, "pll_left_leg", "rotation", .25).x, EPS);
        assertEquals(-108, sample(attack, "prfl_right_foreleg", "rotation", .25).x, EPS);
        assertEquals(-132, sample(attack, "plfl_left_foreleg", "rotation", .25).x, EPS);
        assertTrue(sample(attack, "player_root", "position", .25).y < -2);
        var m = fk(art("h21"), attack, .25);
        var left = point(m.get("plfl_left_foreleg"), 0, 0, 0); var right = point(m.get("prfl_right_foreleg"), 0, 0, 0);
        assertTrue(left.y > right.y + 1); assertTrue(left.z < right.z - .5);
    }

    @Test void everyServerTickRetainsNockContactCheekAndAuthoritativeArrowDirection() throws Exception {
        var model = art("h21"); var attack = clips(resource("h21")).get(ATTACK);
        double[] nocks = {3.27, 3.27, 3.27, 5, 6.75, 8.24, 8.24};
        double[] pitches = {-30, -20, -12, -6, -2, 0, 0};
        for (int tick = 0; tick <= 6; tick++) {
            var matrices = fk(model, attack, tick / 20.0);
            var right = point(matrices.get("pri_right_item"), 0, 0, 0);
            var nock = point(matrices.get("pli_left_item"), 0, 2, nocks[tick]);
            assertTrue(right.distance(nock) < .0001, "tick=" + tick + " gap=" + right.distance(nock));
            var arrow = matrices.get("pli_left_item").transformDirection(new Vector3d(0, 0, -1));
            var expected = new Matrix4d().rotateX(Math.toRadians(pitches[tick])).transformDirection(new Vector3d(0, 0, -1));
            assertTrue(arrow.dot(expected) > .99999);
            if (tick >= 5) assertTrue(right.distance(point(matrices.get("h_ph_head"), 4.2, 3, -2.6)) < .0001);
        }
    }

    @Test void everyHalfTickMovesUpperLandmarksOnlyBySharedGroundFitTranslation() throws Exception {
        var old = art("h20"); var next = art("h21");
        for (String name : Set.of(READY, ATTACK)) {
            var a = clips(old).get(name); var b = clips(next).get(name);
            for (int frame = 0; frame <= Math.round(b.get("length").getAsDouble() * 40); frame++) {
                double time = frame / 40.0;
                var before = fk(old, a, time); var after = fk(next, b, time);
                double dy = sample(b, "player_root", "position", time).y - sample(a, "player_root", "position", time).y;
                for (String bone : animators(a).keySet()) if (!LEGS.contains(bone)) {
                    for (var local : List.of(new Vector3d(), new Vector3d(0, 2, 8.24), new Vector3d(4.2, 3, -2.6))) {
                        var expected = before.get(bone).transformPosition(new Vector3d(local)).add(0, dy, 0);
                        var actual = after.get(bone).transformPosition(new Vector3d(local));
                        assertTrue(expected.distance(actual) < EPS, name + ":" + bone + ":" + time);
                    }
                }
            }
        }
    }
}
