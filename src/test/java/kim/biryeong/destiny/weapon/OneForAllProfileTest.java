package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.function.Consumer;
import static org.junit.jupiter.api.Assertions.*;

class OneForAllProfileTest {
    private static final String RESOURCE = "src/main/resources/destiny/weapons/w109-one-for-all.json";
    private static final String REFERENCES = "art/weapons/w109/references/";
    private static JsonObject json(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }
    private static void rejects(Consumer<JsonObject> change) throws Exception {
        var data = json(RESOURCE);
        change.accept(data);
        assertThrows(IllegalStateException.class, () -> OneForAllProfile.validateResource(data.toString()));
    }

    @Test void exactEightBaseSocketsMatchPinnedOfficialRandomizedPoolsIncludingGoldtusk() throws Exception {
        var proof = json(REFERENCES + "official-sockets.json");
        var rolls = OneForAllProfile.rolls();
        assertEquals(8, rolls.size());
        assertEquals(8, rolls.stream().map(WeaponPerks.Roll::id).distinct().count());
        assertThrows(UnsupportedOperationException.class, rolls::clear);
        var found = new HashSet<WeaponPerks.Roll>();
        for (var element : proof.getAsJsonArray("sockets")) {
            var row = element.getAsJsonObject();
            var roll = new Gson().fromJson(row.get("roll"), WeaponPerks.Roll.class);
            if (roll.perkHash() != OneForAllProfile.HASH) continue;
            assertTrue(found.add(roll));
            assertTrue(rolls.contains(roll));
            assertEquals(4, roll.socket());
            assertEquals(roll.plugSetHash(), row.getAsJsonObject("socketEntry").get("randomizedPlugSetHash").getAsLong());
            var pool = row.getAsJsonObject("pool");
            assertEquals(roll.plugSetHash(), pool.get("hash").getAsLong());
            assertFalse(pool.get("isFakePlugSet").getAsBoolean());
            var matches = pool.getAsJsonArray("reusablePlugItems").asList().stream()
                .map(JsonElement::getAsJsonObject).filter(p -> p.get("plugItemHash").getAsLong() == OneForAllProfile.HASH).toList();
            assertEquals(1, matches.size());
            assertTrue(matches.getFirst().get("currentlyCanRoll").getAsBoolean());
            var entry = WeaponCatalog.find(roll.id()).orElseThrow();
            assertTrue(OneForAllProfile.supports(entry));
            assertEquals(roll.hash(), WeaponCharacteristics.of(entry).bungieHash());
            assertFalse(WeaponCharacteristics.of(entry).exotic());
        }
        assertEquals(new HashSet<>(rolls), found);
        assertEquals("sword", WeaponCatalog.find("goldtusk").orElseThrow().family());
        assertTrue(rolls.stream().anyMatch(r -> r.id().equals("goldtusk")));
    }

    @Test void exactClarityEntrySupportsThreeTargetsSixtyTicksThirtyFivePercentAndNonrefreshableTenSeconds() throws Exception {
        var source = json(REFERENCES + "clarity-source.json");
        assertEquals("039cfbc4732c33573568b28cc6335dd3332a9296", source.get("commit").getAsString());
        assertEquals("881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384",
                source.get("sourceFileSha256").getAsString());
        var entry = source.getAsJsonObject("entries").getAsJsonObject("4049631843");
        assertEquals(4049631843L, entry.get("hash").getAsLong());
        assertEquals("Weapon Trait", entry.get("type").getAsString());
        assertEquals("One for All", entry.get("name").getAsString());
        String description = entry.getAsJsonObject("descriptions").toString();
        assertTrue(description.contains("3 Separate Enemies within 3 seconds of each"));
        assertTrue(description.contains("35% increased damage for 10 seconds"));
        assertTrue(description.contains("Does not require Direct Hits."));
        assertTrue(description.contains("Buff duration cannot be refreshed."));
        var official = json(REFERENCES + "official-sockets.json").getAsJsonObject("officialTraits")
            .getAsJsonObject("one_for_all");
        assertEquals(OneForAllProfile.HASH, official.get("hash").getAsLong());
        assertEquals("Hitting three separate targets increases damage for a moderate duration.",
            official.getAsJsonObject("displayProperties").get("description").getAsString());
        assertEquals(new OneForAllProfile.Perk("one_for_all", 4049631843L, 60, 200, 1.35f,
            REFERENCES + "clarity-source.json"), OneForAllProfile.perk());
        assertEquals(60, OneForAllProfile.hitWindowTicks());
        assertEquals(200, OneForAllProfile.durationTicks());
        assertEquals(1.35f, OneForAllProfile.multiplier());
    }

