package kim.biryeong.destiny.compat.pack;

import com.google.gson.*;
import eu.pb4.polymer.resourcepack.api.PackResource;
import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class PackAtlasRoutingTest {
    private static final String ITEMS = "assets/minecraft/atlases/items.json", BLOCKS = "assets/minecraft/atlases/blocks.json";
    private static PackAtlasRouting.Route rule(byte[] bytes) {
        return new PackAtlasRouting.Route(PackAtlasRouting.sha256(bytes), "assets/bettermodel/textures/", "minecraft:items", "minecraft:blocks");
    }
    @Test void followsRenamedSpritesWithoutTouchingTexturesOrUnrelatedAtlasSources() {
        var texture = PackResource.fromString("fixture png bytes");
        var bytes = texture.readAllBytes();
        var files = new HashMap<String, PackResource>();
        files.put("assets/bettermodel/textures/item/renamed.png", texture);
        files.put("assets/other/textures/item/renamed.png", texture);
        files.put(ITEMS, PackResource.fromString("{\"sources\":[{\"type\":\"minecraft:directory\",\"source\":\"item\",\"prefix\":\"item/\"}]}"));
        var result = PackAtlasRouting.route(files, List.of(rule(bytes)));
        assertEquals(List.of("bettermodel:item/renamed"), result.sprites());
        assertTrue(result.missingHashes().isEmpty());
        assertEquals(Set.of(ITEMS, BLOCKS), result.updates().keySet());
        var sources = JsonParser.parseString(result.updates().get(ITEMS).asString()).getAsJsonObject().getAsJsonArray("sources");
        assertEquals(2, sources.size());
        assertEquals("minecraft:directory", sources.get(0).getAsJsonObject().get("type").getAsString());
        var pattern = sources.get(1).getAsJsonObject().getAsJsonObject("pattern");
        assertTrue("item/renamed".matches(pattern.get("path").getAsString()));
        assertFalse("item/renamed2".matches(pattern.get("path").getAsString()));
        assertArrayEquals(bytes, texture.readAllBytes());
        files.putAll(result.updates());
        var repeated = PackAtlasRouting.route(files, List.of(rule(bytes)));
        assertEquals(result.updates().get(ITEMS).asString(), repeated.updates().get(ITEMS).asString());
        assertEquals(result.updates().get(BLOCKS).asString(), repeated.updates().get(BLOCKS).asString());
    }
    @Test void changedExternalTextureIsNotMatchedByItsGeneratedName() {
        var expected = "original".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        var result = PackAtlasRouting.route(Map.of("assets/bettermodel/textures/item/o.png", PackResource.fromString("different")), List.of(rule(expected)));
        assertTrue(result.updates().isEmpty());
        assertEquals(Set.of(PackAtlasRouting.sha256(expected)), result.missingHashes());
    }
    @Test void duplicateBytesAreRoutedAtEveryGeneratedSprite() {
        var data = PackResource.fromString("same");
        var result = PackAtlasRouting.route(Map.of("assets/bettermodel/textures/item/a.png", data,
                "assets/bettermodel/textures/item/b.png", data), List.of(rule(data.readAllBytes())));
        assertEquals(List.of("bettermodel:item/a", "bettermodel:item/b"), result.sprites());
    }
    @Test void conflictingDestinationFailsBeforeAnyBuilderMutation() {
        var data = PackResource.fromString("same"); var r = rule(data.readAllBytes());
        assertThrows(IllegalStateException.class, () -> PackAtlasRouting.route(Map.of("assets/bettermodel/textures/item/a.png", data),
                List.of(r, new PackAtlasRouting.Route(r.sha256(), r.texturePrefix(), r.from(), "minecraft:particles"))));
    }
}
