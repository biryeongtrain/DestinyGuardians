package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class KillClipProfileTest {
    private static JsonObject json(String file) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(file))).getAsJsonObject();
    }
    @Test void thirteenExactSelectedBaseTraitSocketsMatchOfficialEvidenceIncludingOneFixedInitialTrait() throws Exception {
        var evidence=json("art/weapons/w61/references/socket-pools.json");
        var rolls=KillClipProfile.rolls();assertEquals(13,rolls.size());
        assertEquals(13,rolls.stream().map(WeaponPerks.Roll::id).distinct().count());
        assertEquals(63,evidence.get("selectedCount").getAsInt());assertEquals(12,evidence.get("randomizedPoolRows").getAsInt());
        assertEquals(1,evidence.get("fixedDirectRows").getAsInt());
        var seen=new HashSet<String>();int fixed=0;
        for(var item:evidence.getAsJsonArray("weapons")) {
            var row=item.getAsJsonObject();var socket=row.getAsJsonObject("socketEntry");
            var roll=rolls.stream().filter(r->r.id().equals(row.get("id").getAsString())&&r.socket()==row.get("socket").getAsInt()).findFirst().orElseThrow();
            assertTrue(seen.add(roll.id()+":"+roll.socket()));
            assertEquals(roll.hash(),row.get("hash").getAsLong());assertEquals(roll.plugSetHash(),row.get("plugSetHash").getAsLong());
            assertEquals(KillClipProfile.HASH,roll.perkHash());assertEquals(4241085061L,row.get("socketCategoryHash").getAsLong());
            var entry=WeaponCatalog.find(roll.id()).orElseThrow();var meta=WeaponCharacteristics.of(entry);
            assertEquals(meta.bungieHash(),roll.hash());assertFalse(meta.exotic());assertNotEquals("sword",entry.family());
            if(row.get("selection").getAsString().equals("fixedInitialTrait")) {
                fixed++;assertEquals("antiope_d",roll.id());assertEquals(566976653L,roll.hash());assertEquals(3,roll.socket());
                assertTrue(row.get("isFakePlugSet").getAsBoolean());assertEquals(669L,roll.plugSetHash());
                assertEquals(KillClipProfile.HASH,socket.get("singleInitialItemHash").getAsLong());
                assertEquals(roll.plugSetHash(),socket.get("reusablePlugSetHash").getAsLong());
            } else {
                assertEquals("randomized",row.get("selection").getAsString());assertFalse(row.get("isFakePlugSet").getAsBoolean());
                assertEquals(roll.plugSetHash(),socket.get("randomizedPlugSetHash").getAsLong());
                assertTrue(row.getAsJsonObject("plugSetItem").get("currentlyCanRoll").getAsBoolean());
                assertEquals(KillClipProfile.HASH,row.getAsJsonObject("plugSetItem").get("plugItemHash").getAsLong());
            }
        }
        assertEquals(1,fixed);assertEquals(rolls.size(),seen.size());assertThrows(UnsupportedOperationException.class,()->rolls.clear());
    }
    @Test void damageAndRefreshAreOfficialButTimingAndStowAreCommunityAndPoliciesStayExplicit() throws Exception {
        var evidence=json("art/weapons/w61/references/mechanics.json");var p=KillClipProfile.perk();
        assertEquals(1.25f,p.multiplier());assertEquals(72,p.killWindowTicks());assertEquals(100,p.durationTicks());
        assertTrue(evidence.getAsJsonObject("primaryChange").get("primary").getAsBoolean());
        assertFalse(evidence.getAsJsonObject("communityMeasurements").get("primary").getAsBoolean());
        assertFalse(evidence.getAsJsonObject("enhancedComparison").get("implemented").getAsBoolean());
        assertEquals(p.killWindowTicks(),evidence.get("killWindowSeconds").getAsDouble()*20);
        assertEquals(p.durationTicks(),evidence.get("durationSeconds").getAsDouble()*20);
        assertEquals("unresolved",evidence.getAsJsonObject("stowRules").get("pendingKillWindow").getAsString());
        assertFalse(evidence.getAsJsonObject("reloadRules").getAsJsonObject("shotgunFirstShell").get("verified").getAsBoolean());
        assertTrue(KillClipProfile.rolls().stream().noneMatch(r->r.perkHash()==2923251173L));
    }
    @Test void socketOverlapIsExclusiveOnlyWhereActualOfficialSocketsCollide() {
        var overlap=new HashMap<String,Boolean>();
        for(var a:WeaponPerks.rolls())for(var b:KillClipProfile.rolls())if(a.id().equals(b.id()))overlap.put(a.id(),a.socket()==b.socket());
        assertEquals(Map.of("duke_mk_44",true,"gnawing_hunger",false,"dust_rock_blues",false,"bad_omens",false),overlap);
    }
}
