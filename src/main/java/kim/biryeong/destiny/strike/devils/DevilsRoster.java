package kim.biryeong.destiny.strike.devils;

import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

/** Fixed one-to-three-member identity and reconnect policy; never changes encounter tuning. Server-thread owned. */
public final class DevilsRoster {
    public static final long RECONNECT_TICKS = 2400;
    public enum Join { ACCEPTED, UNKNOWN, EXPIRED }
    public record Member(UUID id, boolean connected, boolean ready, boolean down, boolean expired) { }
    private static final class Slot {
        final UUID id;
        boolean connected = true, ready, down, expired;
        long disconnectedAt = -1;
        Slot(UUID id) { this.id = id; }
        Member snapshot() { return new Member(id, connected, ready, down, expired); }
    }
    private final Map<UUID, Slot> members = new LinkedHashMap<>();
    private long allOfflineAt = -1;

    public DevilsRoster(Collection<UUID> ids) {
        Objects.requireNonNull(ids);
        for (UUID id : ids) {
            Objects.requireNonNull(id);
            if (members.putIfAbsent(id, new Slot(id)) != null) throw new IllegalArgumentException("Duplicate participant");
        }
        if (members.size() < DevilsPlan.MIN_PLAYERS || members.size() > DevilsPlan.PLAYERS) throw new IllegalArgumentException("The Devils' Lair requires one to three participants");
    }
    public boolean contains(UUID id) { return members.containsKey(id); }
    public List<Member> members() { return members.values().stream().map(Slot::snapshot).toList(); }
    public int connected() { return (int) members.values().stream().filter(s -> s.connected).count(); }
    public int living() { return (int) members.values().stream().filter(s -> s.connected && s.ready && !s.down).count(); }
    public boolean allReady() { return members.values().stream().allMatch(s -> s.connected && s.ready && !s.expired); }
    public void ready(UUID id, boolean ready) { var s = require(id); s.ready = ready && s.connected; }
    public void down(UUID id, boolean down) { require(id).down = down; }
    public void disconnected(UUID id, long now) {
        var s = require(id);
        if (!s.connected) return; // duplicate disconnect must not extend the grace window
        s.connected = false;
        s.ready = false;
        s.disconnectedAt = now;
        if (connected() == 0 && allOfflineAt < 0) allOfflineAt = now;
    }
    public Join rejoin(UUID id, long now) {
        var s = members.get(id);
        if (s == null) return Join.UNKNOWN;
        if (s.expired || !s.connected && now - s.disconnectedAt >= RECONNECT_TICKS) {
            s.expired = true;
            return Join.EXPIRED;
        }
        if (!s.connected) { s.connected = true; s.ready = false; s.disconnectedAt = -1; }
        allOfflineAt = -1;
        return Join.ACCEPTED;
    }
    public void expire(long now) {
        for (var s : members.values()) if (!s.connected && now - s.disconnectedAt >= RECONNECT_TICKS) s.expired = true;
    }
    public boolean abandoned(long now) { return allOfflineAt >= 0 && now - allOfflineAt >= RECONNECT_TICKS; }
    private Slot require(UUID id) {
        var s = members.get(id);
        if (s == null) throw new IllegalArgumentException("Not a strike participant: " + id);
        return s;
    }
}
