package kim.biryeong.destiny.compat.pack;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import eu.pb4.polymer.resourcepack.api.PackResource;
import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class ParticleTextureFallbacksTest {
    private static final Path RES = Path.of("src/main/resources");
    private static final String HUD = "assets/destiny/models/gui/hud/";

    @Test void repairsCurrentStandaloneModelsWithoutChangingAnyOtherField() throws Exception {
        var paths = new ArrayList<Path>();
        try (var files = Files.walk(RES.resolve(HUD))) {
            files.filter(Files::isRegularFile).filter(p -> p.toString().endsWith(".json"))
                    .sorted().forEach(paths::add);
        }
        paths.add(RES.resolve("assets/destiny/models/fx/glaive_shield_w41.json"));
        var expectedRepairs = new HashSet<String>();
        var repaired = new HashSet<String>();
        for (Path file : paths) {
            String path = RES.relativize(file).toString();
            var original = JsonParser.parseString(Files.readString(file)).getAsJsonObject();
            Set<String> faceSprites = eligibleFaceSprites(original);
            if (!faceSprites.isEmpty()) expectedRepairs.add(path);
            var input = PackResource.fromString(original.toString());
            var output = ParticleTextureFallbacks.convert(path, input);
            if (input != output) repaired.add(path);
            if (faceSprites.isEmpty()) {
                assertSame(input, output, "Ineligible model must remain untouched: " + path);
                continue;
            }
            assertNotSame(input, output, "Missing particle fallback: " + path);
            var model = JsonParser.parseString(output.asString()).getAsJsonObject();
            var particle = model.getAsJsonObject("textures").remove("particle");
            assertNotNull(particle, path);
            assertTrue(particle.isJsonPrimitive() && particle.getAsJsonPrimitive().isString(), path);
            String sprite = particle.getAsString();
            assertTrue(faceSprites.contains(sprite), "Particle must be a resolved input face sprite: " + path);
            String[] location = sprite.split(":", 2);
            assertTrue(Files.isRegularFile(RES.resolve("assets/" + location[0] + "/textures/"
                    + location[1] + ".png")), sprite);
            assertEquals(original, model, "Only the particle slot may change: " + path);
            assertSame(output, ParticleTextureFallbacks.convert(path, output), path);
        }
        assertFalse(expectedRepairs.isEmpty(), "The asset scan must exercise particle repair");
        assertEquals(expectedRepairs, repaired, "Every eligible standalone HUD/glaive model must be repaired");
    }

    // Build the input texture alias closure independently of the converter's traversal/first-face choice.
    private static Set<String> eligibleFaceSprites(JsonObject model) {
        if (model.has("parent") || !model.has("elements") || !model.has("textures")) return Set.of();
        var textures = model.getAsJsonObject("textures");
        if (textures.has("particle")) return Set.of();
        var resolved = new HashMap<String, String>();
        for (var entry : textures.entrySet()) {
            if (entry.getValue().isJsonPrimitive()) {
                String value = entry.getValue().getAsString();
                if (value.matches("[a-z0-9_.-]+:[a-z0-9_./-]+")) resolved.put(entry.getKey(), value);
            }
        }
        boolean changed;
        do {
            int size = resolved.size();
            for (var entry : textures.entrySet()) {
                if (!entry.getValue().isJsonPrimitive()) continue;
                String alias = entry.getValue().getAsString();
                if (alias.startsWith("#") && resolved.containsKey(alias.substring(1))) {
                    resolved.put(entry.getKey(), resolved.get(alias.substring(1)));
                }
            }
            changed = resolved.size() != size;
        } while (changed);
        var sprites = new HashSet<String>();
        for (var element : model.getAsJsonArray("elements")) {
            var cube = element.getAsJsonObject();
            if (!cube.has("faces")) continue;
            for (var face : cube.getAsJsonObject("faces").entrySet()) {
                var texture = face.getValue().getAsJsonObject().get("texture");
                if (texture == null) continue;
                String reference = texture.getAsString();
                String sprite = reference.startsWith("#") ? resolved.get(reference.substring(1)) : reference;
                if (sprite != null && sprite.matches("[a-z0-9_.-]+:[a-z0-9_./-]+")) sprites.add(sprite);
            }
        }
        return sprites;
    }

    @Test void preservesExistingParticlesInheritedModelsAndUnrelatedResources() {
        String face = "\"elements\":[{\"faces\":{\"north\":{\"texture\":\"#layer0\"}}}]";
        for (String source : new String[]{
                "{\"parent\":\"destiny:gui/hud/solid\",\"textures\":{\"layer0\":\"destiny:item/hud/tile\"}," + face + "}",
                "{\"textures\":{\"layer0\":\"destiny:item/hud/tile\",\"particle\":\"#layer0\"}," + face + "}",
                "{\"textures\":{\"layer0\":\"destiny:item/hud/tile\",\"particle\":\"destiny:item/hud/existing\"}," + face + "}",
                "{\"textures\":{\"layer0\":\"destiny:item/hud/tile\"}}",
                "{" + face + "}",
                "{\"textures\":{\"layer0\":\"destiny:item/hud/tile\"},\"elements\":[]}"}) {
            var input = PackResource.fromString(source);
            assertSame(input, ParticleTextureFallbacks.convert(HUD + "example.json", input), source);
        }
        var other = PackResource.fromString("not JSON, must not be inspected");
        assertSame(other, ParticleTextureFallbacks.convert("assets/destiny/models/weapon/example.json", other));
        assertNull(ParticleTextureFallbacks.convert(HUD + "missing.json", null));
    }

    @Test void followsFaceAliasesButDoesNotInventFallbacksForCyclesOrMissingSlots() {
        String prefix = "{\"textures\":%s,\"elements\":[{\"faces\":{\"north\":{\"texture\":\"#a\"}}}]}";
        for (String aliases : new String[]{"{\"a\":\"#b\",\"b\":\"#a\"}", "{\"a\":\"#missing\"}",
                "{\"a\":\"invalid sprite\"}", "{\"a\":{}}",
                "{\"unused\":\"destiny:item/hud/tile\"}"}) {
            var input = PackResource.fromString(prefix.formatted(aliases));
            assertSame(input, ParticleTextureFallbacks.convert(HUD + "aliases.json", input), aliases);
        }
        var input = PackResource.fromString(prefix.formatted("{\"a\":\"#b\",\"b\":\"destiny:item/hud/tile\"}"));
        var output = ParticleTextureFallbacks.convert(HUD + "aliases.json", input);
        assertEquals("destiny:item/hud/tile", JsonParser.parseString(output.asString()).getAsJsonObject()
                .getAsJsonObject("textures").get("particle").getAsString());
        assertSame(output, ParticleTextureFallbacks.convert(HUD + "aliases.json", output));
    }

    @Test void skipsUnresolvableFacesAndUsesADirectFaceSprite() {
        var original = JsonParser.parseString("""
                {"textures":{"unused":"destiny:item/hud/unrelated"},"elements":[
                  {"from":[0,0,8],"to":[16,16,8],"faces":{
                    "north":{"texture":"#missing"},
                    "south":{"texture":"destiny:item/hud/tile","tintindex":0}}}]}
                """).getAsJsonObject();
        var input = PackResource.fromString(original.toString());
        var output = ParticleTextureFallbacks.convert(HUD + "direct.json", input);
        var model = JsonParser.parseString(output.asString()).getAsJsonObject();
        assertEquals("destiny:item/hud/tile", model.getAsJsonObject("textures").remove("particle").getAsString());
        assertEquals(original, model);
        assertSame(output, ParticleTextureFallbacks.convert(HUD + "direct.json", output));
    }
}
