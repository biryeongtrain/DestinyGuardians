package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import kim.biryeong.destiny.guardian.Element;
import org.junit.jupiter.api.Test;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Pure production profile/catalog tests. Source guards are static; no native/runtime claim. */
class ElementalCapacitorW184Test {
    private static final Gson GSON = new Gson();
    private static final Set<String> EXPECTED = Set.of("steelfeather_repeater:1251729046:4:2645685327", "patron_of_lost_causes:2723241847:4:120674550");
    static JsonElement read(String file) {
        var stream = ElementalCapacitorW184Test.class.getResourceAsStream("/destiny/weapons/" + file);
        assertNotNull(stream, file);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) { return JsonParser.parseReader(reader); }
        catch (java.io.IOException e) { throw new AssertionError(e); }
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    @Test void exactBaseTwoOfficialSocketIdentitiesNoFamilyGrant() {
        assertEquals("elemental_capacitor", ElementalCapacitorProfile.ID);
        assertEquals(3511092054L, ElementalCapacitorProfile.HASH);
        var actual = new HashSet<String>();
        for (var r : ElementalCapacitorProfile.rolls().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id())).toList()) {
            assertEquals(3511092054L, r.perkHash());
            assertNotEquals(711234314L, r.perkHash());
            assertTrue(actual.add(r.id()+":"+r.hash()+":"+r.socket()+":"+r.plugSetHash()));
            assertTrue(ElementalCapacitorProfile.supports(entry(r.id())));
        }
        assertEquals(EXPECTED, actual);
        assertEquals(65, WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id()) && !WeaponExotics.expanded(legacy)).toList().size());
        assertEquals(2, WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id()) && !WeaponExotics.expanded(legacy)).toList().stream().filter(ElementalCapacitorProfile::supports).count());
        assertFalse(ElementalCapacitorProfile.supports(entry("cold_denial")));
        assertFalse(ElementalCapacitorProfile.supports(entry("ace_of_spades")));
        assertThrows(UnsupportedOperationException.class, () -> ElementalCapacitorProfile.rolls().clear());
    }
    @Test void canonicalIdentityEveryFieldAndNullFailClosed() {
        var e=entry("steelfeather_repeater");
        assertFalse(ElementalCapacitorProfile.supports(null));
        var fields=new String[]{e.id(),e.family(),e.frame(),e.name(),e.source_frame_label(),e.item_model()};
        for(int i=0;i<fields.length;i++) {
            var copy=fields.clone();copy[i]="mutated";
            var bad=new WeaponCatalog.Entry(copy[0],copy[1],copy[2],copy[3],copy[4],copy[5]);
            assertFalse(ElementalCapacitorProfile.supports(bad));
            assertThrows(IllegalArgumentException.class,()->ElementalCapacitorProfile.reloadTicks(bad,18,1));
            copy=fields.clone();copy[i]=null;
            assertFalse(ElementalCapacitorProfile.supports(new WeaponCatalog.Entry(copy[0],copy[1],copy[2],copy[3],copy[4],copy[5])));
        }
    }
    @Test void pinnedResourceRejectsMissingExtraEnhancedAndCurvePolicyMutations() {
        var source=read("w184-elemental_capacitor.json").getAsJsonObject();
        assertDoesNotThrow(()->ElementalCapacitorProfile.validateResource(source.toString()));
        for(String key:source.keySet()) {
            var x=source.deepCopy();x.remove(key);
            assertThrows(IllegalStateException.class,()->ElementalCapacitorProfile.validateResource(x.toString()),key);
        }
        var extra=source.deepCopy();extra.addProperty("durationTicks",100);
        assertThrows(IllegalStateException.class,()->ElementalCapacitorProfile.validateResource(extra.toString()));
        var enhanced=source.deepCopy();enhanced.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("perkHash",711234314L);
        assertThrows(IllegalStateException.class,()->ElementalCapacitorProfile.validateResource(enhanced.toString()));
        var curve=source.deepCopy();curve.getAsJsonArray("curves").get(0).getAsJsonObject().getAsJsonObject("reload").addProperty("offset",1);
        assertThrows(IllegalStateException.class,()->ElementalCapacitorProfile.validateResource(curve.toString()));
        var policy=source.deepCopy();policy.getAsJsonObject("policies").addProperty("ads","APPLY_THREAT_SCALAR");
        assertThrows(IllegalStateException.class,()->ElementalCapacitorProfile.validateResource(policy.toString()));
        for(String bad:List.of("null","[]","{}","not json")) assertThrows(IllegalStateException.class,()->ElementalCapacitorProfile.validateResource(bad));
    }
    @Test void exactDistinctCompanionPairsAndSameSocketDenials() {
        var files=Map.ofEntries(
            Map.entry("rapid_hit","w169-rapid-hit.json"),Map.entry("feeding_frenzy","w108-feeding-frenzy.json"),
            Map.entry("surplus","w183-surplus.json"),Map.entry("outlaw","w62-outlaw.json"),
            Map.entry("subsistence","w167-subsistence.json"),Map.entry("grave_robber","w110-grave-robber.json"),
            Map.entry("multikill_clip","w165-multikill-clip.json"),Map.entry("swashbuckler","w110-swashbuckler.json"),
            Map.entry("surrounded","w109-surrounded.json"),Map.entry("vorpal","w181-vorpal.json"),Map.entry("payload","w80-payload.json"));
        var found=new HashSet<String>();
        for(var pair:files.entrySet()) {
            var data=read(pair.getValue()).getAsJsonObject();
            for(var value:data.getAsJsonArray(data.has("rolls")?"rolls":"weapons")) {
                var b=GSON.fromJson(value,WeaponPerks.Roll.class);
                for(var a:ElementalCapacitorProfile.rolls().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id())).toList()) if(a.id().equals(b.id())) {
                    boolean distinct=a.socket()!=b.socket();
                    assertEquals(distinct,ElementalCapacitorProfile.compatible(entry(a.id()),pair.getKey(),b));
                    if(distinct) found.add(a.id()+":"+pair.getKey());
                    var forged=new WeaponPerks.Roll(b.id(),b.hash(),b.socket(),b.perkHash(),b.plugSetHash()+1);
                    assertFalse(ElementalCapacitorProfile.compatible(entry(a.id()),pair.getKey(),forged));
                }
            }
        }
        assertEquals(Set.of("steelfeather_repeater:feeding_frenzy","patron_of_lost_causes:rapid_hit",
            "steelfeather_repeater:subsistence","steelfeather_repeater:grave_robber","patron_of_lost_causes:grave_robber"),found);
    }

    @Test void reproduceEveryExistingBaselineAndShellTopology() {
        var timings=new HashMap<String,JsonObject>();var handling=new HashMap<String,JsonObject>();var aim=new HashMap<String,JsonObject>();
        for(var row:read("w46-timing.json").getAsJsonArray()) {var o=row.getAsJsonObject();timings.put(o.get("id").getAsString(),o.getAsJsonObject("timing"));}
        for(var row:read("w58-handling.json").getAsJsonArray()) {var o=row.getAsJsonObject();handling.put(o.get("id").getAsString(),o.getAsJsonObject("profile"));}
        for(var row:read("w44-aim.json").getAsJsonArray()) {var o=row.getAsJsonObject();aim.put(o.get("id").getAsString(),o.getAsJsonObject("profile"));}
        int shells=0;
        for(var roll:ElementalCapacitorProfile.rolls().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id())).toList()) {
            var e=entry(roll.id());var t=timings.get(e.id());var h=handling.get(e.id());
            boolean shell=t.get("shellReload").getAsBoolean();if(shell)shells++;
            assertEquals(t.get(shell?"reloadPerRoundTicks":"reloadTicks").getAsInt(),ElementalCapacitorProfile.reloadTicks(e,0,1));
            assertEquals(h.get("readyTicks").getAsInt(),ElementalCapacitorProfile.handlingTicks(e,0,1,true));
            assertEquals(h.get("stowTicks").getAsInt(),ElementalCapacitorProfile.handlingTicks(e,0,1,false));
            assertEquals(aim.get(e.id()).get("transitionTicks").getAsInt(),ElementalCapacitorProfile.adsTicks(e,0,false));
        }
        assertEquals(0,shells);
    }

    @Test void exactBonusesOnlySupportedElementsNoKineticOrNullBonus() {
        for(var e:Element.values()) {
            assertEquals(e==Element.SOLAR?50:0,ElementalCapacitorProfile.reloadBonus(e));
            assertEquals(e==Element.ARC?50:0,ElementalCapacitorProfile.handlingBonus(e));
            assertEquals(e==Element.VOID?20:0,ElementalCapacitorProfile.stabilityBonus(e));
        }
        assertEquals(4,Element.values().length);
        assertEquals(0,ElementalCapacitorProfile.reloadBonus(null));
        assertEquals(0,ElementalCapacitorProfile.handlingBonus(null));
        assertEquals(0,ElementalCapacitorProfile.stabilityBonus(null));
    }
    @Test void allEightWeaponElementsMatchFrozenHistoricalRawOracle() {
        var rows=List.of(
            "steelfeather_repeater KINETIC 9 8 7 37",
            "steelfeather_repeater SOLAR 9 8 7 25",
            "steelfeather_repeater ARC 6 5 5 37",
            "steelfeather_repeater VOID 9 8 7 37",
            "patron_of_lost_causes KINETIC 8 7 7 39",
            "patron_of_lost_causes SOLAR 8 7 7 28",
            "patron_of_lost_causes ARC 6 5 5 39",
            "patron_of_lost_causes VOID 8 7 7 39");
        for(String row:rows) {
            var v=row.split(" "); var e=entry(v[0]);var element=Element.valueOf(v[1]);
            int h=ElementalCapacitorProfile.handlingBonus(element), r=ElementalCapacitorProfile.reloadBonus(element);
            assertEquals(Integer.parseInt(v[2]),ElementalCapacitorProfile.handlingTicks(e,h,1,true),row);
            assertEquals(Integer.parseInt(v[3]),ElementalCapacitorProfile.handlingTicks(e,h,1,false),row);
            assertEquals(Integer.parseInt(v[4]),ElementalCapacitorProfile.adsTicks(e,h,false),row);
            assertEquals(Integer.parseInt(v[5]),ElementalCapacitorProfile.reloadTicks(e,r,1),row);
        }
    }
    @Test void allFortyLegalCompanionElementTierCasesUseRealProfilesRawStatsAndSingleRounding() {
        var rows=List.of(
            "steelfeather_repeater feeding_frenzy KINETIC 1 8 0.975 33",
            "steelfeather_repeater feeding_frenzy KINETIC 2 50 0.9 23",
            "steelfeather_repeater feeding_frenzy KINETIC 3 60 0.87 22",
            "steelfeather_repeater feeding_frenzy KINETIC 4 75 0.84 21",
            "steelfeather_repeater feeding_frenzy KINETIC 5 100 0.8 20",
            "steelfeather_repeater feeding_frenzy SOLAR 1 58 0.975 25",
            "steelfeather_repeater feeding_frenzy SOLAR 2 100 0.9 23",
            "steelfeather_repeater feeding_frenzy SOLAR 3 110 0.87 22",
            "steelfeather_repeater feeding_frenzy SOLAR 4 125 0.84 21",
            "steelfeather_repeater feeding_frenzy SOLAR 5 150 0.8 20",
            "steelfeather_repeater feeding_frenzy ARC 1 8 0.975 33",
            "steelfeather_repeater feeding_frenzy ARC 2 50 0.9 23",
            "steelfeather_repeater feeding_frenzy ARC 3 60 0.87 22",
            "steelfeather_repeater feeding_frenzy ARC 4 75 0.84 21",
            "steelfeather_repeater feeding_frenzy ARC 5 100 0.8 20",
            "steelfeather_repeater feeding_frenzy VOID 1 8 0.975 33",
            "steelfeather_repeater feeding_frenzy VOID 2 50 0.9 23",
            "steelfeather_repeater feeding_frenzy VOID 3 60 0.87 22",
            "steelfeather_repeater feeding_frenzy VOID 4 75 0.84 21",
            "steelfeather_repeater feeding_frenzy VOID 5 100 0.8 20",
            "patron_of_lost_causes rapid_hit KINETIC 1 5 0.99 37",
            "patron_of_lost_causes rapid_hit KINETIC 2 30 0.96 30",
            "patron_of_lost_causes rapid_hit KINETIC 3 35 0.95 29",
            "patron_of_lost_causes rapid_hit KINETIC 4 42 0.945 27",
            "patron_of_lost_causes rapid_hit KINETIC 5 60 0.92 26",
            "patron_of_lost_causes rapid_hit SOLAR 1 55 0.99 28",
            "patron_of_lost_causes rapid_hit SOLAR 2 80 0.96 27",
            "patron_of_lost_causes rapid_hit SOLAR 3 85 0.95 27",
            "patron_of_lost_causes rapid_hit SOLAR 4 92 0.945 27",
            "patron_of_lost_causes rapid_hit SOLAR 5 110 0.92 26",
            "patron_of_lost_causes rapid_hit ARC 1 5 0.99 37",
            "patron_of_lost_causes rapid_hit ARC 2 30 0.96 30",
            "patron_of_lost_causes rapid_hit ARC 3 35 0.95 29",
            "patron_of_lost_causes rapid_hit ARC 4 42 0.945 27",
            "patron_of_lost_causes rapid_hit ARC 5 60 0.92 26",
            "patron_of_lost_causes rapid_hit VOID 1 5 0.99 37",
            "patron_of_lost_causes rapid_hit VOID 2 30 0.96 30",
            "patron_of_lost_causes rapid_hit VOID 3 35 0.95 29",
            "patron_of_lost_causes rapid_hit VOID 4 42 0.945 27",
            "patron_of_lost_causes rapid_hit VOID 5 60 0.92 26");
        for(String row:rows) {
            var v=row.split(" ");var e=entry(v[0]);var element=Element.valueOf(v[2]);int tier=Integer.parseInt(v[3]);
            int total=Integer.parseInt(v[4]);double scalar=Double.parseDouble(v[5]);
            int effective,base;double actualScalar;
            if(v[1].equals("rapid_hit")) {
                var boost=RapidHitProfile.reload(e,tier);effective=boost.effectiveReloadStat();base=boost.baseReloadStat();
                actualScalar=RapidHitProfile.durationMultiplier(tier);
            } else {
                var boost=FeedingFrenzyProfile.reload(e,tier);effective=boost.effectiveReloadStat();base=boost.baseReloadStat();
                actualScalar=FeedingFrenzyProfile.durationMultiplier(tier);
            }
            assertEquals(scalar,actualScalar);
            assertEquals(Integer.parseInt(v[6]),ElementalCapacitorProfile.reloadTicks(e,total,scalar),row);
            assertEquals(Integer.parseInt(v[6]),ElementalCapacitorProfile.reloadTicks(e,
                ElementalCapacitorProfile.reloadBonus(element)+effective-base,actualScalar),row);
        }
    }
    @Test void wideCapsNonfiniteScalarsAndRawVersusRoundedCombination() {
        assertEquals(100,ElementalCapacitorProfile.effectiveStat(99,Integer.MAX_VALUE));
        assertEquals(0,ElementalCapacitorProfile.effectiveStat(99,Integer.MIN_VALUE));
        boolean differs=false;
        for(var roll:ElementalCapacitorProfile.rolls().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id())).toList()) {
            var e=entry(roll.id());
            assertEquals(ElementalCapacitorProfile.reloadTicks(e,100,1),ElementalCapacitorProfile.reloadTicks(e,Integer.MAX_VALUE,1));
            assertEquals(ElementalCapacitorProfile.handlingTicks(e,100,1,true),ElementalCapacitorProfile.handlingTicks(e,Integer.MAX_VALUE,1,true));
            for(double scalar:new double[]{.975,.9,.87,.84,.8,.99,.96,.95,.945,.92}) {
                differs|=(int)Math.ceil(ElementalCapacitorProfile.reloadTicks(e,50,1)*scalar)!=ElementalCapacitorProfile.reloadTicks(e,50,scalar);
            }
        }
        assertTrue(differs,"Must detect multiplication of previously rounded ticks");
        for(double bad:new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY,0,-1,1.0001}) {
            assertThrows(IllegalArgumentException.class,()->ElementalCapacitorProfile.reloadTicks(entry("steelfeather_repeater"),50,bad));
            assertThrows(IllegalArgumentException.class,()->ElementalCapacitorProfile.handlingTicks(entry("patron_of_lost_causes"),50,bad,true));
        }
    }
    @Test void noSnapshotAndAcceptedReloadImmutableAcrossElementEdits() {
        var e=entry("patron_of_lost_causes");var base=new WeaponReloadPolicy.Plan(39,39,0);
        var accepted=ElementalCapacitorProfile.reloadPlan(e,55,.99,base);
        assertEquals(new WeaponReloadPolicy.Plan(28,28,0),accepted);
        for(var element:Element.values())ElementalCapacitorProfile.reloadPlan(e,ElementalCapacitorProfile.reloadBonus(element),1,base);
        assertEquals(new WeaponReloadPolicy.Plan(28,28,0),accepted);
        assertEquals(new WeaponReloadPolicy.Plan(39,39,0),base);
        for(var roll:ElementalCapacitorProfile.rolls()) assertThrows(IllegalArgumentException.class,
            ()->ElementalCapacitorProfile.adsTicks(entry(roll.id()),50,true));
    }
    @Test void initializationUsesJsonSourcesWithoutCatalogOrPerkRegistryRecursion() throws Exception {
        String source=java.nio.file.Files.readString(java.nio.file.Path.of("src/main/java/kim/biryeong/destiny/weapon/ElementalCapacitorProfile.java"));
        String initialization=source.substring(0,source.indexOf("public static List<WeaponPerks.Roll> rolls()"));
        for(String forbidden:List.of("WeaponCatalog.find(","WeaponCatalog.all(","WeaponCharacteristics.of(","WeaponPerks.rolls(","WeaponPerks.available(","WeaponPerks.selected("))
            assertFalse(initialization.contains(forbidden),forbidden);
        assertTrue(source.contains("byId(\"/destiny/weapons/w30.json\")"));
        assertEquals(2,ElementalCapacitorProfile.rolls().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id())).toList().size());
    }

}
