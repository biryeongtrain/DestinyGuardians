package kim.biryeong.destiny.campaign.map;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.campaign.RisingServices;
import kim.biryeong.destiny.campaign.GuardianRisesInstances;
import kim.biryeong.destiny.world.template.NbtTemplateChunkGenerator;
import net.minecraft.server.MinecraftServer;
import xyz.nucleoid.map_templates.BlockBounds;
import xyz.nucleoid.map_templates.MapTemplate;
import xyz.nucleoid.map_templates.MapTemplateSerializer;
import java.util.concurrent.CompletableFuture;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.Vec3;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.Pattern;

/**
 * {@link RisingServices.Zones} over the bundled voxel zones (gateway, breach, divide, dock13) and their
 * zone-local markers ({@code data/destiny/guardian_rises/zones/markers.json}).
 */
public final class RisingZones implements RisingServices.Zones {
    public static final String MARKERS_RESOURCE = ZoneTemplate.RESOURCE_DIR + "markers.json";
    /** Marker id grammar from {@link RisingServices.Marker}. */
    static final Pattern ID = Pattern.compile(
            "spawn\\.player|ghost\\.scan|checkpoint\\.[a-z0-9_]+|trigger\\.[a-z0-9_]+|enemy\\.[a-z0-9_]+\\.[0-9]+"
                    + "|prop\\.[a-z0-9_]+|exit\\.[a-z0-9_]+|light\\.[a-z0-9_]+");
    static final Set<String> ENEMY_KINDS = Set.of("dreg", "vandal", "captain", "shank", "walker");
    private static final RisingZones INSTANCE = new RisingZones();
    private static volatile Map<RisingServices.Zone, LocalZone> markers;

    /** Zone-local marker set and the zone's block size. */
    record LocalZone(int sizeX, int sizeY, int sizeZ, List<RisingServices.Marker> markers) {}

    private RisingZones() {}

    /** Registers the zone service; NBT loading is owned by each server's instance manager. */
    public static void init() {
        RisingServices.register(INSTANCE);
    }

    @Override public RisingServices.ZoneBuild begin(ServerLevel level, RisingServices.Zone zone, BlockPos origin) {
        var bounds = bounds(zone);
        if (!origin.equals(bounds.min())) throw new IllegalArgumentException("Guardian Rises template origin mismatch");
        if (!(level.getChunkSource().getGenerator() instanceof NbtTemplateChunkGenerator generator)
                || generator.templates().stream().noneMatch(t -> t.getBounds().min().equals(bounds.min())
                        && t.getBounds().max().equals(bounds.max())))
            throw new IllegalStateException("Guardian Rises requires its NBT chunk generator");
        // Assignment/metadata validation only. Never enumerate the zone bounds or view-distance margins.
        return new RisingServices.ZoneBuild() {
            private boolean cancelled;
            @Override public boolean step(long budget) { return !cancelled; }
            @Override public double progress() { return cancelled ? 0 : 1; }
            @Override public void cancel() { cancelled = true; }
        };
    }

    public static BlockBounds bounds(RisingServices.Zone zone) {
        var local = localMarkers().get(zone);
        var origin = GuardianRisesInstances.origin(zone);
        return new BlockBounds(origin, origin.offset(local.sizeX() - 1, local.sizeY() - 1, local.sizeZ() - 1));
    }

    /** One immutable template set per instance manager, shared by its worlds, loaded without server-thread IO. */
    public static CompletableFuture<List<MapTemplate>> preloadAsync(MinecraftServer server) {
        var registries = server.registryAccess();
        return CompletableFuture.supplyAsync(() -> {
            var loaded = new ArrayList<MapTemplate>();
            for (var zone : RisingServices.Zone.values()) {
                String path = "/data/destiny/map_template/guardian_rises/" + ZoneTemplate.resourceName(zone) + ".nbt";
                try (var in = RisingZones.class.getResourceAsStream(path)) {
                    if (in == null) throw new IOException("Missing " + path);
                    var template = MapTemplateSerializer.loadFrom(in, registries);
                    var bounds = bounds(zone);
                    if (!template.getBounds().min().equals(bounds.min()) || !template.getBounds().max().equals(bounds.max()))
                        throw new IOException("Guardian Rises NBT bounds do not match markers: " + zone);
                    loaded.add(template);
                } catch (IOException e) { throw new UncheckedIOException(path, e); }
            }
            return List.copyOf(loaded);
        });
    }

