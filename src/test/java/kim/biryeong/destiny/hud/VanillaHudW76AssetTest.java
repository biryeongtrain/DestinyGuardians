package kim.biryeong.destiny.hud;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/** Resource contract checks only; client rendering still requires in-game verification. */
class VanillaHudW76AssetTest {
    private static final String MANIFEST = "destiny/hud/w76-vanilla.json";
    private static final String HUD = "assets/minecraft/textures/gui/sprites/hud/";
    private static final String LANG = "assets/minecraft/lang/";
    private static final String XP_LEVEL = "gui.experience.level";
    private static final Path RESOURCES = Path.of("src/main/resources");
    // Original Minecraft 26.3 dimensions, independent of the generated manifest.
    private static final Map<String, Size> SPRITES = Map.ofEntries(
            Map.entry("food_empty", new Size(9, 9)),
            Map.entry("food_half", new Size(9, 9)),
            Map.entry("food_full", new Size(9, 9)),
            Map.entry("food_empty_hunger", new Size(9, 9)),
            Map.entry("food_half_hunger", new Size(9, 9)),
            Map.entry("food_full_hunger", new Size(9, 9)),
            Map.entry("hotbar", new Size(182, 22)),
            Map.entry("hotbar_selection", new Size(24, 23)),
            Map.entry("hotbar_offhand_left", new Size(29, 24)),
            Map.entry("hotbar_offhand_right", new Size(29, 24)),
            Map.entry("hotbar_attack_indicator_background", new Size(18, 18)),
            Map.entry("hotbar_attack_indicator_progress", new Size(18, 18)),
            Map.entry("experience_bar_background", new Size(182, 5)),
            Map.entry("experience_bar_progress", new Size(182, 5)));
    private static final Set<String> CROSSHAIRS = Set.of("crosshair",
            "crosshair_attack_indicator_background", "crosshair_attack_indicator_full",
            "crosshair_attack_indicator_progress");

    @Test
    void manifestPinsSchemaStageMinecraftAndStableCounts() throws IOException {
        var manifest = json(MANIFEST);
        assertEquals(JsonParser.parseString("1"), manifest.get("schema"));
        assertEquals(JsonParser.parseString("\"W76\""), manifest.get("stage"));
        assertEquals(JsonParser.parseString("\"26.3\""), manifest.get("minecraft"));
        assertEquals(14, manifest.getAsJsonArray("sprites").size());
        assertEquals(143, manifest.getAsJsonArray("locales").size());
        assertEquals(JsonParser.parseString("[\"gui.experience.level\"]"),
                manifest.get("hiddenTranslationKeys"), "Only the dedicated XP level key is hidden");
    }

    @Test
    void spriteManifestContainsExactlyTheFourteenAllowedPathsWithoutDuplicates() throws IOException {
        var paths = new HashSet<String>();
        for (var entry : json(MANIFEST).getAsJsonArray("sprites")) {
            String path = entry.getAsJsonObject().get("path").getAsString();
            assertTrue(paths.add(path), "Duplicate sprite: " + path);
        }
        assertEquals(spritePaths(), paths,
                "W76 is limited to food, hotbar chrome/attack indicators, and XP bars");
    }

    @Test
    void vanillaOverridesRetainExistingHeartsAndCrosshairsWithoutExpandingHudScope() throws IOException {
        var allowed = new HashSet<>(spritePaths());
        var hearts = JsonParser.parseString(resource("assets/destiny/hud_heart_sprites.json")).getAsJsonArray();
        assertEquals(44, hearts.size(), "Existing player-heart suppression remains listed");
        for (var entry : hearts) {
            String path = entry.getAsJsonObject().get("path").getAsString();
            assertTrue(path.startsWith(HUD + "heart/"), path);
            assertFalse(path.contains("vehicle_"), "Mount hearts must stay outside the overrides");
            assertTrue(allowed.add(path), "Duplicate existing heart: " + path);
            var image = image(path);
            assertEquals(9, image.getWidth(), path);
            assertEquals(9, image.getHeight(), path);
            assertTransparent(image, path);
        }
        for (String name : CROSSHAIRS) {
            String path = HUD + name + ".png";
            allowed.add(path);
            assertTransparent(image(path), path);
        }
        try (var files = Files.walk(RESOURCES.resolve(HUD))) {
            var actual = files.filter(Files::isRegularFile)
                    .filter(path -> path.toString().endsWith(".png"))
                    .map(path -> RESOURCES.relativize(path).toString().replace('\\', '/'))
                    .collect(Collectors.toSet());
            assertEquals(allowed, actual,
                    "No additional vanilla HUD overrides, including armor, air, vehicle, or locator sprites");
        }
    }

