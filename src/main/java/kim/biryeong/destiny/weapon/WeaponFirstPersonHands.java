package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Map;

/** Stateless cosmetic projection after Polymer has resolved the authorized weapon route.
 * The generated wrapper adds player-skin block arms in first-person contexts and retains every other
 * context's original graph. No persisted selector, ownership or gameplay state is added.
 */
public final class WeaponFirstPersonHands {
    private record Routes(int schemaVersion, Map<String, String> models) {}
    private static final Map<Identifier, Identifier> MODELS = load();
    private WeaponFirstPersonHands() {}

    private static Map<Identifier, Identifier> load() {
        var stream = WeaponFirstPersonHands.class.getResourceAsStream(
                "/destiny/weapons/w201-first-person-hands.json");
        if (stream == null) throw new IllegalStateException("Missing first-person arm routes");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var data = new Gson().fromJson(reader, Routes.class);
            if (data.schemaVersion != 1 || data.models == null || data.models.isEmpty())
                throw new IllegalStateException("Invalid first-person arm routes");
            var result = new java.util.HashMap<Identifier, Identifier>();
            data.models.forEach((from, to) -> {
                var source = Identifier.parse(from);
                var target = Identifier.parse(to);
                if (!source.getNamespace().equals("destiny") || !target.getNamespace().equals("destiny")
                        || !target.getPath().equals("weapon_hands_w201/" + source.getPath()))
                    throw new IllegalStateException("Invalid first-person arm mapping: " + from);
                result.put(source, target);
            });
            return Map.copyOf(result);
        } catch (java.io.IOException e) {
            throw new IllegalStateException("Unreadable first-person arm routes", e);
        }
    }

    /** Generation-only route inventory; the live selectors decide which sources remain reachable. */
    public static java.util.Set<Identifier> sources() { return MODELS.keySet(); }

    public static Identifier model(Identifier original) {
        return original == null ? null : MODELS.getOrDefault(original, original);
    }

    /** Only call with a fresh outgoing carrier, never an authoritative inventory stack. */
    static ItemStack project(ItemStack carrier, net.fabricmc.fabric.api.networking.v1.context.PacketContext context) {
        var original = carrier.get(DataComponents.ITEM_MODEL);
        var model = model(original);
        if (model != null && !model.equals(original)) carrier.set(DataComponents.ITEM_MODEL, model);
        return model != null && !model.equals(original) && !ProfileWeaponView.enabled() ? WeaponSkinArms.project(carrier, context) : carrier;
    }
}
