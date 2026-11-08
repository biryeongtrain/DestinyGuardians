package kim.biryeong.destiny.activity.strike;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * Registry of the strikes and the questions other systems ask of all of them at once ("is this player in any strike",
 * "may this player fight"). It holds coordinators only; every run's state lives in its own coordinator.
 */
public final class Strikes {
    private static final List<StrikeCoordinator> ALL = new CopyOnWriteArrayList<>();
    private Strikes() { }

    public static void register(StrikeCoordinator coordinator) {
        Objects.requireNonNull(coordinator);
        for (var existing : ALL)
            if (existing == coordinator || existing.info().id().equals(coordinator.info().id()))
                throw new IllegalStateException("Strike already registered: " + coordinator.info().id());
        ALL.add(coordinator);
    }
    public static List<StrikeCoordinator> all() { return List.copyOf(ALL); }
    public static boolean participating(ServerPlayer p) { return ALL.stream().anyMatch(s -> s.participating(p)); }
    public static boolean briefing(ServerPlayer p) { return ALL.stream().anyMatch(s -> s.briefing(p)); }
    public static boolean allows(ServerPlayer p) { return ALL.stream().allMatch(s -> s.allows(p)); }
    public static boolean isLevel(Level level) { return ALL.stream().anyMatch(s -> s.isLevel(level)); }
}
