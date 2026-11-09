package kim.biryeong.destiny.compat.pack;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
import static org.junit.jupiter.api.Assertions.*;

class ActivityPackArchiveTest {
    @TempDir Path directory;
    private static final byte[] META = "{\"pack\":{\"min_format\":[97,1],\"max_format\":97,\"description\":\"base\"}}".getBytes(StandardCharsets.UTF_8);
    private Path base() throws Exception {
        Path base = directory.resolve("base.zip");
        try (var zip = new ZipOutputStream(Files.newOutputStream(base))) {
            zip.putNextEntry(new ZipEntry("pack.mcmeta")); zip.write(META); zip.closeEntry();
        }
        return base;
    }
    private ActivityPackArchive capture() {
        var capture = new ActivityPackArchive(ActivityPackCatalog.load());
        capture.convert("assets/destiny_devils/sounds/voice/a.ogg", new byte[]{1, 2, 3});
        capture.convert("assets/destiny_exodus/sounds/voice/b.ogg", new byte[]{4, 5, 6});
        return capture;
    }
    @Test void exclusiveMediaLeavesTheBaseWhileSharedModelsAndBriefingMusicStay() throws Exception {
        var capture = capture();
        assertFalse(capture.selects("assets/bettermodel/items/c/dl_servitor_body.json"));
        assertFalse(capture.selects("assets/destiny/textures/item/hud/fireteam/banner_devils_lair.png"));
        assertFalse(capture.selects("assets/destiny_music/sounds/devils_descent_80d715da.ogg"));
        assertTrue(capture.selects("assets/destiny_music/sounds/devils/123.ogg"));
        assertNull(capture.convert("assets/destiny_music/sounds/devils/123.ogg", new byte[]{9, 8, 7}));
        byte[] remaining = capture.convert("assets/destiny_music/sounds.json", """
            {"tower_a":{"sounds":["destiny_music:tower_a"]},
             "devils_descent_80d715da":{"sounds":["destiny_music:devils_descent_80d715da"]},
             "devils_segment_123":{"sounds":[{"name":"destiny_music:devils/123","stream":true}]}}
            """.getBytes(StandardCharsets.UTF_8));
        var baseSounds = JsonParser.parseString(new String(remaining, StandardCharsets.UTF_8)).getAsJsonObject();
        assertTrue(baseSounds.has("tower_a")); assertTrue(baseSounds.has("devils_descent_80d715da"));
        assertFalse(baseSounds.has("devils_segment_123"));
        var result = capture.finish(base(), "base-hash", directory.resolve("packs"));
        try (var devils = new ZipFile(result.get("devils_lair").path().toFile());
             var exodus = new ZipFile(result.get("exodus_crash").path().toFile())) {
            assertArrayEquals(new byte[]{1,2,3}, devils.getInputStream(devils.getEntry("assets/destiny_devils/sounds/voice/a.ogg")).readAllBytes());
            assertNull(exodus.getEntry("assets/destiny_devils/sounds/voice/a.ogg"));
            assertArrayEquals(new byte[]{4,5,6}, exodus.getInputStream(exodus.getEntry("assets/destiny_exodus/sounds/voice/b.ogg")).readAllBytes());
            var sounds = JsonParser.parseString(new String(devils.getInputStream(devils.getEntry("assets/destiny_music/sounds.json")).readAllBytes(), StandardCharsets.UTF_8)).getAsJsonObject();
            assertEquals(Set.of("devils_segment_123"), sounds.keySet());
            var metadata = JsonParser.parseString(new String(exodus.getInputStream(exodus.getEntry("pack.mcmeta")).readAllBytes(), StandardCharsets.UTF_8)).getAsJsonObject();
            assertEquals(97, metadata.getAsJsonObject("pack").get("max_format").getAsInt());
        }
    }
    @Test void startupReuseRejectsMismatchedMissingAndCorruptActivityPacks() throws Exception {
        Path packs = directory.resolve("packs");
        var result = capture().finish(base(), "base-hash", packs);
        assertEquals(result, ActivityPackArchive.read(packs, "base-hash", ActivityPackCatalog.load()));
        assertThrows(java.io.IOException.class, () -> ActivityPackArchive.read(packs, "other-base", ActivityPackCatalog.load()));
        Path zip = result.get("exodus_crash").path();
        byte[] original = Files.readAllBytes(zip); byte[] corrupt = original.clone(); corrupt[20] ^= 1;
        Files.write(zip, corrupt);
        assertThrows(java.io.IOException.class, () -> ActivityPackArchive.read(packs, "base-hash", ActivityPackCatalog.load()));
        Files.delete(zip);
        assertThrows(java.io.IOException.class, () -> ActivityPackArchive.read(packs, "base-hash", ActivityPackCatalog.load()));
    }
    @Test void unchangedMediaProducesIdenticalArchivesAndChangedMediaGetsANewHash() throws Exception {
        Path base = base();
        var first = capture().finish(base, "base-hash", directory.resolve("one"));
        var second = capture().finish(base, "base-hash", directory.resolve("two"));
        assertEquals(first.get("devils_lair").sha1(), second.get("devils_lair").sha1());
        var changed = capture(); changed.convert("assets/destiny_devils/sounds/voice/a.ogg", new byte[]{1, 2, 9});
        var third = changed.finish(base, "base-hash", directory.resolve("three"));
        assertNotEquals(first.get("devils_lair").sha1(), third.get("devils_lair").sha1());
        assertEquals(first.get("exodus_crash").sha1(), third.get("exodus_crash").sha1());
    }
    @Test void exclusiveContentAndOwnershipAreBoundToTheBaseEvenWhenVisibleBaseAssetsAreUnchanged() {
        var catalog = ActivityPackCatalog.load();
        var files = new LinkedHashMap<String, byte[]>();
        files.put("assets/destiny_exodus/sounds/voice/b.ogg", new byte[]{1,2,3});
        files.put("assets/destiny/shared.json", new byte[]{4});
        byte[] first = ActivityPackArchive.inputFingerprint(catalog, files);
        files.put("assets/destiny/shared.json", new byte[]{9});
        assertArrayEquals(first, ActivityPackArchive.inputFingerprint(catalog, files));
        files.put("assets/destiny_exodus/sounds/voice/b.ogg", new byte[]{1,2,4});
        assertFalse(Arrays.equals(first, ActivityPackArchive.inputFingerprint(catalog, files)));
        var changedCatalog = ActivityPackCatalog.parse(catalog.definition().replace("엑소더스의 추락", "엑소더스 새 버전"));
        assertFalse(Arrays.equals(ActivityPackArchive.inputFingerprint(catalog, files), ActivityPackArchive.inputFingerprint(changedCatalog, files)));
    }
    @Test void preMigrationBaseCachesAndDifferentOwnershipCannotRestoreAnActivitySet() throws Exception {
        var catalog = ActivityPackCatalog.load();
        assertThrows(java.io.IOException.class, () -> ActivityPackArchive.validateBase(base(), catalog));
        var inputs = Map.of("assets/destiny_exodus/sounds/voice/a.ogg", new byte[]{1,2,3});
        Path current = directory.resolve("current-base.zip");
        try (var zip = new ZipOutputStream(Files.newOutputStream(current))) {
            zip.putNextEntry(new ZipEntry("destiny/activity-pack-inputs.json"));
            zip.write(ActivityPackArchive.inputFingerprint(catalog, inputs)); zip.closeEntry();
        }
        ActivityPackArchive.validateBase(current, catalog);
        var changed = ActivityPackCatalog.parse(catalog.definition().replace("엑소더스의 추락", "다른 버전"));
        assertThrows(java.io.IOException.class, () -> ActivityPackArchive.validateBase(current, changed));
    }
}
