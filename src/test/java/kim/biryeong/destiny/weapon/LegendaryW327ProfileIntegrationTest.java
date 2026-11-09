package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.nio.file.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Validates 24 new identities against separately pinned selected manifest evidence, not copied base stats. */
class LegendaryW327ProfileIntegrationTest {
    private static JsonObject source() throws Exception {
        return JsonParser.parseString(Files.readString(Path.of("art/weapons/w327/catalog-source.json"))).getAsJsonObject();
    }
    private static double solve(JsonObject c,int x) {
        return (c.has("evpp")?c.get("evpp").getAsDouble():0)*x*x
                +(c.has("vpp")?c.get("vpp").getAsDouble():0)*x+c.get("offset").getAsDouble();
    }
    @Test void exactTwentyFourHashesAndOwnOfficialStatsReachProductionProfiles() throws Exception {
        var evidence=source().getAsJsonArray("weapons"); assertEquals(24,evidence.size()); assertEquals(24,LegendaryWeapons.ids().size());
        Set<Long> hashes=new HashSet<>();
        for(var value:evidence) {
            var row=value.getAsJsonObject();var registry=row.getAsJsonObject("registry");String id=registry.get("id").getAsString();
            var entry=WeaponCatalog.find(id).orElseThrow();var actual=WeaponCharacteristics.of(entry);
            long hash=registry.get("bungie_hash").getAsLong(); assertTrue(hashes.add(hash)); assertEquals(hash,actual.bungieHash());
            var expected=row.getAsJsonObject("stats");assertEquals(expected.size(),actual.stats().size());
            for(var stat:expected.entrySet())assertEquals(stat.getValue().getAsJsonObject().get("value").getAsInt(),actual.stats().get(stat.getKey()),id+":"+stat.getKey());
            assertNotEquals(id,LegendaryWeapons.baseId(id));
            assertEquals(row.get("nameKo").getAsString(),LegendaryWeapons.name(id));
            assertEquals(entry.family().equals("sidearm")?.85:.75,WeaponAimMovementProfile.scalar(entry),1e-12,id);
        }
    }
    @Test void newHandlingAndAdsEvaluateOwnStatsAgainstHistoricalCoefficients() throws Exception {
        var formulas=JsonParser.parseString(Files.readString(Path.of("art/weapons/w46/weapon_formulas.json"))).getAsJsonObject();
        for(String id:LegendaryWeapons.ids()) {
            var entry=WeaponCatalog.find(id).orElseThrow();var mapping=LegendaryWeapons.field(id,"source").getAsJsonObject("formulaMapping");
            var c=formulas.getAsJsonObject(mapping.get("family").getAsString()).getAsJsonObject("cat").getAsJsonObject(mapping.get("category").getAsString()).getAsJsonObject("handling");
            int stat=WeaponCharacteristics.of(entry).stats().get("943549884");var h=WeaponHandlingProfile.of(entry);
            assertEquals(stat,h.handling());assertEquals((int)Math.ceil(solve(c.getAsJsonObject("ready"),stat)*20),h.readyTicks(),id);
            assertEquals((int)Math.ceil(Math.max(solve(c.getAsJsonObject("stow"),stat),solve(c.getAsJsonObject("stow"),100))*20),h.stowTicks(),id);
            assertEquals(Math.clamp((int)Math.ceil(solve(c.getAsJsonObject("ads"),stat)*20),2,20),WeaponAimProfile.of(entry).transitionTicks(),id);
        }
    }
    @Test void catalogEvidenceGettersCannotMutateRegisteredGameplayData() {
        var before=LegendaryWeapons.field("krait","characteristics");var copy=LegendaryWeapons.field("krait","characteristics");
        copy.getAsJsonObject("stats").addProperty("943549884",100);copy.addProperty("bungieHash",1);
        assertEquals(before,LegendaryWeapons.field("krait","characteristics"));
        assertThrows(UnsupportedOperationException.class,()->LegendaryWeapons.ids().clear());
    }
}
