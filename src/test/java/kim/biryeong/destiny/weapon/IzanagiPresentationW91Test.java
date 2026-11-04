package kim.biryeong.destiny.weapon;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.color.item.ItemTintSources;
import org.junit.jupiter.api.Test;

import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Actual item codec, model inheritance/geometry and original-source regression checks.
 * Live owner/transaction assertions belong to the W90-isolated production-path GameTests.
 */
class IzanagiPresentationW91Test {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");
    private static final Path ITEM = ROOT.resolve("items/weapon_izanagi_w91/izanagis_burden.json");
    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }
    private static String sha(Path path) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
    }

    @Test void exactExoticIdentityAloneSupportsPresentation() {
        assertEquals(6, WeaponIzanagiPresentation.SELECTOR_INDEX);
        assertFalse(WeaponIzanagiPresentation.supports(null));
        var real = WeaponCatalog.find("izanagis_burden").orElseThrow();
        for (var e : WeaponCatalog.all()) assertEquals(e.equals(real), WeaponIzanagiPresentation.supports(e));
        assertFalse(WeaponIzanagiPresentation.supports(new WeaponCatalog.Entry(real.id(), "hand_cannon", real.frame(),
                real.name(), real.source_frame_label(), real.item_model())));
    }

    @Test void originalSourceAndThreeAtlasesRemainByteIdentical() throws Exception {
        assertEquals("9ae28369f80ff0f81bb7e1344ee50b618b9a2de62dcafc631287084dbe3c8f31",
                sha(Path.of("art/weapons/w84/model/source/izanagi.bbmodel")));
        for (var pin : Map.of("izanagis_burden_lens", "905b370044dbbb942b2db8515e29f2a053725a8d67268ad7c9d376124b7b7423",
                "izanagis_burden", "d4a156893b64a1cec3243f3ad7f734c9e633b4041958f869c98414e7f96c9429",
                "izanagis_burden_accent", "d8703b3370a5337e11c99e6a3f2c06a33d97417d3dbc5fdff96727169ec3cf6a").entrySet())
            assertEquals(pin.getValue(), sha(ROOT.resolve("textures/item/weapon/" + pin.getKey() + ".png")));
    }

    @Test void actualMinecraftCodecAndCuboidParserAcceptNewItemAndModelBank() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion(); net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap(); ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        var decoded = ItemModels.CODEC.parse(JsonOps.INSTANCE, json(ITEM).get("model"));
        assertTrue(decoded.isSuccess(), "Actual26.3 item codec: " + decoded.error());
        try (var files = Files.walk(ROOT.resolve("models/item/weapon_izanagi_w91"))) {
            var paths = files.filter(p -> p.toString().endsWith(".json")).toList();
            assertFalse(paths.isEmpty());
            for (var path : paths) assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(path))), path.toString());
        }
    }

    @Test void everyReloadAndHonedSamplePreservesAllSeventyNineOriginalCubesAndUvs() throws Exception {
        var original = json(ROOT.resolve("models/item/weapon/izanagis_burden.json"));
        var cubes = original.getAsJsonArray("elements"); assertEquals(79, cubes.size());
        var item = json(ITEM).getAsJsonObject("model");
        for (String context : List.of("firstperson_righthand", "firstperson_lefthand")) for (boolean grip : List.of(false, true)) {
            var normalMotion = new HashSet<String>(); var honedMotion = new HashSet<String>();
            for (int base : new int[]{0, 2}) for (int frame = 0; frame <= 60; frame++) {
                var state = new State(context, "hip", grip, 0, (float) base + (float) frame / 60);
                var parts = selected(item, state).stream().map(IzanagiPresentationW91Test::effectiveUnchecked).toList();
                assertOriginal(cubes, original.getAsJsonObject("textures"), parts);
                assertEquals(3, parts.size(), "Body, source magazine, and stationary source bolt remain separate");
                assertEquals(List.of(76, 1, 2), parts.stream().map(p -> p.getAsJsonArray("elements").size()).toList());
                if (frame == 0 || frame == 60) {
                    var accepted = grip ? effectiveUnchecked("destiny:item/weapon/izanagis_burden_twohand") : original;
                    for (var part : parts) assertEquals(accepted.getAsJsonObject("display").get(context),
                            part.getAsJsonObject("display").get(context), "Exact accepted neutral endpoint");
                }
                var signature = parts.stream().map(p -> p.getAsJsonObject("display").get(context).toString()).toList().toString();
                (base == 0 ? normalMotion : honedMotion).add(signature);
            }
            assertEquals(60, normalMotion.size(), "All 61 source poses must be distinct except exact neutral endpoints");
            assertEquals(60, honedMotion.size(), "Honed retains all new intermediate poses and exact neutral endpoints");
            assertNotEquals(normalMotion, honedMotion, "Normal and Honed motion retain their source transform differences");
        }
    }

    @Test void denseFloat32BucketsAndAllGenerationOffsetsSelectExactSourceSample() throws Exception {
        var item = json(ITEM).getAsJsonObject("model");
        assertEquals("16d333d78c42336e58116519b4fa951c5242326541ae7f5d8c33530fd3796e38",
                sha(Path.of("art/weapons/w197/izanagi-source-motion.json")));
        for (String context : List.of("firstperson_righthand", "firstperson_lefthand"))
            for (boolean grip : List.of(false, true)) for (int base : new int[]{0, 2})
                for (int frame = 0; frame <= 60; frame++) {
                    String kind = base == 0 ? "ordinary" : "honed";
                    String branch = grip ? "twohand" : "native";
                    float threshold = base + (float) frame / 60;
                    var expected = new ArrayList<String>();
                    for (String part : List.of("body", "magazine", "bolt"))
                        expected.add("destiny:item/weapon_izanagi_w91/izanagis_burden_" + kind
                                + "_%02d_".formatted(frame) + part + "_" + branch);
                    for (float offset : new float[]{0, .00025f, .0005f})
                        assertEquals(expected, selected(item, new State(context, "hip", grip, 0, threshold + offset)),
                                "Float32 threshold and generation offset must select the exact dense sample");
                    if (frame > 0) {
                        var previous = new ArrayList<String>();
                        for (String part : List.of("body", "magazine", "bolt"))
                            previous.add("destiny:item/weapon_izanagi_w91/izanagis_burden_" + kind
                                    + "_%02d_".formatted(frame - 1) + part + "_" + branch);
                        assertEquals(previous, selected(item, new State(context, "hip", grip, 0, Math.nextDown(threshold))));
                    }
                    if (frame % 3 != 0) {
                        var actual = effectiveUnchecked(expected.getFirst()).getAsJsonObject("display").get(context);
                        for (int oldFrame : new int[]{frame / 3 * 3, (frame / 3 + 1) * 3}) {
                            String oldId = "destiny:item/weapon_izanagi_w91/izanagis_burden_" + kind
                                    + "_%02d_body_".formatted(oldFrame) + branch;
                            assertNotEquals(effectiveUnchecked(oldId).getAsJsonObject("display").get(context), actual,
                                    "Every new intermediate pose differs from both neighboring old-bank poses");
                        }
                    }
                }
    }

    @Test void chargedCueKeepsAdsPoseScopeAndGripRoutesAndNonFirstPersonReloadKeepsOriginal() throws Exception {
        var item = json(ITEM).getAsJsonObject("model");
        var originalItem = json(ROOT.resolve("items/weapon/izanagis_burden.json")).getAsJsonObject("model");
        var aimItem = json(ROOT.resolve("items/weapon_aim_w70/izanagis_burden.json")).getAsJsonObject("model");
        var original = json(ROOT.resolve("models/item/weapon/izanagis_burden.json"));
        var cubes = original.getAsJsonArray("elements");
        for (String context : List.of("gui", "ground", "fixed", "head", "thirdperson_righthand", "thirdperson_lefthand"))
            for (String pose : List.of("hip", "ads", "inspect", "scope")) for (boolean grip : List.of(false, true)) {
                for (double selector : new double[]{.5005, 2.5005, -1}) {
                    var state = new State(context, pose, grip, .65, selector);
                    assertEquals(selected(originalItem, state), selected(item, state), "Exact original reload/fallback route in " + state);
                }
            }
        for (String context : List.of("firstperson_righthand", "firstperson_lefthand", "gui", "ground", "fixed", "head",
                "thirdperson_righthand", "thirdperson_lefthand")) for (boolean grip : List.of(false, true))
            for (String pose : List.of("hip", "ads", "inspect", "scope")) for (double aim : new double[]{-1, 0, .35, .65, 1}) {
                var state = new State(context, pose, grip, aim, 4.0005);
                var actual = selected(item, state).stream().map(IzanagiPresentationW91Test::effectiveUnchecked).toList();
                assertOriginal(cubes, original.getAsJsonObject("textures"), actual);
                // The existing W70 graph owns explicit inspect/scope fallbacks as well as float3.
                var expected = selected(aimItem, state).stream().map(IzanagiPresentationW91Test::effectiveUnchecked).toList();
                for (var cube : cubes) {
                    var originalLayer = expected.stream().filter(p -> p.getAsJsonArray("elements").contains(cube)).findFirst().orElseThrow();
                    var actualLayer = actual.stream().filter(p -> p.getAsJsonArray("elements").contains(cube)).findFirst().orElseThrow();
                    assertEquals(originalLayer.getAsJsonObject("display").get(context), actualLayer.getAsJsonObject("display").get(context),
                            "Charged cue cannot shift the original sight line, scope or inspect pose: " + state);
                }
                assertTrue(actual.stream().mapToInt(p -> p.getAsJsonArray("elements").size()).sum() > 79,
                        "Funded charge adds a distinct authored barrel cue while preserving base geometry");
            }
    }

    private static void assertOriginal(JsonArray cubes, JsonObject textures, List<JsonObject> parts) {
        int count = parts.stream().mapToInt(p -> p.getAsJsonArray("elements").size()).sum();
        assertTrue(count >= 79 && count <= 256, "Detailed original stays within cube budget");
        for (var cube : cubes) {
            long occurrences = parts.stream().flatMap(p -> p.getAsJsonArray("elements").asList().stream()).filter(cube::equals).count();
            assertEquals(1, occurrences, "Every original cube/face/UV/rotation appears exactly once");
            for (var part : parts) if (part.getAsJsonArray("elements").contains(cube))
                for (var texture : textures.entrySet()) assertEquals(texture.getValue(), part.getAsJsonObject("textures").get(texture.getKey()));
        }
    }

    private record State(String context, String pose, boolean grip, double aim, double selector) {}

    /** Evaluate real item-definition branches rather than filename conventions or generator counters. */
    private static List<String> selected(JsonObject tree, State state) {
        return switch (tree.get("type").getAsString()) {
            case "minecraft:model" -> List.of(tree.get("model").getAsString());
            case "minecraft:composite" -> {
                var out = new ArrayList<String>();
                for (var child : tree.getAsJsonArray("models")) out.addAll(selected(child.getAsJsonObject(), state));
                yield out;
            }
            case "minecraft:condition" -> {
                assertEquals("minecraft:custom_model_data", tree.get("property").getAsString());
                assertEquals(0, tree.get("index").getAsInt());
                yield selected(tree.getAsJsonObject(state.grip ? "on_true" : "on_false"), state);
            }
            case "minecraft:select" -> {
                String value = switch (tree.get("property").getAsString()) {
                    case "minecraft:display_context" -> state.context;
                    case "minecraft:custom_model_data" -> { assertEquals(0, tree.get("index").getAsInt()); yield state.pose; }
                    default -> throw new AssertionError("Unknown select property " + tree);
                };
                JsonObject match = tree.getAsJsonObject("fallback");
                for (var entry : tree.getAsJsonArray("cases")) {
                    var c = entry.getAsJsonObject(); var when = c.get("when");
                    if (when.isJsonArray() ? when.getAsJsonArray().asList().stream().anyMatch(v -> v.getAsString().equals(value))
                            : when.getAsString().equals(value)) { match = c.getAsJsonObject("model"); break; }
                }
                yield selected(match, state);
            }
            case "minecraft:range_dispatch" -> {
                assertEquals("minecraft:custom_model_data", tree.get("property").getAsString());
                int index = tree.get("index").getAsInt(); assertTrue(index == 3 || index == 6);
                float value = (float) (index == 3 ? state.aim : state.selector);
                if (tree.has("scale")) value *= tree.get("scale").getAsFloat();
                JsonObject match = tree.getAsJsonObject("fallback");
                for (var entry : tree.getAsJsonArray("entries")) {
                    var e = entry.getAsJsonObject();
                    if (value >= e.get("threshold").getAsFloat()) match = e.getAsJsonObject("model");
                }
                yield selected(match, state);
            }
            default -> throw new AssertionError("Unsupported item branch " + tree);
        };
    }

    private static JsonObject effectiveUnchecked(String id) {
        try { return effective(id, new HashSet<>()); } catch (Exception e) { throw new AssertionError(id, e); }
    }
    private static JsonObject effective(String id, Set<String> seen) throws Exception {
        assertTrue(id.startsWith("destiny:")); assertTrue(seen.add(id), "Model inheritance cycle " + id);
        var model = json(ROOT.resolve("models/" + id.substring("destiny:".length()) + ".json"));
        if (!model.has("parent")) return model;
        var parent = effective(model.get("parent").getAsString(), seen);
        for (var entry : model.entrySet()) {
            if (Set.of("display", "textures").contains(entry.getKey()) && parent.has(entry.getKey())) {
                var merged = parent.getAsJsonObject(entry.getKey()).deepCopy();
                entry.getValue().getAsJsonObject().entrySet().forEach(e -> merged.add(e.getKey(), e.getValue()));
                parent.add(entry.getKey(), merged);
            } else parent.add(entry.getKey(), entry.getValue());
        }
        return parent;
    }
}
