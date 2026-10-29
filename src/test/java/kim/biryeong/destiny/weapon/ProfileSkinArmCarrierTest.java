package kim.biryeong.destiny.weapon;

import com.google.common.collect.ImmutableMultimap;
import com.mojang.authlib.GameProfile;
import com.mojang.authlib.properties.Property;
import com.mojang.authlib.properties.PropertyMap;
import com.mojang.serialization.JsonOps;
import io.netty.buffer.Unpooled;
import net.minecraft.SharedConstants;
import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponentMap;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.Bootstrap;
import net.minecraft.util.Brightness;
import net.minecraft.util.LightCoordsUtil;
import net.minecraft.world.entity.player.PlayerSkin;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.ResolvableProfile;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class ProfileSkinArmCarrierTest {
    @BeforeAll static void bootstrap() {
        SharedConstants.tryDetectVersion();
        Bootstrap.bootStrap();
        // Pure JUnit has no data-pack item defaults in 26.3; the factory sets every tested component.
        var head = (Holder.Reference<Item>) BuiltInRegistries.ITEM.wrapAsHolder(Items.PLAYER_HEAD);
        if (!head.areComponentsBound()) head.bindComponents(DataComponentMap.EMPTY);
    }

    private static GameProfile profile(String json) {
        String value = Base64.getEncoder().encodeToString(json.getBytes(StandardCharsets.UTF_8));
        return new GameProfile(new UUID(0, 9), "W237Owner", new PropertyMap(
                ImmutableMultimap.of("textures", new Property("textures", value))));
    }

    @Test void nativeProfileCodecsPreserveUnsignedTexturePropertyWithoutPatch() {
        var owner = profile("{\"textures\":{\"SKIN\":{\"url\":\"https://textures.invalid/local-fixture\","
                + "\"metadata\":{\"model\":\"slim\"}}}}");
        var carrier = ProfileSkinArmCarrier.createCarrier(owner);
        assertTrue(carrier.is(Items.PLAYER_HEAD));
        assertEquals("destiny:probe/profile_arm", carrier.get(DataComponents.ITEM_MODEL).toString());
        var nativeProfile = carrier.get(DataComponents.PROFILE);
        assertSame(owner, nativeProfile.partialProfile());
        assertSame(owner, nativeProfile.resolveProfile(null).join());
        assertEquals(PlayerSkin.Patch.EMPTY, nativeProfile.skinPatch());
        var encoded = ResolvableProfile.CODEC.encodeStart(JsonOps.INSTANCE, nativeProfile).getOrThrow();
        assertFalse(encoded.getAsJsonObject().has("texture"));
        var decoded = ResolvableProfile.CODEC.parse(JsonOps.INSTANCE, encoded).getOrThrow();
        assertEquals(owner, decoded.partialProfile());
        assertEquals(owner.properties(), decoded.partialProfile().properties());
        var bytes = Unpooled.buffer();
        try {
            ResolvableProfile.STREAM_CODEC.encode(bytes, nativeProfile);
            var wireProfile = ResolvableProfile.STREAM_CODEC.decode(bytes);
            assertEquals(owner, wireProfile.partialProfile());
            assertEquals(PlayerSkin.Patch.EMPTY, wireProfile.skinPatch());
            assertEquals(0, bytes.readableBytes());
        } finally {
            bytes.release();
        }
        assertNull(carrier.get(DataComponents.CUSTOM_MODEL_DATA));
        var another = ProfileSkinArmCarrier.createCarrier(owner);
        assertNotSame(carrier, another);
        another.setCount(2);
        assertEquals(1, carrier.getCount());
    }

    @Test void missingOwnerIsRejectedInsteadOfCreatingAnUnownedCarrier() {
        assertThrows(NullPointerException.class, () -> ProfileSkinArmCarrier.createCarrier(null));
    }

    @Test void markerIdsSurviveActualNativeBlockAndSkyMasksAndRepacking() {
        for (int id = 0; id < 16; id++) {
            var marker = ProfileSkinArmCarrier.marker(id);
            assertEquals(new Brightness(id, 13), marker);
            int packed = marker.pack();
            // DisplayRenderer extracts these masked levels, then EntityRenderer repacks them.
            int block = LightCoordsUtil.block(packed), sky = LightCoordsUtil.sky(packed);
            assertEquals(id, block);
            assertEquals(13, sky);
            int rendered = LightCoordsUtil.pack(block, sky);
            assertEquals(packed, rendered);
            assertEquals(id, ProfileSkinArmCarrier.markerId(rendered));
            assertEquals(id * 16, rendered & 0xffff);
            assertEquals(208, rendered >>> 16);
            // Former high-bit proposal is lossy even though its direct pack retains extra bits.
            int rejectedHighBits = new Brightness(128 + id, 173).pack();
            int masked = LightCoordsUtil.pack(LightCoordsUtil.block(rejectedHighBits),
                    LightCoordsUtil.sky(rejectedHighBits));
            assertNotEquals(rejectedHighBits, masked);
            assertEquals(packed, masked);
            assertEquals(-1, ProfileSkinArmCarrier.markerId(rejectedHighBits));
        }
    }

    @Test void markerRejectsInvalidIdsLightingAndNoncanonicalPackedBits() {
        assertThrows(IllegalArgumentException.class, () -> ProfileSkinArmCarrier.marker(-1));
        assertThrows(IllegalArgumentException.class, () -> ProfileSkinArmCarrier.marker(16));
        for (int sky = 0; sky < 16; sky++) {
            for (int block = 0; block < 16; block++) {
                assertEquals(sky == 13 ? block : -1,
                        ProfileSkinArmCarrier.markerId(new Brightness(block, sky).pack()));
            }
        }
        int valid = ProfileSkinArmCarrier.marker(3).pack();
        assertEquals(-1, ProfileSkinArmCarrier.markerId(valid | 1));
        assertEquals(-1, ProfileSkinArmCarrier.markerId(valid | Integer.MIN_VALUE));
        assertEquals(-1, ProfileSkinArmCarrier.markerId(-1));
    }
}
