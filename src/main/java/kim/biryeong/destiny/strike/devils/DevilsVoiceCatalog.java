package kim.biryeong.destiny.strike.devils;

import com.google.gson.JsonParser;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;

/** Read-only original Korean base-strike speech. Timing is measured from the full delivered OGG. */
public final class DevilsVoiceCatalog {
    public record Line(String id, String speaker, String text, String event, int ticks, double seconds) { }
    private static final Map<String, Line> LINES = load();
    private DevilsVoiceCatalog() { }
    public static Optional<Line> line(String id) { return Optional.ofNullable(LINES.get(id)); }
    public static Map<String, Line> lines() { return LINES; }
    private static Map<String, Line> load() {
        var path = "/destiny/devils_lair/subtitles_ko.json";
        try (var stream = DevilsVoiceCatalog.class.getResourceAsStream(path)) {
            if (stream == null) throw new IllegalStateException("Missing " + path);
            var root = JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
            var lines = new LinkedHashMap<String, Line>();
            for (var entry : root.getAsJsonObject("lines").entrySet()) {
                var row = entry.getValue().getAsJsonObject();
                var line = new Line(entry.getKey(), row.get("speaker").getAsString(), row.get("text").getAsString(),
                        row.get("event").getAsString(), row.get("ticks").getAsInt(), row.get("seconds").getAsDouble());
                if (!line.id().matches("80b59f[0-9a-f]{2}") || line.text().isBlank()
                        || !line.event().equals("destiny_devils:voice." + line.id())
                        || !Double.isFinite(line.seconds()) || line.seconds() <= 0 || line.seconds() > 120
                        || line.ticks() != (int) Math.ceil(line.seconds() * 20))
                    throw new IllegalStateException("Invalid strike voice: " + entry.getKey());
                lines.put(line.id(), line);
            }
            if (lines.size() != 12) throw new IllegalStateException("Expected twelve base strike lines");
            return Map.copyOf(lines);
        } catch (java.io.IOException e) { throw new IllegalStateException("Cannot load strike voice", e); }
    }
}
