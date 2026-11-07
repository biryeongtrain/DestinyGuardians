package kim.biryeong.destiny.strike.devils;

import com.google.gson.JsonParser;
import kim.biryeong.destiny.sound.EnemySoundMix;
import org.junit.jupiter.api.Test;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import static org.junit.jupiter.api.Assertions.*;

class DevilsCombatSoundsTest {
    @Test void everyEnemyHasAShippedDeathSoundIncludingHive() throws Exception {
        for(var kind:DevilsPlan.Kind.values()) {
            var id=DevilsCombatSounds.event(kind,"death");
            assertNotNull(id,kind.name());
            try(var in=getClass().getResourceAsStream("/assets/"+id.getNamespace()+"/sounds.json")) {
                assertNotNull(in,id.toString());
                var sounds=JsonParser.parseReader(new InputStreamReader(in,StandardCharsets.UTF_8)).getAsJsonObject();
                assertTrue(sounds.has(id.getPath()),id.toString());
            }
        }
    }
    @Test void deathAndPainStayBelowTheQuieterCombatMix() {
        assertEquals(.35f,EnemySoundMix.volume("death"));
        assertTrue(EnemySoundMix.volume("hurt")<EnemySoundMix.volume("death"));
        for(var event:new String[]{"death","hurt","impact","fire","charge"}) {
            assertTrue(EnemySoundMix.volume(event)>0);
            assertTrue(EnemySoundMix.volume(event)<=.55f);
        }
    }
}
