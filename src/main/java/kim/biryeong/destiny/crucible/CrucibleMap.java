package kim.biryeong.destiny.crucible;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.GZIPInputStream;

/** Immutable, bounded sparse voxel data; omitted positions remain air. */
public final class CrucibleMap {
    public static final String VOXEL_RESOURCE = "/data/destiny/crucible/javelin4.vox.gz";
    public static final String MANIFEST_RESOURCE = "/data/destiny/crucible/javelin4.json";
    public static final int MIN_Y = -64, HEIGHT = 384;
    private static final int MAX_VOXELS = 2_000_000;
    private final Manifest manifest;
    private final List<String> palette;
    private final Map<Long, int[]> chunks;
    private final int blockCount;

    private CrucibleMap(Manifest manifest, List<String> palette, Map<Long, int[]> chunks, int count) {
        this.manifest = manifest;
        this.palette = List.copyOf(palette);
        this.chunks = Map.copyOf(chunks);
        this.blockCount = count;
    }

    public static CrucibleMap loadBundled() throws IOException {
        try (InputStream manifest = CrucibleMap.class.getResourceAsStream(MANIFEST_RESOURCE);
             InputStream voxels = CrucibleMap.class.getResourceAsStream(VOXEL_RESOURCE)) {
            if (manifest == null || voxels == null) throw new IOException("시련의 장 맵 리소스가 없습니다.");
            return decode(manifest, voxels);
        }
    }

