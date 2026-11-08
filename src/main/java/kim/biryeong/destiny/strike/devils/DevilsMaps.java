package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.activity.strike.StrikeMaps;
import kim.biryeong.destiny.campaign.RisingServices;
import kim.biryeong.destiny.campaign.map.ZoneTemplate;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.Vec3;

import java.io.IOException;
import java.io.Reader;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

/** Devils Lair's map data: the shared {@link StrikeMaps} loader configured with this strike's zones. */
public final class DevilsMaps {
    public static final String RESOURCE_DIR = "/data/destiny/devils_lair/zones/";
    private static final StrikeMaps<DevilsPlan.Zone> MAPS = new StrikeMaps<>(
            "devils_lair", "Devils Lair", "devils_", DevilsPlan.Zone.class, DevilsWorldBuild::origin);
    private DevilsMaps() { }

    public static StrikeMaps<DevilsPlan.Zone> maps() { return MAPS; }
    public static xyz.nucleoid.map_templates.MapTemplate nbt(DevilsPlan.Zone zone) { return MAPS.nbt(zone); }
    public static List<xyz.nucleoid.map_templates.MapTemplate> nbtTemplates() { return MAPS.nbtTemplates(); }
    public static String resourceName(DevilsPlan.Zone zone) { return zone.resourceName(); }
    public static ZoneTemplate template(DevilsPlan.Zone zone) { return MAPS.template(zone); }
    public static CompletableFuture<Void> preloadAsync(net.minecraft.server.MinecraftServer server) { return MAPS.preloadAsync(server); }
    public static RisingServices.ZoneBuild begin(ServerLevel level, DevilsPlan.Zone zone, BlockPos origin) { return MAPS.begin(level, zone, origin); }
    static int warmupMargin(int viewDistance) { return StrikeMaps.warmupMargin(viewDistance); }
    public static List<RisingServices.Marker> markers(DevilsPlan.Zone zone, BlockPos origin) { return MAPS.markers(zone, origin); }
    public static RisingServices.Marker anchor(DevilsPlan.Zone zone, String id, BlockPos origin) { return MAPS.anchor(zone, id, origin); }
    public static List<RisingServices.Marker> candidates(DevilsPlan.Zone zone, String lane, BlockPos origin) { return MAPS.candidates(zone, lane, origin); }
    public static boolean contains(DevilsPlan.Zone zone, BlockPos origin, Vec3 p) { return MAPS.contains(zone, origin, p); }
    public static BlockPos dimensions(DevilsPlan.Zone zone) { return MAPS.dimensions(zone); }
    static Map<DevilsPlan.Zone, List<RisingServices.Marker>> parse(Reader reader) throws IOException { return MAPS.parse(reader); }
}
