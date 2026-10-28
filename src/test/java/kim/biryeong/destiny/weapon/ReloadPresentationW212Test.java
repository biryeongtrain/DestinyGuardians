package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import java.io.StringReader;
import java.nio.file.*;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class ReloadPresentationW212Test {
    static final Path A=Path.of("src/main/resources/assets/destiny");
    static final List<String> IDS=List.of("antiope_d","bug_out_bag","cold_denial","bygones","lonesome","steelfeather_repeater","aishas_embrace","chattering_bone","halfdan_d","claws_of_the_wolf","bite_of_the_fox","retrofit_escapade","duke_mk_44","farewell","apostate","fixed_odds","distant_relation","patron_of_lost_causes","brass_attacks","ikelos_smg_v1_0_1","erentil_fr4","hollow_words","dream_breaker","null_composure","coriolis_force","line_in_the_sand","stormchaser","code_duello","bellowing_giant","bad_omens","allied_demand","dead_man_walking_xx7463","high_albedo","frontier_justice","retraced_path","edge_transit","canis_major","dimensional_hypotrochoid","deafening_whisper","salvager_s_salvo","pyroclastic_flow","seventh_seraph_officer_revolver");
    @BeforeAll static void bootstrap(){
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
    }
    @Test void actual263ParserAcceptsDensePartBanks()throws Exception {
        for(String id:IDS) try(var files=Files.list(A.resolve("models/"+WeaponReloadPresentation.model(WeaponCatalog.find(id).orElseThrow()).getPath().split("/")[0]))) {
            for(var p:files.toList()) assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(p))),p.toString());
        }
    }
    @Test void threeShotgunsUseDenseInitialLoopReturnBanks()throws Exception {
        for(String id:List.of("ikelos_sg_v1_0_1","mindbender_s_ambition_adept","parcel_of_stardust_fell_to_earth")) {
            var entry=WeaponCatalog.find(id).orElseThrow();
            assertTrue(WeaponProfile.forEntry(entry).shellReload());
            String key=WeaponInsertPresentation.model(entry).getPath();
            // Parcel closes the two unused inter-phase gaps with canonical
            // guards; these are separate from its3x61 animation poses.
            int dispatchEntries=id.equals("parcel_of_stardust_fell_to_earth")?185:183;
            ReloadPresentationW208Test.assertDenseDispatch(JsonParser.parseString(Files.readString(A.resolve("items/"+key+".json"))),4,dispatchEntries);
            try(var files=Files.list(A.resolve("models/"+key.split("/")[0]))) {
                for(var path:files.toList()) assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(path))),path.toString());
            }
        }
    }
    @Test void liveRoutesHaveAll61SamplesAndNativeArms()throws Exception {
        for(String id:IDS) {
            var entry=WeaponCatalog.find(id).orElseThrow();
            String key=WeaponReloadPresentation.model(entry).getPath();
            var graph=JsonParser.parseString(Files.readString(A.resolve("items/"+key+".json")));
            ReloadPresentationW208Test.assertDenseDispatch(graph,1,61);
            var route=JsonParser.parseString(Files.readString(Path.of("src/main/resources/destiny/weapons/w201-first-person-hands.json"))).getAsJsonObject().getAsJsonObject("models");
            assertTrue(route.has("destiny:"+key));
            assertTrue(Files.isRegularFile(A.resolve("items/"+route.get("destiny:"+key).getAsString().split(":",2)[1]+".json")));
        }
    }
}
