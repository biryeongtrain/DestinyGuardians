package kim.biryeong.destiny.fx;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/** Delivered source props for Fusion/Solar/Vortex/Storm; W252 fallbacks for missing species. */
public final class GrenadeModels {
    private GrenadeModels() { }

    /** Class defaults resolve through the same exact ability mapping as held props. */
    public static ItemStack item(GuardianClass cls, Element element) {
        if (cls == null || element == null || cls == GuardianClass.NONE || element == Element.KINETIC)
            return ItemStack.EMPTY;
        String ability = switch (cls) {
            case HUNTER -> switch (element) {
                case ARC -> "hunter/arc_flashbang";
                case SOLAR -> "hunter/solar_incendiary";
                case VOID -> "hunter/void_vortex";
                default -> throw new IllegalArgumentException("Unsupported grenade element: " + element);
            };
            case TITAN -> switch (element) {
                case ARC -> "titan/arc_grenade";
                case SOLAR -> "titan/solar_grenade";
                case VOID -> "titan/void_grenade";
                default -> throw new IllegalArgumentException("Unsupported grenade element: " + element);
            };
            case WARLOCK -> switch (element) {
                case ARC -> "warlock/arc_grenade";
                case SOLAR -> "warlock/solar_grenade";
                case VOID -> "warlock/void_grenade";
                default -> throw new IllegalArgumentException("Unsupported grenade element: " + element);
            };
            default -> throw new IllegalArgumentException("Unsupported grenade class: " + cls);
        };
        return item(DestinyGuardians.id(ability));
    }

    /** Held is the default. Unrelated ability IDs return EMPTY for caller-owned routing. */
    public static ItemStack item(Identifier ability) {
        return model(ability, "held");
    }

    /** Flight uses the delivered projectile candidate, independently from the held source. */
    public static ItemStack projectile(Identifier ability) {
        return model(ability, "projectile");
    }

    private static ItemStack model(Identifier ability, String phase) {
        if (ability == null || !ability.getNamespace().equals("destiny")) return ItemStack.EMPTY;
        String path = switch (ability.getPath()) {
            case "titan/solar_grenade" -> "ability_w255/grenade/fusion_" + phase;
            case "warlock/solar_grenade" -> "ability_w255/grenade/solar_" + phase;
            case "hunter/void_vortex", "warlock/void_grenade" -> "ability_w255/grenade/vortex_" + phase;
            case "warlock/arc_grenade" -> "ability_w255/grenade/storm_" + phase;
            case "titan/arc_grenade" -> "ability_w252/ripped_grenade/pulse";
            case "hunter/arc_flashbang", "hunter/solar_incendiary", "titan/void_grenade" -> "ability_w252/ripped_grenade/explosion";
            default -> null;
        };
        if (path == null) return ItemStack.EMPTY;
        ItemStack stack = new ItemStack(Items.PAPER);
        stack.set(DataComponents.ITEM_MODEL, DestinyGuardians.id(path));
        return stack;
    }
}
