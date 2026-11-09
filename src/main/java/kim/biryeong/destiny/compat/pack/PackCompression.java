package kim.biryeong.destiny.compat.pack;

import com.google.gson.*;
import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.PolymerResourcePackUtils;
import eu.pb4.polymer.resourcepack.api.ResourcePackBuilder;
import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.loader.api.FabricLoader;

import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.zip.CRC32;
import java.util.zip.Deflater;

/**
 * Output-only, experience-preserving pack compression. Runs as the last converter of the pack build:
 * <ul>
 *   <li>JSON is minified; model geometry/display numbers are rounded to 5 decimals (exact for every 1/32-texel UV
 *   step, far below one screen pixel for positions and angles). Item routes and other data keep exact numbers.</li>
 *   <li>PNG is re-encoded losslessly (identical RGBA, including colour under transparent pixels): smallest colour type,
 *   per-row adaptive filters, maximum deflate. Results are cached on disk by content hash.</li>
 *   <li>Sound files that no {@code sounds.json} references are omitted (they cannot be played).</li>
 * </ul>
 * Source resources are never modified. {@code -Ddestiny.pack.compress=false} disables the pass.
 */
public final class PackCompression {
    private static final Gson GSON = new GsonBuilder().disableHtmlEscaping().create();
    private static final Set<String> GEOMETRY_KEYS = Set.of("elements", "display", "from", "to", "origin", "uv",
            "rotation", "translation", "scale", "angle", "faces");
    private static boolean initialized;
    private PackCompression() {}

    public static synchronized void init() {
        if (initialized || !Boolean.parseBoolean(System.getProperty("destiny.pack.compress", "true"))) return;
        initialized = true;
        // Registered after every other pack hook, so this task and its converter run last.
        PolymerResourcePackUtils.RESOURCE_PACK_CREATION_EVENT.register(builder -> builder.addPreFinishTask(PackCompression::prepare));
    }

    private static void prepare(ResourcePackBuilder builder) {
        long t0 = System.nanoTime();
        var files = new LinkedHashMap<String, PackResource>();
        builder.forEachResource(files::put);
        var referenced = referencedSounds(files);
        var unused = new HashSet<String>();
        for (String p : files.keySet())
            // Vanilla's own sounds.json references minecraft-namespace overrides, so those always stay.
            if (p.startsWith("assets/") && !p.startsWith("assets/minecraft/") && !untouched(p) && p.endsWith(".ogg") && !referenced.contains(p)) unused.add(p);
        var upstream = upstream(builder);
        var renames = renames(builder, files, upstream, unused);
        var png = new ConcurrentHashMap<String, byte[]>();
        Path cache = FabricLoader.getInstance().getGameDir().resolve("polymer/destiny-png-cache-v2");
        try { Files.createDirectories(cache); } catch (IOException ignored) {}
        var before = new java.util.concurrent.atomic.AtomicLong(); var after = new java.util.concurrent.atomic.AtomicLong();
        files.entrySet().parallelStream().filter(e -> e.getKey().endsWith(".png") && !untouched(e.getKey())).forEach(e -> {
            var resource = upstream == null ? e.getValue() : upstream.convert(e.getKey(),e.getValue());
            if (resource == null) return;
            byte[] src = resource.readAllBytes();
            byte[] out = optimizedPng(src, cache);
            before.addAndGet(src.length); after.addAndGet(out.length);
            if (out.length < src.length) png.put(sha1(src), out);
        });
        var ids = renames.ids;
        builder.addResourceConverter((path, data) -> {
            if (data == null || unused.contains(path) || renames.moved.contains(path)) return null;
            if (untouched(path)) return data;
            if (path.endsWith(".png")) {
                // Keyed by the bytes actually reaching this converter: earlier converters (e.g. font marker pixels)
                // may have changed the file after the snapshot, and those bytes get optimized on demand.
                byte[] in = data.readAllBytes(); String k = sha1(in);
                byte[] b = png.computeIfAbsent(k, x -> optimizedPng(in, cache));
                return b.length < in.length ? PackResource.of(b) : data;
            }
            if (path.endsWith(".json") || path.endsWith(".mcmeta")) return json(path, data, ids);
            return data;
        });
        DestinyGuardians.LOGGER.info("Pack compression: PNG {} -> {} bytes ({} files), {} unreferenced sounds omitted, {} generated models given short paths, prepared in {} ms",
                before.get(), after.get(), png.size(), unused.size(), renames.moved.size(), (System.nanoTime() - t0) / 1_000_000);
    }

