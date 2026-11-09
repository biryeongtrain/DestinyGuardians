package kim.biryeong.destiny.compat.pack;

import com.google.gson.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.zip.*;

/** Captures the final converted bytes, without changing source assets or repacking shared assets. */
public final class ActivityPackArchive {
    private static final Gson GSON = new Gson();
    public record Archive(String id, String sha1, long size, Path path) { }
    private record Entry(String id, String sha1, long size, String file) { }
    private record Manifest(int schema, String baseSha1, List<Entry> packs) { }
    private final ActivityPackCatalog catalog;
    private final Map<String, Map<String, byte[]>> packs = new ConcurrentHashMap<>();
    public ActivityPackArchive(ActivityPackCatalog catalog) {
        this.catalog = catalog;
        for (var activity : catalog.activities()) packs.put(activity.id(), new ConcurrentHashMap<>());
    }
    boolean selects(String path) { return catalog.selects(path); }
    /** Bind exclusive inputs and ownership to the base hash, even when the base's visible assets did not change. */
    static byte[] inputFingerprint(ActivityPackCatalog catalog, Map<String, byte[]> files) {
        var hashes = new TreeMap<String, String>();
        try {
            var digest = MessageDigest.getInstance("SHA-256");
            for (var entry : files.entrySet()) if (catalog.selects(entry.getKey()))
                hashes.put(entry.getKey(), HexFormat.of().formatHex(digest.digest(entry.getValue())));
        } catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
        var root = new LinkedHashMap<String, Object>();
        root.put("schema", 1); root.put("catalog", catalog.definition()); root.put("assets", hashes);
        return GSON.toJson(root).getBytes(StandardCharsets.UTF_8);
    }
    static void validateBase(Path baseZip, ActivityPackCatalog catalog) throws IOException {
        try (var zip = new ZipFile(baseZip.toFile())) {
            var marker = zip.getEntry("destiny/activity-pack-inputs.json");
            if (marker == null) throw new IOException("Cached base pack predates activity input fingerprints");
            var root = JsonParser.parseString(new String(zip.getInputStream(marker).readAllBytes(), StandardCharsets.UTF_8)).getAsJsonObject();
            if (root.get("schema").getAsInt() != 1 || !root.get("catalog").getAsString().equals(catalog.definition())
                    || root.getAsJsonObject("assets").isEmpty()) throw new IOException("Cached activity ownership does not match this catalog");
        } catch (RuntimeException e) { throw new IOException("Invalid base activity fingerprint", e); }
    }
    /** Null removes an exclusive resource from the base ZIP. Mixed sound registries are split by event. */
    byte[] convert(String path, byte[] bytes) {
        String owner = catalog.owner(path);
        if (owner != null) { packs.get(owner).put(path, bytes); return null; }
        var root = JsonParser.parseString(new String(bytes, StandardCharsets.UTF_8)).getAsJsonObject();
        var rest = root.deepCopy();
        for (var activity : catalog.activities()) {
            var prefixes = activity.soundEvents().get(path);
            if (prefixes == null) continue;
            var selected = new JsonObject();
            for (var event : root.entrySet()) if (prefixes.stream().anyMatch(event.getKey()::startsWith)) {
                if (!rest.has(event.getKey())) throw new IllegalStateException("Ambiguous sound event: " + event.getKey());
                selected.add(event.getKey(), event.getValue()); rest.remove(event.getKey());
            }
            if (!selected.isEmpty()) packs.get(activity.id()).put(path, GSON.toJson(selected).getBytes(StandardCharsets.UTF_8));
        }
        return GSON.toJson(rest).getBytes(StandardCharsets.UTF_8);
    }
    public Map<String, Archive> finish(Path baseZip, String baseSha1, Path directory) throws IOException {
        Files.createDirectories(directory);
        byte[] metadata;
        try (var zip = new ZipFile(baseZip.toFile())) {
            var entry = zip.getEntry("pack.mcmeta");
            if (entry == null) throw new IOException("Base pack has no compatibility metadata");
            metadata = zip.getInputStream(entry).readAllBytes();
        }
        var archives = new LinkedHashMap<String, Archive>();
        for (var activity : catalog.activities().stream().sorted(Comparator.comparing(ActivityPackCatalog.Activity::id)).toList()) {
            var assets = packs.get(activity.id());
            if (assets.isEmpty()) throw new IOException("Activity pack has no assets: " + activity.id());
            var meta = JsonParser.parseString(new String(metadata, StandardCharsets.UTF_8)).getAsJsonObject();
            meta.getAsJsonObject("pack").addProperty("description", "Destiny Guardians · " + activity.name());
            assets.put("pack.mcmeta", GSON.toJson(meta).getBytes(StandardCharsets.UTF_8));
            Path temporary = Files.createTempFile(directory, activity.id() + "-", ".tmp");
            try {
                try (var output = new ZipOutputStream(Files.newOutputStream(temporary))) {
                    for (String path : new TreeSet<>(assets.keySet())) {
                        var entry = new ZipEntry(path); entry.setTime(0);
                        output.putNextEntry(entry); output.write(assets.get(path)); output.closeEntry();
                    }
                }
                String hash = sha1(temporary);
                Path path = directory.resolve(activity.id() + "-" + hash + ".zip");
                atomicMove(temporary, path);
                archives.put(activity.id(), new Archive(activity.id(), hash, Files.size(path), path));
            } finally { Files.deleteIfExists(temporary); }
        }
        var manifest = new Manifest(1, baseSha1, archives.values().stream()
                .map(a -> new Entry(a.id(), a.sha1(), a.size(), a.path().getFileName().toString())).toList());
        Path temporary = Files.createTempFile(directory, "manifest-", ".tmp");
        try { Files.writeString(temporary, GSON.toJson(manifest)); atomicMove(temporary, directory.resolve("manifest.json")); }
        finally { Files.deleteIfExists(temporary); }
        packs.values().forEach(Map::clear);
        return Map.copyOf(archives);
    }
    public static Map<String, Archive> read(Path directory, String baseSha1, ActivityPackCatalog catalog) throws IOException {
        try {
            var manifest = GSON.fromJson(Files.readString(directory.resolve("manifest.json")), Manifest.class);
            if (manifest == null || manifest.schema() != 1 || !Objects.equals(baseSha1, manifest.baseSha1()))
                throw new IOException("Activity packs do not match this base pack");
            var result = new LinkedHashMap<String, Archive>();
            for (var entry : manifest.packs()) {
                catalog.activity(entry.id());
                if (!entry.sha1().matches("[a-f0-9]{40}") || !entry.file().equals(entry.id() + "-" + entry.sha1() + ".zip"))
                    throw new IOException("Invalid activity archive path");
                Path path = directory.resolve(entry.file());
                if (Files.size(path) != entry.size() || !sha1(path).equals(entry.sha1())) throw new IOException("Invalid activity ZIP: " + entry.id());
                if (result.putIfAbsent(entry.id(), new Archive(entry.id(), entry.sha1(), entry.size(), path)) != null)
                    throw new IOException("Duplicate activity archive");
            }
            if (!result.keySet().equals(catalog.activities().stream().map(ActivityPackCatalog.Activity::id).collect(java.util.stream.Collectors.toSet())))
                throw new IOException("Incomplete activity archive set");
            return Map.copyOf(result);
        } catch (RuntimeException e) { throw new IOException("Invalid activity pack manifest", e); }
    }
    static String sha1(Path path) throws IOException {
        try (var input = Files.newInputStream(path)) {
            var digest = MessageDigest.getInstance("SHA-1");
            byte[] buffer = new byte[65536]; int count;
            while ((count = input.read(buffer)) >= 0) digest.update(buffer, 0, count);
            return HexFormat.of().formatHex(digest.digest());
        } catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
    }
    private static void atomicMove(Path from, Path to) throws IOException {
        Files.move(from, to, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
    }
}
