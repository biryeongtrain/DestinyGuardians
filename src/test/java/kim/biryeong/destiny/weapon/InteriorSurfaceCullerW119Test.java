package kim.biryeong.destiny.weapon;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.joml.Matrix4d;
import org.joml.Vector3d;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;
import java.util.function.Function;
import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.*;

/** Independent W119 safety oracle. Calls the real helper; never joins rigid moving parts.
 * Expected geometry uses homogeneous JOML transforms, not the helper's expanded matrix.
 * This verifies conservative geometry/PNG alpha, not camera visibility or GPU performance.
 */
class InteriorSurfaceCullerW119Test {
    private static final List<String> FACES = List.of("north", "south", "east", "west", "up", "down");
    private static final Path RESOURCES = Path.of("src/main/resources");
    private static final BufferedImage OPAQUE = opaque(16, 16);
    private static final Function<String, BufferedImage> SOLID = id -> OPAQUE;

    private static JsonArray array(double... numbers) {
        var result = new JsonArray();
        for (double n : numbers) result.add(n);
        return result;
    }

    private static JsonObject box(String name, double[] from, double[] to) {
        var e = new JsonObject();
        e.addProperty("name", name);
        e.add("from", array(from)); e.add("to", array(to));
        var faces = new JsonObject();
        for (String direction : FACES) {
            var face = new JsonObject();
            face.addProperty("texture", "#solid"); face.add("uv", array(4, 4, 8, 8));
            faces.add(direction, face);
        }
        e.add("faces", faces);
        return e;
    }

    private static JsonObject cube(String name, double lo, double hi) {
        return box(name, new double[]{lo, lo, lo}, new double[]{hi, hi, hi});
    }

    private static JsonObject model(JsonObject... elements) {
        var model = new JsonObject(); var textures = new JsonObject();
        textures.addProperty("solid", "destiny:w119_solid"); model.add("textures", textures);
        var all = new JsonArray(); for (var e : elements) all.add(e);
        model.add("elements", all);
        return model;
    }

    private static JsonObject pair() { return model(cube("shell", 0, 16), cube("inside", 4, 12)); }
    private static JsonObject element(JsonObject model, int index) { return model.getAsJsonArray("elements").get(index).getAsJsonObject(); }
    private static JsonObject face(JsonObject element, String direction) { return element.getAsJsonObject("faces").getAsJsonObject(direction); }
    private static Set<String> names(JsonObject model) {
        var names = new HashSet<String>();
        for (var e : model.getAsJsonArray("elements")) assertTrue(names.add(e.getAsJsonObject().get("name").getAsString()));
        return names;
    }

    private static BufferedImage opaque(int width, int height) {
        var image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        for (int y = 0; y < height; y++) for (int x = 0; x < width; x++) image.setRGB(x, y, 0xff43617f);
        return image;
    }

    private static void preserved(JsonObject input, Function<String, BufferedImage> loader) {
        var before = input.deepCopy(); var result = InteriorSurfaceCuller.cull(input, loader);
        assertEquals(before, input, "Input must not be mutated");
        assertEquals(before, result.model(), "Unsupported or exposed geometry must survive");
        assertTrue(result.removals().isEmpty()); assertNotSame(input, result.model());
    }

    private static InteriorSurfaceCuller.Result removed(JsonObject input, String name, String container, double margin) {
        var before = input.deepCopy(); var result = InteriorSurfaceCuller.cull(input, SOLID);
        assertEquals(before, input);
        assertEquals(List.of(new InteriorSurfaceCuller.Removal(name, container, margin)), result.removals());
        assertFalse(names(result.model()).contains(name)); assertTrue(names(result.model()).contains(container));
        return result;
    }

    @Test void strictlyInteriorCuboidIsRemovedWithExactClearance() { removed(pair(), "inside", "shell", 4); }

