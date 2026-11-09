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
class ThreatDetectorProfileW178Test {
    private static final Gson GSON = new Gson();
    private static final Set<String> EXPECTED = Set.of(
        "seventh_seraph_officer_revolver:3037520408:3:903350103",
        "cold_denial:1216130969:3:330841869",
        "claws_of_the_wolf:1280933460:3:206409262",
        "bug_out_bag:2744715540:3:907333373",
        "dead_man_walking_xx7463:3751622019:3:3268663985",
        "high_albedo:1197486957:3:2797218184",
        "brass_attacks:2121785039:3:100135553",
        "mindbender_s_ambition_adept:912150785:3:1732284294",
        "dust_rock_blues:636912560:3:3511609070",
        "parcel_of_stardust_fell_to_earth:2217366863:3:2514419370",
        "dream_breaker:2931957300:3:3785896921",
        "ikelos_smg_v1_0_1:1723472487:4:1329", // W320 curated fixed-roll legendary
        "ikelos_sg_v1_0_1:1887808042:4:1324",
        "line_in_the_sand:946443267:3:1503774254",
        "deafening_whisper:981718087:4:3588287812",
        "edge_transit:218335759:3:447678063",
        "dimensional_hypotrochoid:1311684613:3:3235863202",
        "bellowing_giant:2186258845:4:1722393382",
        "hammerhead:603242241:3:2515290473");
    static JsonElement read(String file) {
        var stream = ThreatDetectorProfileW178Test.class.getResourceAsStream("/destiny/weapons/" + file);
        assertNotNull(stream, file);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) { return JsonParser.parseReader(reader); }
        catch (java.io.IOException e) { throw new AssertionError(e); }
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    @Test void exactBaseSeventeenOfficialSocketIdentitiesNoFamilyGrant() {
        assertEquals("threat_detector", ThreatDetectorProfile.ID);
        assertEquals(4071163871L, ThreatDetectorProfile.HASH);
        var actual = new HashSet<String>();
        for (var r : ThreatDetectorProfile.rolls()) {
            assertEquals(4071163871L, r.perkHash());
            assertNotEquals(494941759L, r.perkHash());
            assertTrue(actual.add(r.id()+":"+r.hash()+":"+r.socket()+":"+r.plugSetHash()));
            assertTrue(ThreatDetectorProfile.supports(entry(r.id())));
        }
        assertEquals(EXPECTED, actual);
        assertEquals(65, WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id())).toList().size());
        assertEquals(19, WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id())).toList().stream().filter(ThreatDetectorProfile::supports).count());
        assertFalse(ThreatDetectorProfile.supports(entry("ammit_ar2")));
        assertFalse(ThreatDetectorProfile.supports(entry("ace_of_spades")));
        assertThrows(UnsupportedOperationException.class, () -> ThreatDetectorProfile.rolls().clear());
    }
    @Test void canonicalIdentityEveryFieldAndNullFailClosed() {
        var e=entry("dream_breaker");
        assertFalse(ThreatDetectorProfile.supports(null));
        var fields=new String[]{e.id(),e.family(),e.frame(),e.name(),e.source_frame_label(),e.item_model()};
        for(int i=0;i<fields.length;i++) {
            var copy=fields.clone();copy[i]="mutated";
            var bad=new WeaponCatalog.Entry(copy[0],copy[1],copy[2],copy[3],copy[4],copy[5]);
            assertFalse(ThreatDetectorProfile.supports(bad));
            assertThrows(IllegalArgumentException.class,()->ThreatDetectorProfile.reloadTicks(bad,18,1));
            copy=fields.clone();copy[i]=null;
            assertFalse(ThreatDetectorProfile.supports(new WeaponCatalog.Entry(copy[0],copy[1],copy[2],copy[3],copy[4],copy[5])));
        }
    }
    @Test void pinnedResourceRejectsMissingExtraEnhancedAndCurvePolicyMutations() {
        var source=read("w178-threat-detector.json").getAsJsonObject();
        assertDoesNotThrow(()->ThreatDetectorProfile.validateResource(source.toString()));
        for(String key:source.keySet()) {
            var x=source.deepCopy();x.remove(key);
            assertThrows(IllegalStateException.class,()->ThreatDetectorProfile.validateResource(x.toString()),key);
        }
        var extra=source.deepCopy();extra.addProperty("durationTicks",100);
        assertThrows(IllegalStateException.class,()->ThreatDetectorProfile.validateResource(extra.toString()));
        var enhanced=source.deepCopy();enhanced.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("perkHash",494941759L);
        assertThrows(IllegalStateException.class,()->ThreatDetectorProfile.validateResource(enhanced.toString()));
        var curve=source.deepCopy();curve.getAsJsonArray("curves").get(0).getAsJsonObject().getAsJsonObject("reload").addProperty("offset",1);
        assertThrows(IllegalStateException.class,()->ThreatDetectorProfile.validateResource(curve.toString()));
        var policy=source.deepCopy();policy.getAsJsonObject("policies").addProperty("ads","APPLY_THREAT_SCALAR");
        assertThrows(IllegalStateException.class,()->ThreatDetectorProfile.validateResource(policy.toString()));
        for(String bad:List.of("null","[]","{}","not json")) assertThrows(IllegalStateException.class,()->ThreatDetectorProfile.validateResource(bad));
    }
    @Test void exactDistinctCompanionPairsAndSameSocketDenials() {
        var files=Map.of("snapshot","w68-snapshot.json","frenzy","w172-frenzy.json","adrenaline_junkie","w173-adrenaline-junkie.json",
            "perpetual_motion","w170-perpetual-motion.json","outlaw","w62-outlaw.json","feeding_frenzy","w108-feeding-frenzy.json",
            "rapid_hit","w169-rapid-hit.json","stats_for_all","w176-stats-for-all.json");
        var found=new HashSet<String>();
        for(var pair:files.entrySet()) {
            var data=read(pair.getValue()).getAsJsonObject();
            for(var value:data.getAsJsonArray(data.has("rolls")?"rolls":"weapons")) {
                var b=GSON.fromJson(value,WeaponPerks.Roll.class);
                for(var a:ThreatDetectorProfile.rolls()) if(a.id().equals(b.id())) {
                    boolean distinct=a.socket()!=b.socket();
                    assertEquals(distinct,ThreatDetectorProfile.compatible(entry(a.id()),pair.getKey(),b));
                    if(distinct) found.add(a.id()+":"+pair.getKey());
                    var forged=new WeaponPerks.Roll(b.id(),b.hash(),b.socket(),b.perkHash(),b.plugSetHash()+1);
                    assertFalse(ThreatDetectorProfile.compatible(entry(a.id()),pair.getKey(),forged));
                }
            }
        }
        assertEquals(Set.of("dust_rock_blues:snapshot","high_albedo:snapshot","brass_attacks:frenzy","dream_breaker:frenzy",
            "parcel_of_stardust_fell_to_earth:outlaw","seventh_seraph_officer_revolver:feeding_frenzy"),found);
    }
    @Test void reproduceEveryExistingBaselineAndShellTopology() {
        var timings=new HashMap<String,JsonObject>();var handling=new HashMap<String,JsonObject>();var aim=new HashMap<String,JsonObject>();
        for(var row:read("w46-timing.json").getAsJsonArray()) {var o=row.getAsJsonObject();timings.put(o.get("id").getAsString(),o.getAsJsonObject("timing"));}
        for(var row:read("w58-handling.json").getAsJsonArray()) {var o=row.getAsJsonObject();handling.put(o.get("id").getAsString(),o.getAsJsonObject("profile"));}
        for(var row:read("w44-aim.json").getAsJsonArray()) {var o=row.getAsJsonObject();aim.put(o.get("id").getAsString(),o.getAsJsonObject("profile"));}
        int shells=0;
        for(var roll:ThreatDetectorProfile.rolls()) {
            var e=entry(roll.id());var t=timings.get(e.id());var h=handling.get(e.id());
            boolean shell=t.get("shellReload").getAsBoolean();if(shell)shells++;
            assertEquals(t.get(shell?"reloadPerRoundTicks":"reloadTicks").getAsInt(),ThreatDetectorProfile.reloadTicks(e,0,1));
            assertEquals(h.get("readyTicks").getAsInt(),ThreatDetectorProfile.handlingTicks(e,0,1,true));
            assertEquals(h.get("stowTicks").getAsInt(),ThreatDetectorProfile.handlingTicks(e,0,1,false));
            assertEquals(aim.get(e.id()).get("transitionTicks").getAsInt(),ThreatDetectorProfile.adsTicks(e,0,false));
        }
        assertEquals(4,shells); // + IKELOS_SG
    }
}
