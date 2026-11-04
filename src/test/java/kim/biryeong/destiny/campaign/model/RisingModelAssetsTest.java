package kim.biryeong.destiny.campaign.model;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.campaign.RisingServices;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class RisingModelAssetsTest {
    /** name -> {min elements, max elements, max texture size, required clips} */
    private record Budget(int min, int max, int tex, List<String> clips) { }

    private static final Map<String, Budget> BUDGETS = Map.of(
            // W300 r6: Dreg-Light handoff (source-mesh surface quads, 2048 atlas, 13 retargeted D2 clips + aliases).
            RisingServices.Models.DREG, new Budget(1500, 2200, 2048, RisingServices.Models.INFANTRY_CLIPS),
            // W300 r7: Vandal/Captain/Shank/Walker baked with the same technique (scripts/campaign/bake_dreglight.py).
            RisingServices.Models.VANDAL, new Budget(1500, 2200, 2048, RisingServices.Models.INFANTRY_CLIPS),
            RisingServices.Models.CAPTAIN, new Budget(1500, 2200, 2048, RisingServices.Models.INFANTRY_CLIPS),
            RisingServices.Models.SHANK, new Budget(800, 1500, 2048, RisingServices.Models.SHANK_CLIPS),
            RisingServices.Models.WALKER, new Budget(2000, 3000, 2048, RisingServices.Models.WALKER_CLIPS),
            RisingServices.Models.SKIFF, new Budget(40, 300, 1024, RisingServices.Models.SKIFF_CLIPS),
            RisingServices.Models.GHOST, new Budget(20, 300, 256, RisingServices.Models.GHOST_CLIPS),
            RisingServices.Models.SHIP, new Budget(40, 400, 512, RisingServices.Models.SHIP_CLIPS));
    private static final Set<String> LOOPING = Set.of("idle", "walk", "run", "fly", "scan", "speak");

    private static JsonObject load(String name) throws IOException {
        return JsonParser.parseString(new String(RisingModelAssets.bundled(name), StandardCharsets.UTF_8)).getAsJsonObject();
    }

    @Test
    void everyContractModelIsBundledWithBudget() throws IOException {
        assertEquals(Set.copyOf(BUDGETS.keySet()), Set.copyOf(RisingModelAssets.MODELS));
        for (String name : RisingModelAssets.MODELS) {
            JsonObject model = load(name);
            Budget budget = BUDGETS.get(name);
            int elements = model.getAsJsonArray("elements").size();
            assertTrue(elements >= budget.min() && elements <= budget.max(), name + " element count " + elements);
            assertEquals("free", model.getAsJsonObject("meta").get("model_format").getAsString(), name);
            JsonArray textures = model.getAsJsonArray("textures");
            assertEquals(1, textures.size(), name);
            JsonObject tex = textures.get(0).getAsJsonObject();
            int[] size = pngSize(tex.get("source").getAsString());
            assertEquals(tex.get("width").getAsInt(), size[0], name);
            assertEquals(tex.get("height").getAsInt(), size[1], name);
            assertTrue(size[0] <= budget.tex() && size[1] <= budget.tex(), name + " texture " + size[0]);
            JsonObject res = model.getAsJsonObject("resolution");
            assertEquals(size[0], res.get("width").getAsInt(), name);
        }
    }

    @Test
    void clipsMatchContractAndLoopModes() throws IOException {
        for (String name : RisingModelAssets.MODELS) {
            JsonObject model = load(name);
            Map<String, String> loops = new HashMap<>();
            for (JsonElement a : model.getAsJsonArray("animations")) {
                JsonObject clip = a.getAsJsonObject();
                assertNull(loops.put(clip.get("name").getAsString(), clip.get("loop").getAsString()), name + " duplicate clip");
                assertTrue(clip.get("length").getAsDouble() > 0, name);
                assertFalse(clip.getAsJsonObject("animators").isEmpty(), name + "/" + clip.get("name"));
            }
            for (String required : BUDGETS.get(name).clips()) {
                assertTrue(loops.containsKey(required), name + " missing clip " + required);
                String loop = loops.get(required);
                if (LOOPING.contains(required)) assertEquals("loop", loop, name + "/" + required);
                else assertTrue(loop.equals("once") || loop.equals("hold"), name + "/" + required + " " + loop);
            }
            // r4: the Shank arrival plays through FallenModels SPAWN (spawn/arrive fallback).
            if (name.equals(RisingServices.Models.SHANK)) assertTrue(loops.containsKey("spawn"), "shank spawn clip");
        }
    }

    @Test
    void structureIsConsistent() throws IOException {
        for (String name : RisingModelAssets.MODELS) {
            JsonObject model = load(name);
            int w = model.getAsJsonObject("resolution").get("width").getAsInt();
            Set<String> elementIds = new HashSet<>();
            for (JsonElement e : model.getAsJsonArray("elements")) {
                JsonObject el = e.getAsJsonObject();
                assertTrue(elementIds.add(el.get("uuid").getAsString()), name);
                JsonArray from = el.getAsJsonArray("from"), to = el.getAsJsonArray("to");
                int flat = 0;
                for (int i = 0; i < 3; i++) {
                    double lo = from.get(i).getAsDouble(), hi = to.get(i).getAsDouble();
                    assertTrue(Double.isFinite(lo) && Double.isFinite(hi) && hi >= lo, name + " inverted element");
                    if (hi == lo) flat++;
                    assertTrue(Double.isFinite(el.getAsJsonArray("rotation").get(i).getAsDouble()), name);
                }
                assertTrue(flat <= 1, name + " degenerate element"); // zero-thickness quads (one flat axis) are allowed
                for (var face : el.getAsJsonObject("faces").entrySet()) {
                    JsonObject f = face.getValue().getAsJsonObject();
                    if (f.get("texture").isJsonNull()) continue;
                    for (JsonElement uv : f.getAsJsonArray("uv")) {
                        double v = uv.getAsDouble();
                        assertTrue(v >= 0 && v <= w, name + " uv out of atlas " + v);
                    }
                }
            }
            Map<String, String> groupNames = groupsOf(model);
            Set<String> seen = new HashSet<>();
            for (JsonElement root : model.getAsJsonArray("outliner")) walk(root, groupNames, seen, name);
            assertEquals(elementIds, seen, name + " every element exactly once in the outliner");
            for (JsonElement a : model.getAsJsonArray("animations")) {
                for (var animator : a.getAsJsonObject().getAsJsonObject("animators").entrySet()) {
                    assertTrue(groupNames.containsKey(animator.getKey()), name + " animator for unknown bone");
                    assertEquals(groupNames.get(animator.getKey()), animator.getValue().getAsJsonObject().get("name").getAsString());
                }
            }
        }
    }

    private static void walk(JsonElement node, Map<String, String> groups, Set<String> seen, String name) {
        if (node.isJsonPrimitive()) {
            assertTrue(seen.add(node.getAsString()), name + " element listed twice");
            return;
        }
        JsonObject group = node.getAsJsonObject();
        assertTrue(groups.containsKey(group.get("uuid").getAsString()), name + " outliner group missing");
        for (JsonElement child : group.getAsJsonArray("children")) walk(child, groups, seen, name);
    }

    @Test
    void walkerAndGhostExposeContractBones() throws IOException {
        Set<String> walker = boneNames(load(RisingServices.Models.WALKER));
        for (String bone : List.of("leg_fl", "leg_fr", "leg_bl", "leg_br", "weakpoint")) assertTrue(walker.contains(bone), bone);
        Set<String> ghost = boneNames(load(RisingServices.Models.GHOST));
        for (String bone : List.of("eye", "core", "shell", "shell_a_top", "shell_b_bottom")) assertTrue(ghost.contains(bone), bone);
        // W300 r6: the Dreg handoff rig names its four arms arm_*/lower_arm_* and carries the pistol in hand_r.
        // W300 r7: Vandal/Captain share that 19-bone rig (same D2 skeleton) plus a weapon bone under hand_r.
        for (String fallen : List.of(RisingServices.Models.DREG, RisingServices.Models.VANDAL, RisingServices.Models.CAPTAIN)) {
            Set<String> bones = boneNames(load(fallen));
            for (String bone : List.of("arm_l", "arm_r", "lower_arm_l", "lower_arm_r", "hand_r", "head")) assertTrue(bones.contains(bone), fallen + " " + bone);
            if (!fallen.equals(RisingServices.Models.DREG)) assertTrue(bones.contains("weapon"), fallen);
        }
        assertTrue(boneNames(load(RisingServices.Models.CAPTAIN)).contains("blade"), "captain blade");
        Set<String> shank = boneNames(load(RisingServices.Models.SHANK));
        for (String bone : List.of("body", "gun", "wing_ul", "wing_ur", "wing_ll", "wing_lr")) assertTrue(shank.contains(bone), "shank " + bone);
    }

    /** r2: emissive accents live in bones suffixed _glow so the runtime can force full brightness per bone. */
    static final Map<String, List<String>> GLOW_BONES = Map.of(
            RisingServices.Models.DREG, List.of("eyes_glow"),
            RisingServices.Models.VANDAL, List.of("eyes_glow", "weapon_glow"),
            RisingServices.Models.CAPTAIN, List.of("eyes_glow", "weapon_glow", "blade_glow", "pack_glow"),
            RisingServices.Models.SHANK, List.of("eye_glow"),
            RisingServices.Models.WALKER, List.of("eye_glow", "weakpoint_glow", "leg_fl_glow", "leg_fr_glow", "leg_bl_glow", "leg_br_glow"),
            RisingServices.Models.SKIFF, List.of("engines_glow"),
            RisingServices.Models.GHOST, List.of("eye_glow"),
            RisingServices.Models.SHIP, List.of("engine_l_glow", "engine_r_glow", "lights_glow"));

    @Test
    void emissivePartsLiveInGlowBones() throws IOException {
        for (String name : RisingModelAssets.MODELS) {
            JsonObject model = load(name);
            Map<String, String> groups = groupsOf(model);
            Map<String, String> owner = new HashMap<>();
            Map<String, Integer> counts = new HashMap<>();
            for (JsonElement root : model.getAsJsonArray("outliner")) owners(root, groups, owner);
            for (JsonElement e : model.getAsJsonArray("elements")) {
                JsonObject el = e.getAsJsonObject();
                String bone = owner.get(el.get("uuid").getAsString());
                boolean glow = el.has("light_emission") && el.get("light_emission").getAsInt() > 0;
                assertEquals(bone.endsWith("_glow"), glow, name + " element in " + bone);
                counts.merge(bone, 1, Integer::sum);
            }
            for (String bone : GLOW_BONES.get(name)) assertTrue(counts.getOrDefault(bone, 0) > 0, name + " " + bone);
            for (String bone : groups.values())
                if (bone.endsWith("_glow")) assertTrue(GLOW_BONES.get(name).contains(bone), name + " undeclared " + bone);
        }
    }

    /** r4b: Rising-era repaints carry at least 2 texels per model pixel (32 px per block) on every textured face.
     *  r7: the baked models hold this too (Walker, the largest, about 2.1 texels per px). */
    private static final Set<String> DENSE = Set.of(RisingServices.Models.DREG, RisingServices.Models.VANDAL, RisingServices.Models.CAPTAIN,
            RisingServices.Models.SHANK, RisingServices.Models.WALKER, RisingServices.Models.SKIFF);

    @Test
    void repaintedModelsHaveThirtyTwoPixelsPerBlock() throws IOException {
        for (String name : DENSE) {
            JsonObject model = load(name);
            double texels = 0, area = 0;
            for (JsonElement e : model.getAsJsonArray("elements")) {
                JsonObject el = e.getAsJsonObject();
                JsonArray from = el.getAsJsonArray("from"), to = el.getAsJsonArray("to");
                double[] s = new double[3];
                for (int i = 0; i < 3; i++) s[i] = to.get(i).getAsDouble() - from.get(i).getAsDouble();
                for (var face : el.getAsJsonObject("faces").entrySet()) {
                    JsonObject f = face.getValue().getAsJsonObject();
                    if (f.get("texture").isJsonNull()) continue;
                    JsonArray uv = f.getAsJsonArray("uv");
                    texels += Math.abs(uv.get(2).getAsDouble() - uv.get(0).getAsDouble()) * Math.abs(uv.get(3).getAsDouble() - uv.get(1).getAsDouble());
                    area += switch (face.getKey()) {
                        case "north", "south" -> s[0] * s[1];
                        case "east", "west" -> s[2] * s[1];
                        default -> s[0] * s[2];
                    };
                }
            }
            assertTrue(texels / area >= 3.6, name + " texels per px^2 " + texels / area);
        }
    }

    /** r4b: Fallen cloth uses alpha cutout (only fully opaque or fully clear pixels, some clear pixels inside used faces). */
    @Test
    void fallenClothIsAlphaCutout() throws IOException {
        for (String name : List.of(RisingServices.Models.DREG, RisingServices.Models.VANDAL, RisingServices.Models.CAPTAIN)) {
            JsonObject model = load(name);
            String uri = model.getAsJsonArray("textures").get(0).getAsJsonObject().get("source").getAsString();
            var img = javax.imageio.ImageIO.read(new java.io.ByteArrayInputStream(
                    Base64.getDecoder().decode(uri.substring("data:image/png;base64,".length()))));
            for (int y = 0; y < img.getHeight(); y++) for (int x = 0; x < img.getWidth(); x++) {
                int a = img.getRGB(x, y) >>> 24;
                assertTrue(a == 0 || a == 255, name + " partial alpha at " + x + "," + y);
            }
            int clearInFaces = 0;
            for (JsonElement e : model.getAsJsonArray("elements"))
                for (var face : e.getAsJsonObject().getAsJsonObject("faces").entrySet()) {
                    JsonObject f = face.getValue().getAsJsonObject();
                    if (f.get("texture").isJsonNull()) continue;
                    JsonArray uv = f.getAsJsonArray("uv");
                    for (int y = (int) uv.get(1).getAsDouble(); y < (int) uv.get(3).getAsDouble(); y++)
                        for (int x = (int) uv.get(0).getAsDouble(); x < (int) uv.get(2).getAsDouble(); x++)
                            if ((img.getRGB(x, y) >>> 24) == 0) clearInFaces++;
                }
            assertTrue(clearInFaces > 200, name + " cutout fringe pixels " + clearInFaces);
        }
    }

    @Test
    void texturesAreReadableMidTones() throws IOException {
        for (String name : RisingModelAssets.MODELS) {
            String uri = load(name).getAsJsonArray("textures").get(0).getAsJsonObject().get("source").getAsString();
            var img = javax.imageio.ImageIO.read(new java.io.ByteArrayInputStream(
                    Base64.getDecoder().decode(uri.substring("data:image/png;base64,".length()))));
            double sum = 0; int n = 0;
            for (int y = 0; y < img.getHeight(); y++) for (int x = 0; x < img.getWidth(); x++) {
                int argb = img.getRGB(x, y);
                if ((argb >>> 24) == 0) continue;
                sum += 0.299 * ((argb >> 16) & 255) + 0.587 * ((argb >> 8) & 255) + 0.114 * (argb & 255); n++;
            }
            double mean = sum / n;
            // r4b: weathered House-of-Devils palette (dirt dither, dark undersuit) sits lower; the runtime light floor keeps it readable.
            assertTrue(mean >= 80 && mean <= 175, name + " mean luma " + mean);
        }
    }

    private static void owners(JsonElement node, Map<String, String> groups, Map<String, String> out) {
        JsonObject group = node.getAsJsonObject();
        String name = groups.get(group.get("uuid").getAsString());
        for (JsonElement child : group.getAsJsonArray("children")) {
            if (child.isJsonPrimitive()) out.put(child.getAsString(), name);
            else owners(child, groups, out);
        }
    }

    /**
     * r3: the authored Walker is laid out on WalkerBoss.LAYOUT (campaign/fallen, anchor-local blocks:
     * x right, y up, z forward; model px = (16x, 16y, -16z)). Copied here because the lane worktree does not
     * own WalkerBoss; if the layout changes, regenerate rg_walker and update these numbers together.
     */
    @Test
    void walkerGeometryMatchesWalkerBossHitRegions() throws IOException {
        JsonObject model = load(RisingServices.Models.WALKER);
        Map<String, String> groups = groupsOf(model), owner = new HashMap<>();   // r7: 4.10 inline outliner (no "groups")
        for (JsonElement root : model.getAsJsonArray("outliner")) owners(root, groups, owner);
        // weakpoint glow core centred on LAYOUT WEAKPOINT (0, 2.75 + 1.1/2, 1.6)
        double[] core = bounds(model, owner, "weakpoint_glow");
        assertEquals(0, (core[0] + core[3]) / 2 / 16, 0.05);
        assertEquals(2.75 + 0.55, (core[1] + core[4]) / 2 / 16, 0.1);
        assertEquals(1.6, -(core[2] + core[5]) / 2 / 16, 0.1);
        assertTrue((core[3] - core[0]) / 16 >= 0.8, "weakpoint glow reads at boss distance");
        // each leg's lowest elements (foot pad) stand on the ground inside its LEG_* box (x +-2.3, z +-2.0)
        for (String leg : List.of("fl", "fr", "bl", "br")) {
            double[] b = bounds(model, owner, "leg_" + leg + "_low");
            assertEquals(0, b[1], 1e-6, leg + " foot on the ground");
            double x = leg.endsWith("l") ? -2.3 : 2.3, z = leg.startsWith("f") ? 2.0 : -2.0;
            double[] foot = footCentre(model, owner, "leg_" + leg + "_low");
            assertEquals(x, foot[0] / 16, 0.4, leg);
            assertEquals(z, -foot[1] / 16, 0.4, leg);
        }
        // hull spans the HULL box height band (3.7 .. 5.8 blocks) and is at least the box width (4 blocks)
        double[] hull = bounds(model, owner, "body");
        assertTrue(hull[1] / 16 <= 3.75 && hull[4] / 16 >= 5.8, "hull height band");
        assertTrue((hull[3] - hull[0]) / 16 >= 4.0, "hull width");
        Set<String> names = boneNames(model);
        for (String b : List.of("head", "eye_glow", "plate_l", "plate_r")) assertTrue(names.contains(b), b);
    }

    /** min/max of unrotated element corners for one bone: {x0, y0, z0, x1, y1, z1}. */
    private static double[] bounds(JsonObject model, Map<String, String> owner, String bone) {
        double[] b = {1e9, 1e9, 1e9, -1e9, -1e9, -1e9};
        for (JsonElement e : model.getAsJsonArray("elements")) {
            JsonObject el = e.getAsJsonObject();
            if (!bone.equals(owner.get(el.get("uuid").getAsString()))) continue;
            for (int i = 0; i < 3; i++) {
                b[i] = Math.min(b[i], el.getAsJsonArray("from").get(i).getAsDouble());
                b[i + 3] = Math.max(b[i + 3], el.getAsJsonArray("to").get(i).getAsDouble());
            }
        }
        assertTrue(b[0] < 1e9, "bone without elements: " + bone);
        return b;
    }

    /** x/z centre of the elements touching the ground (y == 0) of a bone. */
    private static double[] footCentre(JsonObject model, Map<String, String> owner, String bone) {
        double x = 0, z = 0; int n = 0;
        for (JsonElement e : model.getAsJsonArray("elements")) {
            JsonObject el = e.getAsJsonObject();
            if (!bone.equals(owner.get(el.get("uuid").getAsString()))) continue;
            if (Math.abs(el.getAsJsonArray("from").get(1).getAsDouble()) > 1e-6) continue;
            JsonArray f = el.getAsJsonArray("from"), t = el.getAsJsonArray("to");
            if (t.get(0).getAsDouble() - f.get(0).getAsDouble() < 20) continue;   // the foot pad, not toes
            x += (f.get(0).getAsDouble() + t.get(0).getAsDouble()) / 2;
            z += (f.get(2).getAsDouble() + t.get(2).getAsDouble()) / 2; n++;
        }
        assertTrue(n > 0, bone + " has a ground pad");
        return new double[]{x / n, z / n};
    }

    /** uuid -> bone name; Blockbench 5 keeps bones in "groups", 4.x (the Dreg handoff) inlines them in the outliner. */
    private static Map<String, String> groupsOf(JsonObject model) {
        Map<String, String> out = new HashMap<>();
        if (model.has("groups"))
            for (JsonElement g : model.getAsJsonArray("groups"))
                out.put(g.getAsJsonObject().get("uuid").getAsString(), g.getAsJsonObject().get("name").getAsString());
        for (JsonElement root : model.getAsJsonArray("outliner")) inlineGroups(root, out);
        return out;
    }

    private static void inlineGroups(JsonElement node, Map<String, String> out) {
        if (!node.isJsonObject()) return;
        JsonObject g = node.getAsJsonObject();
        if (g.has("name")) out.putIfAbsent(g.get("uuid").getAsString(), g.get("name").getAsString());
        for (JsonElement c : g.getAsJsonArray("children")) inlineGroups(c, out);
    }

    private static Set<String> boneNames(JsonObject model) {
        if (!model.has("groups")) return new HashSet<>(groupsOf(model).values());
        Set<String> out = new HashSet<>();
        for (JsonElement g : model.getAsJsonArray("groups")) out.add(g.getAsJsonObject().get("name").getAsString());
        return out;
    }

    // BetterModel's ModelData.loadBlueprint needs the running platform (BoneItemMapper bootstrap), so the
    // strict BetterModel load is verified in-game by master; these tests pin the Blockbench JSON contract.

    @Test
    void installWritesUpdatesAndPreservesForeignCopies(@TempDir Path dir) throws IOException {
        Path models = dir.resolve("bettermodel/models"), markers = dir.resolve("markers");
        String name = RisingServices.Models.DREG;
        byte[] v1 = "{\"v\":1}".getBytes(StandardCharsets.UTF_8), v2 = "{\"v\":2}".getBytes(StandardCharsets.UTF_8);
        Files.createDirectories(models);
        Files.writeString(models.resolve("unrelated.bbmodel"), "keep");
        assertEquals(RisingModelAssets.Outcome.INSTALLED, RisingModelAssets.install(models, markers, name, v1));
        assertEquals(RisingModelAssets.Outcome.CURRENT, RisingModelAssets.install(models, markers, name, v1));
        assertEquals(RisingModelAssets.Outcome.UPDATED, RisingModelAssets.install(models, markers, name, v2));
        assertArrayEquals(v2, Files.readAllBytes(models.resolve(name + ".bbmodel")));
        Files.writeString(models.resolve(name + ".bbmodel"), "{\"edited\":true}");
        assertEquals(RisingModelAssets.Outcome.KEPT_USER_COPY, RisingModelAssets.install(models, markers, name, v1));
        assertEquals("{\"edited\":true}", Files.readString(models.resolve(name + ".bbmodel")));
        assertEquals("keep", Files.readString(models.resolve("unrelated.bbmodel")));
        assertThrows(IllegalArgumentException.class, () -> RisingModelAssets.install(models, markers, "unrelated", v1));
        Path link = models.resolve(RisingServices.Models.SHIP + ".bbmodel");
        Files.createSymbolicLink(link, models.resolve("unrelated.bbmodel"));
        assertEquals(RisingModelAssets.Outcome.SKIPPED_LINK, RisingModelAssets.install(models, markers, RisingServices.Models.SHIP, v1));
        assertEquals("keep", Files.readString(models.resolve("unrelated.bbmodel")));
    }

    private static int[] pngSize(String dataUri) {
        assertTrue(dataUri.startsWith("data:image/png;base64,"));
        byte[] png = Base64.getDecoder().decode(dataUri.substring("data:image/png;base64,".length()));
        ByteBuffer b = ByteBuffer.wrap(png);
        assertEquals(0x89504E47, b.getInt(0));
        return new int[]{b.getInt(16), b.getInt(20)};
    }
}
