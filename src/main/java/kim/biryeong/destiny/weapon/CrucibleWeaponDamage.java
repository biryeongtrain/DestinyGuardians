package kim.biryeong.destiny.weapon;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalDouble;

/** Raw Destiny PvP points per bullet, pellet, bolt or projectile.
 * Precision is absolute damage, never a multiplier. No health scaling or perks here.
 * Missing weapons/components are deliberately absent, not zero or estimated.
 * W263 provenance records source dates, frame mappings and provisional source warnings.
 */
public final class CrucibleWeaponDamage {
    public record Row(double body, double precision, OptionalDouble explosion,
                      OptionalDouble melee, String component) {
        public Row {
            positive(body);
            positive(precision);
            Objects.requireNonNull(explosion).ifPresent(CrucibleWeaponDamage::positive);
            Objects.requireNonNull(melee).ifPresent(CrucibleWeaponDamage::positive);
            Objects.requireNonNull(component);
            if (component.isBlank()) throw new IllegalArgumentException("Missing damage component");
        }
    }
    private static final Map<String, Row> ROWS = load();
    private CrucibleWeaponDamage() {}
    public static Optional<Row> find(String weaponId) {
        return weaponId == null ? Optional.empty() : Optional.ofNullable(ROWS.get(weaponId));
    }
    private static void positive(double value) {
        if (!Double.isFinite(value) || value <= 0)
            throw new IllegalArgumentException("Damage must be finite and positive");
    }
    private static OptionalDouble optional(JsonObject row, String key) {
        JsonElement value = row.get(key);
        return value == null || value.isJsonNull() ? OptionalDouble.empty()
                : OptionalDouble.of(value.getAsDouble());
    }
    private static Map<String, Row> load() {
        var stream = CrucibleWeaponDamage.class.getResourceAsStream("/destiny/weapons/w263-pvp-damage.json");
        if (stream == null) throw new IllegalStateException("Missing W263 PvP damage data");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var result = new LinkedHashMap<String, Row>();
            for (var entry : JsonParser.parseReader(reader).getAsJsonObject().entrySet()) {
                if (!entry.getKey().matches("[a-z0-9_]+"))
                    throw new IllegalStateException("Invalid weapon id: " + entry.getKey());
                var row = entry.getValue().getAsJsonObject();
                result.put(entry.getKey(), new Row(row.get("body").getAsDouble(),
                        row.get("precision").getAsDouble(), optional(row, "explosion"),
                        optional(row, "melee"), row.get("component").getAsString()));
            }
            if (result.isEmpty()) throw new IllegalStateException("Empty W263 PvP damage data");
            return Map.copyOf(result);
        } catch (IOException exception) {
            throw new IllegalStateException("Unreadable W263 PvP damage data", exception);
        }
    }
}
