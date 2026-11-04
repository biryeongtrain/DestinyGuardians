package kim.biryeong.destiny.fx;

import com.google.gson.*;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import javax.imageio.ImageIO;
import java.nio.file.*;
import java.io.StringReader;
import java.security.MessageDigest;
import java.util.HexFormat;
import static org.junit.jupiter.api.Assertions.*;

/** Codec and authored glyph checks only. No framebuffer, accessibility or actual client text-size evidence. */
class ArcherTempoHudW73Test {
    @Test void native26CodecAcceptsNewTintedHudModelAndManifestPinsEveryGeneratedByte() throws Exception {
        ItemModels.bootstrap();ItemTintSources.bootstrap();
        var m=JsonParser.parseString(Files.readString(Path.of("art/hud/w73-archers-tempo/manifest.json"))).getAsJsonObject();
        for(var e:m.getAsJsonObject("sha256").entrySet()) {
            var p=Path.of(e.getKey());var bytes=Files.readAllBytes(p);
            assertEquals(e.getValue().getAsString(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
            if(e.getKey().contains("/items/")) {
                var model=JsonParser.parseString(Files.readString(p)).getAsJsonObject();
                assertTrue(ItemModels.CODEC.parse(JsonOps.INSTANCE,model.get("model")).isSuccess());
            }
            if(e.getKey().contains("/models/"))assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(p))));
        }
    }
    @Test void spriteFitsOriginalSlotWithTransparentMarginAndContainsVisibleGlyphs() throws Exception {
        var p=Path.of("src/main/resources/assets/destiny/textures/item/hud/perk_archers_tempo_w73.png");
        var im=ImageIO.read(p.toFile());assertNotNull(im);assertEquals(94,im.getWidth());assertEquals(24,im.getHeight());
        int ink=0;
        for(int y=0;y<24;y++)for(int x=0;x<94;x++) {
            int alpha=im.getRGB(x,y)>>>24;if(alpha>0)ink++;
            if(x==0||x==93||y==0||y==23)assertEquals(0,alpha,"No clipped edge glyphs");
        }
        assertTrue(ink>150 && ink<94*24/2);
        var model=JsonParser.parseString(Files.readString(Path.of("src/main/resources/assets/destiny/models/gui/hud/perk_archers_tempo_w73.json"))).getAsJsonObject();
        assertEquals("destiny:item/hud/perk_archers_tempo_w73",model.getAsJsonObject("textures").get("layer0").getAsString());
    }
}
