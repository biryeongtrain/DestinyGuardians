package kim.biryeong.destiny.weapon;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class SubsistenceProfileTest {
    /** Historical source assertions remain frozen; new identities require exact official tuples. */
    private static java.util.List<WeaponPerks.Roll> legacyRolls() {
        var all = SubsistenceProfile.rolls();
        var added = all.stream().filter(r -> LegendaryWeapons.contains(r.id())).toList();
        assertEquals(java.util.Set.of("commemoration", "krait", "subjunctive", "submission"), added.stream().map(WeaponPerks.Roll::id)
            .collect(java.util.stream.Collectors.toSet()));
        for (var roll : added) assertTrue(LegendaryWeapons.exactRoll(roll), roll.toString());
        assertEquals(all.size(), new java.util.HashSet<>(all).size());
        return all.stream().filter(r -> !LegendaryWeapons.contains(r.id())).toList();
    }

    private static final Path RESOURCE = Path.of("src/main/resources/destiny/weapons/w167-subsistence.json");
    private static final Path REFS = Path.of("art/weapons/w167/references");
    private static final Set<String> IDS = Set.of("gnawing_hunger", "steelfeather_repeater", "long_arm",
        "bug_out_bag", "allied_demand", "farewell", "retraced_path");
    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }

    @Test void sevenExactBaseSocketsMatchOfficialCurrentlyRollablePools() throws Exception {
        var official = json(REFS.resolve("official-sockets.json"));
        var found = new HashSet<WeaponPerks.Roll>();
        assertEquals("subsistence", SubsistenceProfile.ID);
        assertEquals(1820235745L, SubsistenceProfile.HASH);
        assertEquals(SubsistenceProfile.HASH, official.getAsJsonObject("traits")
            .getAsJsonObject("subsistence").get("hash").getAsLong());
        for (var value : official.getAsJsonObject("weapons").getAsJsonArray("subsistence")) {
            var row = value.getAsJsonObject();
            var pool = row.getAsJsonObject("plugSet");
            var roll = new WeaponPerks.Roll(row.get("id").getAsString(), row.get("hash").getAsLong(),
                row.get("socket").getAsInt(), SubsistenceProfile.HASH, pool.get("hash").getAsLong());
            assertTrue(found.add(roll));
            assertEquals(3, roll.socket());
            assertEquals(4241085061L, row.get("socketCategoryHash").getAsLong());
            assertEquals(roll.plugSetHash(), row.getAsJsonObject("socketEntry")
                .get("randomizedPlugSetHash").getAsLong());
            assertFalse(pool.get("isFakePlugSet").getAsBoolean());
            var matches = pool.getAsJsonArray("reusablePlugItems").asList().stream()
                .map(JsonElement::getAsJsonObject)
                .filter(p -> p.get("plugItemHash").getAsLong() == SubsistenceProfile.HASH).toList();
            assertEquals(1, matches.size());
            assertTrue(matches.getFirst().get("currentlyCanRoll").getAsBoolean());
            assertEquals(roll.hash(), WeaponCharacteristics.of(entry(roll.id())).bungieHash());
            assertFalse(WeaponCharacteristics.of(entry(roll.id())).exotic());
        }
        assertEquals(7, found.size());
        assertEquals(IDS, found.stream().map(WeaponPerks.Roll::id).collect(Collectors.toSet()));
        assertEquals(found, new HashSet<>(legacyRolls()));
        assertEquals(7, legacyRolls().size());
        assertThrows(UnsupportedOperationException.class, () -> legacyRolls().clear());
    }

    @Test void exhaustiveAuditIncludesAll65CatalogIdsAndBothExotics() throws Exception {
        var audited = new HashSet<String>();
        var admitted = new HashSet<WeaponPerks.Roll>();
        int exotics = 0;
        for (var value : json(REFS.resolve("official-sockets.json")).getAsJsonArray("audit")) {
            var row = value.getAsJsonObject();
            String id = row.get("id").getAsString();
            assertTrue(audited.add(id));
            var weapon = entry(id);
            var meta = WeaponCharacteristics.of(weapon);
            assertEquals(meta.bungieHash(), row.get("hash").getAsLong());
            assertEquals(meta.exotic(), row.get("exotic").getAsBoolean());
            assertEquals(weapon.family(), row.get("family").getAsString());
            if (meta.exotic()) { exotics++; assertFalse(SubsistenceProfile.supports(weapon)); }
            var matches = new HashSet<WeaponPerks.Roll>();
            for (var p : row.getAsJsonArray("pools")) {
                var pool = p.getAsJsonObject();
                if (!pool.get("field").getAsString().equals("randomizedPlugSetHash")
                        || pool.get("isFakePlugSet").getAsBoolean()
                        || !row.getAsJsonArray("traitSocketIndexes").asList().contains(pool.get("socket"))) continue;
                for (var m : pool.getAsJsonArray("baseMatches")) {
                    var plug = m.getAsJsonObject();
                    assertEquals(SubsistenceProfile.HASH, plug.get("plugItemHash").getAsLong());
                    if (plug.get("currentlyCanRoll").getAsBoolean()) matches.add(new WeaponPerks.Roll(id,
                        meta.bungieHash(), pool.get("socket").getAsInt(), SubsistenceProfile.HASH,
                        pool.get("plugSetHash").getAsLong()));
                }
            }
            var admissions = new HashSet<WeaponPerks.Roll>();
            for (var a : row.getAsJsonArray("admissions")) {
                var socket = a.getAsJsonObject();
                admissions.add(new WeaponPerks.Roll(id, meta.bungieHash(), socket.get("socket").getAsInt(),
                    SubsistenceProfile.HASH, socket.get("plugSetHash").getAsLong()));
            }
            assertEquals(matches, admissions, id);
            admitted.addAll(admissions);
            assertEquals(!admissions.isEmpty(), SubsistenceProfile.supports(weapon), id);
            for (var socket : row.getAsJsonArray("directSockets"))
                assertTrue(admissions.stream().anyMatch(r -> r.socket() == socket.getAsInt()));
        }
        assertEquals(65, audited.size());
        assertEquals(2, exotics);
        assertEquals(WeaponCatalog.all().stream().filter(w -> !LegendaryWeapons.contains(w.id())).map(WeaponCatalog.Entry::id).collect(Collectors.toSet()), audited);
        assertEquals(new HashSet<>(legacyRolls()), admitted);
    }

    @Test void pinnedClarityDescribesBaseRatesReservesAndRefillSemantics() throws Exception {
        var clarity = json(REFS.resolve("clarity-source.json"));
        assertEquals("039cfbc4732c33573568b28cc6335dd3332a9296", clarity.get("commit").getAsString());
        assertEquals("881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384",
            clarity.get("sha256").getAsString());
        var source = clarity.getAsJsonObject("entries").getAsJsonObject("subsistence");
        assertEquals(SubsistenceProfile.HASH, source.get("hash").getAsLong());
        assertEquals("Subsistence", source.get("name").getAsString());
        assertEquals("Weapon Trait", source.get("type").getAsString());
        String text = source.getAsJsonObject("descriptions").toString();
        for (String line : List.of("Weapon Kills", "10% of the magazine (rounded up) from reserves.",
                "Submachine Gun and Auto Rifle Kills refill 17% of the magazine.",
                "does not need a reload animation", "doesn't trigger on-reload perks"))
            assertTrue(text.contains(line), line);
        var perk = json(RESOURCE).getAsJsonObject("perk");
        assertEquals(10, perk.get("defaultPercent").getAsInt());
        assertEquals(17, perk.get("bonusPercent").getAsInt());
        assertEquals(List.of("submachine_gun", "auto_rifle"), perk.getAsJsonArray("bonusFamilies")
            .asList().stream().map(JsonElement::getAsString).toList());
        assertEquals("ceil", perk.get("rounding").getAsString());
        assertTrue(perk.get("fromReserves").getAsBoolean());
        assertFalse(perk.get("reloadAnimation").getAsBoolean());
        assertFalse(perk.get("triggersOnReload").getAsBoolean());
    }

    @Test void refillMathUsesActualFamiliesCeilingAndOverflowSafeArithmetic() {
        var bonusIds = Set.of("gnawing_hunger", "steelfeather_repeater", "bug_out_bag");
        for (String id : IDS) {
            var weapon = entry(id);
            assertEquals(bonusIds.contains(id), Set.of("submachine_gun", "auto_rifle").contains(weapon.family()));
            var rate = new BigDecimal(bonusIds.contains(id) ? "0.17" : "0.10");
            for (int capacity : new int[]{1, 2, 5, 6, 7, 9, 10, 11, 17, 20, 29, 30, 59, 60, 100, Integer.MAX_VALUE}) {
                int expected = rate.multiply(BigDecimal.valueOf(capacity)).setScale(0, RoundingMode.CEILING).intValueExact();
                assertEquals(expected, SubsistenceProfile.refillRounds(weapon, capacity), id + "/" + capacity);
            }
        }
        assertEquals(4, SubsistenceProfile.refillRounds(entry("bug_out_bag"), 20));
        assertEquals(3, SubsistenceProfile.refillRounds(entry("long_arm"), 20 + 1));
        assertEquals(10, SubsistenceProfile.refillRounds(entry("retraced_path"), 100));
    }

    @Test void invalidCapacitiesUnsupportedAndNoncanonicalEntriesReturnZero() {
        assertFalse(SubsistenceProfile.supports(null));
        assertEquals(0, SubsistenceProfile.refillRounds(null, 30));
        for (var weapon : WeaponCatalog.all().stream().filter(w -> !LegendaryWeapons.contains(w.id())).toList()) {
            assertEquals(IDS.contains(weapon.id()), SubsistenceProfile.supports(weapon));
            for (int capacity : new int[]{Integer.MIN_VALUE, -1, 0})
                assertEquals(0, SubsistenceProfile.refillRounds(weapon, capacity));
            if (!IDS.contains(weapon.id())) assertEquals(0, SubsistenceProfile.refillRounds(weapon, 100));
        }
        var actual = entry("gnawing_hunger");
        for (var forged : List.of(
                new WeaponCatalog.Entry(actual.id(), "submachine_gun", actual.frame(), actual.name(), actual.source_frame_label(), actual.item_model()),
                new WeaponCatalog.Entry(actual.id(), actual.family(), actual.frame(), "forged", actual.source_frame_label(), actual.item_model()),
                new WeaponCatalog.Entry("unknown", actual.family(), actual.frame(), actual.name(), actual.source_frame_label(), actual.item_model()),
                new WeaponCatalog.Entry(null, null, null, null, null, null))) {
            assertFalse(SubsistenceProfile.supports(forged));
            assertEquals(0, SubsistenceProfile.refillRounds(forged, 100));
        }
    }

    @Test void resourceAndSourceEvidenceRemainBytePinned() throws Exception {
        var pins = Map.of(RESOURCE, "abe5e37fb0632fb9da5a65f803b33349337d686523d4eef054bcb10742dc0835",
            REFS.resolve("clarity-source.json"), "29498f290fa32c305b3ac32b435f7f3ab799c53e4cf4877b166851ce8a0be109",
            REFS.resolve("official-sockets.json"), "db66e3ee2c9cf6184b17dcc0dbde6e6bfb4d0ada690d0be30fd0d1bdaf5d8a15");
        var digest = MessageDigest.getInstance("SHA-256");
        for (var pin : pins.entrySet())
            assertEquals(pin.getValue(), HexFormat.of().formatHex(digest.digest(Files.readAllBytes(pin.getKey()))));
    }
}
