package kim.biryeong.destiny.weapon;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/** Independent official eligibility, source and literal damage oracles. */
class PayloadW80Test {
    private static final long HASH = 3038247973L;
    private static final String REF = "art/weapons/w80/references/official-eligibility.json";
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
            new WeaponPerks.Roll("distant_relation", 2034817450L, 4, HASH, 3824767299L),
            new WeaponPerks.Roll("patron_of_lost_causes", 2723241847L, 4, HASH, 120674550L),
            new WeaponPerks.Roll("long_arm", 8293111L, 4, HASH, 619833418L),
            new WeaponPerks.Roll("bite_of_the_fox", 1403800851L, 4, HASH, 2442672691L),
            new WeaponPerks.Roll("apostate", 2164448701L, 4, HASH, 2826016044L));

    private static JsonObject evidence() throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(REF))).getAsJsonObject();
    }

    private static WeaponPerks.Roll roll(JsonObject row) {
        return new WeaponPerks.Roll(row.get("id").getAsString(), row.get("itemHash").getAsLong(),
                row.get("socketIndex").getAsInt(), row.get("perkHash").getAsLong(),
                row.get("plugSetHash").getAsLong());
    }

    @Test void runtimeProfileHasExactlyTheFiveImmutableBaseSocketsAndExplicitLocalRadialPolicy() throws Exception {
        assertEquals("explosive_payload", PayloadProfile.ID);
        assertEquals(3038247973L, PayloadProfile.HASH);
        var rolls = PayloadProfile.rolls();
        assertEquals(5, rolls.size());
        assertEquals(EXPECTED, new HashSet<>(rolls));
        assertThrows(UnsupportedOperationException.class, () -> rolls.add(EXPECTED.iterator().next()));
        assertThrows(UnsupportedOperationException.class, () -> rolls.set(0, EXPECTED.iterator().next()));
        assertThrows(UnsupportedOperationException.class, rolls::clear);
        assertEquals(EXPECTED, new HashSet<>(PayloadProfile.rolls()));
        var perk = PayloadProfile.perk();
        assertEquals(.5, perk.convertedBodyFraction());
        assertEquals(1.3, perk.pveExplosionMultiplier());
        assertEquals(3, PayloadProfile.radius());
        assertEquals(.25, perk.radialFloor());
        assertEquals("local_linear_floor_nearest_aabb", perk.radialPolicy());
        var path = Path.of("src/main/resources/destiny/weapons/w80-payload.json");
        try (var input = PayloadW80Test.class.getResourceAsStream("/destiny/weapons/w80-payload.json")) {
            assertNotNull(input);
            assertArrayEquals(Files.readAllBytes(path), input.readAllBytes());
        }
    }

    @Test void literalImpactCheckpointsSubtractConvertedBodyDamageRatherThanHalfOfCriticalDamage() {
        // B=20: body impact 10, explosion 13, crit M=2 impact 30 and total 43.
        assertEquals(10f, PayloadProfile.impact(20, 2, false, 1));
        assertEquals(30f, PayloadProfile.impact(20, 2, true, 1));
        assertEquals(25f, PayloadProfile.impact(20, 1.75, true, 1));
        assertEquals(50f, PayloadProfile.impact(20, 3, true, 1));
        assertEquals(90f, PayloadProfile.impact(20, 5, true, 1));
        assertEquals(10f, PayloadProfile.impact(20, 1, true, 1));
        assertEquals(13f, PayloadProfile.explosion(20));
        assertEquals(23f, PayloadProfile.impact(20, 2, false, 1) + PayloadProfile.explosion(20));
        assertEquals(43f, PayloadProfile.impact(20, 2, true, 1) + PayloadProfile.explosion(20));
        assertEquals(4f, PayloadProfile.impact(20, 2, false, .4));
        assertEquals(12f, PayloadProfile.impact(20, 2, true, .4));
        assertEquals(25f, PayloadProfile.impact(20, 2, true, .4) + PayloadProfile.explosion(20));
        assertEquals(0f, PayloadProfile.impact(20, 2, true, 0));
        assertEquals(6.5f, PayloadProfile.explosion(10));
        assertEquals(.65f, PayloadProfile.explosion(1));
    }

    @Test void localRadialCurveHasLiteralLinearCheckpointsAndQuarterFloorThroughInclusiveThreeMetres() {
        for (double[] point : new double[][]{{0, 1}, {-.0, 1}, {.75, .75}, {1.5, .5},
                {2, 1d / 3}, {2.25, .25}, {2.5, .25}, {3, .25}})
            assertEquals(point[1], PayloadProfile.splash(point[0]), .000001, "distance=" + point[0]);
        assertEquals(.25f, PayloadProfile.splash(Math.nextDown(3d)));
        assertEquals(0f, PayloadProfile.splash(Math.nextUp(3d)));
        float previous = 1;
        for (int step = 0; step <= 3000; step++) {
            float value = PayloadProfile.splash(step / 1000d);
            assertTrue(Float.isFinite(value) && value >= .25f && value <= previous);
            previous = value;
        }
    }

    @Test void invalidDamageAndDistanceInputsCannotProduceDamage() {
        for (float base : new float[]{0, -0f, -1, Float.NaN, Float.POSITIVE_INFINITY, Float.NEGATIVE_INFINITY}) {
            assertEquals(0f, PayloadProfile.explosion(base));
            assertEquals(0f, PayloadProfile.impact(base, 2, true, 1));
        }
        for (double multiplier : new double[]{Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY, 0, .99, 5.01})
            assertEquals(0f, PayloadProfile.impact(20, multiplier, true, 1));
        for (double falloff : new double[]{Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY, -.01, 1.01})
            assertEquals(0f, PayloadProfile.impact(20, 2, true, falloff));
        for (double distance : new double[]{Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY,
                -Double.MIN_VALUE, -1, Math.nextUp(3d), Double.MAX_VALUE})
            assertEquals(0f, PayloadProfile.splash(distance));
    }

    @Test void originalDdcRowAndModeLegendSupportSplitPrecisionCompensationAndPveMultiplier() throws Exception {
        var ddc = JsonParser.parseString(Files.readString(Path.of("art/weapons/w80/references/ddc-explosive-payload.json"))).getAsJsonObject();
        assertEquals("d8e45a514e221d5aabd0746f6d02bc5c44242e4e47a76a56e6774eba87246139", ddc.get("responseSha256").getAsString());
        String html = ddc.get("exactHtmlRow").getAsString();
        assertTrue(html.contains("Weapons deal 50% of their"));
        assertTrue(html.contains("Non-Precision"));
        assertTrue(html.contains("damaging enemies within 3 meters"));
        assertTrue(html.contains("New Ratio = (Base Ratio - 50%) / (1 - 50%)"));
        assertTrue(html.contains("color:#a4c2f4;\">30% increased"));
        var legend = JsonParser.parseString(Files.readString(Path.of("art/weapons/w80/references/ddc-mode-legend.json"))).getAsJsonObject();
        assertEquals("df4e2fe149d52fac8b6f1929d116561b968d2ea5bf55bc7994b5b8785f99cf14", legend.get("responseSha256").getAsString());
        assertTrue(legend.get("exactHtmlRow").getAsString().contains("Combatants, their Constructs, and other PVE Activities"));
        assertTrue(legend.getAsJsonArray("exactReferencedCssRules").asList().stream()
                .map(JsonElement::getAsString).anyMatch(rule -> rule.contains(".s78{") && rule.contains("color:#a4c2f4")));
        assertEquals("community", PayloadProfile.perk().mechanicsSource().authority());
        assertEquals(ddc.get("sourceUrl").getAsString(), PayloadProfile.perk().mechanicsSource().url());
        assertEquals(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(
                Path.of("art/weapons/w80/references/ddc-explosive-payload.json")))),
                PayloadProfile.perk().mechanicsSource().sha256());
    }

    @Test void exactFiveBaseRowsJoinTheirRetainedOfficialRandomizedPoolsIncludingZeroWeight() throws Exception {
        var proof = evidence();
        var rows = proof.getAsJsonArray("eligible");
        assertEquals(5, rows.size());
        var seen = new HashSet<WeaponPerks.Roll>();
        for (var element : rows) {
            var row = element.getAsJsonObject();
            var candidate = roll(row);
            assertTrue(EXPECTED.contains(candidate), candidate.toString());
            assertTrue(seen.add(candidate), "Duplicate eligibility " + candidate);
            assertEquals("randomizedPlugSetHash", row.get("field").getAsString());
            assertTrue(row.get("traitCategory").getAsBoolean());
            assertFalse(row.get("isFakePlugSet").getAsBoolean());
            var pool = proof.getAsJsonObject("rawRelevantPlugSets")
                    .getAsJsonObject(Long.toString(candidate.plugSetHash()));
            assertEquals(candidate.plugSetHash(), pool.get("hash").getAsLong());
            assertFalse(pool.get("isFakePlugSet").getAsBoolean());
            int index = row.get("poolEntryIndex").getAsInt();
            assertTrue(index >= 0 && index < pool.getAsJsonArray("reusablePlugItems").size());
            var raw = pool.getAsJsonArray("reusablePlugItems").get(index).getAsJsonObject();
            assertEquals(raw, row.getAsJsonObject("rawPoolEntry"));
            assertEquals(HASH, raw.get("plugItemHash").getAsLong());
            assertTrue(raw.get("currentlyCanRoll").getAsBoolean());
            assertEquals(0d, raw.get("weight").getAsDouble(), "Zero weight is still a rollable base perk");
        }
        assertEquals(EXPECTED, seen);
    }

    @Test void retainedSocketCategoriesAndEntriesAuthorizeExactlyTheSameFiveRows() throws Exception {
        var proof = evidence();
        var positives = proof.getAsJsonArray("positiveProofs");
        assertEquals(5, positives.size());
        var seen = new HashSet<String>();
        for (var element : positives) {
            var positive = element.getAsJsonObject();
            String id = positive.get("id").getAsString();
            assertTrue(seen.add(id));
            var expected = EXPECTED.stream().filter(r -> r.id().equals(id)).findFirst().orElseThrow();
            assertEquals(expected.hash(), positive.get("itemHash").getAsLong());
            assertTrue(positive.getAsJsonArray("rawSocketCategories").asList().stream()
                    .map(JsonElement::getAsJsonObject)
                    .filter(c -> c.get("socketCategoryHash").getAsLong() == 4241085061L)
                    .flatMap(c -> c.getAsJsonArray("socketIndexes").asList().stream())
                    .anyMatch(i -> i.getAsInt() == 4), id);
            var occurrences = positive.getAsJsonArray("occurrences").asList().stream()
                    .map(JsonElement::getAsJsonObject).toList();
            var pooled = occurrences.stream().filter(o -> o.has("rawPoolEntry")).toList();
            assertEquals(1, pooled.size(), id);
            assertEquals(expected, roll(pooled.getFirst()));
            for (var direct : occurrences.stream().filter(o -> o.has("rawSocketEntry")).toList()) {
                assertEquals(4, direct.get("socketIndex").getAsInt());
                var socket = direct.getAsJsonObject("rawSocketEntry");
                assertEquals(expected.plugSetHash(), socket.get("randomizedPlugSetHash").getAsLong());
                assertEquals(HASH, socket.get("singleInitialItemHash").getAsLong());
                assertTrue(socket.getAsJsonArray("reusablePlugItems").asList().stream()
                        .map(JsonElement::getAsJsonObject).anyMatch(r -> r.get("plugItemHash").getAsLong() == HASH));
            }
        }
        assertEquals(EXPECTED.stream().map(WeaponPerks.Roll::id).collect(Collectors.toSet()), seen);
    }

    @Test void allSixtyThreeCatalogHashesAreAuditedWithoutFamilyWideEligibility() throws Exception {
        var proof = evidence();
        var coverage = proof.getAsJsonObject("coverage");
        assertEquals(63, coverage.get("selectedWeapons").getAsInt());
        assertEquals(678, coverage.get("socketEntries").getAsInt());
        assertEquals(627, coverage.get("referencedPlugSetFields").getAsInt());
        var rows = proof.getAsJsonArray("allSelectedAudit");
        assertEquals(63, rows.size());
        var audit = rows.asList().stream().map(JsonElement::getAsJsonObject)
                .collect(Collectors.toMap(r -> r.get("id").getAsString(), r -> r));
        assertEquals(WeaponCatalogTest.originalW30Entries().stream().map(WeaponCatalog.Entry::id).collect(Collectors.toSet()), audit.keySet());
        int sockets = 0;
        for (var entry : WeaponCatalogTest.originalW30Entries()) {
            var row = audit.get(entry.id());
            assertEquals(WeaponCharacteristics.of(entry).bungieHash(), row.get("itemHash").getAsLong(), entry.id());
            long eligible = EXPECTED.stream().filter(r -> r.id().equals(entry.id())).count();
            // Distant Relation and Apostate also retain a direct socket occurrence.
            long occurrences = Set.of("distant_relation", "apostate").contains(entry.id()) ? 2 : eligible;
            assertEquals(occurrences, row.get("baseExplosivePayloadOccurrences").getAsLong(), entry.id());
            if (eligible == 1) assertTrue(row.getAsJsonArray("traitSocketIndexes").asList().stream()
                    .anyMatch(i -> i.getAsInt() == 4), entry.id());
            sockets += row.get("socketCount").getAsInt();
        }
        assertEquals(678, sockets);
        var families = EXPECTED.stream().map(r -> WeaponCatalog.find(r.id()).orElseThrow().family())
                .collect(Collectors.groupingBy(f -> f, Collectors.counting()));
        assertEquals(Map.of("scout_rifle", 3L, "sniper_rifle", 2L), families);
        for (var candidate : EXPECTED) {
            var entry = WeaponCatalog.find(candidate.id()).orElseThrow();
            assertEquals(candidate.hash(), WeaponCharacteristics.of(entry).bungieHash());
            assertFalse(WeaponCharacteristics.of(entry).exotic());
            var profile = WeaponProfile.forEntry(entry);
            assertEquals(WeaponProfile.Mode.HITSCAN, profile.mode());
            assertEquals(0, profile.chargeTicks());
            assertEquals(1, profile.burst());
            assertEquals(1, profile.pellets());
        }
    }

    @Test void enhancedAndTimedPayloadDefinitionsCannotMasqueradeAsTheBasePerk() throws Exception {
        var proof = evidence();
        var definitions = proof.getAsJsonObject("rawPerkDefinitions");
        for (long hash : new long[]{HASH, 64866129L})
            assertEquals(hash, definitions.getAsJsonObject(Long.toString(hash)).get("hash").getAsLong());
        assertEquals("Explosive Payload", definitions.getAsJsonObject("3038247973")
                .getAsJsonObject("displayProperties").get("name").getAsString());
        var excluded = proof.getAsJsonArray("excludedTimedOrEnhancedOccurrences");
        assertTrue(excluded.isEmpty(), "Current official selected hashes contain no enhanced/Timed Payload occurrence");
        assertFalse(proof.get("excludedTimedOrEnhancedOccurrencesNote").getAsString().isBlank());
        assertTrue(EXPECTED.stream().noneMatch(r -> r.id().equals("seventh_seraph_officer_revolver")));
    }

    @Test void distantRelationRetainsExclusiveDragonflyPoolAndCompatibleHolsterSocket() throws Exception {
        var proof = evidence();
        var distant = proof.getAsJsonArray("positiveProofs").asList().stream()
                .map(JsonElement::getAsJsonObject).filter(r -> r.get("id").getAsString().equals("distant_relation"))
                .findFirst().orElseThrow();
        var traits = proof.getAsJsonObject("rawRelevantPlugSets").getAsJsonObject("3824767299")
                .getAsJsonArray("reusablePlugItems").asList().stream().map(JsonElement::getAsJsonObject)
                .filter(r -> r.get("currentlyCanRoll").getAsBoolean())
                .map(r -> r.get("plugItemHash").getAsLong()).collect(Collectors.toSet());
        assertTrue(traits.containsAll(Set.of(3038247973L, 2848615171L)));
        var compatible = distant.getAsJsonArray("rampageAndAutoLoadingHolsterOccurrences");
        assertEquals(1, compatible.size());
        var holster = compatible.get(0).getAsJsonObject();
        assertEquals(3, holster.get("socketIndex").getAsInt());
        assertEquals("randomizedPlugSetHash", holster.get("field").getAsString());
        assertEquals(1131958073L, holster.get("plugSetHash").getAsLong());
        assertEquals(3300816228L, holster.get("plugItemHash").getAsLong());
        var raw = holster.getAsJsonObject("rawPoolEntry");
        assertTrue(raw.get("currentlyCanRoll").getAsBoolean());
        assertTrue(proof.getAsJsonObject("rawRelevantPlugSets").getAsJsonObject("1131958073")
                .getAsJsonArray("reusablePlugItems").asList().contains(raw));
    }

    @Test void publicEvidencePinsOfficialInputsWithoutReadingPrivateCaches() throws Exception {
        var proof = evidence();
        var manifest = proof.getAsJsonObject("officialManifest");
        assertEquals("245114.26.10.13.2000-1-bnet.66137", manifest.get("version").getAsString());
        String prefix = "https://www.bungie.net/common/destiny2_content/json/en/";
        String suffix = "-e677f6ea-2a1e-48d4-a8c8-700a39a62585.json";
        assertEquals(prefix + "DestinyInventoryItemDefinition" + suffix, manifest.get("inventoryUrl").getAsString());
        assertEquals(prefix + "DestinyPlugSetDefinition" + suffix, manifest.get("plugSetsUrl").getAsString());
        var pins = proof.getAsJsonObject("sourcePins");
        var hashes = Map.of(
                "selected", "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
                "catalog", "3e9377cce928958a89208ce69f34210fe7e17ae17afd1f4959bb418b1ed120f5",
                "inventory", "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
                "plugSets", "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
                "manifest", "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce");
        assertEquals(hashes.keySet(), pins.keySet());
        for (var pin : hashes.entrySet()) {
            var source = pins.getAsJsonObject(pin.getKey());
            assertEquals(pin.getValue(), source.get("sha256").getAsString());
            assertTrue(source.get("bytes").getAsLong() > 0);
        }
        for (String key : Set.of("selected", "catalog")) {
            var pin = pins.getAsJsonObject(key);
            var path = Path.of(key.equals("selected") ? "art/weapons/w40/definitions.json" : "art/weapons/w30/catalog.json");
            assertEquals(path.toString(), pin.get("path").getAsString());
            assertEquals(Files.size(path), pin.get("bytes").getAsLong());
            assertEquals(hashes.get(key), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(Files.readAllBytes(path))));
        }
    }
}
