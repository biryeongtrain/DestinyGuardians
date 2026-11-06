package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.activity.ActivityAttemptStats;
import kim.biryeong.destiny.combat.CombatDamageEvents;
import net.minecraft.server.level.ServerPlayer;
import java.util.*;

/** Activity adapter: identity/world/current actor generation are checked before feeding common attempt facts. */
final class DevilsAttemptStats implements AutoCloseable {
    private final DevilsSession session;
    private final Map<UUID, String> names = new LinkedHashMap<>();
    private final ActivityAttemptStats stats;
    private final AutoCloseable subscription;
    private boolean closed;
    DevilsAttemptStats(DevilsSession session, List<ServerPlayer> initial) {
        this.session = session; stats = new ActivityAttemptStats(session.id());
        for (var player : initial) names.put(player.getUUID(), player.getScoreboardName());
        subscription = CombatDamageEvents.subscribe(this::applied);
    }
    void scope() {
        if (closed || !session.running()) return;
        Set<UUID> present = new HashSet<>(); for (var player : session.players()) present.add(player.getUUID());
        var members = names.entrySet().stream().filter(e -> session.member(e.getKey()))
                .map(e -> new ActivityAttemptStats.Member(e.getKey(), e.getValue(), present.contains(e.getKey())
                        ? ActivityAttemptStats.Presence.PRESENT : ActivityAttemptStats.Presence.DISCONNECTED)).toList();
        if (!members.isEmpty()) stats.reset(session.director().generation(), checkpoint(session.director().phase().zone()), members);
        for (UUID id : names.keySet()) stats.presence(id, !session.member(id) ? ActivityAttemptStats.Presence.LEFT
                : present.contains(id) ? ActivityAttemptStats.Presence.PRESENT : ActivityAttemptStats.Presence.DISCONNECTED);
    }
    private static String checkpoint(DevilsPlan.Zone zone) {
        return switch (zone) { case RY -> "로켓 야드"; case RF -> "정제소"; case BL -> "발사장"; case SP -> "세픽스 프라임"; };
    }
    private void applied(CombatDamageEvents.Applied event) {
        if (closed || !(event.recipient() instanceof DevilsMob mob) || !session.acceptStats(event, mob)) return;
        stats.damage(stats.token(), event.source().getUUID(), mob.getUUID(), event.damage(), event.killed(), mob.kind().boss());
    }
    void down(DevilsRecovery.DownToken token) {
        if (!closed && token.activity().equals(session.id()) && token.generation() == session.director().generation())
            stats.death(stats.token(), token.player(), token.life());
    }
    ActivityAttemptStats.Snapshot freeze() { scope(); return stats.freeze(stats.token()); }
    String status() {
        var snapshot = stats.snapshot();
        return " stats={generation=" + snapshot.token().generation() + ",checkpoint=" + snapshot.checkpoint()
                + ",attempt=" + snapshot.attempt() + ",frozen=" + stats.frozen() + ",rows=" + snapshot.rows() + "}";
    }
    ActivityAttemptStats.Snapshot snapshot() { return stats.snapshot(); }
    @Override public void close() {
        if (closed) return; closed = true; stats.close();
        try { subscription.close(); } catch (Exception failure) { session.problem("Stats subscription close: " + failure); }
    }
}
