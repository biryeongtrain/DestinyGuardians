package kim.biryeong.destiny.crucible;

import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;

/**
 * Single-session Control rules; call exclusively on the server thread.
 * Runtime owns locations, connection validity, spawning and authoritative death events.
 * Each tick call advances one server tick, including waiting/results; never use wall time.
 *
 * Local policies: tied timer/score limit is a draw, no overtime; loss of an entire team
 * during PLAYING pauses scoring, captures and the match clock for forfeitGraceTicks
 * consecutive ticks. Rejoining either way to restore both teams cancels that countdown;
 * expiry forfeits to the remaining team. INTRO instead returns to WAITING. Empty
 * membership resets everything except monotonic tick/life/round identifiers.
 * Joins fill the smaller team (ALPHA on ties); reconnect prefers its old team only
 * when that does not worsen balance. Existing players never switch during PLAYING.
 * At the next round, insertion-order alternating assignment restores team balance.
 *
 * Capture is two stages for enemy zones: neutralize, then capture. Both teams present
 * freezes progress regardless of headcount. Empty zones lose partial progress;
 * defenders clear enemy progress; changing the attacking team starts fresh.
 * Multiple occupants do not accelerate capture. These timings and interruption rules
 * are local tuning, not measured Destiny mechanics. Capture reward is once per team,
 * not per occupant, and neutralization gives no reward. No passive zone scoring.
 */
public final class ControlMatch {
    public enum Team { ALPHA, BRAVO }
    public enum Phase { WAITING, INTRO, PLAYING, RESULTS }
    public enum EndReason { SCORE_LIMIT, TIME_LIMIT, FORFEIT }
    public static final List<String> ZONE_IDS = List.of("A", "B", "C");

    public record Config(int scoreLimit, int matchTicks, int introTicks, int resultTicks,
                         int neutralizeTicks, int captureTicks, int captureReward, int forfeitGraceTicks) {
        public Config {
            if (scoreLimit <= 0 || matchTicks <= 0 || introTicks < 0 || resultTicks < 0
                    || neutralizeTicks <= 0 || captureTicks <= 0 || captureReward < 0
                    || forfeitGraceTicks <= 0) {
                throw new IllegalArgumentException("Invalid Control timing/scoring configuration");
            }
        }
        /**
         * Bungie Activities / Control: capture +1 and winning score 150 (source supplied
         * and confirmed by the integration coordinator):
         * https://help.bungie.net/hc/en-us/articles/360048720992-Destiny-2-Activities
         * Local tuning at 20 TPS: ten-minute active clock; five seconds EACH for
         * neutralization/capture; 30-second forfeit grace; ten-second results.
         * Intro: 400 ticks covering five-second map view + 14.83-second source animation.
         */
        public static Config defaults() {
            return new Config(150, 10 * 60 * 20, 400, 200, 100, 100, 1, 600);
        }
    }

    /** Null owner/capturingTeam means neutral/idle. Progress is 0..1 for the current stage. */
    public record ZoneSnapshot(Team owner, double progress, Team capturingTeam,
                               boolean contested, int progressTicks, int requiredTicks) { }
    /** Null winner with a non-null endReason is a draw; otherwise no result yet. */
    public record Snapshot(Phase phase, long tick, long round, int phaseTicks,
                           int remainingTicks, Map<UUID, Team> members, Map<Team, Integer> scores,
                           Map<String, ZoneSnapshot> zones, Team winner, EndReason endReason,
                           boolean paused, int forfeitTicks, int forfeitRemainingTicks) {
        public Snapshot {
            members = Map.copyOf(members);
            scores = Map.copyOf(scores);
            zones = Map.copyOf(zones);
        }
    }

    private static final class Zone {
        Team owner;
        Team capturing;
        int progress;
        boolean contested;
        void clearProgress() { capturing = null; progress = 0; }
    }

    private final Config config;
    private final Map<UUID, Team> members = new LinkedHashMap<>();
    private final Map<UUID, Team> previousTeams = new HashMap<>();
    private final Map<UUID, Long> lives = new HashMap<>();
    private final Set<UUID> dead = new HashSet<>();
    private final Map<String, Zone> zones = new LinkedHashMap<>();
    private final EnumMap<Team, Integer> scores = new EnumMap<>(Team.class);
    private Phase phase = Phase.WAITING;
    private long tick;
    private long round;
    private long nextLife;
    private int phaseTicks;
    private int forfeitTicks;
    private Team winner;
    private EndReason endReason;

