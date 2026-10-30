package kim.biryeong.destiny.combat;

import com.google.gson.JsonParser;
import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.weapon.CrucibleDamage;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

/** Per-contact Destiny PvP points, converted once before perk/weakness/resistance modifiers.
 * The caster's captured ability is explicit; delayed attacks never consult the current loadout.
 * Existing local PvE damage remains independent. See W267 provenance for approximated contacts.
 */
public final class AbilityDamage {
    private static final Map<String, Double> POINTS = load();
    private AbilityDamage() { }
    private static Map<String, Double> load() {
        var rows = new HashMap<String, Double>();
        for (String guardian : new String[]{"hunter", "titan", "warlock"}) {
            String resource = "/destiny/abilities/w267-" + guardian + "-pvp.json";
            var stream = AbilityDamage.class.getResourceAsStream(resource);
            if (stream == null) throw new IllegalStateException("Missing ability PvP data: " + resource);
            try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
                for (var row : JsonParser.parseReader(reader).getAsJsonObject().entrySet()) {
                    double value = row.getValue().getAsDouble();
                    if (!Double.isFinite(value) || value < 0 || rows.put(row.getKey(), value) != null)
                        throw new IllegalStateException("Invalid/duplicate ability PvP damage: " + row.getKey());
                }
            } catch (java.io.IOException failure) { throw new IllegalStateException(resource, failure); }
        }
        return Map.copyOf(rows);
    }
    public static float pvp(Ability ability, String contact, LivingEntity target, float local) {
        return pvp(ability.id(), contact, target, local);
    }
    public static float pvp(Identifier ability, String contact, LivingEntity target, float local) {
        if (!(target instanceof ServerPlayer)) return local;
        Double points = POINTS.get(ability.getPath() + "/" + contact);
        return points == null ? local : (float)(points * target.getMaxHealth() / CrucibleDamage.GUARDIAN_HP);
    }
}