    @Test void strictSettingsRejectWrongStageMissingValuesNumericCoercionsAndRoundedDamage() throws Exception {
        OneForAllProfile.validateResource(Files.readString(Path.of(RESOURCE)));
        rejects(d -> d.addProperty("stage", "W108"));
        rejects(d -> d.add("perk", JsonNull.INSTANCE));
        rejects(d -> d.getAsJsonObject("perk").addProperty("id", "surrounded"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("hash", 4049631844L));
        rejects(d -> d.getAsJsonObject("perk").addProperty("hitWindowTicks", 61));
        rejects(d -> d.getAsJsonObject("perk").addProperty("hitWindowTicks", 60.5));
        rejects(d -> d.getAsJsonObject("perk").addProperty("durationTicks", "200"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("durationTicks", 200.1));
        rejects(d -> d.getAsJsonObject("perk").addProperty("multiplier", 1.35000000001));
        rejects(d -> d.getAsJsonObject("perk").addProperty("multiplier", "1.35"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("timingSource", "unverified"));
        rejects(d -> d.getAsJsonObject("perk").remove("durationTicks"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("enhanced", true));
        rejects(d -> d.addProperty("extra", "forged"));
    }

    @Test void eachExactRollRejectsForgedHashSocketPerkPoolAndTypes() throws Exception {
        for (int i = 0; i < 8; i++) {
            final int row = i;
            for (String field : List.of("hash", "socket", "perkHash", "plugSetHash")) {
                rejects(d -> {
                    var r = d.getAsJsonArray("weapons").get(row).getAsJsonObject();
                    r.addProperty(field, r.get(field).getAsLong() + 1);
                });
                rejects(d -> {
                    var r = d.getAsJsonArray("weapons").get(row).getAsJsonObject();
                    r.addProperty(field, r.get(field).getAsString());
                });
                rejects(d -> d.getAsJsonArray("weapons").get(row).getAsJsonObject().remove(field));
            }
        }
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("hash", 2119346509.1));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("hash", "18446744075828898125"));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("id", "ace_of_spades"));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("id", "bad_omens"));
    }

    @Test void membershipRejectsMissingDuplicateExtraNullRowsAndAcceptsOnlyOrderChanges() throws Exception {
        rejects(d -> d.getAsJsonArray("weapons").remove(0));
        rejects(d -> d.getAsJsonArray("weapons").add(d.getAsJsonArray("weapons").get(0).deepCopy()));
        rejects(d -> d.getAsJsonArray("weapons").set(1, d.getAsJsonArray("weapons").get(0).deepCopy()));
        rejects(d -> d.getAsJsonArray("weapons").set(0, JsonNull.INSTANCE));
        rejects(d -> d.add("weapons", new JsonArray()));
        rejects(d -> d.remove("weapons"));
        var data = json(RESOURCE);
        var rows = data.getAsJsonArray("weapons");
        rows.add(rows.remove(0));
        OneForAllProfile.validateResource(data.toString());
    }

    @Test void malformedNullLenientDuplicateAndTrailingJsonAlwaysReject() throws Exception {
        String original = Files.readString(Path.of(RESOURCE));
        for (String broken : new String[]{null, "", "null", "[]", "{", original + "{}",
                original.replace("\"stage\": \"W109\"", "\"stage\": \"W108\", \"stage\": \"W109\""),
                original.replace("\"durationTicks\": 200", "\"durationTicks\": 1, \"durationTicks\": 200"),
                original.replace("\"multiplier\": 1.35", "\"multiplier\": NaN"),
                original.replace("\"stage\"", "stage"), "/* comment */" + original})
            assertThrows(IllegalStateException.class, () -> OneForAllProfile.validateResource(broken));
    }

    @Test void unsupportedNullAndForgedCatalogEntriesFailClosed() {
        assertFalse(OneForAllProfile.supports(null));
        assertFalse(OneForAllProfile.supports(WeaponCatalog.find("ace_of_spades").orElseThrow()));
        assertFalse(OneForAllProfile.supports(WeaponCatalog.find("bad_omens").orElseThrow()));
        var actual = WeaponCatalog.find("goldtusk").orElseThrow();
        var forged = new WeaponCatalog.Entry(actual.id(), "glaive", actual.frame(), actual.name(),
            actual.source_frame_label(), actual.item_model());
        assertFalse(OneForAllProfile.supports(forged));
    }

    @Test void wrapperSourceContractRetainsIdentityEpochSnapshotAndPostDamageLethalCredit() throws Exception {
        // Structural guard only. Real ServerPlayer/ItemStack lifecycle requires master's central fixtures.
        String source = Files.readString(Path.of("src/main/java/kim/biryeong/destiny/weapon/WeaponOneForAll.java"));
        assertTrue(source.contains("public static final Token NONE"));
        assertTrue(source.contains("private final float multiplier;"));
        assertTrue(source.contains("private final Object editEpoch;"));
        assertTrue(source.contains("p.level().getServer().getTickCount()"));
        assertFalse(source.contains("getGameTime()"));
        assertTrue(source.contains("session.owner == p && session.level == p.level()"));
        assertTrue(source.contains("getItem(i) == stack"));
        assertTrue(source.contains(".filter(session.selection::equals)"));
        assertTrue(source.contains("sessions.get(session.stack) == session"));
        assertTrue(source.contains("token.editEpoch == session.editEpoch"));
        assertTrue(source.contains("!AbilityService.inSuper(p)"));
        assertTrue(source.contains("WeaponLoadout.canUse(p)"));
        String confirmed = source.substring(source.indexOf("public static void confirmed"), source.indexOf("public static void edited"));
        assertFalse(confirmed.contains(".isAlive("));
        assertFalse(confirmed.contains("Combat.isEnemy("));
        assertTrue(confirmed.contains("target.getUUID()"));
        String reads = source.substring(source.indexOf("public static int progress"), source.indexOf("public static Token capture"));
        assertFalse(reads.contains("update("));
        assertFalse(reads.contains("confirmed("));
        assertFalse(reads.contains("computeIfAbsent("));
    }
}
