package kim.biryeong.destiny.sound;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import static org.junit.jupiter.api.Assertions.*;

class HiveDeathAssetsW344Test {
    @Test void fourSpeciesHaveSeparateSoftAndHardPoolsWithThirtySixMonoVariants() throws Exception {
        try(var in=getClass().getResourceAsStream("/assets/destiny_hive_death/sounds.json")) {
            assertNotNull(in);
            var sounds=JsonParser.parseReader(new InputStreamReader(in,StandardCharsets.UTF_8)).getAsJsonObject();
            assertEquals(8,sounds.size());var files=new HashSet<String>();
            for(var unit:new String[]{"thrall","trooper","knight","wizard"}) for(var style:new String[]{"soft","hard"}) {
                var variants=sounds.getAsJsonObject("death."+unit+"."+style).getAsJsonArray("sounds");
                assertEquals(style.equals("soft")?5:4,variants.size());
                for(var value:variants) {
                    var row=value.getAsJsonObject();var name=row.get("name").getAsString();assertTrue(files.add(name));
                    assertEquals(40,row.get("attenuation_distance").getAsInt());
                    try(var ogg=getClass().getResourceAsStream("/assets/destiny_hive_death/sounds/"+name.split(":")[1]+".ogg")) {
                        assertNotNull(ogg,name);var head=ogg.readNBytes(44);
                        assertEquals("OggS",new String(head,0,4,StandardCharsets.US_ASCII));assertEquals(1,head[39]);
                    }
                }
            }
            assertEquals(36,files.size());
        }
    }
    @Test void normalDeathsUseSpeciesSoftEventsWithoutClaimingPrecisionOnly() throws Exception {
        try(var in=getClass().getResourceAsStream("/destiny/devils_lair/combat-sound-routes.json")) {
            var root=JsonParser.parseReader(new InputStreamReader(in,StandardCharsets.UTF_8)).getAsJsonObject();
            var routes=root.getAsJsonObject("routes");var units=new String[][]{{"THRALL","thrall"},{"ACOLYTE","trooper"},{"KNIGHT","knight"},{"WIZARD","wizard"}};
            for(var unit:units) {
                var events=routes.getAsJsonObject(unit[0]);
                assertEquals("destiny_hive_death:death."+unit[1]+".soft",events.get("death").getAsString());
                assertEquals("destiny_hive_death:death."+unit[1]+".hard",events.get("death_hard").getAsString());
                assertFalse(root.getAsJsonObject("approximations").has(unit[0]+".death"));
            }
            var policy=root.getAsJsonObject("hive_death_policy");
            assertFalse(policy.get("headshot_only_confirmed").getAsBoolean());
            assertFalse(policy.get("soft_hard_equals_body_headshot").getAsBoolean());
            assertEquals(.35f,EnemySoundMix.volume("death"));assertEquals(.35f,EnemySoundMix.volume("death_hard"));
        }
    }
}
