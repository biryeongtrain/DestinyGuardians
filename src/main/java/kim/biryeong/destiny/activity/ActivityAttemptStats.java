package kim.biryeong.destiny.activity;

import java.util.*;

/** Actual combat facts for one activity/checkpoint attempt; never reads permanent player statistics. */
public final class ActivityAttemptStats implements AutoCloseable {
    public enum Presence { PRESENT, DISCONNECTED, LEFT }
    public record Member(UUID id, String name, Presence presence) { }
    public record Token(UUID activity, long generation, long epoch) { }
    public record Row(UUID player, String name, Presence presence, long kills, double damage, double bossDamage, long deaths) { }
    public record Snapshot(Token token, String checkpoint, int attempt, List<Row> rows) {
        public Snapshot { rows = List.copyOf(rows); }
    }
    private static final class Mutable {
        final UUID id; final String name; Presence presence;
        long kills, deaths; double damage, bossDamage;
        Mutable(Member member) { id = member.id(); name = member.name(); presence = member.presence(); }
        Row row() { return new Row(id, name, presence, kills, damage, bossDamage, deaths); }
    }
    private record Death(UUID player, long life) { }
    private final UUID activity;
    private final Map<UUID, Mutable> rows = new LinkedHashMap<>();
    private final Set<UUID> killed = new HashSet<>();
    private final Set<Death> deaths = new HashSet<>();
    private long generation, epoch;
    private String checkpoint = "";
    private int attempt;
    private boolean closed;
    private Snapshot frozen;
    public ActivityAttemptStats(UUID activity) { this.activity = Objects.requireNonNull(activity); }
    public boolean reset(long nextGeneration, String checkpoint, Collection<Member> members) {
        Objects.requireNonNull(checkpoint);
        if (closed || nextGeneration <= 0 || nextGeneration < generation || members.isEmpty()
                || nextGeneration == generation && this.checkpoint.equals(checkpoint)) return false;
        var next = new LinkedHashMap<UUID, Mutable>();
        for (var member : members) {
            Objects.requireNonNull(member.id()); Objects.requireNonNull(member.name()); Objects.requireNonNull(member.presence());
            if (next.putIfAbsent(member.id(), new Mutable(member)) != null) throw new IllegalArgumentException("Duplicate stats member");
        }
        attempt = this.checkpoint.equals(checkpoint) ? attempt + 1 : 1;
        this.checkpoint = checkpoint; generation = nextGeneration; epoch++;
        rows.clear(); rows.putAll(next); killed.clear(); deaths.clear(); frozen = null;
        return true;
    }
    public Token token() { return new Token(activity, generation, epoch); }
    private boolean current(Token token) { return !closed && generation > 0 && token != null && token.equals(token()); }
    public boolean damage(Token token, UUID player, UUID victim, double applied, boolean finalBlow, boolean boss) {
        var row = rows.get(player);
        if (!current(token) || frozen != null || row == null || row.presence != Presence.PRESENT
                || victim == null || !Double.isFinite(applied) || applied <= 0) return false;
        row.damage += applied; if (boss) row.bossDamage += applied;
        if (finalBlow && killed.add(victim)) row.kills++;
        return true;
    }
    /** Actual activity down life token, not a polling count or a lifetime Minecraft death statistic. */
    public boolean death(Token token, UUID player, long life) {
        var row = rows.get(player);
        if (!current(token) || frozen != null || row == null || life <= 0 || !deaths.add(new Death(player, life))) return false;
        row.deaths++; return true;
    }
    public void presence(UUID player, Presence presence) {
        if (closed || frozen != null) return;
        var row = rows.get(player); if (row != null) row.presence = Objects.requireNonNull(presence);
    }
    /** Freeze exactly once at committed wipe; departures afterwards cannot rewrite that results table. */
    public Snapshot freeze(Token token) {
        if (!current(token)) return null;
        if (frozen == null) frozen = snapshot();
        return frozen;
    }
    public Snapshot snapshot() {
        return frozen != null ? frozen : new Snapshot(token(), checkpoint, attempt, rows.values().stream().map(Mutable::row).toList());
    }
    public boolean frozen() { return frozen != null; }
    @Override public void close() { closed = true; }
}
