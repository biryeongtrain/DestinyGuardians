package kim.biryeong.destiny.hud;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import javax.imageio.ImageIO;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.HexFormat;
import static org.junit.jupiter.api.Assertions.*;

class MeleeTraitHudW110AssetTest {
    @Test void exactThreePackAssetsHavePinnedBytesAndItemAtlasTextures() throws Exception {
        long total=0;
        for(String trait:new String[]{"swashbuckler"}) {
            String name="perk_"+trait+"_w110";
            var manifest=JsonParser.parseString(Files.readString(Path.of("art/weapons/w110/hud/"+trait+"/manifest.json"))).getAsJsonObject();
            var files=manifest.getAsJsonObject("pack_files");assertEquals(3,files.size());
            for(var entry:files.entrySet()) {
                byte[] data=Files.readAllBytes(Path.of(entry.getKey()));total+=data.length;
                assertEquals(entry.getValue().getAsString(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data)));
            }
            var model=JsonParser.parseString(Files.readString(Path.of("src/main/resources/assets/destiny/models/gui/hud/"+name+".json"))).getAsJsonObject();
            assertEquals("destiny:item/hud/"+name,model.getAsJsonObject("textures").get("0").getAsString());
            var item=JsonParser.parseString(Files.readString(Path.of("src/main/resources/assets/destiny/items/gui/hud/"+name+".json"))).getAsJsonObject();
            assertEquals("destiny:gui/hud/"+name,item.getAsJsonObject("model").get("model").getAsString());
        }
        assertTrue(total<=32768,"Three bounded assets; no unrelated replacements");
    }
    @Test void oneLabelHaveLegibleTransparentUnclippedGlyphs() throws Exception {
        for(String trait:new String[]{"swashbuckler"}) {
            var image=ImageIO.read(Path.of("src/main/resources/assets/destiny/textures/item/hud/perk_"+trait+"_w110.png").toFile());
            assertEquals(118,image.getWidth());assertEquals(24,image.getHeight());int visible=0,antialias=0;
            for(int y=0;y<24;y++)for(int x=0;x<118;x++) {
                int rgba=image.getRGB(x,y),alpha=rgba>>>24;assertEquals(0xffffff,rgba&0xffffff);
                if(alpha>0)visible++;if(alpha>0&&alpha<255)antialias++;
                if(x==0||x==117||y==0||y==23)assertEquals(0,alpha);
            }
            assertTrue(visible>500&&visible<1900);assertTrue(antialias>100);
        }
    }
}
