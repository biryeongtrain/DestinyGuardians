package kim.biryeong.destiny.sound;

import com.google.gson.JsonParser;
import kim.biryeong.destiny.weapon.*;
import org.junit.jupiter.api.Test;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import static org.junit.jupiter.api.Assertions.*;

class ReloadAudioProfileW63Test {
    // Historical exact-duration recordings; W327 explicitly reuses base audio and is checked separately.
    @Test void everyWholeMagazineHasExactlyItsRealBasePhase() {
        int expected=0;
        for(var e:WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id())).toList()) {
            var p=WeaponProfile.forEntry(e);
            boolean eligible=p.mode()!=WeaponProfile.Mode.MELEE&&!p.shellReload()&&!e.family().equals("bow");
            var clip=ReloadAudioProfile.find(e,p.firstReloadTicks());
            assertEquals(eligible,clip.isPresent(),e.id());
            if(!eligible)continue;
            expected++;assertEquals(e.id(),clip.orElseThrow().id());
            assertEquals(p.firstReloadTicks(),clip.orElseThrow().ticks());
        }
        assertTrue(expected>40,"Coverage is all selected full-magazine weapons, not only the easiest few");
    }
    @Test void everySupportedFullMagazineOutlawVariantUsesModifiedCurveDeadline() {
        int count=0;
        for(var row:OutlawProfile.rolls().stream().filter(r -> !LegendaryWeapons.contains(r.id())).toList()) {
            var e=WeaponCatalog.find(row.id()).orElseThrow();var p=WeaponProfile.forEntry(e);
            var boost=OutlawProfile.reload(e);var clip=ReloadAudioProfile.find(e,boost.firstTicks());
            if(p.shellReload()) {assertTrue(clip.isEmpty(),"No full reload sound on each shell");continue;}
            assertEquals(boost.firstTicks(),clip.orElseThrow().ticks());
            assertNotEquals(ReloadAudioProfile.find(e,p.firstReloadTicks()).orElseThrow().event(),clip.orElseThrow().event());count++;
        }
        assertEquals(11,count);
        var duke=WeaponCatalog.find("duke_mk_44").orElseThrow();
        assertEquals(33,ReloadAudioProfile.find(duke,33).orElseThrow().ticks());
        assertEquals(59,ReloadAudioProfile.find(duke,59).orElseThrow().ticks());
    }
    @Test void unsupportedDurationsAndNullQueriesNeverInventVariants() {
        var e=WeaponCatalog.find("duke_mk_44").orElseThrow();
        for(int ticks:new int[]{Integer.MIN_VALUE,-1,0,1,32,34,58,60,1201,Integer.MAX_VALUE})
            assertTrue(ReloadAudioProfile.find(e,ticks).isEmpty(),"Unknown deadline "+ticks);
        assertTrue(ReloadAudioProfile.find(null,59).isEmpty());
        assertThrows(UnsupportedOperationException.class,()->ReloadAudioProfile.all().clear());
    }
    @Test void allAliasesResolveToIntendedMonoResourcesWithOriginalEventIdentity() throws Exception {
        try(var in=getClass().getResourceAsStream("/assets/destiny/sounds.json")) {
            assertNotNull(in);var table=JsonParser.parseReader(new InputStreamReader(in,StandardCharsets.UTF_8)).getAsJsonObject();
            var keys=new HashSet<String>();
            for(var c:ReloadAudioProfile.all()) {
                assertTrue(keys.add(c.id()+":"+c.ticks()));assertTrue(DestinySounds.has(c.event()));
                assertEquals(DestinySounds.weaponKey(WeaponCatalog.find(c.id()).orElseThrow(),"reload"),c.sourceEvent());
                var sound=table.getAsJsonObject(c.event()).getAsJsonArray("sounds");assertEquals(1,sound.size());
                var record=sound.get(0);var name=record.isJsonPrimitive()?record.getAsString():record.getAsJsonObject().get("name").getAsString();
                assertEquals(c.asset(),"assets/destiny/sounds/"+name.substring("destiny:".length())+".ogg");
                try(var clip=getClass().getResourceAsStream("/"+c.asset())) {assertNotNull(clip,c.event());assertEquals("OggS",new String(clip.readNBytes(4),StandardCharsets.US_ASCII));}
            }
        }
    }
}