    @TestFactory Stream<DynamicTest> touchingAndProtrudingPlanesSurviveOnEveryBoundary() {
        var cases = new ArrayList<DynamicTest>();
        for (int axis = 0; axis < 3; axis++) for (int side = 0; side < 2; side++) for (double offset : new double[]{0, .01}) {
            int a = axis, s = side;
            cases.add(DynamicTest.dynamicTest("axis=" + a + " side=" + s + " protrusion=" + offset, () -> {
                double[] lo = {4, 4, 4}, hi = {12, 12, 12};
                lo[a] = hi[a] = s == 0 ? -offset : 16 + offset;
                preserved(model(cube("shell", 0, 16), box("exposed-plane", lo, hi)), SOLID);
            }));
        }
        return cases.stream();
    }

    @Test void strictlyInteriorZeroThicknessPlaneCanBeRemoved() {
        removed(model(cube("shell", 0, 16), box("plane", new double[]{4, 4, 8}, new double[]{12, 12, 8})), "plane", "shell", 4);
    }

    @Test void centerInsideDoesNotLicenseOneEscapingCorner() {
        var plane = box("rotated-plane", new double[]{2, 2, 8}, new double[]{14, 14, 8});
        plane.add("rotation", rotation(new double[]{8, 8, 8}, 0, 0, 45));
        assertTrue(corners(plane).stream().anyMatch(p -> p.x < 0 || p.x > 16 || p.y < 0 || p.y > 16));
        preserved(model(cube("shell", 0, 16), plane), SOLID);
    }

    @Test void nearTouchingRoundoffMarginIsConservative() {
        preserved(model(cube("shell", 0, 16), cube("near", .00005, 15)), SOLID);
        removed(model(cube("shell", 0, 16), cube("safe", .001, 15)), "safe", "shell", .001);
    }

    @TestFactory Stream<DynamicTest> alphaInsideOrOneTexelOutsideUvPreventsOcclusion() {
        // UV [4,4,8,8] at 16px touches [4..7]; immediate filtering neighbours are 3 and 8.
        return Stream.of(new int[]{5, 5}, new int[]{3, 5}, new int[]{8, 5}, new int[]{5, 3}, new int[]{5, 8}, new int[]{3, 3}, new int[]{8, 8})
                .flatMap(pixel -> Stream.of(0, 254).map(alpha -> DynamicTest.dynamicTest("alpha=" + alpha + " pixel=" + pixel[0] + "," + pixel[1], () -> {
                    var image = opaque(16, 16); image.setRGB(pixel[0], pixel[1], alpha << 24 | 0x43617f);
                    preserved(pair(), id -> image);
                })));
    }

    @Test void transparencyTwoTexelsAwayDoesNotBlockOpaqueUvIsland() {
        var image = opaque(16, 16); image.setRGB(2, 5, 0); image.setRGB(9, 5, 0);
        assertEquals(1, InteriorSurfaceCuller.cull(pair(), id -> image).removals().size());
    }

    @Test void uvNeighbourhoodScalesToNonSquareRealPixelDimensions() {
        var image = opaque(64, 32); image.setRGB(15, 10, 0);
        preserved(pair(), id -> image); // U=4 maps to x=16, so x=15 is its neighbour.
        image.setRGB(15, 10, 0xff000000); image.setRGB(14, 10, 0);
        assertEquals(1, InteriorSurfaceCuller.cull(pair(), id -> image).removals().size());
    }

    @Test void reversedUvAndQuarterTurnFaceRotationStillAllowSolidContainer() {
        var input = pair();
        for (String direction : FACES) { var f = face(element(input, 0), direction); f.add("uv", array(8, 8, 4, 4)); f.addProperty("rotation", 90); }
        removed(input, "inside", "shell", 4);
    }

    @TestFactory Stream<DynamicTest> eachMissingFacePreventsContainerUse() {
        return FACES.stream().map(direction -> DynamicTest.dynamicTest(direction, () -> {
            var input = pair(); element(input, 0).getAsJsonObject("faces").remove(direction); preserved(input, SOLID);
        }));
    }

    @TestFactory Stream<DynamicTest> conditionalOrTintedFacesCannotCertifyOpaqueContainer() {
        return Stream.of("cullface", "tintindex").flatMap(field -> FACES.stream().map(direction -> DynamicTest.dynamicTest(field + ":" + direction, () -> {
            var input = pair(); var f = face(element(input, 0), direction);
            if (field.equals("cullface")) f.addProperty(field, direction); else f.addProperty(field, 0);
            preserved(input, SOLID);
        })));
    }

