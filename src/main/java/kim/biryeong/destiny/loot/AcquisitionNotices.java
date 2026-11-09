package kim.biryeong.destiny.loot;

import kim.biryeong.destiny.inventory.WeaponScreenText;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.weapon.WeaponRarity;
import kim.biryeong.destiny.weapon.WeaponSkins;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

import java.util.List;

/** Successful exotic acquisitions, scoped to the actual current world instance rather than a party or template id. */
public final class AcquisitionNotices {
    private AcquisitionNotices() { }

    /** The same Korean name used by acquisition cards, without combat-item prefixes. */
    public static String weaponName(ItemStack stack) {
        var entry = WeaponItems.entry(stack);
        if (entry.isEmpty()) return stack.getHoverName().getString();
        return WeaponSkins.of(stack).map(WeaponSkins.Skin::display)
                .orElseGet(() -> WeaponScreenText.weapon(entry.get().id(), entry.get().name()));
    }

    public static void weapon(ServerPlayer owner, ItemStack stack) {
        if (WeaponRarity.of(stack) == WeaponRarity.EXOTIC) broadcast(owner, weaponName(stack));
    }

    public static void engram(ServerPlayer owner, String tier) {
        if (WeaponRarity.parse(tier).orElse(null) == WeaponRarity.EXOTIC)
            broadcast(owner, Loot.engramName(WeaponRarity.EXOTIC.id()));
    }

    private static void broadcast(ServerPlayer owner, String itemName) {
        if (owner.hasDisconnected() || owner.isRemoved()) return;
        var instance = owner.level();
        var message = Component.literal(owner.getGameProfile().name()).withStyle(ChatFormatting.AQUA)
                .append(Component.literal(" 님이 ").withStyle(ChatFormatting.GRAY))
                .append(Component.literal(itemName).withStyle(ChatFormatting.GOLD))
                .append(Component.literal(particle(itemName) + " 획득했습니다.").withStyle(ChatFormatting.GRAY));
        for (var recipient : List.copyOf(instance.players()))
            if (recipient.level() == instance && !recipient.hasDisconnected()) recipient.sendSystemMessage(message);
    }

    private static String particle(String name) {
        int last = name.codePointBefore(name.length());
        if (last < 0xAC00 || last > 0xD7A3) return "을(를)";
        return (last - 0xAC00) % 28 == 0 ? "를" : "을";
    }
}
