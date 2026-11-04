package kim.biryeong.destiny.weapon;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties;
import net.minecraft.client.renderer.item.properties.conditional.CustomModelDataProperty;
import net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties;
import net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import net.minecraft.world.item.component.CustomModelData;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.function.Consumer;

import static org.junit.jupiter.api.Assertions.*;

/** Targeted 26.3 codecs; main runs this centrally. No native pixel acceptance. */
class AmmitCrouchModelsW161Test {
    private static final Path ROOT = Path.of("");
    private static final String ASSETS = "src/main/resources/assets/destiny/";
    private static final String MANIFEST = "art/weapons/w161/ammit-crouch.json";
    private static final Set<String> THIRD = Set.of("thirdperson_righthand", "thirdperson_lefthand");

    @BeforeAll static void bootstrap() {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();
        ItemTintSources.bootstrap();
        SelectItemModelProperties.bootstrap();
        ConditionalItemModelProperties.bootstrap();
        RangeSelectItemModelProperties.bootstrap();
    }

    private static JsonObject json(String path) throws Exception {
        return JsonParser.parseString(Files.readString(ROOT.resolve(path))).getAsJsonObject();
    }

    private static void walk(JsonElement element, Consumer<JsonObject> visit) {
        if (element.isJsonObject()) {
            var object = element.getAsJsonObject();
            visit.accept(object);
            object.entrySet().forEach(entry -> walk(entry.getValue(), visit));
        } else if (element.isJsonArray()) {
            element.getAsJsonArray().forEach(child -> walk(child, visit));
        }
    }

