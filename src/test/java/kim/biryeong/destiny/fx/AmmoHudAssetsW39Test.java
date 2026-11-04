package kim.biryeong.destiny.fx;

import com.google.gson.*;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import org.junit.jupiter.api.Test;
import java.io.StringReader;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.HexFormat;
import static org.junit.jupiter.api.Assertions.*;

class AmmoHudAssetsW39Test {
    @Test void allGlyphsAndFamiliesDecodeWithNative26CodecAndManifestMatches() throws Exception {
        ItemModels.bootstrap(); ItemTintSources.bootstrap();
        var root=Path.of("src/main/resources/assets/destiny");
        var manifest=JsonParser.parseString(Files.readString(Path.of("art/hud/w39/manifest.json"))).getAsJsonObject();
        for(var entry:manifest.getAsJsonObject("sha256").entrySet()) {
            var path=Path.of(entry.getKey());
            assertEquals(entry.getValue().getAsString(),HexFormat.of().formatHex(
                    MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))));
        }
        var names=new java.util.HashSet<String>();
        names.add("ammo_panel");
        for(int i=0;i<10;i++)names.add("ammo_digit_"+i);
        for(var entry:WeaponCatalog.all())names.add("ammo_"+entry.family());
        assertEquals(29,names.size());
        for(String name:names) {
            var item=JsonParser.parseString(Files.readString(root.resolve("items/gui/hud/"+name+".json"))).getAsJsonObject();
            assertTrue(ItemModels.CODEC.parse(JsonOps.INSTANCE,item.get("model")).isSuccess(),name);
            assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(root.resolve("models/gui/hud/"+name+".json")))));
            assertTrue(Files.size(root.resolve("textures/item/hud/"+name+".png"))>90);
        }
    }
    @Test void goldenGunAimIsCloserToForwardAndLeftHandMirrored() throws Exception {
        var root=Path.of("src/main/resources/assets/destiny/models/mesh/h29/golden_gun_triangle.json");
        var display=JsonParser.parseString(Files.readString(root)).getAsJsonObject().getAsJsonObject("display");
        var right=display.getAsJsonObject("firstperson_righthand").getAsJsonArray("rotation");
        var left=display.getAsJsonObject("firstperson_lefthand").getAsJsonArray("rotation");
        assertTrue(Math.abs(180+right.get(1).getAsDouble())<28);
        assertTrue(Math.abs(right.get(0).getAsDouble())<24);
        assertEquals(-right.get(1).getAsDouble(),left.get(1).getAsDouble());
        assertEquals(right.get(0),left.get(0));
        assertEquals(JsonParser.parseString(Files.readString(Path.of("src/main/resources/assets/destiny/models/item/golden_gun_h29.json")))
                .getAsJsonObject().get("display"),display);
    }
}
