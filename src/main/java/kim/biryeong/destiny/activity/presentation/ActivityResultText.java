package kim.biryeong.destiny.activity.presentation;

import com.google.gson.JsonParser;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** The same20px bitmap advance metrics used by the objective HUD, for result-table alignment. */
final class ActivityResultText {
    private static final Map<Integer, Integer> ADVANCES = load();
    private ActivityResultText() { }
    static float width(String value, float size) {
        return value.codePoints().map(c -> ADVANCES.getOrDefault(c, ADVANCES.getOrDefault((int)'?', 12))).sum() * size / 20f;
    }
    static String fit(String value, float size, float maxWidth) {
        if (width(value, size) <= maxWidth) return value;
        String shortened = value;
        while (!shortened.isEmpty() && width(shortened + "…", size) > maxWidth)
            shortened = shortened.substring(0, shortened.offsetByCodePoints(shortened.length(), -1));
        return shortened + "…";
    }
    static String damage(double value) {
        return value == Math.rint(value) ? String.format(Locale.ROOT, "%,.0f", value) : String.format(Locale.ROOT, "%,.1f", value);
    }
    private static Map<Integer, Integer> load() {
        try (var input = ActivityResultText.class.getResourceAsStream("/assets/destiny/hud/rg_objective_metrics.json")) {
            if (input == null) throw new IllegalStateException("Missing result HUD font metrics");
            var medium = JsonParser.parseString(new String(input.readAllBytes(), StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonObject("medium");
            var advances = new HashMap<Integer, Integer>();
            medium.entrySet().forEach(e -> advances.put(e.getKey().codePointAt(0), e.getValue().getAsInt()));
            return Map.copyOf(advances);
        } catch (java.io.IOException failure) { throw new IllegalStateException(failure); }
    }
}
