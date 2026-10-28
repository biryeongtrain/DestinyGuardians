package kim.biryeong.destiny.fx;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.loader.api.FabricLoader;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.util.HashMap;
import java.util.HashSet;

/** Source-derived Titan/Warlock clips on BetterModel's complete player-skin rig. */
public final class ClassSuperModelAssets {
    public static final String MODEL_NAME = "guardian_classes_w229_r3";
    static final String RESOURCE = "/destiny/animation/classes_w229.animation.json";
    private ClassSuperModelAssets() { }

    public static String prefix(String abilityPath) {
        return "w229_" + abilityPath.replace('/', '_').replace("_super", "");
    }

    public static boolean hasClip(String clip) {
        return ClipIndex.NAMES.contains(clip);
    }

    private static final class ClipIndex {
        static final java.util.Set<String> NAMES = load();
    }

    private static java.util.Set<String> load() {
        try (var in = ClassSuperModelAssets.class.getResourceAsStream(RESOURCE)) {
            if (in == null) return java.util.Set.of();
            var animations = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8))
                    .getAsJsonObject().getAsJsonArray("animations");
            var names = new HashSet<String>();
            for (var a : animations) names.add(a.getAsJsonObject().get("name").getAsString());
            return java.util.Set.copyOf(names);
        } catch (Exception e) { return java.util.Set.of(); }
    }

    public static void prepare() {
        var target = FabricLoader.getInstance().getConfigDir().resolve("bettermodel/players/" + MODEL_NAME + ".bbmodel");
        if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)) return;
        try (var template = ClassSuperModelAssets.class.getResourceAsStream("/steve.bbmodel");
             var clips = ClassSuperModelAssets.class.getResourceAsStream(RESOURCE)) {
            if (template == null || clips == null) return;
            var model = buildModel(JsonParser.parseReader(new InputStreamReader(template, StandardCharsets.UTF_8)).getAsJsonObject(),
                    JsonParser.parseReader(new InputStreamReader(clips, StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonArray("animations"));
            if (HunterModelAssets.installIfAbsent(target, model))
                DestinyGuardians.LOGGER.info("Installed source-derived Titan/Warlock limb: {}", target);
        } catch (Exception e) {
            DestinyGuardians.LOGGER.warn("Cannot install Titan/Warlock source limb: {}", e.toString());
        }
    }

    static JsonObject buildModel(JsonObject template, JsonArray clips) {
        var model = template.deepCopy();
        model.addProperty("name", MODEL_NAME);
        model.addProperty("model_identifier", MODEL_NAME);
        var groups = new HashMap<String, String>();
        for (var g : model.getAsJsonArray("groups")) {
            var group = g.getAsJsonObject();
            groups.put(group.get("name").getAsString(), group.get("uuid").getAsString());
        }
        var animations = model.getAsJsonArray("animations");
        if (animations == null) { animations = new JsonArray(); model.add("animations", animations); }
        var names = new HashSet<String>();
        for (var a : animations) names.add(a.getAsJsonObject().get("name").getAsString());
        for (var a : clips) {
            var animation = a.getAsJsonObject().deepCopy();
            String name = animation.get("name").getAsString();
            if (!name.startsWith("w229_") || !names.add(name)) throw new IllegalArgumentException("Foreign/duplicate class clip " + name);
            var remapped = new JsonObject();
            for (var entry : animation.getAsJsonObject("animators").entrySet()) {
                var animator = entry.getValue().getAsJsonObject();
                String bone = animator.get("name").getAsString();
                if (!groups.containsKey(bone)) throw new IllegalArgumentException("Missing skin rig bone " + bone);
                remapped.add(groups.get(bone), animator);
            }
            animation.add("animators", remapped);
            animations.add(animation);
        }
        return model;
    }
}
