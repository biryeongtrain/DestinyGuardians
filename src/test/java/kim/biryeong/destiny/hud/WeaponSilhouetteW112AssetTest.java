package kim.biryeong.destiny.hud;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashMap;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Plain JVM asset contract only; no Minecraft codecs, game runtime, or native HUD claim. */
class WeaponSilhouetteW112AssetTest {
    private static final String ASSET = "src/main/resources/assets/destiny/";
    private static final String HUD = "art/weapons/w112/hud/";
    private static final String PREFIX = "ammo_weapon_w112_";

    private static JsonObject object(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }

    private static JsonObject manifest() throws Exception {
        return object(HUD + "manifest.json");
    }

    private static String hash(byte[] data) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data));
    }

    private static Map<String, JsonObject> catalog() throws Exception {
        Map<String, JsonObject> rows = new HashMap<>();
        for (String file : new String[]{"w30.json", "w83-exotics.json", "w84-exotics.json"}) {
            JsonArray entries = JsonParser.parseString(Files.readString(
                    Path.of("src/main/resources/destiny/weapons/" + file))).getAsJsonArray();
            assertEquals(file.equals("w30.json") ? 63 : 1, entries.size());
            for (JsonElement entry : entries) {
                JsonObject row = entry.getAsJsonObject();
                if (!file.equals("w30.json")) row = row.getAsJsonObject("catalog");
                assertNull(rows.put(row.get("id").getAsString(), row), "Duplicate catalog ID");
            }
        }
        assertEquals(65, rows.size());
        assertTrue(rows.containsKey("ace_of_spades"));
        assertTrue(rows.containsKey("izanagis_burden"));
        return rows;
    }

    @Test void exact65CatalogIdsAnd195PackFilesWithoutVariants() throws Exception {
        JsonObject manifest = manifest();
        assertEquals(65, manifest.get("count").getAsInt());
        assertEquals(65, manifest.getAsJsonArray("weapons").size());
        Set<String> ids = new HashSet<>(), paths = new HashSet<>();
        for (JsonElement entry : manifest.getAsJsonArray("weapons")) {
            JsonObject weapon = entry.getAsJsonObject();
            String id = weapon.get("id").getAsString();
            assertTrue(ids.add(id));
            assertEquals(3, weapon.getAsJsonObject("pack_files").size());
            for (String path : weapon.getAsJsonObject("pack_files").keySet()) assertTrue(paths.add(path));
            assertTrue(paths.contains(ASSET + "items/gui/hud/" + PREFIX + id + ".json"));
            assertTrue(paths.contains(ASSET + "models/gui/hud/" + PREFIX + id + ".json"));
            assertTrue(paths.contains(ASSET + "textures/item/hud/" + PREFIX + id + ".png"));
        }
        assertEquals(catalog().keySet(), ids);
        assertEquals(195, paths.size());
        Set<String> actual = new HashSet<>();
        for (String directory : new String[]{"items/gui/hud", "models/gui/hud", "textures/item/hud"}) {
            try (var files = Files.list(Path.of(ASSET + directory))) {
                files.filter(p -> p.getFileName().toString().startsWith(PREFIX)).forEach(p -> actual.add(p.toString()));
            }
        }
        assertEquals(paths, actual, "No aimed/reload/twohand or other W112 variants");
    }

    @Test void historicalSourceInputsAndCurrentTransportRetainAllOutputBytes() throws Exception {
        JsonObject manifest = manifest();
        for (var entry : manifest.getAsJsonObject("inputs_sha256").entrySet()) {
            var input = entry.getKey().equals("src/main/resources/weapon_surface_w123/manifest.json")
                    ? kim.biryeong.destiny.testfixtures.PreW251Assets.path(entry.getKey()) : Path.of(entry.getKey());
            assertEquals(entry.getValue().getAsString(), hash(Files.readAllBytes(input)), entry.getKey());
        }
        assertEquals(7, manifest.getAsJsonObject("inputs_sha256").size());
        Map<String, JsonObject> catalog = catalog();
        JsonObject migration = JsonParser.parseString(Files.readString(kim.biryeong.destiny.testfixtures.PreW251Assets.path("src/main/resources/weapon_surface_w123/manifest.json"))).getAsJsonObject();
        var liveMigration = object("src/main/resources/weapon_surface_w123/manifest.json");
        for (var field : migration.entrySet()) if (!field.getKey().equals("targets"))
            assertEquals(field.getValue(), liveMigration.get(field.getKey()), field.getKey());
        assertEquals(migration.getAsJsonArray("targets").size(), liveMigration.getAsJsonArray("targets").size());
        for (int i = 0; i < migration.getAsJsonArray("targets").size(); i++) {
            var historicalRule = migration.getAsJsonArray("targets").get(i).getAsJsonObject().deepCopy();
            var liveRule = liveMigration.getAsJsonArray("targets").get(i).getAsJsonObject().deepCopy();
            historicalRule.remove("replacementSha256"); liveRule.remove("replacementSha256");
            assertEquals(historicalRule, liveRule, "Only later replacement geometry may have a new digest");
        }
        Map<String, JsonObject> replacements = new HashMap<>();
        for (JsonElement target : migration.getAsJsonArray("targets")) {
            JsonObject rule = target.getAsJsonObject();
            assertNull(replacements.put("src/main/resources/" + rule.get("path").getAsString(), rule));
        }
        int replaced = 0;
        for (JsonElement entry : manifest.getAsJsonArray("weapons")) {
            JsonObject weapon = entry.getAsJsonObject();
            String id = weapon.get("id").getAsString(), family = weapon.get("family").getAsString();
            assertEquals(catalog.get(id).get("family").getAsString(), family);
            String source = ASSET + "models/" + (id.equals("ace_of_spades") || id.equals("izanagis_burden")
                    ? "item/weapon/" : "weapon/" + family + "/") + id + ".json";
            assertEquals(source, weapon.get("canonical_model").getAsString());
            JsonObject rule = replacements.get(source);
            if (rule != null) {
                assertEquals(rule.get("sourceSha256").getAsString(), hash(Files.readAllBytes(Path.of(source))), id);
                source = "src/main/resources/" + rule.get("replacement").getAsString();
                assertEquals(rule.get("replacementSha256"), weapon.get("source_sha256"), id);
                assertEquals("default W123 pack migration", weapon.get("source_profile").getAsString());
                replaced++;
            } else assertEquals("canonical unchanged", weapon.get("source_profile").getAsString());
            assertEquals(source, weapon.get("source_model").getAsString());
            assertEquals(weapon.get("source_sha256").getAsString(), hash(Files.readAllBytes(Set.of("austringer", "mindbender_s_ambition_adept", "blast_furnace", "hammerhead", "the_recluse").contains(id)
                    ? kim.biryeong.destiny.testfixtures.PreW251Assets.path(source) : Path.of(source))), id);
            JsonArray cubes = JsonParser.parseString(Files.readString(Set.of("austringer", "mindbender_s_ambition_adept", "blast_furnace", "hammerhead", "the_recluse").contains(id)
                    ? kim.biryeong.destiny.testfixtures.PreW251Assets.path(source) : Path.of(source))).getAsJsonObject().getAsJsonArray("elements");
            assertEquals(cubes.size(), weapon.get("elements").getAsInt());
            int faces = 0, rotations = 0;
            for (JsonElement cube : cubes) {
                faces += cube.getAsJsonObject().getAsJsonObject("faces").size();
                if (cube.getAsJsonObject().has("rotation")) rotations++;
            }
            assertEquals(faces, weapon.get("source_faces").getAsInt(), id);
            assertEquals(rotations, weapon.get("rotated_elements").getAsInt(), id);
            if (id.equals("ace_of_spades")) assertEquals(41, rotations);
            if (id.equals("izanagis_burden")) assertEquals(30, rotations);

            for (var file : weapon.getAsJsonObject("pack_files").entrySet())
                assertEquals(file.getValue().getAsString(), hash(Files.readAllBytes(Path.of(file.getKey()))), file.getKey());
        }
        long fullTargets = replacements.keySet().stream().filter(path -> path.contains("/models/weapon/")).count();
        assertEquals(fullTargets, replaced, "Every active full weapon drives HUD; split reload parts do not");
        assertTrue(replaced > 0);
        assertEquals(manifest.get("contact_sheet_sha256").getAsString(),
                hash(Files.readAllBytes(Path.of(HUD + "contact-sheet.png"))));
    }

    @Test void itemAtlasAndTintIndexZeroPreserveOriginalHudTransport() throws Exception {
        JsonObject originalItem = object(ASSET + "items/gui/hud/ammo_hand_cannon.json");
        JsonObject originalModel = object(ASSET + "models/gui/hud/ammo_hand_cannon.json");
        for (String id : catalog().keySet()) {
            String name = PREFIX + id;
            JsonObject expectedItem = originalItem.deepCopy(), expectedModel = originalModel.deepCopy();
            expectedItem.getAsJsonObject("model").addProperty("model", "destiny:gui/hud/" + name);
            expectedModel.getAsJsonObject("textures").addProperty("layer0", "destiny:item/hud/" + name);
            expectedModel.getAsJsonObject("textures").addProperty("particle", "#layer0");
            JsonObject item = object(ASSET + "items/gui/hud/" + name + ".json");
            JsonObject model = object(ASSET + "models/gui/hud/" + name + ".json");
            assertEquals(expectedItem, item, id);
            assertEquals(expectedModel, model, id);
            JsonObject tint = item.getAsJsonObject("model").getAsJsonArray("tints").get(0).getAsJsonObject();
            assertEquals("minecraft:custom_model_data", tint.get("type").getAsString());
            assertEquals(0, tint.get("index").getAsInt());
            assertEquals(0xffffff, tint.get("default").getAsInt());
            for (JsonElement element : model.getAsJsonArray("elements"))
                for (var face : element.getAsJsonObject().getAsJsonObject("faces").entrySet())
                    assertEquals(0, face.getValue().getAsJsonObject().get("tintindex").getAsInt());
            assertTrue(Files.isRegularFile(Path.of(ASSET + "textures/item/hud/" + name + ".png")));
        }
    }

    @Test void individualMasksAreWhiteRgbaNonemptyPaddedAndDistinctWithinFamilies() throws Exception {
        Map<String, Set<String>> familyMasks = new HashMap<>();
        for (JsonElement entry : manifest().getAsJsonArray("weapons")) {
            JsonObject weapon = entry.getAsJsonObject();
            String id = weapon.get("id").getAsString();
            var image = ImageIO.read(Path.of(ASSET + "textures/item/hud/" + PREFIX + id + ".png").toFile());
            assertEquals(160, image.getWidth());
            assertEquals(64, image.getHeight());
            assertTrue(image.getColorModel().hasAlpha());
            assertEquals(4, image.getColorModel().getNumComponents());
            byte[] alpha = new byte[160 * 64];
            int visible = 0, antialias = 0, opaque = 0, left = 160, top = 64, right = 0, bottom = 0;
            for (int y = 0; y < 64; y++) for (int x = 0; x < 160; x++) {
                int pixel = image.getRGB(x, y), a = pixel >>> 24;
                assertEquals(0xffffff, pixel & 0xffffff, id + " neutral RGB including transparent pixels");
                alpha[y * 160 + x] = (byte) a;
                if (x < 4 || x >= 156 || y < 4 || y >= 60) assertEquals(0, a, id + " clear padding");
                if (a > 0) {
                    visible++;
                    left = Math.min(left, x); top = Math.min(top, y);
                    right = Math.max(right, x + 1); bottom = Math.max(bottom, y + 1);
                    if (a < 255) antialias++; else opaque++;
                }
            }
            assertTrue(visible > 100 && visible < 152 * 56, id + " bounded silhouette occupancy");
            assertTrue(visible < (right - left) * (bottom - top) - 20, id + " shape is not a filled rectangle");
            assertTrue(opaque > 50 && antialias > 20, id + " opaque core and antialiased edge");
            assertEquals(weapon.get("visible_pixels").getAsInt(), visible, id);
            assertEquals(weapon.getAsJsonArray("alpha_bbox").toString(),
                    "[" + left + "," + top + "," + right + "," + bottom + "]", id);
            String maskHash = hash(alpha);
            assertEquals(weapon.get("alpha_sha256").getAsString(), maskHash, id);
            assertTrue(familyMasks.computeIfAbsent(weapon.get("family").getAsString(), ignored -> new HashSet<>())
                    .add(maskHash), id + " cannot duplicate another same-family icon");
        }
    }

    @Test void projectedExtentsKeepAspectAndOnlyMeleeFamiliesRotate() throws Exception {
        JsonObject manifest = manifest();
        assertEquals("[160,64]", manifest.getAsJsonArray("texture_size").toString());
        assertEquals("[80,32]", manifest.getAsJsonArray("selected_quad_size").toString());
        assertEquals(8, manifest.get("supersampling").getAsInt());
        for (JsonElement entry : manifest.getAsJsonArray("weapons")) {
            JsonObject weapon = entry.getAsJsonObject(), orientation = weapon.getAsJsonObject("orientation");
            boolean melee = Set.of("sword", "glaive").contains(weapon.get("family").getAsString());
            assertEquals("YZ", orientation.get("plane").getAsString());
            assertEquals(melee ? "+Y" : "+Z", orientation.get("screen_x").getAsString());
            assertEquals(melee ? "+Z" : "-Y", orientation.get("screen_y").getAsString());
            assertEquals(melee ? 90 : 0, orientation.get("side_rotation_degrees").getAsInt());
            assertEquals(manifest.get("method"), weapon.get("method"));
            JsonArray bounds = weapon.getAsJsonArray("projected_bounds"), bbox = weapon.getAsJsonArray("alpha_bbox");
            double width = bounds.get(2).getAsDouble() - bounds.get(0).getAsDouble();
            double height = bounds.get(3).getAsDouble() - bounds.get(1).getAsDouble();
            double scale = weapon.get("pixels_per_model_unit").getAsDouble();
            assertEquals(Math.min(151 / width, 55 / height), scale, 1e-7);
            assertEquals(width * scale, bbox.get(2).getAsInt() - bbox.get(0).getAsInt(), 2.1);
            assertEquals(height * scale, bbox.get(3).getAsInt() - bbox.get(1).getAsInt(), 2.1);
            assertTrue(weapon.get("projected_faces").getAsInt() >= weapon.get("elements").getAsInt());
        }
    }
}
