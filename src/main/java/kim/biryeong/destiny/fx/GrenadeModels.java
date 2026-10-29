package kim.biryeong.destiny.fx;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/** Source-mesh grenade props. Explosion/Pulse also temporarily substitute missing species meshes. */
public final class GrenadeModels {
    private GrenadeModels() { }

    /** Current class/element mapping: Arc Titan/Warlock use Pulse; all others use Explosion. */
    public static ItemStack item(GuardianClass cls, Element element) {
        if (cls == null || element == null || cls == GuardianClass.NONE || element == Element.KINETIC)
            return ItemStack.EMPTY;
        String name = switch (cls) {
            case HUNTER -> switch (element) {
                case ARC, SOLAR, VOID -> "explosion";
                default -> throw new IllegalArgumentException("Unsupported grenade element: " + element);
            };
            case TITAN -> switch (element) {
                case ARC -> "pulse";
                case SOLAR, VOID -> "explosion";
                default -> throw new IllegalArgumentException("Unsupported grenade element: " + element);
            };
            case WARLOCK -> switch (element) {
                case ARC -> "pulse";
                case SOLAR, VOID -> "explosion";
                default -> throw new IllegalArgumentException("Unsupported grenade element: " + element);
            };
            default -> throw new IllegalArgumentException("Unsupported grenade class: " + cls);
        };
        return named(name);
    }

    /** Exact existing ability IDs; unrelated IDs return EMPTY so callers can retain their own routing. */
    public static ItemStack item(Identifier ability) {
        if (ability == null || !ability.getNamespace().equals("destiny")) return ItemStack.EMPTY;
        String name = switch (ability.getPath()) {
            case "titan/arc_grenade", "warlock/arc_grenade" -> "pulse";
            case "hunter/arc_flashbang", "hunter/solar_incendiary", "hunter/void_vortex",
                    "titan/solar_grenade", "titan/void_grenade",
                    "warlock/solar_grenade", "warlock/void_grenade" -> "explosion";
            default -> null;
        };
        return name == null ? ItemStack.EMPTY : named(name);
    }

    private static ItemStack named(String name) {
        ItemStack stack = new ItemStack(Items.PAPER);
        stack.set(DataComponents.ITEM_MODEL, DestinyGuardians.id("ability_w252/ripped_grenade/" + name));
        return stack;
    }
}