    @Override public RisingServices.Markers markers(RisingServices.Zone zone, BlockPos origin) {
        List<RisingServices.Marker> local = localMarkers().get(zone).markers();
        List<RisingServices.Marker> world = new ArrayList<>(local.size());
        Vec3 o = Vec3.atLowerCornerOf(origin);
        for (RisingServices.Marker m : local) world.add(new RisingServices.Marker(m.id(), m.pos().add(o), m.yaw(), m.tags()));
        List<RisingServices.Marker> view = List.copyOf(world);
        return () -> view;
    }

    static Map<RisingServices.Zone, LocalZone> localMarkers() {
        Map<RisingServices.Zone, LocalZone> m = markers;
        if (m == null) {
            synchronized (RisingZones.class) {
                if (markers == null) {
                    try (InputStream in = RisingZones.class.getResourceAsStream(MARKERS_RESOURCE)) {
                        if (in == null) throw new IOException("Missing " + MARKERS_RESOURCE);
                        markers = parse(new InputStreamReader(in, StandardCharsets.UTF_8));
                    } catch (IOException e) {
                        throw new UncheckedIOException(e);
                    }
                }
                m = markers;
            }
        }
        return m;
    }

    /** Parses and validates markers.json: grammar, enemy kinds, positions inside each zone. */
    static Map<RisingServices.Zone, LocalZone> parse(Reader reader) throws IOException {
        try {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            if (root.get("schema").getAsInt() != 1) throw new IOException("Unsupported markers schema");
            JsonObject zones = root.getAsJsonObject("zones");
            Map<RisingServices.Zone, LocalZone> out = new EnumMap<>(RisingServices.Zone.class);
            for (RisingServices.Zone zone : RisingServices.Zone.values()) {
                JsonObject z = zones.getAsJsonObject(ZoneTemplate.resourceName(zone));
                if (z == null) throw new IOException("No markers for zone " + zone);
                var size = z.getAsJsonArray("size");
                int sx = size.get(0).getAsInt(), sy = size.get(1).getAsInt(), sz = size.get(2).getAsInt();
                List<RisingServices.Marker> list = new ArrayList<>();
                Set<String> ids = new HashSet<>();
                for (var e : z.getAsJsonArray("markers")) {
                    JsonObject m = e.getAsJsonObject();
                    String id = m.get("id").getAsString();
                    if (!ID.matcher(id).matches()) throw new IOException("Bad marker id " + id + " in " + zone);
                    if (!ids.add(id)) throw new IOException("Duplicate marker " + id + " in " + zone);
                    var p = m.getAsJsonArray("pos");
                    Vec3 pos = new Vec3(p.get(0).getAsDouble(), p.get(1).getAsDouble(), p.get(2).getAsDouble());
                    if (pos.x < 0 || pos.y < -1 || pos.z < 0 || pos.x > sx || pos.y > sy + 64 || pos.z > sz)
                        throw new IOException("Marker " + id + " outside zone " + zone);
                    Map<String, String> tags = new LinkedHashMap<>();
                    if (m.has("tags")) for (var t : m.getAsJsonObject("tags").entrySet()) tags.put(t.getKey(), t.getValue().getAsString());
                    if (id.startsWith("enemy.") && !ENEMY_KINDS.contains(tags.get("kind")))
                        throw new IOException("Enemy marker " + id + " needs kind=" + ENEMY_KINDS);
                    list.add(new RisingServices.Marker(id, pos, m.get("yaw").getAsFloat(), tags));
                }
                if (!ids.contains("spawn.player")) throw new IOException("Zone " + zone + " has no spawn.player");
                out.put(zone, new LocalZone(sx, sy, sz, List.copyOf(list)));
            }
            return Collections.unmodifiableMap(out);
        } catch (RuntimeException e) {
            throw new IOException("Invalid " + MARKERS_RESOURCE, e);
        }
    }
}
