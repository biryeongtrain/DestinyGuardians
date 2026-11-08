package kim.biryeong.destiny.activity.strike;

import com.google.gson.JsonParser;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/**
 * Authored voice lines of one strike: the subtitle table, the sound event naming and where the packaged clips live.
 * Each strike builds its own instance; nothing here is global.
 */
public final class StrikeVoiceCatalog {
    public record Line(String id, String speaker, String text, String event, int ticks, double seconds) { }
    /**
     * @param subtitles     classpath JSON with {@code lines.<id>.{speaker,text,event,ticks,seconds}}
     * @param idPattern     regex every line id must match (keeps another strike's or variant's lines out)
     * @param eventPrefix   sound event prefix; the event must be exactly {@code eventPrefix + id}
     * @param clipDirectory classpath directory (trailing slash) of {@code <id>.ogg}
     * @param expectedLines exact number of lines the table must define
     */
    public record Spec(String subtitles, String idPattern, String eventPrefix, String clipDirectory, int expectedLines) {
        public Spec {
            Objects.requireNonNull(subtitles); Objects.requireNonNull(idPattern);
            Objects.requireNonNull(eventPrefix); Objects.requireNonNull(clipDirectory);
            if (expectedLines < 1) throw new IllegalArgumentException("A voice catalog needs lines");
        }
    }
    private final Spec spec;
    private final Map<String, Line> lines;

    public StrikeVoiceCatalog(Spec spec) { this.spec = Objects.requireNonNull(spec); lines = load(spec); }
    public Optional<Line> line(String id) { return Optional.ofNullable(lines.get(id)); }
    public Map<String, Line> lines() { return lines; }
    /** The packaged clip exists and is an Ogg stream; a missing clip falls back to an authored notice. */
    public boolean packaged(Line line) {
        try (var input = StrikeVoiceCatalog.class.getResourceAsStream(spec.clipDirectory() + line.id() + ".ogg")) {
            return input != null && Arrays.equals(input.readNBytes(4), new byte[]{'O', 'g', 'g', 'S'});
        } catch (java.io.IOException unavailable) { return false; }
    }

    private static Map<String, Line> load(Spec spec) {
        try (var stream = StrikeVoiceCatalog.class.getResourceAsStream(spec.subtitles())) {
            if (stream == null) throw new IllegalStateException("Missing " + spec.subtitles());
            var root = JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
            var result = new LinkedHashMap<String, Line>();
            for (var entry : root.getAsJsonObject("lines").entrySet()) {
                var row = entry.getValue().getAsJsonObject();
                var line = new Line(entry.getKey(), row.get("speaker").getAsString(), row.get("text").getAsString(),
                        row.get("event").getAsString(), row.get("ticks").getAsInt(), row.get("seconds").getAsDouble());
                if (!line.id().matches(spec.idPattern()) || line.text().isBlank()
                        || !line.event().equals(spec.eventPrefix() + line.id())
                        || !Double.isFinite(line.seconds()) || line.seconds() <= 0 || line.seconds() > 120
                        || line.ticks() != (int) Math.ceil(line.seconds() * 20))
                    throw new IllegalStateException("Invalid strike voice: " + entry.getKey());
                result.put(line.id(), line);
            }
            if (result.size() != spec.expectedLines()) throw new IllegalStateException("Expected " + spec.expectedLines() + " strike lines");
            return Map.copyOf(result);
        } catch (java.io.IOException e) { throw new IllegalStateException("Cannot load strike voice", e); }
    }
}
