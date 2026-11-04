package kim.biryeong.destiny.weapon;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonPrimitive;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import net.minecraft.world.item.ItemDisplayContext;
import org.joml.Matrix4f;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Source assets plus actual 26.3 client-JAR codecs; no server/game runtime needed. */
class WeaponScopeAssetsW45Test {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");
    private static final List<String> IDS = List.of(
            "bite_of_the_fox", "beloved", "apostate", "line_in_the_sand", "stormchaser");
    private static final Set<String> LFRS = Set.of("line_in_the_sand", "stormchaser");

    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }

    private static JsonObject ads(JsonObject item) {
        return item.getAsJsonObject("model").getAsJsonArray("cases").asList().stream()
                .map(JsonElement::getAsJsonObject)
                .filter(c -> "ads".equals(c.get("when").getAsString()))
                .findFirst().orElseThrow().getAsJsonObject("model");
    }

    @Test void legacyFiveAndIzanagiHaveScopeRoutes() throws Exception {
        assertFalse(WeaponScopes.supports(null));
        for (var entry : WeaponCatalog.all()) {
            assertEquals(IDS.contains(entry.id()) || entry.id().equals("izanagis_burden"), WeaponScopes.supports(entry), entry.id());
            if (WeaponScopes.supports(entry)) {
                assertEquals("destiny:weapon_scope_w45/" + entry.id(), WeaponScopes.model(entry).toString());
            } else {
                assertThrows(IllegalArgumentException.class, () -> WeaponScopes.model(entry));
            }
        }
        try (var files = Files.list(ROOT.resolve("items/weapon_scope_w45"))) {
            assertEquals(java.util.stream.Stream.concat(IDS.stream(), java.util.stream.Stream.of("izanagis_burden"))
                            .map(id -> id + ".json").collect(java.util.stream.Collectors.toSet()),
                    files.map(path -> path.getFileName().toString()).collect(java.util.stream.Collectors.toSet()));
        }
    }

    @Test void firstPersonHidesOnlySnipersAndLfrKeeps3dGunWhileEveryOtherContextKeepsExactAdsAndGrip() throws Exception {
        for (String id : IDS) {
            var original = json(ROOT.resolve("items/weapon/" + id + ".json"));
            var wrapper = json(ROOT.resolve("items/weapon_scope_w45/" + id + ".json"));
            var select = wrapper.getAsJsonObject("model");
            assertEquals("minecraft:select", select.get("type").getAsString());
            assertEquals("minecraft:display_context", select.get("property").getAsString());
            assertEquals(1, select.getAsJsonArray("cases").size());
            var branch = select.getAsJsonArray("cases").get(0).getAsJsonObject();
            assertEquals(JsonParser.parseString("[\"firstperson_righthand\",\"firstperson_lefthand\"]"), branch.get("when"));
            if (LFRS.contains(id)) {
                var firstPerson = branch.getAsJsonObject("model");
                assertEquals("minecraft:condition", firstPerson.get("type").getAsString());
                assertEquals("minecraft:custom_model_data", firstPerson.get("property").getAsString());
                assertEquals(0, firstPerson.get("index").getAsInt());
                assertEquals("destiny:weapon_scope_w45/" + id + "_native",
                        firstPerson.getAsJsonObject("on_false").get("model").getAsString());
                assertEquals("destiny:weapon_scope_w45/" + id + "_twohand",
                        firstPerson.getAsJsonObject("on_true").get("model").getAsString());
                for (String key : List.of("on_true", "on_false")) {
                    var tint = firstPerson.getAsJsonObject(key).getAsJsonArray("tints").get(0).getAsJsonObject();
                    assertEquals("minecraft:constant", tint.get("type").getAsString());
                    assertEquals(id.equals("line_in_the_sand") ? 0xB777FF : 0xE8C08A,
                            tint.get("value").getAsInt(), "Line uses violet inlay; Storm uses warm bronze, never violet");
                }
            } else {
                assertEquals(JsonParser.parseString("{\"type\":\"minecraft:empty\"}"), branch.get("model"));
            }
            assertEquals(ads(original), select.get("fallback"), id);
            var grip = select.getAsJsonObject("fallback");
            assertEquals("minecraft:condition", grip.get("type").getAsString());
            assertEquals("minecraft:custom_model_data", grip.get("property").getAsString());
            assertEquals(0, grip.get("index").getAsInt());
            for (var context : ItemDisplayContext.values()) {
                boolean overridden = branch.getAsJsonArray("when").contains(new JsonPrimitive(context.getSerializedName()));
                assertEquals(context.firstPerson(), overridden, id + ": " + context);
                if (!overridden) for (boolean twoHanded : List.of(false, true)) {
                    String key = twoHanded ? "on_true" : "on_false";
                    assertEquals(ads(original).get(key), grip.get(key), context + ": " + key);
                    String model = grip.getAsJsonObject(key).get("model").getAsString();
                    assertTrue(Files.isRegularFile(ROOT.resolve("models/" + model.substring("destiny:".length()) + ".json")));
                }
            }
            original.remove("model");
            wrapper.remove("model");
            assertEquals(original, wrapper, "All non-model item options remain identical");
        }
    }

    @Test void lfrGeometryClonesOriginalBodyAndTextureWithOnlyUpperOpticsRemovedAndOpenNewSight() throws Exception {
        var manifest = json(Path.of("art/weapons/w45-models/manifest.json"));
        for (String id : LFRS) {
            var original = json(ROOT.resolve("models/weapon/linear_fusion_rifle/" + id + ".json"));
            var geometryPath = ROOT.resolve("models/weapon_scope_w45/" + id + "_geometry.json");
            var geometry = json(geometryPath);
            assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(geometryPath))), id);
            assertEquals(original.get("textures"), geometry.get("textures"), "Reuse exact original textures");
            var expectedBody = new com.google.gson.JsonArray();
            int removed = 0, clipped = 0;
            for (var value : original.getAsJsonArray("elements")) {
                var element = value.deepCopy().getAsJsonObject();
                var low = element.getAsJsonArray("from");
                var high = element.getAsJsonArray("to");
                if (low.get(1).getAsDouble() >= 11.2) {
                    removed++;
                    continue;
                }
                if (high.get(1).getAsDouble() > 11.2) {
                    high.set(1, new JsonPrimitive(11.2));
                    clipped++;
                }
                expectedBody.add(element);
            }
            var elements = geometry.getAsJsonArray("elements");
            assertTrue(elements.size() > expectedBody.size() && elements.size() <= 256, id);
            for (int i = 0; i < expectedBody.size(); i++) {
                assertEquals(expectedBody.get(i), elements.get(i), "Unchanged body faces/UVs except y clipping: " + id + ":" + i);
            }
            var metadata = manifest.getAsJsonObject("lfr").getAsJsonObject(id);
            assertEquals(original.getAsJsonArray("elements").size(), metadata.get("sourceCubes").getAsInt());
            assertEquals(expectedBody.size(), metadata.get("bodyCubes").getAsInt());
            assertEquals(removed, metadata.get("removedCubes").getAsInt());
            assertEquals(clipped, metadata.get("clippedCubes").getAsInt());
            assertEquals(elements.size(), metadata.get("totalCubes").getAsInt());
            assertEquals(elements.size() - expectedBody.size(), metadata.get("opticCubes").getAsInt());
            assertEquals(JsonParser.parseString("[8,12.7]"), metadata.get("opticCenter"));
            var texture = ImageIO.read(ROOT.resolve("textures/item/weapon/w30/" + id + ".png").toFile());
            var palette = metadata.getAsJsonObject("paletteSamples");
            if (id.equals("stormchaser")) {
                assertFalse(palette.has("violet"), "Stormchaser cannot inherit Line's violet material");
                int tint = metadata.get("opticTintRgb").getAsInt();
                assertTrue(((tint >>> 16) & 255) > ((tint >>> 8) & 255)
                        && ((tint >>> 8) & 255) > (tint & 255), "Bronze tint has warm descending RGB channels");
            }
            for (var sample : palette.entrySet()) {
                var record = sample.getValue().getAsJsonObject();
                var pixel = record.getAsJsonArray("pixel");
                int argb = texture.getRGB(pixel.get(0).getAsInt(), pixel.get(1).getAsInt());
                var rgba = record.getAsJsonArray("rgba");
                assertEquals(255, argb >>> 24, "Sample is fully opaque original artwork");
                assertEquals((argb >>> 16) & 255, rgba.get(0).getAsInt());
                assertEquals((argb >>> 8) & 255, rgba.get(1).getAsInt());
                assertEquals(argb & 255, rgba.get(2).getAsInt());
                assertEquals(255, rgba.get(3).getAsInt());
            }
            boolean topBridge = false;
            JsonObject outerTop = null, outerBottom = null, innerTop = null, innerBottom = null;
            for (int i = expectedBody.size(); i < elements.size(); i++) {
                var optic = elements.get(i).getAsJsonObject();
                var low = optic.getAsJsonArray("from");
                var high = optic.getAsJsonArray("to");
                assertTrue(optic.get("name").getAsString().startsWith("w45_"));
                switch (optic.get("name").getAsString()) {
                    case "w45_outer_top" -> outerTop = optic;
                    case "w45_outer_bottom" -> outerBottom = optic;
                    case "w45_inner_top" -> innerTop = optic;
                    case "w45_inner_bottom" -> innerBottom = optic;
                }
                for (int axis = 0; axis < 3; axis++) {
                    assertTrue(low.get(axis).getAsDouble() < high.get(axis).getAsDouble(), "No degenerate cube");
                }
                assertFalse(coversXY(optic, 8, 12.7), "Rotated geometry cannot block the actual sight line");
                for (double x : new double[]{7.7, 8, 8.3}) for (double y : new double[]{12.4, 12.7, 13.0}) {
                    assertFalse(coversXY(optic, x, y), "Clear aperture around center, using inverse element rotation");
                }
                if (coversXY(optic, 8, 14)) topBridge = true;
                for (var face : optic.getAsJsonObject("faces").entrySet()) {
                    var definition = face.getValue().getAsJsonObject();
                    assertEquals("#0", definition.get("texture").getAsString());
                    boolean tinted = id.equals("line_in_the_sand")
                            ? optic.get("name").getAsString().contains("inner")
                            : !optic.get("name").getAsString().equals("w45_mount");
                    if (tinted) {
                        assertEquals(0, definition.get("tintindex").getAsInt());
                        if (id.equals("line_in_the_sand"))
                            assertEquals(palette.getAsJsonObject("violet").get("uv"), definition.get("uv"));
                    } else assertFalse(definition.has("tintindex"), "Body and outer housing retain original texture colors");
                    assertTrue(palette.entrySet().stream().anyMatch(sample -> sample.getValue().getAsJsonObject()
                            .get("uv").equals(definition.get("uv"))), "Every optic face samples pinned original texels");
                }
            }
            assertEquals(id.equals("line_in_the_sand"), topBridge, "Stormchaser horns must stay open at top");
            if (id.equals("line_in_the_sand")) {
                assertNotNull(outerTop);
                assertNotNull(outerBottom);
                assertNotNull(innerTop);
                assertNotNull(innerBottom);
                assertTrue(width(outerTop) < width(outerBottom), "Reference Line trapezoid narrows toward the top");
                assertTrue(width(innerTop) < width(innerBottom), "Violet inner edges follow the same trapezoid");
            }
        }
    }

    private static double width(JsonObject cube) {
        return cube.getAsJsonArray("to").get(0).getAsDouble() - cube.getAsJsonArray("from").get(0).getAsDouble();
    }

    /** Sight ray runs along z. Undo the actual z rotation before testing the local box.
     * Testing the unrotated or enclosing axis-aligned bounds would miss angled blockers.
     */
    private static boolean coversXY(JsonObject cube, double x, double y) {
        if (cube.has("rotation")) {
            var rotation = cube.getAsJsonObject("rotation");
            assertEquals("z", rotation.get("axis").getAsString());
            assertFalse(rotation.get("rescale").getAsBoolean());
            var origin = rotation.getAsJsonArray("origin");
            double ox = origin.get(0).getAsDouble(), oy = origin.get(1).getAsDouble();
            double angle = -Math.toRadians(rotation.get("angle").getAsDouble());
            double dx = x - ox, dy = y - oy;
            x = ox + Math.cos(angle) * dx - Math.sin(angle) * dy;
            y = oy + Math.sin(angle) * dx + Math.cos(angle) * dy;
        }
        var low = cube.getAsJsonArray("from");
        var high = cube.getAsJsonArray("to");
        return x >= low.get(0).getAsDouble() && x <= high.get(0).getAsDouble()
                && y >= low.get(1).getAsDouble() && y <= high.get(1).getAsDouble();
    }

    private static double[] beamEndpoint(JsonObject cube, boolean upper) {
        var low = cube.getAsJsonArray("from");
        var high = cube.getAsJsonArray("to");
        double x = (low.get(0).getAsDouble() + high.get(0).getAsDouble()) / 2;
        double y = (upper ? high : low).get(1).getAsDouble();
        var rotation = cube.getAsJsonObject("rotation");
        var origin = rotation.getAsJsonArray("origin");
        double ox = origin.get(0).getAsDouble(), oy = origin.get(1).getAsDouble();
        double angle = Math.toRadians(rotation.get("angle").getAsDouble());
        double dx = x - ox, dy = y - oy;
        return new double[]{ox + Math.cos(angle) * dx - Math.sin(angle) * dy,
                oy + Math.sin(angle) * dx + Math.cos(angle) * dy};
    }

    @Test void inverseRotationApertureTestDetectsAngledBlockersAndDoesNotTreatBoundingBoxesAsSolids() {
        var angled = JsonParser.parseString("""
                {"from":[7.45,11.4,12.65],"to":[7.55,13.0,13.15],
                 "rotation":{"origin":[7.5,12.2,12.9],"axis":"z","angle":-45,"rescale":false}}
                """).getAsJsonObject();
        assertTrue(coversXY(angled, 8, 12.7), "Rotated beam blocks center although raw box misses it");
        assertFalse(coversXY(angled, 7.5, 12.8), "Raw box overlaps this ray but actual angled beam is clear");
    }

    @Test void lineHasThinContinuousAngledSidesAndStormHasConnectedCurvedBronzeHorns() throws Exception {
        var line = json(ROOT.resolve("models/weapon_scope_w45/line_in_the_sand_geometry.json"));
        for (int side = 0; side < 2; side++) for (String part : List.of("outer", "inner")) {
            String name = "w45_" + part + "_" + side;
            var beam = line.getAsJsonArray("elements").asList().stream().map(JsonElement::getAsJsonObject)
                    .filter(c -> c.has("name") && name.equals(c.get("name").getAsString())).findFirst().orElseThrow();
            assertEquals(part.equals("outer") ? .12 : .05, width(beam), .000001, "Thin rim and finer inlay");
            var rotation = beam.getAsJsonObject("rotation");
            assertEquals("z", rotation.get("axis").getAsString());
            assertEquals(13.495733, Math.abs(rotation.get("angle").getAsDouble()), .000001,
                    "Single continuous side uses actual trapezoid slope, not quantized stair steps");
            var bottom = beamEndpoint(beam, false);
            var top = beamEndpoint(beam, true);
            assertTrue(top[1] - bottom[1] > 2.2, "One beam spans the side");
        }
        var storm = json(ROOT.resolve("models/weapon_scope_w45/stormchaser_geometry.json"));
        for (int side = 0; side < 2; side++) {
            String prefix = "w45_horn_" + side + "_";
            var horns = storm.getAsJsonArray("elements").asList().stream().map(JsonElement::getAsJsonObject)
                    .filter(c -> c.has("name") && c.get("name").getAsString().startsWith(prefix)).toList();
            assertEquals(8, horns.size(), "At least four short rotated segments per side; eight follow the reference curve");
            double middle = Double.POSITIVE_INFINITY;
            for (int i = 0; i < horns.size(); i++) {
                var cube = horns.get(i);
                var rotation = cube.getAsJsonObject("rotation");
                assertEquals("z", rotation.get("axis").getAsString());
                assertFalse(rotation.get("rescale").getAsBoolean());
                assertTrue(Double.isFinite(rotation.get("angle").getAsDouble())
                        && Math.abs(rotation.get("angle").getAsDouble()) > 1, "Every horn section is smoothly angled");
                var low = beamEndpoint(cube, false);
                var high = beamEndpoint(cube, true);
                assertTrue(Math.hypot(high[0] - low[0], high[1] - low[1]) < .6, "Short sections approximate a curve");
                middle = Math.min(middle, side == 0 ? low[0] : 16 - low[0]);
                if (i > 0) {
                    var previous = beamEndpoint(horns.get(i - 1), true);
                    assertTrue(Math.hypot(previous[0] - low[0], previous[1] - low[1]) <= .025,
                            "Adjacent rotated sections meet without axis-aligned stair gaps");
                }
            }
            var base = beamEndpoint(horns.getFirst(), false);
            var tip = beamEndpoint(horns.getLast(), true);
            assertTrue((side == 0 ? base[0] : 16 - base[0]) > middle + .5, "Base curls inward from the widest middle");
            assertTrue((side == 0 ? tip[0] : 16 - tip[0]) > middle + .5, "Top tips curl inward again");
        }
    }

    private static Matrix4f transform(JsonObject display, boolean left) {
        var rotation = display.getAsJsonArray("rotation");
        var translation = display.getAsJsonArray("translation");
        var scale = display.getAsJsonArray("scale");
        float sign = left ? -1 : 1;
        return new Matrix4f().translate(translation.get(0).getAsFloat() * sign / 16,
                        translation.get(1).getAsFloat() / 16, translation.get(2).getAsFloat() / 16)
                .rotateXYZ((float) Math.toRadians(rotation.get(0).getAsDouble()),
                        (float) Math.toRadians(rotation.get(1).getAsDouble()) * sign,
                        (float) Math.toRadians(rotation.get(2).getAsDouble()) * sign)
                .scale(scale.get(0).getAsFloat(), scale.get(1).getAsFloat(), scale.get(2).getAsFloat());
    }

    @Test void lfrPoseChildrenAlignActualOpenSightAndCompensateBothExistingGrips() throws Exception {
        for (String id : LFRS) {
            var source = json(ROOT.resolve("models/weapon/linear_fusion_rifle/" + id + "_ads.json"));
            var nativeModel = json(ROOT.resolve("models/weapon_scope_w45/" + id + "_native.json"));
            var twohand = json(ROOT.resolve("models/weapon_scope_w45/" + id + "_twohand.json"));
            assertEquals("destiny:weapon_scope_w45/" + id + "_geometry", nativeModel.get("parent").getAsString());
            assertEquals(nativeModel.get("parent"), twohand.get("parent"));
            assertFalse(nativeModel.has("elements"));
            assertFalse(twohand.has("elements"));
            var expected = source.getAsJsonObject("display").deepCopy();
            for (boolean left : List.of(false, true)) {
                String context = "firstperson_" + (left ? "lefthand" : "righthand");
                expected.getAsJsonObject(context).getAsJsonArray("translation").set(1, new JsonPrimitive(3.855));
                var nativeDisplay = nativeModel.getAsJsonObject("display").getAsJsonObject(context);
                assertEquals(3.855, nativeDisplay.getAsJsonArray("translation").get(1).getAsDouble(), .000001);
                float sign = left ? -1 : 1;
                var compensated = new Matrix4f().translate(-.641864f * sign, 0, 0)
                        .rotateY((float) Math.toRadians(10) * sign)
                        .mul(transform(twohand.getAsJsonObject("display").getAsJsonObject(context), left));
                assertTrue(transform(nativeDisplay, left).equals(compensated, .000002f), id + ":" + context);
            }
            assertEquals(expected, nativeModel.get("display"), "Only native first-person y changes from original ADS");
            for (var model : List.of(nativeModel, twohand)) {
                assertNotNull(CuboidModel.fromStream(new StringReader(model.toString())), "Actual client cuboid codec accepts child");
            }
        }
    }

    @Test void actual26_3JarCodecsAcceptWrappersAndExactDisplayContextEnumStrings() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();
        ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        assertEquals("firstperson_righthand", ItemDisplayContext.FIRST_PERSON_RIGHT_HAND.getSerializedName());
        assertEquals("firstperson_lefthand", ItemDisplayContext.FIRST_PERSON_LEFT_HAND.getSerializedName());
        for (String id : IDS) {
            var model = json(ROOT.resolve("items/weapon_scope_w45/" + id + ".json")).getAsJsonObject("model");
            var result = ItemModels.CODEC.parse(JsonOps.INSTANCE, model);
            assertTrue(result.isSuccess(), id + ": " + result.error());
            var invalid = model.deepCopy();
            invalid.getAsJsonArray("cases").get(0).getAsJsonObject().addProperty("when", "first_person_right_hand");
            assertFalse(ItemModels.CODEC.parse(JsonOps.INSTANCE, invalid).isSuccess(), "Enum spelling must be exact");
        }
    }

    @Test void manifestPinsGeneratedWrappersAndUntouchedOriginalItems() throws Exception {
        var manifest = json(Path.of("art/weapons/w45-models/manifest.json"));
        assertEquals(IDS, manifest.getAsJsonArray("ids").asList().stream().map(JsonElement::getAsString).toList());
        assertEquals(11, manifest.getAsJsonObject("sha256").size());
        assertEquals(5, manifest.getAsJsonObject("originalItemSha256").size());
        assertEquals(12, manifest.getAsJsonObject("sourceSha256").size());
        for (String id : LFRS) {
            assertTrue(manifest.getAsJsonObject("sourceSha256").has("src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/" + id + ".json"));
            assertTrue(manifest.getAsJsonObject("sourceSha256").has("src/main/resources/assets/destiny/textures/item/weapon/w30/" + id + ".png"));
        }
        for (String section : List.of("sha256", "originalItemSha256", "sourceSha256")) {
            for (var entry : manifest.getAsJsonObject(section).entrySet()) {
                var digest = MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(Path.of(entry.getKey())));
                assertEquals(entry.getValue().getAsString(), HexFormat.of().formatHex(digest), entry.getKey());
            }
        }
    }
}
