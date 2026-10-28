package kim.biryeong.destiny.sound;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.sound.ReloadAudioProfile.Clip;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponProfile;
import org.junit.jupiter.api.Test;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

/** Independent finite identities and inherited deadlines; no acoustic identity/hearing claim. */
class NamedAudioW102Test {
    private static final Path ART = Path.of("art/weapons/w102/audio");
    private static final Path RES = Path.of("src/main/resources");
    private static final Map<String, String> FAMILIES = Map.of(
            "blast_furnace", "pulse_rifle", "chattering_bone", "pulse_rifle",
            "aishas_embrace", "scout_rifle", "long_arm", "scout_rifle",
            "whispering_slab", "bow", "retrofit_escapade", "machine_gun");
    private static final Set<String> TIMED = Set.of("aishas_embrace:46", "blast_furnace:24",
            "blast_furnace:43", "chattering_bone:24", "chattering_bone:34", "retrofit_escapade:90");
    private record Pin(String id, String action, String folder, String drive, String sha) {}
    private static final List<Pin> PINS = List.of(
            new Pin("blast_furnace", "fire", "1_lzX2VeWtM9APWox0nRDqCbiHoEx65rE", "1tEqq1X5Uo59EnCOMTgb3LtPyUBDcp9Im", "34fc6eb60618ca8a1eea4c6de2a2879c294a0741c12ab1a9d6cb935a267e8a8d"),
            new Pin("blast_furnace", "reload", "1_lzX2VeWtM9APWox0nRDqCbiHoEx65rE", "1peMhfJX85VJtXnzIhzuQmBN7MfDoKj-R", "3d785814085b4945ae38c126c7da4144ba17622fd1cb9140175936bfa5278baf"),
            new Pin("chattering_bone", "fire", "1ZJiFDuXrgh8QBqaSfSNpEOyTCMBmeiSr", "1-X4w_iHBKxroRVlrjVi_EAx_chb4cHDJ", "a8328639260f8b033a75721864082f160c7227ec0084f98c11333a5d443591d2"),
            new Pin("chattering_bone", "reload", "1ZJiFDuXrgh8QBqaSfSNpEOyTCMBmeiSr", "1DYvTv12wNvSwoyHzBnOUYZ6r2LoJ_6du", "48f6c156e5c90d398be2640dcb22231afa0a5e06d2d9420bcf9dfd5be1875f44"),
            new Pin("aishas_embrace", "fire", "1cxZNF8D46mAb-iBWbJwxmqYzOu4NGl2g", "18ogeCxQCYRvtRLe5LWziYbctGopN62sG", "0649f2b3bee1e17d1baf2ec52dc0cd64464216a46c275270371ec73b8206fbc6"),
            new Pin("aishas_embrace", "reload", "1cxZNF8D46mAb-iBWbJwxmqYzOu4NGl2g", "1Ay45wGx86ZNrTUi6O0E3QIUCW5BHrKFa", "b49840534aa288d428f759cddb01958dd776b0c8fbf689ea8526b474c22374f3"),
            new Pin("long_arm", "fire", "1_1pwacAXcVs6wJm7U9OuscnGbrGg9K7p", "1TXx6af6I4LxMm6hYKIJ5Aad4KOv3c38f", "3d5c9ebf6fbc27fc133cf1af803a7eaf1fb97c142edb7aad9a0b66123a00456d"),
            new Pin("whispering_slab", "fire", "1EnZCnW__Yu5QV3FxG0Ns_fUGCUR502Nk", "1nFo6nvNuOMBVVGseh2v5n-kiCBjQ9_dF", "dd418a0de4689952f6cd77f9c3ce49ff0b9d95c105d53cd3aa954c3dd492748f"),
            new Pin("retrofit_escapade", "fire", "1bAwsxY_CNiiiFKC8zzyZlt7UyAav4erF", "1cTrlAKqj2j6tASojKlE_gVNJH7ymOTed", "d09d3423b8d7dd8507098a97461ec7a22984dc2fa10e6067595b2f0e8b5cae79"),
            new Pin("retrofit_escapade", "reload", "1bAwsxY_CNiiiFKC8zzyZlt7UyAav4erF", "1UtJqWcVtJ5s2dSgvBBzVzxIvauxTqAfB", "31191b410564eb7d6bf71044c209423abdd312d8f60de124291f9d78dca36063"));

    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }
    private static String sha(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
    private static String sha(Path path) throws Exception { return sha(Files.readAllBytes(path)); }
    private static String key(Clip c) { return c.id() + ":" + c.ticks(); }
    private static List<Clip> clips(String file) throws Exception {
        return List.of(new Gson().fromJson(json(RES.resolve("destiny/sounds/" + file))
                .getAsJsonArray("entries"), Clip[].class));
    }
    private static Map<String, JsonObject> definitions() {
        var expected = new HashMap<String, JsonObject>();
        for (var pin : PINS) expected.put("weapon." + pin.id + "." + pin.action,
                definition(pin.id, pin.action, pin.action));
        for (var k : TIMED) {
            var parts = k.split(":");
            expected.put("weapon.reload_w102." + parts[0] + "." + parts[1],
                    definition(parts[0], "reload", "reload_" + parts[1]));
        }
        return expected;
    }
    private static JsonObject definition(String id, String action, String file) {
        return JsonParser.parseString("{\"subtitle\":\"subtitles.destiny.weapon." + FAMILIES.get(id)
                + "." + action + "\",\"sounds\":[{\"name\":\"destiny:w102/" + id + "/" + file
                + "\",\"stream\":false,\"attenuation_distance\":32}]}").getAsJsonObject();
    }

    @Test void exactSixIdentitiesTenPinsAndSixteenDefinitionsHaveNoFamilySubstitutions() throws Exception {
        var pins = JsonParser.parseString(Files.readString(ART.resolve("source-pins.json"))).getAsJsonArray();
        assertEquals(10, pins.size());
        var observed = new HashSet<String>();
        for (var value : pins) {
            var p = value.getAsJsonObject();
            String id = p.get("id").getAsString(), action = p.get("action").getAsString();
            var pin = PINS.stream().filter(e -> e.id.equals(id) && e.action.equals(action)).findFirst().orElseThrow();
            assertTrue(observed.add(id + ":" + action));
            assertEquals(FAMILIES.get(id), WeaponCatalog.find(id).orElseThrow().family());
            assertEquals(FAMILIES.get(id), p.get("family").getAsString());
            assertEquals(pin.folder, p.get("folderId").getAsString());
            assertEquals(pin.drive, p.get("driveId").getAsString());
            assertEquals(pin.sha, p.get("sourceSha256").getAsString());
            assertEquals(pin.sha, p.get("actualPayloadSha256").getAsString());
            assertEquals(action.equals("fire") ? "Fire_1.mp3" : "Reload_1.mp3", p.get("originalName").getAsString());
            assertEquals("https://drive.google.com/uc?export=download&id=" + pin.drive, p.get("sourceUrl").getAsString());
            assertEquals("weapon." + id + "." + action, p.get("event").getAsString());
        }
        var expected = definitions();
        assertEquals(16, expected.size());
        assertEquals(expected, json(ART.resolve("event-definitions.json")).asMap());
        var table = json(RES.resolve("assets/destiny/sounds.json"));
        for (var e : expected.entrySet()) {
            assertEquals(e.getValue(), table.get(e.getKey()), e.getKey());
            assertTrue(DestinySounds.has(e.getKey()));
        }
        for (var pin : PINS) assertEquals("weapon." + pin.id + "." + pin.action,
                DestinySounds.weaponKey(WeaponCatalog.find(pin.id).orElseThrow(), pin.action));
        assertFalse(DestinySounds.has("weapon.long_arm.reload"));
        assertFalse(DestinySounds.has("weapon.whispering_slab.reload"));
        assertTrue(WeaponProfile.forEntry(WeaponCatalog.find("long_arm").orElseThrow()).shellReload());
        assertEquals("weapon.scout_rifle.reload", DestinySounds.weaponKey(WeaponCatalog.find("long_arm").orElseThrow(), "reload"));
        assertEquals("weapon.bow.reload", DestinySounds.weaponKey(WeaponCatalog.find("whispering_slab").orElseThrow(), "reload"));
    }

    @Test void productionLookupOverlaysExactlySixInheritedKeysAndRejectsUnsupportedOrForgedClips() throws Exception {
        var old = clips("w63-reload.json");
        var replacements = clips("w102-reload.json");
        assertEquals("W102", json(RES.resolve("destiny/sounds/w102-reload.json")).get("stage").getAsString());
        assertEquals(6, replacements.size());
        assertEquals(TIMED, replacements.stream().map(NamedAudioW102Test::key).collect(java.util.stream.Collectors.toSet()));
        assertEquals(TIMED, old.stream().filter(c -> TIMED.contains(key(c))).map(NamedAudioW102Test::key)
                .collect(java.util.stream.Collectors.toSet()));
        for (var legacy : old) {
            var actual = ReloadAudioProfile.find(WeaponCatalog.find(legacy.id()).orElseThrow(), legacy.ticks()).orElseThrow();
            if (!TIMED.contains(key(legacy))) {
                assertSame(legacy, NamedReloadAudioW102.overlay(legacy));
                assertEquals(legacy, actual, key(legacy));
                assertFalse(NamedReloadAudioW102.isReplacement(actual));
                continue;
            }
            var expected = replacements.stream().filter(c -> key(c).equals(key(legacy))).findFirst().orElseThrow();
            assertEquals(expected, NamedReloadAudioW102.overlay(legacy));
            assertEquals(expected, actual, "Actual production lookup must return the replacement");
            assertTrue(NamedReloadAudioW102.isReplacement(actual));
            assertEquals("weapon.reload_w102." + legacy.id() + "." + legacy.ticks(), actual.event());
            assertEquals("weapon." + legacy.id() + ".reload", actual.sourceEvent());
            assertEquals("assets/destiny/sounds/w102/" + legacy.id() + "/reload_" + legacy.ticks() + ".ogg", actual.asset());
            assertEquals(sha(RES.resolve("assets/destiny/sounds/w102/" + legacy.id() + "/reload.ogg")), actual.sourceSha256());
            for (var forged : List.of(
                    new Clip(legacy.id(), legacy.ticks(), "weapon.reload_w63.wrong", legacy.sourceEvent(), legacy.sourceSha256(), legacy.asset()),
                    new Clip(legacy.id(), legacy.ticks(), legacy.event(), "weapon.wrong.reload", legacy.sourceSha256(), legacy.asset()),
                    new Clip(legacy.id(), legacy.ticks(), legacy.event(), legacy.sourceEvent(), legacy.sourceSha256(), "assets/destiny/sounds/w63/reload/wrong.ogg")))
                assertThrows(IllegalStateException.class, () -> NamedReloadAudioW102.overlay(forged));
        }
        assertEquals(6, ReloadAudioProfile.all().stream().filter(NamedReloadAudioW102::isReplacement).count());
        for (String id : FAMILIES.keySet()) {
            var entry = WeaponCatalog.find(id).orElseThrow();
            for (int ticks : new int[]{-1, 0, 1, 23, 25, 33, 35, 42, 44, 45, 47, 89, 91, 1201}) {
                assertTrue(ReloadAudioProfile.find(entry, ticks).isEmpty(), id + ":" + ticks);
                var unsupported = new Clip(id, ticks, "unused", "unused", "unused", "unused");
                assertSame(unsupported, NamedReloadAudioW102.overlay(unsupported));
                assertFalse(NamedReloadAudioW102.isReplacement(unsupported));
            }
        }
        assertTrue(ReloadAudioProfile.find(null, 46).isEmpty());
        assertFalse(NamedReloadAudioW102.isReplacement(null));
        assertThrows(UnsupportedOperationException.class, () -> ReloadAudioProfile.all().clear());
    }

    @Test void exactSixteenOggResourcesMatchManifestAndMonoVorbisMetadataWithExactTimedGranules() throws Exception {
        var expectedPaths = new HashSet<String>();
        for (var d : definitions().values()) {
            var sound = d.getAsJsonArray("sounds").get(0).getAsJsonObject().get("name").getAsString();
            expectedPaths.add("assets/destiny/sounds/" + sound.substring("destiny:".length()) + ".ogg");
        }
        try (var files = Files.walk(RES.resolve("assets/destiny/sounds/w102"))) {
            assertEquals(expectedPaths, files.filter(Files::isRegularFile).map(RES::relativize).map(Path::toString)
                    .collect(java.util.stream.Collectors.toSet()));
        }
        var manifest = json(ART.resolve("implementation.json"));
        assertEquals("W102", manifest.get("stage").getAsString());
        assertEquals(10, manifest.getAsJsonArray("records").size());
        assertEquals(6, manifest.getAsJsonArray("timedRecords").size());
        assertFalse(manifest.get("runtimeAudioAccepted").getAsBoolean());
        for (String path : expectedPaths) {
            byte[] bytes = Files.readAllBytes(RES.resolve(path));
            var output = manifest.getAsJsonObject("outputs").getAsJsonObject("src/main/resources/" + path);
            assertEquals(output.get("sha256").getAsString(), sha(bytes), path);
            assertEquals(output.get("bytes").getAsInt(), bytes.length, path);
            assertTrue(oggSamples(bytes) > 0, path);
        }
        for (var value : manifest.getAsJsonArray("records")) {
            var row = value.getAsJsonObject();
            var pin = PINS.stream().filter(p -> ("weapon." + p.id + "." + p.action).equals(row.get("event").getAsString())).findFirst().orElseThrow();
            assertEquals(pin.sha, row.get("source_sha256").getAsString());
            var output = row.getAsJsonObject("output");
            assertEquals(1, output.get("channels").getAsInt());
            assertEquals(32000, output.get("sample_rate_hz").getAsInt());
            assertEquals(0, output.get("clipped_samples").getAsInt());
            assertTrue(Double.isFinite(output.get("sample_peak_dbfs").getAsDouble()));
            assertTrue(output.get("sample_peak_dbfs").getAsDouble() <= -1);
            assertEquals(sha(Path.of(row.get("asset_path").getAsString())), output.get("sha256").getAsString());
        }
        var timedSeen = new HashSet<String>();
        for (var value : manifest.getAsJsonArray("timedRecords")) {
            var row = value.getAsJsonObject();
            String id = row.get("id").getAsString(); int ticks = row.get("ticks").getAsInt();
            assertTrue(timedSeen.add(id + ":" + ticks));
            assertEquals(ticks * 1600L, oggSamples(Files.readAllBytes(RES.resolve(row.get("asset").getAsString()))));
            var output = row.getAsJsonObject("output");
            assertEquals(ticks * 1600L, output.get("granuleSamples").getAsLong());
            assertEquals(0, output.get("clippedSamples").getAsInt());
            assertTrue(Double.isFinite(output.get("samplePeakDbfs").getAsDouble()));
            assertTrue(output.get("samplePeakDbfs").getAsDouble() <= -1);
            assertEquals(sha(RES.resolve(row.get("asset").getAsString())), output.get("sha256").getAsString());
        }
        assertEquals(TIMED, timedSeen);
    }

    /** Parse physical Ogg pages and the first Vorbis identification packet, including EOS. */
    private static long oggSamples(byte[] bytes) {
        var buffer = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);
        long samples = -1; int offset = 0; boolean identified = false, eos = false;
        while (offset < bytes.length) {
            assertTrue(offset + 27 <= bytes.length);
            assertEquals("OggS", new String(bytes, offset, 4, StandardCharsets.US_ASCII));
            assertEquals(0, bytes[offset + 4]);
            int segments = Byte.toUnsignedInt(bytes[offset + 26]), body = offset + 27 + segments;
            assertTrue(body <= bytes.length);
            int size = 0;
            for (int i = 0; i < segments; i++) size += Byte.toUnsignedInt(bytes[offset + 27 + i]);
            assertTrue(body + size <= bytes.length);
            if (!identified) {
                assertTrue(size >= 30); assertEquals(1, bytes[body]);
                assertEquals("vorbis", new String(bytes, body + 1, 6, StandardCharsets.US_ASCII));
                assertEquals(0, buffer.getInt(body + 7)); assertEquals(1, bytes[body + 11]);
                assertEquals(32000, buffer.getInt(body + 12)); identified = true;
            }
            if (buffer.getLong(offset + 6) >= 0) samples = buffer.getLong(offset + 6);
            eos = (bytes[offset + 5] & 4) != 0;
            offset = body + size;
        }
        assertEquals(bytes.length, offset); assertTrue(identified && eos);
        return samples;
    }

    @Test void originalDefinitionsW63TableAndAll196PreservedSourceFilesRemainByteExact() throws Exception {
        assertEquals("e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b", sha(RES.resolve("destiny/sounds/w63-reload.json")));
        assertEquals("45f4bffbe2cd3915b5b068c517522254692d8f3895283a25cfebce04efaa7b7c", sha(ART.resolve("preserved-audio.json")));
        var preserved = json(ART.resolve("preserved-audio.json"));
        assertEquals(196, preserved.size());
        for (var row : preserved.entrySet()) assertEquals(row.getValue().getAsString(), sha(Path.of(row.getKey())), row.getKey());
        var table = json(RES.resolve("assets/destiny/sounds.json"));
        var original = new TreeMap<>(ReviewedAudioW234.legacyW102(table).asMap());
        definitions().keySet().forEach(original::remove);
        assertEquals(162, original.size());
        var canonical = new StringBuilder();
        original.forEach((k, v) -> canonical.append(k).append('=').append(v).append('\n'));
        assertEquals("49bcdbf5b0ef0ebd0c1c855a60fefe2afff2631daf374b036f72acf6871af6f3",
                sha(canonical.toString().getBytes(StandardCharsets.UTF_8)), "Every pre-W102 definition, including family and W63 aliases");
        var manifest = json(ART.resolve("implementation.json"));
        for (var input : manifest.getAsJsonObject("inputPins").entrySet())
            assertEquals(input.getValue().getAsString(), sha(ART.resolve(input.getKey())));
    }
}
