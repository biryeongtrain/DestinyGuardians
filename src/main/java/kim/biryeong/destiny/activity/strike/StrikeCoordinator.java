package kim.biryeong.destiny.activity.strike;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import java.util.List;

/**
 * What the rest of the mod needs to know about one strike, without knowing which strike it is: the finder launches it,
 * the personal-exit command leaves it, and combat, abilities and other activities ask whether a player may act.
 * One coordinator owns all runs (sessions, instances, world construction) of one strike; implementations keep their
 * own per-run state and never share it with another strike.
 */
public interface StrikeCoordinator {
    /** Finder listing. Images are resource-pack GUI sprite paths relative to {@code destiny:gui/}. */
    record Info(String id, String name, String type, String description, String banner, String icon,
                int minPlayers, int maxPlayers, int order) {
        public Info {
            if (id == null || id.isBlank() || name == null || type == null || description == null
                    || banner == null || icon == null || minPlayers < 1 || maxPlayers < minPlayers)
                throw new IllegalArgumentException("Invalid strike listing");
        }
    }
    Info info();
    /** Null when this fireteam may launch now, otherwise a Korean reason. Must not mutate anything. */
    String check(List<ServerPlayer> fireteam);
    /** Start a run for the whole fireteam. Null on success, otherwise a Korean reason. */
    String start(List<ServerPlayer> fireteam);
    /** The run has placed this player in its world and owns their presentation from here. */
    boolean entered(ServerPlayer player);
    /** The player belongs to a run of this strike (queued, preparing or running). */
    boolean participating(ServerPlayer player);
    /** Preparation progress 0..1 for the launch loading screen, or negative when unknown. */
    float loadProgress(ServerPlayer player);
    /** Opaque identity of the player's current run, or null; compared by identity when leaving. */
    Object participationToken(ServerPlayer player);
    boolean leave(ServerPlayer player, Object expected);
    /** The player's run is in its opening briefing. */
    boolean briefing(ServerPlayer player);
    /** False when this strike forbids the player to fight or use abilities right now. True outside the strike. */
    boolean allows(ServerPlayer player);
    /** The level is one of this strike's run worlds. */
    boolean isLevel(Level level);
}
