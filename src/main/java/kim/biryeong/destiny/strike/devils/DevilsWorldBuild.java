package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.activity.strike.StrikeWorldBuild;
import kim.biryeong.destiny.campaign.RisingServices;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import java.util.function.Function;

/** Devils Lair's four-zone build: the shared {@link StrikeWorldBuild} with this strike's zone origins. */
public final class DevilsWorldBuild extends StrikeWorldBuild<DevilsPlan.Zone> {
    public DevilsWorldBuild(ServerLevel level) { this(z -> DevilsMaps.begin(level, z, origin(z))); }
    DevilsWorldBuild(Function<DevilsPlan.Zone, RisingServices.ZoneBuild> factory) { super(DevilsPlan.Zone.class, factory); }
    public static BlockPos origin(DevilsPlan.Zone zone) { return new BlockPos(256 + zone.ordinal() * 512, 64, 256); }
}
