package kim.biryeong.destiny.campaign.presentation;

import com.google.gson.JsonParser;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.FontDescription;
import net.minecraft.resources.Identifier;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Metrics from the exact bitmap glyphs sent to the client, in the 20px source layout. */
final class ObjectiveTypography {
    private static final Map<String, Map<Integer, Integer>> ADVANCES = load();
    private ObjectiveTypography() { }

    static Component text(String text, int color, boolean bold) {
        var font = new FontDescription.Resource(Identifier.fromNamespaceAndPath("destiny",
                "rg_objective_" + (bold ? "bold" : "medium")));
        return Component.literal(text).withStyle(s -> s.withFont(font).withColor(color).withBold(false));
    }

    static float width(String text, float size, boolean bold) {
        var metrics = ADVANCES.get(bold ? "bold" : "medium");
        return text.codePoints().map(c -> metrics.getOrDefault(c, metrics.get((int) '?'))).sum() * size / 20f;
    }

    /** Character-safe wrapping also handles a long Korean word without spaces. */
    static List<String> wrap(String text, float maxWidth, float size) {
        var lines = new ArrayList<String>();
        var row = new StringBuilder();
        for (int cp : text.codePoints().toArray()) {
            String next = new String(Character.toChars(cp));
            if (cp == '\n') {
                lines.add(row.toString().stripTrailing());
                row.setLength(0);
            } else if (!row.isEmpty() && width(row + next, size, false) > maxWidth) {
                int space = row.lastIndexOf(" ");
                if (space > 0) {
                    lines.add(row.substring(0, space));
                    row.delete(0, space + 1);
                } else {
                    lines.add(row.toString());
                    row.setLength(0);
                }
            }
            if (cp != '\n' && !(row.isEmpty() && Character.isWhitespace(cp))) row.append(next);
        }
        if (!row.isEmpty()) lines.add(row.toString());
        return lines.isEmpty() ? List.of("") : List.copyOf(lines);
    }

    private static Map<String, Map<Integer, Integer>> load() {
        try (var stream = ObjectiveTypography.class.getResourceAsStream("/assets/destiny/hud/rg_objective_metrics.json")) {
            if (stream == null) throw new IllegalStateException("Missing objective HUD font metrics");
            var json = JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
            var result = new HashMap<String, Map<Integer, Integer>>();
            for (var weight : json.entrySet()) {
                var advances = new HashMap<Integer, Integer>();
                for (var entry : weight.getValue().getAsJsonObject().entrySet())
                    advances.put(entry.getKey().codePointAt(0), entry.getValue().getAsInt());
                result.put(weight.getKey(), Map.copyOf(advances));
            }
            return Map.copyOf(result);
        } catch (java.io.IOException e) {
            throw new IllegalStateException("Cannot load objective HUD font metrics", e);
        }
    }
}
