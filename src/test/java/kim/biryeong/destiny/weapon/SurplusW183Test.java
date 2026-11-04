package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Pure production profile/catalog tests; standalone harness replaces only the outer perk
 * registry's Roll carrier to break its game-dependent registry cycle. No Minecraft claim.
 */
class SurplusW183Test {
    private static final Gson GSON = new Gson();
    private static final Set<String> EXPECTED = Set.of(
        "ammit_ar2:2119346509:3:1723759242",
        "high_albedo:1197486957:3:2797218184",
        "brass_attacks:2121785039:3:100135553",
        "biting_winds:1621657423:3:3968704963",
        "beloved:3107853529:3:1196545279",
        "apostate:2164448701:3:1306932196",
        "deafening_whisper:981718087:3:3110206796",
        "canis_major:2066434718:3:4037911937",
        "code_duello:2496242052:3:3719628667");
    static JsonElement read(String file) {
        var stream = SurplusW183Test.class.getResourceAsStream("/destiny/weapons/" + file);
        assertNotNull(stream, file);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) { return JsonParser.parseReader(reader); }
        catch (java.io.IOException e) { throw new AssertionError(e); }
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    @Test void exactBaseNineOfficialSocketIdentitiesNoFamilyGrant() {
        assertEquals("surplus", SurplusProfile.ID);
        assertEquals(3436462433L, SurplusProfile.HASH);
        var actual = new HashSet<String>();
        for (var r : SurplusProfile.rolls()) {
            assertEquals(3436462433L, r.perkHash());
            assertNotEquals(2658083589L, r.perkHash());
            assertTrue(actual.add(r.id()+":"+r.hash()+":"+r.socket()+":"+r.plugSetHash()));
            assertTrue(SurplusProfile.supports(entry(r.id())));
        }
        assertEquals(EXPECTED, actual);
        assertEquals(65, WeaponCatalog.all().size());
        assertEquals(9, WeaponCatalog.all().stream().filter(SurplusProfile::supports).count());
        assertFalse(SurplusProfile.supports(entry("cold_denial")));
        assertFalse(SurplusProfile.supports(entry("ace_of_spades")));
        assertThrows(UnsupportedOperationException.class, () -> SurplusProfile.rolls().clear());
    }
    @Test void canonicalIdentityEveryFieldAndNullFailClosed() {
        var e=entry("ammit_ar2");
        assertFalse(SurplusProfile.supports(null));
        var fields=new String[]{e.id(),e.family(),e.frame(),e.name(),e.source_frame_label(),e.item_model()};
        for(int i=0;i<fields.length;i++) {
            var copy=fields.clone();copy[i]="mutated";
            var bad=new WeaponCatalog.Entry(copy[0],copy[1],copy[2],copy[3],copy[4],copy[5]);
            assertFalse(SurplusProfile.supports(bad));
            assertThrows(IllegalArgumentException.class,()->SurplusProfile.reloadTicks(bad,18,1));
            copy=fields.clone();copy[i]=null;
            assertFalse(SurplusProfile.supports(new WeaponCatalog.Entry(copy[0],copy[1],copy[2],copy[3],copy[4],copy[5])));
        }
    }
    @Test void pinnedResourceRejectsMissingExtraEnhancedAndCurvePolicyMutations() {
        var source=read("w183-surplus.json").getAsJsonObject();
        assertDoesNotThrow(()->SurplusProfile.validateResource(source.toString()));
        for(String key:source.keySet()) {
            var x=source.deepCopy();x.remove(key);
            assertThrows(IllegalStateException.class,()->SurplusProfile.validateResource(x.toString()),key);
        }
        var extra=source.deepCopy();extra.addProperty("durationTicks",100);
        assertThrows(IllegalStateException.class,()->SurplusProfile.validateResource(extra.toString()));
        var enhanced=source.deepCopy();enhanced.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("perkHash",2658083589L);
        assertThrows(IllegalStateException.class,()->SurplusProfile.validateResource(enhanced.toString()));
        var curve=source.deepCopy();curve.getAsJsonArray("curves").get(0).getAsJsonObject().getAsJsonObject("reload").addProperty("offset",1);
        assertThrows(IllegalStateException.class,()->SurplusProfile.validateResource(curve.toString()));
        var policy=source.deepCopy();policy.getAsJsonObject("policies").addProperty("ads","APPLY_THREAT_SCALAR");
        assertThrows(IllegalStateException.class,()->SurplusProfile.validateResource(policy.toString()));
        for(String bad:List.of("null","[]","{}","not json")) assertThrows(IllegalStateException.class,()->SurplusProfile.validateResource(bad));
    }
    @Test void exactDistinctCompanionPairsAndSameSocketDenials() {
        var files=Map.of("snapshot","w68-snapshot.json","frenzy","w172-frenzy.json","adrenaline_junkie","w173-adrenaline-junkie.json",
            "perpetual_motion","w170-perpetual-motion.json","outlaw","w62-outlaw.json","feeding_frenzy","w108-feeding-frenzy.json",
            "rapid_hit","w169-rapid-hit.json","stats_for_all","w176-stats-for-all.json","threat_detector","w178-threat-detector.json","heating_up","w177-heating-up.json");
        var found=new HashSet<String>();
        for(var pair:files.entrySet()) {
            var data=read(pair.getValue()).getAsJsonObject();
            for(var value:data.getAsJsonArray(data.has("rolls")?"rolls":"weapons")) {
                var b=GSON.fromJson(value,WeaponPerks.Roll.class);
                for(var a:SurplusProfile.rolls()) if(a.id().equals(b.id())) {
                    boolean distinct=a.socket()!=b.socket();
                    assertEquals(distinct,SurplusProfile.compatible(entry(a.id()),pair.getKey(),b));
                    if(distinct) found.add(a.id()+":"+pair.getKey());
                    var forged=new WeaponPerks.Roll(b.id(),b.hash(),b.socket(),b.perkHash(),b.plugSetHash()+1);
                    assertFalse(SurplusProfile.compatible(entry(a.id()),pair.getKey(),forged));
                }
            }
        }
        assertEquals(Set.of("high_albedo:snapshot","biting_winds:snapshot","apostate:snapshot","deafening_whisper:snapshot","brass_attacks:frenzy","code_duello:frenzy","ammit_ar2:adrenaline_junkie","apostate:rapid_hit","deafening_whisper:threat_detector"),found);
    }
    @Test void reproduceEveryExistingBaselineAndShellTopology() {
        var timings=new HashMap<String,JsonObject>();var handling=new HashMap<String,JsonObject>();var aim=new HashMap<String,JsonObject>();
        for(var row:read("w46-timing.json").getAsJsonArray()) {var o=row.getAsJsonObject();timings.put(o.get("id").getAsString(),o.getAsJsonObject("timing"));}
        for(var row:read("w58-handling.json").getAsJsonArray()) {var o=row.getAsJsonObject();handling.put(o.get("id").getAsString(),o.getAsJsonObject("profile"));}
        for(var row:read("w44-aim.json").getAsJsonArray()) {var o=row.getAsJsonObject();aim.put(o.get("id").getAsString(),o.getAsJsonObject("profile"));}
        int shells=0;
        for(var roll:SurplusProfile.rolls()) {
            var e=entry(roll.id());var t=timings.get(e.id());var h=handling.get(e.id());
            boolean shell=t.get("shellReload").getAsBoolean();if(shell)shells++;
            assertEquals(t.get(shell?"reloadPerRoundTicks":"reloadTicks").getAsInt(),SurplusProfile.reloadTicks(e,0,1));
            assertEquals(h.get("readyTicks").getAsInt(),SurplusProfile.handlingTicks(e,0,1,true));
            assertEquals(h.get("stowTicks").getAsInt(),SurplusProfile.handlingTicks(e,0,1,false));
            assertEquals(aim.get(e.id()).get("transitionTicks").getAsInt(),SurplusProfile.adsTicks(e,0,false));
        }
        assertEquals(0,shells);
    }

