package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class GraveRobberProfileTest {
    private static final Path RESOURCE = Path.of("src/main/resources/destiny/weapons/w110-grave-robber.json");
    private static final Path REFS = Path.of("art/weapons/w110/references");
    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }

    @Test void exactNineBaseSocketsMatchPinnedOfficialPoolsAndCatalog() throws Exception {
        var evidence = json(REFS.resolve("official-sockets.json"));
        var expected = new HashSet<WeaponPerks.Roll>();
        var sockets = evidence.getAsJsonObject("weapons").getAsJsonArray(GraveRobberProfile.ID);
        assertEquals(9, sockets.size());
        assertEquals(GraveRobberProfile.HASH, evidence.getAsJsonObject("traits")
            .getAsJsonObject(GraveRobberProfile.ID).get("hash").getAsLong());
        for (var value : sockets) {
            var row = value.getAsJsonObject(); var pool = row.getAsJsonObject("plugSet");
            var socket = row.getAsJsonObject("socketEntry");
            long poolHash = pool.get("hash").getAsLong();
            // The original IKELOS socket is a reusable pool; the other eight are randomized pools.
            String poolField = socket.has("randomizedPlugSetHash") ? "randomizedPlugSetHash" : "reusablePlugSetHash";
            assertEquals(poolHash, socket.get(poolField).getAsLong());
            assertTrue(pool.getAsJsonArray("reusablePlugItems").asList().stream()
                .anyMatch(p -> p.getAsJsonObject().get("plugItemHash").getAsLong() == GraveRobberProfile.HASH));
            var roll = new WeaponPerks.Roll(row.get("id").getAsString(), row.get("hash").getAsLong(),
                row.get("socket").getAsInt(), GraveRobberProfile.HASH, poolHash);
            assertTrue(expected.add(roll));
            assertTrue(roll.socket() == 3 || roll.socket() == 4);
            var weapon = entry(roll.id()); var meta = WeaponCharacteristics.of(weapon);
            assertEquals(meta.bungieHash(), roll.hash()); assertFalse(meta.exotic());
            assertTrue(GraveRobberProfile.supports(weapon));
        }
        assertEquals(expected, new HashSet<>(GraveRobberProfile.rolls()));
        assertEquals(Set.of("steelfeather_repeater", "cold_denial", "claws_of_the_wolf", "patron_of_lost_causes",
            "bug_out_bag", "ikelos_smg_v1_0_1", "lonesome", "dead_man_walking_xx7463", "dust_rock_blues"),
            expected.stream().map(WeaponPerks.Roll::id).collect(java.util.stream.Collectors.toSet()));
        assertThrows(UnsupportedOperationException.class, () -> GraveRobberProfile.rolls().clear());
    }

    @Test void currentPinnedSourceSaysPoweredHitsMeleeKillsReservesAndThreeSeconds() throws Exception {
        var clarity = json(REFS.resolve("clarity-source.json"));
        assertEquals("039cfbc4732c33573568b28cc6335dd3332a9296", clarity.get("commit").getAsString());
        var source = clarity.getAsJsonObject("entries").getAsJsonObject(GraveRobberProfile.ID);
        assertEquals(GraveRobberProfile.HASH, source.get("hash").getAsLong());
        assertEquals("Grave Robber", source.get("name").getAsString());
        String lines = source.getAsJsonObject("descriptions").getAsJsonArray("en").toString();
        assertTrue(lines.contains("Powered Melee Hits and (Glaive) Melee Kills"));
        assertTrue(lines.contains("the magazine from reserves."));
        assertTrue(lines.contains("3 second cooldown between activations."));
        assertTrue(lines.contains("doesn't trigger on-reload perks"));
        assertEquals("grave_robber", GraveRobberProfile.perk().id());
        assertEquals(GraveRobberProfile.HASH, GraveRobberProfile.perk().hash());
        assertEquals("art/weapons/w110/references/clarity-source.json", GraveRobberProfile.perk().timingSource());
        assertEquals(60, GraveRobberProfile.cooldownTicks());
        assertEquals(GraveRobberCycle.COOLDOWN_TICKS, GraveRobberProfile.cooldownTicks());
    }

    @Test void pinnedResourceAndEvidenceBytesAreReproducible() throws Exception {
        var sha = MessageDigest.getInstance("SHA-256");
        var pins = Map.of(RESOURCE, "d8746295ed704fa6d5db254247baf000228655924629a3fd4cc4b067cd9a759b",
            REFS.resolve("clarity-source.json"), "0039d63e1baeece90b37d83c2251aca4e26943d10c3bbb48b285742f08689bfc",
            REFS.resolve("official-sockets.json"), "1a16970a69d37077516b621fcda6172032f300f1bae74ab49f751f72937da26a");
        for (var pin : pins.entrySet())
            assertEquals(pin.getValue(), HexFormat.of().formatHex(sha.digest(Files.readAllBytes(pin.getKey()))));
    }

    private static void rejects(Consumer<JsonObject> edit) throws Exception {
        var resource = json(RESOURCE); edit.accept(resource);
        assertThrows(IllegalStateException.class, () -> GraveRobberProfile.validateResource(resource.toString()));
    }

    @Test void rejectsAlteredStageMissingFieldsUnsupportedDuplicateAndExtraRows() throws Exception {
        GraveRobberProfile.validateResource(Files.readString(RESOURCE));
        rejects(d -> d.addProperty("stage", "W109"));
        rejects(d -> d.remove("perk")); rejects(d -> d.remove("weapons"));
        rejects(d -> d.addProperty("unexpected", true));
        rejects(d -> d.getAsJsonArray("weapons").remove(0));
        rejects(d -> d.getAsJsonArray("weapons").add(d.getAsJsonArray("weapons").get(0).deepCopy()));
        rejects(d -> d.getAsJsonArray("weapons").set(0, d.getAsJsonArray("weapons").get(1).deepCopy()));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("id", "bad_omens"));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("id", "ace_of_spades"));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("extra", 1));
    }

    @Test void rejectsForgedSocketFieldsFractionalAndCoercedNumericTypes() throws Exception {
        for (String field : List.of("hash", "socket", "perkHash", "plugSetHash")) {
            rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty(field, -1));
            rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty(field, 3.1));
            rejects(d -> { var row = d.getAsJsonArray("weapons").get(0).getAsJsonObject();
                row.addProperty(field, row.get(field).getAsString()); });
            rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().remove(field));
        }
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("socket", 4294967299L));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("plugSetHash", 473189354L));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("perkHash", 4082225868L));
    }

    @Test void rejectsAlteredCooldownAndEveryPerkIdentityField() throws Exception {
        for (String field : List.of("hash", "cooldownTicks")) {
            rejects(d -> d.getAsJsonObject("perk").addProperty(field, -1));
            rejects(d -> d.getAsJsonObject("perk").remove(field));
            rejects(d -> { var p = d.getAsJsonObject("perk"); p.addProperty(field, p.get(field).getAsString()); });
        }
        for (int ticks : new int[]{0, 59, 61, Integer.MAX_VALUE})
            rejects(d -> d.getAsJsonObject("perk").addProperty("cooldownTicks", ticks));
        rejects(d -> d.getAsJsonObject("perk").addProperty("cooldownTicks", 60.1));
        rejects(d -> d.getAsJsonObject("perk").addProperty("id", "enhanced_grave_robber"));
        rejects(d -> d.getAsJsonObject("perk").remove("id"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("timingSource", "forged"));
        rejects(d -> d.getAsJsonObject("perk").remove("timingSource"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("killOnly", true));
    }

    @Test void rejectsMalformedNullBooleanDuplicateMembersNonfiniteOverflowAndTrailingInput() throws Exception {
        String original = Files.readString(RESOURCE);
        for (String invalid : List.of("", "null", "[]", "{}", "{", "true", original + " {}",
                original.replace("\"W110\"", "\"W110\", \"stage\": \"W110\""),
                original.replace("\"cooldownTicks\": 60", "\"cooldownTicks\": 60, \"cooldownTicks\": 60"),
                original.replace("\"socket\": 3", "\"socket\": 3, \"socket\": 3"),
                original.replace("\"cooldownTicks\": 60", "\"cooldownTicks\": NaN"),
                original.replace("\"cooldownTicks\": 60", "\"cooldownTicks\": Infinity"),
                original.replace("1251729046", "9223372036854775808"),
                original.replace("\"cooldownTicks\": 60", "\"cooldownTicks\": null"),
                original.replace("\"socket\": 3", "\"socket\": true"),
                "/* comment */" + original))
            assertThrows(IllegalStateException.class, () -> GraveRobberProfile.validateResource(invalid));
        assertThrows(IllegalStateException.class, () -> GraveRobberProfile.validateResource(null));
        rejects(d -> d.getAsJsonObject("perk").add("cooldownTicks", JsonParser.parseString("[[[[[[60]]]]]]")));
        rejects(d -> { var a = d.getAsJsonArray("weapons"); while (a.size() < 17) a.add(a.get(0).deepCopy()); });
    }

    @Test void rejectsForgedUnsupportedAndExoticCatalogEntries() {
        assertFalse(GraveRobberProfile.supports(null));
        assertFalse(GraveRobberProfile.supports(entry("bad_omens")));
        assertFalse(GraveRobberProfile.supports(entry("ace_of_spades")));
        var actual = entry("steelfeather_repeater");
        var forged = new WeaponCatalog.Entry(actual.id(), "sword", actual.frame(), actual.name(),
            actual.source_frame_label(), actual.item_model());
        assertFalse(GraveRobberProfile.supports(forged));
    }
}
