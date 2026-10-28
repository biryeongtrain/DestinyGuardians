package kim.biryeong.destiny.weapon;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

class PinnedProfileSourcesW234Test {
    @TempDir Path root;
    private static final byte[] ORIGINAL = "complete original source including unrelated records\n".getBytes(StandardCharsets.UTF_8);

    private static String sha(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }

    private static JsonObject pin(String path, byte[] bytes) throws Exception {
        var pin = new JsonObject();
        pin.addProperty("path", path);
        pin.addProperty("sha256", sha(bytes));
        pin.addProperty("bytes", bytes.length);
        return pin;
    }

    private static JsonObject catalog(JsonObject source) {
        var catalog = new JsonObject();
        catalog.addProperty("schemaVersion", 1);
        var sources = new JsonArray(); sources.add(source);
        catalog.add("sources", sources);
        return catalog;
    }

    private JsonObject archived(byte[] payload) throws Exception {
        var source = pin("/absent-w234-original/source.json", ORIGINAL);
        source.add("repositoryPaths", new JsonArray());
        source.addProperty("archiveEntry", "original.json");
        Path archive = root.resolve("original.zip");
        try (var zip = new ZipOutputStream(Files.newOutputStream(archive))) {
            zip.putNextEntry(new ZipEntry("original.json"));
            zip.write(payload); zip.closeEntry();
        }
        var catalog = catalog(source);
        catalog.add("archive", pin("original.zip", Files.readAllBytes(archive)));
        return catalog;
    }

    @Test void missingHistoricalAbsolutePathStillHashesEveryOriginalByteFromZip() throws Exception {
        var catalog = archived(ORIGINAL);
        var source = catalog.getAsJsonArray("sources").get(0).getAsJsonObject();
        var result = new PinnedProfileSourcesW234(root, null, catalog).verifyPin(source);
        assertEquals(sha(ORIGINAL), result.sha256());
        assertEquals(ORIGINAL.length, result.bytes());
        assertTrue(result.origin().endsWith("original.zip!/original.json"));
    }

    @Test void sameLengthChangedOriginalIsRejectedEvenWithValidZipHash() throws Exception {
        byte[] mutated = ORIGINAL.clone(); mutated[0] ^= 1;
        var catalog = archived(mutated);
        var source = catalog.getAsJsonArray("sources").get(0).getAsJsonObject();
        var failure = assertThrows(IOException.class,
            () -> new PinnedProfileSourcesW234(root, null, catalog).verifyPin(source));
        assertTrue(failure.getMessage().contains("SHA-256/size mismatch"));
    }

    @Test void truncatedOrOverlongOriginalsAndWrongDigestFailClosed() throws Exception {
        for (long length : new long[]{ORIGINAL.length - 1, ORIGINAL.length + 1})
            assertThrows(IOException.class, () -> PinnedProfileSourcesW234.verifyStream(
                new ByteArrayInputStream(ORIGINAL), sha(ORIGINAL), length, "test"));
        assertThrows(IOException.class, () -> PinnedProfileSourcesW234.verifyStream(
            new ByteArrayInputStream(ORIGINAL), "0".repeat(64), ORIGINAL.length, "test"));
    }

    @Test void absentArchiveMissingEntryAndArchiveCorruptionAreRejected() throws Exception {
        var catalog = archived(ORIGINAL);
        var source = catalog.getAsJsonArray("sources").get(0).getAsJsonObject();
        var resolver = new PinnedProfileSourcesW234(root, null, catalog);
        source.addProperty("archiveEntry", "absent.json");
        assertThrows(IOException.class, () -> resolver.verifyPin(source));
        source.addProperty("archiveEntry", "original.json");
        byte[] changed = Files.readAllBytes(root.resolve("original.zip")); changed[0] ^= 1;
        Files.write(root.resolve("original.zip"), changed);
        assertThrows(IOException.class, () -> resolver.verifyPin(source));
        Files.delete(root.resolve("original.zip"));
        assertThrows(IOException.class, () -> resolver.verifyPin(source));
    }

