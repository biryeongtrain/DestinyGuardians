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

/** Versioned close high carry, lowered elbows and one-hand light recovery; preserves existing W53/W55 artist installs. */
public final class SwordPoseW146Assets {
    public static final String MODEL_NAME = "guardian_sword_w146";
    public static final String RESOURCE = "/destiny/animation/sword_w146.animation.json";
    private SwordPoseW146Assets() { }

    public static void prepare() {
        var target = FabricLoader.getInstance().getConfigDir().resolve("bettermodel/players/" + MODEL_NAME + ".bbmodel");
        if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)) return;
        try (var base = SwordPoseW146Assets.class.getResourceAsStream("/steve.bbmodel");
             var clips = SwordPoseW146Assets.class.getResourceAsStream(RESOURCE)) {
            if (base == null || clips == null) throw new IllegalStateException("Missing W146 sword rig/clips");
            var model = buildModel(JsonParser.parseReader(new InputStreamReader(base, StandardCharsets.UTF_8)).getAsJsonObject(),
                    JsonParser.parseReader(new InputStreamReader(clips, StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonArray("animations"));
            if (HunterModelAssets.installIfAbsent(target, model)) DestinyGuardians.LOGGER.info("Installed W146 raised sword limb: {}", target);
        } catch (Exception e) {
            DestinyGuardians.LOGGER.warn("Raised sword limb unavailable: {}", e.toString());
        }
    }

    static JsonObject buildModel(JsonObject template, JsonArray clips) {
        var result = SwordModelAssets.buildModel(template, clips);
        result.addProperty("name", MODEL_NAME);
        result.addProperty("model_identifier", MODEL_NAME);
        return result;
    }
}
