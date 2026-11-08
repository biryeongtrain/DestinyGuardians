package kim.biryeong.destiny.strike.exodus;

import kim.biryeong.destiny.activity.strike.StrikeMaps;
import kim.biryeong.destiny.campaign.RisingServices;
import kim.biryeong.destiny.world.template.TemplateChunkWarmup;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.Vec3;
import xyz.nucleoid.map_templates.BlockBounds;

/**
 * Exodus Crash's map data: one 1115x231x1680 section-NBT template. The shared {@link StrikeMaps} loads and checks it;
 * only the start of the walk is generated ahead of the fireteam, the rest follows the players' view distance.
 */
public final class ExodusMaps {
    public static final BlockPos ORIGIN = new BlockPos(256, 32, 256);
    /** Chunk columns prepared around the arrival pad before admission. */
    private static final int START_RADIUS = 96;
    private static final StrikeMaps<ExodusPlan.Zone> MAPS = new StrikeMaps<>(
            "exodus_crash", "Exodus Crash", "exodus_", ExodusPlan.Zone.class, z -> ORIGIN);
    private ExodusMaps() { }

    public static StrikeMaps<ExodusPlan.Zone> maps() { return MAPS; }
    public static BlockPos dimensions() { return MAPS.dimensions(ExodusPlan.Zone.WORLD); }
    public static RisingServices.Marker anchor(String id) { return MAPS.anchor(ExodusPlan.Zone.WORLD, id, ORIGIN); }
    public static java.util.List<RisingServices.Marker> markers() { return MAPS.markers(ExodusPlan.Zone.WORLD, ORIGIN); }
    public static boolean contains(Vec3 p) { return MAPS.contains(ExodusPlan.Zone.WORLD, ORIGIN, p); }
    public static Vec3 world(Vec3 local) { return local.add(ORIGIN.getX(), ORIGIN.getY(), ORIGIN.getZ()); }
    public static BlockPos world(BlockPos local) { return local.offset(ORIGIN); }

    /** Warm only the chunks around the start. The full map is 7,350 columns; the walk generates the rest on demand. */
    public static RisingServices.ZoneBuild begin(ServerLevel level, ExodusPlan.Zone zone) {
        var at = BlockPos.containing(anchor("WORLD.IN").pos());
        return new TemplateChunkWarmup(level, BlockBounds.of(at.offset(-START_RADIUS, 0, -START_RADIUS),
                at.offset(START_RADIUS, 0, START_RADIUS)), 0);
    }
}
