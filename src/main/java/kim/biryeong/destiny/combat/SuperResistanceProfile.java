package kim.biryeong.destiny.combat;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

/** DDC fractions. Unknown source values remain null in the resource and grant no invented bonus. */
public final class SuperResistanceProfile {
    public record Rates(double pvp, double pve) { }
    private static final Map<String, Rates> SUPERS = new HashMap<>();
    private static final JsonObject WELL;
    static {
        var stream = SuperResistanceProfile.class.getResourceAsStream("/destiny/abilities/w265-super-resistance.json");
        if (stream == null) throw new IllegalStateException("Missing super damage resistance data");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var root = JsonParser.parseReader(reader).getAsJsonObject();
            for (var item : root.getAsJsonArray("supers")) {
                var row = item.getAsJsonObject();
                var id = row.get("id").getAsString();
                if (SUPERS.put(id, new Rates(fraction(row, "pvp"), fraction(row, "pve"))) != null)
                    throw new IllegalStateException("Duplicate super resistance: " + id);
            }
            WELL = root.getAsJsonObject("well");
            for (String key : new String[]{"pvp_primary", "pvp_other", "pve", "pve_boss"}) fraction(WELL, key);
        } catch (java.io.IOException failure) {
            throw new IllegalStateException("Unreadable super damage resistance data", failure);
        }
    }
    private SuperResistanceProfile() { }
    private static double fraction(JsonObject row, String key) {
        var value = row.get(key);
        if (value == null) throw new IllegalStateException("Missing super resistance field " + key);
        if (value.isJsonNull()) return 0;
        double result = value.getAsDouble();
        if (!Double.isFinite(result) || result < 0 || result >= 1)
            throw new IllegalStateException("Invalid super resistance " + key + ": " + result);
        return result;
    }
    public static double cast(String id, boolean pvp) {
        var rates = SUPERS.get(id);
        return rates == null ? 0 : pvp ? rates.pvp() : rates.pve();
    }
    public static double well(boolean pvp, boolean primary, boolean boss) {
        return fraction(WELL, pvp ? primary ? "pvp_primary" : "pvp_other" : boss ? "pve_boss" : "pve");
    }
}