    @Test void originalPinCannotBeReplacedByExtractHashOrUnknownAbsolutePath() throws Exception {
        var catalog = archived(ORIGINAL);
        var source = catalog.getAsJsonArray("sources").get(0).getAsJsonObject();
        var resolver = new PinnedProfileSourcesW234(root, null, catalog);
        for (String field : List.of("sha256", "bytes", "path")) {
            var forged = source.deepCopy();
            if (field.equals("sha256")) forged.addProperty(field, sha("extract".getBytes(StandardCharsets.UTF_8)));
            else if (field.equals("bytes")) forged.addProperty(field, 7);
            else forged.addProperty(field, "/unknown-w234-original.json");
            assertThrows(IOException.class, () -> resolver.verifyPin(forged), field);
        }
        catalog.getAsJsonArray("sources").add(source.deepCopy());
        assertThrows(IOException.class, () -> resolver.verifyPin(source));
    }

    @Test void verifiedCacheIsSupportedAndCorruptCacheDoesNotSilentlyFallBack() throws Exception {
        var catalog = archived(ORIGINAL);
        var source = catalog.getAsJsonArray("sources").get(0).getAsJsonObject();
        Path cache = Files.createDirectory(root.resolve("cache"));
        Path cached = cache.resolve(sha(ORIGINAL) + ".json");
        Files.write(cached, ORIGINAL);
        var resolver = new PinnedProfileSourcesW234(root, cache, catalog);
        assertEquals(cached.toString(), resolver.verifyPin(source).origin());
        Files.writeString(cached, "corrupted cache");
        assertThrows(IOException.class, () -> resolver.verifyPin(source));
    }

    @Test void repositoryPinsDoNotFallBackToUnrelatedEvidenceAndPathsCannotEscapeRoot() throws Exception {
        var catalog = archived(ORIGINAL);
        var resolver = new PinnedProfileSourcesW234(root, null, catalog);
        Files.write(root.resolve("local.json"), ORIGINAL);
        assertEquals(sha(ORIGINAL), resolver.verifyPin(pin("local.json", ORIGINAL)).sha256());
        Files.writeString(root.resolve("local.json"), "bad");
        assertThrows(IOException.class, () -> resolver.verifyPin(pin("local.json", ORIGINAL)));
        assertThrows(IOException.class, () -> resolver.verifyPin(pin("missing.json", ORIGINAL)));
        assertThrows(IOException.class, () -> resolver.verifyPin(pin("../escape.json", ORIGINAL)));
    }

    @Test void allFourRealOriginalsResolveOfflineWithoutHistoricalTmpOrW83Files() throws Exception {
        Path repository = Path.of("").toAbsolutePath();
        var catalog = JsonParser.parseString(Files.readString(repository.resolve(PinnedProfileSourcesW234.CATALOG))).getAsJsonObject();
        Path archive = root.resolve(catalog.getAsJsonObject("archive").get("path").getAsString());
        Files.createDirectories(archive.getParent());
        Files.copy(repository.resolve(catalog.getAsJsonObject("archive").get("path").getAsString()), archive);
        var resolver = new PinnedProfileSourcesW234(root, null, catalog);
        assertFalse(Files.exists(root.resolve("art/weapons/w83")));
        assertEquals(4, catalog.getAsJsonArray("sources").size());
        for (var element : catalog.getAsJsonArray("sources")) {
            var source = element.getAsJsonObject();
            var result = resolver.verifyPin(source);
            assertEquals(source.get("sha256").getAsString(), result.sha256());
            assertEquals(source.get("bytes").getAsLong(), result.bytes());
            assertTrue(result.origin().startsWith(root.toString()), result.origin());
            assertTrue(result.origin().contains(".zip!/"), result.origin());
            assertNotEquals(source.get("path").getAsString(), result.origin());
        }
    }
}
