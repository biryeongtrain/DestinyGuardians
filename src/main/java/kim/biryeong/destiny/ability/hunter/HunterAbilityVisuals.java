package kim.biryeong.destiny.ability.hunter;

import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.guardian.Element;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/** Fresh resource-pack visuals for hunter grenades and thrown melee abilities. */
public final class HunterAbilityVisuals {
    /** Contacts in these clips are authored at T+4, including the animation start transition. */
    public static final String GRENADE_ANIMATION = "grenade";

    private HunterAbilityVisuals() {
    }

    public static ItemStack grenade(Element element) {
        return kim.biryeong.destiny.fx.GrenadeModels.item(kim.biryeong.destiny.guardian.GuardianClass.HUNTER, element);
    }

    /** Combination blow is unarmed and has no projectile visual. */
    public static ItemStack melee(Element element) {
        return switch (element) {
            case ARC -> ItemStack.EMPTY;
            case SOLAR -> item(HunterAbilities.SOLAR_KNIFE);
            default -> item(HunterAbilities.VOID_SMOKE_BOMB);
        };
    }

    public static String meleeAnimation(Element element) {
        return switch (element) {
            case ARC -> "melee";
            case SOLAR -> "melee_solar";
            default -> "melee_void";
        };
    }

    /** Logical names let PlayerAnimations resolve the versioned model's h15_ namespace. */
    static boolean play(ServerPlayer player, String animation) {
        if (animation.startsWith("melee")) {
            if (PlayerAnimations.playMelee(player, animation)) return true;
            return (animation.equals("melee_solar") || animation.equals("melee_void"))
                    && PlayerAnimations.playMelee(player, GRENADE_ANIMATION);
        }
        if (PlayerAnimations.play(player, animation)) return true;
        return (animation.equals("melee_solar") || animation.equals("melee_void"))
                && PlayerAnimations.play(player, GRENADE_ANIMATION);
    }

    private static ItemStack item(Identifier model) {
        ItemStack stack = new ItemStack(Items.PAPER);
        stack.set(DataComponents.ITEM_MODEL, model);
        return stack;
    }
}
