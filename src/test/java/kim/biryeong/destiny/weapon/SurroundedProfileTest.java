package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class SurroundedProfileTest {
    private static final Path RESOURCE = Path.of("src/main/resources/destiny/weapons/w109-surrounded.json");
    private static final Path REFS = Path.of("art/weapons/w109/references");
    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }

    @Test void exactEightBaseSocketsMatchPinnedOfficialPoolsAndCatalog() throws Exception {
        var evidence = json(REFS.resolve("official-sockets.json"));
        var actual = new HashSet<>(SurroundedProfile.rolls());
        var expected = new HashSet<WeaponPerks.Roll>();
        for (var value : evidence.getAsJsonArray("sockets")) {
            var row = value.getAsJsonObject(); var r = row.getAsJsonObject("roll");
            if (r.get("perkHash").getAsLong() != SurroundedProfile.HASH) continue;
            var roll = new WeaponPerks.Roll(r.get("id").getAsString(), r.get("hash").getAsLong(),
                r.get("socket").getAsInt(), r.get("perkHash").getAsLong(), r.get("plugSetHash").getAsLong());
            assertTrue(expected.add(roll));
            var socket = row.getAsJsonObject("socketEntry"); var pool = row.getAsJsonObject("pool");
            assertEquals(roll.plugSetHash(), socket.get("randomizedPlugSetHash").getAsLong());
            assertEquals(roll.plugSetHash(), pool.get("hash").getAsLong());
            assertTrue(pool.getAsJsonArray("reusablePlugItems").asList().stream()
                .anyMatch(p -> p.getAsJsonObject().get("plugItemHash").getAsLong() == SurroundedProfile.HASH));
            var meta = WeaponCharacteristics.of(entry(roll.id()));
            assertEquals(meta.bungieHash(), roll.hash()); assertFalse(meta.exotic());
            assertEquals(4, roll.socket());
        }
        assertEquals(8, actual.size()); assertEquals(expected, actual);
        assertEquals(Set.of("crown_splitter", "falling_guillotine", "temptation_s_hook"),
            actual.stream().map(WeaponPerks.Roll::id).filter(id -> entry(id).family().equals("sword"))
                .collect(java.util.stream.Collectors.toSet()));
        assertTrue(actual.stream().noneMatch(r -> Set.of("rocket_launcher", "grenade_launcher").contains(entry(r.id()).family())));
        assertThrows(UnsupportedOperationException.class, () -> SurroundedProfile.rolls().clear());
    }

    @Test void sourcedFifteenMetreThreeEnemyFortyPercentAndSwordThirtyFivePercent() throws Exception {
        var clarity = json(REFS.resolve("clarity-source.json"));
        assertEquals("039cfbc4732c33573568b28cc6335dd3332a9296", clarity.get("commit").getAsString());
        var source = clarity.getAsJsonObject("entries").getAsJsonObject(Long.toString(SurroundedProfile.HASH));
        assertEquals("Surrounded", source.get("name").getAsString());
        String lines = source.getAsJsonObject("descriptions").getAsJsonArray("en").toString();
        assertTrue(lines.contains("within 15 meters of 3 Enemies grants 40%"));
        assertTrue(lines.contains("lingers for 1.5 seconds"));
        assertTrue(lines.contains("Swords only receive a 35%"));
        assertEquals(15, SurroundedProfile.radius());
        assertEquals(SurroundedCycle.RADIUS, SurroundedProfile.radius());
        assertEquals(SurroundedCycle.MINIMUM_ENEMIES, SurroundedProfile.minimumEnemies());
        assertEquals(SurroundedCycle.LINGER_TICKS, SurroundedProfile.lingerTicks());
        assertEquals("art/weapons/w109/references/clarity-source.json", SurroundedProfile.perk().timingSource());
        for (var roll : SurroundedProfile.rolls()) {
            var weapon = entry(roll.id());
            assertEquals(weapon.family().equals("sword") ? 1.35f : 1.4f, SurroundedProfile.multiplier(weapon));
        }
    }

    @Test void pinnedResourceAndEvidenceBytesAreReproducible() throws Exception {
        var sha = MessageDigest.getInstance("SHA-256");
        var pins = Map.of(RESOURCE, "799f763f0f0882eec7b3a172592fdeb3f95e8fca1a95149274f3db82fac6f777",
            REFS.resolve("clarity-source.json"), "f97553ddc91fdf5cc78263049ca36f505ced62be5093e29635ad31a781579e04",
            REFS.resolve("official-sockets.json"), "47be7ab7a443007d0336791dc5e4cb7e98326470a675bac813ee636f174369d4");
        for (var pin : pins.entrySet())
            assertEquals(pin.getValue(), HexFormat.of().formatHex(sha.digest(Files.readAllBytes(pin.getKey()))));
    }

    private static void rejects(Consumer<JsonObject> edit) throws Exception {
        var resource = json(RESOURCE); edit.accept(resource);
        assertThrows(IllegalStateException.class, () -> SurroundedProfile.validateResource(resource.toString()));
    }

    @Test void rejectsAlteredStageMissingFieldsUnsupportedAndDuplicateRows() throws Exception {
        SurroundedProfile.validateResource(Files.readString(RESOURCE));
        rejects(d -> d.addProperty("stage", "W108"));
        rejects(d -> d.remove("perk")); rejects(d -> d.remove("weapons"));
        rejects(d -> d.addProperty("unexpected", true));
        rejects(d -> d.getAsJsonArray("weapons").remove(0));
        rejects(d -> d.getAsJsonArray("weapons").add(d.getAsJsonArray("weapons").get(0).deepCopy()));
        rejects(d -> d.getAsJsonArray("weapons").set(0, d.getAsJsonArray("weapons").get(1).deepCopy()));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("id", "bad_omens"));
    }

    @Test void rejectsEveryForgedSocketIdentityFieldAndCoercedNumericTypes() throws Exception {
        for (String field : List.of("hash", "socket", "perkHash", "plugSetHash")) {
            rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty(field, -1));
            rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty(field, 4.1));
            rejects(d -> {
                var row = d.getAsJsonArray("weapons").get(0).getAsJsonObject();
                row.addProperty(field, row.get(field).getAsString());
            });
            rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().remove(field));
        }
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("hash", 1251729046.9));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("socket", 4294967300L));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("plugSetHash", 2645685328L));
    }

    @Test void rejectsEveryAlteredPerkConstantIncludingObsoleteEightMetres() throws Exception {
        for (String field : List.of("radius", "minimumEnemies", "lingerTicks", "multiplier", "swordMultiplier", "hash")) {
            rejects(d -> d.getAsJsonObject("perk").addProperty(field, -1));
            rejects(d -> d.getAsJsonObject("perk").remove(field));
            rejects(d -> { var p = d.getAsJsonObject("perk"); p.addProperty(field, p.get(field).getAsString()); });
        }
        rejects(d -> d.getAsJsonObject("perk").addProperty("radius", 8));
        rejects(d -> d.getAsJsonObject("perk").addProperty("minimumEnemies", 2));
        rejects(d -> d.getAsJsonObject("perk").addProperty("lingerTicks", 29));
        rejects(d -> d.getAsJsonObject("perk").addProperty("multiplier", 1.35));
        rejects(d -> d.getAsJsonObject("perk").addProperty("swordMultiplier", 1.4));
        rejects(d -> d.getAsJsonObject("perk").addProperty("id", "enhanced_surrounded"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("timingSource", "forged"));
    }

    @Test void rejectsMalformedNullBooleanDuplicateMembersNonfiniteOverflowAndTrailingInput() throws Exception {
        String original = Files.readString(RESOURCE);
        for (String invalid : List.of("", "null", "[]", "{}", "{", "true", original + " {}",
                original.replace("\"W109\"", "\"W109\", \"stage\": \"W109\""),
                original.replace("15.0", "NaN"), original.replace("15.0", "Infinity"),
                original.replace("1251729046", "9223372036854775808"),
                original.replace("\"radius\": 15.0", "\"radius\": null"),
                original.replace("\"socket\": 4", "\"socket\": true"),
                "/* comment */" + original))
            assertThrows(IllegalStateException.class, () -> SurroundedProfile.validateResource(invalid));
        assertThrows(IllegalStateException.class, () -> SurroundedProfile.validateResource(null));
    }

    @Test void rejectsForgedAndUnsupportedCatalogEntries() {
        assertThrows(IllegalArgumentException.class, () -> SurroundedProfile.multiplier(null));
        assertThrows(IllegalArgumentException.class, () -> SurroundedProfile.multiplier(entry("bad_omens")));
        var actual = entry("steelfeather_repeater");
        var forged = new WeaponCatalog.Entry(actual.id(), "sword", actual.frame(), actual.name(),
            actual.source_frame_label(), actual.item_model());
        assertThrows(IllegalArgumentException.class, () -> SurroundedProfile.multiplier(forged));
    }
}
