package kim.biryeong.destiny.fx;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.Set;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/** Filesystem-only W106 overlay contract; no client bootstrap or native input. */
class ReticleParticlesW106Test {
    private static final Path ASSETS = Path.of("src/main/resources/assets/destiny");
    private static final Path MANIFEST = Path.of("art/hud/w105-shotgun/manifest.json");
    private static final Set<String> FRAMES = Set.of("aggressive", "precision", "lightweight", "rapid_fire");
    private static final String PARTICLE = ",\n    \"particle\": \"#0\"";

    @Test
    void overlayCoversExactlyTheFourOriginalModelsAndAllTwelveInventoryPaths() throws Exception {
        var manifest = json(MANIFEST);
        assertEquals(FRAMES, manifest.getAsJsonObject("frames").keySet());
        assertEquals(12, manifest.get("assetCount").getAsInt());
        var expected = new HashSet<String>();
        for (String frame : FRAMES) {
            String name = "reticle_w105_shotgun_" + frame;
            expected.add(ASSETS.resolve("models/gui/hud/" + name + ".json").toString());
            expected.add(ASSETS.resolve("items/gui/hud/" + name + ".json").toString());
            expected.add(ASSETS.resolve("textures/item/hud/" + name + ".png").toString());
        }
        assertEquals(expected, manifest.getAsJsonObject("sha256").keySet());
        for (String directory : Set.of("models/gui/hud", "items/gui/hud", "textures/item/hud")) {
            String extension = directory.startsWith("textures") ? ".png" : ".json";
            try (var files = Files.list(ASSETS.resolve(directory))) {
                var actual = files.filter(p -> p.getFileName().toString().startsWith("reticle_w105_shotgun_")
                                && p.toString().endsWith(extension))
                        .map(Path::toString).collect(Collectors.toSet());
                assertEquals(expected.stream().filter(p -> Path.of(p).getParent().equals(ASSETS.resolve(directory)))
                        .collect(Collectors.toSet()), actual, directory);
                assertEquals(4, actual.size(), directory);
            }
        }
    }

    @Test
    void particleAliasesResolveToEachOriginalPngAndPreserveAimGeometryAndTint() throws Exception {
        var manifest = json(MANIFEST);
        for (String frame : FRAMES) {
            String name = "reticle_w105_shotgun_" + frame;
            var model = json(modelPath(frame));
            var textures = model.getAsJsonObject("textures");
            assertEquals(Set.of("0", "particle"), textures.keySet(), frame);
            assertEquals("#0", textures.get("particle").getAsString(), frame);
            String texture = textures.get(textures.get("particle").getAsString().substring(1)).getAsString();
            assertEquals("destiny:item/hud/" + name, texture, frame);
            var png = ASSETS.resolve("textures/" + texture.substring("destiny:".length()) + ".png");
            assertTrue(Files.isRegularFile(png), frame);
            assertEquals(manifest.getAsJsonObject("sha256").get(png.toString()).getAsString(),
                    sha256(Files.readAllBytes(png)), frame);
            assertFalse(model.has("parent"), frame);
            assertEquals("front", model.get("gui_light").getAsString(), frame);
            var elements = model.getAsJsonArray("elements");
            assertEquals(1, elements.size(), frame);
            var quad = elements.get(0).getAsJsonObject();
            assertEquals(JsonParser.parseString("[0,0,8]"), quad.get("from"), frame);
            assertEquals(JsonParser.parseString("[16,16,8]"), quad.get("to"), frame);
            var faces = quad.getAsJsonObject("faces");
            assertEquals(Set.of("north", "south"), faces.keySet(), frame);
            for (String direction : faces.keySet()) {
                var face = faces.getAsJsonObject(direction);
                assertEquals("#0", face.get("texture").getAsString(), frame);
                assertEquals(JsonParser.parseString("[0,0,16,16]"), face.get("uv"), frame);
                assertEquals(0, face.get("tintindex").getAsInt(), frame);
            }
        }
    }

    @Test
    void strippingOnlyParticleRestoresOriginalCanonicalBytesAndManifestHashes() throws Exception {
        var hashes = json(MANIFEST).getAsJsonObject("sha256");
        for (String frame : FRAMES) {
            Path path = modelPath(frame);
            String patched = Files.readString(path);
            assertEquals(1, patched.split(java.util.regex.Pattern.quote(PARTICLE), -1).length - 1, frame);
            String original = patched.replace(PARTICLE, "");
            var stripped = JsonParser.parseString(patched).getAsJsonObject();
            assertEquals("#0", stripped.getAsJsonObject("textures").remove("particle").getAsString(), frame);
            assertEquals(stripped, JsonParser.parseString(original), frame);
            // The W105 byte hash pins whitespace, field order and all semantics,
            // including geometry, texture 0, UVs and tint; no manifest rewrite.
            assertEquals(hashes.get(path.toString()).getAsString(),
                    sha256(original.getBytes(StandardCharsets.UTF_8)), path.toString());
            assertNotEquals(hashes.get(path.toString()).getAsString(), sha256(Files.readAllBytes(path)), frame);
        }
    }

    @Test
    void allEightUnrelatedW105InventoryAssetsStillMatchTheOriginalManifest() throws Exception {
        var modelPaths = FRAMES.stream().map(ReticleParticlesW106Test::modelPath)
                .map(Path::toString).collect(Collectors.toSet());
        int untouched = 0;
        for (var entry : json(MANIFEST).getAsJsonObject("sha256").entrySet()) {
            if (modelPaths.contains(entry.getKey())) continue;
            assertEquals(entry.getValue().getAsString(), sha256(Files.readAllBytes(Path.of(entry.getKey()))),
                    "Unrelated original asset: " + entry.getKey());
            untouched++;
        }
        assertEquals(8, untouched, "Four item definitions and four PNGs remain byte-identical");
    }

    private static Path modelPath(String frame) {
        return ASSETS.resolve("models/gui/hud/reticle_w105_shotgun_" + frame + ".json");
    }

    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }

    private static String sha256(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
}
