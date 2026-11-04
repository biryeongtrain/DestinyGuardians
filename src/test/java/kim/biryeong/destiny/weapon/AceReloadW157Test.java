package kim.biryeong.destiny.weapon;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import java.io.StringReader;
import java.nio.file.*;
import static org.junit.jupiter.api.Assertions.*;

/** Uses the actual 26.3 codecs; offline acceptance is not native motion/hand IK. */
class AceReloadW157Test {
    static final Path A = Path.of("src/main/resources/assets/destiny");
    static final String KEY = "weapon_reload_w157/ace_of_spades";
    static JsonObject json(Path p) throws Exception {
        return JsonParser.parseString(Files.readString(p)).getAsJsonObject();
    }
    @Test void onlyTheExistingReloadLifecycleCanSelectTheNewRoute() {
        var ace = WeaponCatalog.find("ace_of_spades").orElseThrow();
        assertTrue(WeaponReloadPresentation.supports(ace));
        assertEquals("destiny:" + KEY, WeaponReloadPresentation.model(ace).toString());
        assertEquals(1, WeaponReloadPresentation.PROGRESS_INDEX);
        assertEquals("weapon_sight_w159/", WeaponAimPresentation.modelPrefix(ace));
        assertTrue(WeaponAimPresentation.physicalSight(ace, 1));
    }
    @Test void targetCuboidParserAcceptsTwoPartsAndAll244Transforms() throws Exception {
        try (var paths = Files.list(A.resolve("models/weapon_reload_w157"))) {
            var all = paths.toList();
            assertEquals(246, all.size());
            for (var path : all) {
                String raw = Files.readString(path);
                assertNotNull(CuboidModel.fromStream(new StringReader(raw)), path.toString());
            }
            int body = json(A.resolve("models/" + KEY + "_body.json")).getAsJsonArray("elements").size();
            int cylinder = json(A.resolve("models/" + KEY + "_cylinder.json")).getAsJsonArray("elements").size();
            assertEquals(87, body + cylinder);
            int max = 0;
            for (int i = 0; i <= 60; i++) for (String grip : new String[]{"native", "twohand"}) {
                var frame = json(A.resolve("models/" + KEY + "_%02d_cylinder_%s.json".formatted(i, grip)));
                int assembled = body + (frame.has("elements") ? frame.getAsJsonArray("elements").size() : cylinder);
                assertTrue(assembled <= 1000, "Count parts visible together, not all alternative samples");
                max = Math.max(max, assembled);
            }
            assertEquals(93, max);
        }
    }
    @Test void targetCodecAcceptsGraphAndNonFirstpersonFallsBackToCanonical() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion(); net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap(); ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        var graph = json(A.resolve("items/" + KEY + ".json"));
        var model = graph.getAsJsonObject("model");
        var result = ItemModels.CODEC.parse(JsonOps.INSTANCE, model);
        assertTrue(result.error().isEmpty(), result.error().toString());
        assertEquals("minecraft:display_context", model.get("property").getAsString());
        assertEquals(json(A.resolve("items/weapon/ace_of_spades.json")).get("model"), model.get("fallback"));
        var contexts = model.getAsJsonArray("cases").get(0).getAsJsonObject();
        assertEquals(JsonParser.parseString("[\"firstperson_righthand\",\"firstperson_lefthand\"]"), contexts.get("when"));
    }
    @Test void sourceBodyIsAceAndAcceptedGripEndpointsRemainExact() throws Exception {
        var dataset = json(Path.of("art/weapons/w197/ace-source-motion.json"));
        var manifest = json(Path.of("art/weapons/w157/ace-reload.json"));
        assertEquals("80A8A567", dataset.getAsJsonObject("clip").get("tag").getAsString());
        assertEquals("4A0810C4", dataset.get("bodyBone").getAsString());
        assertEquals(127, dataset.getAsJsonArray("samples").size());
        assertEquals(61, manifest.get("frames").getAsInt());
        assertEquals(60, manifest.get("intervals").getAsInt());
        assertTrue(manifest.get("hybridAnimation").getAsBoolean());
        assertEquals("80A8A567", manifest.get("bodyMotionTag").getAsString());
        for (String grip : new String[]{"native", "twohand"}) {
            var accepted = json(A.resolve("models/item/weapon/ace_of_spades"
                    + (grip.equals("twohand") ? "_twohand" : "") + ".json")).get("display");
            for (int frame : new int[]{0, 60}) for (String part : new String[]{"body", "cylinder"}) {
                var pose = json(A.resolve("models/" + KEY + "_%02d_%s_%s.json".formatted(frame, part, grip)));
                assertEquals(accepted, pose.get("display"));
            }
            for (int frame = 1; frame < 60; frame++) {
                if (frame % 3 == 0) continue;
                for (String part : new String[]{"body", "cylinder"}) {
                    var moving = json(A.resolve("models/" + KEY + "_%02d_%s_%s.json".formatted(frame, part, grip)));
                    var lower = json(A.resolve("models/" + KEY + "_%02d_%s_%s.json".formatted(frame / 3 * 3, part, grip)));
                    var upper = json(A.resolve("models/" + KEY + "_%02d_%s_%s.json".formatted((frame / 3 + 1) * 3, part, grip)));
                    assertNotEquals(lower.get("display"), moving.get("display"));
                    assertNotEquals(upper.get("display"), moving.get("display"));
                }
            }
        }
    }


    @Test void all61FloatBucketsIncludeTheActivationOffsetWithoutAdvancing() throws Exception {
        var entries = json(A.resolve("items/" + KEY + ".json"))
                .getAsJsonObject("model").getAsJsonArray("cases").get(0).getAsJsonObject()
                .getAsJsonObject("model").getAsJsonArray("entries");
        assertEquals(61, entries.size());
        for (int frame = 0; frame <= 60; frame++) {
            float threshold = entries.get(frame).getAsJsonObject().get("threshold").getAsFloat();
            assertEquals(frame / 60f, threshold);
            for (float offset : new float[]{0, .001f}) {
                float wire = frame / 60f + offset;
                int selected = -1;
                for (int i = 0; i < entries.size(); i++)
                    if (wire >= entries.get(i).getAsJsonObject().get("threshold").getAsFloat()) selected = i;
                assertEquals(frame, selected, "frame=" + frame + " offset=" + offset);
            }
            if (frame > 0) {
                float below = Math.nextDown(threshold);
                assertTrue(below < threshold);
                assertTrue(below >= entries.get(frame - 1).getAsJsonObject().get("threshold").getAsFloat());
            }
            if (frame == 0 || frame == 60)
                assertEquals(json(A.resolve("items/weapon/ace_of_spades.json")).get("model"),
                        entries.get(frame).getAsJsonObject().get("model"));
        }
    }

}
