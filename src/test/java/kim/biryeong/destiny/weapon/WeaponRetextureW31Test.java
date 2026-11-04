package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import javax.imageio.ImageIO;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class WeaponRetextureW31Test {
    private static final Path ART=Path.of("art/weapons/w31");
    private static JsonElement read(Path p) throws Exception {
        return JsonParser.parseString(Files.readString(p));
    }
    @Test void everyWeaponActuallyGainsGeometryWithinTheNewBudgetWithoutChangingHeldPoses() throws Exception {
        var before=read(ART.resolve("baseline.json")).getAsJsonArray();
        assertEquals(63,before.size());
        for(var value:before) {
            var old=value.getAsJsonObject();String id=old.get("id").getAsString();
            var bb=read(Path.of("art/blockbench/weapons/w30/"+id+".bbmodel")).getAsJsonObject();
            int cubes=bb.getAsJsonArray("elements").size();
            assertTrue(cubes>old.get("cubes").getAsInt() && cubes<=256,id);
            assertEquals(old.get("source_files"),bb.getAsJsonObject("destiny_w30").get("source_files"),id);
            var row=WeaponCatalog.find(id).orElseThrow();
            for(String state:List.of("hip","ads","inspect")) {
                String suffix=state.equals("hip")?"":"_"+state;
                var model=read(Path.of("src/main/resources/assets/destiny/models/weapon/"+row.family()+"/"+id+suffix+".json")).getAsJsonObject();
                var expected=old.getAsJsonObject("displays").getAsJsonObject(state).deepCopy();
                if(row.family().equals("glaive")) {
                    var w37=read(Path.of("art/weapons/w37/firstperson-poses.json")).getAsJsonObject()
                            .getAsJsonObject("poses").get(state);
                    expected.add("firstperson_righthand",w37.deepCopy());
                    expected.add("firstperson_lefthand",w37.deepCopy());
                }
                // W156 changes only Ammit native third-person rotation; all other fields stay frozen.
                if (id.equals("ammit_ar2")) for (String hand : List.of("thirdperson_righthand", "thirdperson_lefthand")) {
                    var rotation=read(Path.of("art/weapons/w156/ammit-pose.json")).getAsJsonObject()
                            .getAsJsonObject("rotations").get("native");
                    assertEquals(JsonParser.parseString("[72,0,0]"), rotation);
                    expected.getAsJsonObject(hand).add("rotation", rotation.deepCopy());
                }
                assertEquals(expected,model.get("display"),id+" "+state+" pose drift outside reviewed W37 first-person / W156 Ammit rotation overrides");
            }
        }
    }
    @Test void embeddedTexturesMatchRuntimeAndCarryExplicitDyeBakeProvenance() throws Exception {
        for(var entry:WeaponCatalogTest.originalW30Entries()) {
            var bb=read(Path.of("art/blockbench/weapons/w30/"+entry.id()+".bbmodel")).getAsJsonObject();
            var bake=bb.getAsJsonObject("destiny_w31");
            assertEquals("saved_default_shader_graph_pure_dye_albedo_v2",bake.get("method").getAsString());
            assertEquals("sRGB",bake.get("color_space").getAsString());
            assertEquals(14,bake.get("pixels_per_model_unit").getAsInt());
            var texture=bb.getAsJsonArray("textures").get(0).getAsJsonObject();
            var embedded=Base64.getDecoder().decode(texture.get("source").getAsString().split(",",2)[1]);
            var runtime=Files.readAllBytes(Path.of("src/main/resources/assets/destiny/textures/item/weapon/w30/"+entry.id()+".png"));
            assertArrayEquals(embedded,runtime,entry.id());
            assertEquals(1024,texture.get("width").getAsInt());
            assertEquals(bb.getAsJsonObject("destiny_w30").get("texture_sha256").getAsString(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(runtime)));
            assertFalse(bake.getAsJsonObject("material_stats").isEmpty());
        }
    }
    @Test void allReferencesPinTheExactWeaponScreenshotAndItsDefaultDyeIdentity() throws Exception {
        var refs=read(ART.resolve("references.json")).getAsJsonArray();
        assertEquals(63,refs.size());Set<String> ids=new HashSet<>();
        for(var value:refs) {
            var r=value.getAsJsonObject();String id=r.get("id").getAsString(),hash=r.get("bungie_hash").getAsString();
            assertTrue(ids.add(id));assertTrue(WeaponCatalog.find(id).isPresent());
            assertEquals("https://www.light.gg/db/items/"+hash+"/",r.get("lightgg").getAsString());
            assertEquals("https://www.bungie.net/common/destiny2_content/screenshots/"+hash+".jpg",r.get("screenshot").getAsString());
            assertEquals(64,r.get("sha256").getAsString().length());
            assertEquals(3,r.getAsJsonArray("default_dyes").size(),id);
        }
    }
    @Test void knownDyeChannelsRemainVisibleAndMissingLookupDoesNotBakeMagenta() throws Exception {
        for(String id:List.of("duke_mk_44","austringer","hammerhead","retrofit_escapade")) {
            var image=ImageIO.read(Path.of("src/main/resources/assets/destiny/textures/item/weapon/w30/"+id+".png").toFile());
            int used=0,blue=0,gold=0,red=0,magenta=0;
            for(int y=0;y<image.getHeight();y++)for(int x=0;x<image.getWidth();x++) {
                int p=image.getRGB(x,y);if((p>>>24)==0)continue;used++;
                int r=(p>>16)&255,g=(p>>8)&255,b=p&255;
                if(b>r*1.25 && b>g*1.1 && b>40)blue++;
                if(r>g*1.05 && g>b*1.2 && r>60)gold++;
                if(r>g*1.3 && r>b*1.3 && r>50)red++;
                if(r>220 && b>220 && g<25)magenta++;
            }
            assertTrue(used>10000,id);
            if(id.equals("duke_mk_44"))assertTrue(blue>used*.01,"Screenshot blue lacquer missing");
            if(id.equals("austringer"))assertTrue(gold>used*.01,"Gold dye missing");
            if(id.equals("hammerhead"))assertTrue(red>used*.005,"Red accent missing");
            if(id.equals("retrofit_escapade"))assertTrue(magenta<used*.001,"Missing-image magenta baked into material");
        }
    }
}
