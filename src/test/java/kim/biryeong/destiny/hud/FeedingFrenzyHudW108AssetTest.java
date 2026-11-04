package kim.biryeong.destiny.hud;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Set;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/** Pure offline asset contracts: JUnit/Gson/JDK only, no Minecraft bootstrap or runtime claims. */
class FeedingFrenzyHudW108AssetTest {
    private static final String NAME = "perk_feeding_frenzy_w108";
    private static final String ICON = "destiny:gui/hud/" + NAME;
    private static final Path ASSETS = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/weapons/w108/hud");
    private static final Path ITEM = ASSETS.resolve("items/gui/hud/" + NAME + ".json");
    private static final Path MODEL = ASSETS.resolve("models/gui/hud/" + NAME + ".json");
    private static final Path PNG = ASSETS.resolve("textures/item/hud/" + NAME + ".png");
    private static final Set<String> PACK = Set.of(ITEM.toString(), MODEL.toString(), PNG.toString());
    private static final Set<String> OWNED = Set.of(
            "scripts/build_feeding_frenzy_hud_w108.py",
            "src/test/java/kim/biryeong/destiny/hud/FeedingFrenzyHudW108AssetTest.java",
            ART.resolve("label-source.svg").toString(), ART.resolve("offline-preview.png").toString(),
            ART.resolve("manifest.json").toString(), ITEM.toString(), MODEL.toString(), PNG.toString());

    @Test
    void exactRgbaPngFits118By24WithWhiteTranslucentGlyphsAndUnclippedMargins() throws Exception {
        byte[] bytes = Files.readAllBytes(PNG);
        assertEquals("89504e470d0a1a0a", HexFormat.of().formatHex(bytes, 0, 8));
        assertEquals("IHDR", new String(bytes, 12, 4, java.nio.charset.StandardCharsets.US_ASCII));
        assertEquals(118, ByteBuffer.wrap(bytes, 16, 4).getInt());
        assertEquals(24, ByteBuffer.wrap(bytes, 20, 4).getInt());
        assertEquals(8, bytes[24], "8-bit channels");
        assertEquals(6, bytes[25], "RGBA, no palette or RGB-only substitute");
        assertEquals("ce4e7bee537c2964b7f7de13288c3953a372793e5bb61625a72b9983d60fa792",
                sha256(bytes), "Exact authored PNG bytes");
        var image = ImageIO.read(PNG.toFile());
        assertNotNull(image);
        assertEquals(118, image.getWidth());
        assertEquals(24, image.getHeight());
        assertTrue(image.getColorModel().hasAlpha());
        int visible = 0, translucent = 0, solid = 0;
        int minX = 118, minY = 24, maxX = -1, maxY = -1;
        for (int y = 0; y < 24; y++) for (int x = 0; x < 118; x++) {
            int pixel = image.getRGB(x, y), alpha = pixel >>> 24;
            assertEquals(0xFFFFFF, pixel & 0xFFFFFF, "White RGB preserves CMD tint, including clear pixels");
            if (alpha > 0) {
                visible++;
                minX = Math.min(x, minX); minY = Math.min(y, minY);
                maxX = Math.max(x, maxX); maxY = Math.max(y, maxY);
                if (alpha < 255) translucent++; else solid++;
            }
            if (x == 0 || x == 117 || y == 0 || y == 23) assertEquals(0, alpha, "No edge clipping");
        }
        assertTrue(visible > 500 && visible < 118 * 24 * .65, "Readable glyph coverage; no blank or solid panel");
        assertTrue(translucent > 100 && solid > 25, "Antialiased alpha and legible solid glyph cores");
        var bounds = json(ART.resolve("manifest.json")).getAsJsonArray("alpha_bounds_px");
        assertEquals(JsonParser.parseString("[" + minX + "," + minY + "," + (maxX + 1) + "," + (maxY + 1) + "]"), bounds);
    }

    @Test
    void iconRoutesExactlyToTintZeroModelWithBothFullUvFacesAndExplicitParticleReference() throws Exception {
        assertEquals(JsonParser.parseString("""
                {"model":{"type":"minecraft:model","model":"destiny:gui/hud/perk_feeding_frenzy_w108",
                "tints":[{"type":"minecraft:custom_model_data","index":0,"default":16777215}]}}
                """), json(ITEM));
        assertEquals(JsonParser.parseString("""
                {"ambientocclusion":false,"gui_light":"front",
                "textures":{"0":"destiny:item/hud/perk_feeding_frenzy_w108","particle":"#0"},
                "elements":[{"from":[0,0,8],"to":[16,16,8],"shade":false,"faces":{
                "north":{"texture":"#0","uv":[0,0,16,16],"tintindex":0},
                "south":{"texture":"#0","uv":[0,0,16,16],"tintindex":0}}}]}
                """), json(MODEL));
        var itemModel = json(ITEM).getAsJsonObject("model");
        assertEquals(MODEL, resource("models", itemModel.get("model").getAsString(), ".json"));
        var textures = json(MODEL).getAsJsonObject("textures");
        assertEquals("#0", textures.get("particle").getAsString());
        assertEquals(PNG, resource("textures", textures.get("0").getAsString(), ".png"));
        assertTrue(Files.isRegularFile(PNG));
        assertFalse(Files.exists(ASSETS.resolve("textures/gui/hud/" + NAME + ".png")), "No texture outside the default item atlas");
        assertTrue(textures.get("0").getAsString().startsWith("destiny:item/"), "Item-model texture must be included by the vanilla items atlas directory source");
    }