    public ControlMatch() { this(Config.defaults()); }
    public ControlMatch(Config config) {
        this.config = Objects.requireNonNull(config, "config");
        resetRound();
    }
    public Config config() { return config; }
    public Phase phase() { return phase; }
    public Team team(UUID player) { return members.get(player); }
    public Map<UUID, Team> members() {
        return Collections.unmodifiableMap(new LinkedHashMap<>(members));
    }

    /** Idempotent; join opens a new life only for a previously absent member. */
    public Team join(UUID player) {
        Objects.requireNonNull(player, "player");
        if (members.containsKey(player)) return members.get(player);
        int alpha = count(Team.ALPHA), bravo = count(Team.BRAVO);
        Team old = previousTeams.get(player);
        Team assigned = alpha <= bravo ? Team.ALPHA : Team.BRAVO;
        if (old != null && count(old) <= count(opponent(old))) assigned = old;
        members.put(player, assigned);
        lives.put(player, ++nextLife);
        dead.remove(player);
        if (bothTeamsPresent()) forfeitTicks = 0;
        return assigned;
    }

    public boolean leave(UUID player) {
        Team removed = members.remove(player);
        if (removed == null) return false;
        previousTeams.put(player, removed);
        lives.remove(player);
        dead.remove(player);
        if (members.isEmpty()) resetRound();
        else if (!bothTeamsPresent() && phase == Phase.INTRO) resetRound();
        return true;
    }

    /** -1 for nonmembers. Capture this token when the runtime observes a death. */
    public long life(UUID player) { return lives.getOrDefault(player, -1L); }
    public boolean alive(UUID player) { return members.containsKey(player) && !dead.contains(player); }

    /** Call after an actual respawn; duplicate notifications do not renew a living player's token. */
    public boolean respawn(UUID player) {
        if (phase != Phase.PLAYING || !members.containsKey(player) || !dead.remove(player)) return false;
        lives.put(player, ++nextLife);
        return true;
    }

    /**
     * Convenience for synchronous death delivery. Runtime must not replay this overload
     * after respawn; use the life-token overload for queued/repeated callbacks.
     * Null killer records environmental death without score. Friendly/self deaths also
     * consume the victim life without points. Nonmember killers/victims are rejected.
     * Dead member killers may score delayed projectiles/trades; runtime validates attribution.
     * During grace valid deaths still consume a life, but award no score.
     */
    public int kill(UUID killer, UUID victim) { return kill(killer, victim, life(victim)); }
    public int kill(UUID killer, UUID victim, long victimLife) {
        if (phase != Phase.PLAYING || !members.containsKey(victim)
                || (killer != null && !members.containsKey(killer))
                || victimLife != life(victim) || !dead.add(victim)) return 0;
        if (paused()) return 0;
        Team attacking = members.get(killer);
        if (attacking == null || attacking == members.get(victim)) return 0;
        int points = Math.max(1, ownedZones(attacking));
        addScore(attacking, points);
        checkScoreLimit();
        return points;
    }

    /** True immediately on team loss; runtime can freeze combat while keeping respawns enabled. */
    public boolean paused() { return phase == Phase.PLAYING && !bothTeamsPresent(); }

    /** Runtime supplies only alive, in-world occupants; membership/death are filtered again. */
    public void tick(Map<String, Set<UUID>> occupants) {
        Objects.requireNonNull(occupants, "occupants");
        tick++;
        switch (phase) {
            case WAITING -> {
                if (bothTeamsPresent()) startRound();
            }
            case INTRO -> {
                if (++phaseTicks >= config.introTicks()) enterPlaying();
            }
            case PLAYING -> {
                if (paused()) {
                    if (++forfeitTicks >= config.forfeitGraceTicks()) {
                        finish(count(Team.ALPHA) > 0 ? Team.ALPHA : Team.BRAVO, EndReason.FORFEIT);
                    }
                    return;
                }
                // Resolve every zone before checking scores so A/B/C iteration cannot decide ties.
                for (String id : ZONE_IDS) updateZone(zones.get(id), occupants.get(id));
                phaseTicks++;
                checkScoreLimit();
                if (phase == Phase.PLAYING && phaseTicks >= config.matchTicks()) {
                    finish(leadingTeam(), EndReason.TIME_LIMIT);
                }
            }
            case RESULTS -> {
                if (++phaseTicks >= config.resultTicks()) resetRound();
            }
        }
    }