    /** Assets this pass never rewrites (minigame-lib font/transition art ships exactly as its library provides it). */
    static boolean untouched(String path) {
        return path.startsWith("assets/minigamelib/");
    }

    /** Generated-only model directories: no code or data outside item/model JSON names these files. */
    private static final List<String> SHORTEN = List.of("assets/destiny/models/first_person_framing_w205/",
            "assets/destiny/models/weapon_reload_w");
    private static final String SHORT_DIR = "assets/destiny/models/z/";

    private record Renames(Set<String> moved, Map<String, String> ids) {}

    /**
     * Zip headers store each path twice, so 70k long generated names cost ~18 MB. Give generated pose/framing models
     * short base-36 paths; every JSON reference is rewritten by the converter. Each file is first passed through the
     * converters registered before this pass, so omissions and rewrites made by earlier hooks are preserved.
     */
    private static Renames renames(ResourcePackBuilder builder, Map<String, PackResource> files,
                                   ResourcePackBuilder.ResourceConverter upstream, Set<String> unused) {
        var moved = new HashSet<String>(); var ids = new HashMap<String, String>();
        if (upstream == null) return new Renames(moved, ids);
        int n = 0;
        var sorted = new ArrayList<>(files.keySet()); Collections.sort(sorted);   // deterministic names
        for (String path : sorted) {
            if (!path.endsWith(".json") || SHORTEN.stream().noneMatch(path::startsWith)) continue;
            if (path.startsWith("assets/destiny/models/weapon_reload_w") && path.indexOf('/', "assets/destiny/models/".length()) < 0) continue;
            PackResource res = upstream.convert(path, files.get(path));
            if (res == null) { moved.add(path); continue; }   // omitted upstream: stays omitted
            String shortPath = SHORT_DIR + Integer.toString(n++, 36) + ".json";
            if (files.containsKey(shortPath)) throw new IllegalStateException("short model path in use " + shortPath);
            builder.addData(shortPath, res);
            moved.add(path);
            ids.put(id(path), id(shortPath));
        }
        return new Renames(moved, ids);
    }

    private static String id(String path) {
        String rest = path.substring("assets/".length(), path.length() - ".json".length());
        int slash = rest.indexOf('/');
        return rest.substring(0, slash) + ":" + rest.substring(slash + "/models/".length());
    }

    @SuppressWarnings("unchecked")
    private static ResourcePackBuilder.ResourceConverter upstream(ResourcePackBuilder builder) {
        try {
            var f = builder.getClass().getDeclaredField("converters"); f.setAccessible(true);
            var list = List.copyOf((List<ResourcePackBuilder.ResourceConverter>) f.get(builder));
            return (path, data) -> {
                for (var c : list) { data = c.convert(path, data); if (data == null) return null; }
                return data;
            };
        } catch (ReflectiveOperationException | RuntimeException ex) {
            DestinyGuardians.LOGGER.warn("Pack compression: converter chain unavailable, model paths kept ({})", ex.toString());
            return null;
        }
    }

