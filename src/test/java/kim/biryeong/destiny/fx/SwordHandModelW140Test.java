package kim.biryeong.destiny.fx;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import eu.pb4.polymer.resourcepack.api.PackResource;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/** Pack-output contracts only; native hand-cache/camera/BetterModel behavior needs master QA. */
class SwordHandModelW140Test {
    private static final String TARGET = "assets/destiny/items/weapon/abide_the_return.json";

    @Test void allowlistIsExactlyTheFiveCatalogSwordItemDefinitions() {
        var expected = Set.of("abide_the_return", "goldtusk", "crown_splitter", "falling_guillotine",
                "temptation_s_hook");
        var swords = WeaponCatalog.family("sword");
        assertEquals(expected, swords.stream().map(WeaponCatalog.Entry::id).collect(Collectors.toSet()));
        assertEquals(5, SwordHandModelAssets.TARGETS.size());
        assertEquals(swords.stream().map(e -> "assets/destiny/items/weapon/" + e.id() + ".json")
                .collect(Collectors.toSet()), Set.copyOf(SwordHandModelAssets.TARGETS));
    }

    @Test void allCanonicalSwordsMaskOnlyBothFirstPersonContextsAndKeepEntireFallback() throws Exception {
        for (String path : SwordHandModelAssets.TARGETS) {
            String source = canonical(path);
            JsonObject original = object(source);
            JsonObject output = object(SwordHandModelAssets.transform(path, source));
            JsonObject select = output.getAsJsonObject("model");
            assertEquals("minecraft:select", select.get("type").getAsString(), path);
            assertEquals("minecraft:display_context", select.get("property").getAsString(), path);
            assertEquals(Set.of("type", "property", "cases", "fallback"), select.keySet(), path);
            var cases = select.getAsJsonArray("cases");
            assertEquals(1, cases.size(), path);
            var handCase = cases.get(0).getAsJsonObject();
            assertEquals(JsonParser.parseString("[\"firstperson_righthand\",\"firstperson_lefthand\"]"),
                    handCase.get("when"), path);
            assertEquals(object("{\"type\":\"minecraft:empty\"}"), handCase.get("model"), path);
            // GUI, ground, both third-person hands, fixed/BM props and all other contexts fall back.
            assertEquals(original.get("model"), select.get("fallback"), path);
            assertEquals(original.keySet(), output.keySet(), path);
            for (String key : original.keySet()) if (!key.equals("model"))
                assertEquals(original.get(key), output.get(key), path + ":" + key);
        }
    }

    @Test void wrappingPreservesNestedRoutingAndUnknownRootFieldsWithoutMutatingInput() throws Exception {
        JsonObject original = object(canonical(TARGET));
        original.addProperty("oversized_in_gui", true);
        original.addProperty("swap_animation_scale", 0.25);
        original.add("future_root", JsonParser.parseString("{\"nested\":[1,false,{\"keep\":\"yes\"}]}"));
        JsonObject before = original.deepCopy();
        JsonObject output = SwordHandModelAssets.wrap(TARGET, original);
        assertNotSame(original, output);
        assertEquals(before, original);
        assertEquals(before.get("model"), output.getAsJsonObject("model").get("fallback"));
        for (String key : before.keySet()) if (!key.equals("model"))
            assertEquals(before.get(key), output.get(key), key);
        // Returned nested structures are independent too.
        output.getAsJsonObject("model").getAsJsonObject("fallback").addProperty("changed", true);
        output.getAsJsonObject("future_root").addProperty("changed", true);
        assertEquals(before, original);
    }

    @Test void transformationIsDeterministicAndByteIdempotentForEveryCanonicalSword() throws Exception {
        for (String path : SwordHandModelAssets.TARGETS) {
            String source = canonical(path);
            String once = SwordHandModelAssets.transform(path, source);
            assertEquals(once, SwordHandModelAssets.transform(path, source), path);
            assertEquals(once, SwordHandModelAssets.transform(path, once), path);
            String formatted = "\n " + once + " \n";
            assertEquals(formatted, SwordHandModelAssets.transform(path, formatted), path);
            var wrapped = PackResource.fromString(once);
            assertSame(wrapped, SwordHandModelAssets.convert(path, wrapped), path);
        }
    }

