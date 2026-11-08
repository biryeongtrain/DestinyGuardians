package kim.biryeong.destiny.compat.pack;

import com.google.gson.Gson;
import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.util.zip.ZipFile;

/** Validated on-disk outputs. Manifest is published last; interrupted writes can only cause a cache miss. */
final class PackCacheStore {
    private static final Gson JSON = new Gson();
    record Manifest(int schema, String inputs, String zipSha1, String zipSha256, String profilesSha256, Map<String,String> groups) {}
    record Key(String value, Map<String,String> groups) {}
    record Hit(Path archive, Path profiles, String sha1) {}
    private final Path directory;
    PackCacheStore(Path directory) { this.directory = directory; }

    synchronized Optional<Hit> read(String inputs) throws IOException {
        Path manifest = directory.resolve("manifest.json");
        if (!Files.isRegularFile(manifest)) return Optional.empty();
        Manifest m;
        try { m = JSON.fromJson(Files.readString(manifest), Manifest.class); }
        catch (RuntimeException e) { return Optional.empty(); }
        if (m == null || m.schema != 1 || !inputs.equals(m.inputs)) return Optional.empty();
        Path zip = directory.resolve("pack.zip"), profiles = directory.resolve("profiles.bin.gz");
        if (!Files.isRegularFile(zip) || !Files.isRegularFile(profiles)
                || !digest(zip, "SHA-256").equals(m.zipSha256)
                || !digest(zip, "SHA-1").equals(m.zipSha1)
                || !digest(profiles, "SHA-256").equals(m.profilesSha256)) return Optional.empty();
        try (var archive = new ZipFile(zip.toFile())) {
            if (archive.getEntry("pack.mcmeta") == null) return Optional.empty();
        }
        return Optional.of(new Hit(zip, profiles, m.zipSha1));
    }

    synchronized void write(String inputs, Path archive, Path profiles, String expectedSha1) throws IOException {
        write(inputs, Map.of(), archive, profiles, expectedSha1);
    }
    /** Names of the input groups whose digest differs from the stored manifest (or "no previous cache"). */
    synchronized List<String> changedGroups(Map<String,String> now) {
        try {
            Path manifest = directory.resolve("manifest.json");
            if (!Files.isRegularFile(manifest)) return List.of("no previous cache");
            var m = JSON.fromJson(Files.readString(manifest), Manifest.class);
            if (m == null || m.groups == null || m.groups.isEmpty()) return List.of("previous cache has no group record");
            var changed = new TreeSet<String>();
            for (var e : now.entrySet()) if (!e.getValue().equals(m.groups.get(e.getKey()))) changed.add(e.getKey());
            for (var k : m.groups.keySet()) if (!now.containsKey(k)) changed.add(k);
            return List.copyOf(changed);
        } catch (IOException | RuntimeException e) { return List.of("unreadable manifest"); }
    }
    synchronized void write(String inputs, Map<String,String> groups, Path archive, Path profiles, String expectedSha1) throws IOException {
        Files.createDirectories(directory);
        String sha1 = digest(archive, "SHA-1");
        if (!sha1.equals(expectedSha1)) throw new IOException("Generated ZIP hash changed before cache publication");
        var m = new Manifest(1, inputs, sha1, digest(archive, "SHA-256"), digest(profiles, "SHA-256"), Map.copyOf(groups));
        replace(archive, directory.resolve("pack.zip"));
        replace(profiles, directory.resolve("profiles.bin.gz"));
        Path temp = Files.createTempFile(directory, "manifest-", ".tmp");
        try { Files.writeString(temp, JSON.toJson(m)); move(temp, directory.resolve("manifest.json")); }
        finally { Files.deleteIfExists(temp); }
    }

    static void replace(Path source, Path target) throws IOException {
        if (source.toAbsolutePath().normalize().equals(target.toAbsolutePath().normalize())) return;
        Path temp = prepare(source, target);
        try { install(temp, target); }
        finally { Files.deleteIfExists(temp); }
    }
    static Path prepare(Path source, Path target) throws IOException {
        Files.createDirectories(target.toAbsolutePath().getParent());
        Path temp = Files.createTempFile(target.toAbsolutePath().getParent(), "pack-", ".tmp");
        try { Files.copy(source, temp, StandardCopyOption.REPLACE_EXISTING); return temp; }
        catch (IOException e) { Files.deleteIfExists(temp); throw e; }
    }
    static void install(Path prepared, Path target) throws IOException { move(prepared, target); }
    private static void move(Path source, Path target) throws IOException {
        try { Files.move(source, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING); }
        catch (AtomicMoveNotSupportedException e) { Files.move(source, target, StandardCopyOption.REPLACE_EXISTING); }
    }
    static String digest(Path file, String algorithm) throws IOException {
        try {
            var digest = MessageDigest.getInstance(algorithm);
            try (var in = new DigestInputStream(Files.newInputStream(file), digest)) { in.transferTo(OutputStream.nullOutputStream()); }
            return HexFormat.of().formatHex(digest.digest());
        } catch (NoSuchAlgorithmException e) { throw new AssertionError(e); }
    }