    private static String sha(String path) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(ROOT.resolve(path))));
    }

    @Test void actual26_3ItemModelsCodecAcceptsAllSevenProductGraphs() throws Exception {
        var graphs = json(MANIFEST).getAsJsonObject("graphs");
        assertEquals(7, graphs.size());
        for (var entry : graphs.entrySet()) {
            var result = ItemModels.CODEC.parse(JsonOps.INSTANCE, json(entry.getKey()).get("model"));
            assertTrue(result.isSuccess(), entry.getKey() + ": " + result.error());
        }
    }

    @Test void actualCodecRejectsInventedPropertiesAndInvalidContext() {
        var leaf = "{\"type\":\"minecraft:model\",\"model\":\"destiny:weapon/auto_rifle/ammit_ar2_twohand\"}";
        for (String property : List.of("minecraft:entity_properties", "minecraft:keybind_downonlylocal")) {
            var invalid = JsonParser.parseString("{\"type\":\"minecraft:condition\",\"property\":\"" + property
                    + "\",\"on_true\":" + leaf + ",\"on_false\":" + leaf + "}");
            assertFalse(ItemModels.CODEC.parse(JsonOps.INSTANCE, invalid).isSuccess(), property);
        }
        var invalid = JsonParser.parseString("{\"type\":\"minecraft:select\",\"property\":\"minecraft:display_context\","
                + "\"cases\":[{\"when\":\"thirdperson_both\",\"model\":" + leaf + "}],\"fallback\":" + leaf + "}");
        assertFalse(ItemModels.CODEC.parse(JsonOps.INSTANCE, invalid).isSuccess());
    }

    @Test void actualCuboidParserAcceptsThreeChildrenAndTheirExactCanonicalParents() throws Exception {
        var manifest = json(MANIFEST);
        assertEquals(3, manifest.getAsJsonObject("generatedModels").size());
        for (String pose : List.of("hip", "ads", "inspect")) {
            String path = ASSETS + "models/weapon_pose_w161/ammit_ar2_" + pose + ".json";
            var source = Files.readString(ROOT.resolve(path));
            var child = assertDoesNotThrow(() -> CuboidModel.fromStream(new StringReader(source)));
            assertNotNull(child);
            var raw = JsonParser.parseString(source).getAsJsonObject();
            assertEquals(Set.of("parent", "display"), raw.keySet());
            assertEquals(THIRD, raw.getAsJsonObject("display").keySet());
            String expected = manifest.getAsJsonObject("bases").getAsJsonObject(pose).get("parent").getAsString();
            assertEquals(expected, child.parent().toString());
            String parentPath = ASSETS + "models/" + expected.substring("destiny:".length()) + ".json";
            var parentText = Files.readString(ROOT.resolve(parentPath));
            assertNotNull(assertDoesNotThrow(() -> CuboidModel.fromStream(new StringReader(parentText))));
            assertEquals(manifest.getAsJsonObject("bases").getAsJsonObject(pose).get("newThirdperson"), raw.get("display"));
        }
    }

    @Test void actualBooleanPropertyAndComponentCodecsKeepCrouchSeparateFromAds() {
        // ItemStack runtime evaluation/Polymer copies live in WeaponCrouchW161GameTests;
        // plain JUnit bootstrap has no bound default item components in 26.3.
        var crouchProperty = CustomModelDataProperty.MAP_CODEC.codec().parse(JsonOps.INSTANCE,
                JsonParser.parseString("{\"index\":1}")).getOrThrow();
        var gripProperty = CustomModelDataProperty.MAP_CODEC.codec().parse(JsonOps.INSTANCE,
                JsonParser.parseString("{\"index\":0}")).getOrThrow();
        assertEquals(1, crouchProperty.index());
        assertEquals(0, gripProperty.index());
        for (boolean grip : List.of(false, true)) for (boolean crouch : List.of(false, true)) {
            for (float lingeringAds : List.of(0f, .5f, 1f)) {
                var cmd = new CustomModelData(List.of(0f, 0f, 0f, lingeringAds),
                        List.of(grip, crouch), List.of("ads"), List.of());
                var encoded = CustomModelData.CODEC.encodeStart(JsonOps.INSTANCE, cmd).getOrThrow();
                var decoded = CustomModelData.CODEC.parse(JsonOps.INSTANCE, encoded).getOrThrow();
                assertEquals(cmd, decoded);
                assertEquals(crouch, decoded.getBoolean(crouchProperty.index()));
                assertEquals(grip, decoded.getBoolean(gripProperty.index()));
                assertEquals(lingeringAds, decoded.floats().get(3));
            }
        }
        assertNull(new CustomModelData(List.of(1f), List.of(true), List.of("ads"), List.of()).getBoolean(1));
    }

    @Test void allTwentyOneWrappersUseOnlyThirdpersonAndBooleanIndexOne() throws Exception {
        int total = 0;
        for (String path : json(MANIFEST).getAsJsonObject("graphs").keySet()) {
            int[] count = {0};
            walk(json(path), node -> {
                if (!node.has("property") || !"minecraft:display_context".equals(node.get("property").getAsString())) return;
                var fallback = node.getAsJsonObject("fallback");
                if (!fallback.has("type") || !"minecraft:model".equals(fallback.get("type").getAsString())) return;
                if (!fallback.get("model").getAsString().startsWith("destiny:weapon/auto_rifle/ammit_ar2")) return;
                count[0]++;
                assertEquals(1, node.getAsJsonArray("cases").size());
                var branch = node.getAsJsonArray("cases").get(0).getAsJsonObject();
                assertEquals(2, branch.getAsJsonArray("when").size());
                var contexts = new java.util.HashSet<String>();
                branch.getAsJsonArray("when").forEach(value -> contexts.add(value.getAsString()));
                assertEquals(THIRD, contexts);
                var condition = branch.getAsJsonObject("model");
                assertEquals("minecraft:condition", condition.get("type").getAsString());
                assertEquals("minecraft:custom_model_data", condition.get("property").getAsString());
                assertEquals(1, condition.get("index").getAsInt());
                assertEquals(fallback, condition.get("on_false"));
                assertTrue(condition.getAsJsonObject("on_true").get("model").getAsString().startsWith("destiny:weapon_pose_w161/"));
            });
            assertEquals(3, count[0], path);
            total += count[0];
        }
        assertEquals(21, total);
    }

    @Test void manifestGuardsPreservedSourcesAndProductHashesAndLeavesNativePending() throws Exception {
        var manifest = json(MANIFEST);
        for (var entry : manifest.getAsJsonObject("preservedSources").entrySet()) {
            var record = entry.getValue().getAsJsonObject();
            assertEquals(record.get("beforeSha256"), record.get("afterSha256"));
            assertEquals(record.get("beforeSha256").getAsString(), sha(entry.getKey()), entry.getKey());
        }
        for (var entry : manifest.getAsJsonObject("graphs").entrySet()) {
            var record = entry.getValue().getAsJsonObject();
            assertEquals(record.get("afterSha256").getAsString(), sha(entry.getKey()));
            assertEquals(record.get("beforeSha256"), record.get("restoredSourceSha256"));
            assertEquals(record.get("firstpersonBefore"), record.get("firstpersonAfter"));
            assertEquals(record.get("animatedEntriesBefore"), record.get("animatedEntriesAfter"));
        }
        for (var entry : manifest.getAsJsonObject("generatedModels").entrySet()) {
            assertEquals(entry.getValue().getAsString(), sha(entry.getKey()));
        }
        assertFalse(manifest.getAsJsonObject("native").get("visualAcceptance").getAsBoolean());
        assertEquals(0, manifest.getAsJsonObject("native").get("operations").getAsInt());
    }
}
