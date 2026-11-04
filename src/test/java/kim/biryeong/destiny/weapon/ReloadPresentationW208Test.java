package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import java.io.StringReader;
import java.nio.file.*;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class ReloadPresentationW208Test {
    static final Path A=Path.of("src/main/resources/assets/destiny");
    @BeforeAll static void bootstrap(){
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
    }
    @Test void actual263CuboidParserAcceptsFiveBanks()throws Exception {
        for(String id:List.of("the_recluse","beloved","gnawing_hunger","austringer","first_in_last_out")) {
            String folder=(id.equals("first_in_last_out")?"weapon_insert":"weapon_reload")+"_w208_"+id;
            try(var files=Files.list(A.resolve("models/"+folder))) {
                for(var p:files.toList()) assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(p))),p.toString());
            }
        }
    }
    @Test void liveReloadRoutesResolveToDenseBanks()throws Exception {
        for(String id:List.of("the_recluse","beloved","gnawing_hunger","austringer")) {
            var entry=WeaponCatalog.find(id).orElseThrow();
            String key="weapon_reload_w208_"+id+"/"+id;
            assertEquals("destiny:"+key,WeaponReloadPresentation.model(entry).toString());
            var graph=JsonParser.parseString(Files.readString(A.resolve("items/"+key+".json")));
            assertDenseDispatch(graph,1,61);
        }
    }
    static void assertDenseDispatch(com.google.gson.JsonElement value,int index,int entries) {
        boolean found=findDenseDispatch(value,index,entries);
        assertTrue(found,"Missing dense progress dispatch");
    }
    static boolean findDenseDispatch(com.google.gson.JsonElement v,int index,int entries) {
        if(v.isJsonArray()) {for(var c:v.getAsJsonArray())if(findDenseDispatch(c,index,entries))return true;}
        if(v.isJsonObject()) {
            var o=v.getAsJsonObject();
            if(o.has("type") && o.get("type").getAsString().equals("minecraft:range_dispatch")
                    && o.has("index") && o.get("index").getAsInt()==index) {
                var samples=o.getAsJsonArray("entries");assertEquals(entries,samples.size());
                float before=-1;
                for(var sample:samples) {float t=sample.getAsJsonObject().get("threshold").getAsFloat();assertTrue(t>before);before=t;}
                return true;
            }
            for(var c:o.entrySet())if(findDenseDispatch(c.getValue(),index,entries))return true;
        }
        return false;
    }
    @Test void firstInLastOutUsesDenseRealInsertPhases()throws Exception {
        var e=WeaponCatalog.find("first_in_last_out").orElseThrow();
        assertTrue(WeaponInsertPresentation.supports(e));
        assertTrue(WeaponProfile.forEntry(e).shellReload());
        assertDenseDispatch(JsonParser.parseString(Files.readString(A.resolve("items/weapon_insert_w208_first_in_last_out/first_in_last_out.json"))),4,183);
        assertEquals("destiny:weapon_insert_w208_first_in_last_out/first_in_last_out",WeaponInsertPresentation.model(e).toString());
    }
}
