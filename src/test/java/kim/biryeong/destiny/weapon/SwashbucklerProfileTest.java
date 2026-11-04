package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class SwashbucklerProfileTest {
    private static final Path RESOURCE = Path.of("src/main/resources/destiny/weapons/w110-swashbuckler.json");
    private static final Path REFS = Path.of("art/weapons/w110/references");
    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }
    private static void rejects(Consumer<JsonObject> edit) throws Exception {
        var data = json(RESOURCE); edit.accept(data);
        assertThrows(IllegalStateException.class, () -> SwashbucklerProfile.validateResource(data.toString()));
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }

    @Test void exactEightSocketsMatchOfficialPoolsAndCanonicalNonexoticCatalog() throws Exception {
        var official = json(REFS.resolve("official-sockets.json"));
        var found = new HashSet<WeaponPerks.Roll>();
        for (var value : official.getAsJsonObject("weapons").getAsJsonArray("swashbuckler")) {
            var row = value.getAsJsonObject();
            var socket = row.getAsJsonObject("socketEntry");
            var pool = row.getAsJsonObject("plugSet");
            var r = new WeaponPerks.Roll(row.get("id").getAsString(), row.get("hash").getAsLong(),
                row.get("socket").getAsInt(), SwashbucklerProfile.HASH, pool.get("hash").getAsLong());
            assertTrue(found.add(r)); assertEquals(4, r.socket());
            assertEquals(r.plugSetHash(), socket.get("randomizedPlugSetHash").getAsLong());
            assertFalse(pool.get("isFakePlugSet").getAsBoolean());
            var matches = pool.getAsJsonArray("reusablePlugItems").asList().stream()
                .map(JsonElement::getAsJsonObject)
                .filter(p -> p.get("plugItemHash").getAsLong() == SwashbucklerProfile.HASH).toList();
            assertEquals(1, matches.size()); assertTrue(matches.getFirst().get("currentlyCanRoll").getAsBoolean());
            var weapon = entry(r.id()); var meta = WeaponCharacteristics.of(weapon);
            assertTrue(SwashbucklerProfile.supports(weapon));
            assertEquals(r.hash(), meta.bungieHash()); assertFalse(meta.exotic());
            assertFalse(Set.of("sword", "glaive").contains(weapon.family()));
        }
        assertEquals(8, found.size()); assertEquals(found, new HashSet<>(SwashbucklerProfile.rolls()));
        assertThrows(UnsupportedOperationException.class, () -> SwashbucklerProfile.rolls().clear());
        assertEquals(SwashbucklerProfile.HASH, official.getAsJsonObject("traits")
            .getAsJsonObject("swashbuckler").get("hash").getAsLong());
    }

    @Test void pinnedSourceSpecifiesAllFiveExactBonusesNinetyTicksMeleeAndStow() throws Exception {
        var clarity = json(REFS.resolve("clarity-source.json"));
        assertEquals("039cfbc4732c33573568b28cc6335dd3332a9296", clarity.get("commit").getAsString());
        assertEquals("881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384",
            clarity.get("sha256").getAsString());
        var source = clarity.getAsJsonObject("entries").getAsJsonObject("swashbuckler");
        assertEquals(4082225868L, source.get("hash").getAsLong());
        assertEquals("Swashbuckler", source.get("name").getAsString());
        String text = source.getAsJsonObject("descriptions").toString();
        for (String line : List.of("4.5 seconds", "Maximum of 5 Stacks", "Melee Kills grant all 5 Stacks instantly.",
                "6.7% | 13.3% | 20% | 26.6% | 33.3%", "Stowing the weapon removes the buff."))
            assertTrue(text.contains(line), line);
        assertEquals(new SwashbucklerProfile.Perk("swashbuckler", 4082225868L, 90,
            List.of(1f, 1.067f, 1.133f, 1.2f, 1.266f, 1.333f),
            "art/weapons/w110/references/clarity-source.json"), SwashbucklerProfile.perk());
        assertEquals(SwashbucklerCycle.DURATION_TICKS, SwashbucklerProfile.durationTicks());
        var cycle = new SwashbucklerCycle();
        for (int i = 0; i <= 5; i++) {
            if (i > 0) cycle.killed(i);
            assertEquals(SwashbucklerProfile.multiplier(i), cycle.multiplier(i));
        }
        assertThrows(UnsupportedOperationException.class, () -> SwashbucklerProfile.multipliers().set(5, 2f));
        assertThrows(IllegalArgumentException.class, () -> SwashbucklerProfile.multiplier(-1));
        assertThrows(IllegalArgumentException.class, () -> SwashbucklerProfile.multiplier(6));
    }

    @Test void pinnedResourceAndBothEvidenceFilesRemainByteExact() throws Exception {
        var pins = Map.of(RESOURCE, "0315293d63b74a8fd224772832dea879851151a6ec34998d47d268d170eec7b6",
            REFS.resolve("clarity-source.json"), "0039d63e1baeece90b37d83c2251aca4e26943d10c3bbb48b285742f08689bfc",
            REFS.resolve("official-sockets.json"), "1a16970a69d37077516b621fcda6172032f300f1bae74ab49f751f72937da26a");
        var digest = MessageDigest.getInstance("SHA-256");
        for (var pin : pins.entrySet())
            assertEquals(pin.getValue(), HexFormat.of().formatHex(digest.digest(Files.readAllBytes(pin.getKey()))));
    }

    @Test void stageAndPerkRequireExactFieldsTypesAndPinnedValues() throws Exception {
        SwashbucklerProfile.validateResource(Files.readString(RESOURCE));
        for (String field : List.of("stage", "perk", "weapons")) {
            rejects(d -> d.remove(field)); rejects(d -> d.add(field, JsonNull.INSTANCE));
        }
        rejects(d -> d.addProperty("stage", "W109")); rejects(d -> d.addProperty("extra", true));
        for (String field : List.of("id", "hash", "durationTicks", "multipliers", "timingSource")) {
            rejects(d -> d.getAsJsonObject("perk").remove(field));
            rejects(d -> d.getAsJsonObject("perk").add(field, JsonNull.INSTANCE));
        }
        rejects(d -> d.getAsJsonObject("perk").addProperty("id", "enhanced_swashbuckler"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("hash", 4082225869L));
        rejects(d -> d.getAsJsonObject("perk").addProperty("hash", "4082225868"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("durationTicks", "90"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("durationTicks", 90.1));
        rejects(d -> d.getAsJsonObject("perk").addProperty("durationTicks", 91));
        rejects(d -> d.getAsJsonObject("perk").addProperty("timingSource", "forged"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("enhanced", true));
    }

    @Test void everyMultiplierRejectsRoundingStringBooleanNullAndExtraOrMissingValues() throws Exception {
        for (int i = 0; i < 6; i++) {
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
        rejects(d -> d.getAsJsonObject("perk").getAsJsonArray("multipliers").set(4, new JsonPrimitive(1.267)));
    }

    @Test void everyRollRejectsForgedHashSocketPerkPoolTypesAndExtraFields() throws Exception {
        for (int i = 0; i < 8; i++) {
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
        SwashbucklerProfile.validateResource(data.toString());
    }

    @Test void malformedLenientDuplicateKeysNonfiniteOverflowAndTrailingDataReject() throws Exception {
        String original = Files.readString(RESOURCE);
        for (String broken : new String[]{null, "", "null", "[]", "{}", "{", "true", original + " {}",
                original.replace("\"stage\": \"W110\"", "\"stage\": \"W109\", \"stage\": \"W110\""),
                original.replace("\"durationTicks\": 90", "\"durationTicks\": 1, \"durationTicks\": 90"),
                original.replace("1.067", "NaN"), original.replace("1.067", "Infinity"),
                original.replace("821154603", "9223372036854775808"),
                original.replace("\"stage\"", "stage"), "/* comment */" + original,
                original.replace("\"socket\": 4", "\"socket\": true"),
                original.replace("\"id\": \"gnawing_hunger\"", "\"id\": \"forged\", \"id\": \"gnawing_hunger\""),
                original.replace("1.067", "1e2147483648")})
            assertThrows(IllegalStateException.class, () -> SwashbucklerProfile.validateResource(broken));
    }

    @Test void unsupportedNullAndForgedCatalogRecordsFailClosed() {
        assertFalse(SwashbucklerProfile.supports(null));
        assertFalse(SwashbucklerProfile.supports(entry("ace_of_spades")));
        assertFalse(SwashbucklerProfile.supports(entry("bad_omens")));
        var actual = entry("gnawing_hunger");
        var forged = new WeaponCatalog.Entry(actual.id(), "glaive", actual.frame(), actual.name(),
            actual.source_frame_label(), actual.item_model());
        assertFalse(SwashbucklerProfile.supports(forged));
    }
}