    public int ownedZones(Team team) {
        Objects.requireNonNull(team, "team");
        return (int) zones.values().stream().filter(z -> z.owner == team).count();
    }

    public Snapshot snapshot() {
        Map<String, ZoneSnapshot> copy = new LinkedHashMap<>();
        zones.forEach((id, zone) -> {
            int required = zone.owner == null ? config.captureTicks() : config.neutralizeTicks();
            copy.put(id, new ZoneSnapshot(zone.owner, (double) zone.progress / required,
                    zone.capturing, zone.contested, zone.progress, required));
        });
        int remaining = switch (phase) {
            case WAITING -> 0;
            case INTRO -> Math.max(0, config.introTicks() - phaseTicks);
            case PLAYING -> Math.max(0, config.matchTicks() - phaseTicks);
            case RESULTS -> Math.max(0, config.resultTicks() - phaseTicks);
        };
        return new Snapshot(phase, tick, round, phaseTicks, remaining,
                members, scores, copy, winner, endReason, paused(), forfeitTicks,
                paused() ? Math.max(0, config.forfeitGraceTicks() - forfeitTicks) : 0);
    }

    private void updateZone(Zone zone, Set<UUID> occupants) {
        boolean alpha = false, bravo = false;
        if (occupants != null) for (UUID player : occupants) {
            if (!alive(player)) continue;
            Team team = members.get(player);
            alpha |= team == Team.ALPHA;
            bravo |= team == Team.BRAVO;
        }
        zone.contested = alpha && bravo;
        if (zone.contested) return;
        Team present = alpha ? Team.ALPHA : bravo ? Team.BRAVO : null;
        if (present == null || present == zone.owner) {
            zone.clearProgress();
            return;
        }
        if (zone.capturing != present) {
            zone.clearProgress();
            zone.capturing = present;
        }
        int required = zone.owner == null ? config.captureTicks() : config.neutralizeTicks();
        if (++zone.progress >= required) {
            if (zone.owner != null) {
                zone.owner = null;
                zone.progress = 0;
                // Expose the second stage, but never advance it on the neutralization tick.
            } else {
                zone.owner = present;
                zone.clearProgress();
                addScore(present, config.captureReward());
            }
        }
    }

    private void startRound() {
        int index = 0;
        for (var entry : members.entrySet()) entry.setValue(index++ % 2 == 0 ? Team.ALPHA : Team.BRAVO);
        round++;
        phase = Phase.INTRO;
        phaseTicks = 0;
        if (config.introTicks() == 0) enterPlaying();
    }
    private void enterPlaying() {
        phase = Phase.PLAYING;
        phaseTicks = 0;
        dead.clear();
        members.keySet().forEach(id -> lives.put(id, ++nextLife));
    }
    private void resetRound() {
        forfeitTicks = 0;
        phase = Phase.WAITING;
        phaseTicks = 0;
        winner = null;
        endReason = null;
        previousTeams.clear();
        dead.clear();
        zones.clear();
        ZONE_IDS.forEach(id -> zones.put(id, new Zone()));
        scores.put(Team.ALPHA, 0);
        scores.put(Team.BRAVO, 0);
        if (members.isEmpty()) lives.clear();
    }
    private int count(Team team) { return (int) members.values().stream().filter(t -> t == team).count(); }
    private boolean bothTeamsPresent() { return count(Team.ALPHA) > 0 && count(Team.BRAVO) > 0; }
    private static Team opponent(Team team) { return team == Team.ALPHA ? Team.BRAVO : Team.ALPHA; }
    private void addScore(Team team, int points) {
        scores.put(team, (int) Math.min(Integer.MAX_VALUE, (long) scores.get(team) + points));
    }
    private Team leadingTeam() {
        int comparison = Integer.compare(scores.get(Team.ALPHA), scores.get(Team.BRAVO));
        return comparison == 0 ? null : comparison > 0 ? Team.ALPHA : Team.BRAVO;
    }
    private void checkScoreLimit() {
        if (scores.get(Team.ALPHA) >= config.scoreLimit() || scores.get(Team.BRAVO) >= config.scoreLimit()) {
            finish(leadingTeam(), EndReason.SCORE_LIMIT);
        }
    }
    private void finish(Team winningTeam, EndReason reason) {
        winner = winningTeam;
        endReason = reason;
        phase = Phase.RESULTS;
        phaseTicks = 0;
    }
}