    private static Set<String> referencedSounds(Map<String, PackResource> files) {
        var out = new HashSet<String>();
        for (var e : files.entrySet()) {
            if (!e.getKey().endsWith("/sounds.json") || !e.getKey().startsWith("assets/")) continue;
            String ns = e.getKey().split("/")[1];
            try {
                var root = JsonParser.parseString(e.getValue().asString()).getAsJsonObject();
                for (var ev : root.entrySet()) {
                    if (!ev.getValue().isJsonObject() || !ev.getValue().getAsJsonObject().has("sounds")) continue;
                    for (var s : ev.getValue().getAsJsonObject().getAsJsonArray("sounds")) {
                        String name;
                        if (s.isJsonPrimitive()) name = s.getAsString();
                        else {
                            var o = s.getAsJsonObject();
                            if (o.has("type") && "event".equals(o.get("type").getAsString())) continue;
                            name = o.get("name").getAsString();
                        }
                        String n2 = name.contains(":") ? name.substring(name.indexOf(':') + 1) : name;
                        String n1 = name.contains(":") ? name.substring(0, name.indexOf(':')) : "minecraft";
                        out.add("assets/" + n1 + "/sounds/" + n2 + ".ogg");
                    }
                }
            } catch (RuntimeException ex) {
                // An unreadable sounds.json keeps every sound of that namespace.
                for (String p : files.keySet()) if (p.startsWith("assets/" + ns + "/sounds/")) out.add(p);
            }
        }
        return out;
    }

    // ---------------------------------------------------------------- JSON

    static PackResource json(String path, PackResource data, Map<String, String> ids) {
        String text;
        JsonElement el;
        try { text = data.asString(); el = JsonParser.parseString(text); } catch (RuntimeException ex) { return data; }
        if (path.contains("/models/")) el = round(el, false);
        if (!ids.isEmpty()) el = relink(el, ids);
        String min = GSON.toJson(el);
        return min.equals(text) ? data : PackResource.fromString(min);
    }

    static JsonElement relink(JsonElement el, Map<String, String> ids) {
        if (el.isJsonObject()) { var o = el.getAsJsonObject(); for (var e : o.entrySet()) e.setValue(relink(e.getValue(), ids)); return o; }
        if (el.isJsonArray()) { var a = el.getAsJsonArray(); for (int i = 0; i < a.size(); i++) a.set(i, relink(a.get(i), ids)); return a; }
        if (el.isJsonPrimitive() && el.getAsJsonPrimitive().isString()) {
            String r = ids.get(el.getAsString());
            return r == null ? el : new JsonPrimitive(r);
        }
        return el;
    }

    static JsonElement round(JsonElement el, boolean geometry) {
        if (el.isJsonObject()) {
            var o = el.getAsJsonObject(); var n = new JsonObject();
            for (var e : o.entrySet()) n.add(e.getKey(), round(e.getValue(), geometry || GEOMETRY_KEYS.contains(e.getKey())));
            return n;
        }
        if (el.isJsonArray()) {
            var a = new JsonArray();
            for (var v : el.getAsJsonArray()) a.add(round(v, geometry));
            return a;
        }
        if (geometry && el.isJsonPrimitive() && el.getAsJsonPrimitive().isNumber()) {
            double d = el.getAsDouble();
            double r = Math.round(d * 100000.0) / 100000.0;
            if (r == Math.rint(r) && Math.abs(r) < 1e15) return new JsonPrimitive((long) r);
            return new JsonPrimitive(new java.math.BigDecimal(Double.toString(r)).stripTrailingZeros());
        }
        return el;
    }

    // ---------------------------------------------------------------- PNG

    private static byte[] optimizedPng(byte[] src, Path cache) {
        String key = sha1(src);
        Path hit = cache.resolve(key + ".png");
        try { if (Files.exists(hit)) return Files.readAllBytes(hit); } catch (IOException ignored) {}
        byte[] out;
        try { out = encode(src); } catch (Exception ex) { out = src; }
        if (out.length >= src.length) out = src;
        try { Files.write(hit, out); } catch (IOException ignored) {}
        return out;
    }

