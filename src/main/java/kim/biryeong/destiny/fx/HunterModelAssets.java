package kim.biryeong.destiny.fx;

import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.loader.api.FabricLoader;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Map;
import java.util.UUID;

/** Derives the initial hunter limb from the installed BetterModel template, preserving its skin rig. */
public final class HunterModelAssets {
    private HunterModelAssets() { }

    public static void prepare() {
        var target = FabricLoader.getInstance().getConfigDir().resolve("bettermodel/players/guardian_hunter.bbmodel");
        // Server artists own this file after its first installation.
        if (Files.exists(target)) return;
        try (var template = HunterModelAssets.class.getResourceAsStream("/steve.bbmodel")) {
            if (template == null) throw new IllegalStateException("BetterModel steve.bbmodel template missing");
            JsonObject model = JsonParser.parseReader(new InputStreamReader(template, StandardCharsets.UTF_8)).getAsJsonObject();
            model.addProperty("name", "guardian_hunter");
            model.addProperty("model_identifier", "guardian_hunter");
            var animations = model.getAsJsonArray("animations");
            addPose(model, animations, "super_arc", Map.of(
                    "pc_chest", new int[]{0, -15, 0}, "pra_right_arm", new int[]{-65, 0, -35},
                    "pla_left_arm", new int[]{-35, 0, 30}, "prl_right_leg", new int[]{-15, 0, -8},
                    "pll_left_leg", new int[]{15, 0, 8}));
            addPose(model, animations, "super_solar", Map.of(
                    "pc_chest", new int[]{0, 15, 0}, "pra_right_arm", new int[]{-90, 0, 0},
                    "pla_left_arm", new int[]{-45, 0, 20}));
            addPose(model, animations, "super_void", Map.of(
                    "pc_chest", new int[]{0, -25, 0}, "pra_right_arm", new int[]{-90, -55, 0},
                    "pla_left_arm", new int[]{-90, 35, 0}, "plfa_left_forearm", new int[]{-65, 0, 0}));
            Files.createDirectories(target.getParent());
            Files.writeString(target, new GsonBuilder().setPrettyPrinting().create().toJson(model));
            DestinyGuardians.LOGGER.info("Installed hunter limb (roll + three super poses): {}", target);
        } catch (Exception e) {
            throw new IllegalStateException("Cannot prepare hunter player model", e);
        }
    }

    private static void addPose(JsonObject model, JsonArray animations, String name, Map<String, int[]> rotations) {
        JsonObject animation = new JsonObject();
        animation.addProperty("uuid", UUID.randomUUID().toString());
        animation.addProperty("name", name);
        animation.addProperty("loop", "loop");
        animation.addProperty("length", 1.0);
        animation.addProperty("snapping", 20);
        JsonObject animators = new JsonObject();
        for (var entry : model.getAsJsonArray("groups")) {
            JsonObject group = entry.getAsJsonObject();
            String boneName = group.get("name").getAsString();
            int[] rotation = rotations.get(boneName);
            if (rotation == null) continue;
            JsonObject animator = new JsonObject();
            animator.addProperty("name", boneName);
            animator.addProperty("type", "bone");
            JsonArray keyframes = new JsonArray();
            for (double time : new double[]{0, 0.5, 1}) {
                JsonObject key = new JsonObject();
                key.addProperty("channel", "rotation");
                key.addProperty("time", time);
                key.addProperty("interpolation", "linear");
                key.addProperty("uuid", UUID.randomUUID().toString());
                JsonObject point = new JsonObject();
                point.addProperty("x", rotation[0] + (time == 0.5 ? 2 : 0));
                point.addProperty("y", rotation[1]);
                point.addProperty("z", rotation[2]);
                JsonArray points = new JsonArray();
                points.add(point);
                key.add("data_points", points);
                keyframes.add(key);
            }
            animator.add("keyframes", keyframes);
            animators.add(group.get("uuid").getAsString(), animator);
        }
        animation.add("animators", animators);
        animations.add(animation);
    }
}
