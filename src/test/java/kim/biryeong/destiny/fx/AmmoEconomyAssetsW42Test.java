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
class AmmoEconomyAssetsW42Test {
    @Test void originalAssetsAndEditableModelsDecodeAndMatchManifest() throws Exception {
        ItemModels.bootstrap();ItemTintSources.bootstrap();
        var m=JsonParser.parseString(Files.readString(Path.of("art/hud/w42/manifest.json"))).getAsJsonObject();
        assertTrue(m.get("originalArtwork").getAsBoolean());assertEquals(11,m.getAsJsonObject("sha256").size());
        for(var e:m.getAsJsonObject("sha256").entrySet()) {
            var p=Path.of(e.getKey());var raw=Files.readAllBytes(p);
            assertEquals(e.getValue().getAsString(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
            if(e.getKey().contains("/items/"))assertTrue(ItemModels.CODEC.parse(JsonOps.INSTANCE,JsonParser.parseString(new String(raw)).getAsJsonObject().get("model")).isSuccess());
            if(e.getKey().contains("/models/"))assertNotNull(CuboidModel.fromStream(new StringReader(new String(raw))));
            if(e.getKey().endsWith(".bbmodel")) {
                var bb=JsonParser.parseString(new String(raw)).getAsJsonObject();
                assertTrue(bb.getAsJsonArray("elements").size()>16);assertTrue(bb.getAsJsonArray("elements").size()<=256);
            }
        }
    }
}
