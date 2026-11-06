package kim.biryeong.destiny.fireteam;

import net.minecraft.server.level.ServerPlayer;

import java.util.*;

/**
 * Registry behind the Fireteam Finder. Categories (공격전, 캠페인, later 던전·레이드…) hold activities; each activity
 * brings its own {@link Launcher}, so a new strike, dungeon or raid only registers a definition and an adapter.
 * Registration happens at init on the server thread; reads are unsynchronised.
 */
public final class ActivityCatalog {
    /** A finder tab. {@code icon}/{@code banner} are HUD sprite keys (destiny:gui/hud/&lt;key&gt;). */
    public record Category(String id, String name, String description, String icon, String banner, int order) { }

    /**
     * One launchable activity. {@code minPlayers}/{@code maxPlayers} bound the fireteam that may launch it;
     * {@code type} is the small label above the name (e.g. "공격전 · 우주선 발사 기지").
     */
    public record Activity(String id, String category, String name, String type, String description, String banner,
                           String icon, int minPlayers, int maxPlayers, int order, Launcher launcher) {
        public Activity {
            if (minPlayers < 1 || maxPlayers < minPlayers) throw new IllegalArgumentException("bad fireteam size for " + id);
            Objects.requireNonNull(launcher);
        }
        public String sizeLabel() { return minPlayers == maxPlayers ? maxPlayers + "인" : minPlayers + "~" + maxPlayers + "인"; }
    }

    /**
     * Adapter between the finder and an activity. The launch sequence calls {@link #check} before the countdown and
     * again before {@link #launch}; {@link #launch} runs under the black curtain (activity pre-processing), and the
     * curtain lifts per player once {@link #entered} reports that the activity has taken them (its own cinematic
     * then plays). All methods run on the server thread.
     */
    public interface Launcher {
        /** Null when this fireteam may launch now, otherwise a Korean reason. Must not mutate anything. */
        String check(List<ServerPlayer> fireteam);
        /** Start the activity for the whole fireteam. Null on success, otherwise a Korean reason. */
        String launch(List<ServerPlayer> fireteam);
        /** The activity has placed this player in its world and owns their presentation from here. */
        boolean entered(ServerPlayer player);
        /** The player is in this activity (queued, preparing or running). Hides the fireteam's listing. */
        boolean participating(ServerPlayer player);
    }

    private static final Map<String, Category> CATEGORIES = new LinkedHashMap<>();
    private static final Map<String, Activity> ACTIVITIES = new LinkedHashMap<>();

    private ActivityCatalog() { }

    public static void category(Category c) {
        if (CATEGORIES.putIfAbsent(c.id(), c) != null) throw new IllegalStateException("duplicate category " + c.id());
    }
    public static void activity(Activity a) {
        if (!CATEGORIES.containsKey(a.category())) throw new IllegalStateException("unknown category " + a.category());
        if (ACTIVITIES.putIfAbsent(a.id(), a) != null) throw new IllegalStateException("duplicate activity " + a.id());
    }

    public static List<Category> categories() {
        return CATEGORIES.values().stream().sorted(Comparator.comparingInt(Category::order)).toList();
    }
    public static List<Activity> activities(String category) {
        return ACTIVITIES.values().stream().filter(a -> a.category().equals(category))
                .sorted(Comparator.comparingInt(Activity::order)).toList();
    }
    public static Optional<Activity> find(String id) { return Optional.ofNullable(id == null ? null : ACTIVITIES.get(id)); }
    public static Optional<Category> category(String id) { return Optional.ofNullable(id == null ? null : CATEGORIES.get(id)); }
    /** Any registered activity currently holds this player. */
    public static boolean busy(ServerPlayer p) {
        for (var a : ACTIVITIES.values()) if (a.launcher().participating(p)) return true;
        return false;
    }
}
