package kim.biryeong.destiny.weapon;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/** Pure profile, source and damage contracts; selected stacks and combat events belong in GameTests. */
class DragonflyW77Test {
    private static final long HASH = 2848615171L;
    private static final String RESOURCE = "/destiny/weapons/w77-dragonfly.json";
    private static final String REF = "art/weapons/w77/references/";
    private static final double EPSILON = 0.000001;
    // Exact base rows checked against the pinned inventory and real randomized plug sets.
    // Literal identities also catch a generator and runtime resource changing together.
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
            new WeaponPerks.Roll("brass_attacks", 2121785039L, 4, HASH, 3403850295L),
            new WeaponPerks.Roll("distant_relation", 2034817450L, 4, HASH, 3824767299L),
            new WeaponPerks.Roll("line_in_the_sand", 946443267L, 4, HASH, 3257645194L),
            new WeaponPerks.Roll("long_arm", 8293111L, 4, HASH, 619833418L));

    private static JsonObject json(String file) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(file))).getAsJsonObject();
    }

    private static JsonObject resource() throws Exception {
        try (var input = DragonflyW77Test.class.getResourceAsStream(RESOURCE)) {
            assertNotNull(input, "W77 profile must be on the test classpath");
            try (var reader = new InputStreamReader(input, StandardCharsets.UTF_8)) {
                return JsonParser.parseReader(reader).getAsJsonObject();
            }
        }
    }

    private static String sha256(Path file) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file)));
    }

    private static WeaponPerks.Roll roll(JsonObject row) {
        return new WeaponPerks.Roll(row.get("id").getAsString(), row.get("hash").getAsLong(),
                row.get("socket").getAsInt(), row.get("perkHash").getAsLong(), row.get("plugSetHash").getAsLong());
    }

    @Test void exactBaseIdentityAndFourOfficialSocketsMatchTheClasspathProfile() throws Exception {
        assertEquals("dragonfly", DragonflyProfile.ID);
        assertEquals(HASH, DragonflyProfile.HASH);
        assertEquals(4, DragonflyProfile.rolls().size());
        assertEquals(EXPECTED, new HashSet<>(DragonflyProfile.rolls()));
        assertEquals(4, DragonflyProfile.rolls().stream().map(WeaponPerks.Roll::id).distinct().count());
        var data = resource();
        assertEquals("W77", data.get("stage").getAsString());
        var perk = data.getAsJsonObject("perk");
        assertEquals("dragonfly", perk.get("id").getAsString());
        assertEquals(HASH, perk.get("hash").getAsLong());
        var rows = data.getAsJsonArray("weapons");
        assertEquals(4, rows.size());
        for (var element : rows)
            assertEquals(Set.of("id", "hash", "socket", "perkHash", "plugSetHash"), element.getAsJsonObject().keySet());
        assertEquals(EXPECTED, rows.asList().stream().map(JsonElement::getAsJsonObject)
                .map(DragonflyW77Test::roll).collect(Collectors.toSet()));
    }

    @Test void allSixtyThreeSelectedWeaponsHaveExactEligibilityWithoutFamilyOrElementWideGrants() {
        WeaponCatalogTest.assertExpandedCatalog();
        var ids = new HashSet<String>();
        int eligibleWeapons = 0;
        for (var entry : WeaponCatalog.all()) {
            assertTrue(ids.add(entry.id()), "Duplicate catalog id " + entry.id());
            var expected = EXPECTED.stream().filter(r -> r.id().equals(entry.id())).collect(Collectors.toSet());
            var actual = DragonflyProfile.rolls().stream().filter(r -> r.id().equals(entry.id())).toList();
            assertEquals(expected.size(), actual.size(), entry.id());
            assertEquals(expected, new HashSet<>(actual), entry.id());
            var meta = WeaponCharacteristics.of(entry);
            for (var candidate : actual) {
                eligibleWeapons++;
                assertEquals(meta.bungieHash(), candidate.hash(), entry.id());
                assertEquals(HASH, candidate.perkHash(), entry.id());
                assertEquals(4, candidate.socket(), entry.id());
                assertTrue(candidate.plugSetHash() > 0 && candidate.plugSetHash() <= 0xffffffffL);
                assertFalse(meta.exotic(), entry.id());
                assertTrue(Set.of(WeaponCharacteristics.Damage.ARC, WeaponCharacteristics.Damage.SOLAR,
                        WeaponCharacteristics.Damage.VOID).contains(meta.damage()), entry.id());
                assertTrue(Set.of("scout_rifle", "sidearm", "linear_fusion_rifle").contains(entry.family()), entry.id());
            }
        }
        assertEquals(4, eligibleWeapons);
        // Same family and allowed element are insufficient: these exact official pools have no base Dragonfly.
        for (var id : List.of("aishas_embrace", "dead_man_walking_xx7463", "stormchaser",
                "ammit_ar2", "apostate", "retraced_path", "fixed_odds", "nezarec_s_whisper",
                "falling_guillotine", "dimensional_hypotrochoid", "frontier_justice", "whispering_slab")) {
            assertTrue(WeaponCatalog.find(id).isPresent(), "Exclusion must name a selected weapon: " + id);
            assertTrue(DragonflyProfile.rolls().stream().noneMatch(r -> r.id().equals(id)), id);
        }
    }

    @Test void loadedRollsAreImmutableAndFailedMutationsCannotChangeThePool() {
        var rolls = DragonflyProfile.rolls();
        var replacement = new WeaponPerks.Roll("stormchaser", 3652506829L, 4, HASH, 4213354588L);
        assertThrows(UnsupportedOperationException.class, () -> rolls.add(replacement));
        assertThrows(UnsupportedOperationException.class, () -> rolls.set(0, replacement));
        assertThrows(UnsupportedOperationException.class, () -> rolls.remove(0));
        assertThrows(UnsupportedOperationException.class, rolls::clear);
        assertEquals(EXPECTED, new HashSet<>(DragonflyProfile.rolls()));
        assertEquals(4, DragonflyProfile.rolls().size());
    }

    @Test void radiusIsCommunitySourcedWhileDamageAndFalloffAreExplicitLocalHpPolicies() throws Exception {
        assertEquals(4.5, DragonflyProfile.radius());
        assertEquals(10f, DragonflyProfile.damage());
        assertEquals(.3f, DragonflyProfile.falloffFloor());
        var perk = DragonflyProfile.perk();
        assertEquals("dragonfly", perk.id());
        assertEquals(HASH, perk.hash());
        assertEquals(4.5, perk.radiusMeters());
        assertEquals(10f, perk.damageHp());
        assertEquals(.3f, perk.falloffFloor());
        assertEquals("community", perk.radiusSource().authority());
        assertEquals("https://www.light.gg/db/items/2848615171/dragonfly/", perk.radiusSource().url());
        assertEquals("official", perk.officialChange().authority());
        assertEquals("https://www.bungie.net/7/en/News/Article/twid_07_03_2025", perk.officialChange().url());
        assertEquals("local_authored_pve", perk.damagePolicy().authority());
        assertEquals("Minecraft HP", perk.damagePolicy().units());
        assertEquals("fixed_perk_damage", perk.damagePolicy().scaling());
        assertFalse(perk.damagePolicy().description().isBlank());
        assertEquals("local_authored_pve", perk.falloffPolicy().authority());
        assertEquals("damage fraction", perk.falloffPolicy().units());
        assertEquals("linear_floor", perk.falloffPolicy().scaling());
        assertFalse(perk.falloffPolicy().description().isBlank());
        var raw = resource().getAsJsonObject("perk");
        assertEquals(4.5, raw.get("radiusMeters").getAsDouble());
        assertEquals(10f, raw.get("damageHp").getAsFloat());
        assertEquals(.3f, raw.get("falloffFloor").getAsFloat());
        var research = json(REF + "research.json");
        for (var source : List.of(perk.radiusSource(), perk.officialChange())) {
            var evidence = research.getAsJsonObject(source.authority().equals("community") ? "community" : "official");
            assertEquals(evidence.get("url").getAsString(), source.url());
            assertEquals(evidence.get("sourceSha256").getAsString(), source.sourceSha256());
            assertTrue(source.sourceSha256().matches("[0-9a-f]{64}"));
        }
        assertEquals(4.5, research.getAsJsonObject("community").get("radiusMeters").getAsDouble());
        assertEquals(HASH, research.getAsJsonObject("community").get("apiId").getAsLong());
        assertFalse(research.getAsJsonObject("official").get("weaponArchetypeScaling").getAsBoolean());
        var mechanics = json(REF + "mechanics.json");
        assertEquals("W77", mechanics.get("stage").getAsString());
        assertEquals(HASH, mechanics.get("baseHash").getAsLong());
        assertEquals(169755979L, mechanics.get("enhancedHashExcluded").getAsLong());
        assertEquals(3865257976L, mechanics.get("otherSameNameHashExcluded").getAsLong());
        assertEquals("precision weapon final blow", mechanics.get("trigger").getAsString());
        assertEquals(research.get("official"), mechanics.get("officialPrimary"));
        assertEquals(research.get("community"), mechanics.get("communityRadius"));
        var policy = mechanics.getAsJsonObject("serverPolicy");
        assertEquals(10f, policy.get("damageHp").getAsFloat());
        assertEquals(4.5, policy.get("radiusBlocks").getAsDouble());
        assertEquals(.3f, policy.get("falloffFloor").getAsFloat());
        assertEquals(raw.get("damagePolicy"), policy.get("damage"));
        assertEquals(raw.get("falloffPolicy"), policy.get("falloff"));
    }

    @Test void officialSocketProofAuditsAllSelectedWeaponsAndJoinsOnlyTheFourRollableBasePools() throws Exception {
        var proof = json(REF + "socket-pools.json");
        assertEquals("W77", proof.get("stage").getAsString());
        assertEquals(63, proof.get("selectedCount").getAsInt());
        assertEquals(678, proof.get("socketCount").getAsInt());
        assertEquals(627, proof.get("plugSetReferencesReviewed").getAsInt());
        assertEquals(4, proof.get("runtimeRollCount").getAsInt());
        var runtimeRows = proof.getAsJsonArray("runtimeRolls");
        assertEquals(4, runtimeRows.size());
        assertEquals(EXPECTED, runtimeRows.asList().stream().map(JsonElement::getAsJsonObject)
                .map(DragonflyW77Test::roll).collect(Collectors.toSet()));
        var audit = proof.getAsJsonArray("selectionAudit").asList().stream().map(JsonElement::getAsJsonObject)
                .collect(Collectors.toMap(row -> row.get("id").getAsString(), row -> row));
        assertEquals(WeaponCatalogTest.originalW30Entries().stream().map(WeaponCatalog.Entry::id).collect(Collectors.toSet()), audit.keySet());
        int sockets = 0;
        int reviewedSets = 0;
        for (var entry : WeaponCatalogTest.originalW30Entries()) {
            var row = audit.get(entry.id());
            var meta = WeaponCharacteristics.of(entry);
            assertEquals(meta.bungieHash(), row.get("hash").getAsLong(), entry.id());
            assertEquals(meta.exotic(), row.get("exotic").getAsBoolean(), entry.id());
            assertEquals(meta.damage().name(), row.get("damage").getAsString(), entry.id());
            assertEquals(entry.family(), row.get("family").getAsString(), entry.id());
            assertEquals(EXPECTED.stream().filter(r -> r.id().equals(entry.id())).count(),
                    row.get("baseRandomizedRows").getAsLong(), entry.id());
            var socketRows = row.getAsJsonArray("sockets");
            assertEquals(row.get("socketCount").getAsInt(), socketRows.size(), entry.id());
            var indexes = new HashSet<Integer>();
            for (var socket : socketRows) {
                var socketRow = socket.getAsJsonObject();
                int index = socketRow.get("socket").getAsInt();
                assertTrue(index >= 0 && index < socketRows.size(), entry.id());
                assertTrue(indexes.add(index), entry.id() + ":" + index);
                reviewedSets += socketRow.getAsJsonArray("reviewedPlugSets").size();
            }
            sockets += socketRows.size();
        }
        assertEquals(678, sockets);
        assertEquals(627, reviewedSets);
        var seen = new HashSet<WeaponPerks.Roll>();
        for (var element : proof.getAsJsonArray("weapons")) {
            var row = element.getAsJsonObject();
            var candidate = roll(row);
            assertTrue(EXPECTED.contains(candidate), candidate.toString());
            assertTrue(seen.add(candidate), "Duplicate proof " + candidate);
            assertEquals(4241085061L, row.get("socketCategoryHash").getAsLong());
            assertEquals("randomizedPlugSetHash", row.get("plugSetField").getAsString());
            assertFalse(row.get("isFakePlugSet").getAsBoolean());
            assertEquals(Map.of("ARC", 2, "SOLAR", 3, "VOID", 4).get(row.get("damage").getAsString()).intValue(),
                    row.get("officialDamageType").getAsInt());
            var weaponAudit = audit.get(candidate.id());
            assertFalse(weaponAudit.get("exotic").getAsBoolean());
            assertEquals(weaponAudit.get("damage"), row.get("damage"));
            assertEquals(weaponAudit.get("family"), row.get("family"));
            assertTrue(weaponAudit.getAsJsonArray("traitSocketIndexes").asList().stream()
                    .anyMatch(index -> index.getAsInt() == candidate.socket()));
            var socket = weaponAudit.getAsJsonArray("sockets").asList().stream().map(JsonElement::getAsJsonObject)
                    .filter(s -> s.get("socket").getAsInt() == candidate.socket()).findFirst().orElseThrow();
            assertTrue(socket.get("traitCategory").getAsBoolean());
            assertEquals(1, socket.getAsJsonArray("reviewedPlugSets").asList().stream().map(JsonElement::getAsJsonObject)
                    .filter(s -> "randomizedPlugSetHash".equals(s.get("field").getAsString())
                            && s.get("hash").getAsLong() == candidate.plugSetHash()
                            && !s.get("isFakePlugSet").getAsBoolean()).count());
            var matches = row.getAsJsonArray("matchingEntries");
            assertEquals(1, matches.size());
            var match = matches.get(0).getAsJsonObject();
            assertTrue(match.get("index").getAsInt() >= 0);
            var item = match.getAsJsonObject("item");
            assertEquals(HASH, item.get("plugItemHash").getAsLong());
            assertTrue(item.get("currentlyCanRoll").getAsBoolean());
            assertEquals(0d, item.get("weight").getAsDouble(), "Zero weight must not discard a rollable base trait");
        }
        assertEquals(EXPECTED, seen);
        assertEquals(4, proof.getAsJsonArray("weapons").size());
        for (var key : List.of("directSocketOptions", "enhancedAndOtherHashOccurrencesExcluded",
                "otherBasePoolOccurrencesNotSelected", "unsupportedBaseElementOccurrences"))
            assertTrue(proof.getAsJsonArray(key).isEmpty(), key);
        var excluded = proof.getAsJsonArray("noOfficialBaseRandomizedRollIds");
        assertEquals(59, excluded.size());
        assertEquals(WeaponCatalogTest.originalW30Entries().stream().map(WeaponCatalog.Entry::id)
                        .filter(id -> EXPECTED.stream().noneMatch(r -> r.id().equals(id))).collect(Collectors.toSet()),
                excluded.asList().stream().map(JsonElement::getAsString).collect(Collectors.toSet()));
        assertEquals(Set.of("ARC", "SOLAR", "VOID"), proof.getAsJsonArray("supportedElements").asList()
                .stream().map(JsonElement::getAsString).collect(Collectors.toSet()));
    }

    @Test void provenancePinsPublicInputsGeneratorProfileAndEveryGeneratedOutputWithoutPrivateCacheDependencies() throws Exception {
        var provenance = json(REF + "provenance.json");
        assertEquals("W77", provenance.get("stage").getAsString());
        assertEquals("245114.26.10.13.2000-1-bnet.66137", provenance.get("manifestVersion").getAsString());
        String prefix = "https://www.bungie.net/common/destiny2_content/json/en/";
        String suffix = "-e677f6ea-2a1e-48d4-a8c8-700a39a62585.json";
        assertEquals(prefix + "DestinyInventoryItemDefinition" + suffix, provenance.get("inventoryUrl").getAsString());
        assertEquals(prefix + "DestinyPlugSetDefinition" + suffix, provenance.get("plugSetsUrl").getAsString());
        var expectedPins = Map.of(
                "selected", "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
                "w40Provenance", "281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42",
                "catalog", "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
                "characteristics", "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
                "inventory", "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
                "plugSets", "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
                "manifest", "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
                "research", "ca514c058c0461d8f445489bc9e6b3ccb0c1e96c3564003329181635db57ed66");
        var pins = provenance.getAsJsonObject("sourceHashes");
        assertEquals(expectedPins.keySet(), pins.keySet());
        for (var pin : expectedPins.entrySet()) {
            var source = pins.getAsJsonObject(pin.getKey());
            assertEquals(pin.getValue(), source.get("sha256").getAsString(), pin.getKey());
            assertTrue(source.get("bytes").getAsLong() > 0, pin.getKey());
        }
        // Private paths remain provenance metadata; pure tests read only repository artifacts.
        for (var input : Map.of("selected", "art/weapons/w40/definitions.json",
                "w40Provenance", "art/weapons/w40/provenance.json",
                "catalog", "src/main/resources/destiny/weapons/w30.json",
                "characteristics", "src/main/resources/destiny/weapons/w40-characteristics.json",
                "research", REF + "research.json").entrySet()) {
            var file = Path.of(input.getValue());
            var source = pins.getAsJsonObject(input.getKey());
            assertEquals(input.getValue(), source.get("path").getAsString());
            assertEquals(expectedPins.get(input.getKey()), sha256(file));
            assertEquals(Files.size(file), source.get("bytes").getAsLong());
        }
        var w40 = json("art/weapons/w40/provenance.json");
        assertEquals(expectedPins.get("inventory"), w40.get("cachedInventorySha256").getAsString());
        assertEquals(provenance.get("inventoryUrl"), w40.get("source"));
        assertEquals(provenance.get("manifestVersion"), w40.getAsJsonObject("manifest").get("version"));
        assertEquals("scripts/extract_dragonfly_w77.py", provenance.get("generator").getAsString());
        assertEquals(sha256(Path.of("scripts/extract_dragonfly_w77.py")), provenance.get("generatorSha256").getAsString());
        assertEquals("src/main/java/kim/biryeong/destiny/weapon/DragonflyProfile.java", provenance.get("profile").getAsString());
        assertEquals(sha256(Path.of(provenance.get("profile").getAsString())), provenance.get("profileSha256").getAsString());
        String runtime = "src/main/resources/destiny/weapons/w77-dragonfly.json";
        var outputs = provenance.getAsJsonObject("outputHashes");
        assertEquals(Set.of(runtime, REF + "socket-pools.json", REF + "mechanics.json",
                "art/weapons/w77/reference-notes.md"), outputs.keySet());
        for (var output : outputs.entrySet())
            assertEquals(sha256(Path.of(output.getKey())), output.getValue().getAsString(), output.getKey());
        try (var input = DragonflyW77Test.class.getResourceAsStream(RESOURCE)) {
            assertNotNull(input);
            assertArrayEquals(Files.readAllBytes(Path.of(runtime)), input.readAllBytes(), "Classpath must contain the proven profile bytes");
        }
        assertEquals("rtk proxy python3 scripts/extract_dragonfly_w77.py --verify", provenance.get("reproduce").getAsString());
    }

    @Test void fixedLocalCurveHasTenHpAtCenterLinearInteriorAndThreeHpFloorThroughTheEdge() {
        // Literal HP checkpoints distinguish linear-floor attenuation from interpolation to a 3 HP edge.
        double[][] points = {{0, 10}, {-0.0, 10}, {1.125, 7.5}, {2.25, 5}, {2.7, 4},
                {3.15, 3}, {3.6, 3}, {4, 3}, {4.5, 3}};
        for (var point : points)
            assertEquals(point[1], WeaponDragonfly.damageAt(point[0]), EPSILON, "distance=" + point[0]);
        assertEquals(10, WeaponDragonfly.damageAt(Double.MIN_VALUE), EPSILON);
        assertEquals(3, WeaponDragonfly.damageAt(Math.nextDown(4.5)), EPSILON);
        assertEquals(0f, WeaponDragonfly.damageAt(Math.nextUp(4.5)));
    }

    @Test void invalidDistancesAndEveryOutsideRadiusDistanceReturnZero() {
        for (double distance : new double[]{Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY,
                -Double.MAX_VALUE, -4.5, -1, -Double.MIN_VALUE, Math.nextUp(4.5), 4.5001, 9, Double.MAX_VALUE})
            assertEquals(0f, WeaponDragonfly.damageAt(distance), "distance=" + distance);
    }

    @Test void damageIsFiniteBoundedAndMonotonicAcrossTheWholeRadiusIncludingItsDiscontinuity() {
        float previous = WeaponDragonfly.damageAt(0);
        for (int step = 1; step <= 4500; step++) {
            double distance = step / 1000.0;
            float damage = WeaponDragonfly.damageAt(distance);
            assertTrue(Float.isFinite(damage), "distance=" + distance);
            assertTrue(damage >= 3f && damage <= 10f, "distance=" + distance);
            assertTrue(damage <= previous, "Damage increased at distance=" + distance);
            previous = damage;
        }
        assertTrue(WeaponDragonfly.damageAt(3.149) > WeaponDragonfly.damageAt(3.15));
        assertEquals(WeaponDragonfly.damageAt(3.15), WeaponDragonfly.damageAt(4.5));
        assertTrue(WeaponDragonfly.damageAt(Math.nextUp(4.5)) < previous);
    }
}