    public static CrucibleMap decode(InputStream manifestInput, InputStream compressedInput) throws IOException {
        Manifest manifest;
        try {
            JsonObject root = JsonParser.parseReader(new InputStreamReader(manifestInput, StandardCharsets.UTF_8)).getAsJsonObject();
            if (root.get("schema").getAsInt() != 1 || !root.get("id").getAsString().equals("destiny:javelin4")
                    || !root.get("voxelResource").getAsString().equals(VOXEL_RESOURCE.substring(1)))
                throw new IllegalArgumentException("Unsupported manifest");
            var bounds = root.getAsJsonObject("bounds");
            var lo = bounds.getAsJsonArray("min");
            var hi = bounds.getAsJsonArray("max");
            manifest = new Manifest(root.get("key").getAsString(), root.get("name").getAsString(),
                    new Bounds(lo.get(0).getAsInt(),lo.get(1).getAsInt(),lo.get(2).getAsInt(),
                            hi.get(0).getAsInt(),hi.get(1).getAsInt(),hi.get(2).getAsInt()),
                    root.get("returnBelowY").getAsInt(),root.get("worldBorder").getAsDouble(),root.get("blockCount").getAsInt(),
                    parseList(root,"alphaSpawns",Spawn.class),parseList(root,"bravoSpawns",Spawn.class),
                    parseList(root,"zones",Zone.class),parseList(root,"shots",Shot.class));
            manifest.validate();
        } catch (RuntimeException e) { throw new IOException("Invalid crucible manifest", e); }
        try (var in = new DataInputStream(new GZIPInputStream(compressedInput))) {
            if (!Arrays.equals(in.readNBytes(8), "DGCRU001".getBytes(StandardCharsets.US_ASCII)))
                throw new IOException("Invalid crucible voxel magic");
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
            if (in.read() != -1) throw new IOException("Trailing crucible voxel data");
            Map<Long, int[]> chunks = new HashMap<>();
            for (var entry : buffers.entrySet()) {
                int[] data = entry.getValue().finish();
                Arrays.sort(data);
                for (int i = 1; i < data.length; i++)
                    if ((data[i - 1] >>> 12) == (data[i] >>> 12)) throw new IOException("Duplicate crucible voxel");
                chunks.put(entry.getKey(), data);
            }
            var result = new CrucibleMap(manifest, palette, chunks, count);
            result.validateWalkablePoints();
            return result;
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
    public record Spawn(double x, double y, double z, float yaw, float pitch) {
        boolean finite() { return Double.isFinite(x) && Double.isFinite(y) && Double.isFinite(z)
                && Float.isFinite(yaw) && Float.isFinite(pitch) && Math.abs(pitch) <= 90; }
    }
    public record Zone(String key, String name, Spawn center, double radius, double height) {}
    public record Shot(String key, Spawn camera, Spawn target, int durationTicks) {}
    public record Manifest(String key, String name, Bounds bounds, int returnBelowY, double worldBorder,
            int blockCount, List<Spawn> alphaSpawns, List<Spawn> bravoSpawns, List<Zone> zones, List<Shot> shots) {
        public Manifest {
            alphaSpawns = List.copyOf(alphaSpawns); bravoSpawns = List.copyOf(bravoSpawns);
            zones = List.copyOf(zones); shots = List.copyOf(shots);
        }
        private void validate() {
            if (!key.equals("destiny:javelin4") || name.isBlank()
                    || bounds.minX() > bounds.maxX() || bounds.minY() > bounds.maxY() || bounds.minZ() > bounds.maxZ()
                    || bounds.minY() < MIN_Y || bounds.maxY() >= MIN_Y + HEIGHT
                    || Math.abs((long)bounds.minX()) > 1024 || Math.abs((long)bounds.maxX()) > 1024
                    || Math.abs((long)bounds.minZ()) > 1024 || Math.abs((long)bounds.maxZ()) > 1024
                    || !Double.isFinite(worldBorder) || worldBorder < 1 || worldBorder > 2048
                    || worldBorder < 2 * Math.max(Math.max(Math.abs(bounds.minX()),Math.abs(bounds.maxX())+1),
                                                 Math.max(Math.abs(bounds.minZ()),Math.abs(bounds.maxZ())+1))
                    || blockCount < 1 || blockCount > MAX_VOXELS || alphaSpawns.isEmpty() || bravoSpawns.isEmpty()
                    || alphaSpawns.size() > 64 || bravoSpawns.size() > 64 || zones.size() != 3 || shots.size() > 16)
                throw new IllegalArgumentException("Invalid crucible manifest");
            var zoneKeys = new HashSet<String>();
            for (Spawn spawn : alphaSpawns) validateGroundPoint(spawn);
            for (Spawn spawn : bravoSpawns) validateGroundPoint(spawn);
            for (Zone zone : zones) {
                if (!Set.of("A","B","C").contains(zone.key()) || !zoneKeys.add(zone.key()) || zone.name().isBlank()
                        || !Double.isFinite(zone.radius()) || zone.radius() <= 0 || zone.radius() > 16
                        || !Double.isFinite(zone.height()) || zone.height() < 2 || zone.height() > 16)
                    throw new IllegalArgumentException("Invalid zone");
                validateGroundPoint(zone.center());
            }
            for (Shot shot : shots) if (shot.key().isBlank() || !shot.camera().finite() || !shot.target().finite()
                    || shot.durationTicks() < 1 || shot.durationTicks() > 1200)
                throw new IllegalArgumentException("Invalid shot");
        }
        private void validateGroundPoint(Spawn p) {
            if (!p.finite() || returnBelowY >= p.y() || !bounds.contains((int)Math.floor(p.x()),
                    (int)Math.floor(p.y()-1), (int)Math.floor(p.z())))
                throw new IllegalArgumentException("Invalid ground point");
        }
    }
    private static <T> List<T> parseList(JsonObject root, String key, Class<T> type) {
        var result = new ArrayList<T>(); var gson = new com.google.gson.Gson();
        for (var element : root.getAsJsonArray(key)) result.add(gson.fromJson(element,type));
        return result;
    }
    /** Iterates sparse occupied cells without exposing mutable chunk arrays. */
    public void forEachVoxel(VoxelConsumer consumer) {
        for (long key : chunks.keySet()) forChunk((int)(key >> 32),(int)key,consumer);
    }
    /** Integer floor semantics match Minecraft, including negative coordinates. */
    public boolean isWalkable(Spawn p) {
        int x=(int)Math.floor(p.x()), y=(int)Math.floor(p.y()), z=(int)Math.floor(p.z());
        return p.finite() && p.y()==y && paletteIndexAt(x,y-1,z)>=0
                && paletteIndexAt(x,y,z)<0 && paletteIndexAt(x,y+1,z)<0;
    }
    private void validateWalkablePoints() throws IOException {
        for (Spawn p : manifest.alphaSpawns()) if (!isWalkable(p)) throw new IOException("Blocked alpha spawn");
        for (Spawn p : manifest.bravoSpawns()) if (!isWalkable(p)) throw new IOException("Blocked bravo spawn");
        for (Zone z : manifest.zones()) if (!isWalkable(z.center())) throw new IOException("Blocked zone " + z.key());
    }
    private static final class IntBuffer {
        private int[] data = new int[256];
        private int size;
        void add(int value) { if (size == data.length) data = Arrays.copyOf(data, size * 2); data[size++] = value; }
        int[] finish() { return Arrays.copyOf(data, size); }
    }
}