    static String sha1(byte[] b) {
        try {
            var md = MessageDigest.getInstance("SHA-1"); var sb = new StringBuilder();
            for (byte x : md.digest(b)) sb.append(String.format("%02x", x));
            return sb.toString();
        } catch (Exception e) { throw new IllegalStateException(e); }
    }

    /** Lossless re-encode. Exact RGBA per pixel; returns null-equivalent (src) on anything unusual. */
    static byte[] encode(byte[] src) throws IOException {
        // Leave animated/indexed-with-metadata PNGs alone unless we can decode them fully: decode via ImageIO.
        if (!plain(src)) return src;
        BufferedImage img = javax.imageio.ImageIO.read(new ByteArrayInputStream(src));
        if (img == null) return src;
        int w = img.getWidth(), h = img.getHeight();
        int[] argb = img.getRGB(0, 0, w, h, null, 0, w);
        // ImageIO decodes 16-bit or gamma-tagged files lossy; only proceed for 8-bit sources.
        if (img.getColorModel().getComponentSize(0) > 8) return src;
        boolean opaque = true, gray = true;
        var palette = new LinkedHashMap<Integer, Integer>();
        for (int c : argb) {
            int a = c >>> 24, r = (c >> 16) & 255, g = (c >> 8) & 255, b = c & 255;
            if (a != 255) opaque = false;
            if (r != g || g != b) gray = false;
            if (palette.size() <= 256 && !palette.containsKey(c)) palette.put(c, palette.size());
        }
        var candidates = new ArrayList<byte[]>();
        // Whole-image filter strategies (-1 = per-row minimum-sum heuristic); textures with flat areas often compress
        // best unfiltered, photographic ones with Paeth/Up. The smallest result wins.
        for (int strategy : new int[]{-1, 0, 1, 2, 4}) {
            if (palette.size() <= 256) candidates.add(png(w, h, argb, 3, palette, strategy));
            if (gray) candidates.add(png(w, h, argb, opaque ? 0 : 4, null, strategy));
            candidates.add(png(w, h, argb, opaque ? 2 : 6, null, strategy));
        }
        byte[] best = src;
        for (var c : candidates) if (c.length < best.length) best = c;
        if (best != src) {   // round-trip guard: the new file must decode to exactly the same pixels
            var back = javax.imageio.ImageIO.read(new ByteArrayInputStream(best));
            if (back == null || back.getWidth() != w || back.getHeight() != h || !Arrays.equals(argb, back.getRGB(0, 0, w, h, null, 0, w))) return src;
        }
        return best;
    }

