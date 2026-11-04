package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WeaponReloadPolicyW48Test {
    @Test void onlyExactSelectedLongArmOverridesHistoricalCurveAndKeepsOfficialCapacity() {
        for (var e:WeaponCatalog.all()) {
            var p=WeaponProfile.forEntry(e);var t=WeaponTiming.forEntry(e);
            if(e.id().equals("long_arm")) {
                assertEquals(8293111L,WeaponCharacteristics.of(e).bungieHash());
                assertEquals(14,p.magazine());assertTrue(p.infiniteReserve());
                assertTrue(p.shellReload());assertEquals(2,p.roundsPerInsert());
                assertEquals(20,p.firstReloadTicks());assertEquals(13,p.reloadTicks());
                assertEquals(42,t.reloadTicks().orElseThrow());assertFalse(t.shellReload());
            } else {
                assertEquals(t.shellReload(),p.shellReload(),e.id());
                assertEquals(t.shellReload()?1:0,p.roundsPerInsert(),e.id());
                assertEquals(p.reloadTicks(),p.firstReloadTicks(),e.id());
                if(t.supported())assertEquals(t.shellReload()?t.reloadPerRoundTicks().orElseThrow():t.reloadTicks().orElseThrow(),p.reloadTicks(),e.id());
            }
            assertEquals(WeaponFirePolicy.supportsAutomatic(e),p.automatic(),e.id());
        }
    }
    @Test void invalidOrForgedEntryNeverSelectsLongArmOverride() {
        var forged=new WeaponCatalog.Entry("long_arm","auto_rifle","aggressive","Wrong","Wrong","wrong");
        assertEquals(new WeaponReloadPolicy.Plan(42,42,0),WeaponReloadPolicy.forEntry(forged,42,false));
        assertEquals(new WeaponReloadPolicy.Plan(8,8,1),WeaponReloadPolicy.forEntry(null,8,true));
        assertThrows(IllegalArgumentException.class,()->new WeaponReloadPolicy.Plan(0,13,2));
        assertThrows(IllegalArgumentException.class,()->new WeaponReloadPolicy.Plan(20,0,2));
        assertThrows(IllegalArgumentException.class,()->new WeaponReloadPolicy.Plan(20,13,4));
    }
    @Test void referencePinsAndRuntimePolicyStayHonestAboutUnmeasuredInitialDelay() throws Exception {
        var e=JsonParser.parseString(Files.readString(Path.of("art/weapons/w48/reload-policy-evidence.json"))).getAsJsonObject();
        var policy=e.getAsJsonObject("policy");var p=WeaponProfile.forEntry(WeaponCatalog.find("long_arm").orElseThrow());
        assertEquals(p.firstReloadTicks(),policy.get("firstTicks").getAsInt());
        assertEquals(p.reloadTicks(),policy.get("intervalTicks").getAsInt());
        assertEquals(p.roundsPerInsert(),policy.get("roundsPerInsert").getAsInt());
        assertEquals("AUTHORED_REFERENCE_INFORMED_NOT_OFFICIAL_BASE_TIMING",policy.get("classification").getAsString());
        assertTrue(policy.get("firstDelay").getAsString().contains("not observable"));
        for(var pin:e.getAsJsonObject("sourceHashes").entrySet())
            assertEquals(pin.getValue().getAsString(),sha(Path.of(pin.getKey())));
        var crop=e.getAsJsonObject("reviewedHudExcerpt");
        assertEquals(crop.get("sha256").getAsString(),sha(Path.of(crop.get("path").getAsString())));
    }
    private static String sha(Path p) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p)));
    }
}
