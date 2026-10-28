package kim.biryeong.destiny.world;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.GZIPInputStream;

/** Immutable, bounded sparse voxel data; omitted positions remain air. */
public final class TowerVoxelMap {
    public static final String VOXEL_RESOURCE = "/data/destiny/tower/courtyard.vox.gz";
    public static final String MANIFEST_RESOURCE = "/data/destiny/tower/courtyard.json";
    public static final int MIN_Y = -64, HEIGHT = 384;
    private static final int MAX_VOXELS = 12_000_000;
    private final Manifest manifest;
    private final List<String> palette;
    private final Map<Long, int[]> chunks;
    private final int blockCount;

    private TowerVoxelMap(Manifest manifest, List<String> palette, Map<Long, int[]> chunks, int count) {
        this.manifest = manifest;
        this.palette = List.copyOf(palette);
        this.chunks = Map.copyOf(chunks);
        this.blockCount = count;
    }

    public static TowerVoxelMap loadBundled() throws IOException {
        try (InputStream manifest = TowerVoxelMap.class.getResourceAsStream(MANIFEST_RESOURCE);
             InputStream voxels = TowerVoxelMap.class.getResourceAsStream(VOXEL_RESOURCE)) {
            if (manifest == null || voxels == null) throw new IOException("타워 맵 리소스가 없습니다.");
            return decode(manifest, voxels);
        }
    }

    public static TowerVoxelMap decode(InputStream manifestInput, InputStream compressedInput) throws IOException {
        Manifest manifest;
        try {
            JsonObject root = JsonParser.parseReader(new InputStreamReader(manifestInput, StandardCharsets.UTF_8)).getAsJsonObject();
            if (root.get("schema").getAsInt() != 1 || !root.get("id").getAsString().equals("destiny:tower")
                    || !root.get("voxelResource").getAsString().equals(VOXEL_RESOURCE.substring(1)))
                throw new IllegalArgumentException("Unsupported manifest");
            var bounds = root.getAsJsonObject("bounds");
            var lo = bounds.getAsJsonArray("min");
            var hi = bounds.getAsJsonArray("max");
            var s = root.getAsJsonObject("spawn");
            manifest = new Manifest(new Bounds(lo.get(0).getAsInt(), lo.get(1).getAsInt(), lo.get(2).getAsInt(),
                    hi.get(0).getAsInt(), hi.get(1).getAsInt(), hi.get(2).getAsInt()),
                    new Spawn(s.get("x").getAsDouble(), s.get("y").getAsDouble(), s.get("z").getAsDouble(),
                            s.get("yaw").getAsFloat(), s.get("pitch").getAsFloat()),
                    root.get("returnBelowY").getAsInt(), root.get("worldBorder").getAsDouble(), root.get("blockCount").getAsInt());
            manifest.validate();
        } catch (RuntimeException e) { throw new IOException("Invalid tower manifest", e); }
        try (var in = new DataInputStream(new GZIPInputStream(compressedInput))) {
            if (!Arrays.equals(in.readNBytes(8), "DGTWR001".getBytes(StandardCharsets.US_ASCII)))
                throw new IOException("Invalid tower voxel magic");
            int paletteCount = in.readInt();
            if (paletteCount < 1 || paletteCount > 4096) throw new IOException("Invalid palette count");
            List<String> palette = new ArrayList<>(paletteCount);
            for (int i = 0; i < paletteCount; i++) {
                int length = in.readUnsignedShort();
                if (length == 0 || length > 8192) throw new IOException("Invalid palette entry length");
                byte[] bytes = in.readNBytes(length);
                if (bytes.length != length) throw new EOFException("Truncated palette");
                String state = new String(bytes, StandardCharsets.UTF_8);
                if (!state.matches("minecraft:[a-z0-9_]+(\\[[a-z0-9_=,]+\\])?")
                        || state.equals("minecraft:air") || state.equals("minecraft:cave_air") || state.equals("minecraft:void_air"))
                    throw new IOException("Only non-air vanilla block states are allowed: " + state);
                palette.add(state);
            }
            int count = in.readInt();
            if (count < 1 || count > MAX_VOXELS || count != manifest.blockCount()) throw new IOException("Invalid voxel count");
            Map<Long, IntBuffer> buffers = new HashMap<>();
            for (int i = 0; i < count; i++) {
                int x = in.readInt(), y = in.readInt(), z = in.readInt(), index = in.readUnsignedShort();
                if (!manifest.bounds().contains(x, y, z) || index >= paletteCount) throw new IOException("Voxel outside manifest/palette");
                buffers.computeIfAbsent(chunkKey(x >> 4, z >> 4), ignored -> new IntBuffer()).add((localKey(x, y, z) << 12) | index);
            }
            if (in.read() != -1) throw new IOException("Trailing tower voxel data");
            Map<Long, int[]> chunks = new HashMap<>();
            for (var entry : buffers.entrySet()) {
                int[] data = entry.getValue().finish();
                Arrays.sort(data);
                for (int i = 1; i < data.length; i++)
                    if ((data[i - 1] >>> 12) == (data[i] >>> 12)) throw new IOException("Duplicate tower voxel");
                chunks.put(entry.getKey(), data);
            }
            return new TowerVoxelMap(manifest, palette, chunks, count);
        }
    }

