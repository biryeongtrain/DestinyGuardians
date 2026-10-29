package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Map;

/** W241: pinned base AE + explicit bonuses; cone angles are Minecraft tuning, not D2 constants. */
public final class WeaponAccuracy {
    public static final String AIRBORNE_STAT = "2714457168";
    public static final String AIRBORNE_BONUS = "destiny_weapon_airborne_bonus";
    public record Profile(double hipDegrees, double airDegrees) {}
    private static final Map<String, Profile> FAMILIES = load();
    private WeaponAccuracy() {}
    private static Map<String, Profile> load() {
        var stream = WeaponAccuracy.class.getResourceAsStream("/destiny/weapons/w241-accuracy.json");
        if (stream == null) throw new IllegalStateException("Missing accuracy tuning");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var type = new com.google.gson.reflect.TypeToken<Map<String, Profile>>() {}.getType();
            Map<String, Profile> data = new Gson().fromJson(reader, type);
            for (var entry : WeaponCatalog.all()) {
                var profile = data.get(entry.family());
                if (profile == null || !Double.isFinite(profile.hipDegrees()) || profile.hipDegrees() < 0
                        || !Double.isFinite(profile.airDegrees()) || profile.airDegrees() < 0
                        || profile.hipDegrees() > 15 || profile.airDegrees() > 15)
                    throw new IllegalStateException("Invalid accuracy tuning: " + entry.family());
                if (supports(entry) && !WeaponCharacteristics.of(entry).stats().containsKey(AIRBORNE_STAT))
                    throw new IllegalStateException("Missing base AE: " + entry.id());
            }
            return Map.copyOf(data);
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    /** Sword melee and caster waves keep their own targeting; glaive projectiles are included. */
    public static boolean supports(WeaponCatalog.Entry entry) { return !entry.family().equals("sword"); }
    public static int baseAirborne(WeaponCatalog.Entry entry) {
        var value = WeaponCharacteristics.of(entry).stats().get(AIRBORNE_STAT);
        if (value == null) throw new IllegalArgumentException("No ranged AE stat: " + entry.id());
        return value;
    }
    public static int frameAirborne(WeaponCatalog.Entry entry) {
        // DDC Weapon Perks row335: Precision Hand Cannon intrinsic +25, separate from manifest base.
        return entry.family().equals("hand_cannon") && entry.frame().equals("precision") ? 25 : 0;
    }
    public static int airborneBonus(ItemStack stack) {
        var data = stack.get(DataComponents.CUSTOM_DATA);
        return data == null ? 0 : Math.clamp(data.copyTag().getIntOr(AIRBORNE_BONUS, 0), -100, 200);
    }
    /** Explicit admin/item customization only; firing never mutates this component. */
    public static boolean setAirborneBonus(ItemStack stack, int bonus) {
        var entry = WeaponItems.entry(stack);
        if (entry.isEmpty() || !supports(entry.get())) return false;
        var data = stack.get(DataComponents.CUSTOM_DATA).copyTag();
        if (bonus == 0) data.remove(AIRBORNE_BONUS);
        else data.putInt(AIRBORNE_BONUS, Math.clamp(bonus, -100, 200));
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(data));
        return true;
    }
    public static int airborne(WeaponCatalog.Entry entry, ItemStack stack) {
        return Math.clamp(baseAirborne(entry) + frameAirborne(entry) + airborneBonus(stack), 0, 100);
    }
    public static Profile of(WeaponCatalog.Entry entry) {
        var base = FAMILIES.get(entry.family());
        // Local tuning: stability and frame distinguish individual weapons within each family.
        int stability = Math.clamp(WeaponCharacteristics.of(entry).stats().getOrDefault("155624089", 50), 0, 100);
        double frame = switch (entry.frame()) {
            case "precision", "pinpoint_slug" -> .90;
            case "aggressive", "aggressive_burst", "heavy_burst" -> 1.12;
            case "high_impact" -> 1.10;
            case "rapid_fire" -> 1.08;
            case "lightweight" -> .95;
            default -> 1;
        };
        return new Profile(base.hipDegrees() * frame * (1.2 - .004 * stability), base.airDegrees());
    }
    /** Swimming/ladders are not airborne gunplay. Flight, falling and jumping are. */
    public static boolean airborne(ServerPlayer player) {
        return !player.onGround() && !player.isInWater() && !player.isInLava() && !player.onClimbable();
    }
}
