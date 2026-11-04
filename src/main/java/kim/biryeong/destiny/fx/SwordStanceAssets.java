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

/** New versioned limb: W53's eight attacks plus four stance loops.
 * CREATE_NEW installation deliberately preserves all existing artist files. */
public final class SwordStanceAssets {
    public static final String MODEL_NAME = "guardian_sword_w55";
    public static final String RESOURCE = "/destiny/animation/sword_w55.animation.json";
    private SwordStanceAssets() { }

    public static void prepare() {
        var target=FabricLoader.getInstance().getConfigDir().resolve("bettermodel/players/"+MODEL_NAME+".bbmodel");
        if(Files.exists(target,LinkOption.NOFOLLOW_LINKS))return;
        try(var base=SwordStanceAssets.class.getResourceAsStream("/steve.bbmodel");
            var clips=SwordStanceAssets.class.getResourceAsStream(RESOURCE)) {
            if(base==null||clips==null)throw new IllegalStateException("Missing sword stance skin rig/clips");
            var model=buildModel(JsonParser.parseReader(new InputStreamReader(base,StandardCharsets.UTF_8)).getAsJsonObject(),
                    JsonParser.parseReader(new InputStreamReader(clips,StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonArray("animations"));
            if(HunterModelAssets.installIfAbsent(target,model))DestinyGuardians.LOGGER.info("Installed W55 sword stance limb: {}",target);
        } catch(Exception e) {
            DestinyGuardians.LOGGER.warn("Sword stance limb unavailable; native cosmetics remain: {}",e.toString());
        }
    }

    static JsonObject buildModel(JsonObject template,JsonArray clips) {
        var result=SwordModelAssets.buildModel(template,clips);
        result.addProperty("name",MODEL_NAME);
        result.addProperty("model_identifier",MODEL_NAME);
        return result;
    }
}
