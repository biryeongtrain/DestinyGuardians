package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Pure profile/source tests only. No runtime authority, Minecraft or native input claim. */
class FirmlyPlantedW189Test {
    private static final Gson GSON = new Gson();
    private static final String ART = "art/weapons/w189/firmly_planted/";
    private static JsonElement read(String name) {
        var in=FirmlyPlantedW189Test.class.getResourceAsStream("/destiny/weapons/"+name);
        assertNotNull(in,name);
        try(var reader=new InputStreamReader(in,StandardCharsets.UTF_8)) { return JsonParser.parseReader(reader); }
        catch(IOException e) { throw new AssertionError(e); }
    }
    private static JsonObject art(String name) throws IOException {
        return JsonParser.parseString(Files.readString(Path.of(ART+name))).getAsJsonObject();
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static JsonObject resource() { return read("w189-firmly_planted.json").getAsJsonObject(); }
    private static Map<String,JsonObject> index(String name,String field) {
        var map=new HashMap<String,JsonObject>();
        for(var value:read(name).getAsJsonArray()) {var o=value.getAsJsonObject();map.put(o.get("id").getAsString(),o.getAsJsonObject(field));}
        return map;
    }
    @Test void exactEightBaseIdentitiesAcrossCurrentCatalog65() {
        assertEquals("firmly_planted",FirmlyPlantedProfile.ID); assertEquals(280464955L,FirmlyPlantedProfile.HASH);
        var expected=Set.of("seventh_seraph_officer_revolver:3037520408:3:903350103",
          "steelfeather_repeater:1251729046:3:473189353","distant_relation:2034817450:4:3824767299",
          "whispering_slab:211938782:3:1885424927","bite_of_the_fox:1403800851:3:563442205",
          "beloved:3107853529:3:1196545279","apostate:2164448701:3:1306932196","dream_breaker:2931957300:3:3785896921");
        var actual=new HashSet<String>();
        for(var r:FirmlyPlantedProfile.rolls()) {
            assertEquals(280464955L,r.perkHash());assertNotEquals(3920370755L,r.perkHash());
            assertTrue(actual.add(r.id()+":"+r.hash()+":"+r.socket()+":"+r.plugSetHash()));
            assertTrue(FirmlyPlantedProfile.supports(entry(r.id())));
        }
        assertEquals(expected,actual);assertEquals(65,WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id()) && !WeaponExotics.expanded(legacy)).toList().size());
        assertEquals(8,WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id()) && !WeaponExotics.expanded(legacy)).toList().stream().filter(FirmlyPlantedProfile::supports).count());
        assertThrows(UnsupportedOperationException.class,()->FirmlyPlantedProfile.rolls().clear());
    }
    @Test void ordinaryFusionBonusesAndAllUnsupportedNeutral() {
        for(var e:WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id()) && !WeaponExotics.expanded(legacy)).toList()) {
            boolean supported=FirmlyPlantedProfile.supports(e),fusion=e.id().equals("dream_breaker");
            assertEquals(!supported?0:fusion?10:20,FirmlyPlantedProfile.stabilityBonus(e));
            assertEquals(!supported?0:fusion?15:30,FirmlyPlantedProfile.handlingBonus(e));
            assertEquals(!supported?1:fusion?.8:.6,FirmlyPlantedProfile.accuracyScalar(e));
            assertEquals(!supported?1:fusion?.915:.83,FirmlyPlantedProfile.growthScalar(e));
            assertEquals(!supported?1:fusion?.6:.2,FirmlyPlantedProfile.yawScalar(e));
        }
        assertNeutral(null);assertNeutral(entry("erentil_fr4"));assertNeutral(entry("ace_of_spades"));
    }
    private static void assertNeutral(WeaponCatalog.Entry e) {
        assertFalse(FirmlyPlantedProfile.supports(e));assertEquals(0,FirmlyPlantedProfile.stabilityBonus(e));
        assertEquals(0,FirmlyPlantedProfile.handlingBonus(e));assertEquals(1,FirmlyPlantedProfile.accuracyScalar(e));
        assertEquals(1,FirmlyPlantedProfile.growthScalar(e));assertEquals(1,FirmlyPlantedProfile.yawScalar(e));
        assertThrows(IllegalArgumentException.class,()->FirmlyPlantedProfile.handlingTicks(e,30,1,true));
        assertThrows(IllegalArgumentException.class,()->FirmlyPlantedProfile.adsTicks(e,30,false));
        assertFalse(FirmlyPlantedProfile.compatible(e,null,null));
    }
    @Test void everyCanonicalFieldAndNullIdentityFailsClosed() {
        var e=entry("dream_breaker");var fields=new String[]{e.id(),e.family(),e.frame(),e.name(),e.source_frame_label(),e.item_model()};
        for(int i=0;i<fields.length;i++) for(String bad:new String[]{"mutated",null}) {
            var x=fields.clone();x[i]=bad;
            assertNeutral(new WeaponCatalog.Entry(x[0],x[1],x[2],x[3],x[4],x[5]));
        }
    }
    @Test void pinnedResourceRejectsSchemaEnhancedMechanicCurveAndPairMutations() {
        var source=resource();assertDoesNotThrow(()->FirmlyPlantedProfile.validateResource(source.toString()));
        for(String key:source.keySet()) {
            var x=source.deepCopy();x.remove(key);
            assertThrows(IllegalStateException.class,()->FirmlyPlantedProfile.validateResource(x.toString()));
        }
        var mutations=new ArrayList<JsonObject>();
        var x=source.deepCopy();x.addProperty("reloadBonus",10);mutations.add(x);
        x=source.deepCopy();x.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("perkHash",3920370755L);mutations.add(x);
        x=source.deepCopy();x.getAsJsonObject("perk").getAsJsonObject("fusion").addProperty("handlingBonus",18);mutations.add(x);
        x=source.deepCopy();x.getAsJsonArray("curves").get(0).getAsJsonObject().getAsJsonObject("ads").addProperty("offset",1);mutations.add(x);
        x=source.deepCopy();x.getAsJsonArray("coSelections").get(0).getAsJsonObject().getAsJsonObject("roll").addProperty("socket",3);mutations.add(x);
        x=source.deepCopy();x.getAsJsonObject("policies").addProperty("yaw","ALSO_PITCH");mutations.add(x);
        for(var m:mutations)assertThrows(IllegalStateException.class,()->FirmlyPlantedProfile.validateResource(m.toString()));
        for(String bad:List.of("null","[]","{}","not json"))assertThrows(IllegalStateException.class,()->FirmlyPlantedProfile.validateResource(bad));
    }
    @Test void all35ImplementedTraitsYield32DistinctAnd22SameSocketDenials() throws Exception {
        var audit=art("official-sockets.json").getAsJsonArray("companionAudit");
        assertEquals(35,audit.size());int legal=0,denied=0;
        for(var value:audit) {
            var group=value.getAsJsonObject();String perk=group.get("perk").getAsString();
            for(var accepted:group.getAsJsonArray("accepted")) {
                var r=GSON.fromJson(accepted,WeaponPerks.Roll.class);var e=entry(r.id());
                assertTrue(FirmlyPlantedProfile.compatible(e,perk,r),perk+" "+r.id());legal++;
                assertFalse(FirmlyPlantedProfile.compatible(e,perk+"_enhanced",r));
                assertFalse(FirmlyPlantedProfile.compatible(e,perk,null));
                assertFalse(FirmlyPlantedProfile.compatible(e,perk,new WeaponPerks.Roll(r.id(),r.hash(),r.socket(),r.perkHash(),r.plugSetHash()+1)));
                assertFalse(FirmlyPlantedProfile.compatible(e,perk,new WeaponPerks.Roll(r.id(),r.hash()+1,r.socket(),r.perkHash(),r.plugSetHash())));
                assertFalse(FirmlyPlantedProfile.compatible(e,perk,new WeaponPerks.Roll(r.id(),r.hash(),r.socket()+1,r.perkHash(),r.plugSetHash())));
                assertFalse(FirmlyPlantedProfile.compatible(e,perk,new WeaponPerks.Roll(r.id(),r.hash(),r.socket(),3920370755L,r.plugSetHash())));
            }
            for(var rejected:group.getAsJsonArray("denied")) {
                var r=GSON.fromJson(rejected.getAsJsonObject().get("roll"),WeaponPerks.Roll.class);
                assertFalse(FirmlyPlantedProfile.compatible(entry(r.id()),perk,r));denied++;
            }
        }
        assertEquals(32,legal);assertEquals(22,denied);
        var handling=new HashSet<String>();
        for(var value:resource().getAsJsonArray("coSelections")) {
            var p=value.getAsJsonObject();String perk=p.get("perk").getAsString();
            if(Set.of("elemental_capacitor","frenzy","quickdraw","snapshot_sights","surplus","threat_detector","adrenaline_junkie","perpetual_motion","stats_for_all").contains(perk))
                handling.add(p.get("id").getAsString()+":"+perk);
        }
        assertEquals(Set.of("steelfeather_repeater:elemental_capacitor","dream_breaker:frenzy",
          "beloved:quickdraw","dream_breaker:quickdraw","apostate:quickdraw","apostate:snapshot_sights"),handling);
    }
    @Test void allEightExistingHandlingAndAdsBaselinesReproduceExactly() {
        var h=index("w58-handling.json","profile");var a=index("w44-aim.json","profile");
        for(var r:FirmlyPlantedProfile.rolls()) {
            var e=entry(r.id());
            assertEquals(h.get(r.id()).get("readyTicks").getAsInt(),FirmlyPlantedProfile.handlingTicks(e,0,1,true));
            assertEquals(h.get(r.id()).get("stowTicks").getAsInt(),FirmlyPlantedProfile.handlingTicks(e,0,1,false));
            assertEquals(a.get(r.id()).get("transitionTicks").getAsInt(),FirmlyPlantedProfile.adsTicks(e,0,false));
        }
    }
    @Test void eightCrouchedAndSixDistinctHandlingPairsUseFrozenRawOracle() {
        for(String row:List.of("seventh_seraph_officer_revolver 30 1 false 7 7 5",
          "steelfeather_repeater 30 1 false 7 7 6","steelfeather_repeater 80 1 false 5 5 5",
          "distant_relation 30 1 false 7 7 6","whispering_slab 30 1 false 10 8 8",
          "bite_of_the_fox 30 1 false 8 7 8","beloved 30 1 false 7 6 8",
          "beloved 100 .95 false 5 5 7","beloved 100 1 false 5 5 7",
          "apostate 30 1 false 6 5 7","apostate 100 .95 false 5 5 7","apostate 100 1 false 5 5 7",
          "apostate 30 1 true 6 5 6","dream_breaker 15 1 false 9 7 7",
          "dream_breaker 115 1 false 8 4 5","dream_breaker 100 .95 false 7 4 5","dream_breaker 100 1 false 8 4 5")) {
            var v=row.split(" ");var e=entry(v[0]);int total=Integer.parseInt(v[1]);double s=Double.parseDouble(v[2]);
            assertEquals(Integer.parseInt(v[4]),FirmlyPlantedProfile.handlingTicks(e,total,s,true),row);
            assertEquals(Integer.parseInt(v[5]),FirmlyPlantedProfile.handlingTicks(e,total,s,false),row);
            assertEquals(Integer.parseInt(v[6]),FirmlyPlantedProfile.adsTicks(e,total,Boolean.parseBoolean(v[3])),row);
        }
    }
    @Test void noDoubleRoundingWideCapsInvalidScalarsAndSnapshotEnterOnly() {
        var dream=entry("dream_breaker");
        assertEquals(8,FirmlyPlantedProfile.handlingTicks(dream,100,1,true));
        assertEquals(7,FirmlyPlantedProfile.handlingTicks(dream,100,.95,true));
        assertEquals(8,(int)Math.ceil(FirmlyPlantedProfile.handlingTicks(dream,100,1,true)*.95));
        assertEquals(100,FirmlyPlantedProfile.effectiveStat(60,Integer.MAX_VALUE));
        assertEquals(0,FirmlyPlantedProfile.effectiveStat(60,Integer.MIN_VALUE));
        for(var r:FirmlyPlantedProfile.rolls()) {
            var e=entry(r.id());
            assertEquals(FirmlyPlantedProfile.handlingTicks(e,100,1,true),FirmlyPlantedProfile.handlingTicks(e,Integer.MAX_VALUE,1,true));
            assertEquals(FirmlyPlantedProfile.adsTicks(e,100,false),FirmlyPlantedProfile.adsTicks(e,Integer.MAX_VALUE,false));
            for(double bad:new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY,0,-1,1.0001})
                assertThrows(IllegalArgumentException.class,()->FirmlyPlantedProfile.handlingTicks(e,30,bad,true));
            if(!e.id().equals("apostate"))assertThrows(IllegalArgumentException.class,()->FirmlyPlantedProfile.adsTicks(e,30,true));
        }
        assertEquals(6,FirmlyPlantedProfile.adsTicks(entry("apostate"),30,true));
        assertEquals(7,FirmlyPlantedProfile.adsTicks(entry("apostate"),30,false));
    }
    @Test void rawCurvesMatchPinnedOriginalFieldsAndCurrentBaseStats() throws Exception {
        var original=JsonParser.parseString(Files.readString(Path.of("art/weapons/w46/weapon_formulas.json"))).getAsJsonObject();
        var mappings=JsonParser.parseString(Files.readString(Path.of("art/weapons/w43/extraction.json"))).getAsJsonObject().getAsJsonArray("entries");
        for(var value:resource().getAsJsonArray("curves")) {
            var c=value.getAsJsonObject();String id=c.get("id").getAsString();JsonObject mapping=null;
            for(var m:mappings)if(m.getAsJsonObject().get("id").getAsString().equals(id))mapping=m.getAsJsonObject();
            assertNotNull(mapping);
            var raw=original.getAsJsonObject(mapping.get("family").getAsString()).getAsJsonObject("cat")
                .getAsJsonObject(mapping.get("category").getAsString()).getAsJsonObject("handling");
            assertEquals(WeaponCharacteristics.of(entry(id)).stats().get("943549884").intValue(),c.get("baseHandlingStat").getAsInt());
            for(String key:List.of("ready","stow","ads"))for(String f:List.of("evpp","vpp","offset")) {
                var source=raw.getAsJsonObject(key);assertEquals(source.has(f)?source.get(f).getAsDouble():0,c.getAsJsonObject(key).get(f).getAsDouble());
            }
        }
    }
    @Test void noBootstrapCycleAndNoGameplayOrHudSideEffects() throws Exception {
        String source=Files.readString(Path.of("src/main/java/kim/biryeong/destiny/weapon/FirmlyPlantedProfile.java"));
        for(String forbidden:List.of("WeaponCatalog.find(","WeaponCatalog.all(","WeaponCharacteristics.of(","WeaponPerks.rolls(",
          "WeaponPerks.available(","WeaponPerks.selected(","ItemStack","ServerPlayer","reloadTicks(","damageMultiplier(","isCrouching("))
            assertFalse(source.contains(forbidden),forbidden);
        assertEquals(8,FirmlyPlantedProfile.rolls().size());
    }
}
