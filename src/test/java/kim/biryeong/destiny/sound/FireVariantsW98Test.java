package kim.biryeong.destiny.sound;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import org.junit.jupiter.api.Test;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Asset/routing/provenance contracts, not client selection, hearing or renderer evidence. */
class FireVariantsW98Test {
    private static final Path ART = Path.of("art/weapons/w98/audio");
    private static final Path SOUNDS = Path.of("src/main/resources/assets/destiny/sounds.json");
    private static final Map<String, String> FAMILIES = Map.of(
            "seventh_seraph_officer_revolver", "hand_cannon", "steelfeather_repeater", "auto_rifle", "the_recluse", "submachine_gun");
    private static final Map<String, String> FOLDERS = Map.of(
            "seventh_seraph_officer_revolver", "1nrnK-zGDIanwW7xKpBUqjjwQ33I_j-2l",
            "steelfeather_repeater", "1uebuIuIJZ2J5s5yiK99TC5RvGt70LfiM", "the_recluse", "1cA-sz60bEIzxcYGQ9nUlJJX3E9AY4nS2");

    private static JsonObject json(Path path) throws Exception { return JsonParser.parseString(Files.readString(path)).getAsJsonObject(); }
    private static String sha(Path path) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))); }
    private static Set<String> sounds() {
        var result = new HashSet<String>();
        for (var id : FAMILIES.keySet()) for (int i : new int[]{2, 3}) result.add("destiny:w98/" + id + "/fire_" + i);
        return Set.copyOf(result);
    }

    private static Set<String> namedW102Events() {
        var keys = new HashSet<String>();
        for (String id : Set.of("blast_furnace", "chattering_bone", "aishas_embrace", "long_arm", "whispering_slab", "retrofit_escapade"))
            keys.add("weapon." + id + ".fire");
        for (String id : Set.of("blast_furnace", "chattering_bone", "aishas_embrace", "retrofit_escapade"))
            keys.add("weapon." + id + ".reload");
        for (String pair : Set.of("aishas_embrace.46", "blast_furnace.24", "blast_furnace.43", "chattering_bone.24", "chattering_bone.34", "retrofit_escapade.90"))
            keys.add("weapon.reload_w102." + pair);
        return Set.copyOf(keys);
    }
    private static JsonObject namedW102Definitions(JsonObject now) throws Exception {
        var named = json(Path.of("art/weapons/w102/audio/event-definitions.json"));
        assertEquals(namedW102Events(), named.keySet());
        for (String key : namedW102Events()) assertEquals(named.get(key), now.get(key), key);
        return named;
    }

    @Test void onlyThreeExactEventsGainTwoAlternativesAndKeepOriginalFirstEntryAndSubtitles() throws Exception {
        var now = ReviewedAudioW234.legacyW102(json(SOUNDS));
        var beforePath = Path.of("docs/qa/2026-10-25/w98/before/src/main/resources/assets/destiny/sounds.json");
        var w96Path = Path.of("art/qa/w96/implementation.json");
        assertEquals("bbc7ae9a16f42d4b8a4983c29bd8b39eb8e7e8a12f9ec200cdfcc7f501784458", sha(w96Path));
        assertEquals(json(w96Path).getAsJsonObject("clientAssets").get("src/main/resources/assets/destiny/sounds.json").getAsString(), sha(beforePath));
        var before = json(beforePath);
        // W102 explicitly adds only these ten named actions and six timed variants.
        namedW102Definitions(now);
        var inheritedKeys = new HashSet<>(now.keySet());
        assertTrue(inheritedKeys.containsAll(namedW102Events()));
        inheritedKeys.removeAll(namedW102Events());
        assertEquals(before.keySet(), inheritedKeys, "No inherited event removed or renamed");
        var changed = new HashSet<String>();
        for (String key : before.keySet()) if (!before.get(key).equals(now.get(key))) changed.add(key);
        assertEquals(FAMILIES.keySet().stream().map(id -> "weapon." + id + ".fire").collect(java.util.stream.Collectors.toSet()), changed);
        var sidecar = json(ART.resolve("event-definitions.json"));
        assertEquals(changed, sidecar.keySet());
        for (String id : FAMILIES.keySet()) {
            String key = "weapon." + id + ".fire";
            var expected = before.getAsJsonObject(key).deepCopy();
            assertEquals(1, expected.getAsJsonArray("sounds").size());
            for (int i : new int[]{2, 3}) {
                var value = new JsonObject(); value.addProperty("name", "destiny:w98/" + id + "/fire_" + i);
                value.addProperty("stream", false); value.addProperty("attenuation_distance", 32);
                expected.getAsJsonArray("sounds").add(value);
            }
            assertEquals(expected, now.get(key), "Exactly two unit-weight, unchanged-pitch alternatives; original remains first");
            assertEquals(expected, sidecar.get(key));
        }
    }

    // W98 owns audio variants, not a perpetual snapshot of every model/HUD asset.
    // The old W96 all-art inventory predates W156 Ace sights, W159 holograms,
    // W161 Ammit graphs and W162 scope art. Their stage manifests and art tests
    // own those changes. No legacy Ace hash is repinned or treated as audio proof.
    private static boolean runtimeAudioPath(String path) {
        String lower=path.toLowerCase(java.util.Locale.ROOT);
        return lower.contains("/sounds/") || Set.of("ogg", "wav", "mp3", "flac", "opus", "aac", "m4a", "aif", "aiff")
                .stream().anyMatch(extension -> lower.endsWith("."+extension));
    }

    private static Set<String> namedW102AudioPaths() {
        String root="src/main/resources/assets/destiny/sounds/w102/";
        var paths=new HashSet<String>();
        for (String id : Set.of("blast_furnace", "chattering_bone", "aishas_embrace", "long_arm", "whispering_slab", "retrofit_escapade"))
            paths.add(root+id+"/fire.ogg");
        for (String id : Set.of("blast_furnace", "chattering_bone", "aishas_embrace", "retrofit_escapade"))
            paths.add(root+id+"/reload.ogg");
        for (String pair : Set.of("aishas_embrace:46", "blast_furnace:24", "blast_furnace:43", "chattering_bone:24", "chattering_bone:34", "retrofit_escapade:90")) {
            var parts=pair.split(":"); paths.add(root+parts[0]+"/reload_"+parts[1]+".ogg");
        }
        assertEquals(16, paths.size());
        return Set.copyOf(paths);
    }

    private static void assertAudioInventory(Set<String> expected, Set<String> actual) {
        assertEquals(expected, actual, "Closed runtime audio inventory: no removed inherited clips or extra OGG/audio anywhere under assets");
    }

    @Test void inheritedAudioBytesAndExactlySixW98PlusSixteenW102ClipsFormClosedRuntimeInventory() throws Exception {
        var inherited=json(Path.of("art/qa/w96/implementation.json")).getAsJsonObject("clientAssets");
        assertEquals(7013, inherited.size());
        var expected=new HashSet<String>();
        for (var row : inherited.entrySet()) if (runtimeAudioPath(row.getKey())) {
            assertTrue(expected.add(row.getKey()));
            assertEquals(row.getValue().getAsString(), sha(Path.of(row.getKey())), row.getKey());
        }
        assertEquals(187, expected.size(), "Every inherited W96 audio file remains pinned");
        var w98=sounds().stream().map(sound -> "src/main/resources/assets/destiny/sounds/"
                +sound.substring(8)+".ogg").collect(java.util.stream.Collectors.toSet());
        assertEquals(6, w98.size());
        for (String stage : Set.of("w98", "w102")) {
            var declared=stage.equals("w98") ? w98 : namedW102AudioPaths();
            var outputs=json(Path.of("art/weapons/"+stage+"/audio/implementation.json")).getAsJsonObject("outputs");
            var runtime=new HashSet<String>();
            for (var output : outputs.entrySet()) if (output.getKey().startsWith("src/main/resources/assets/")) {
                runtime.add(output.getKey());
                if (stage.equals("w102")) {
                    var record=output.getValue().getAsJsonObject();
                    assertEquals(Set.of("sha256", "bytes"), record.keySet());
                    assertEquals(record.get("sha256").getAsString(), sha(Path.of(output.getKey())), output.getKey());
                    assertEquals(record.get("bytes").getAsLong(), Files.size(Path.of(output.getKey())), output.getKey());
                } else assertEquals(output.getValue().getAsString(), sha(Path.of(output.getKey())), output.getKey());
            }
            assertEquals(declared, runtime, stage+" manifests only its exact reviewed clips");
            for (String path : declared) assertTrue(expected.add(path), "No inherited audio overwritten: "+path);
        }
        var actual=new HashSet<String>();
        try (var paths=Files.walk(Path.of("src/main/resources/assets"))) {
            paths.filter(Files::isRegularFile).map(Path::toString)
                    .filter(FireVariantsW98Test::runtimeAudioPath).forEach(actual::add);
        }
        assertEquals(209, expected.size(), "Historical W102 inventory remains unchanged");
        for (String path : ReviewedAudioW234.verifiedLaterAudioPaths())
            assertTrue(expected.add(path), "Later stages cannot overwrite inherited audio: " + path);
        var crucible = json(Path.of("art/crucible/w260/sound-provenance.json")).getAsJsonObject("cues");
        var definitions = json(Path.of("src/main/resources/assets/destiny_crucible/sounds.json"));
        assertEquals(Set.of("control", "start", "capture_a", "capture_b", "capture_c",
                "lost_a", "lost_b", "lost_c", "advantage", "enemy_advantage",
                "power_play", "enemy_power_play", "victory", "defeat"), crucible.keySet());
        assertEquals(crucible.keySet(), definitions.keySet());
        for (var entry : crucible.entrySet()) {
            String path = "src/main/resources/assets/destiny_crucible/sounds/w260/" + entry.getKey() + ".ogg";
            assertEquals(entry.getValue().getAsJsonObject().get("sha256").getAsString(), sha(Path.of(path)), path);
            assertEquals("destiny_crucible:w260/" + entry.getKey(), definitions.getAsJsonObject(entry.getKey())
                    .getAsJsonArray("sounds").get(0).getAsJsonObject().get("name").getAsString());
            assertTrue(expected.add(path), "Crucible does not replace inherited audio");
        }
        var music = json(Path.of("art/audio/w262/provenance.json")).getAsJsonArray("tracks");
        var musicEvents = new HashSet<String>();
        for (var value : music) {
            var track = value.getAsJsonObject();
            String path = track.get("output").getAsString();
            String event = track.get("event").getAsString();
            assertTrue(musicEvents.add(event));
            assertEquals("src/main/resources/assets/destiny_music/sounds/" + event.substring("destiny_music:".length()) + ".ogg", path);
            assertEquals(track.get("sha256").getAsString(), sha(Path.of(path)), path);
            assertEquals(track.get("bytes").getAsLong(), Files.size(Path.of(path)));
            assertTrue(expected.add(path), "W262 music does not replace inherited audio");
        }
        assertEquals(Set.of("destiny_music:tower_80d73421", "destiny_music:tower_80d7341d",
                "destiny_music:tower_80d73424", "destiny_music:tower_80d73419",
                "destiny_music:crucible_intro", "destiny_music:crucible_result"), musicEvents);
        assertAudioInventory(expected, actual);
        assertSixOggBytes(w98);
    }

    @Test void closedAudioInventoryRejectsExtraOggOutsideSoundDirectoriesAndMissingClips() {
        var expected=Set.of("src/main/resources/assets/destiny/sounds/w98/the_recluse/fire_2.ogg");
        for (String extra : Set.of("src/main/resources/assets/destiny/textures/unreviewed.ogg",
                "src/main/resources/assets/other/models/unreviewed.OGG",
                "src/main/resources/assets/destiny/sounds/unreviewed.bin")) {
            assertTrue(runtimeAudioPath(extra));
            var actual=new HashSet<>(expected); actual.add(extra);
            assertThrows(AssertionError.class, () -> assertAudioInventory(expected, actual), extra);
        }
        assertThrows(AssertionError.class, () -> assertAudioInventory(expected, Set.of()));
    }

    @Test void sixVariantOggPayloadsRemainPinnedEvenIfAnUnrelatedArtInventoryContractFails() throws Exception {
        assertSixOggBytes(sounds().stream().map(sound -> "src/main/resources/assets/destiny/sounds/"
                + sound.substring(8) + ".ogg").collect(java.util.stream.Collectors.toSet()));
    }

    private static void assertSixOggBytes(Set<String> added) throws Exception {
        assertEquals(6, added.size());
        var manifest = json(ART.resolve("implementation.json"));
        int total = 0;
        for (String path : added) {
            assertEquals(manifest.getAsJsonObject("outputs").get(path).getAsString(), sha(Path.of(path)));
            byte[] bytes = Files.readAllBytes(Path.of(path)); total += bytes.length;
            assertEquals("OggS", new String(bytes, 0, 4, StandardCharsets.US_ASCII));
            int index = -1;
            for (int i = 0; i < Math.min(200, bytes.length - 16); i++)
                if (bytes[i] == 1 && new String(bytes, i + 1, 6, StandardCharsets.US_ASCII).equals("vorbis")) { index = i; break; }
            assertTrue(index >= 0, path);
            assertEquals(1, bytes[index + 11]);
            assertEquals(32000, ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).getInt(index + 12));
        }
        assertTrue(total < 512 * 1024, "Bounded six-clip addition, no unreviewed archive bulk");
    }

    @Test void pinsKeepNamedSameFolderFireActionsWithFiniteOutputMeasurementsAndNoInventedDragonflyAttribution() throws Exception {
        var manifest = json(ART.resolve("implementation.json"));
        assertEquals("W98", manifest.get("stage").getAsString()); assertFalse(manifest.get("wholeGoalAchieved").getAsBoolean());
        assertEquals(sha(ART.resolve("source-pins.json")), manifest.get("sourcePinsSha256").getAsString());
        assertEquals(sha(ART.resolve("folder-discovery.json")), manifest.get("folderDiscoverySha256").getAsString());
        assertEquals(sha(Path.of("scripts/audio/build_fire_variants_w98.py")), manifest.get("generatorSha256").getAsString());
        assertEquals(sha(Path.of("scripts/audio/import_sounds_w33.py")), manifest.get("helperSha256").getAsString());
        var pins = JsonParser.parseString(Files.readString(ART.resolve("source-pins.json"))).getAsJsonArray();
        assertEquals(9, pins.size()); var identities = new HashSet<String>(); var files = new HashSet<String>();
        for (var value : pins) {
            var p = value.getAsJsonObject(); String id = p.get("id").getAsString(); int variant = p.get("variant").getAsInt();
            assertTrue(FAMILIES.containsKey(id)); assertTrue(variant >= 1 && variant <= 3);
            assertTrue(identities.add(id + ":" + variant)); assertTrue(files.add(p.get("driveId").getAsString()));
            assertEquals(FAMILIES.get(id), p.get("family").getAsString()); assertEquals(FOLDERS.get(id), p.get("folderId").getAsString());
            assertEquals("Fire_" + variant + (id.equals("the_recluse") ? ".mp3" : ".wav"), p.get("originalName").getAsString());
            assertEquals("weapon." + id + ".fire", p.get("event").getAsString());
            assertEquals("https://drive.google.com/uc?export=download&id=" + p.get("driveId").getAsString(), p.get("sourceUrl").getAsString());
            assertTrue(p.get("sourceSha256").getAsString().matches("[a-f0-9]{64}"));
            assertEquals(variant == 1 ? "retained_original_ogg" : "new_variant", p.get("action").getAsString());
        }
        var records = manifest.getAsJsonArray("records"); assertEquals(9, records.size());
        for (var value : records) {
            var row = value.getAsJsonObject(); var output = row.getAsJsonObject("output");
            assertEquals(1, output.get("channels").getAsInt()); assertEquals(32000, output.get("sample_rate_hz").getAsInt());
            assertEquals(0, output.get("clipped_samples").getAsInt());
            assertTrue(Double.isFinite(output.get("sample_peak_dbfs").getAsDouble()));
            assertTrue(output.get("sample_peak_dbfs").getAsDouble() <= -1);
            assertTrue(output.get("duration_seconds").getAsDouble() > 0 && output.get("duration_seconds").getAsDouble() <= 3.001);
        }
        assertTrue(manifest.getAsJsonArray("limitations").toString().contains("not independent acoustic identification"));
        assertTrue(manifest.getAsJsonArray("limitations").toString().contains("Dragonfly/Firefly surrogate"));
    }

    @Test void exactRoutingDoesNotTransferVariantsToOtherFramesOrChangeReloadMappings() throws Exception {
        var now = json(SOUNDS); var before = json(Path.of("docs/qa/2026-10-25/w98/before/src/main/resources/assets/destiny/sounds.json"));
        var named = namedW102Definitions(now);
        for (var entry : WeaponCatalog.all()) {
            String key = DestinySounds.weaponKey(entry, "fire");
            if (FAMILIES.containsKey(entry.id())) assertEquals("weapon." + entry.id() + ".fire", key);
            else if (namedW102Events().contains(key)) assertEquals(named.get(key), now.get(key), entry.id());
            else assertEquals(before.get(key), now.get(key), entry.id());
            String reload = DestinySounds.weaponKey(entry, "reload");
            if (namedW102Events().contains(reload)) assertEquals(named.get(reload), now.get(reload));
            else assertEquals(before.get(reload), now.get(reload));
        }
        assertEquals("weapon.hand_cannon.fire", DestinySounds.weaponKey(WeaponCatalog.find("duke_mk_44").orElseThrow(), "fire"));
        assertEquals("weapon.hand_cannon.fire", DestinySounds.weaponKey(WeaponCatalog.find("austringer").orElseThrow(), "fire"));
        for (String family : FAMILIES.values()) assertEquals(before.get("weapon." + family + ".fire"), now.get("weapon." + family + ".fire"));
        for (var clip : ReloadAudioProfile.all()) {
            if (namedW102Events().contains(clip.event())) assertEquals(named.get(clip.event()), now.get(clip.event()));
            else assertEquals(before.get(clip.event()), now.get(clip.event()));
        }
    }

    @Test void auditionWavsAreOrderedPackDerivedPcmWithSilenceAndNeverRuntimeReferences() throws Exception {
        var manifest = json(ART.resolve("implementation.json")); var active = json(SOUNDS).toString();
        for (var value : manifest.getAsJsonArray("auditions")) {
            var row = value.getAsJsonObject(); String id = row.get("id").getAsString();
            var p = ART.resolve("audition/" + id + "_fire_123.wav"); byte[] bytes = Files.readAllBytes(p);
            assertEquals(manifest.getAsJsonObject("outputs").get(p.toString()).getAsString(), sha(p));
            assertEquals("RIFF", new String(bytes, 0, 4, StandardCharsets.US_ASCII));
            assertEquals("WAVE", new String(bytes, 8, 4, StandardCharsets.US_ASCII));
            var b = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);
            assertEquals(1, b.getShort(20)); assertEquals(1, b.getShort(22)); assertEquals(32000, b.getInt(24)); assertEquals(16, b.getShort(34));
            long offset = 0; int expectedVariant = 1;
            for (var position : row.getAsJsonArray("positions")) {
                var part = position.getAsJsonObject(); assertEquals(expectedVariant++, part.get("variant").getAsInt());
                assertEquals(offset, part.get("startSample").getAsLong()); offset += part.get("samples").getAsLong() + 32000;
            }
            assertEquals(4, expectedVariant); assertEquals(offset * 2, b.getInt(40)); assertEquals(44 + offset * 2, bytes.length);
            assertFalse(active.contains(p.getFileName().toString()));
        }
    }
}
