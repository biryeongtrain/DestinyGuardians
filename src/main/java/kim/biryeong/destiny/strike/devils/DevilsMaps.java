package kim.biryeong.destiny.strike.devils;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.campaign.RisingServices;
import kim.biryeong.destiny.campaign.map.ZoneTemplate;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.Vec3;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;

/** Source-derived strike maps. All positions returned with an origin are already world coordinates. */
public final class DevilsMaps {
    public static final String RESOURCE_DIR = "/data/destiny/devils_lair/zones/";
    private static final Map<DevilsPlan.Zone, ZoneTemplate> TEMPLATES = new ConcurrentHashMap<>();
    private static volatile Map<DevilsPlan.Zone, List<RisingServices.Marker>> localMarkers;
    private static volatile Map<DevilsPlan.Zone, xyz.nucleoid.map_templates.MapTemplate> nbtTemplates = Map.of();
    public static xyz.nucleoid.map_templates.MapTemplate nbt(DevilsPlan.Zone zone) {
        var template = nbtTemplates.get(zone);
        if (template == null) throw new IllegalStateException("NBT templates have not finished loading");
        return template;
    }
    public static List<xyz.nucleoid.map_templates.MapTemplate> nbtTemplates() {
        return Arrays.stream(DevilsPlan.Zone.values()).map(DevilsMaps::nbt).toList();
    }
    private DevilsMaps() { }

