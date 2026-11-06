package kim.biryeong.destiny.fireteam;

import java.util.*;

/**
 * Pure fireteam bookkeeping (no Minecraft types): who is in which fireteam, its leader, target activity, listing
 * state and tags. One fireteam per player; the first member is always the leader. A fireteam that is launching or
 * whose members are inside its activity cannot be joined. {@link Fireteams} wires this to players and the server.
 */
public final class FireteamRoster {
    /** Recruitment tags, like the Destiny Fireteam Finder's preset tags. */
    public static final List<String> TAGS = List.of("초보 환영", "첫 클리어", "빠른 진행", "보상 파밍", "음성 채팅", "느긋하게");
    public static final int MAX_TAGS = 3;

    public enum Error {
        IN_FIRETEAM("이미 화력팀에 속해 있습니다. 먼저 화력팀에서 나가세요."),
        NO_FIRETEAM("화력팀에 속해 있지 않습니다."),
        NOT_LEADER("화력팀장만 할 수 있습니다."),
        GONE("모집이 종료된 화력팀입니다."),
        FULL("화력팀 정원이 가득 찼습니다."),
        CLOSED("현재 참가할 수 없는 화력팀입니다."),
        BUSY("화력팀이 활동을 시작하는 중입니다."),
        NOT_MEMBER("화력팀원이 아닙니다."),
        SELF("자기 자신에게는 할 수 없습니다."),
        TOO_MANY("이 활동의 정원보다 화력팀 인원이 많습니다."),
        TAG_LIMIT("태그는 최대 " + MAX_TAGS + "개까지 고를 수 있습니다."),
        UNKNOWN_TAG("알 수 없는 태그입니다.");
        public final String message;
        Error(String message) { this.message = message; }
    }

    public static final class Team {
        public final long id;
        final List<UUID> members = new ArrayList<>();
        final Map<UUID, String> names = new HashMap<>();
        final LinkedHashSet<String> tags = new LinkedHashSet<>();
        String activity;
        boolean listed, launching, inActivity;
        final long created;
        Team(long id, String activity, long created) { this.id = id; this.activity = activity; this.created = created; }
        public UUID leader() { return members.getFirst(); }
        public List<UUID> members() { return List.copyOf(members); }
        public String name(UUID id) { return names.getOrDefault(id, "?"); }
        public String activity() { return activity; }
        public boolean listed() { return listed; }
        public boolean launching() { return launching; }
        public boolean inActivity() { return inActivity; }
        public Set<String> tags() { return Collections.unmodifiableSet(tags); }
        public long created() { return created; }
        public int size() { return members.size(); }
        /** Visible and joinable by strangers right now (capacity aside). */
        public boolean recruiting() { return listed && !launching && !inActivity; }
    }

    private final Map<Long, Team> teams = new LinkedHashMap<>();
    private final Map<UUID, Team> byMember = new HashMap<>();
    private long nextId = 1;

    public Optional<Team> team(UUID player) { return Optional.ofNullable(byMember.get(player)); }
    public Optional<Team> byId(long id) { return Optional.ofNullable(teams.get(id)); }
    public Collection<Team> all() { return Collections.unmodifiableCollection(teams.values()); }

    /** A new fireteam led by {@code leader}, targeting {@code activity}. */
    public Team create(UUID leader, String name, String activity, boolean listed, long now) {
        if (byMember.containsKey(leader)) throw new IllegalStateException("already in a fireteam");
        var t = new Team(nextId++, activity, now);
        t.members.add(leader); t.names.put(leader, name); t.listed = listed;
        teams.put(t.id, t); byMember.put(leader, t);
        return t;
    }

    /** Join an open listing. {@code capacity} is the activity's maximum fireteam size. */
    public Error join(UUID player, String name, long teamId, int capacity) {
        if (byMember.containsKey(player)) return Error.IN_FIRETEAM;
        var t = teams.get(teamId);
        if (t == null) return Error.GONE;
        if (t.launching) return Error.BUSY;
        if (!t.listed || t.inActivity) return Error.CLOSED;
        if (t.members.size() >= capacity) return Error.FULL;
        t.members.add(player); t.names.put(player, name); byMember.put(player, t);
        return null;
    }

    /** Leave; the next member becomes leader, an empty fireteam disbands. Returns the team left, if any. */
    public Optional<Team> leave(UUID player) {
        var t = byMember.remove(player);
        if (t == null) return Optional.empty();
        t.members.remove(player); t.names.remove(player);
        if (t.members.isEmpty()) teams.remove(t.id);
        return Optional.of(t);
    }

    public Error kick(UUID leader, UUID target) {
        var t = byMember.get(leader);
        if (t == null) return Error.NO_FIRETEAM;
        if (!t.leader().equals(leader)) return Error.NOT_LEADER;
        if (leader.equals(target)) return Error.SELF;
        if (byMember.get(target) != t) return Error.NOT_MEMBER;
        if (t.launching) return Error.BUSY;
        leave(target);
        return null;
    }

    public Error promote(UUID leader, UUID target) {
        var t = byMember.get(leader);
        if (t == null) return Error.NO_FIRETEAM;
        if (!t.leader().equals(leader)) return Error.NOT_LEADER;
        if (leader.equals(target)) return Error.SELF;
        if (byMember.get(target) != t) return Error.NOT_MEMBER;
        t.members.remove(target); t.members.addFirst(target);
        return null;
    }

    /** Retarget the fireteam (leader only); the current members must fit the new activity. */
    public Error retarget(UUID leader, String activity, int capacity) {
        var t = byMember.get(leader);
        if (t == null) return Error.NO_FIRETEAM;
        if (!t.leader().equals(leader)) return Error.NOT_LEADER;
        if (t.launching || t.inActivity) return Error.BUSY;
        if (t.members.size() > capacity) return Error.TOO_MANY;
        t.activity = activity;
        return null;
    }

    public Error listed(UUID leader, boolean listed) {
        var t = byMember.get(leader);
        if (t == null) return Error.NO_FIRETEAM;
        if (!t.leader().equals(leader)) return Error.NOT_LEADER;
        t.listed = listed;
        return null;
    }

    public Error toggleTag(UUID leader, String tag) {
        var t = byMember.get(leader);
        if (t == null) return Error.NO_FIRETEAM;
        if (!t.leader().equals(leader)) return Error.NOT_LEADER;
        if (!TAGS.contains(tag)) return Error.UNKNOWN_TAG;
        if (t.tags.remove(tag)) return null;
        if (t.tags.size() >= MAX_TAGS) return Error.TAG_LIMIT;
        t.tags.add(tag);
        return null;
    }

    void launching(Team t, boolean value) { t.launching = value; }
    void inActivity(Team t, boolean value) { t.inActivity = value; }

    /** Open listings for {@code activity}, oldest first (Destiny lists by age). */
    public List<Team> listings(String activity) {
        return teams.values().stream().filter(t -> t.activity.equals(activity) && t.recruiting())
                .sorted(Comparator.comparingLong(Team::created)).toList();
    }
}