    @TestFactory Stream<DynamicTest> malformedUvAndMissingTexturesFailClosed() {
        Map<String, Consumer<JsonObject>> changes = Map.of(
                "missing-uv", f -> f.remove("uv"), "short-uv", f -> f.add("uv", array(4, 4, 8)),
                "zero-uv", f -> f.add("uv", array(4, 4, 4, 8)), "outside-uv", f -> f.add("uv", array(-1, 4, 8, 8)),
                "nan-uv", f -> f.add("uv", array(4, Double.NaN, 8, 8)), "missing-texture", f -> f.remove("texture"));
        return changes.entrySet().stream().map(change -> DynamicTest.dynamicTest(change.getKey(), () -> {
            var input = pair(); change.getValue().accept(face(element(input, 0), "north")); preserved(input, SOLID);
        }));
    }

    @Test void missingOrThrowingTextureLoaderCannotCertifyContainer() {
        preserved(pair(), id -> null); preserved(pair(), id -> { throw new IllegalArgumentException("unavailable PNG"); });
    }

    @Test void textureAliasesResolveButCyclesMissingAndUnsafeIdsFailClosed() {
        var valid = pair(); valid.getAsJsonObject("textures").addProperty("solid", "#alias");
        valid.getAsJsonObject("textures").addProperty("alias", "destiny:w119_solid"); removed(valid, "inside", "shell", 4);
        for (String alias : List.of("#solid", "#missing", "bad texture", "destiny:../escape")) {
            var input = pair(); input.getAsJsonObject("textures").addProperty("solid", alias); preserved(input, SOLID);
        }
        var cycle = pair(); cycle.getAsJsonObject("textures").addProperty("solid", "#b");
        cycle.getAsJsonObject("textures").addProperty("b", "#c"); cycle.getAsJsonObject("textures").addProperty("c", "#solid");
        preserved(cycle, SOLID);
    }

    @TestFactory Stream<DynamicTest> unsupportedParentRenderModeRescaleAndRotationStayUnchanged() {
        Map<String, Consumer<JsonObject>> changes = Map.ofEntries(
                Map.entry("parent", m -> m.addProperty("parent", "minecraft:block/cube_all")),
                Map.entry("render-type", m -> m.addProperty("render_type", "translucent")),
                Map.entry("rescale", m -> { var r = rotation(new double[]{8, 8, 8}, 12, 0, 0); r.addProperty("rescale", true); element(m, 0).add("rotation", r); }),
                Map.entry("bad-axis", m -> element(m, 0).add("rotation", JsonParser.parseString("{\"origin\":[8,8,8],\"axis\":\"xy\",\"angle\":15}"))),
                Map.entry("mixed-axis-euler", m -> element(m, 0).add("rotation", JsonParser.parseString("{\"origin\":[8,8,8],\"axis\":\"x\",\"angle\":15,\"y\":12}"))),
                Map.entry("unknown-rotation", m -> { var r = rotation(new double[]{8, 8, 8}, 0, 0, 0); r.addProperty("quaternion", 1); element(m, 1).add("rotation", r); }),
                Map.entry("missing-origin", m -> element(m, 1).add("rotation", JsonParser.parseString("{\"x\":15}"))),
                Map.entry("unknown-element-field", m -> element(m, 1).addProperty("inflate", 2)));
        return changes.entrySet().stream().map(change -> DynamicTest.dynamicTest(change.getKey(), () -> { var input = pair(); change.getValue().accept(input); preserved(input, SOLID); }));
    }

    @TestFactory Stream<DynamicTest> nonfiniteCoordinatesPivotsAndAnglesStayUnchanged() {
        var tests = new ArrayList<DynamicTest>();
        for (double bad : new double[]{Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY}) {
            for (String field : List.of("from", "to", "origin", "angle")) for (int axis = 0; axis < 3; axis++) {
                int a = axis;
                tests.add(DynamicTest.dynamicTest(field + "[" + a + "]=" + bad, () -> {
                    var input = pair(); var e = element(input, 1);
                    if (field.equals("from") || field.equals("to")) e.getAsJsonArray(field).set(a, new com.google.gson.JsonPrimitive(bad));
                    else { var r = rotation(new double[]{8, 8, 8}, 0, 0, 0); if (field.equals("origin")) r.getAsJsonArray("origin").set(a, new com.google.gson.JsonPrimitive(bad)); else r.addProperty("xyz".substring(a, a + 1), bad); e.add("rotation", r); }
                    preserved(input, SOLID);
                }));
            }
        }
        return tests.stream();
    }