    @Test
    void allW76SpritesAreTransparentRgbaPngsAtOriginalDimensions() throws IOException {
        for (var entry : json(MANIFEST).getAsJsonArray("sprites")) {
            var sprite = entry.getAsJsonObject();
            String path = sprite.get("path").getAsString();
            var expected = SPRITES.entrySet().stream()
                    .filter(candidate -> path.equals(HUD + candidate.getKey() + ".png"))
                    .map(Map.Entry::getValue).findFirst().orElseThrow(() -> new AssertionError(path));
            assertEquals(expected.width(), sprite.get("width").getAsInt(), path);
            assertEquals(expected.height(), sprite.get("height").getAsInt(), path);
            byte[] bytes = bytes(path);
            assertTrue(bytes.length >= 33, "PNG header missing: " + path);
            assertArrayEquals(new byte[]{(byte) 137, 80, 78, 71, 13, 10, 26, 10},
                    Arrays.copyOf(bytes, 8), path);
            assertEquals(8, Byte.toUnsignedInt(bytes[24]), "Expected 8-bit channels: " + path);
            assertEquals(6, Byte.toUnsignedInt(bytes[25]), "Expected PNG RGBA color type: " + path);
            var image = image(path);
            assertEquals(expected.width(), image.getWidth(), path);
            assertEquals(expected.height(), image.getHeight(), path);
            assertTrue(image.getColorModel().hasAlpha(), path);
            assertEquals(3, image.getColorModel().getNumColorComponents(), path);
            assertTransparent(image, path);
        }
    }

    @Test
    void manifestEnumerates143UniqueSafeLocalesAndExactlyTheirLanguageFiles() throws IOException {
        Set<String> expected = locales();
        assertEquals(143, expected.size());
        assertTrue(expected.containsAll(Set.of("en_us", "ko_kr")));
        try (var files = Files.list(RESOURCES.resolve(LANG))) {
            var actual = files.filter(Files::isRegularFile)
                    .map(path -> path.getFileName().toString()).collect(Collectors.toSet());
            assertEquals(expected.stream().map(locale -> locale + ".json").collect(Collectors.toSet()), actual,
                    "Language files must match the manifest-derived locale set exactly");
        }
    }

    @Test
    void everyLocaleContainsOnlyReviewedXpAndInventoryTitleOverrides() throws IOException {
        for (String locale : locales()) {
            String path = LANG + locale + ".json";
            // Streaming also rejects repeated keys, which a JsonObject would silently collapse.
            try (var reader = new JsonReader(new StringReader(resource(path)))) {
                reader.beginObject();
                // The launch loading screen replaces the stock "Loading terrain..." interstitial in the two shipped languages.
                var expected = locale.equals("ko_kr") ? Map.of(XP_LEVEL, "", "container.inventory", "", "multiplayer.downloadingTerrain", "게임을 불러오는 중...")
                        : locale.equals("en_us") ? Map.of(XP_LEVEL, "", "container.inventory", "", "multiplayer.downloadingTerrain", "Loading...")
                        : Map.of(XP_LEVEL, "", "container.inventory", "");
                var seen = new HashSet<String>();
                while (reader.hasNext()) {
                    String key = reader.nextName();
                    assertTrue(seen.add(key), "Duplicate translation: " + path + "/" + key);
                    assertTrue(expected.containsKey(key), "No generic number, item-count or unreviewed key: " + path + "/" + key);
                    assertEquals(JsonToken.STRING, reader.peek(), path);
                    assertEquals(expected.get(key), reader.nextString(), path);
                }
                assertEquals(expected.keySet(), seen, path);
                reader.endObject();
                assertEquals(JsonToken.END_DOCUMENT, reader.peek(), path);
            }
        }
    }

