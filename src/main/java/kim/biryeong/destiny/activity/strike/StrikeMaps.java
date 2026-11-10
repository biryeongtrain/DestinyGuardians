package kim.biryeong.destiny.activity.strike;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.campaign.RisingServices;
import kim.biryeong.destiny.campaign.map.ZoneTemplate;
import kim.biryeong.destiny.world.template.TemplateChunkWarmup;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.Vec3;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;

/**
 * Map data of one strike: per-zone section-NBT templates, and the {@code markers.json} that places named anchors
 * (spawn points, objectives, route nodes) in zone-local coordinates. Everything is keyed by the strike's zone enum and
 * read from {@code /data/destiny/<strike>/zones/} and {@code /data/destiny/map_template/<strike>/}.
 * <p>An instance is immutable configuration plus a load-once cache; nothing in it is tied to a run.
 */
public final class StrikeMaps<Z extends Enum<Z> & StrikeZone> {
    private final String name;
    private final Class<Z> zoneType;
    private final String resourceDir;
    private final String templateDir;
    private final String templateKeyPrefix;
    private final Function<Z, BlockPos> origins;
    private final Map<Z, ZoneTemplate> authoring = new ConcurrentHashMap<>();
    private final Map<Z, BlockPos> dimensions = new ConcurrentHashMap<>();
    private volatile Map<Z, List<RisingServices.Marker>> localMarkers;
    private volatile Map<Z, xyz.nucleoid.map_templates.MapTemplate> nbtTemplates = Map.of();

    /**
     * @param strikeId   directory name under {@code /data/destiny/} and {@code /data/destiny/map_template/}
     * @param name       display name for error messages
     * @param keyPrefix  prefix of the authoring-grid template key (kept for the first strike's existing keys)
     * @param origins    where each zone sits in the run world
     */
    public StrikeMaps(String strikeId, String name, String keyPrefix, Class<Z> zoneType, Function<Z, BlockPos> origins) {
        this.name = Objects.requireNonNull(name);
        this.zoneType = Objects.requireNonNull(zoneType);
        this.templateKeyPrefix = Objects.requireNonNull(keyPrefix);
        this.origins = Objects.requireNonNull(origins);
        this.resourceDir = "/data/destiny/" + strikeId + "/zones/";
        this.templateDir = "/data/destiny/map_template/" + strikeId + "/";
    }

    public String resourceDir() { return resourceDir; }
    public Z[] zones() { return zoneType.getEnumConstants(); }
    public BlockPos origin(Z zone) { return origins.apply(zone); }

    public xyz.nucleoid.map_templates.MapTemplate nbt(Z zone) {
        var template = nbtTemplates.get(zone);
        if (template == null) throw new IllegalStateException("NBT templates have not finished loading");
        return template;
    }
    public List<xyz.nucleoid.map_templates.MapTemplate> nbtTemplates() {
        return Arrays.stream(zones()).map(this::nbt).toList();
    }
    /** Offline authoring-grid access for lossless conversion regression; never used by strike generation. */
    public ZoneTemplate template(Z zone) {
        return authoring.computeIfAbsent(zone, z -> {
            try (InputStream in = resource(z.resourceName() + ".zone")) {
                return ZoneTemplate.decode(templateKeyPrefix + z.resourceName(), in);
            } catch (IOException e) { throw new UncheckedIOException(e); }
        });
    }

    public CompletableFuture<Void> preloadAsync(MinecraftServer server) {
        var registry = server.registryAccess();
        nbtTemplates = Map.of();
        return CompletableFuture.runAsync(() -> {
            var loaded = new EnumMap<Z, xyz.nucleoid.map_templates.MapTemplate>(zoneType);
            for (var zone : zones()) {
                String path = templateDir + zone.resourceName() + ".nbt";
                try (var in = StrikeMaps.class.getResourceAsStream(path)) {
                    if (in == null) throw new FileNotFoundException(path);
                    var value = xyz.nucleoid.map_templates.MapTemplateSerializer.loadFrom(in, registry);
                    var origin = origin(zone);
                    if (!value.getBounds().min().equals(origin))
                        throw new IOException("Template origin does not match anchors: " + zone);
                    if (!value.getBounds().max().equals(origin.offset(dimensions(zone)).offset(-1, -1, -1)))
                        throw new IOException("Template size does not match anchors: " + zone);
                    loaded.put(zone, value);
                } catch (IOException e) { throw new UncheckedIOException(path, e); }
            }
            locals();
            nbtTemplates = Map.copyOf(loaded);
        });
    }
    /** True once {@link #preloadAsync} has published every zone. */
    public boolean loaded() { return !nbtTemplates.isEmpty(); }

    /** Warm generator-owned chunks only: no per-block ServerLevel writes. */
    public RisingServices.ZoneBuild begin(ServerLevel level, Z zone, BlockPos origin) {
        if (!origin.equals(nbt(zone).getBounds().min())) throw new IllegalArgumentException("Template origin mismatch");
        return new TemplateChunkWarmup(level, nbt(zone).getBounds(), warmupMargin(kim.biryeong.destiny.world.DestinyWorldDistances.effectiveViewDistance(level)));
    }
    /** View radius plus one column, capped so neighbouring zones never share columns. */
    public static int warmupMargin(int viewDistance) { return Math.clamp(viewDistance + 1, 0, 12); }

