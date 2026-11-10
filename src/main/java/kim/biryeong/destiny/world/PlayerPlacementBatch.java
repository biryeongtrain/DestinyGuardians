package kim.biryeong.destiny.world;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.AABB;

import java.util.IdentityHashMap;
import java.util.List;
import java.util.Optional;
import java.util.function.Predicate;

/** Per-call collision planning for players that will all move after every destination is validated.
 * Terrain, hazards and destination reservations remain the caller's responsibility.
 */
public final class PlayerPlacementBatch {
    private final ServerLevel target;
    private final IdentityHashMap<ServerPlayer, Object> connections = new IdentityHashMap<>();

    private PlayerPlacementBatch(ServerLevel target, List<ServerPlayer> players) {
        this.target = target;
        for (var player : players) connections.put(player, player.connection);
    }

    /** Captures exact current entities and connections, never UUID-only occupancy exemptions. */
    public static Optional<PlayerPlacementBatch> create(ServerLevel target, List<ServerPlayer> players) {
        thread(target);
        var batch = new PlayerPlacementBatch(target, players);
        return batch.connections.size() == players.size() && batch.current() ? Optional.of(batch) : Optional.empty();
    }

    public boolean current() {
        thread(target);
        var server = target.getServer();
        for (var entry : connections.entrySet()) {
            var player = entry.getKey();
            if (player.level().getServer() != server || player.isRemoved() || player.hasDisconnected()
                    || player.connection == null || player.connection != entry.getValue()
                    || player.connection.getPlayer() != player
                    || server.getPlayerList().getPlayer(player.getUUID()) != player) return false;
        }
        return true;
    }

    /** Retains the adapter's entity-collision policy, excluding only this batch's exact movers. */
    public boolean blocked(ServerPlayer player, AABB body, Predicate<Entity> blocker) {
        thread(target);
        if (!connections.containsKey(player) || !current()) return true;
        return !target.getEntities(player, body,
                entity -> !connections.containsKey(entity) && blocker.test(entity)).isEmpty();
    }

    private static void thread(ServerLevel level) {
        if (!level.getServer().isSameThread()) throw new IllegalStateException("Player placement requires server thread");
    }
}
