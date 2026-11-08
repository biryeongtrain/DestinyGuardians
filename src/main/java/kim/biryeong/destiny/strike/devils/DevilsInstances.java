package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.activity.strike.StrikeInstances;
import net.minecraft.server.MinecraftServer;

/** Devils Lair's run worlds: the shared {@link StrikeInstances} with this strike's roster limits and map generator. */
public final class DevilsInstances extends StrikeInstances {
    public DevilsInstances(MinecraftServer server, int capacity) {
        super(server, "devils_lair", capacity, DevilsPlan.MIN_PLAYERS, DevilsPlan.PLAYERS,
                () -> new DevilsTemplateGenerator(server, DevilsMaps.nbtTemplates()));
    }
}
