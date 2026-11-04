package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.nio.file.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ZenMomentW188Test {
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    @Test void exactTenCanonicalBaseSocketsAndNoEnhanced() {
        assertEquals("zen_moment", ZenMomentProfile.ID); assertEquals(2387244414L, ZenMomentProfile.HASH);
        assertEquals(11, ZenMomentProfile.rolls().size()); // W320: + Frontier Justice curated fixed roll
        var ids = new HashSet<String>();
        for (var roll : ZenMomentProfile.rolls()) {
            assertEquals(ZenMomentProfile.HASH, roll.perkHash()); assertTrue(ids.add(roll.id()));
            assertTrue(ZenMomentProfile.supports(entry(roll.id())));
            assertEquals(roll.hash(), WeaponCharacteristics.of(entry(roll.id())).bungieHash());
            assertFalse(WeaponCharacteristics.of(entry(roll.id())).exotic());
        }
        assertThrows(UnsupportedOperationException.class, () -> ZenMomentProfile.rolls().clear());
        assertFalse(ZenMomentProfile.supports(null)); assertFalse(ZenMomentProfile.supports(entry("hollow_words")));
        var e = entry("austringer");
        assertFalse(ZenMomentProfile.supports(new WeaponCatalog.Entry(e.id(), "auto_rifle", e.frame(), e.name(), e.source_frame_label(), e.item_model())));
    }
    @Test void weightsPreserveFractionalPulseSidearmAndOther() {
        for (String id : List.of("duke_mk_44", "austringer", "distant_relation")) assertEquals(4, ZenMomentProfile.hitUnits(entry(id)));
        for (String id : List.of("cold_denial", "blast_furnace", "lonesome", "dead_man_walking_xx7463")) assertEquals(3, ZenMomentProfile.hitUnits(entry(id)));
        for (String id : List.of("gnawing_hunger", "bug_out_bag", "retrofit_escapade")) assertEquals(2, ZenMomentProfile.hitUnits(entry(id)));
        assertEquals(0, ZenMomentProfile.hitUnits(null)); assertEquals(0, ZenMomentProfile.hitUnits(entry("hollow_words")));
    }
    @Test void familyHitCountsReachBoundedCapWithoutTruncation() {
        for (int increment : new int[]{2,3,4}) {
            var c = new ZenMomentCycle();
            for (int i = 1; i <= 12; i++) {
                assertTrue(c.confirmed(i, increment, 1));
                assertEquals(Math.min(10, i * increment), c.stackUnits(i));
            }
        }
    }
    @Test void oneSecondRefreshAtCapAndExactDeadline() {
        var c = new ZenMomentCycle();
        assertEquals(0, c.stackUnits(0)); assertEquals(1, c.flinchScalar(0));
        c.confirmed(0, 3, 1); assertEquals(3, c.stackUnits(0)); assertEquals(20, c.remaining(0));
        assertEquals(1, c.remaining(19)); assertEquals(0, c.stackUnits(20));
        c.confirmed(20, 4, 1); assertEquals(4, c.stackUnits(20));
        c.confirmed(21, 4, 1); c.confirmed(22, 4, 1); assertEquals(10, c.stackUnits(22));
        c.confirmed(41, 4, 1); assertEquals(20, c.remaining(41));
        assertEquals(10, c.stackUnits(60)); assertEquals(0, c.stackUnits(61));
        c.confirmed(62, 2, 1); assertEquals(2, c.stackUnits(62));
    }
    @Test void failedDamageAndInvalidIncrementCannotRefresh() {
        var c = new ZenMomentCycle(); c.confirmed(0, 2, 1);
        for (float bad : new float[]{0,-1,Float.NaN,Float.POSITIVE_INFINITY,Float.NEGATIVE_INFINITY}) assertFalse(c.confirmed(19, 2, bad));
        for (int bad : new int[]{Integer.MIN_VALUE,-1,0,1,5,Integer.MAX_VALUE}) assertFalse(c.confirmed(19,bad,1));
        assertEquals(1,c.remaining(19)); assertEquals(0,c.remaining(20));
    }
    @Test void readsDoNotRefreshAndTimeRollbackOrOverflowIsInert() {
        var c = new ZenMomentCycle(); c.confirmed(100, 2, 1);
        assertEquals(0,c.remaining(99)); assertEquals(0,c.remaining(-1));
        for(int i=0;i<100;i++) { assertEquals(2,c.stackUnits(119)); assertEquals(.9f,c.flinchScalar(119),.00001); }
        assertFalse(c.confirmed(Long.MAX_VALUE, 2, 1)); assertFalse(c.confirmed(-1,2,1));
        assertEquals(0,c.remaining(120));
        c.confirmed(0,2,1); assertEquals(2,c.stackUnits(0));
        var edge = new ZenMomentCycle(); assertTrue(edge.confirmed(Long.MAX_VALUE-20,2,1));
        assertEquals(1,edge.remaining(Long.MAX_VALUE-1)); assertEquals(0,edge.remaining(Long.MAX_VALUE));
    }
    @Test void authoredFlinchMappingBoundedAndInvalidUnitsNeutral() {
        for(int units=0;units<=10;units++) assertEquals(1-.05f*units,ZenMomentProfile.flinchScalar(units),.00001);
        assertEquals(1,ZenMomentProfile.flinchScalar(-1)); assertEquals(1,ZenMomentProfile.flinchScalar(11));
        assertEquals(.5f,ZenMomentProfile.flinchScalar(10));
    }
    @Test void resourceStrictlyPinsTypesExactSocketsAndHonestUnknowns() throws Exception {
        String raw = Files.readString(Path.of("src/main/resources/destiny/weapons/w188-zen_moment.json"));
        ZenMomentProfile.validateResource(raw);
        var root = JsonParser.parseString(raw).getAsJsonObject(); var perk = root.getAsJsonObject("perk");
        for(String key:List.of("originalCapVerified","originalFlinchMappingVerified","originalExpiryAggregationVerified","visualShakeImplemented","hudProcRow")) assertFalse(perk.get(key).getAsBoolean());
        assertEquals(0,perk.get("stabilityBonus").getAsInt()); assertEquals(1,perk.get("actualRecoilScalar").getAsDouble());
        for(String changed:List.of(raw.replace("2387244414","1748774930"),raw.replace("maxStackUnits", "maxStacks"),raw.replace("0.1", "0.2"),raw.replace("false", "true"),raw.replace("W188", "W187")))
            assertThrows(IllegalStateException.class,()->ZenMomentProfile.validateResource(changed));
    }
    @Test void fullOfficialScanRecordsAll65WithTenAcceptedBaseRandomizedPools() throws Exception {
        var root=JsonParser.parseString(Files.readString(Path.of("art/weapons/w188/zen_moment/official-sockets.json"))).getAsJsonObject();
        assertEquals(65,root.get("selectedCount").getAsInt()); assertEquals(65,root.getAsJsonArray("scans").size());
        assertEquals(10,root.getAsJsonArray("rolls").size());
        for(var row:root.getAsJsonArray("proofs")) {
            var proof=row.getAsJsonObject();var pool=proof.getAsJsonObject("pool");
            assertFalse(pool.get("isFakePlugSet").getAsBoolean()); assertTrue(proof.getAsJsonObject("matchingEntry").get("currentlyCanRoll").getAsBoolean());
            assertEquals(2387244414L,proof.getAsJsonObject("matchingEntry").get("plugItemHash").getAsLong());
            assertEquals(proof.get("plugSetHash"),proof.getAsJsonObject("socketEntry").get("randomizedPlugSetHash"));
        }
    }
}
