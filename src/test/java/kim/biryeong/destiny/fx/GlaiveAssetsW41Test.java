package kim.biryeong.destiny.fx;
import com.google.gson.*;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.io.StringReader;
import java.security.MessageDigest;
import java.util.HexFormat;
import static org.junit.jupiter.api.Assertions.*;
class GlaiveAssetsW41Test {
    @Test void nativeModelsDecodeAndOriginalAssetHashesMatch() throws Exception {
        ItemModels.bootstrap();ItemTintSources.bootstrap();
        var m=JsonParser.parseString(Files.readString(Path.of("art/hud/w41/manifest.json"))).getAsJsonObject();
        assertEquals(6,m.getAsJsonObject("sha256").size());
        for(var e:m.getAsJsonObject("sha256").entrySet()) {
            var p=Path.of(e.getKey());assertEquals(e.getValue().getAsString(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p))));
            if(e.getKey().contains("/items/"))assertTrue(ItemModels.CODEC.parse(JsonOps.INSTANCE,JsonParser.parseString(Files.readString(p)).getAsJsonObject().get("model")).isSuccess());
            if(e.getKey().contains("/models/"))assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(p))));
        }
    }
}
