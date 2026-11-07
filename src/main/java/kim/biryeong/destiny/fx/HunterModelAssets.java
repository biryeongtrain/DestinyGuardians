package kim.biryeong.destiny.fx;

import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.loader.api.FabricLoader;

import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;

/** Installs a versioned limb without ever opening an artist-owned installed model for writing. */
public final class HunterModelAssets {
    public static final String MODEL_NAME = "guardian_hunter_w332_"+SuperMotionOverlaysW332.revision()+"_"+MeleeSuperAnimationTiming.revision(MeleeSuperAnimationTiming.ARC_RESOURCE);
    static final String ANIMATION_RESOURCE = "/destiny/animation/hunter_w199.animation.json";

    private HunterModelAssets() { }

    public static void prepare() {
        Path target = FabricLoader.getInstance().getConfigDir()
                .resolve("bettermodel/players/" + MODEL_NAME + ".bbmodel");
        try {MeleeSuperAnimationTiming.require(MeleeSuperAnimationTiming.ARC_RESOURCE);SuperMotionOverlaysW332.require();}
        catch(IllegalStateException e){DestinyGuardians.LOGGER.error(e.getMessage());return;}
        if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)) return;
        try (var template = HunterModelAssets.class.getResourceAsStream("/steve.bbmodel");
             var clips = HunterModelAssets.class.getResourceAsStream(ANIMATION_RESOURCE)) {
            if (template == null || clips == null) throw new IOException("Hunter template or W199 clips missing");
            JsonArray animations=JsonParser.parseReader(new InputStreamReader(clips,StandardCharsets.UTF_8))
                    .getAsJsonObject().getAsJsonArray("animations");
            try(var grenade=HunterModelAssets.class.getResourceAsStream("/destiny/animation/grenade_w252.animation.json")) {
                if(grenade==null)throw new IOException("W252 throw animation missing");
                JsonObject replacement=JsonParser.parseReader(new InputStreamReader(grenade,StandardCharsets.UTF_8))
                        .getAsJsonObject().getAsJsonArray("animations").get(0).getAsJsonObject();
                for(int i=0;i<animations.size();i++)if(animations.get(i).getAsJsonObject().get("name").getAsString().equals("h15_grenade"))
                    animations.set(i,replacement);
            }
            try(var source=HunterModelAssets.class.getResourceAsStream("/destiny/animation/class_ability_w255.animation.json")) {
                if(source==null)throw new IOException("W255 class animations missing");
                var classes=JsonParser.parseReader(new InputStreamReader(source,StandardCharsets.UTF_8))
                        .getAsJsonObject().getAsJsonArray("animations");
                classes.forEach(animations::add);
            }
            try (var source = HunterModelAssets.class.getResourceAsStream("/destiny/animation/hunter_dodge_w259.animation.json")) {
                if (source == null) throw new IOException("W259 dodge animations missing");
                var dodges = JsonParser.parseReader(new InputStreamReader(source, StandardCharsets.UTF_8))
                        .getAsJsonObject().getAsJsonArray("animations");
                for (var entry : dodges) {
                    String name = entry.getAsJsonObject().get("name").getAsString();
                    boolean replaced = false;
                    for (int i = 0; i < animations.size(); i++) {
                        if (name.equals(animations.get(i).getAsJsonObject().get("name").getAsString())) {
                            animations.set(i, entry);
                            replaced = true;
                            break;
                        }
                    }
                    if (!replaced) animations.add(entry);
                }
            }
            try (var source = HunterModelAssets.class.getResourceAsStream("/destiny/animation/crucible_intro_w260.animation.json")) {
                if (source == null) throw new IOException("W260 intro animations missing");
                JsonParser.parseReader(new InputStreamReader(source, StandardCharsets.UTF_8))
                        .getAsJsonObject().getAsJsonArray("animations")
                        .forEach(entry -> animations.add(inPlaceIntro(entry.getAsJsonObject().deepCopy())));
            }
            try (var source = HunterModelAssets.class.getResourceAsStream("/destiny/animation/briefing_crota_landing.animation.json")) {
                if (source == null) throw new IOException("Briefing landing animations missing");
                JsonParser.parseReader(new InputStreamReader(source, StandardCharsets.UTF_8))
                        .getAsJsonObject().getAsJsonArray("animations")
                        .forEach(entry -> animations.add(inPlaceIntro(entry.getAsJsonObject().deepCopy())));
            }
            try (var source = HunterModelAssets.class.getResourceAsStream("/destiny/animation/revive_combat.animation.json")) {
                if (source == null) throw new IOException("Revive source animation missing");
                JsonParser.parseReader(new InputStreamReader(source, StandardCharsets.UTF_8))
                        .getAsJsonObject().getAsJsonArray("animations").forEach(animations::add);
            }
            JsonArray compiledAnimations=SuperMotionOverlaysW332.overlay(
                    MeleeSuperAnimationTiming.overlay(animations,MeleeSuperAnimationTiming.ARC_RESOURCE),"h15_");
            JsonObject model = buildModel(
                    JsonParser.parseReader(new InputStreamReader(template, StandardCharsets.UTF_8)).getAsJsonObject(),compiledAnimations);
            if (installIfAbsent(target, model)) {
                DestinyGuardians.LOGGER.info("Installed W260 hunter limb: {}", target);
            }
        } catch (Exception e) {
            // Cosmetic failure must not prevent startup: PlayerAnimations tries legacy limb then Steve.
            DestinyGuardians.LOGGER.warn("Cannot prepare W260 hunter limb; legacy fallback remains available: {}", e.toString());
        }
    }


    /** W273: the raw entrance travels tens of blocks and can pass through the floor. Keep the authored
     * pose, timing and vertical landing, but pin horizontal root travel to the final landing spot so
     * the actor stays on its stage anchor. */
    static JsonObject inPlaceIntro(JsonObject clip) {
        for (var animator : clip.getAsJsonObject("animators").entrySet()) {
            JsonObject bone = animator.getValue().getAsJsonObject();
            JsonObject last = null;
            double lastTime = Double.NEGATIVE_INFINITY;
            for (var key : bone.getAsJsonArray("keyframes")) {
                JsonObject k = key.getAsJsonObject();
                if (!"position".equals(k.get("channel").getAsString())) continue;
                double time = k.get("time").getAsDouble();
                if (time >= lastTime) { lastTime = time; last = k; }
            }
            if (last == null) continue;
            var end = last.getAsJsonArray("data_points").get(0).getAsJsonObject();
            for (var key : bone.getAsJsonArray("keyframes")) {
                JsonObject k = key.getAsJsonObject();
                if (!"position".equals(k.get("channel").getAsString())) continue;
                for (var point : k.getAsJsonArray("data_points")) {
                    point.getAsJsonObject().add("x", end.get("x"));
                    point.getAsJsonObject().add("z", end.get("z"));
                }
            }
        }
        return clip;
    }

    /** Remap by bone name, retaining the installed BetterModel version's complete skin/armor rig. */
    static JsonObject buildModel(JsonObject template, JsonArray clips) {
        JsonObject model = template.deepCopy();
        model.addProperty("name", MODEL_NAME);
        model.addProperty("model_identifier", MODEL_NAME);
        Map<String, String> groups = new HashMap<>();
        for (var entry : model.getAsJsonArray("groups")) {
            JsonObject group = entry.getAsJsonObject();
            groups.put(group.get("name").getAsString(), group.get("uuid").getAsString());
        }
        JsonArray animations = model.getAsJsonArray("animations");
        if (animations == null) {
            animations = new JsonArray();
            model.add("animations", animations);
        }
        var names = new HashSet<String>();
        for (var entry : animations) names.add(entry.getAsJsonObject().get("name").getAsString());
        for (var entry : clips) {
            JsonObject animation = SourceAnimationGrid.compile(entry.getAsJsonObject());
            String name = animation.get("name").getAsString();
            if (!name.startsWith("h15_") || !names.add(name)) throw new IllegalArgumentException("Duplicate/foreign H15 clip: " + name);
            JsonObject remapped = new JsonObject();
            for (var animatorEntry : animation.getAsJsonObject("animators").entrySet()) {
                JsonObject animator = animatorEntry.getValue().getAsJsonObject();
                String bone = animator.get("name").getAsString();
                String uuid = groups.get(bone);
                if (uuid == null) throw new IllegalArgumentException("BetterModel template lacks H15 bone " + bone);
                remapped.add(uuid, animator);
            }
            animation.add("animators", remapped);
            animations.add(animation);
        }
        return model;
    }

    /** CREATE_NEW also protects files/symlinks created between the existence check and write. */
    static boolean installIfAbsent(Path target, JsonObject model) throws IOException {
        Files.createDirectories(target.getParent());
        String json = new GsonBuilder().setPrettyPrinting().create().toJson(model);
        try {
            Files.writeString(target, json, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
            return true;
        } catch (FileAlreadyExistsException e) {
            return false;
        }
    }
}
