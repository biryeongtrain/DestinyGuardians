package kim.biryeong.destiny.test;

import com.mojang.datafixers.util.Pair;
import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import io.netty.buffer.Unpooled;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundContainerSetSlotPacket;
import net.minecraft.network.protocol.game.ClientboundSetEntityDataPacket;
import net.minecraft.network.protocol.game.ClientboundSetEquipmentPacket;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/** Real Fabric recipient encoder and context-free client decode; not a rendered-client acceptance test. */
public final class WeaponObserverEquipmentScaleGameTests {
    private static void check(GameTestHelper h, boolean value, String reason) {
        h.assertTrue(value, Component.literal(reason));
    }

    private static ItemStack item(String id) {
        var item = WeaponItems.create(WeaponCatalog.find(id).orElseThrow());
        item.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(
                List.of(17f, .333f, 27f, .725f, 39f), List.of(true, false, true),
                List.of("ads", "observer_keep"), List.of(0xabcdef, 0x123456)));
        item.set(DataComponents.CUSTOM_NAME, Component.literal("Observer render identity"));
        item.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true);
        var tag = item.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putString("private_observer_test", "do_not_send_".repeat(400));
        item.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        return item;
    }

    private static ItemStack ordinary(InventoryWireW92 wire, ItemStack snapshot) {
        var context = ((PacketContextProvider) (Object) wire.player.connection).getPacketContext();
        return PolymerItemUtils.getPolymerItemStack(snapshot, context, wire.player.registryAccess());
    }

    private static ItemStack equipment(GameTestHelper h, InventoryWireW92 wire, int ownerId, ItemStack snapshot) {
        wire.discard();
        wire.player.connection.send(new ClientboundSetEquipmentPacket(ownerId,
                List.of(Pair.of(EquipmentSlot.MAINHAND, snapshot))));
        var packets = wire.capture().stream().filter(ClientboundSetEquipmentPacket.class::isInstance)
                .map(ClientboundSetEquipmentPacket.class::cast).toList();
        check(h, packets.size() == 1 && packets.getFirst().getEntity() == ownerId,
                "One actual equipment frame retains its entity identity");
        var slots = packets.getFirst().getSlots();
        check(h, slots.size() == 1 && slots.getFirst().getFirst() == EquipmentSlot.MAINHAND,
                "Equipment slot and ordering survive the encoder");
        return slots.getFirst().getSecond();
    }

    private static int bytes(InventoryWireW92 wire, ItemStack stack) {
        return PacketContext.supplyWithoutContext(() -> {
            var buffer = new RegistryFriendlyByteBuf(Unpooled.buffer(), wire.player.registryAccess());
            try {
                ItemStack.OPTIONAL_STREAM_CODEC.encode(buffer, stack);
                return buffer.readableBytes();
            } finally { buffer.release(); }
        });
    }

    @GameTest(structure = "destiny-test:w78_floor", maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void observersKeepEveryPublicComponentAndOwnerRetainsRoundtripData(GameTestHelper h) {
        var owner = new InventoryWireW92(h, new Vec3(4, 4, 8));
        var observer = new InventoryWireW92(h, new Vec3(10, 4, 8));
        owner.player.setAttached(WeaponLoadout.ENABLED, false);
        observer.player.setAttached(WeaponLoadout.ENABLED, false);
        for (String id : List.of("austringer", "beloved", "ammit_ar2")) {
            var source = item(id);
            owner.player.setItemInHand(InteractionHand.MAIN_HAND, source);
            var before = source.copy(); var snapshot = source.copy();
            var full = ordinary(observer, snapshot);
            check(h, full.has(DataComponents.CUSTOM_DATA) && full.has(DataComponents.LORE),
                    "Ordinary Polymer projection contains the private roundtrip tag and tooltip");
            var expected = full.copy();
            expected.remove(DataComponents.CUSTOM_DATA); expected.remove(DataComponents.LORE);
            var decoded = equipment(h, observer, owner.player.getId(), snapshot);
            check(h, ItemStack.matches(expected, decoded),
                    "Actual observer wire retains ALL ordinary components except CUSTOM_DATA and LORE: " + id);
            check(h, !decoded.has(DataComponents.CUSTOM_DATA) && !decoded.has(DataComponents.LORE),
                    "The subsequent normal Polymer codec does not reattach private components");
            check(h, bytes(observer, full) - bytes(observer, decoded) > 1000,
                    "Actual native item encoding omits the large private payload");
            var context = ((PacketContextProvider) (Object) observer.player.connection).getPacketContext();
            check(h, PolymerItemUtils.getRealItemStack(decoded, context, observer.player.registryAccess()) == decoded,
                    "Observer equipment intentionally carries no inventory roundtrip identity");
            var self = equipment(h, owner, owner.player.getId(), snapshot);
            check(h, ItemStack.matches(self, ordinary(owner, snapshot)), "Self equipment remains the full ordinary representation");
            check(h, ItemStack.matches(source, before) && ItemStack.matches(snapshot, before)
                            && owner.player.getMainHandItem() == source,
                    "Shared packet snapshot and exact owner inventory remain untouched");
            check(h, PacketContext.get() == null, "No recipient context leaks after encoding/decoding");
        }
        h.succeed();
    }

    @GameTest(structure = "destiny-test:w78_floor", maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void containersEntityDataUnknownItemsAndContextFreeEncodingRemainFull(GameTestHelper h) {
        var wire = new InventoryWireW92(h, new Vec3(4, 4, 8));
        wire.player.setAttached(WeaponLoadout.ENABLED, false);
        var source = item("austringer"); var before = source.copy();
        var full = ordinary(wire, source);
        wire.discard();
        wire.player.connection.send(new ClientboundContainerSetSlotPacket(7, 19, 0, source));
        var slot = wire.capture().stream().filter(ClientboundContainerSetSlotPacket.class::isInstance)
                .map(ClientboundContainerSetSlotPacket.class::cast).findFirst().orElseThrow();
        check(h, ItemStack.matches(slot.getItem(), full), "Container items retain every ordinary roundtrip component");

        var display = new Display.ItemDisplay(EntityTypes.ITEM_DISPLAY, h.getLevel());
        display.setItemStack(source);
        wire.player.connection.send(new ClientboundSetEntityDataPacket(display.getId(),
                display.getEntityData().getNonDefaultValues()));
        var metadata = wire.capture().stream().filter(ClientboundSetEntityDataPacket.class::isInstance)
                .map(ClientboundSetEntityDataPacket.class::cast).findFirst().orElseThrow();
        var metadataItem = metadata.packedItems().stream().map(value -> value.value())
                .filter(ItemStack.class::isInstance).map(ItemStack.class::cast).findFirst().orElseThrow();
        check(h, ItemStack.matches(metadataItem, full), "Item-display metadata stays outside the equipment hook");

        var unknown = new ItemStack(Items.DIAMOND);
        unknown.set(DataComponents.CUSTOM_DATA, source.get(DataComponents.CUSTOM_DATA));
        unknown.set(DataComponents.LORE, source.get(DataComponents.LORE));
        check(h, ItemStack.matches(unknown, equipment(h, wire, wire.player.getId() + 100000, unknown)),
                "Unrecognized vanilla equipment is byte-semantically unchanged");
        var nonCombat = source.copy();
        var tag = nonCombat.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putBoolean(WeaponItems.LIVE, false);
        nonCombat.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        check(h, ItemStack.matches(ordinary(wire, nonCombat),
                        equipment(h, wire, wire.player.getId() + 100000, nonCombat)),
                "A combat item without canonical live admission keeps its full ordinary representation");
        PacketContext.runWithoutContext(() -> {
            var buffer = new RegistryFriendlyByteBuf(Unpooled.buffer(), wire.player.registryAccess());
            try {
                int target = wire.player.getId() + 100000;
                check(h, PacketContext.get() == null && WeaponObserverEquipment.project(target, source, buffer) == source,
                        "No-context observer projection returns the exact source without recipient assumptions");
                // Polymer's ordinary item codec may still project without a recipient context.
                // Establish its full representation independently of the equipment hook.
                ItemStack.OPTIONAL_STREAM_CODEC.encode(buffer, source);
                var ordinaryNoContext = ItemStack.OPTIONAL_STREAM_CODEC.decode(buffer);
                check(h, ordinaryNoContext.has(DataComponents.CUSTOM_DATA) && ordinaryNoContext.has(DataComponents.LORE),
                        "The independent no-context ordinary codec baseline retains private data and lore");
                buffer.clear();
                var packet = new ClientboundSetEquipmentPacket(target,
                        List.of(Pair.of(EquipmentSlot.MAINHAND, source)));
                ClientboundSetEquipmentPacket.STREAM_CODEC.encode(buffer, packet);
                var decoded = ClientboundSetEquipmentPacket.STREAM_CODEC.decode(buffer);
                check(h, ItemStack.matches(ordinaryNoContext, decoded.getSlots().getFirst().getSecond()),
                        "No-context equipment encoding matches the independent full ordinary codec baseline");
                check(h, ItemStack.matches(source, before) && source.has(DataComponents.CUSTOM_DATA)
                                && source.has(DataComponents.LORE),
                        "No-context codecs preserve the source's full private data and lore");
            } finally { buffer.release(); }
        });
        check(h, ItemStack.matches(source, before), "All non-equipment probes preserve their shared source");
        h.succeed();
    }
}
