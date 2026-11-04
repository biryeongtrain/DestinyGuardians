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

class LoadoutHudAssetsW40Test {
    @Test void native26CodecAcceptsInfinityDamageAndStowedAssetsAndManifestPinsBytes() throws Exception {
        ItemModels.bootstrap();ItemTintSources.bootstrap();
        var root=Path.of("src/main/resources/assets/destiny");
        var manifest=JsonParser.parseString(Files.readString(Path.of("art/hud/w40/manifest.json"))).getAsJsonObject();
        assertEquals(24,manifest.getAsJsonObject("sha256").size());
        for(var e:manifest.getAsJsonObject("sha256").entrySet()) {
            assertEquals(e.getValue().getAsString(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(Path.of(e.getKey())))));
            if(e.getKey().contains("/items/")) {
                var json=JsonParser.parseString(Files.readString(Path.of(e.getKey()))).getAsJsonObject();
                assertTrue(ItemModels.CODEC.parse(JsonOps.INSTANCE,json.get("model")).isSuccess());
            }
            if(e.getKey().contains("/models/"))assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(Path.of(e.getKey())))));
        }
    }
}