    private static long chunkKey(int x, int z) { return ((long) x << 32) ^ (z & 0xffffffffL); }
    private static int localKey(int x, int y, int z) { return ((y - MIN_Y) << 8) | ((z & 15) << 4) | (x & 15); }
    public Manifest manifest() { return manifest; }
    public List<String> palette() { return palette; }
    public int blockCount() { return blockCount; }
    public int paletteIndexAt(int x, int y, int z) {
        if (!manifest.bounds().contains(x, y, z)) return -1;
        int[] data = chunks.get(chunkKey(x >> 4, z >> 4));
        if (data == null) return -1;
        int key = localKey(x, y, z) << 12;
        int at = Arrays.binarySearch(data, key);
        if (at < 0) at = -at - 1;
        return at < data.length && (data[at] >>> 12) == (key >>> 12) ? data[at] & 4095 : -1;
    }
    public void forChunk(int chunkX, int chunkZ, VoxelConsumer consumer) {
        int[] data = chunks.get(chunkKey(chunkX, chunkZ));
        if (data == null) return;
        for (int value : data) {
            int key = value >>> 12;
            consumer.accept((chunkX << 4) + (key & 15), MIN_Y + (key >>> 8),
                    (chunkZ << 4) + ((key >>> 4) & 15), value & 4095);
        }
    }
    @FunctionalInterface public interface VoxelConsumer { void accept(int x, int y, int z, int paletteIndex); }
    public record Bounds(int minX, int minY, int minZ, int maxX, int maxY, int maxZ) {
        public boolean contains(int x, int y, int z) {
            return x >= minX && x <= maxX && y >= minY && y <= maxY && z >= minZ && z <= maxZ;
        }
    }
    public record Spawn(double x, double y, double z, float yaw, float pitch) {}
    public record Manifest(Bounds bounds, Spawn spawn, int returnBelowY, double worldBorder, int blockCount) {
        private void validate() {
            if (bounds.minX() > bounds.maxX() || bounds.minY() > bounds.maxY() || bounds.minZ() > bounds.maxZ()
                    || bounds.minY() < MIN_Y || bounds.maxY() >= MIN_Y + HEIGHT
                    || Math.abs((long) bounds.minX()) > 1_000_000 || Math.abs((long) bounds.maxX()) > 1_000_000
                    || Math.abs((long) bounds.minZ()) > 1_000_000 || Math.abs((long) bounds.maxZ()) > 1_000_000
                    || !Double.isFinite(spawn.x()) || !Double.isFinite(spawn.y()) || !Double.isFinite(spawn.z())
                    || !Float.isFinite(spawn.yaw()) || !Float.isFinite(spawn.pitch()) || Math.abs(spawn.pitch()) > 90
                    || !bounds.contains((int) Math.floor(spawn.x()), (int) Math.floor(spawn.y()), (int) Math.floor(spawn.z()))
                    || returnBelowY >= spawn.y() || !Double.isFinite(worldBorder) || worldBorder <= 0
                    || worldBorder > 2_000_000 || worldBorder < Math.max(bounds.maxX() - bounds.minX() + 1, bounds.maxZ() - bounds.minZ() + 1)
                    || blockCount < 1 || blockCount > MAX_VOXELS) throw new IllegalArgumentException("Invalid tower bounds/spawn");
        }
    }
    private static final class IntBuffer {
        private int[] data = new int[256];
        private int size;
        void add(int value) { if (size == data.length) data = Arrays.copyOf(data, size * 2); data[size++] = value; }
        int[] finish() { return Arrays.copyOf(data, size); }
    }
}
