package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class MultikillClipProfileTest {
    private static final Path RESOURCE = Path.of("src/main/resources/destiny/weapons/w165-multikill-clip.json");
    private static final Path REFS = Path.of("art/weapons/w165/references");
    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }
    private static void rejects(Consumer<JsonObject> edit) throws Exception {
        var data = json(RESOURCE); edit.accept(data);
        assertThrows(IllegalStateException.class, () -> MultikillClipProfile.validateResource(data.toString()));
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }

    @Test void exactTenSocketsMatchOfficialPoolsAndCanonicalNonexoticCatalog() throws Exception {
        var official = json(REFS.resolve("official-sockets.json"));
        var found = new HashSet<WeaponPerks.Roll>();
        for (var value : official.getAsJsonObject("weapons").getAsJsonArray("multikill_clip")) {
            var row = value.getAsJsonObject();
            var socket = row.getAsJsonObject("socketEntry");
            var pool = row.getAsJsonObject("plugSet");
            var r = new WeaponPerks.Roll(row.get("id").getAsString(), row.get("hash").getAsLong(),
                row.get("socket").getAsInt(), MultikillClipProfile.HASH, pool.get("hash").getAsLong());
            assertTrue(found.add(r)); assertEquals(4, r.socket());
            assertEquals(r.plugSetHash(), socket.get("randomizedPlugSetHash").getAsLong());
            assertFalse(pool.get("isFakePlugSet").getAsBoolean());
            var matches = pool.getAsJsonArray("reusablePlugItems").asList().stream()
                .map(JsonElement::getAsJsonObject)
                .filter(p -> p.get("plugItemHash").getAsLong() == MultikillClipProfile.HASH).toList();
            assertEquals(1, matches.size()); assertTrue(matches.getFirst().get("currentlyCanRoll").getAsBoolean());
            var weapon = entry(r.id()); var meta = WeaponCharacteristics.of(weapon);
            assertTrue(MultikillClipProfile.supports(weapon));
            assertEquals(r.hash(), meta.bungieHash()); assertFalse(meta.exotic());
            assertFalse(Set.of("sword", "glaive").contains(weapon.family()));
        }
        assertEquals(10, found.size()); assertEquals(found, new HashSet<>(MultikillClipProfile.rolls()));
        assertThrows(UnsupportedOperationException.class, () -> MultikillClipProfile.rolls().clear());
        assertEquals(MultikillClipProfile.HASH, official.getAsJsonObject("traits")
            .getAsJsonObject("multikill_clip").get("hash").getAsLong());
    }

    @Test void pinnedBaseSourceMatchesExactTimingAndAllThreeBonuses() throws Exception {
        var clarity = json(REFS.resolve("clarity-source.json"));
        assertEquals("039cfbc4732c33573568b28cc6335dd3332a9296", clarity.get("commit").getAsString());
        assertEquals("881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384",
            clarity.get("sha256").getAsString());
        var source = clarity.getAsJsonObject("entries").getAsJsonObject("multikill_clip");
        assertEquals(2458213969L, source.get("hash").getAsLong());
        assertEquals("Multikill Clip", source.get("name").getAsString());
        String text = source.getAsJsonObject("descriptions").toString();
        for (String line : List.of("within 3.6 seconds", "1|2|3 Weapon Kills within 3.5 seconds",
                "17%|33%|50% increased damage for 5 seconds", "Buff is overwritten every time",
                "removed on stow")) assertTrue(text.contains(line), line);
        assertEquals(new MultikillClipProfile.Perk("multikill_clip", 2458213969L, 70, 72, 100,
            List.of(1f, 1.17f, 1.33f, 1.5f), "art/weapons/w165/references/clarity-source.json"),
            MultikillClipProfile.perk());
        assertEquals(MultikillClipCycle.CHAIN_GAP_TICKS, MultikillClipProfile.chainGapTicks());
        assertEquals(MultikillClipCycle.RELOAD_WINDOW_TICKS, MultikillClipProfile.reloadWindowTicks());
        assertEquals(MultikillClipCycle.DURATION_TICKS, MultikillClipProfile.durationTicks());
        for (int n = 0; n <= 3; n++) {
            var cycle = new MultikillClipCycle();
            for (int i = 0; i < n; i++) cycle.killed(0);
            cycle.reloaded(0);
            assertEquals(MultikillClipProfile.multiplier(n), cycle.capture(0).multiplier());
        }
        assertThrows(UnsupportedOperationException.class, () -> MultikillClipProfile.multipliers().set(3, 2f));
        assertThrows(IllegalArgumentException.class, () -> MultikillClipProfile.multiplier(-1));
        assertThrows(IllegalArgumentException.class, () -> MultikillClipProfile.multiplier(4));
    }

    @Test void exhaustiveAuditCoversEveryCurrentWeaponAndAllAdmittedSockets() throws Exception {
        var official = json(REFS.resolve("official-sockets.json"));
        var audited = new HashSet<String>();
        var admitted = new HashSet<WeaponPerks.Roll>();
        for (var value : official.getAsJsonArray("audit")) {
            var row = value.getAsJsonObject(); String id = row.get("id").getAsString();
            assertTrue(audited.add(id));
            var weapon = entry(id); var meta = WeaponCharacteristics.of(weapon);
            assertEquals(meta.bungieHash(), row.get("hash").getAsLong());
            assertEquals(meta.exotic(), row.get("exotic").getAsBoolean());
            for (var match : row.getAsJsonArray("admissions")) {
                var socket = match.getAsJsonObject();
                assertFalse(meta.exotic());
                admitted.add(new WeaponPerks.Roll(id, meta.bungieHash(), socket.get("socket").getAsInt(),
                    MultikillClipProfile.HASH, socket.get("plugSetHash").getAsLong()));
            }
            assertEquals(!row.getAsJsonArray("admissions").isEmpty(), MultikillClipProfile.supports(weapon));
            // Every direct occurrence is also independently admitted by its official socket pool.
            for (var socket : row.getAsJsonArray("directSockets"))
                assertTrue(admitted.stream().anyMatch(r -> r.id().equals(id) && r.socket() == socket.getAsInt()));
        }
        assertEquals(65, audited.size());
        assertEquals(WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id())).toList().stream().map(WeaponCatalog.Entry::id)
            .collect(java.util.stream.Collectors.toSet()), audited);
        assertEquals(new HashSet<>(MultikillClipProfile.rolls()), admitted);
    }

    @Test void pinnedResourceAndBothEvidenceFilesRemainByteExact() throws Exception {
        var pins = Map.of(RESOURCE, "f878e4d5c699bdc8d77fc8b86ee653caf8cb4dc4532c641b27d5f3c3be94f593",
            REFS.resolve("clarity-source.json"), "9d43a0fb1a0a47dd9c3905baface7d0996dd6abd77e04411373af32d979b8eb4",
            REFS.resolve("official-sockets.json"), "bd211a40f13d9436e79e2ff6de13f81bcf518ccfd46b7c3904c8e804b6c48d51");
        var digest = MessageDigest.getInstance("SHA-256");
        for (var pin : pins.entrySet())
            assertEquals(pin.getValue(), HexFormat.of().formatHex(digest.digest(Files.readAllBytes(pin.getKey()))));
    }

    @Test void stageAndPerkRequireExactFieldsTypesAndPinnedValues() throws Exception {
        MultikillClipProfile.validateResource(Files.readString(RESOURCE));
        for (String field : List.of("stage", "perk", "weapons")) {
            rejects(d -> d.remove(field)); rejects(d -> d.add(field, JsonNull.INSTANCE));
        }
        rejects(d -> d.addProperty("stage", "W164")); rejects(d -> d.addProperty("extra", true));
        for (String field : List.of("id", "hash", "chainGapTicks", "reloadWindowTicks", "durationTicks", "multipliers", "timingSource")) {
            rejects(d -> d.getAsJsonObject("perk").remove(field));
            rejects(d -> d.getAsJsonObject("perk").add(field, JsonNull.INSTANCE));
        }
        rejects(d -> d.getAsJsonObject("perk").addProperty("id", "enhanced_multikill_clip"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("hash", 2458213970L));
        rejects(d -> d.getAsJsonObject("perk").addProperty("hash", "2458213969"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("durationTicks", "90"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("durationTicks", 90.1));
        rejects(d -> d.getAsJsonObject("perk").addProperty("durationTicks", 91));
        rejects(d -> d.getAsJsonObject("perk").addProperty("timingSource", "forged"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("enhanced", true));
        for (String field : List.of("chainGapTicks", "reloadWindowTicks", "durationTicks")) {
            rejects(d -> d.getAsJsonObject("perk").addProperty(field, -1));
            rejects(d -> d.getAsJsonObject("perk").addProperty(field, true));
            rejects(d -> d.getAsJsonObject("perk").addProperty(field, "70"));
            rejects(d -> d.getAsJsonObject("perk").addProperty(field, 70.1));
            rejects(d -> d.getAsJsonObject("perk").addProperty(field,
                d.getAsJsonObject("perk").get(field).getAsInt() + 1));
        }
    }

    @Test void everyMultiplierRejectsRoundingStringBooleanNullAndExtraOrMissingValues() throws Exception {
        for (int i = 0; i < 4; i++) {
            final int index = i;
            rejects(d -> {
                var a = d.getAsJsonObject("perk").getAsJsonArray("multipliers");
                a.set(index, new JsonPrimitive(a.get(index).getAsString()));
            });
            rejects(d -> d.getAsJsonObject("perk").getAsJsonArray("multipliers").set(index, JsonNull.INSTANCE));
            rejects(d -> d.getAsJsonObject("perk").getAsJsonArray("multipliers").set(index, new JsonPrimitive(true)));
            rejects(d -> {
                var a = d.getAsJsonObject("perk").getAsJsonArray("multipliers");
                a.set(index, new JsonPrimitive(a.get(index).getAsBigDecimal().add(new java.math.BigDecimal("0.00000000001"))));
            });
        }
        rejects(d -> d.getAsJsonObject("perk").getAsJsonArray("multipliers").remove(0));
        rejects(d -> d.getAsJsonObject("perk").getAsJsonArray("multipliers").add(1.333));
        rejects(d -> d.getAsJsonObject("perk").getAsJsonArray("multipliers").set(2, new JsonPrimitive(1.333)));
    }

    @Test void everyRollRejectsForgedHashSocketPerkPoolTypesAndExtraFields() throws Exception {
        for (int i = 0; i < 10; i++) {
            final int index = i;
            for (String field : List.of("hash", "socket", "perkHash", "plugSetHash")) {
                rejects(d -> {
                    var r = d.getAsJsonArray("weapons").get(index).getAsJsonObject();
                    r.addProperty(field, r.get(field).getAsLong() + 1);
                });
                rejects(d -> {
                    var r = d.getAsJsonArray("weapons").get(index).getAsJsonObject();
                    r.addProperty(field, r.get(field).getAsString());
                });
                rejects(d -> d.getAsJsonArray("weapons").get(index).getAsJsonObject().remove(field));
                rejects(d -> d.getAsJsonArray("weapons").get(index).getAsJsonObject().addProperty(field, 4.1));
            }
            rejects(d -> d.getAsJsonArray("weapons").get(index).getAsJsonObject().addProperty("extra", true));
        }
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("id", "ace_of_spades"));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("hash", "18446744074530706219"));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("socket", 4294967300L));
    }

    @Test void exactMembershipRejectsMissingDuplicateExtraNullRowsAndAllowsReordering() throws Exception {
        rejects(d -> d.getAsJsonArray("weapons").remove(0));
        rejects(d -> d.getAsJsonArray("weapons").add(d.getAsJsonArray("weapons").get(0).deepCopy()));
        rejects(d -> d.getAsJsonArray("weapons").set(0, d.getAsJsonArray("weapons").get(1).deepCopy()));
        rejects(d -> d.getAsJsonArray("weapons").set(0, JsonNull.INSTANCE));
        rejects(d -> d.add("weapons", new JsonArray()));
        var data = json(RESOURCE); var rows = data.getAsJsonArray("weapons"); rows.add(rows.remove(0));
        MultikillClipProfile.validateResource(data.toString());
    }

    @Test void malformedLenientDuplicateKeysNonfiniteOverflowAndTrailingDataReject() throws Exception {
        String original = Files.readString(RESOURCE);
        for (String broken : new String[]{null, "", "null", "[]", "{}", "{", "true", original + " {}",
                original.replace("\"stage\": \"W165\"", "\"stage\": \"W164\", \"stage\": \"W165\""),
                original.replace("\"durationTicks\": 100", "\"durationTicks\": 1, \"durationTicks\": 100"),
                original.replace("1.17", "NaN"), original.replace("1.17", "Infinity"),
                original.replace("821154603", "9223372036854775808"),
                original.replace("\"stage\"", "stage"), "/* comment */" + original,
                original.replace("\"socket\": 4", "\"socket\": true"),
                original.replace("\"id\": \"gnawing_hunger\"", "\"id\": \"forged\", \"id\": \"gnawing_hunger\""),
                original.replace("1.17", "1e2147483648")})
            assertThrows(IllegalStateException.class, () -> MultikillClipProfile.validateResource(broken));
    }

    @Test void unsupportedNullAndForgedCatalogRecordsFailClosed() {
        assertFalse(MultikillClipProfile.supports(null));
        assertFalse(MultikillClipProfile.supports(entry("ace_of_spades")));
        assertFalse(MultikillClipProfile.supports(entry("bad_omens")));
        var actual = entry("gnawing_hunger");
        var forged = new WeaponCatalog.Entry(actual.id(), "glaive", actual.frame(), actual.name(),
            actual.source_frame_label(), actual.item_model());
        assertFalse(MultikillClipProfile.supports(forged));
    }
}
