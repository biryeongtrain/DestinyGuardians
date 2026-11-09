package kim.biryeong.destiny.compat.pack;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Immutable ownership of client assets. Shared actor models and finder art stay in the base pack. */
public final class ActivityPackCatalog {
    public record Activity(String id, String name, List<String> prefixes, Map<String, List<String>> soundEvents) {
        public Activity { prefixes = List.copyOf(prefixes); soundEvents = Map.copyOf(soundEvents); }
    }
    private final Map<String, Activity> activities;
    private final String definition;
    private ActivityPackCatalog(Map<String, Activity> activities, String definition) {
        this.activities = Map.copyOf(activities); this.definition = definition;
    }
    String definition() { return definition; }
    public Collection<Activity> activities() { return activities.values(); }
    public Activity activity(String id) {
        var result = activities.get(id);
        if (result == null) throw new IllegalArgumentException("Unknown activity resource pack: " + id);
        return result;
    }
    public static ActivityPackCatalog load() {
        try (var input = ActivityPackCatalog.class.getResourceAsStream("/destiny/pack/activities.json")) {
            if (input == null) throw new IllegalStateException("Missing activity pack catalog");
            return parse(new String(input.readAllBytes(), StandardCharsets.UTF_8));
        } catch (java.io.IOException e) { throw new java.io.UncheckedIOException(e); }
    }
    static ActivityPackCatalog parse(String text) {
        var root = JsonParser.parseString(text).getAsJsonObject();
        if (root.get("schema").getAsInt() != 1) throw new IllegalArgumentException("Unknown activity pack schema");
        var entries = new LinkedHashMap<String, Activity>();
        for (var element : root.getAsJsonArray("activities")) {
            var o = element.getAsJsonObject();
            String id = o.get("id").getAsString();
            if (!id.matches("[a-z0-9_]+")) throw new IllegalArgumentException("Invalid activity pack id");
            var prefixes = new ArrayList<String>();
            for (var prefix : o.getAsJsonArray("prefixes")) {
                String p = prefix.getAsString();
                if (!p.startsWith("assets/") || p.contains("..")) throw new IllegalArgumentException("Invalid asset prefix");
                prefixes.add(p);
            }
            var sounds = new LinkedHashMap<String, List<String>>();
            for (var entry : o.getAsJsonObject("soundEvents").entrySet()) {
                var names = new ArrayList<String>();
                for (var name : entry.getValue().getAsJsonArray()) names.add(name.getAsString());
                sounds.put(entry.getKey(), List.copyOf(names));
            }
            if (entries.putIfAbsent(id, new Activity(id, o.get("name").getAsString(), prefixes, sounds)) != null)
                throw new IllegalArgumentException("Duplicate activity pack id");
        }
        return new ActivityPackCatalog(entries, root.toString());
    }
    String owner(String path) {
        String owner = null;
        for (var activity : activities.values()) if (activity.prefixes().stream().anyMatch(path::startsWith)) {
            if (owner != null) throw new IllegalStateException("Ambiguous activity asset: " + path);
            owner = activity.id();
        }
        return owner;
    }
    boolean selects(String path) { return owner(path) != null || activities.values().stream().anyMatch(a -> a.soundEvents().containsKey(path)); }
}
