package kim.biryeong.destiny.loot;

import kim.biryeong.destiny.weapon.WeaponRarity;
import net.minecraft.server.level.ServerPlayer;

/** Shared, owner-only item/engram acquisition cues. Preserve the source recordings' pitch. */
public final class AcquisitionSounds {
    private AcquisitionSounds() { }

    static String id(WeaponRarity rarity) {
        return switch (rarity) {
            case COMMON, UNCOMMON, RARE -> "destiny:loot.acquire.basic";
            case LEGENDARY -> "destiny:loot.acquire.legendary";
            case EXOTIC -> "destiny:loot.acquire.exotic";
        };
    }

    public static void play(ServerPlayer player, WeaponRarity rarity) {
        LootSounds.play(player, id(rarity), player.position(), 1f, 1f);
    }
}
