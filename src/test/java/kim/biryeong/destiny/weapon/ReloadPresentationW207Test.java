package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import java.io.StringReader;
import java.nio.file.*;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class ReloadPresentationW207Test {
    static final Path A=Path.of("src/main/resources/assets/destiny/models");
    static com.google.gson.JsonObject model(String key)throws Exception {
        return JsonParser.parseString(Files.readString(A.resolve(key+".json"))).getAsJsonObject();
    }
    @Test void actual263ParserAcceptsAllFourNewBanks()throws Exception {
        for(String folder:List.of("weapon_reload_w207_ammit_ar2","weapon_reload_w207_blast_furnace",
                "weapon_reload_w207_hammerhead","weapon_insert_w207_dust_rock_blues")) {
            try(var files=Files.list(A.resolve(folder))) {
                for(var p:files.toList()) assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(p))),p.toString());
            }
        }
    }
    @Test void dustKeepsHeldBodyAcrossShellLoopsAndRestoresAcceptedIdle()throws Exception {
        String prefix="weapon_insert_w207_dust_rock_blues/dust_rock_blues";
        assertTrue(WeaponInsertPresentation.supports(WeaponCatalog.find("dust_rock_blues").orElseThrow()));
        assertTrue(WeaponProfile.forEntry(WeaponCatalog.find("dust_rock_blues").orElseThrow()).shellReload());
        for(String grip:List.of("native","twohand")) {
            var held=model(prefix+"_initial_60_body_"+grip).get("display");
            assertEquals(held,model(prefix+"_loop_00_body_"+grip).get("display"));
            assertEquals(held,model(prefix+"_loop_60_body_"+grip).get("display"));
            assertEquals(held,model(prefix+"_return_00_body_"+grip).get("display"));
            assertEquals(model(prefix+"_initial_00_body_"+grip).get("display"),model(prefix+"_return_60_body_"+grip).get("display"));
            assertNotEquals(model(prefix+"_loop_30_shell_"+grip).get("parent"),model(prefix+"_loop_00_shell_"+grip).get("parent"));
        }
    }
}