    @Test void duplicateOrMissingProvenanceAndMalformedBoundsArePreserved() {
        var duplicate = pair(); element(duplicate, 1).addProperty("name", "shell"); preserved(duplicate, SOLID);
        var unnamed = pair(); element(unnamed, 1).remove("name"); preserved(unnamed, SOLID);
        var reversed = pair(); element(reversed, 1).add("to", array(3, 12, 12)); preserved(reversed, SOLID);
        var shortVector = pair(); element(shortVector, 1).add("from", array(4, 4)); preserved(shortVector, SOLID);
    }

    private static JsonObject rotation(double[] pivot, double x, double y, double z) {
        var r = new JsonObject(); r.add("origin", array(pivot)); r.addProperty("x", x); r.addProperty("y", y); r.addProperty("z", z); return r;
    }

    private static double coordinate(JsonArray values, int axis) { return values.get(axis).getAsDouble(); }
    private static Matrix4d transform(JsonObject e) {
        var matrix = new Matrix4d(); if (!e.has("rotation")) return matrix;
        var r = e.getAsJsonObject("rotation"); var p = r.getAsJsonArray("origin");
        double x = 0, y = 0, z = 0;
        if (r.has("axis")) {
            double angle = Math.toRadians(r.get("angle").getAsDouble());
            switch (r.get("axis").getAsString()) { case "x" -> x = angle; case "y" -> y = angle; case "z" -> z = angle; default -> fail("Unsupported oracle axis"); }
        } else {
            if (r.has("x")) x = Math.toRadians(r.get("x").getAsDouble()); if (r.has("y")) y = Math.toRadians(r.get("y").getAsDouble()); if (r.has("z")) z = Math.toRadians(r.get("z").getAsDouble());
        }
        // Independent library composition and homogeneous inverse; no expanded helper formula.
        return matrix.translation(coordinate(p, 0), coordinate(p, 1), coordinate(p, 2)).rotateZ(z).rotateY(y).rotateX(x)
                .translate(-coordinate(p, 0), -coordinate(p, 1), -coordinate(p, 2));
    }

    private static List<Vector3d> corners(JsonObject e) {
        var result = new ArrayList<Vector3d>(); var matrix = transform(e);
        var lo = e.getAsJsonArray("from"); var hi = e.getAsJsonArray("to");
        for (int x = 0; x < 2; x++) for (int y = 0; y < 2; y++) for (int z = 0; z < 2; z++)
            result.add(matrix.transformPosition(new Vector3d(coordinate(x == 0 ? lo : hi, 0), coordinate(y == 0 ? lo : hi, 1), coordinate(z == 0 ? lo : hi, 2))));
        return result;
    }

    private static double oracleClearance(JsonObject candidate, JsonObject container) {
        var inverse = transform(container).invert(); double margin = Double.POSITIVE_INFINITY;
        for (var corner : corners(candidate)) {
            var local = inverse.transformPosition(corner);
            for (int a = 0; a < 3; a++) margin = Math.min(margin, Math.min(local.get(a) - coordinate(container.getAsJsonArray("from"), a), coordinate(container.getAsJsonArray("to"), a) - local.get(a)));
        }
        return margin;
    }

    @Test void arbitraryMultiAxisRotationAtNonzeroPivotMatchesIndependentMatrixGeometry() {
        var candidate = box("angled", new double[]{6, 8, 7}, new double[]{10, 12, 9});
        candidate.add("rotation", rotation(new double[]{8, 10, 8}, 17.3, -61.2, 134.7));
        double margin = oracleClearance(candidate, cube("shell", 0, 20));
        var result = InteriorSurfaceCuller.cull(model(cube("shell", 0, 20), candidate), SOLID);
        assertEquals(1, result.removals().size()); assertEquals(margin, result.removals().getFirst().minClearance(), 1e-11);
        assertTrue(corners(candidate).stream().allMatch(p -> p.x > 0 && p.x < 20 && p.y > 0 && p.y < 20 && p.z > 0 && p.z < 20));
        // Place a world-space wall between the smallest rotated corner and the unrotated x=6.
        double minX = corners(candidate).stream().mapToDouble(p -> p.x).min().orElseThrow();
        assertTrue(minX < 6); double wall = (minX + 6) / 2;
        preserved(model(box("wall", new double[]{wall, 0, 0}, new double[]{20, 20, 20}), candidate), SOLID);
    }

