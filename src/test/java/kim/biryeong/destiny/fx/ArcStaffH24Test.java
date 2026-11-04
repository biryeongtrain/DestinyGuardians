package kim.biryeong.destiny.fx;

import com.google.gson.*;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import javax.imageio.ImageIO;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.Base64;
import java.util.HashSet;
import static org.junit.jupiter.api.Assertions.*;

/** Native parser and saved geometry contracts; real equipment/contact/pixels are separate gates. */
class ArcStaffH24Test {
    private byte[] bytes(String path) throws Exception {
        try (var in = getClass().getResourceAsStream("/assets/destiny/" + path)) {
            assertNotNull(in, path); return in.readAllBytes();
        }
    }
    private JsonObject resource(String path) throws Exception {
        return JsonParser.parseString(new String(bytes(path), StandardCharsets.UTF_8)).getAsJsonObject();
    }
    private JsonObject model() throws Exception { return resource("models/item/arc_staff_h24.json"); }
    private double axis(JsonObject e, String field, int a) { return e.getAsJsonArray(field).get(a).getAsDouble(); }

    @Test void resolvesThroughNativeParserAndPreservesBothGripAndDisplayFrame() throws Exception {
        var m = model(); assertNotNull(CuboidModel.fromStream(new StringReader(m.toString())));
        assertEquals(resource("models/item/arc_staff.json").get("display"), m.get("display"));
        assertEquals("destiny:item/arc_staff_h24", resource("items/arc_staff_h24.json")
                .getAsJsonObject("model").get("model").getAsString());
        var shaft = m.getAsJsonArray("elements").get(0).getAsJsonObject();
        assertEquals("continuous_silver_shaft_0", shaft.get("name").getAsString());
        for (double y : new double[]{8, 12}) {
            assertTrue(axis(shaft,"from",1) < y && axis(shaft,"to",1) > y);
            for(int a : new int[]{0,2}) assertEquals(8, (axis(shaft,"from",a)+axis(shaft,"to",a))/2,1e-9);
        }
    }

    @Test void longThinSymmetricSingleLanceEndsReplaceForksWithoutLosingDetail() throws Exception {
        var es = model().getAsJsonArray("elements");
        assertTrue(es.size() >= 200 && es.size() <= 300, "Detailed item display, bounded cuboid budget");
        int blades = 0, ribs = 0, ions = 0;
        double low = 100, high = -100;
        for(var v : es) {
            var e=v.getAsJsonObject(); String name=e.get("name").getAsString();
            assertFalse(name.contains("fork"), "One straight point per end, not fantasy forks");
            if(name.contains("lance_blade")) {
                blades++;
                assertEquals(8,(axis(e,"from",0)+axis(e,"to",0))/2,1e-9);
                assertEquals(8,(axis(e,"from",2)+axis(e,"to",2))/2,1e-9);
                if(name.endsWith("23")) assertTrue(axis(e,"to",0)-axis(e,"from",0) < .1);
            }
            if(name.contains("turned_rib")) ribs++;
            if(name.contains("ion_filament")) ions++;
            for(int a=0;a<3;a++) {
                assertTrue(Double.isFinite(axis(e,"from",a)) && Double.isFinite(axis(e,"to",a)));
                assertTrue(axis(e,"from",a) >= -16 && axis(e,"to",a) <= 32);
                assertTrue(axis(e,"from",a)<axis(e,"to",a));
            }
            low=Math.min(low,axis(e,"from",1));high=Math.max(high,axis(e,"to",1));
            assertTrue(axis(e,"to",0)-axis(e,"from",0) < 1.5, "Slender silhouette");
        }
        assertEquals(48,blades);assertEquals(44,ribs);assertEquals(16,ions);
        assertEquals(-16,low,1e-8);assertEquals(32,high,1e-8);
    }

    @Test void editableSourceMatchesNativeGeometryAndEmbedsTheExactOriginalAtlas() throws Exception {
        var bb=JsonParser.parseString(Files.readString(Path.of("art/blockbench/supers/arc_staff_h24.bbmodel"))).getAsJsonObject();
        var nativeModel=model();var nativeElements=nativeModel.getAsJsonArray("elements");var saved=bb.getAsJsonArray("elements");
        assertEquals(nativeElements.size(),saved.size());var ids=new HashSet<String>();
        for(int i=0;i<saved.size();i++) {
            var a=nativeElements.get(i).getAsJsonObject();var b=saved.get(i).getAsJsonObject();
            assertEquals(a.get("name"),b.get("name"));assertEquals(a.get("from"),b.get("from"));assertEquals(a.get("to"),b.get("to"));
            assertTrue(ids.add(b.get("uuid").getAsString()));
            for(var side:a.getAsJsonObject("faces").keySet()) {
                var uv=a.getAsJsonObject("faces").getAsJsonObject(side).getAsJsonArray("uv");
                var buv=b.getAsJsonObject("faces").getAsJsonObject(side).getAsJsonArray("uv");
                for(int k=0;k<4;k++) assertEquals(buv.get(k).getAsDouble(),uv.get(k).getAsDouble()*(k%2==0?16:8),1e-8);
            }
        }
        var texture=bytes("textures/item/supers/arc_staff_h24.png");
        assertArrayEquals(texture,Base64.getDecoder().decode(bb.getAsJsonArray("textures").get(0).getAsJsonObject().get("source").getAsString().split(",",2)[1]));
        var img=ImageIO.read(new ByteArrayInputStream(texture));assertEquals(256,img.getWidth());assertEquals(128,img.getHeight());
        for(var group:bb.getAsJsonArray("outliner")) for(var id:group.getAsJsonObject().getAsJsonArray("children"))
            assertTrue(ids.remove(id.getAsString()));
        assertTrue(ids.isEmpty(),"Every cube belongs to exactly one source group");
    }

    @Test void chargedSurfacesHaveValidUVsEmissionAndOnlyOwnTexture() throws Exception {
        var m=model();assertEquals("destiny:item/supers/arc_staff_h24",m.getAsJsonObject("textures").get("0").getAsString());
        for(var v:m.getAsJsonArray("elements")) {
            var e=v.getAsJsonObject();assertFalse(e.get("shade").getAsBoolean());
            assertTrue(e.get("light_emission").getAsInt()>=6 && e.get("light_emission").getAsInt()<=15);
            for(var f:e.getAsJsonObject("faces").asMap().values()) {
                assertEquals("#0",f.getAsJsonObject().get("texture").getAsString());
                for(var uv:f.getAsJsonObject().getAsJsonArray("uv")) assertTrue(uv.getAsDouble()>=0 && uv.getAsDouble()<=16);
            }
        }
    }
}
