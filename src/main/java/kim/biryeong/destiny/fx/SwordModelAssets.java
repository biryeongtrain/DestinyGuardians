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

/** Separate versioned sword limb; never replaces artist-owned hunter/Steve models. */
public final class SwordModelAssets {
    public static final String MODEL_NAME = "guardian_sword_w53";
    public static final String RESOURCE = "/destiny/animation/sword_w53.animation.json";
    private SwordModelAssets() {}

    public static void prepare() {
        var target=FabricLoader.getInstance().getConfigDir().resolve("bettermodel/players/"+MODEL_NAME+".bbmodel");
        if(Files.exists(target,LinkOption.NOFOLLOW_LINKS))return;
        try(var base=SwordModelAssets.class.getResourceAsStream("/steve.bbmodel");
            var clips=SwordModelAssets.class.getResourceAsStream(RESOURCE)) {
            if(base==null||clips==null)throw new IllegalStateException("Missing sword skin rig/clips");
            var model=buildModel(JsonParser.parseReader(new InputStreamReader(base,StandardCharsets.UTF_8)).getAsJsonObject(),
                    JsonParser.parseReader(new InputStreamReader(clips,StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonArray("animations"));
            if(HunterModelAssets.installIfAbsent(target,model))DestinyGuardians.LOGGER.info("Installed W53 sword limb: {}",target);
        } catch(Exception e) {
            DestinyGuardians.LOGGER.warn("Sword limb unavailable; native swing remains: {}",e.toString());
        }
    }

    static JsonObject buildModel(JsonObject template,JsonArray clips) {
        if(clips.isEmpty())throw new IllegalArgumentException("Empty sword clips");
        for(var clip:clips)if(!clip.getAsJsonObject().get("name").getAsString().startsWith("h15_sword_"))
            throw new IllegalArgumentException("Foreign sword clip");
        var result=HunterModelAssets.buildModel(template,clips);
        result.addProperty("name",MODEL_NAME);
        result.addProperty("model_identifier",MODEL_NAME);
        return result;
    }
}
