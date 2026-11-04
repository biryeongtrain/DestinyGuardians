package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Exact reviewed ownership for historical contracts; never a directory exemption. */
public final class GripContractsW163Support {
    private GripContractsW163Support() {}
    private static final String ROOT = "src/main/resources/assets/destiny/";
    public static JsonObject json(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }
    private static String sha(String path) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(Path.of(path))));
    }
    public static Set<String> ammitLegacyChanges() {
        return Set.of(ROOT+"items/weapon/ammit_ar2.json",
                ROOT+"models/weapon/auto_rifle/ammit_ar2.json",
                ROOT+"models/weapon/auto_rifle/ammit_ar2_ads.json",
                ROOT+"models/weapon/auto_rifle/ammit_ar2_inspect.json");
    }
    public static void assertAssetHash(String path, String historicalHash) throws Exception {
        var pose = json("art/weapons/w156/ammit-pose.json");
        if (ammitLegacyChanges().contains(path) && path.contains("/models/")) {
            assertEquals(historicalHash, pose.getAsJsonObject("beforeSha256").get(path).getAsString(), path);
            assertEquals(pose.getAsJsonObject("outputSha256").get(path).getAsString(), sha(path), path);
            var display = json(path).getAsJsonObject("display");
            for (String hand : List.of("thirdperson_righthand", "thirdperson_lefthand")) {
                assertEquals(JsonParser.parseString("[72,0,0]"), display.getAsJsonObject(hand).get("rotation"));
                assertEquals(pose.getAsJsonObject("rotations").get("native"), display.getAsJsonObject(hand).get("rotation"));
            }
            return;
        }
        var graphs = json("art/weapons/w161/ammit-crouch.json").getAsJsonObject("graphs");
        // Exact seven reviewed paths, each anchored to its historical hash and current output.
        var graphPaths=Set.of(ROOT+"items/weapon/ammit_ar2.json", ROOT+"items/weapon_aim_w70/ammit_ar2.json",
                ROOT+"items/weapon_reload_w69/ammit_ar2.json", ROOT+"items/weapon_sight_w151/ammit_ar2.json",
                ROOT+"items/weapon_swap_w113/austringer_to_ammit_ar2.json",
                ROOT+"items/weapon_swap_w113/beloved_to_ammit_ar2.json",
                ROOT+"items/weapon_swap_w113/the_recluse_to_ammit_ar2.json");
        assertEquals(graphPaths, graphs.keySet(), "W161 owns exactly seven graphs");
        if (graphPaths.contains(path)) {
            var record = graphs.getAsJsonObject(path);
            assertEquals(historicalHash, record.get("beforeSha256").getAsString(), path);
            assertEquals(record.get("beforeSha256"), record.get("restoredSourceSha256"), path);
            assertEquals(record.get("afterSha256").getAsString(), sha(path), path);
            assertEquals(record.get("firstpersonBefore"), record.get("firstpersonAfter"), path);
            assertEquals(record.get("animatedEntriesBefore"), record.get("animatedEntriesAfter"), path);
            int[] count = {0};
            unwrap(json(path), count);
            assertEquals(3, count[0], path);
            return;
        }
        assertEquals(historicalHash, sha(path), path);
    }
    static JsonObject leaf(String model) {
        var leaf = new JsonObject(); leaf.addProperty("type", "minecraft:model"); leaf.addProperty("model", model); return leaf;
    }
    static JsonObject crouchWrapper(String nativeId, String pose) throws Exception {
        var fallback = leaf(nativeId);
        var condition = new JsonObject();
        condition.addProperty("type", "minecraft:condition"); condition.addProperty("property", "minecraft:custom_model_data");
        condition.addProperty("index", 1); condition.add("on_true", leaf("destiny:weapon_pose_w161/ammit_ar2_"+pose));
        condition.add("on_false", fallback.deepCopy());
        var branch = new JsonObject(); branch.add("when", JsonParser.parseString("[\"thirdperson_righthand\",\"thirdperson_lefthand\"]"));
        branch.add("model", condition); var cases = new JsonArray(); cases.add(branch);
        var wrapper = new JsonObject(); wrapper.addProperty("type", "minecraft:select");
        wrapper.addProperty("property", "minecraft:display_context"); wrapper.add("cases", cases); wrapper.add("fallback", fallback);
        var manifest = json("art/weapons/w161/ammit-crouch.json");
        var basis = manifest.getAsJsonObject("bases").getAsJsonObject(pose);
        assertEquals(nativeId, basis.get("parent").getAsString());
        var childPath = ROOT+"models/weapon_pose_w161/ammit_ar2_"+pose+".json";
        var expectedChild = new JsonObject(); expectedChild.addProperty("parent", nativeId);
        expectedChild.add("display", basis.get("newThirdperson").deepCopy());
        assertEquals(expectedChild, json(childPath));
        assertEquals(manifest.getAsJsonObject("generatedModels").get(childPath).getAsString(), sha(childPath));
        return wrapper;
    }
    private static JsonElement unwrap(JsonElement value, int[] count) throws Exception {
        if (value.isJsonArray()) {
            var out = new JsonArray(); for (var v : value.getAsJsonArray()) out.add(unwrap(v, count)); return out;
        }
        if (!value.isJsonObject()) return value.deepCopy();
        var node = value.getAsJsonObject();
        if (node.has("property") && node.get("property").getAsString().equals("minecraft:display_context")) {
            var fallback = node.getAsJsonObject("fallback");
            for (String pose : List.of("hip", "ads", "inspect")) {
                String suffix = pose.equals("hip") ? "" : "_"+pose;
                String id = "destiny:weapon/auto_rifle/ammit_ar2"+suffix+"_twohand";
                if (leaf(id).equals(fallback)) {
                    assertEquals(crouchWrapper(id, pose), node, "Only exact third-person flag[1] wrapper may supersede W32");
                    count[0]++; return fallback.deepCopy();
                }
            }
        }
        if (node.has("model") && node.get("model").isJsonPrimitive())
            assertFalse(node.get("model").getAsString().startsWith("destiny:weapon_pose_w161/"), "Crouch child outside wrapper");
        var out = new JsonObject();
        for (var e : node.entrySet()) out.add(e.getKey(), unwrap(e.getValue(), count));
        return out;
    }
    static JsonObject originalAmmitGraph(JsonObject item) throws Exception {
        int[] count = {0}; var restored = unwrap(item, count).getAsJsonObject(); assertEquals(3, count[0]); return restored;
    }
}