    @Test void anExistingDisplayContextSelectorIsPreservedAsAWholeRatherThanFlattened() {
        String source = """
                {"model":{"type":"minecraft:select","property":"minecraft:display_context",
                "cases":[{"when":"gui","model":{"type":"minecraft:model","model":"destiny:ui/sword"}}],
                "fallback":{"type":"minecraft:model","model":"destiny:weapon/sword/test"}}}
                """;
        String output = SwordHandModelAssets.transform(TARGET, source);
        assertEquals(object(source).get("model"), object(output).getAsJsonObject("model").get("fallback"));
        assertEquals(output, SwordHandModelAssets.transform(TARGET, output));
    }

    @Test void foreignAndNearMatchPathsPassThroughWithoutParsingOrMasking() {
        for (String path : List.of(
                "assets/destiny/items/weapon/ammit_ar2.json",
                "assets/destiny/items/weapon/abide_the_return_ads.json",
                "assets/destiny/items/weapon/abide_the_return.json.bak",
                "assets/destiny/items/weapon/sub/abide_the_return.json",
                "assets/destiny/models/weapon/sword/abide_the_return.json",
                "assets/foreign/items/weapon/abide_the_return.json")) {
            String invalidJson = "not JSON";
            assertSame(invalidJson, SwordHandModelAssets.transform(path, invalidJson), path);
            var resource = PackResource.fromString(invalidJson);
            assertSame(resource, SwordHandModelAssets.convert(path, resource), path);
            assertNull(SwordHandModelAssets.convert(path, null), path);
            assertNull(SwordHandModelAssets.wrap(path, null), path);
        }
    }

    @Test void missingOrInvalidOwnedSourcesFailLoudlyWithTheExactPath() {
        for (String source : List.of("{", "[]", "null", "1", "{}", "{\"model\":null}",
                "{\"model\":[]}", "{\"model\":{}}", "{\"model\":{\"type\":false}}",
                "{\"model\":{\"type\":\"\"}}", "{\"model\":{\"type\":\"bad type\"}}")) {
            var error = assertThrows(IllegalStateException.class,
                    () -> SwordHandModelAssets.transform(TARGET, source), source);
            assertTrue(error.getMessage().contains(TARGET), source);
        }
        assertThrows(IllegalStateException.class, () -> SwordHandModelAssets.transform(TARGET, null));
        assertThrows(IllegalStateException.class, () -> SwordHandModelAssets.wrap(TARGET, null));
        assertThrows(IllegalStateException.class, () -> SwordHandModelAssets.convert(TARGET, null));
    }

    @Test void packConversionLeavesCanonicalAssetBytesAndSourceResourceUnchanged() throws Exception {
        for (String path : SwordHandModelAssets.TARGETS) {
            Path file = Path.of("src/main/resources").resolve(path);
            byte[] before = Files.readAllBytes(file);
            var resource = PackResource.of(before.clone());
            var converted = SwordHandModelAssets.convert(path, resource);
            assertNotSame(resource, converted, path);
            assertArrayEquals(before, resource.readAllBytes(), path);
            assertArrayEquals(before, Files.readAllBytes(file), path);
            assertEquals(object(new String(before, java.nio.charset.StandardCharsets.UTF_8)).get("model"),
                    converted.asJson().getAsJsonObject().getAsJsonObject("model").get("fallback"), path);
        }
    }

    private static String canonical(String path) throws Exception {
        return Files.readString(Path.of("src/main/resources").resolve(path));
    }

    private static JsonObject object(String source) {
        return JsonParser.parseString(source).getAsJsonObject();
    }
}
