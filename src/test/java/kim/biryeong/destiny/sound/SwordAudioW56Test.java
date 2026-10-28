package kim.biryeong.destiny.sound;

import com.google.gson.*;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Routing/edge/manifest evidence; no acoustic audition or native playback proof. */
class SwordAudioW56Test {
    private static WeaponCatalog.Entry sword(String id) {return WeaponCatalog.find(id).orElseThrow();}
    private static JsonObject json(Path p) throws Exception {return JsonParser.parseString(Files.readString(p)).getAsJsonObject();}
    @Test void exactActionRoutingKeepsHeavyAirEmptyAndCasterSeparate() {
        var g=sword("falling_guillotine");
        assertEquals("weapon.falling_guillotine.light",SwordSounds.attackKey(g,false,false,true));
        assertEquals("weapon.falling_guillotine.heavy",SwordSounds.attackKey(g,true,false,true));
        var c=sword("crown_splitter");
        assertEquals("weapon.crown_splitter.light",SwordSounds.attackKey(c,false,false,true));
        assertEquals("weapon.crown_splitter.heavy",SwordSounds.attackKey(c,true,false,true));
        assertEquals("weapon.crown_splitter.heavy_air",SwordSounds.attackKey(c,true,false,false));
        var t=sword("temptation_s_hook");
        assertEquals("weapon.temptation_s_hook.light",SwordSounds.attackKey(t,false,false,true));
        assertEquals("weapon.temptation_s_hook.empty_light",SwordSounds.attackKey(t,false,true,true));
        assertEquals(SwordSounds.CASTER_RELEASE,SwordSounds.attackKey(t,true,false,true));
        assertEquals(SwordSounds.CASTER_RELEASE,SwordSounds.attackKey(t,true,false,false));
    }
    @Test void frameProxiesAndMissingSourcesNeverPretendToBeExactLightweightOrEmptyRecordings() {
        assertEquals("weapon.sword.light",SwordSounds.attackKey(sword("abide_the_return"),false,false,true));
        assertEquals("weapon.sword.uppercut",SwordSounds.attackKey(sword("abide_the_return"),true,false,true));
        assertEquals("weapon.sword.light",SwordSounds.attackKey(sword("goldtusk"),false,false,true));
        assertEquals("weapon.sword.fire",SwordSounds.attackKey(sword("goldtusk"),true,false,true));
        for(String id:List.of("abide_the_return","goldtusk","crown_splitter","falling_guillotine"))
            assertEquals(id.equals("falling_guillotine")?"weapon.falling_guillotine.fire":"weapon.sword.fire",
                    SwordSounds.attackKey(sword(id),false,true,true));
        assertThrows(IllegalArgumentException.class,()->SwordSounds.attackKey(sword("duke_mk_44"),false,false,true));
    }
    @Test void guardRoutesToExactNamedFolderThenDocumentedFamilyProxy() {
        for(String id:List.of("falling_guillotine","crown_splitter","temptation_s_hook"))
            assertEquals("weapon."+id+".guard",SwordSounds.guardKey(sword(id)));
        assertEquals("weapon.sword.guard",SwordSounds.guardKey(sword("abide_the_return")));
        assertEquals("weapon.sword.guard",SwordSounds.guardKey(sword("goldtusk")));
        assertThrows(IllegalArgumentException.class,()->SwordSounds.guardKey(sword("duke_mk_44")));
    }
    @Test void guardOneShotIsRisingEdgeOnlyAcrossDuplicateTicksAndLongHolds() {
        var edge=new SwordGuardAudio();assertFalse(edge.sample(0,false));assertTrue(edge.sample(1,true));
        for(long i=1;i<1000;i++)assertFalse(edge.sample(i,true));
        assertFalse(edge.sample(1000,false));assertTrue(edge.sample(1001,true));
        for(int i=0;i<100;i++)assertFalse(edge.sample(1001,true));
    }
    @Test void guardCancellationAndRapidReentryRetainThrottleWithoutLateMidHoldStart() {
        var edge=new SwordGuardAudio();assertTrue(edge.sample(0,true));edge.release();
        assertFalse(edge.sample(1,true));assertFalse(edge.sample(100,true),"Suppressed edge never starts later in a hold");
        assertFalse(edge.sample(101,false));assertTrue(edge.sample(102,true));
        for(int i=103;i<110;i++) {edge.release();assertFalse(edge.sample(i,true));}
        edge.release();assertTrue(edge.sample(110,true));
    }
    @Test void guardTimestampLimitsAreFiniteAndIndependentPerOwner() {
        var a=new SwordGuardAudio();var b=new SwordGuardAudio();
        assertTrue(a.sample(Long.MIN_VALUE,true));assertTrue(b.sample(Long.MIN_VALUE,true));
        a.release();assertFalse(a.sample(Long.MIN_VALUE+7,true));a.release();assertTrue(a.sample(Long.MIN_VALUE+8,true));
        a.release();assertTrue(a.sample(Long.MAX_VALUE,true));a.release();assertFalse(a.sample(Long.MAX_VALUE,true));
        assertFalse(a.sample(0,false),"Backward timestamps cannot alter current edge state");
        assertFalse(a.sample(Long.MAX_VALUE,true));
        assertFalse(b.sample(Long.MAX_VALUE,true),"Another owner's long hold never retriggers");
    }
    @Test void existingSoundDefinitionsRemainIdenticalWithExactlyFifteenAdditions() throws Exception {
        var before=json(Path.of("docs/qa/2026-10-24/w56/before-sounds.json"));
        var now=ReviewedAudioW234.legacyW102(json(Path.of("src/main/resources/assets/destiny/sounds.json")));
        for(String key:before.keySet()) {
            // Explicit later W98 contract migration for exactly three non-sword fire events.
            // Their original first clip/subtitle remain; FireVariantsW98Test checks the exact two additions.
            if(Set.of("weapon.seventh_seraph_officer_revolver.fire", "weapon.steelfeather_repeater.fire", "weapon.the_recluse.fire").contains(key)) {
                var old=before.getAsJsonObject(key);var current=now.getAsJsonObject(key);
                assertEquals(old.get("subtitle"),current.get("subtitle"));
                assertEquals(1,old.getAsJsonArray("sounds").size());assertEquals(3,current.getAsJsonArray("sounds").size());
                assertEquals(old.getAsJsonArray("sounds").get(0),current.getAsJsonArray("sounds").get(0));
            } else assertEquals(before.get(key),now.get(key),"Existing event "+key);
        }
        var added=new HashSet<>(now.keySet());added.removeAll(before.keySet());
        // W56's exact fifteen additions remain fixed. W63's finite, independently
        // validated timed-reload matrix is a later additive layer, not a sword action.
        var originalIds=kim.biryeong.destiny.weapon.WeaponCatalogTest.originalW30Entries().stream()
                .map(WeaponCatalog.Entry::id).collect(java.util.stream.Collectors.toSet());
        // W102 changes six active aliases, not a single historical W63 event or asset.
        var inheritedProfile=Path.of("src/main/resources/destiny/sounds/w63-reload.json");
        assertEquals("e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b",
                java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(inheritedProfile))));
        var timed=new HashSet<String>();
        for (var value : json(inheritedProfile).getAsJsonArray("entries")) {
            var clip=value.getAsJsonObject();
            if(originalIds.contains(clip.get("id").getAsString())) timed.add(clip.get("event").getAsString());
        }
        assertEquals(timed,added.stream().filter(k->k.startsWith("weapon.reload_w63."))
                .collect(java.util.stream.Collectors.toSet()));
        var ace=Set.of("weapon.ace_of_spades.fire", "weapon.ace_of_spades.reload",
                "weapon.reload_w83.ace_of_spades.55", "weapon.reload_w83.ace_of_spades.39");
        assertTrue(added.containsAll(ace));
        added.removeAll(ace);
        var izanagi=Set.of("weapon.izanagis_burden.fire", "weapon.izanagis_burden.reload",
                "weapon.izanagis_burden.honed_fire", "weapon.izanagis_burden.honed_reload");
        assertTrue(added.containsAll(izanagi));
        added.removeAll(izanagi);
        var izanagiTimed=ReloadAudioProfile.all().stream().filter(c->c.id().equals("izanagis_burden"))
                .map(ReloadAudioProfile.Clip::event).collect(java.util.stream.Collectors.toSet());
        assertTrue(izanagiTimed.add("weapon.reload_w84.izanagis_burden.honed.61"));
        assertEquals(Set.of("weapon.reload_w84.izanagis_burden.61", "weapon.reload_w84.izanagis_burden.honed.61"), izanagiTimed);
        var w84=json(Path.of("art/weapons/w84/audio/event-definitions.json"));
        for (String key : izanagiTimed) assertEquals(w84.get(key), now.get(key), "Exact additive W84 timed event " + key);
        assertEquals(izanagiTimed, added.stream().filter(k->k.startsWith("weapon.reload_w84."))
                .collect(java.util.stream.Collectors.toSet()));
        added.removeAll(izanagiTimed);
        var namedW102=new HashSet<String>();
        for (String id : Set.of("blast_furnace", "chattering_bone", "aishas_embrace", "long_arm", "whispering_slab", "retrofit_escapade"))
            namedW102.add("weapon." + id + ".fire");
        for (String id : Set.of("blast_furnace", "chattering_bone", "aishas_embrace", "retrofit_escapade"))
            namedW102.add("weapon." + id + ".reload");
        for (String pair : Set.of("aishas_embrace.46", "blast_furnace.24", "blast_furnace.43", "chattering_bone.24", "chattering_bone.34", "retrofit_escapade.90"))
            namedW102.add("weapon.reload_w102." + pair);
        var fragment=json(Path.of("art/weapons/w102/audio/event-definitions.json"));
        assertEquals(16,namedW102.size());assertEquals(namedW102,fragment.keySet());
        assertTrue(added.containsAll(namedW102));
        for (String key : namedW102) assertEquals(fragment.get(key),now.get(key));
        added.removeAll(namedW102);
        added.removeAll(timed);assertEquals(15,added.size());
        int clips=0;
        for(String key:added) {
            assertTrue(key.startsWith("weapon."));
            for(var x:now.getAsJsonObject(key).getAsJsonArray("sounds")) {
                var value=x.getAsJsonObject();assertTrue(value.get("name").getAsString().startsWith("destiny:w56/"));
                assertFalse(value.get("stream").getAsBoolean());assertEquals(32,value.get("attenuation_distance").getAsInt());clips++;
            }
        }
        assertEquals(51,clips);
    }
    @Test void everySelectedActionExistsAndSubtitleKeysHaveEnglishAndKoreanDefinitions() throws Exception {
        var defs=json(Path.of("src/main/resources/assets/destiny/sounds.json"));
        for(String id:List.of("abide_the_return","goldtusk","crown_splitter","falling_guillotine","temptation_s_hook")) {
            var e=sword(id);
            for(boolean heavy:new boolean[]{false,true})for(boolean empty:new boolean[]{false,true})for(boolean ground:new boolean[]{false,true})
                assertTrue(DestinySounds.has(SwordSounds.attackKey(e,heavy,empty,ground)));
            assertTrue(DestinySounds.has(SwordSounds.guardKey(e)));
        }
        assertTrue(DestinySounds.has(SwordSounds.CASTER_IMPACT));
        for(String lang:List.of("en_us","ko_kr")) {
            var translations=json(Path.of("src/main/resources/assets/destiny/lang/"+lang+".json"));
            for(var entry:defs.entrySet())if(entry.getKey().startsWith("weapon.")&&entry.getValue().getAsJsonObject().has("subtitle"))
                assertTrue(translations.has(entry.getValue().getAsJsonObject().get("subtitle").getAsString()),entry.getKey()+"/"+lang);
        }
    }
}
