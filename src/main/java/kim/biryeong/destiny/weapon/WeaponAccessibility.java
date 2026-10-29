package kim.biryeong.destiny.weapon;

import com.mojang.serialization.Codec;
import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.minecraft.server.level.ServerPlayer;

/** Persistent player-owned firing preference. Hold-to-fire defaults on; explicit opt-out is retained. */
public final class WeaponAccessibility {
    private static final AttachmentType<Boolean> FULL_AUTO = AttachmentRegistry.create(
            DestinyGuardians.id("weapon_full_auto"),
            builder -> builder.persistent(Codec.BOOL).copyOnDeath().initializer(() -> true));

    private WeaponAccessibility() {}
    public static void init() {}

    /** Reading a default does not create an attachment. */
    public static boolean enabled(ServerPlayer player) {
        return player.getAttachedOrElse(FULL_AUTO, true);
    }

    /** Invalidate the old held-input session before changing its interpretation. */
    public static boolean setEnabled(ServerPlayer player, boolean fullAuto) {
        if (enabled(player) == fullAuto) return false;
        WeaponRuntime.inputSettingsChanged(player);
        player.setAttached(FULL_AUTO, fullAuto);
        return true;
    }
}
