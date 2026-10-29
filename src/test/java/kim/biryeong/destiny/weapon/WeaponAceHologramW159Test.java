package kim.biryeong.destiny.weapon;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import net.minecraft.client.resources.model.cuboid.UnbakedCuboidGeometry;
import net.minecraft.core.Direction;
import org.junit.jupiter.api.Test;

import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** W159 data contracts exercised against the actual Minecraft 26.3 parsers. */
class WeaponAceHologramW159Test {
    private static final Path A = Path.of("src/main/resources/assets/destiny");
    private static final String KEY = "weapon_sight_w159/";
    private static final String CANONICAL = "destiny:item/weapon/ace_of_spades";
    private static final Set<String> FP = Set.of("firstperson_righthand", "firstperson_lefthand");

    private static JsonObject read(String path) throws Exception {
        return JsonParser.parseString(Files.readString(A.resolve(path))).getAsJsonObject();
    }

    @Test void aceRoutesToHologramWithoutChangingPhysicalSightThreshold() {
        var ace = WeaponCatalog.find("ace_of_spades").orElseThrow();
        assertEquals(KEY, WeaponAimPresentation.modelPrefix(ace));
        assertTrue(WeaponAimPresentation.supports(ace));
        for (float progress : new float[]{-1, 0, .9f, .94f, Math.nextDown(.95f),
                Float.NaN, Float.NEGATIVE_INFINITY, Float.POSITIVE_INFINITY}) {
            assertFalse(WeaponAimPresentation.physicalSight(ace, progress), "progress=" + progress);
        }
        for (float progress : new float[]{.95f, Math.nextUp(.95f), 1f}) {
            assertTrue(WeaponAimPresentation.physicalSight(ace, progress), "progress=" + progress);
        }
    }