    @Test
    void packBudgetIsExactlyOneLabelThreeAssetsAndEightOwnedPaths() throws Exception {
        var manifest = json(ART.resolve("manifest.json"));
        var delta = manifest.getAsJsonObject("pack_delta");
        assertEquals(1, delta.get("new_labels").getAsInt());
        assertEquals(3, delta.get("new_files").getAsInt());
        assertEquals(16384, delta.get("byte_budget").getAsInt());
        assertEquals(PACK, strings(delta.getAsJsonArray("paths")));
        assertEquals(3, delta.getAsJsonArray("paths").size());
        assertEquals(OWNED, strings(manifest.getAsJsonArray("freeze_paths")));
        assertEquals(8, manifest.getAsJsonArray("freeze_paths").size());
        long total = 0;
        for (String path : PACK) total += Files.size(Path.of(path));
        assertEquals(total, delta.get("bytes").getAsLong());
        assertTrue(total <= 16384, "Label triplet total byte budget");
        var found = new java.util.HashSet<String>();
        // Includes the legacy texture directory so an accidental duplicate is rejected.
        for (String folder : Set.of("items/gui/hud", "models/gui/hud", "textures/gui/hud", "textures/item/hud")) {
            // Empty legacy directories are not stored by Git or the isolated CoW seeder.
            // Required current directories still fail if missing; scan legacy duplicates when present.
            if (folder.equals("textures/gui/hud") && !Files.exists(ASSETS.resolve(folder))) continue;
            try (var files = Files.list(ASSETS.resolve(folder))) {
                files.filter(p -> p.getFileName().toString().startsWith(NAME)).forEach(p -> found.add(p.toString()));
            }
        }
        assertEquals(PACK, found);
        try (var files = Files.walk(ART)) {
            assertEquals(Set.of("label-source.svg", "offline-preview.png", "manifest.json"),
                    files.filter(Files::isRegularFile).map(p -> ART.relativize(p).toString()).collect(Collectors.toSet()));
        }
    }

    @Test
    void generatedSourceProvenanceAndFreezeHashesCoverOnlyThisSlice() throws Exception {
        var manifest = json(ART.resolve("manifest.json"));
        assertEquals("W108", manifest.get("stage").getAsString());
        assertEquals("FEEDING FRENZY", manifest.get("label").getAsString());
        assertEquals(JsonParser.parseString("[118,24]"), manifest.get("label_size_px"));
        assertTrue(manifest.get("font_size_px").getAsInt() >= 15);
        assertEquals("fcf34b330033e26c06e9bd466bea5a3e4b2f39272972275369beb7d8b257ed57",
                manifest.get("font_sha256").getAsString());
        assertEquals("OFFLINE LABEL PREVIEW - NOT IN GAME", manifest.get("preview_status").getAsString());
        var runtime = manifest.getAsJsonObject("runtime_contract");
        assertEquals(ICON, runtime.get("icon_id").getAsString());
        var reused = new java.util.HashSet<>(Set.of("perk_buff_w61", "perk_stack_x_w83", "perk_colon_w61"));
        for (int n = 0; n < 10; n++) reused.add("ammo_digit_" + n);
        assertEquals(reused, strings(runtime.getAsJsonArray("reused_icons")));
        for (String name : reused) {
            assertTrue(Files.isRegularFile(ASSETS.resolve("items/gui/hud/" + name + ".json")), name);
        }
        var hashed = new java.util.HashSet<String>();
        for (String section : Set.of("sha256", "source_sha256")) {
            for (var entry : manifest.getAsJsonObject(section).entrySet()) {
                assertTrue(OWNED.contains(entry.getKey()), "No shared files in W108 freeze");
                assertEquals(entry.getValue().getAsString(), sha256(Files.readAllBytes(Path.of(entry.getKey()))), entry.getKey());
                assertTrue(hashed.add(entry.getKey()), "No duplicate hash entries");
            }
        }
        var expectedHashes = new java.util.HashSet<>(OWNED);
        expectedHashes.remove(ART.resolve("manifest.json").toString());
        assertEquals(expectedHashes, hashed);
        var generated = new java.util.HashSet<>(OWNED);
        generated.remove("scripts/build_feeding_frenzy_hud_w108.py");
        generated.remove("src/test/java/kim/biryeong/destiny/hud/FeedingFrenzyHudW108AssetTest.java");
        assertEquals(generated, strings(manifest.getAsJsonArray("generated_paths")));
        var svgFactory = javax.xml.parsers.DocumentBuilderFactory.newInstance();
        svgFactory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        var svg = svgFactory.newDocumentBuilder().parse(ART.resolve("label-source.svg").toFile());
        assertEquals("118", svg.getDocumentElement().getAttribute("width"));
        assertEquals("24", svg.getDocumentElement().getAttribute("height"));
        assertEquals(0, svg.getElementsByTagName("text").getLength(), "Self-contained coverage vectors; no external font");
        assertEquals(0, svg.getElementsByTagName("image").getLength(), "No linked or embedded official sprite");
        assertTrue(svg.getElementsByTagName("rect").getLength() > 100);
    }

    private static Path resource(String kind, String id, String extension) {
        assertTrue(id.startsWith("destiny:"));
        return ASSETS.resolve(kind).resolve(id.substring("destiny:".length()) + extension);
    }

    private static Set<String> strings(com.google.gson.JsonArray values) {
        var result = new java.util.HashSet<String>();
        values.forEach(value -> assertTrue(result.add(value.getAsString()), "No duplicate paths/IDs"));
        return result;
    }

    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }

    private static String sha256(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
}