    public static String resourceName(DevilsPlan.Zone zone) {
        return switch (zone) { case RY -> "rocketyard"; case RF -> "refinery"; case BL -> "blast"; case SP -> "lair"; };
    }
    /** Offline authoring-grid access for lossless conversion regression; never used by strike generation. */
    public static ZoneTemplate template(DevilsPlan.Zone zone) {
        return TEMPLATES.computeIfAbsent(zone, z -> {
            String name = resourceName(z);
            try (InputStream in = resource(name + ".zone")) { return ZoneTemplate.decode("devils_" + name, in); }
            catch (IOException e) { throw new UncheckedIOException(e); }
        });
    }
    public static CompletableFuture<Void> preloadAsync(net.minecraft.server.MinecraftServer server) {
        var registry = server.registryAccess();
        nbtTemplates = Map.of();
        return CompletableFuture.runAsync(() -> {
            var loaded = new EnumMap<DevilsPlan.Zone, xyz.nucleoid.map_templates.MapTemplate>(DevilsPlan.Zone.class);
            for (var zone : DevilsPlan.Zone.values()) {
                String path = "/data/destiny/map_template/devils_lair/" + resourceName(zone) + ".nbt";
                try (var in = DevilsMaps.class.getResourceAsStream(path)) {
                    if (in == null) throw new FileNotFoundException(path);
                    var value = xyz.nucleoid.map_templates.MapTemplateSerializer.loadFrom(in, registry);
                    if (!value.getBounds().min().equals(DevilsWorldBuild.origin(zone)))
                        throw new IOException("Template origin does not match anchors: " + zone);
                    var size = dimensions(zone);
                    if (!value.getBounds().max().equals(DevilsWorldBuild.origin(zone).offset(size).offset(-1,-1,-1)))
                        throw new IOException("Template size does not match anchors: " + zone);
                    loaded.put(zone, value);
                } catch (IOException e) { throw new UncheckedIOException(path, e); }
            }
            locals();
            nbtTemplates = Map.copyOf(loaded);
        });
    }
    /** Warm generator-owned chunks only: no per-block ServerLevel writes. */
    public static RisingServices.ZoneBuild begin(ServerLevel level, DevilsPlan.Zone zone, BlockPos origin) {
        if (!origin.equals(nbt(zone).getBounds().min())) throw new IllegalArgumentException("Template origin mismatch");
        return new DevilsChunkWarmup(level, nbt(zone).getBounds(), warmupMargin(level.getServer().getPlayerList().getViewDistance()));
    }
    /** View radius plus one column, capped so neighbouring zones (512 blocks apart) never share columns. */
    static int warmupMargin(int viewDistance) { return Math.clamp(viewDistance + 1, 0, 12); }
    public static List<RisingServices.Marker> markers(DevilsPlan.Zone zone, BlockPos origin) {
        Vec3 offset = Vec3.atLowerCornerOf(origin);
        return locals().get(zone).stream().map(m -> new RisingServices.Marker(m.id(), m.pos().add(offset), m.yaw(), m.tags())).toList();
    }
    public static RisingServices.Marker anchor(DevilsPlan.Zone zone, String id, BlockPos origin) {
        return markers(zone, origin).stream().filter(m -> m.id().equals(id)).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Missing Devils Lair anchor " + zone + "/" + id));
    }
    /** Authored ground or flying alternatives. Runtime rechecks collision, occupancy, distance and reachability. */
    public static List<RisingServices.Marker> candidates(DevilsPlan.Zone zone, String lane, BlockPos origin) {
        return markers(zone, origin).stream().filter(m -> lane.equals(m.tags().get("lane"))).toList();
    }
    public static boolean contains(DevilsPlan.Zone zone, BlockPos origin, Vec3 p) {
        var size = dimensions(zone);
        return Double.isFinite(p.x) && Double.isFinite(p.y) && Double.isFinite(p.z)
                && p.x >= origin.getX() && p.x < origin.getX()+size.getX()
                && p.y >= origin.getY() && p.y < origin.getY()+size.getY()
                && p.z >= origin.getZ() && p.z < origin.getZ()+size.getZ();
    }
    private static final Map<DevilsPlan.Zone, BlockPos> DIMENSIONS = new ConcurrentHashMap<>();
    public static BlockPos dimensions(DevilsPlan.Zone zone) {
        return DIMENSIONS.computeIfAbsent(zone, z -> {
            try (var in = resource("markers.json"); var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
                var size = JsonParser.parseReader(reader).getAsJsonObject().getAsJsonObject("zones")
                        .getAsJsonObject(resourceName(z)).getAsJsonArray("size");
                return new BlockPos(size.get(0).getAsInt(), size.get(1).getAsInt(), size.get(2).getAsInt());
            } catch (IOException e) { throw new UncheckedIOException(e); }
        });
    }
    private static InputStream resource(String name) throws IOException {
        InputStream in = DevilsMaps.class.getResourceAsStream(RESOURCE_DIR + name);
        if (in == null) throw new FileNotFoundException(RESOURCE_DIR + name);
        return in;
    }
    private static Map<DevilsPlan.Zone, List<RisingServices.Marker>> locals() {
        var result = localMarkers;
        if (result == null) synchronized (DevilsMaps.class) {
            if (localMarkers == null) try (var in = resource("markers.json"); var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
                localMarkers = parse(reader);
            } catch (IOException e) { throw new UncheckedIOException(e); }
            result = localMarkers;
        }
        return result;
    }
    static Map<DevilsPlan.Zone, List<RisingServices.Marker>> parse(Reader reader) throws IOException {
        try {
            var root = JsonParser.parseReader(reader).getAsJsonObject();
            if (root.get("schema").getAsInt() != 1) throw new IOException("Unsupported strike marker schema");
            var out = new EnumMap<DevilsPlan.Zone,List<RisingServices.Marker>>(DevilsPlan.Zone.class);
            for (var zone : DevilsPlan.Zone.values()) {
                var obj = root.getAsJsonObject("zones").getAsJsonObject(resourceName(zone));
                var size = obj.getAsJsonArray("size");
                int sx = size.get(0).getAsInt(), sy = size.get(1).getAsInt(), sz = size.get(2).getAsInt();
                if (sx < 1 || sy < 1 || sz < 1 || sx > ZoneTemplate.MAX_EDGE || sy > ZoneTemplate.MAX_HEIGHT || sz > ZoneTemplate.MAX_EDGE)
                    throw new IOException("Invalid map dimensions for " + zone);
                var ids = new HashSet<String>(); var list = new ArrayList<RisingServices.Marker>();
                for (var value : obj.getAsJsonArray("markers")) {
                    JsonObject m = value.getAsJsonObject(); String id = m.get("id").getAsString();
                    if (!id.matches("[A-Za-z][A-Za-z0-9_.-]{1,100}") || !ids.add(id)) throw new IOException("Invalid/duplicate anchor " + id);
                    var p = m.getAsJsonArray("pos");
                    Vec3 at = new Vec3(p.get(0).getAsDouble(), p.get(1).getAsDouble(), p.get(2).getAsDouble());
                    float yaw = m.get("yaw").getAsFloat();
                    if (!Double.isFinite(at.x) || !Double.isFinite(at.y) || !Double.isFinite(at.z) || !Float.isFinite(yaw)
                            || at.x < 0 || at.y < 0 || at.z < 0 || at.x >= sx || at.y >= sy || at.z >= sz)
                        throw new IOException("Anchor outside map: " + id);
                    Map<String,String> tags = new LinkedHashMap<>();
                    for (var tag : m.getAsJsonObject("tags").entrySet()) tags.put(tag.getKey(), tag.getValue().getAsString());
                    list.add(new RisingServices.Marker(id, at, yaw, Map.copyOf(tags)));
                }
                if (!ids.contains(zone.name()+".IN")) throw new IOException("Missing arrival anchor " + zone);
                out.put(zone, List.copyOf(list));
            }
            return Map.copyOf(out);
        } catch (RuntimeException e) { throw new IOException("Invalid Devils Lair markers", e); }
    }
}
