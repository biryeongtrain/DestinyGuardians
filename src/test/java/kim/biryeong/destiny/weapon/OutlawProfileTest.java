package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class OutlawProfileTest {
    /** Historical source assertions remain frozen; new identities require exact official tuples. */
    private static java.util.List<WeaponPerks.Roll> legacyRolls() {
        var all = OutlawProfile.rolls();
        var added = all.stream().filter(r -> LegendaryWeapons.contains(r.id())).toList();
        assertEquals(java.util.Set.of("heritage", "trustee"), added.stream().map(WeaponPerks.Roll::id)
            .collect(java.util.stream.Collectors.toSet()));
        for (var roll : added) assertTrue(LegendaryWeapons.exactRoll(roll), roll.toString());
        assertEquals(all.size(), new java.util.HashSet<>(all).size());
        return all.stream().filter(r -> !LegendaryWeapons.contains(r.id())).toList();
    }

    private static JsonObject json(String file) throws Exception {return JsonParser.parseString(Files.readString(Path.of(file))).getAsJsonObject();}
    @Test void exactThirteenOfficialSocketsIncludeTwelveRandomPoolsAndOneExplicitFixedInitialTrait() throws Exception {
        var proof=json("art/weapons/w62/references/socket-pools.json");var rolls=legacyRolls();
        assertEquals(13,rolls.size());assertEquals(13,rolls.stream().map(WeaponPerks.Roll::id).distinct().count());
        assertEquals(63,proof.get("selectedCount").getAsInt());assertEquals(12,proof.get("randomizedPoolRows").getAsInt());assertEquals(1,proof.get("fixedDirectRows").getAsInt());
        assertEquals(0,proof.getAsJsonArray("duplicateBaseSelectedOptions").size());var seen=new HashSet<String>();int fixed=0;
        for(var e:proof.getAsJsonArray("weapons")) {
            var row=e.getAsJsonObject();var socket=row.getAsJsonObject("socketEntry");
            var match=rolls.stream().filter(x->x.id().equals(row.get("id").getAsString())&&x.socket()==row.get("socket").getAsInt()).findFirst().orElseThrow();
            assertTrue(seen.add(match.id()+":"+match.socket()));assertEquals(row.get("hash").getAsLong(),match.hash());
            assertEquals(row.get("plugSetHash").getAsLong(),match.plugSetHash());assertEquals(OutlawProfile.HASH,match.perkHash());
            var entry=WeaponCatalog.find(match.id()).orElseThrow();assertEquals(WeaponCharacteristics.of(entry).bungieHash(),match.hash());
            assertFalse(WeaponCharacteristics.of(entry).exotic());assertNotEquals("sword",entry.family());assertEquals(4241085061L,row.get("socketCategoryHash").getAsLong());
            if(row.get("selection").getAsString().equals("fixedInitialTrait")) {
                fixed++;assertEquals("halfdan_d",match.id());assertEquals(650L,match.plugSetHash());assertTrue(row.get("isFakePlugSet").getAsBoolean());
                assertEquals(OutlawProfile.HASH,socket.get("singleInitialItemHash").getAsLong());assertEquals(match.plugSetHash(),socket.get("reusablePlugSetHash").getAsLong());
            } else {
                assertEquals("randomized",row.get("selection").getAsString());assertFalse(row.get("isFakePlugSet").getAsBoolean());
                assertEquals(match.plugSetHash(),socket.get("randomizedPlugSetHash").getAsLong());
                assertTrue(row.getAsJsonArray("matchingEntries").asList().stream().map(JsonElement::getAsJsonObject)
                        .map(x->x.getAsJsonObject("item")).anyMatch(x->x.get("currentlyCanRoll").getAsBoolean()&&x.get("plugItemHash").getAsLong()==OutlawProfile.HASH));
            }
        }
        assertEquals(1,fixed);assertEquals(13,seen.size());assertThrows(UnsupportedOperationException.class,()->rolls.clear());
    }
    @Test void reloadUsesModifiedCappedStatAndScalarBeforeRoundingInsteadOfOnlyMultiplyingOldTicks() throws Exception {
        var evidence=json("art/weapons/w62/references/reload-timings.json");int checked=0;
        for(var e:evidence.getAsJsonArray("entries")) {
            var row=e.getAsJsonObject();var entry=WeaponCatalog.find(row.get("id").getAsString()).orElseThrow();var actual=OutlawProfile.reload(entry);
            int original=WeaponCharacteristics.of(entry).stats().get("4188031367"),effective=Math.min(100,original+70);
            assertEquals(original,actual.baseReloadStat());assertEquals(effective,actual.effectiveReloadStat());
            var curve=row.getAsJsonObject("curve");
            double seconds=.9*(curve.get("evpp").getAsDouble()*effective*effective+curve.get("vpp").getAsDouble()*effective+curve.get("offset").getAsDouble());
            int expected=(int)Math.ceil(seconds*20);assertEquals(expected,actual.firstTicks());assertEquals(expected,actual.intervalTicks());
            assertTrue(expected<WeaponProfile.forEntry(entry).reloadTicks());checked++;
        }
        assertEquals(13,checked);var duke=OutlawProfile.reload(WeaponCatalog.find("duke_mk_44").orElseThrow());assertEquals(33,duke.firstTicks());
        assertNotEquals((int)Math.ceil(WeaponProfile.forEntry(WeaponCatalog.find("duke_mk_44").orElseThrow()).reloadTicks()*.9),duke.firstTicks());
    }
    @Test void officialBonusHistoryCommunityDurationAndUnsettledPoliciesAreNotConflated() throws Exception {
        var proof=json("art/weapons/w62/references/mechanics.json");var p=OutlawProfile.perk();
        assertEquals(120,p.durationTicks());assertEquals(70,p.reloadBonus());assertEquals(.9,p.durationMultiplier());
        assertEquals(50,proof.getAsJsonArray("primaryHistory").get(0).getAsJsonObject().get("reloadBonusAfter").getAsInt());
        assertEquals(70,proof.getAsJsonArray("primaryHistory").get(1).getAsJsonObject().get("reloadBonusAfter").getAsInt());
        assertFalse(proof.getAsJsonObject("communityMeasurements").get("primary").getAsBoolean());
        assertFalse(proof.getAsJsonObject("enhancedComparison").get("implemented").getAsBoolean());
        assertFalse(proof.getAsJsonObject("animationSnapshot").get("verifiedDestinyBehavior").getAsBoolean());
        assertFalse(proof.getAsJsonObject("mixedPelletPrecision").get("verified").getAsBoolean());
        assertTrue(legacyRolls().stream().noneMatch(r->r.perkHash()==1347741687L||r.perkHash()==1528281896L));
        assertThrows(IllegalArgumentException.class,()->OutlawProfile.reload(WeaponCatalog.find("bad_omens").orElseThrow()));
    }
}