    @Test
    void dedicatedHudImageryStillRoutesFromItemsThroughModelsToVisibleTextures() throws IOException {
        var names = new HashSet<>(Set.of("solid", "tile", "diamond", "flash", "flame", "vortex",
                "fist", "knife", "smoke", "dodge", "staff", "gun", "bow", "ammo_panel",
                "ammo_stowed_panel", "ammo_infinity", "ammo_meter_w42", "reticle_w44_dot"));
        for (int digit = 0; digit < 10; digit++) names.add("ammo_digit_" + digit);
        for (String name : names) {
            String id = "destiny:gui/hud/" + name;
            var item = json("assets/destiny/items/gui/hud/" + name + ".json").getAsJsonObject("model");
            assertEquals("minecraft:model", item.get("type").getAsString(), name);
            assertEquals(id, item.get("model").getAsString(), name);
            assertEquals("minecraft:custom_model_data", item.getAsJsonArray("tints").get(0)
                    .getAsJsonObject().get("type").getAsString(), name);
            var model = json("assets/destiny/models/gui/hud/" + name + ".json");
            assertFalse(model.getAsJsonArray("elements").isEmpty(), name);
            String textureId = "destiny:item/hud/" + name;
            var textures = model.getAsJsonObject("textures");
            assertTrue(textures.entrySet().stream().anyMatch(e -> textureId.equals(e.getValue().getAsString())), name);
            boolean routedFace = false;
            for (var element : model.getAsJsonArray("elements")) {
                for (var face : element.getAsJsonObject().getAsJsonObject("faces").entrySet()) {
                    String reference = face.getValue().getAsJsonObject().get("texture").getAsString();
                    assertTrue(reference.startsWith("#"), name);
                    var target = textures.get(reference.substring(1));
                    assertNotNull(target, "Unresolved texture reference: " + name + " " + reference);
                    routedFace |= textureId.equals(target.getAsString());
                }
            }
            assertTrue(routedFace, "Model must use its HUD texture: " + name);
            var image = image("assets/destiny/textures/item/hud/" + name + ".png");
            boolean hasVisiblePixel = false;
            for (int y = 0; y < image.getHeight() && !hasVisiblePixel; y++)
                for (int x = 0; x < image.getWidth() && !hasVisiblePixel; x++)
                    hasVisiblePixel = (image.getRGB(x, y) >>> 24) != 0;
            assertTrue(hasVisiblePixel, "Dedicated HUD imagery must not be blanked: " + name);
        }
    }

    @Test
    void residualLimitationsAreExplicitAndNonempty() throws IOException {
        var residuals = json(MANIFEST).getAsJsonArray("residuals");
        assertNotNull(residuals, "Resource suppression limitations must be documented");
        assertFalse(residuals.isEmpty(), "Resource checks cannot establish complete client HUD suppression");
        for (var residual : residuals)
            assertTrue(hasNonblankText(residual), "Each residual needs an explicit description: " + residual);
    }

    private Set<String> locales() throws IOException {
        var locales = new HashSet<String>();
        for (var value : json(MANIFEST).getAsJsonArray("locales")) {
            assertTrue(value.isJsonPrimitive() && value.getAsJsonPrimitive().isString(), "Locale must be a string");
            String locale = value.getAsString();
            assertTrue(locale.matches("[a-z0-9]+(?:_[a-z0-9]+)*"), "Unsafe locale: " + locale);
            assertTrue(locales.add(locale), "Duplicate locale: " + locale);
        }
        return locales;
    }

    private Set<String> spritePaths() {
        return SPRITES.keySet().stream().map(name -> HUD + name + ".png").collect(Collectors.toSet());
    }

    private void assertTransparent(BufferedImage image, String path) {
        for (int y = 0; y < image.getHeight(); y++)
            for (int x = 0; x < image.getWidth(); x++)
                assertEquals(0, image.getRGB(x, y) >>> 24, path + " alpha at " + x + "," + y);
    }

    private boolean hasNonblankText(JsonElement value) {
        if (value.isJsonPrimitive())
            return value.getAsJsonPrimitive().isString() && !value.getAsString().isBlank();
        if (value.isJsonObject())
            return value.getAsJsonObject().entrySet().stream().anyMatch(entry -> hasNonblankText(entry.getValue()));
        if (value.isJsonArray()) {
            for (var entry : value.getAsJsonArray()) if (hasNonblankText(entry)) return true;
        }
        return false;
    }

    private byte[] bytes(String path) throws IOException {
        try (var stream = getClass().getClassLoader().getResourceAsStream(path)) {
            assertNotNull(stream, "Missing pack resource " + path);
            return stream.readAllBytes();
        }
    }

    private String resource(String path) throws IOException {
        return new String(bytes(path), StandardCharsets.UTF_8);
    }

    private JsonObject json(String path) throws IOException {
        return JsonParser.parseString(resource(path)).getAsJsonObject();
    }

    private BufferedImage image(String path) throws IOException {
        try (var stream = getClass().getClassLoader().getResourceAsStream(path)) {
            assertNotNull(stream, "Missing pack resource " + path);
            var image = ImageIO.read(stream);
            assertNotNull(image, "Unreadable PNG " + path);
            return image;
        }
    }

    private record Size(int width, int height) {}
}
