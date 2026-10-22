package kim.biryeong.destiny.fx;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/** Asset-only, full-chain FK regression tests. No game, scheduler, or runtime classes. */
class HunterAnimationH19Test {
    private static final Path ART = Path.of("art/blockbench/animations");
    private static final String READY = "h15_super_void";
    private static final String ATTACK = READY + "_attack";
    private static final double EPS = .001;

    private JsonObject artist(String version) throws Exception {
        return JsonParser.parseString(Files.readString(ART.resolve("guardian_hunter_" + version + ".bbmodel")))
                .getAsJsonObject();
    }

    private JsonObject pack() throws Exception {
        try (var stream = getClass().getResourceAsStream("/destiny/animation/hunter_h19.animation.json")) {
            assertNotNull(stream, "The H19 pack must be present independently of runtime model selection");
            return JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }

    private Map<String, JsonObject> clips(JsonObject model) {
        var result = new HashMap<String, JsonObject>();
        for (var value : model.getAsJsonArray("animations")) {
            var clip = value.getAsJsonObject();
            assertNull(result.put(clip.get("name").getAsString(), clip), "Duplicate clip ID");
        }
        return result;
    }

    @Test
    void h19PreservesTheCompleteRigAndAllEightOtherCompatibilityClips() throws Exception {
        var source = artist("h15");
        var model = artist("h19");
        var pack = pack();
        assertEquals("guardian_hunter_h19", model.get("name").getAsString());
        assertEquals(model.get("name"), model.get("model_identifier"));
        assertEquals(model.get("name"), pack.get("model"));
        for (var entry : source.entrySet()) {
            if (!Set.of("name", "model_identifier", "animations").contains(entry.getKey()))
                assertEquals(entry.getValue(), model.get(entry.getKey()), entry.getKey());
        }
        var original = clips(source);
        var current = clips(model);
        assertEquals(original.keySet(), current.keySet());
        for (var entry : original.entrySet()) {
            if (!Set.of(READY, ATTACK).contains(entry.getKey()))
                assertEquals(entry.getValue(), current.get(entry.getKey()), entry.getKey());
        }
        var exported = clips(pack);
        assertEquals(10, exported.size());
        assertEquals(original.keySet().stream().filter(n -> n.startsWith("h15_")).collect(Collectors.toSet()),
                exported.keySet());
        exported.forEach((name, clip) -> assertEquals(current.get(name), clip, name));
    }

    @Test
    void lowReadyAndAttackEndpointsMatchAndFullDrawHoldsUntilElapsedTickSeven() throws Exception {
        var model = artist("h19");
        var clips = clips(pack());
        var ready = clips.get(READY);
        var attack = clips.get(ATTACK);
        assertEquals("loop", ready.get("loop").getAsString());
        assertEquals(.90, attack.get("length").getAsDouble(), EPS);
        assertEquals(7, 1 + Math.round(.30 * 20), "One transition tick plus six clip ticks");
        assertPosesEqual(sample(ready, 0), sample(ready, 2.4));
        assertPosesEqual(sample(ready, 0), sample(attack, 0));
        assertPosesEqual(sample(ready, 0), sample(attack, .90));
        assertPosesEqual(sample(attack, .25), sample(attack, .275));
        assertPosesEqual(sample(attack, .25), sample(attack, .30));
        for (var animator : attack.getAsJsonObject("animators").asMap().values()) {
            boolean releaseKey = false;
            for (var keyValue : animator.getAsJsonObject().getAsJsonArray("keyframes")) {
                var key = keyValue.getAsJsonObject();
                assertEquals("linear", key.get("interpolation").getAsString(), "No spline pre-release drift");
                releaseKey |= Math.abs(key.get("time").getAsDouble() - .30) < EPS;
            }
            assertTrue(releaseKey, "Every animated bone has an explicit .30 release boundary");
        }
        var idle = fk(model, sample(ready, 0));
        assertTrue(origin(idle.get("pli_left_item"))[1] < origin(idle.get("h_ph_head"))[1] - 3);
        assertPoint(point(idle.get("pli_left_item"), new double[]{0, 2, 3.27}),
                origin(idle.get("pri_right_item")), "Low-ready hand touches relaxed nock");
    }

    @Test
    void fullDrawActuallyContactsTheRightCheekAndDrawnNockWithAnExtendedLeftArm() throws Exception {
        var model = artist("h19");
        var attack = clips(pack()).get(ATTACK);
        for (double time : new double[]{.25, .275, .30}) {
            var world = fk(model, sample(attack, time));
            double[] left = origin(world.get("pli_left_item"));
            double[] right = origin(world.get("pri_right_item"));
            double[] head = origin(world.get("h_ph_head"));
            double[] elbow = origin(world.get("prfa_right_forearm"));
            assertPoint(point(world.get("h_ph_head"), new double[]{4.2, 3, -2.6}), right, "Right cheek anchor");
            // Model grip (8,8,8); drawn nock (16.24,8,8). Left display Ry(-90)
            // turns +8.24 model-X into +8.24 world-Z; display adds two units Y.
            assertPoint(point(world.get("pli_left_item"), new double[]{0, 2, 8.24}), right, "Drawn nock contact");
            assertEquals(right[1], point(world.get("pli_left_item"), new double[]{0, 2, 0})[1], EPS);
            assertTrue(distance(left, origin(world.get("pla_left_arm"))) > 10.4, "Support arm stays extended");
            assertTrue(left[2] < head[2] - 9, "Bow is in front of the -Z-facing skin");
            assertTrue(elbow[2] > head[2] + 1, "Draw elbow passes behind head center");
            assertTrue(elbow[0] > right[0] + 2, "Draw elbow flares on the character right");
            double[] aim = vector(world.get("pli_left_item"), new double[]{0, 0, -1});
            assertPoint(new double[]{0, 0, -1}, aim, "Item cancels root/chest/arm/bind rotations before display");
        }
        var follow = fk(model, sample(attack, .35));
        var held = fk(model, sample(attack, .30));
        assertPoint(origin(held.get("pli_left_item")), origin(follow.get("pli_left_item")), "Bow hand stays put on release");
        assertTrue(distance(origin(follow.get("pri_right_item")),
                point(follow.get("pli_left_item"), new double[]{0, 2, 8.24})) > 1.5,
                "Right hand separates from the string after .30");
    }

    @Test
    void everyInterpolatedFrameHasFiniteTransformsAndNoHorizontalRootSlide() throws Exception {
        var model = artist("h19");
        var attack = clips(pack()).get(ATTACK);
        for (int i = 0; i <= 180; i++) {
            var pose = sample(attack, i / 200.0);
            var root = pose.get("player_root")[1];
            assertEquals(0, root[0], EPS);
            assertEquals(0, root[2], EPS);
            for (var matrix : fk(model, pose).values())
                for (var row : matrix)
                    for (double value : row) assertTrue(Double.isFinite(value));
        }
    }

    // Independent Java FK: hierarchy traversal, bind rotations, sampled local
    // animation and root position. Coordinates are artist BB units, not game pixels.
    private Map<String, double[][]> sample(JsonObject clip, double time) {
        var result = new HashMap<String, double[][]>();
        for (var entry : clip.getAsJsonObject("animators").asMap().values()) {
            var animator = entry.getAsJsonObject();
            var channels = new double[2][3];
            for (int channel = 0; channel < 2; channel++) {
                String name = channel == 0 ? "rotation" : "position";
                JsonObject before = null, after = null;
                for (var keyValue : animator.getAsJsonArray("keyframes")) {
                    var key = keyValue.getAsJsonObject();
                    if (!name.equals(key.get("channel").getAsString())) continue;
                    double t = key.get("time").getAsDouble();
                    if (t <= time && (before == null || t > before.get("time").getAsDouble())) before = key;
                    if (t >= time && (after == null || t < after.get("time").getAsDouble())) after = key;
                }
                if (before == null) before = after;
                if (after == null) after = before;
                if (before == null) continue;
                double t0 = before.get("time").getAsDouble(), t1 = after.get("time").getAsDouble();
                double fraction = t0 == t1 ? 0 : (time - t0) / (t1 - t0);
                var a = before.getAsJsonArray("data_points").get(0).getAsJsonObject();
                var b = after.getAsJsonArray("data_points").get(0).getAsJsonObject();
                for (int axis = 0; axis < 3; axis++) {
                    String xyz = "xyz".substring(axis, axis + 1);
                    channels[channel][axis] = a.get(xyz).getAsDouble()
                            + fraction * (b.get(xyz).getAsDouble() - a.get(xyz).getAsDouble());
                }
            }
            result.put(animator.get("name").getAsString(), channels);
        }
        return result;
    }

    private Map<String, double[][]> fk(JsonObject model, Map<String, double[][]> pose) {
        var groups = new HashMap<String, JsonObject>();
        for (var value : model.getAsJsonArray("groups")) {
            var group = value.getAsJsonObject();
            groups.put(group.get("uuid").getAsString(), group);
        }
        var result = new HashMap<String, double[][]>();
        walk(model.getAsJsonArray("outliner"), groups, pose, identity(), new double[3], result);
        return result;
    }

    private void walk(JsonArray nodes, Map<String, JsonObject> groups, Map<String, double[][]> pose,
                      double[][] parent, double[] parentOrigin, Map<String, double[][]> result) {
        for (var node : nodes) {
            if (!node.isJsonObject()) continue;
            var object = node.getAsJsonObject();
            var group = groups.get(object.get("uuid").getAsString());
            String name = group.get("name").getAsString();
            double[] origin = xyz(group.getAsJsonArray("origin"));
            double[] angles = group.has("rotation") ? xyz(group.getAsJsonArray("rotation")) : new double[3];
            double[][] animation = pose.getOrDefault(name, new double[2][3]);
            var translation = identity();
            for (int i = 0; i < 3; i++) {
                angles[i] += animation[0][i];
                translation[i][3] = origin[i] - parentOrigin[i] + animation[1][i];
            }
            var matrix = mm(parent, mm(translation, rotation(angles)));
            result.put(name, matrix);
            walk(object.getAsJsonArray("children"), groups, pose, matrix, origin, result);
        }
    }

    private double[] xyz(JsonArray array) {
        return new double[]{array.get(0).getAsDouble(), array.get(1).getAsDouble(), array.get(2).getAsDouble()};
    }

    private double[][] identity() {
        return new double[][]{{1, 0, 0, 0}, {0, 1, 0, 0}, {0, 0, 1, 0}, {0, 0, 0, 1}};
    }

    private double[][] rotation(double[] angles) {
        double x = Math.toRadians(angles[0]), y = Math.toRadians(angles[1]), z = Math.toRadians(angles[2]);
        double cx = Math.cos(x), sx = Math.sin(x), cy = Math.cos(y), sy = Math.sin(y), cz = Math.cos(z), sz = Math.sin(z);
        double[][] rx = {{1, 0, 0, 0}, {0, cx, -sx, 0}, {0, sx, cx, 0}, {0, 0, 0, 1}};
        double[][] ry = {{cy, 0, sy, 0}, {0, 1, 0, 0}, {-sy, 0, cy, 0}, {0, 0, 0, 1}};
        double[][] rz = {{cz, -sz, 0, 0}, {sz, cz, 0, 0}, {0, 0, 1, 0}, {0, 0, 0, 1}};
        return mm(rz, mm(ry, rx));
    }

    private double[][] mm(double[][] a, double[][] b) {
        var result = new double[4][4];
        for (int i = 0; i < 4; i++) for (int j = 0; j < 4; j++)
            for (int k = 0; k < 4; k++) result[i][j] += a[i][k] * b[k][j];
        return result;
    }

    private double[] vector(double[][] matrix, double[] value) {
        var result = new double[3];
        for (int i = 0; i < 3; i++) for (int j = 0; j < 3; j++) result[i] += matrix[i][j] * value[j];
        return result;
    }

    private double[] point(double[][] matrix, double[] value) {
        var result = vector(matrix, value);
        for (int i = 0; i < 3; i++) result[i] += matrix[i][3];
        return result;
    }

    private double[] origin(double[][] matrix) { return point(matrix, new double[3]); }

    private double distance(double[] a, double[] b) {
        double sum = 0;
        for (int i = 0; i < 3; i++) sum += (a[i] - b[i]) * (a[i] - b[i]);
        return Math.sqrt(sum);
    }

    private void assertPoint(double[] expected, double[] actual, String message) {
        assertArrayEquals(expected, actual, EPS, message);
    }

    private void assertPosesEqual(Map<String, double[][]> a, Map<String, double[][]> b) {
        assertEquals(a.keySet(), b.keySet());
        for (var name : a.keySet()) for (int i = 0; i < 2; i++)
            assertArrayEquals(a.get(name)[i], b.get(name)[i], EPS, name);
    }
}
