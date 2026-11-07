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
    @Test void reviewedFrameEvidenceAndRuntimePolicyPreserveUnmeasuredInitialDelay() throws Exception {
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
        // The retired QA JPEG is not a shipped input. Retain its original identity
        // and validate the reproducible frame observations instead of requiring an
        // ephemeral local capture or claiming that the unavailable image was read.
        assertEquals("docs/qa/2026-10-24/w48/long-arm-reference-hud.jpg",crop.get("path").getAsString());
        assertEquals("8451d72ec5a8e89705292ac46e6e25697075070986ebf5eff835b2ca533fc463",crop.get("sha256").getAsString());
        var reference=e.getAsJsonObject("reference");
        assertEquals(25,reference.get("fps").getAsInt());
        assertEquals("5bcc330a9559b67950a2f46f807d1365f93fa81d769b87c1f69abbb1844d0574",reference.get("videoSha256").getAsString());
        var observations=e.getAsJsonArray("observations");assertEquals(2,observations.size());
        for(var value:observations) {
            var row=value.getAsJsonObject();
            assertEquals(row.get("previousFrame").getAsInt()+1,row.get("firstVisibleFrame").getAsInt());
            assertEquals(p.roundsPerInsert(),row.get("rounds").getAsInt()-row.get("previousRounds").getAsInt());
            assertEquals(row.get("firstVisibleFrame").getAsDouble()/25,row.get("firstVisibleSeconds").getAsDouble(),1e-9);
            assertEquals(row.get("previousFrame").getAsDouble()/25,row.get("previousSeconds").getAsDouble(),1e-9);
        }
        double interval=(observations.get(1).getAsJsonObject().get("firstVisibleFrame").getAsInt()
                -observations.get(0).getAsJsonObject().get("firstVisibleFrame").getAsInt())/25.0;
        assertEquals(.64,interval,1e-9);
        assertEquals(interval,e.get("observedIntervalSeconds").getAsDouble(),1e-9);
        assertEquals(1.0/25,e.get("frameResolutionSeconds").getAsDouble(),1e-9);
        assertTrue(Math.abs(p.reloadTicks()/20.0-interval)<=e.get("frameResolutionSeconds").getAsDouble(),
                "Authored per-pair ticks remain within the historical observation resolution");
    }
    private static String sha(Path p) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p)));
    }
}