    /** Content keys ignore filesystem/ZIP timestamps and machine-specific absolute roots. */
    static final class Inputs {
        private final MessageDigest digest;
        private final Map<String, MessageDigest> groups = new TreeMap<>();
        private String current;
        Inputs() { try { digest = MessageDigest.getInstance("SHA-256"); } catch (NoSuchAlgorithmException e) { throw new AssertionError(e); } }
        Inputs text(String label, String value) {
            byte[] bytes = (label + "\0" + value + "\0").getBytes(java.nio.charset.StandardCharsets.UTF_8);
            digest.update(bytes);
            groups.computeIfAbsent(current != null ? current : group(label), k -> sha256()).update(bytes);
            return this;
        }
        private static MessageDigest sha256() {
            try { return MessageDigest.getInstance("SHA-256"); } catch (NoSuchAlgorithmException e) { throw new AssertionError(e); }
        }
        /** Group of a label: its first segment, so {@code mod/foo/0} reports as {@code mod/foo}. */
        static String group(String label) {
            int first = label.indexOf('/');
            if (first < 0) return label;
            if (label.startsWith("mod/") || label.startsWith("config/")) { int second = label.indexOf('/', label.indexOf('/') + 1); return second < 0 ? label : label.substring(0, second); }
            return label.substring(0, first);
        }
        /** Per-group digests, used only to tell the operator which input group caused a miss. */
        Map<String,String> groups() {
            var out = new TreeMap<String,String>();
            groups.forEach((k, v) -> out.put(k, HexFormat.of().formatHex(((MessageDigest) clone(v)).digest())));
            return out;
        }
        private static Object clone(MessageDigest d) {
            try { return d.clone(); } catch (CloneNotSupportedException e) { throw new AssertionError(e); }
        }
        Inputs path(String label, Path path) throws IOException {
            String previous = current; current = group(label);
            try { return pathInner(label, path); } finally { current = previous; }
        }
        /** Hash only archive/directory entries under the given prefixes (resource-bearing paths of a foreign mod). */
        Inputs assetsOnly(String label, Path path, String... prefixes) throws IOException {
            String previous = current; current = group(label);
            try {
                if (!Files.exists(path)) return text(label, "missing");
                if (Files.isDirectory(path)) {
                    text(label, "directory");
                    try (var walk = Files.walk(path)) {
                        for (var file : walk.filter(Files::isRegularFile).sorted().toList()) {
                            String rel = path.relativize(file).toString().replace('\\','/');
                            if (wanted(rel, prefixes)) file(label + "/" + rel, file);
                        }
                    }
                } else {
                    try (var zip = new ZipFile(path.toFile())) {
                        text(label, "archive");
                        for (var e : zip.stream().filter(e -> !e.isDirectory() && wanted(e.getName(), prefixes))
                                .sorted(Comparator.comparing(java.util.zip.ZipEntry::getName)).toList())
                            text(e.getName(), e.getSize() + ":" + e.getCrc());
                    }
                }
                return this;
            } finally { current = previous; }
        }
        private static boolean wanted(String name, String[] prefixes) {
            for (String p : prefixes) if (name.startsWith(p)) return true;
            return false;
        }
        private Inputs pathInner(String label, Path path) throws IOException {
            if (!Files.exists(path)) return text(label, "missing");
            if (Files.isDirectory(path)) {
                text(label, "directory");
                try (var walk = Files.walk(path)) {
                    for (var file : walk.filter(Files::isRegularFile).filter(p -> !ignored(path.relativize(p))).sorted().toList())
                        file(label + "/" + path.relativize(file).toString().replace('\\','/'), file);
                }
            } else file(label, path);
            return this;
        }
        private void file(String label, Path path) throws IOException {
            String name = path.getFileName().toString();
            if (name.endsWith(".jar") || name.endsWith(".zip")) {
                try (var zip = new ZipFile(path.toFile())) {
                    text(label, "archive");
                    // BetterModel rewrites its generated icon on every start (200 B vs 2.4 KB observed); the shipped pack icon is
                    // Polymer's, which is hashed separately, so the generated one must not decide hit or miss.
                    boolean generatedIcon = label.equals("bettermodel-output");
                    for (var e : zip.stream().filter(e -> !e.isDirectory() && !(generatedIcon && e.getName().equals("pack.png")))
                            .sorted(Comparator.comparing(java.util.zip.ZipEntry::getName)).toList())
                        text(e.getName(), e.getSize() + ":" + e.getCrc());
                }
            } else { text(label, "file"); text("contents", PackCacheStore.digest(path, "SHA-256")); }
        }
        private static boolean ignored(Path relative) {
            for (var part : relative) if (part.toString().equals(".cache") || part.toString().equals(".DS_Store")) return true;
            String name = relative.toString().replace('\\','/'); return name.equals("bettermodel/build.zip") || name.equals("build.zip");
        }
        String finish() { return HexFormat.of().formatHex(digest.digest()); }
        Key key() { var g = groups(); return new Key(finish(), g); }
    }
}
