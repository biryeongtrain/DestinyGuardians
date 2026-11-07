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
    public static final String MODEL_NAME = "guardian_classes_w336_"+SuperLocomotionW336.revision(SuperLocomotionW336.HUNTER_RESOURCE,SuperLocomotionW336.CLASSES_RESOURCE,SuperLocomotionW336.TITAN_RUNNING_RESOURCE)+"_"+SuperMotionOverlaysW332.revision()+"_"+MeleeSuperAnimationTiming.revision(MeleeSuperAnimationTiming.SPECTRAL_RESOURCE);
    static final String RESOURCE = "/destiny/animation/classes_w230.animation.json";
    private static final java.util.Set<String> EXPANDED = java.util.Set.of(
            "hunter/blade_barrage", "hunter/spectral_blades", "hunter/gathering_storm", "hunter/storms_edge",
            "titan/thundercrash", "titan/burning_maul", "titan/ward_of_dawn",
            "warlock/well_of_radiance", "warlock/chaos_reach", "warlock/nova_warp");
    private ClassSuperModelAssets() { }

    public static String prefix(String abilityPath) {
        return (isExpanded(abilityPath) ? "w230_" : "w229_")
                + abilityPath.replace('/', '_').replace("_super", "");
    }

    public static boolean isExpanded(String path) { return EXPANDED.contains(path); }

    /** Full clip span in server ticks; call sites add their explicit entry blend separately. */
    public static int durationTicks(String path, String phase, int fallback) {
        Double seconds = ClipIndex.LENGTHS.get(prefix(path) + "_" + phase);
        return seconds == null ? fallback : Math.max(1, (int) Math.ceil(seconds * 20));
    }

    public static boolean hasClip(String clip) {
        return ClipIndex.LENGTHS.containsKey(clip);
    }

    private static final class ClipIndex {
        static final java.util.Map<String, Double> LENGTHS = load();
    }

    private static java.util.Map<String, Double> load() {
        try (var in = ClassSuperModelAssets.class.getResourceAsStream(RESOURCE)) {
            if (in == null) return java.util.Map.of();
            var animations = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8))
                    .getAsJsonObject().getAsJsonArray("animations");
            var lengths = new HashMap<String, Double>();
            animations=SuperLocomotionW336.overlay(SuperMotionOverlaysW332.overlay(MeleeSuperAnimationTiming.overlay(animations,MeleeSuperAnimationTiming.SPECTRAL_RESOURCE),"w2"),"w2");
            for (var a : animations) {
                var clip = a.getAsJsonObject();
                lengths.put(clip.get("name").getAsString(), clip.get("length").getAsDouble());
            }
            return java.util.Map.copyOf(lengths);
        } catch (Exception e) { return java.util.Map.of(); }
    }

    public static void prepare() {
        var target = FabricLoader.getInstance().getConfigDir().resolve("bettermodel/players/" + MODEL_NAME + ".bbmodel");
        try {MeleeSuperAnimationTiming.require(MeleeSuperAnimationTiming.SPECTRAL_RESOURCE);SuperMotionOverlaysW332.require();}
        catch(IllegalStateException e){DestinyGuardians.LOGGER.error(e.getMessage());return;}
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
        clips=SuperLocomotionW336.overlay(SuperMotionOverlaysW332.overlay(MeleeSuperAnimationTiming.overlay(clips,MeleeSuperAnimationTiming.SPECTRAL_RESOURCE),"w2"),"w2");
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
            var animation = SourceAnimationGrid.compile(a.getAsJsonObject());
            String name = animation.get("name").getAsString();
            if (!(name.startsWith("w229_") || name.startsWith("w230_")) || !names.add(name))
                throw new IllegalArgumentException("Foreign/duplicate class clip " + name);
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
