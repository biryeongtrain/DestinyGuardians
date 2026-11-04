package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Pure cycle/profile tests. Item selection, ownership and projectile integration belong in GameTests. */
class RampageW66Test {
    private static final int DECAY = 90;
    private static final long HASH = 3425386926L;
    private static final String REF = "art/weapons/w66/references/";
    // Independently checked against the pinned original inventory and referenced randomized sets.
    // Keep literal identities here so changing a generator and its output together cannot bless a new pool.
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
            new WeaponPerks.Roll("duke_mk_44", 2112909414L, 4, HASH, 3815727680L),
            new WeaponPerks.Roll("austringer", 3055790362L, 4, HASH, 785215120L),
            new WeaponPerks.Roll("gnawing_hunger", 821154603L, 4, HASH, 594510568L),
            new WeaponPerks.Roll("bygones", 2712244741L, 3, HASH, 1760176771L),
            new WeaponPerks.Roll("chattering_bone", 568515759L, 4, HASH, 423791138L),
            new WeaponPerks.Roll("blast_furnace", 3843477312L, 4, HASH, 169306153L),
            new WeaponPerks.Roll("claws_of_the_wolf", 1280933460L, 4, HASH, 753756428L),
            new WeaponPerks.Roll("dead_man_walking_xx7463", 3751622019L, 4, HASH, 1210839935L),
            new WeaponPerks.Roll("brass_attacks", 2121785039L, 4, HASH, 3403850295L),
            new WeaponPerks.Roll("beloved", 3107853529L, 4, HASH, 887157889L),
            new WeaponPerks.Roll("dust_rock_blues", 636912560L, 4, HASH, 1624251370L),
            new WeaponPerks.Roll("parcel_of_stardust_fell_to_earth", 2217366863L, 4, HASH, 3424940310L),
            new WeaponPerks.Roll("dream_breaker", 2931957300L, 4, HASH, 1206254527L),
            new WeaponPerks.Roll("line_in_the_sand", 946443267L, 4, HASH, 3257645194L),
            new WeaponPerks.Roll("stormchaser", 3652506829L, 4, HASH, 4213354588L),
            new WeaponPerks.Roll("deafening_whisper", 981718087L, 4, HASH, 3588287812L),
            new WeaponPerks.Roll("edge_transit", 218335759L, 4, HASH, 2535579724L),
            new WeaponPerks.Roll("canis_major", 2066434718L, 4, HASH, 2791121719L),
            new WeaponPerks.Roll("fixed_odds", 2194955522L, 4, HASH, 1686775256L),
            new WeaponPerks.Roll("hammerhead", 603242241L, 4, HASH, 2479293397L),
            new WeaponPerks.Roll("retrofit_escapade", 3103325054L, 4, HASH, 2461260598L));

    private static JsonObject json(String file) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(file))).getAsJsonObject();
    }
    private static String sha256(Path file) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file)));
    }
    private static WeaponPerks.Roll roll(JsonObject row) {
        return new WeaponPerks.Roll(row.get("id").getAsString(), row.get("hash").getAsLong(),
                row.get("socket").getAsInt(), row.get("perkHash").getAsLong(), row.get("plugSetHash").getAsLong());
    }
    private static RampageCycle full(long tick, int duration) {
        var cycle = new RampageCycle();
        for (int stacks = 1; stacks <= 3; stacks++) {
            assertTrue(cycle.killed(tick, duration));
            assertEquals(stacks, cycle.stacks(tick, duration));
        }
        return cycle;
    }
    private static void state(RampageCycle cycle, long tick, int stacks, int remaining) {
        assertEquals(stacks, cycle.stacks(tick, DECAY), "stacks at tick=" + tick);
        assertEquals(remaining, cycle.remaining(tick, DECAY), "remaining at tick=" + tick);
    }

    @Test void freshReadsNeverCreateStacksAndOneKillHasAnExactNinetyTickWindow() {
        var cycle = new RampageCycle();
        for (long tick : new long[]{Long.MIN_VALUE, -1, 0, 1, 89, 90, 270, Long.MAX_VALUE})
            state(cycle, tick, 0, 0);
        assertTrue(cycle.killed(40, DECAY));
        state(cycle, 39, 0, 0);
        state(cycle, 40, 1, 90);
        state(cycle, 41, 1, 89);
        state(cycle, 129, 1, 1);
        state(cycle, 130, 0, 0);
        state(cycle, 131, 0, 0);
    }

    @Test void eachKillAddsOneStackUpToThreeAndEvenACappedKillRefreshesWithoutAddingTime() {
        var cycle = new RampageCycle();
        for (int kills = 1; kills <= 8; kills++) {
            int tick = (kills - 1) * 20;
            assertTrue(cycle.killed(tick, DECAY));
            state(cycle, tick, Math.min(3, kills), 90);
            state(cycle, tick + 19, Math.min(3, kills), 71);
        }
        state(cycle, 229, 3, 1);
        state(cycle, 230, 2, 90);
        state(cycle, 319, 2, 1);
        state(cycle, 320, 1, 90);
        state(cycle, 410, 0, 0);
    }

    @Test void threeStacksDecayIndividuallyAtNinetyOneHundredEightyAndTwoHundredSeventy() {
        var cycle = full(0, DECAY);
        long[] ticks = {0, 1, 89, 90, 91, 179, 180, 181, 269, 270, 271};
        int[] stacks = {3, 3, 3, 2, 2, 2, 1, 1, 1, 0, 0};
        int[] remaining = {90, 89, 1, 90, 89, 1, 90, 89, 1, 0, 0};
        for (int i = 0; i < ticks.length; i++) state(cycle, ticks[i], stacks[i], remaining[i]);
        for (int initial = 1; initial <= 2; initial++) {
            var shorter = new RampageCycle();
            for (int i = 0; i < initial; i++) assertTrue(shorter.killed(0, DECAY));
            state(shorter, initial * 90L - 1, 1, 1);
            state(shorter, initial * 90L, 0, 0);
        }
    }

    @Test void skippedTicksExpireExactlyTheElapsedStacksBeforeAFreshKillAddsAndRefreshes() {
        for (int tick : new int[]{89, 90, 91, 179, 180, 181, 269, 270, 271, 10000}) {
            var cycle = full(0, DECAY);
            int surviving = Math.max(0, 3 - tick / DECAY);
            int afterKill = Math.min(3, surviving + 1);
            // No intermediate reads or update ticks may be required to catch up.
            assertTrue(cycle.killed(tick, DECAY));
            state(cycle, tick, afterKill, 90);
            state(cycle, tick + 89L, afterKill, 1);
            state(cycle, tick + 90L, afterKill - 1, afterKill > 1 ? 90 : 0);
            state(cycle, tick + (afterKill - 1) * 90L, 1, 90);
            state(cycle, tick + afterKill * 90L, 0, 0);
        }
    }

    @Test void repeatedAndOutOfOrderQueriesNeitherAdvanceRefreshNorPauseTheClock() {
        var cycle = full(100, DECAY);
        for (int tick = 100; tick <= 371; tick++) {
            int elapsed = tick - 100;
            int stacks = Math.max(0, 3 - elapsed / DECAY);
            for (int read = 0; read < 8; read++)
                state(cycle, tick, stacks, stacks == 0 ? 0 : DECAY - elapsed % DECAY);
        }
        state(cycle, Long.MAX_VALUE, 0, 0);
        state(cycle, 100, 3, 90);
        state(cycle, 280, 1, 90);
        state(cycle, 189, 3, 1);
        state(cycle, 370, 0, 0);
        var unread = full(100, DECAY);
        state(unread, 279, 2, 1);
        state(unread, 369, 1, 1);
        state(unread, 370, 0, 0);
        assertTrue(cycle.killed(101, DECAY));
        state(cycle, 101, 3, 90); // Future HUD reads did not commit an expiration.
    }

    @Test void negativeAndBackwardKillTicksAreRejectedWithoutErasingExistingStacks() {
        var cycle = full(100, DECAY);
        for (long bad : new long[]{Long.MIN_VALUE, -1, 0, 99}) {
            state(cycle, bad, 0, 0);
            assertFalse(cycle.killed(bad, DECAY));
            state(cycle, 100, 3, 90);
            state(cycle, 189, 3, 1);
            state(cycle, 190, 2, 90);
        }
        assertTrue(cycle.killed(190, DECAY));
        state(cycle, 190, 3, 90);
        assertFalse(cycle.killed(189, DECAY));
        state(cycle, 190, 3, 90);
    }

    @Test void overflowingKillsAreInertAndLongMaxValueQueriesRetainExactDecayBoundaries() {
        var cycle = full(10, DECAY);
        for (long bad : new long[]{Long.MAX_VALUE - DECAY + 1, Long.MAX_VALUE - 1, Long.MAX_VALUE}) {
            assertFalse(cycle.killed(bad, DECAY));
            state(cycle, 10, 3, 90);
            state(cycle, 100, 2, 90);
            state(cycle, bad, 0, 0);
        }
        var exact = full(Long.MAX_VALUE - 270, DECAY);
        state(exact, Long.MAX_VALUE - 181, 3, 1);
        state(exact, Long.MAX_VALUE - 180, 2, 90);
        state(exact, Long.MAX_VALUE - 90, 1, 90);
        state(exact, Long.MAX_VALUE - 1, 1, 1);
        state(exact, Long.MAX_VALUE, 0, 0);
        var latest = full(Long.MAX_VALUE - DECAY, DECAY);
        state(latest, Long.MAX_VALUE - 1, 3, 1);
        state(latest, Long.MAX_VALUE, 2, 90);
        assertFalse(latest.killed(Long.MAX_VALUE, DECAY));
        state(latest, Long.MAX_VALUE, 2, 90);
    }

    @Test void allCycleOperationsRejectInvalidDurationsWithoutMutationAndAcceptBothLimits() {
        var cycle = full(10, DECAY);
        for (int bad : new int[]{Integer.MIN_VALUE, -1, 0, 1201, Integer.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class, () -> cycle.killed(20, bad));
            assertThrows(IllegalArgumentException.class, () -> cycle.stacks(20, bad));
            assertThrows(IllegalArgumentException.class, () -> cycle.remaining(20, bad));
            state(cycle, 20, 3, 80);
            state(cycle, 100, 2, 90);
            var empty = new RampageCycle();
            assertThrows(IllegalArgumentException.class, () -> empty.stacks(0, bad));
            assertThrows(IllegalArgumentException.class, () -> empty.remaining(0, bad));
        }
        for (int duration : new int[]{1, 1200}) {
            var valid = full(0, duration);
            for (int elapsed = 0; elapsed <= 3 * duration; elapsed++) {
                int stacks = Math.max(0, 3 - elapsed / duration);
                assertEquals(stacks, valid.stacks(elapsed, duration));
                assertEquals(stacks == 0 ? 0 : duration - elapsed % duration, valid.remaining(elapsed, duration));
            }
        }
    }

    @Test void profileMultipliersAndRollsAreExactImmutableAndDefensivelyCopied() {
        var perk = RampageProfile.perk();
        assertEquals("rampage", RampageProfile.ID);
        assertEquals(HASH, RampageProfile.HASH);
        assertEquals("rampage", perk.id());
        assertEquals(HASH, perk.hash());
        assertEquals(DECAY, perk.decayTicks());
        assertEquals(List.of(1f, 1.1f, 1.21f, 1.331f), perk.multipliers());
        for (int i = 0; i <= 3; i++) assertEquals(perk.multipliers().get(i).floatValue(), RampageProfile.multiplier(i));
        assertThrows(IndexOutOfBoundsException.class, () -> RampageProfile.multiplier(-1));
        assertThrows(IndexOutOfBoundsException.class, () -> RampageProfile.multiplier(4));
        assertThrows(UnsupportedOperationException.class, () -> perk.multipliers().set(1, 2f));
        assertThrows(UnsupportedOperationException.class, () -> perk.multipliers().clear());
        var original = new ArrayList<>(perk.multipliers());
        var copy = new RampageProfile.Perk(perk.id(), perk.hash(), DECAY, original, perk.timingSource());
        original.set(1, 2f);
        original.clear();
        assertEquals(perk.multipliers(), copy.multipliers());
        assertThrows(UnsupportedOperationException.class, () -> copy.multipliers().add(2f));
        var rolls = RampageProfile.rolls();
        assertThrows(UnsupportedOperationException.class, rolls::clear);
        assertThrows(UnsupportedOperationException.class, () -> rolls.set(0, rolls.getFirst()));
        assertEquals(EXPECTED, new HashSet<>(RampageProfile.rolls()));
    }

    @Test void exactTwentyOneSelectedWeaponHashesSocketsAndPlugSetsMatchTheClasspathResource() throws Exception {
        var rolls = RampageProfile.rolls();
        assertEquals(21, rolls.size());
        assertEquals(21, rolls.stream().map(WeaponPerks.Roll::id).distinct().count());
        assertEquals(EXPECTED, new HashSet<>(rolls));
        WeaponCatalogTest.assertExpandedCatalog();
        for (var roll : rolls) {
            var entry = WeaponCatalog.find(roll.id()).orElseThrow();
            var meta = WeaponCharacteristics.of(entry);
            assertEquals(meta.bungieHash(), roll.hash());
            assertFalse(meta.exotic());
            assertEquals(HASH, roll.perkHash());
            assertNotEquals(288411554L, roll.perkHash()); // Enhanced Rampage.
            assertNotEquals(3551326236L, roll.perkHash()); // Separate exotic Rampage definition.
            assertNotEquals(2286143274L, roll.hash()); // The Huckleberry is not this selected base trait.
            assertFalse(Set.of("sword", "glaive").contains(entry.family()), "No selected pool match: " + entry.id());
        }
        try (var input = RampageW66Test.class.getResourceAsStream("/destiny/weapons/w66-rampage.json")) {
            assertNotNull(input, "W66 runtime resource must be on the test classpath");
            var data = JsonParser.parseReader(new InputStreamReader(input, StandardCharsets.UTF_8)).getAsJsonObject();
            assertEquals("W66", data.get("stage").getAsString());
            var perk = data.getAsJsonObject("perk");
            assertEquals("rampage", perk.get("id").getAsString());
            assertEquals(HASH, perk.get("hash").getAsLong());
            assertEquals(DECAY, perk.get("decayTicks").getAsInt());
            var multipliers = perk.getAsJsonArray("multipliers");
            String[] decimals = {"1.0", "1.1", "1.21", "1.331"};
            assertEquals(decimals.length, multipliers.size());
            for (int i = 0; i < decimals.length; i++)
                assertEquals(0, new BigDecimal(decimals[i]).compareTo(multipliers.get(i).getAsBigDecimal()));
            assertEquals(RampageProfile.perk().timingSource(), perk.get("timingSource").getAsString());
            var resourceRolls = data.getAsJsonArray("weapons");
            assertEquals(21, resourceRolls.size());
            assertEquals(EXPECTED, new HashSet<>(resourceRolls.asList().stream()
                    .map(JsonElement::getAsJsonObject).map(RampageW66Test::roll).toList()));
        }
    }

    @Test void publicOriginalSocketProofJoinsAllTwentyOnePoolsAndAuditsEverySelectedWeapon() throws Exception {
        var proof = json(REF + "socket-pools.json");
        assertEquals("W66", proof.get("stage").getAsString());
        assertEquals(63, proof.get("selectedCount").getAsInt());
        assertEquals(21, proof.get("supportedCount").getAsInt());
        assertEquals(21, proof.get("poolRows").getAsInt());
        assertEquals(21, proof.get("randomizedPoolRows").getAsInt());
        assertEquals(0, proof.get("fixedDirectRows").getAsInt());
        assertEquals(List.of(HASH), proof.getAsJsonArray("provenBaseHashes").asList().stream()
                .map(JsonElement::getAsLong).toList());
        var audit = new HashMap<String, JsonObject>();
        for (var element : proof.getAsJsonArray("selectionAudit")) {
            var row = element.getAsJsonObject();
            String id = row.get("id").getAsString();
            assertNull(audit.put(id, row), "Duplicate selected weapon " + id);
            var meta = WeaponCharacteristics.of(WeaponCatalog.find(id).orElseThrow());
            assertEquals(meta.bungieHash(), row.get("hash").getAsLong());
            assertEquals(meta.exotic(), row.get("exotic").getAsBoolean());
            assertEquals(EXPECTED.stream().filter(r -> r.id().equals(id)).count(), row.get("randomizedBaseRows").getAsInt());
        }
        assertEquals(WeaponCatalogTest.originalW30Entries().stream().map(WeaponCatalog.Entry::id).collect(java.util.stream.Collectors.toSet()), audit.keySet());
        var seen = new HashSet<WeaponPerks.Roll>();
        for (var element : proof.getAsJsonArray("weapons")) {
            var row = element.getAsJsonObject();
            var expected = roll(row);
            assertTrue(EXPECTED.contains(expected), "Unexpected original socket " + expected);
            assertTrue(seen.add(expected), "Duplicate original socket " + expected);
            assertEquals("randomized", row.get("selection").getAsString());
            assertEquals(4241085061L, row.get("socketCategoryHash").getAsLong());
            assertEquals("randomizedPlugSetHash", row.get("plugSetField").getAsString());
            assertFalse(row.get("isFakePlugSet").getAsBoolean());
            assertEquals(expected.plugSetHash(), row.getAsJsonObject("socketEntry").get("randomizedPlugSetHash").getAsLong());
            var selected = audit.get(expected.id());
            assertEquals(selected.get("weaponType").getAsString(), row.get("weaponType").getAsString());
            assertTrue(expected.socket() < selected.get("socketCount").getAsInt());
            assertTrue(selected.getAsJsonArray("traitSocketIndexes").asList().stream()
                    .anyMatch(index -> index.getAsInt() == expected.socket()));
            var matches = row.getAsJsonArray("matchingEntries");
            assertEquals(1, matches.size());
            var match = matches.get(0).getAsJsonObject();
            assertTrue(match.get("index").getAsInt() >= 0);
            var item = match.getAsJsonObject("item");
            assertEquals(HASH, item.get("plugItemHash").getAsLong());
            assertTrue(item.get("currentlyCanRoll").getAsBoolean());
            assertEquals(0d, item.get("weight").getAsDouble()); // Weight zero is not a reason to omit a rollable trait.
        }
        assertEquals(EXPECTED, seen);
        assertEquals(21, proof.getAsJsonArray("weapons").size());
        var direct = proof.getAsJsonArray("directSocketOptions");
        assertEquals(8, direct.size());
        var directIds = new HashSet<String>();
        for (var element : direct) {
            var row = element.getAsJsonObject();
            String id = row.get("id").getAsString();
            assertTrue(directIds.add(id));
            assertTrue(EXPECTED.stream().anyMatch(r -> r.id().equals(id) && r.hash() == row.get("hash").getAsLong()
                    && r.socket() == row.get("socket").getAsInt()));
            assertEquals(HASH, row.get("perkHash").getAsLong());
            assertTrue(row.get("initialPerk").getAsBoolean());
            assertTrue(row.get("alsoProvenRandomized").getAsBoolean());
            assertFalse(row.get("addsRuntimeRow").getAsBoolean());
        }
        assertEquals(Set.of("gnawing_hunger", "dust_rock_blues", "parcel_of_stardust_fell_to_earth", "dream_breaker",
                "line_in_the_sand", "stormchaser", "deafening_whisper", "hammerhead"), directIds);
        var enhancedIds = new HashSet<String>();
        for (var element : proof.getAsJsonArray("enhancedSelectedOptionsExcluded")) {
            var row = element.getAsJsonObject();
            assertEquals(288411554L, row.get("perkHash").getAsLong());
            assertTrue(enhancedIds.add(row.get("id").getAsString()));
            assertFalse(EXPECTED.contains(roll(row)));
        }
        assertEquals(Set.of("austringer", "beloved", "fixed_odds", "retrofit_escapade"), enhancedIds);
        assertEquals(4, proof.getAsJsonArray("enhancedSelectedOptionsExcluded").size());
        assertEquals(0, proof.getAsJsonArray("huckleberrySelectedOptionsExcluded").size());
        assertEquals(0, proof.getAsJsonArray("otherBasePoolOccurrencesNotSelected").size());
        var unsupported = proof.getAsJsonArray("unsupportedSelectedIds").asList().stream()
                .map(JsonElement::getAsString).toList();
        var expectedUnsupported = new HashSet<>(audit.keySet());
        EXPECTED.forEach(r -> expectedUnsupported.remove(r.id()));
        assertEquals(42, unsupported.size());
        assertEquals(expectedUnsupported, new HashSet<>(unsupported));
        var melee = audit.values().stream().filter(r -> Set.of("Sword", "Glaive").contains(r.get("weaponType").getAsString())).toList();
        assertEquals(Set.of("abide_the_return", "goldtusk", "crown_splitter", "falling_guillotine", "temptation_s_hook", "nezarec_s_whisper"),
                melee.stream().map(r -> r.get("id").getAsString()).collect(java.util.stream.Collectors.toSet()));
        for (var row : melee) {
            assertEquals(0, row.get("randomizedBaseRows").getAsInt());
            assertTrue(unsupported.contains(row.get("id").getAsString()));
        }
    }

    @Test void compactPublicEvidencePinsSourcesGeneratorAndOutputsAndSeparatesOfficialFromSecondaryMechanics() throws Exception {
        var provenance = json(REF + "provenance.json");
        assertEquals("W66", provenance.get("stage").getAsString());
        assertEquals("245114.26.10.13.2000-1-bnet.66137", provenance.get("manifestVersion").getAsString());
        String prefix = "https://www.bungie.net/common/destiny2_content/json/en/";
        String suffix = "-e677f6ea-2a1e-48d4-a8c8-700a39a62585.json";
        assertEquals(prefix + "DestinyInventoryItemDefinition" + suffix, provenance.get("inventoryUrl").getAsString());
        assertEquals(prefix + "DestinyPlugSetDefinition" + suffix, provenance.get("plugSetsUrl").getAsString());
        var pins = provenance.getAsJsonObject("sourceHashes");
        var expectedPins = Map.of(
                "selected", "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
                "w40Provenance", "281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42",
                "inventory", "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
                "plugSets", "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
                "manifest", "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
                "research1.json", "0c625014aaf5b3066622274e289c07115e612ab429a2ba217fad3853e9ff30fa",
                "research2.json", "a2e2c1964d0436ec6b7c9cb405c38ae39adfff9540390c1967fc76fda762266e",
                "research3.json", "0de7595629a87a4c4071f9c5f27f265e2231c240464f259f33a2d005f6e55c2e",
                "research4.json", "2524c9732272fcebbb1e35c2bc4384f83dbd15091d44292e65302d7ea8b11347");
        assertEquals(expectedPins.keySet(), pins.keySet());
        for (var pin : expectedPins.entrySet()) {
            var source = pins.getAsJsonObject(pin.getKey());
            assertEquals(pin.getValue(), source.get("sha256").getAsString());
            assertTrue(source.get("bytes").getAsLong() > 0);
        }
        // Only public inputs are opened here. Private inventory/capture locations are metadata, never test inputs.
        for (var input : Map.of("selected", "art/weapons/w40/definitions.json", "w40Provenance", "art/weapons/w40/provenance.json").entrySet()) {
            var file = Path.of(input.getValue());
            var pin = pins.getAsJsonObject(input.getKey());
            assertEquals(input.getValue(), pin.get("path").getAsString());
            assertEquals(expectedPins.get(input.getKey()), sha256(file));
            assertEquals(Files.size(file), pin.get("bytes").getAsLong());
        }
        var w40 = json("art/weapons/w40/provenance.json");
        assertEquals(expectedPins.get("inventory"), w40.get("cachedInventorySha256").getAsString());
        assertEquals(provenance.get("inventoryUrl"), w40.get("source"));
        assertEquals(provenance.get("manifestVersion"), w40.getAsJsonObject("manifest").get("version"));
        assertEquals("scripts/extract_rampage_w66.py", provenance.get("generator").getAsString());
        assertEquals(sha256(Path.of("scripts/extract_rampage_w66.py")), provenance.get("generatorSha256").getAsString());
        String runtime = "src/main/resources/destiny/weapons/w66-rampage.json";
        assertEquals(sha256(Path.of(runtime)), provenance.get("runtimeSha256").getAsString());
        var outputs = provenance.getAsJsonObject("outputHashes");
        assertEquals(Set.of(runtime, REF + "socket-pools.json", REF + "mechanics.json", "art/weapons/w66/reference-notes.md"), outputs.keySet());
        long publicBytes = Files.size(Path.of(REF + "provenance.json"));
        for (var output : outputs.entrySet()) {
            var file = Path.of(output.getKey());
            assertEquals(sha256(file), output.getValue().getAsString());
            publicBytes += Files.size(file);
        }
        assertTrue(publicBytes < 100_000, "Public proof must stay compact instead of embedding raw source dumps");
        assertEquals("rtk proxy python3 scripts/extract_rampage_w66.py --verify", provenance.get("reproduce").getAsString());
        var mechanics = json(REF + "mechanics.json");
        assertEquals("W66", mechanics.get("stage").getAsString());
        assertEquals(HASH, mechanics.get("baseHash").getAsLong());
        assertEquals(288411554L, mechanics.get("enhancedHashExcluded").getAsLong());
        assertEquals(3551326236L, mechanics.get("huckleberryHashExcluded").getAsLong());
        assertEquals(3, mechanics.get("maxStacks").getAsInt());
        assertEquals(90, mechanics.get("decayTicks").getAsInt());
        assertEquals(4.5, mechanics.get("baseDurationSeconds").getAsDouble());
        assertEquals(20, mechanics.get("ticksPerSecond").getAsInt());
        assertEquals(REF + "mechanics.json", RampageProfile.perk().timingSource());
        var primary = mechanics.getAsJsonObject("primaryChange");
        assertTrue(primary.get("primary").getAsBoolean());
        assertEquals("Bungie", primary.get("publisher").getAsString());
        assertEquals("2025-12-02", primary.get("publishedAt").getAsString());
        assertEquals("https://www.bungie.net/7/en/News/Article/destiny_update_9_5_0", primary.get("url").getAsString());
        assertEquals("Now loses only one stack after the timer expires.", primary.get("excerpt").getAsString());
        var community = mechanics.getAsJsonObject("communityMeasurements");
        assertFalse(community.get("primary").getAsBoolean());
        assertEquals(HASH, community.get("exactPerkHash").getAsLong());
        assertEquals("Community Research", community.get("section").getAsString());
        assertEquals(4.5, community.get("durationSeconds").getAsDouble());
        assertFalse(community.get("stowMentioned").getAsBoolean());
        assertFalse(community.get("refreshMentionedExplicitly").getAsBoolean());
        var damage = community.getAsJsonArray("damageIncreasePercentByStack");
        assertEquals(3, damage.size());
        String[] percent = {"10", "21", "33.1"};
        for (int i = 0; i < percent.length; i++)
            assertEquals(0, new BigDecimal(percent[i]).compareTo(damage.get(i).getAsBigDecimal()));
        var secondary = mechanics.getAsJsonObject("stowAndRefreshSecondary");
        assertFalse(secondary.get("primary").getAsBoolean());
        assertEquals("D2 Arsenal", secondary.get("publisher").getAsString());
        assertTrue(secondary.get("stowPersists").getAsBoolean());
        assertTrue(secondary.get("additionalWeaponKillsRefresh").getAsBoolean());
        assertFalse(mechanics.getAsJsonObject("projectIntegrationPolicy").get("verifiedDestinyBehavior").getAsBoolean());
    }
}