    @Test void actual263CuboidParserAcceptsExactlyBodyAnd42Frames() throws Exception {
        var expected = new HashSet<String>();
        expected.add("ace_of_spades_body.json");
        for (int frame = 0; frame <= 20; frame++) {
            for (String style : Set.of("native", "twohand")) {
                expected.add("ace_of_spades_%02d_%s.json".formatted(frame, style));
            }
        }
        try (var paths = Files.list(A.resolve("models/" + KEY))) {
            var all = paths.toList();
            assertEquals(43, all.size());
            assertEquals(expected, all.stream().map(p -> p.getFileName().toString())
                    .collect(java.util.stream.Collectors.toSet()));
            for (var path : all) {
                assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(path))), path.toString());
            }
        }
    }

    @Test void bodyPreservesEveryOriginalElementAndUsesTwoSidedReticlePlanes() throws Exception {
        var original = read("models/item/weapon/ace_of_spades.json");
        var body = read("models/" + KEY + "ace_of_spades_body.json");
        var oldElements = original.getAsJsonArray("elements");
        var elements = body.getAsJsonArray("elements");
        var parsed = CuboidModel.fromStream(new StringReader(body.toString()));
        var geometry = assertInstanceOf(UnbakedCuboidGeometry.class, parsed.geometry());
        assertEquals(90, geometry.elements().size());
        assertEquals(87, oldElements.size());
        assertEquals(90, elements.size());
        for (int i = 0; i < 87; i++) assertEquals(oldElements.get(i), elements.get(i), "original element " + i);
        var textures = body.getAsJsonObject("textures");
        for (var slot : original.getAsJsonObject("textures").entrySet()) {
            assertEquals(slot.getValue(), textures.get(slot.getKey()), slot.getKey());
        }
        var extraSlots = new HashSet<>(textures.keySet());
        extraSlots.removeAll(original.getAsJsonObject("textures").keySet());
        assertEquals(Set.of("hologram"), extraSlots);
        assertEquals("destiny:item/" + KEY + "ace_reticle", textures.get("hologram").getAsString());
        var names = new HashSet<String>();
        for (int i = 87; i < 90; i++) {
            var plane = elements.get(i).getAsJsonObject();
            assertTrue(names.add(plane.get("name").getAsString()));
            var from = plane.getAsJsonArray("from");
            var to = plane.getAsJsonArray("to");
            assertTrue(from.get(0).getAsDouble() < to.get(0).getAsDouble());
            assertTrue(from.get(1).getAsDouble() < to.get(1).getAsDouble());
            assertEquals(from.get(2).getAsDouble(), to.get(2).getAsDouble());
            assertEquals(15, plane.get("light_emission").getAsInt());
            assertEquals("up", plane.get("shade_direction_override").getAsString());
            assertEquals(Set.of("south", "north"), plane.getAsJsonObject("faces").keySet());
            assertEquals("#hologram", plane.getAsJsonObject("faces").getAsJsonObject("south")
                    .get("texture").getAsString());
            assertEquals(Set.of(Direction.SOUTH, Direction.NORTH), geometry.elements().get(i).faces().keySet());
        }
        assertEquals(Set.of("w159_hologram_left", "w159_hologram_right", "w159_hologram_dot"), names);
    }

    @Test void profileViewRecognizesEmissionAdjustedReticleLight() throws Exception {
        int carrier = net.minecraft.util.LightCoordsUtil.pack(0, 12);
        int emissive = net.minecraft.util.LightCoordsUtil.lightCoordsWithEmission(carrier, 15);
        assertEquals(240, emissive & 65535);
        assertEquals(240, (emissive >>> 16) & 65535);
        String shader = Files.readString(Path.of("src/main/resources/destiny/profile_view/main.item.vsh"));
        assertTrue(shader.contains("UV2.y == 192 || (UV2.x == 240 && UV2.y == 240)"),
                "Emissive reticle must use the same view projection as its carrier");
        assertTrue(shader.contains("Position.y < -9000000.0 && Position.y > -11000000.0"),
                "Full-bright world items must remain outside the view marker range");
    }

    @Test void hologramParentsStartAtFrame19AndAllNonFirstPersonTransformsArePreserved() throws Exception {
        for (String style : Set.of("native", "twohand")) {
            String suffix = style.equals("twohand") ? "_twohand" : "";
            var original = read("models/item/weapon/ace_of_spades" + suffix + ".json").getAsJsonObject("display");
            for (int frame = 0; frame <= 20; frame++) {
                String name = "ace_of_spades_%02d_%s.json".formatted(frame, style);
                var model = read("models/" + KEY + name);
                assertEquals(frame < 19 ? CANONICAL : "destiny:" + KEY + "ace_of_spades_body",
                        model.get("parent").getAsString(), name);
                assertFalse(model.has("elements"), name);
                assertFalse(model.has("textures"), name);
                var display = model.getAsJsonObject("display");
                assertEquals(original.keySet(), display.keySet(), name);
                for (var context : original.entrySet()) {
                    if (!FP.contains(context.getKey())) {
                        assertEquals(context.getValue(), display.get(context.getKey()), name + " " + context.getKey());
                    }
                }
                if (frame == 0) assertEquals(original, display, name);
            }
        }
    }

    @Test void actual263ItemModelsCodecAcceptsGraphAndCanonicalNonFirstPersonFallback() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();
        ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        var graph = read("items/" + KEY + "ace_of_spades.json");
        var parsed = ItemModels.CODEC.parse(JsonOps.INSTANCE, graph.get("model"));
        assertTrue(parsed.error().isEmpty(), parsed.error().toString());
        assertNotNull(parsed.getOrThrow());
        var root = graph.getAsJsonObject("model");
        assertEquals("minecraft:select", root.get("type").getAsString());
        assertEquals("minecraft:display_context", root.get("property").getAsString());
        var cases = root.getAsJsonArray("cases");
        assertEquals(1, cases.size());
        var contexts = new HashSet<String>();
        for (var context : cases.get(0).getAsJsonObject().getAsJsonArray("when")) {
            contexts.add(context.getAsString());
        }
        assertEquals(FP, contexts);
        var old = read("items/weapon_aim_w70/ace_of_spades.json");
        assertEquals(old.getAsJsonObject("model").get("fallback"), root.get("fallback"));
    }
}
