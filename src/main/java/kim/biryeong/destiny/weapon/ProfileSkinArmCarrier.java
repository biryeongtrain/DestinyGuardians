package kim.biryeong.destiny.weapon;

import com.mojang.authlib.GameProfile;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Brightness;
import net.minecraft.util.LightCoordsUtil;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.ResolvableProfile;

import java.util.Objects;

/** Native profile carrier for the owner-only W237 ItemDisplay probe.
 * The caller owns recipient checks, display lifetime and the reserved shader lane.
 * This factory neither changes inventory nor installs a held-item projection. */
public final class ProfileSkinArmCarrier {
    private static final Identifier MODEL = Identifier.fromNamespaceAndPath("destiny", "probe/profile_arm");
    private static final int MARKER_SKY = 13;

    private ProfileSkinArmCarrier() {}

    /** Creates a fresh carrier; the caller sends the display only to this profile's owner. */
    public static ItemStack createCarrier(GameProfile ownerProfile) {
        Objects.requireNonNull(ownerProfile, "ownerProfile");
        var carrier = new ItemStack(Items.PLAYER_HEAD);
        carrier.set(DataComponents.ITEM_MODEL, MODEL);
        carrier.set(DataComponents.PROFILE, ResolvableProfile.createResolved(ownerProfile));
        return carrier;
    }

    /** Valid native light levels survive DisplayRenderer's 4-bit block/sky masks. */
    public static Brightness marker(int id) {
        if (id < 0 || id > 15) throw new IllegalArgumentException("Probe marker id must be 0..15");
        return new Brightness(id, MARKER_SKY);
    }

    /** Returns -1 for noncanonical packed markers. This does not check the shader position gate. */
    public static int markerId(int packed) {
        int id = LightCoordsUtil.block(packed);
        return packed == marker(id).pack() ? id : -1;
    }
}
