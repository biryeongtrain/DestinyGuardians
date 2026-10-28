package kim.biryeong.destiny.weapon;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.zip.ZipFile;

/** Test-only resolution of complete original sources; never downloads or writes files. */
final class PinnedProfileSourcesW234 {
    static final String CATALOG = "art/weapons/w234/pinned-sources.json";
    private final Path root;
    private final Path cache;
    private final JsonObject catalog;

    record VerifiedSource(long bytes, String sha256, String origin) {}

    PinnedProfileSourcesW234(Path root, Path cache, JsonObject catalog) {
        this.root = root.toAbsolutePath().normalize();
        this.cache = cache;
        this.catalog = catalog;
        if (catalog.get("schemaVersion").getAsInt() != 1)
            throw new IllegalArgumentException("Unsupported W234 source catalog schema");
    }

    static VerifiedSource verify(JsonObject pin) throws IOException {
        Path root = Path.of("").toAbsolutePath();
        String configured = System.getProperty("destiny.profile.sources.cache");
        if (configured == null || configured.isBlank()) configured = System.getenv("DESTINY_PROFILE_SOURCE_CACHE");
        Path cache = configured == null || configured.isBlank() ? null : Path.of(configured);
        var catalog = JsonParser.parseString(Files.readString(root.resolve(CATALOG))).getAsJsonObject();
        return new PinnedProfileSourcesW234(root, cache, catalog).verifyPin(pin);
    }

    VerifiedSource verifyPin(JsonObject pin) throws IOException {
        String path = pin.get("path").getAsString();
        String expected = pin.get("sha256").getAsString();
        long length = pin.get("bytes").getAsLong();
        if (!expected.matches("[0-9a-f]{64}") || length < 0)
            throw new IOException("Invalid full-source pin: " + path);
        if (!Path.of(path).isAbsolute()) return verifyFile(repositoryPath(path), expected, length);
        JsonObject source = null;
        for (var element : catalog.getAsJsonArray("sources")) {
            var candidate = element.getAsJsonObject();
            if (candidate.get("path").getAsString().equals(path)) {
                if (source != null) throw new IOException("Duplicate W234 source: " + path);
                source = candidate;
            }
        }
        if (source == null) throw new IOException("No W234 full-source mapping: " + path);
        if (!expected.equals(source.get("sha256").getAsString()) || length != source.get("bytes").getAsLong())
            throw new IOException("Historical source pin disagrees with W234 catalog: " + path);
        if (cache != null) {
            Path cached = cache.resolve(expected + ".json");
            if (Files.exists(cached)) return verifyFile(cached, expected, length);
        }
        for (var element : source.getAsJsonArray("repositoryPaths")) {
            Path candidate = repositoryPath(element.getAsString());
            if (Files.exists(candidate)) return verifyFile(candidate, expected, length);
        }
        if (source.has("archiveEntry")) {
            var fixture = catalog.getAsJsonObject("archive");
            Path archive = repositoryPath(fixture.get("path").getAsString());
            verifyFile(archive, fixture.get("sha256").getAsString(), fixture.get("bytes").getAsLong());
            try (var zip = new ZipFile(archive.toFile())) {
                var entry = zip.getEntry(source.get("archiveEntry").getAsString());
                if (entry == null) throw new IOException("Missing complete original ZIP entry: " + path);
                if (entry.getSize() != length) throw new IOException("Original ZIP entry size disagrees with pin: " + path);
                try (var input = zip.getInputStream(entry)) {
                    return verifyStream(input, expected, length, archive + "!/" + entry.getName());
                }
            }
        }
        throw new IOException("Missing complete pinned source: " + path + "; expected SHA-256 " + expected
            + ". Restore the committed source fixture or run rtk proxy python3 scripts/qa/verify_profile_sources_w234.py --populate-cache"
            + " --cache-dir <cache>, then set DESTINY_PROFILE_SOURCE_CACHE to that directory.");
    }

    private Path repositoryPath(String name) throws IOException {
        Path result = root.resolve(name).normalize();
        if (Path.of(name).isAbsolute() || !result.startsWith(root))
            throw new IOException("Source path escapes repository: " + name);
        return result;
    }

    private static VerifiedSource verifyFile(Path path, String expected, long length) throws IOException {
        try (var input = Files.newInputStream(path)) {
            return verifyStream(input, expected, length, path.toString());
        }
    }

    static VerifiedSource verifyStream(InputStream input, String expected, long length, String origin) throws IOException {
        final MessageDigest digest;
        try { digest = MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException e) { throw new AssertionError(e); }
        long count = 0;
        byte[] buffer = new byte[64 * 1024];
        int read;
        while ((read = input.read(buffer)) != -1) {
            count += read;
            if (count > length) throw new IOException("Full-source byte count exceeds pin: " + origin);
            digest.update(buffer, 0, read);
        }
        String actual = HexFormat.of().formatHex(digest.digest());
        if (count != length || !actual.equals(expected))
            throw new IOException("Full-source SHA-256/size mismatch: " + origin + "; got " + actual + " / " + count
                + ", expected " + expected + " / " + length);
        return new VerifiedSource(count, actual, origin);
    }
}