    @Test void independentlyRotatedContainerUsesItsLocalHalfspacesNotWorldAabb() {
        var shell = box("angled-shell", new double[]{6, 8, 7}, new double[]{10, 12, 9});
        shell.add("rotation", rotation(new double[]{8, 10, 8}, 17.3, -61.2, 134.7));
        var safe = box("safe", new double[]{7.9, 9.9, 7.9}, new double[]{8.1, 10.1, 8.1});
        var result = InteriorSurfaceCuller.cull(model(shell, safe), SOLID);
        assertEquals(1, result.removals().size()); assertEquals(oracleClearance(safe, shell), result.removals().getFirst().minClearance(), 1e-11);
        var worldCorners = corners(shell);
        double minX = worldCorners.stream().mapToDouble(p -> p.x).min().orElseThrow(), minY = worldCorners.stream().mapToDouble(p -> p.y).min().orElseThrow();
        var unsafe = box("aabb-only", new double[]{minX + .01, minY + .01, 7.99}, new double[]{minX + .02, minY + .02, 8.01});
        assertTrue(oracleClearance(unsafe, shell) < 0); preserved(model(shell, unsafe), SOLID);
    }

    @Test void singleAxisRotationAndExplicitFalseRescaleAreSupported() {
        var input = pair(); element(input, 1).add("rotation", JsonParser.parseString("{\"origin\":[8,8,8],\"axis\":\"y\",\"angle\":67.4,\"rescale\":false}"));
        var result = InteriorSurfaceCuller.cull(input, SOLID);
        assertEquals(1, result.removals().size()); assertEquals(oracleClearance(element(input, 1), element(input, 0)), result.removals().getFirst().minClearance(), 1e-11);
    }

    @Test void maximalVolumeRetainedRootIsReportedForNestedContainerChainInAnyOrder() {
        for (var input : List.of(model(cube("outer", 0, 20), cube("middle", 2, 18), cube("inner", 4, 16), cube("tiny", 6, 14)),
                model(cube("tiny", 6, 14), cube("inner", 4, 16), cube("middle", 2, 18), cube("outer", 0, 20)))) {
            var result = InteriorSurfaceCuller.cull(input, SOLID); assertEquals(Set.of("outer"), names(result.model())); assertEquals(3, result.removals().size());
            for (var removal : result.removals()) { assertEquals("outer", removal.container()); assertEquals(Map.of("middle", 2d, "inner", 4d, "tiny", 6d).get(removal.name()), removal.minClearance()); }
        }
    }

    @Test void outputIsDeepCopyWithStableMetadataOrderAndIdempotentSecondPass() {
        var input = pair(); input.add("display", JsonParser.parseString("{\"gui\":{\"translation\":[1,2,3]}}")); var before = input.deepCopy();
        var first = InteriorSurfaceCuller.cull(input, SOLID); var second = InteriorSurfaceCuller.cull(first.model(), SOLID);
        assertEquals(before, input); assertEquals(first.model(), second.model()); assertTrue(second.removals().isEmpty());
        assertNotSame(first.model(), second.model()); assertNotSame(element(input, 0), element(first.model(), 0));
        assertThrows(UnsupportedOperationException.class, () -> first.removals().clear());
        element(first.model(), 0).addProperty("name", "changed"); first.model().getAsJsonObject("display").getAsJsonObject("gui").getAsJsonArray("translation").set(0, new com.google.gson.JsonPrimitive(99));
        first.model().getAsJsonObject("textures").addProperty("solid", "destiny:changed");
        assertEquals(before, input); assertEquals(Set.of("shell"), names(second.model())); assertEquals(1, second.model().getAsJsonObject("display").getAsJsonObject("gui").getAsJsonArray("translation").get(0).getAsInt());
    }