    public List<RisingServices.Marker> markers(Z zone, BlockPos origin) {
        Vec3 offset = Vec3.atLowerCornerOf(origin);
        return locals().get(zone).stream().map(m -> new RisingServices.Marker(m.id(), m.pos().add(offset), m.yaw(), m.tags())).toList();
    }
    public RisingServices.Marker anchor(Z zone, String id, BlockPos origin) {
        return markers(zone, origin).stream().filter(m -> m.id().equals(id)).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Missing " + name + " anchor " + zone + "/" + id));
    }
    /** Authored alternatives sharing a {@code lane} tag. Runtime rechecks collision, occupancy, distance and reachability. */
    public List<RisingServices.Marker> candidates(Z zone, String lane, BlockPos origin) {
        return markers(zone, origin).stream().filter(m -> lane.equals(m.tags().get("lane"))).toList();
    }
    public boolean contains(Z zone, BlockPos origin, Vec3 p) {
        var size = dimensions(zone);
        return Double.isFinite(p.x) && Double.isFinite(p.y) && Double.isFinite(p.z)
                && p.x >= origin.getX() && p.x < origin.getX() + size.getX()
                && p.y >= origin.getY() && p.y < origin.getY() + size.getY()
                && p.z >= origin.getZ() && p.z < origin.getZ() + size.getZ();
    }
    public BlockPos dimensions(Z zone) {
        return dimensions.computeIfAbsent(zone, z -> {
            try (var in = resource("markers.json"); var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
                var size = JsonParser.parseReader(reader).getAsJsonObject().getAsJsonObject("zones")
                        .getAsJsonObject(z.resourceName()).getAsJsonArray("size");
                return new BlockPos(size.get(0).getAsInt(), size.get(1).getAsInt(), size.get(2).getAsInt());
            } catch (IOException e) { throw new UncheckedIOException(e); }
        });
    }

    private InputStream resource(String file) throws IOException {
        InputStream in = StrikeMaps.class.getResourceAsStream(resourceDir + file);
        if (in == null) throw new FileNotFoundException(resourceDir + file);
        return in;
    }
    private Map<Z, List<RisingServices.Marker>> locals() {
        var result = localMarkers;
        if (result == null) synchronized (this) {
            if (localMarkers == null) try (var in = resource("markers.json"); var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
                localMarkers = parse(reader);
            } catch (IOException e) { throw new UncheckedIOException(e); }
            result = localMarkers;
        }
        return result;
    }
    /** Every zone needs an {@code <ZONE>.IN} arrival anchor; anchors must lie inside their zone. */
    public Map<Z, List<RisingServices.Marker>> parse(Reader reader) throws IOException {
        try {
            var root = JsonParser.parseReader(reader).getAsJsonObject();
            if (root.get("schema").getAsInt() != 1) throw new IOException("Unsupported strike marker schema");
            var out = new EnumMap<Z, List<RisingServices.Marker>>(zoneType);
            for (var zone : zones()) {
                var obj = root.getAsJsonObject("zones").getAsJsonObject(zone.resourceName());
                var size = obj.getAsJsonArray("size");
                int sx = size.get(0).getAsInt(), sy = size.get(1).getAsInt(), sz = size.get(2).getAsInt();
                if (sx < 1 || sy < 1 || sz < 1 || sx > ZoneTemplate.MAX_EDGE || sy > ZoneTemplate.MAX_HEIGHT || sz > ZoneTemplate.MAX_EDGE)
                    throw new IOException("Invalid map dimensions for " + zone);
                var ids = new HashSet<String>();
                var list = new ArrayList<RisingServices.Marker>();
                for (var value : obj.getAsJsonArray("markers")) {
                    JsonObject m = value.getAsJsonObject();
                    String id = m.get("id").getAsString();
                    if (!id.matches("[A-Za-z][A-Za-z0-9_.-]{1,100}") || !ids.add(id)) throw new IOException("Invalid/duplicate anchor " + id);
                    var p = m.getAsJsonArray("pos");
                    Vec3 at = new Vec3(p.get(0).getAsDouble(), p.get(1).getAsDouble(), p.get(2).getAsDouble());
                    float yaw = m.get("yaw").getAsFloat();
                    if (!Double.isFinite(at.x) || !Double.isFinite(at.y) || !Double.isFinite(at.z) || !Float.isFinite(yaw)
                            || at.x < 0 || at.y < 0 || at.z < 0 || at.x >= sx || at.y >= sy || at.z >= sz)
                        throw new IOException("Anchor outside map: " + id);
                    Map<String, String> tags = new LinkedHashMap<>();
                    for (var tag : m.getAsJsonObject("tags").entrySet()) tags.put(tag.getKey(), tag.getValue().getAsString());
                    list.add(new RisingServices.Marker(id, at, yaw, Map.copyOf(tags)));
                }
                if (!ids.contains(zone.name() + ".IN")) throw new IOException("Missing arrival anchor " + zone);
                out.put(zone, List.copyOf(list));
            }
            return Map.copyOf(out);
        } catch (RuntimeException e) { throw new IOException("Invalid " + name + " markers", e); }
    }
}
