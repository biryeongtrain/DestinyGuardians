package kim.biryeong.destiny.weapon;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.OptionalDouble;
import java.util.OptionalInt;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Pure source/resource tests; no Minecraft bootstrap, server or runtime integration. */
class WeaponTimingW46Test {
    private static WeaponTiming.Timing timing(String id) {
        return WeaponTiming.forEntry(WeaponCatalog.find(id).orElseThrow());
    }

    private static JsonObject artifact(String file) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of("art/weapons/w46", file))).getAsJsonObject();
    }

    private static JsonArray resource(String file) throws Exception {
        var stream = WeaponTimingW46Test.class.getResourceAsStream("/destiny/weapons/" + file);
        assertNotNull(stream);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader).getAsJsonArray();
        }
    }

    @Test void all63HaveExplicitSupportAndMissingValues() throws Exception {
        assertEquals(63, WeaponCatalogTest.originalW30Entries().size());
        var ids = new HashSet<String>();
        for (var row : resource("w46-timing.json")) assertTrue(ids.add(row.getAsJsonObject().get("id").getAsString()));
        assertEquals(63, ids.size());
        assertEquals(new HashSet<>(WeaponCatalogTest.originalW30Entries().stream().map(WeaponCatalog.Entry::id).toList()), ids);
        int supported = 0;
        for (var entry : WeaponCatalogTest.originalW30Entries()) {
            var t = WeaponTiming.of(entry);
            assertSame(t, WeaponTiming.forEntry(entry));
            assertTrue(ids.contains(entry.id()));
            assertEquals(!entry.family().equals("sword"), t.supported());
            if (t.supported()) supported++;
            assertTrue(t.burstSize() >= 1 && t.burstSize() <= 9);
            t.cadenceTicks().ifPresent(v -> assertTrue(Double.isFinite(v) && v > 0));
            t.burstSpacingTicks().ifPresent(v -> assertTrue(Double.isFinite(v) && v >= 0));
        }
        assertEquals(58, supported);
    }

    @Test void positiveMagazineAndRpmAreExactOfficialValuesNotFamilyGuesses() throws Exception {
        for (var row : resource("w40-characteristics.json")) {
            var r = row.getAsJsonObject();
            var t = timing(r.get("id").getAsString());
            var stats = r.getAsJsonObject("stats");
            for (var hash : new String[]{"3871231066", "4284893193"}) {
                var actual = hash.equals("3871231066") ? t.magazine() : t.rpm();
                if (stats.has(hash) && stats.get(hash).getAsInt() > 0)
                    assertEquals(stats.get(hash).getAsInt(), actual.orElseThrow());
                else assertTrue(actual.isEmpty());
            }
        }
        assertEquals(94, timing("retraced_path").magazine().orElseThrow());
        assertEquals(491, timing("high_albedo").rpm().orElseThrow());
        assertEquals(325, timing("brass_attacks").rpm().orElseThrow());
        assertTrue(timing("biting_winds").magazine().isEmpty());
        assertEquals(50, timing("abide_the_return").magazine().orElseThrow());
    }

    @Test void actualOfficialDefinitionsVerifyHashNamesAndMillisecondUnits() throws Exception {
        var defs = artifact("stat-definitions.json");
        assertEquals("Magazine", defs.getAsJsonObject("3871231066").getAsJsonObject("displayProperties").get("name").getAsString());
        assertEquals("Rounds Per Minute", defs.getAsJsonObject("4284893193").getAsJsonObject("displayProperties").get("name").getAsString());
        assertEquals("Reload Speed", defs.getAsJsonObject("4188031367").getAsJsonObject("displayProperties").get("name").getAsString());
        for (var hash : new String[]{"2961396640", "447667954"})
            assertTrue(defs.getAsJsonObject(hash).getAsJsonObject("displayProperties").get("description").getAsString().contains("milliseconds"));
        var meta = artifact("extraction.json");
        assertTrue(meta.get("officialStatSource").getAsString().endsWith("DestinyStatDefinition-e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"));
        assertEquals("b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
                meta.getAsJsonObject("officialManifest").get("cachedInventorySha256").getAsString());
    }

    @Test void chargeDrawCeilWithoutMisinterpretingReusedStats() {
        assertEquals(967, timing("erentil_fr4").chargeMillis().orElseThrow());
        assertEquals(20, timing("erentil_fr4").chargeTicks().orElseThrow());
        assertEquals(11, timing("stormchaser").chargeTicks().orElseThrow());
        assertEquals(667, timing("biting_winds").drawMillis().orElseThrow());
        assertEquals(14, timing("biting_winds").drawTicks().orElseThrow());
        assertEquals(12, timing("whispering_slab").drawTicks().orElseThrow());
        for (var entry : WeaponCatalog.all()) {
            var t = WeaponTiming.of(entry);
            boolean charged = entry.family().equals("fusion_rifle") || entry.family().equals("linear_fusion_rifle");
            assertEquals(charged, t.chargeTicks().isPresent());
            assertEquals(entry.family().equals("bow"), t.drawTicks().isPresent());
        }
        assertEquals(7, timing("nezarec_s_whisper").magazine().orElseThrow());
        assertEquals(55, timing("nezarec_s_whisper").rpm().orElseThrow());
        assertTrue(timing("nezarec_s_whisper").chargeMillis().isEmpty());
        assertTrue(timing("abide_the_return").chargeMillis().isEmpty());
    }

    @Test void fractionalNormalAndRealBurstCadenceUseCorrectUnits() throws Exception {
        assertEquals(1200.0 / 400, timing("halfdan_d").cadenceTicks().orElseThrow(), 1e-10);
        assertEquals(1200.0 / 1000, timing("retraced_path").cadenceTicks().orElseThrow(), 1e-10);
        assertEquals(3, timing("cold_denial").burstSize());
        assertEquals((12 + 2 * 2) * 20.0 / 30, timing("cold_denial").cadenceTicks().orElseThrow(), 1e-10);
        assertEquals(4, timing("blast_furnace").burstSize());
        assertEquals(2 * 20.0 / 30, timing("blast_furnace").burstSpacingTicks().orElseThrow(), 1e-10);
        assertEquals((7 + 2 * 2) * 20.0 / 30, timing("high_albedo").cadenceTicks().orElseThrow(), 1e-10);
        assertEquals(2, timing("brass_attacks").burstSize());
        assertEquals((8 + 3) * 20.0 / 30, timing("brass_attacks").cadenceTicks().orElseThrow(), 1e-10);
        assertTrue(timing("biting_winds").cadenceTicks().isEmpty());
        var build = Files.readString(Path.of("art/weapons/w46/build.rs"));
        assertTrue(build.contains("burst_delay: value.burst_delay / 30.0"));
        assertTrue(build.contains("inner_burst_delay: value.inner_burst_delay / 30.0"));
    }

    @Test void chargedLockoutExcludesNextChargeAndBoltsShareAmmo() {
        assertEquals(5, timing("erentil_fr4").burstSize());
        assertEquals(7, timing("hollow_words").burstSize());
        assertEquals(9, timing("null_composure").burstSize());
        assertEquals(1 * 20.0 / 30, timing("null_composure").burstSpacingTicks().orElseThrow(), 1e-10);
        assertEquals(9 + 8 * 20.0 / 30, timing("null_composure").cadenceTicks().orElseThrow(), 1e-10);
        assertEquals(0, timing("coriolis_force").burstSpacingTicks().orElseThrow());
        assertEquals(9, timing("coriolis_force").cadenceTicks().orElseThrow());
        assertEquals(3, timing("stormchaser").burstSize());
        assertEquals(5 * 20.0 / 30, timing("stormchaser").burstSpacingTicks().orElseThrow(), 1e-10);
        assertEquals(19 + 2 * 5 * 20.0 / 30, timing("stormchaser").cadenceTicks().orElseThrow(), 1e-10);
        assertEquals(19, timing("line_in_the_sand").cadenceTicks().orElseThrow());
        for (var entry : WeaponCatalog.all().stream().filter(e -> !WeaponExotics.expanded(e)).toList())
            assertEquals(entry.family().equals("fusion_rifle") || entry.family().equals("linear_fusion_rifle"),
                    WeaponTiming.of(entry).sharedBurstAmmo());
    }

    @Test void approximateReloadCurveIsSecondsButShellsNeverWholeMagazine() throws Exception {
        var meta = artifact("extraction.json");
        int shellCount = 0;
        for (var value : meta.getAsJsonArray("entries")) {
            var row = value.getAsJsonObject();
            var t = timing(row.get("id").getAsString());
            if (!t.supported()) { assertTrue(t.reloadTicks().isEmpty()); continue; }
            var curve = row.getAsJsonObject("reloadCurve");
            int x = row.get("reloadStatUsed").getAsInt();
            double seconds = curve.get("evpp").getAsDouble() * x * x
                    + curve.get("vpp").getAsDouble() * x + curve.get("offset").getAsDouble();
            assertEquals(seconds, row.get("reloadSeconds").getAsDouble(), 1e-12);
            int ticks = (int) Math.ceil(seconds * 20);
            if (t.shellReload()) {
                shellCount++;
                assertTrue(t.reloadTicks().isEmpty());
                assertEquals(ticks, t.reloadPerRoundTicks().orElseThrow());
                assertTrue(t.reloadInitialTicks().isEmpty());
            } else {
                assertEquals(ticks, t.reloadTicks().orElseThrow());
                assertTrue(t.reloadPerRoundTicks().isEmpty());
            }
        }
        assertEquals(5, shellCount); // Only the five shotguns, never Long Arm.
        assertFalse(timing("long_arm").shellReload());
        assertTrue(timing("long_arm").reloadPerRoundTicks().isEmpty());
        assertEquals(42, timing("long_arm").reloadTicks().orElseThrow());
        assertEquals(1, timing("mindbender_s_ambition_adept").burstSize());
        assertEquals(1, timing("ikelos_sg_v1_0_1").burstSize());
        assertFalse(timing("mindbender_s_ambition_adept").sharedBurstAmmo());
    }

    @Test void provenancePinsEverySourceAndRuntimeByte() throws Exception {
        var meta = artifact("extraction.json");
        assertEquals(63, meta.get("profileCount").getAsInt());
        assertEquals(58, meta.get("supportedCount").getAsInt());
        assertEquals("dcd0c7d302b056ffbb532edcb711d724a17ca8c1", meta.get("commit").getAsString());
        for (var source : meta.getAsJsonObject("sourceHashes").entrySet())
            assertEquals(source.getValue().getAsString(), sha(Files.readAllBytes(Path.of(source.getKey()))), source.getKey());
        assertEquals(meta.get("runtimeSha256").getAsString(), sha(Files.readAllBytes(Path.of("src/main/resources/destiny/weapons/w46-timing.json"))));
    }

    @Test void missingAndUnsafeValuesCannotMasqueradeAsExactZero() {
        assertThrows(NullPointerException.class, () -> WeaponTiming.of(null));
        assertThrows(IllegalArgumentException.class, () -> WeaponTiming.of(
                new WeaponCatalog.Entry("not_selected", "auto_rifle", "adaptive", "Unknown", "Adaptive", "unknown")));
        var t = timing("austringer");
        assertThrows(IllegalArgumentException.class, () -> new WeaponTiming.Timing(
                true, OptionalInt.of(0), t.rpm(), t.chargeMillis(), t.drawMillis(),
                t.cadenceTicks(), t.burstSpacingTicks(), t.burstSize(), t.sharedBurstAmmo(),
                t.chargeTicks(), t.drawTicks(), t.reloadTicks(), t.shellReload(),
                t.reloadPerRoundTicks(), t.reloadInitialTicks()));
        assertThrows(IllegalArgumentException.class, () -> new WeaponTiming.Timing(
                true, t.magazine(), t.rpm(), t.chargeMillis(), t.drawMillis(),
                OptionalDouble.of(Double.NaN), t.burstSpacingTicks(), t.burstSize(), t.sharedBurstAmmo(),
                t.chargeTicks(), t.drawTicks(), t.reloadTicks(), t.shellReload(),
                t.reloadPerRoundTicks(), t.reloadInitialTicks()));
    }

    private static String sha(byte[] raw) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
    }
}
