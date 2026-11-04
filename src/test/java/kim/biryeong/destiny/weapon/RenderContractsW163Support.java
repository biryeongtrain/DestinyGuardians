package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.regex.Pattern;
import static org.junit.jupiter.api.Assertions.*;

/** Narrow, reversible reviewed migrations; all other bytes retain their historical pins. */
public final class RenderContractsW163Support {
    private static final String ROOT = "src/main/resources/assets/destiny/";
    private static final List<String> THIRD = List.of("thirdperson_righthand", "thirdperson_lefthand");
    private static final Gson PRETTY = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();
    private RenderContractsW163Support() {}

    public static String historicalSha(Path path) throws Exception {
        String name = path.toString();
        byte[] bytes = Files.readAllBytes(path);
        // W161's exact seven reviewed graphs, never arbitrary current item graphs.
        var graphs = json(Path.of("art/weapons/w161/ammit-crouch.json"));
        assertEquals("W161", graphs.get("stage").getAsString());
        var row = graphs.getAsJsonObject("graphs").get(name);
        if (row != null) {
            var record = row.getAsJsonObject();
            assertEquals(record.get("afterSha256").getAsString(), sha(bytes), name);
            var restored = historicalNormalGraph(JsonParser.parseString(new String(bytes, StandardCharsets.UTF_8)));
            bytes = (PRETTY.toJson(restored) + "\n").getBytes(StandardCharsets.UTF_8);
            assertEquals(record.get("beforeSha256").getAsString(), sha(bytes), "Exact W161 source restoration: " + name);
            assertEquals(record.get("restoredSourceSha256").getAsString(), sha(bytes));
        }
        // W156 canonical and propagated native poses: only Rx90 -> Rx72 in both third-person contexts.
        if (name.matches(Pattern.quote(ROOT) + "models/(weapon/auto_rifle/ammit_ar2(?:_ads|_inspect)?|weapon_aim_w70/ammit_ar2_[0-9]{2}_native|weapon_reload_w69/ammit_ar2_[0-9]{2}_(?:body|magazine)_native)\\.json")) {
            String text = new String(bytes, StandardCharsets.UTF_8);
            var model = JsonParser.parseString(text).getAsJsonObject();
            for (String context : THIRD) {
                assertEquals(JsonParser.parseString("[72,0,0]"), model.getAsJsonObject("display").getAsJsonObject(context).get("rotation"), name);
                var pattern = Pattern.compile("(\"" + context + "\"\\s*:\\s*\\{\\s*\"rotation\"\\s*:\\s*\\[\\s*)72(?=\\s*,)");
                var matcher = pattern.matcher(text);
                assertTrue(matcher.find(), "Only documented rotation field: " + name);
                text = matcher.replaceFirst(java.util.regex.Matcher.quoteReplacement(matcher.group(1) + "90"));
            }
            bytes = text.getBytes(StandardCharsets.UTF_8);
            if (name.startsWith(ROOT + "models/weapon/auto_rifle/")) {
                var manifest = json(Path.of("art/weapons/w156/ammit-pose.json"));
                assertEquals("W156", manifest.get("stage").getAsString());
                assertEquals(manifest.getAsJsonObject("beforeSha256").get(name).getAsString(), sha(bytes));
                assertEquals(manifest.getAsJsonObject("outputSha256").get(name).getAsString(), sha(Files.readAllBytes(path)));
            }
        }
        return sha(bytes);
    }

    /** Remove only the exact W161 third-person flag[1] wrapper; reject any other alteration. */
    public static JsonElement historicalNormalGraph(JsonElement value) {
        if (value.isJsonArray()) {
            var result = new JsonArray();
            for (var child : value.getAsJsonArray()) result.add(historicalNormalGraph(child));
            return result;
        }
        if (!value.isJsonObject()) return value.deepCopy();
        var node = value.getAsJsonObject();
        if (node.has("property") && node.get("property").getAsString().equals("minecraft:display_context")
                && node.has("fallback") && node.get("fallback").isJsonObject()) {
            var leaf = node.getAsJsonObject("fallback");
            if (leaf.has("model") && leaf.get("model").isJsonPrimitive()) {
                String id = leaf.get("model").getAsString();
                String pose = switch (id) {
                    case "destiny:weapon/auto_rifle/ammit_ar2_twohand" -> "hip";
                    case "destiny:weapon/auto_rifle/ammit_ar2_ads_twohand" -> "ads";
                    case "destiny:weapon/auto_rifle/ammit_ar2_inspect_twohand" -> "inspect";
                    default -> null;
                };
                if (pose != null) {
                    assertEquals(Set.of("type", "model"), leaf.keySet());
                    var expected = JsonParser.parseString("{\"type\":\"minecraft:select\",\"property\":\"minecraft:display_context\",\"cases\":[{\"when\":[\"thirdperson_righthand\",\"thirdperson_lefthand\"],\"model\":{\"type\":\"minecraft:condition\",\"property\":\"minecraft:custom_model_data\",\"index\":1}}]}").getAsJsonObject();
                    var condition = expected.getAsJsonArray("cases").get(0).getAsJsonObject().getAsJsonObject("model");
                    var crouch = new JsonObject(); crouch.addProperty("type", "minecraft:model");
                    crouch.addProperty("model", "destiny:weapon_pose_w161/ammit_ar2_" + pose);
                    condition.add("on_true", crouch); condition.add("on_false", leaf.deepCopy());
                    expected.add("fallback", leaf.deepCopy());
                    assertEquals(expected, node, "Exact reviewed W161 context/grip/crouch routing");
                    return leaf.deepCopy();
                }
            }
        }
        if (node.has("model") && node.get("model").isJsonPrimitive())
            assertFalse(node.get("model").getAsString().startsWith("destiny:weapon_pose_w161/"), "Crouch leaf outside reviewed wrapper");
        var result = new JsonObject();
        for (var entry : node.entrySet()) result.add(entry.getKey(), historicalNormalGraph(entry.getValue()));
        return result;
    }

    private static JsonObject json(Path p) throws Exception { return JsonParser.parseString(Files.readString(p)).getAsJsonObject(); }
    private static String sha(byte[] bytes) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
}
