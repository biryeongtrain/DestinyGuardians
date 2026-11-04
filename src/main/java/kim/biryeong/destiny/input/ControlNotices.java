package kim.biryeong.destiny.input;

import net.minecraft.network.chat.Component;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.UUID;

/** Optional connection notices, held per recipient without delaying capability detection. */
final class ControlNotices {
    static final int MAX_ANNOUNCEMENTS = 32;
    private final LinkedHashMap<UUID, Component> announcements = new LinkedHashMap<>();
    private Component recommendation;

    void recommend(Component message) { recommendation = message; }
    void installed() { recommendation = null; }

    void announce(UUID subject, Component message) {
        announcements.put(subject, message);
        // A busy public server must not accumulate an unbounded history during a strike.
        while (announcements.size() > MAX_ANNOUNCEMENTS)
            announcements.remove(announcements.keySet().iterator().next());
    }

    List<Component> drain(boolean blocked) {
        if (blocked) return List.of();
        var result = new java.util.ArrayList<Component>();
        if (recommendation != null) result.add(recommendation);
        result.addAll(announcements.values());
        recommendation = null;
        announcements.clear();
        return List.copyOf(result);
    }
}