    @Test void exactCurrentTierArraysAndInvalidCountsFailClosed() {
        for (int i=0;i<=3;i++) {
            assertEquals(new int[]{0,5,15,25}[i],SurplusProfile.stabilityBonus(i));
            assertEquals(new int[]{0,5,25,60}[i],SurplusProfile.handlingBonus(i));
            assertEquals(new int[]{0,10,25,60}[i],SurplusProfile.reloadBonus(i));
        }
        for(int bad:new int[]{Integer.MIN_VALUE,-1,4,Integer.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class,()->SurplusProfile.stabilityBonus(bad));
            assertThrows(IllegalArgumentException.class,()->SurplusProfile.handlingBonus(bad));
            assertThrows(IllegalArgumentException.class,()->SurplusProfile.reloadBonus(bad));
        }
    }
    @Test void allThirtySixWeaponTiersMatchFrozenHistoricalRawCurveOracle() {
        var rows=List.of(
            "ammit_ar2 0 8 8 7 41",
            "ammit_ar2 1 8 7 6 37",
            "ammit_ar2 2 7 6 6 33",
            "ammit_ar2 3 5 5 5 26",
            "high_albedo 0 6 7 5 36",
            "high_albedo 1 6 7 5 34",
            "high_albedo 2 5 6 4 31",
            "high_albedo 3 4 5 3 25",
            "brass_attacks 0 7 8 6 37",
            "brass_attacks 1 7 7 6 35",
            "brass_attacks 2 6 7 5 32",
            "brass_attacks 3 4 5 3 25",
            "biting_winds 0 12 10 9 16",
            "biting_winds 1 12 9 9 15",
            "biting_winds 2 11 9 8 14",
            "biting_winds 3 9 8 7 13",
            "beloved 0 8 7 9 62",
            "beloved 1 8 7 9 58",
            "beloved 2 7 6 8 53",
            "beloved 3 5 5 7 45",
            "apostate 0 7 7 8 54",
            "apostate 1 7 6 8 51",
            "apostate 2 6 6 7 47",
            "apostate 3 5 5 7 44",
            "deafening_whisper 0 8 7 8 42",
            "deafening_whisper 1 7 7 8 40",
            "deafening_whisper 2 6 6 7 37",
            "deafening_whisper 3 6 6 7 37",
            "canis_major 0 10 9 10 73",
            "canis_major 1 10 9 10 69",
            "canis_major 2 9 8 9 63",
            "canis_major 3 7 7 8 52",
            "code_duello 0 8 7 8 67",
            "code_duello 1 8 7 8 64",
            "code_duello 2 6 5 7 60",
            "code_duello 3 6 5 7 53");
        assertEquals(36,rows.size());
        for(String row:rows) {
            var v=row.split(" ");var e=entry(v[0]);int tier=Integer.parseInt(v[1]);
            int h=SurplusProfile.handlingBonus(tier),r=SurplusProfile.reloadBonus(tier);
            assertEquals(Integer.parseInt(v[2]),SurplusProfile.handlingTicks(e,h,1,true),row);
            assertEquals(Integer.parseInt(v[3]),SurplusProfile.handlingTicks(e,h,1,false),row);
            assertEquals(Integer.parseInt(v[4]),SurplusProfile.adsTicks(e,h,false),row);
            assertEquals(Integer.parseInt(v[5]),SurplusProfile.reloadTicks(e,r,1),row);
        }
    }
    @Test void allFortyTwoLegalCompanionTierCasesMatchFrozenOneRoundingOracle() {
        var rows=List.of(
            "ammit_ar2 adrenaline_junkie 1 1 25 10 1.0 1.0 false 7 6 6 37",
            "ammit_ar2 adrenaline_junkie 2 1 45 25 1.0 1.0 false 6 5 5 33",
            "ammit_ar2 adrenaline_junkie 3 1 80 60 1.0 1.0 false 5 5 5 26",
            "high_albedo snapshot 1 1 5 10 1.0 1.0 true 6 7 3 34",
            "high_albedo snapshot 2 1 25 25 1.0 1.0 true 5 6 2 31",
            "high_albedo snapshot 3 1 60 60 1.0 1.0 true 4 5 2 25",
            "brass_attacks frenzy 1 1 105 110 1.0 1.0 false 4 5 3 23",
            "brass_attacks frenzy 2 1 125 125 1.0 1.0 false 4 5 3 23",
            "brass_attacks frenzy 3 1 160 160 1.0 1.0 false 4 5 3 23",
            "biting_winds snapshot 1 1 5 10 1.0 1.0 true 12 9 5 15",
            "biting_winds snapshot 2 1 25 25 1.0 1.0 true 11 9 4 14",
            "biting_winds snapshot 3 1 60 60 1.0 1.0 true 9 8 4 13",
            "apostate snapshot 1 1 5 10 1.0 1.0 true 7 6 6 51",
            "apostate snapshot 2 1 25 25 1.0 1.0 true 6 6 6 47",
            "apostate snapshot 3 1 60 60 1.0 1.0 true 5 5 5 44",
            "apostate rapid_hit 1 1 5 15 1.0 0.99 false 7 6 8 49",
            "apostate rapid_hit 1 2 5 40 1.0 0.96 false 7 6 8 43",
            "apostate rapid_hit 1 3 5 45 1.0 0.95 false 7 6 8 42",
            "apostate rapid_hit 1 4 5 52 1.0 0.945 false 7 6 8 42",
            "apostate rapid_hit 1 5 5 70 1.0 0.92 false 7 6 8 41",
            "apostate rapid_hit 2 1 25 30 1.0 0.99 false 6 6 7 46",
            "apostate rapid_hit 2 2 25 55 1.0 0.96 false 6 6 7 43",
            "apostate rapid_hit 2 3 25 60 1.0 0.95 false 6 6 7 42",
            "apostate rapid_hit 2 4 25 67 1.0 0.945 false 6 6 7 42",
            "apostate rapid_hit 2 5 25 85 1.0 0.92 false 6 6 7 41",
            "apostate rapid_hit 3 1 60 65 1.0 0.99 false 5 5 7 44",
            "apostate rapid_hit 3 2 60 90 1.0 0.96 false 5 5 7 43",
            "apostate rapid_hit 3 3 60 95 1.0 0.95 false 5 5 7 42",
            "apostate rapid_hit 3 4 60 102 1.0 0.945 false 5 5 7 42",
            "apostate rapid_hit 3 5 60 120 1.0 0.92 false 5 5 7 41",
            "deafening_whisper snapshot 1 1 5 10 1.0 1.0 true 7 7 6 40",
            "deafening_whisper snapshot 2 1 25 25 1.0 1.0 true 6 6 6 37",
            "deafening_whisper snapshot 3 1 60 60 1.0 1.0 true 6 6 6 37",
            "deafening_whisper threat_detector 1 1 30 28 0.9 1.0 false 6 5 7 37",
            "deafening_whisper threat_detector 1 2 105 70 0.81 1.0 false 5 5 7 37",
            "deafening_whisper threat_detector 2 1 50 43 0.9 1.0 false 6 5 7 37",
            "deafening_whisper threat_detector 2 2 125 85 0.81 1.0 false 5 5 7 37",
            "deafening_whisper threat_detector 3 1 85 78 0.9 1.0 false 6 5 7 37",
            "deafening_whisper threat_detector 3 2 160 120 0.81 1.0 false 5 5 7 37",
            "code_duello frenzy 1 1 105 110 1.0 1.0 false 6 5 7 53",
            "code_duello frenzy 2 1 125 125 1.0 1.0 false 6 5 7 53",
            "code_duello frenzy 3 1 160 160 1.0 1.0 false 6 5 7 53");
        assertEquals(42,rows.size());
        for(String row:rows) {
            var v=row.split(" ");var e=entry(v[0]);
            int tier=Integer.parseInt(v[2]),companion=Integer.parseInt(v[3]);
            int h=Integer.parseInt(v[4]),r=Integer.parseInt(v[5]);
            double hs=Double.parseDouble(v[6]),rs=Double.parseDouble(v[7]);
            assertEquals(Integer.parseInt(v[9]),SurplusProfile.handlingTicks(e,h,hs,true),row);
            assertEquals(Integer.parseInt(v[10]),SurplusProfile.handlingTicks(e,h,hs,false),row);
            assertEquals(Integer.parseInt(v[11]),SurplusProfile.adsTicks(e,h,Boolean.parseBoolean(v[8])),row);
            assertEquals(Integer.parseInt(v[12]),SurplusProfile.reloadTicks(e,r,rs),row);
            if(v[1].equals("rapid_hit")) {
                var rapid=RapidHitProfile.reload(e,companion);
                assertEquals(rs,RapidHitProfile.durationMultiplier(companion));
                assertEquals(Integer.parseInt(v[12]),SurplusProfile.reloadTicks(e,
                    SurplusProfile.reloadBonus(tier)+rapid.effectiveReloadStat()-rapid.baseReloadStat(),rs));
            }
            if(v[1].equals("threat_detector")) {
                assertEquals(h,SurplusProfile.handlingBonus(tier)+ThreatDetectorProfile.handlingBonus(companion));
                assertEquals(r,SurplusProfile.reloadBonus(tier)+ThreatDetectorProfile.reloadBonus(companion));
                assertEquals(hs,ThreatDetectorProfile.handlingScalar(companion));
            }
        }
    }
    @Test void wideStatCapsBow85AndSingleRoundingWithCompanionScalar() {
        assertEquals(100,SurplusProfile.effectiveStat(99,Integer.MAX_VALUE));
        assertEquals(0,SurplusProfile.effectiveStat(99,Integer.MIN_VALUE));
        boolean differs=false;
        for(var roll:SurplusProfile.rolls()) {
            var e=entry(roll.id());
            assertEquals(SurplusProfile.reloadTicks(e,100,1),SurplusProfile.reloadTicks(e,Integer.MAX_VALUE,1));
            assertEquals(SurplusProfile.handlingTicks(e,100,.81,true),SurplusProfile.handlingTicks(e,Integer.MAX_VALUE,.81,true));
            assertEquals(SurplusProfile.adsTicks(e,100,false),SurplusProfile.adsTicks(e,Integer.MAX_VALUE,false));
            differs|=(int)Math.ceil(SurplusProfile.handlingTicks(e,25,1,true)*.81)!=SurplusProfile.handlingTicks(e,25,.81,true);
        }
        assertTrue(differs,"Detect multiplying already rounded ticks");
        // Biting Winds base reload28: bonus57 reaches cap85. Bonuses above it must stay equal.
        assertEquals(SurplusProfile.reloadTicks(entry("biting_winds"),57,1),SurplusProfile.reloadTicks(entry("biting_winds"),100,1));
        for(double bad:new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY,0,-1,1.0001}) {
            assertThrows(IllegalArgumentException.class,()->SurplusProfile.handlingTicks(entry("ammit_ar2"),25,bad,true));
            assertThrows(IllegalArgumentException.class,()->SurplusProfile.reloadTicks(entry("ammit_ar2"),25,bad));
        }
    }
    @Test void snapshotEntryOnlyAndNoInventedSurplusScalar() {
        for(String id:List.of("high_albedo","biting_winds","apostate","deafening_whisper")) {
            var e=entry(id);
            assertTrue(SurplusProfile.adsTicks(e,25,true)<=SurplusProfile.adsTicks(e,25,false));
        }
        assertThrows(IllegalArgumentException.class,()->SurplusProfile.adsTicks(entry("beloved"),25,true));
        assertEquals(3,SurplusProfile.adsTicks(entry("high_albedo"),60,false));
        assertEquals(2,SurplusProfile.adsTicks(entry("high_albedo"),60,true));
    }
    @Test void acceptedReloadValueFrozenWhileNewTiersAreQueriedAndBaseUnchanged() {
        var e=entry("apostate");var base=new WeaponReloadPolicy.Plan(55,55,0);
        var accepted=SurplusProfile.reloadPlan(e,60,.92,base);
        int acceptedTicks=SurplusProfile.reloadTicks(e,60,.92);
        for(int i=0;i<=3;i++)SurplusProfile.reloadPlan(e,SurplusProfile.reloadBonus(i),1,base);
        assertEquals(new WeaponReloadPolicy.Plan(acceptedTicks,acceptedTicks,0),accepted);
        assertEquals(new WeaponReloadPolicy.Plan(55,55,0),base);
        assertEquals(0,accepted.roundsPerInsert());
    }
}