    private static byte[] png(int w, int h, int[] argb, int type, Map<Integer, Integer> palette, int strategy) throws IOException {
        int bpp = switch (type) { case 0 -> 1; case 2 -> 3; case 3 -> 1; case 4 -> 2; default -> 4; };
        int stride = w * bpp;
        byte[] prev = new byte[stride], cur = new byte[stride];
        var raw = new ByteArrayOutputStream(h * (stride + 1));
        byte[][] trial = new byte[5][stride];
        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                int c = argb[y * w + x], i = x * bpp;
                int a = c >>> 24, r = (c >> 16) & 255, g = (c >> 8) & 255, b = c & 255;
                switch (type) {
                    case 0 -> cur[i] = (byte) r;
                    case 2 -> { cur[i] = (byte) r; cur[i + 1] = (byte) g; cur[i + 2] = (byte) b; }
                    case 3 -> cur[i] = (byte) (int) palette.get(c);
                    case 4 -> { cur[i] = (byte) r; cur[i + 1] = (byte) a; }
                    default -> { cur[i] = (byte) r; cur[i + 1] = (byte) g; cur[i + 2] = (byte) b; cur[i + 3] = (byte) a; }
                }
            }
            int f;
            if (strategy >= 0 ? strategy == 0 : type == 3) { f = 0; System.arraycopy(cur, 0, trial[0], 0, stride); }
            else {
                long bestSum = Long.MAX_VALUE; f = 0;
                for (int ft = strategy >= 0 ? strategy : 0; ft < (strategy >= 0 ? strategy + 1 : 5); ft++) {
                    long sum = 0; byte[] t = trial[ft];
                    for (int i = 0; i < stride; i++) {
                        int x = cur[i] & 255, a = i >= bpp ? cur[i - bpp] & 255 : 0, b = prev[i] & 255, c = i >= bpp ? prev[i - bpp] & 255 : 0;
                        int p = switch (ft) { case 0 -> 0; case 1 -> a; case 2 -> b; case 3 -> (a + b) >>> 1; default -> paeth(a, b, c); };
                        t[i] = (byte) (x - p); sum += Math.abs((int) t[i]);
                    }
                    if (sum < bestSum) { bestSum = sum; f = ft; }
                }
            }
            raw.write(f); raw.write(trial[f], 0, stride);
            byte[] sw = prev; prev = cur; cur = sw;
        }
        var def = new Deflater(Deflater.BEST_COMPRESSION);
        def.setInput(raw.toByteArray()); def.finish();
        var idat = new ByteArrayOutputStream(); byte[] buf = new byte[1 << 16];
        while (!def.finished()) idat.write(buf, 0, def.deflate(buf));
        def.end();
        var out = new ByteArrayOutputStream(); var d = new DataOutputStream(out);
        d.write(new byte[]{(byte) 0x89, 'P', 'N', 'G', '\r', '\n', 0x1a, '\n'});
        var ihdr = new ByteArrayOutputStream(); var hd = new DataOutputStream(ihdr);
        hd.writeInt(w); hd.writeInt(h); hd.writeByte(8); hd.writeByte(type); hd.writeByte(0); hd.writeByte(0); hd.writeByte(0);
        chunk(d, "IHDR", ihdr.toByteArray());
        if (type == 3) {
            var plte = new ByteArrayOutputStream(); var trns = new ByteArrayOutputStream(); int lastAlpha = -1, i = 0;
            for (int c : palette.keySet()) {
                plte.write((c >> 16) & 255); plte.write((c >> 8) & 255); plte.write(c & 255);
                trns.write(c >>> 24); if ((c >>> 24) != 255) lastAlpha = i; i++;
            }
            chunk(d, "PLTE", plte.toByteArray());
            if (lastAlpha >= 0) chunk(d, "tRNS", Arrays.copyOf(trns.toByteArray(), lastAlpha + 1));
        }
        chunk(d, "IDAT", idat.toByteArray());
        chunk(d, "IEND", new byte[0]);
        return out.toByteArray();
    }

    /** 8-bit-or-less PNG without colour-management chunks (ImageIO would convert those values). */
    static boolean plain(byte[] b) {
        if (b.length < 33 || (b[0] & 255) != 0x89 || b[1] != 'P') return false;
        int depth = b[24] & 255;
        if (depth > 8) return false;
        int i = 8;
        while (i + 8 <= b.length) {
            int len = ((b[i] & 255) << 24) | ((b[i + 1] & 255) << 16) | ((b[i + 2] & 255) << 8) | (b[i + 3] & 255);
            String t = new String(b, i + 4, 4, StandardCharsets.US_ASCII);
            if (t.equals("iCCP") || t.equals("gAMA") || t.equals("cHRM") || t.equals("acTL")) return false;
            if (t.equals("IEND")) return true;
            if (len < 0) return false;
            i += 12 + len;
        }
        return false;
    }

    private static int paeth(int a, int b, int c) {
        int p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
        return pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
    }

    private static void chunk(DataOutputStream d, String type, byte[] data) throws IOException {
        byte[] t = type.getBytes(StandardCharsets.US_ASCII);
        d.writeInt(data.length); d.write(t); d.write(data);
        var crc = new CRC32(); crc.update(t); crc.update(data); d.writeInt((int) crc.getValue());
    }
}