    @Test void unrelatedRigidPartsNeverSupplyEachOthersContainers() {
        var body = model(cube("body-shell", 0, 16)); var magazine = model(cube("magazine", 4, 12));
        preserved(body, SOLID); preserved(magazine, SOLID);
        assertEquals(Set.of("body-shell"), names(InteriorSurfaceCuller.cull(body, SOLID).model()));
        assertEquals(Set.of("magazine"), names(InteriorSurfaceCuller.cull(magazine, SOLID).model()));
    }

    private static int faces(JsonObject model) {
        int count = 0; for (var e : model.getAsJsonArray("elements")) count += e.getAsJsonObject().getAsJsonObject("faces").size(); return count;
    }

    @Test void actualBlastFurnaceAndHammerheadPartsUseRealPngsAndIndependentRetainedContainerAudit() throws IOException {
        var cache = new HashMap<String, BufferedImage>();
        Function<String, BufferedImage> loader = id -> cache.computeIfAbsent(id, key -> {
            String[] resource = key.split(":", 2);
            Path path = RESOURCES.resolve("assets").resolve(resource[0]).resolve("textures").resolve(resource[1] + ".png");
            try { var image = ImageIO.read(path.toFile()); assertNotNull(image, "Actual PNG: " + path); return image; } catch (IOException ex) { throw new AssertionError(path.toString(), ex); }
        });
        Map<String, int[]> expected = Map.of("blast_furnace_body", new int[]{1744, 1372, 5299, 4717}, "blast_furnace_magazine", new int[]{49, 47, 260, 249},
                "hammerhead_body", new int[]{624, 618, 3744, 3708}, "hammerhead_magazine", new int[]{562, 559, 1508, 1502}, "hammerhead_cover", new int[]{143, 142, 858, 852});
        for (String part : List.of("blast_furnace_body", "blast_furnace_magazine", "hammerhead_body", "hammerhead_magazine", "hammerhead_cover")) {
            var input = JsonParser.parseString(Files.readString(RESOURCES.resolve("assets/destiny/models/weapon_surface_w115/" + part + ".json"))).getAsJsonObject();
            var before = input.deepCopy(); var result = InteriorSurfaceCuller.cull(input, loader); assertEquals(before, input);
            int[] actual = {input.getAsJsonArray("elements").size(), result.model().getAsJsonArray("elements").size(), faces(input), faces(result.model())};
            System.out.printf("W119 %s elements %d -> %d; faces %d -> %d; removals %d%n", part, actual[0], actual[1], actual[2], actual[3], result.removals().size());
            assertArrayEquals(expected.get(part), actual, part + " baseline product counts");
            var originals = new HashMap<String, JsonObject>(); for (var e : input.getAsJsonArray("elements")) originals.put(e.getAsJsonObject().get("name").getAsString(), e.getAsJsonObject());
            Set<String> kept = names(result.model()), removed = new HashSet<>();
            for (var audit : result.removals()) {
                assertTrue(removed.add(audit.name())); assertTrue(kept.contains(audit.container()), "Audit must identify a retained same-part root"); assertFalse(kept.contains(audit.name()));
                assertNotNull(originals.get(audit.name())); assertNotNull(originals.get(audit.container()));
                double margin = oracleClearance(originals.get(audit.name()), originals.get(audit.container()));
                assertTrue(margin > .0001, part + ": every rendered corner must be strictly inside"); assertEquals(margin, audit.minClearance(), 1e-9);
                assertEquals(Set.copyOf(FACES), originals.get(audit.container()).getAsJsonObject("faces").keySet());
            }
            for (var e : result.model().getAsJsonArray("elements")) assertEquals(originals.get(e.getAsJsonObject().get("name").getAsString()), e);
            assertEquals(actual[0] - actual[1], removed.size());
            var second = InteriorSurfaceCuller.cull(result.model(), loader); assertEquals(result.model(), second.model()); assertTrue(second.removals().isEmpty());
        }
        assertEquals(2, cache.size(), "Both real weapon PNGs must be loaded");
    }
}
