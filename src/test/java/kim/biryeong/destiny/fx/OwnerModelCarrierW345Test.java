package kim.biryeong.destiny.fx;

import io.netty.channel.embedded.EmbeddedChannel;
import io.netty.channel.ChannelOutboundHandlerAdapter;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelPromise;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.*;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

class OwnerModelCarrierW345Test {
    private static final int OWNER=42, ANCHOR=100, LIMB=101;
    @BeforeAll static void bootstrap() {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        var helmet = net.minecraft.world.item.Items.DIAMOND_HELMET.builtInRegistryHolder();
        if (!helmet.areComponentsBound()) helmet.bindComponents(net.minecraft.core.component.DataComponentMap.EMPTY);
    }
    private static ClientboundAddEntityPacket add(int id, double x) {
        return new ClientboundAddEntityPacket(id, UUID.randomUUID(), x, 64, 0, 0, 0,
                EntityTypes.ITEM_DISPLAY, 0, Vec3.ZERO, 0);
    }
    private static ClientboundSetEntityDataPacket flags(int id, int flags) {
        return new ClientboundSetEntityDataPacket(id, List.of(new SynchedEntityData.DataValue<>(
                0, EntityDataSerializers.BYTE, (byte)flags)));
    }
    private static OwnerModelCarrier.MountRelay relay() {
        return new OwnerModelCarrier.MountRelay(OWNER, ANCHOR, Set.of(LIMB),
                List.of(add(ANCHOR, 12)), flags(OWNER, 2));
    }
    private static List<Packet<?>> flat(Packet<?> packet) {
        var list=new ArrayList<Packet<?>>();
        if(packet instanceof ClientboundBundlePacket b) b.subPackets().forEach(list::add);
        else list.add(packet);
        assertTrue(list.stream().noneMatch(ClientboundBundlePacket.class::isInstance));
        return list;
    }
    @Test void firstModelSpawnCarriesItsAnchorAndHiddenBodyWithoutWaitingForSuccessCallback() {
        var limb=add(LIMB, 999);
        var packets=flat(relay().rewrite(limb));
        assertEquals(4, packets.size());
        assertEquals(ANCHOR, ((ClientboundAddEntityPacket)packets.get(0)).getId());
        assertEquals(12, ((ClientboundAddEntityPacket)packets.get(0)).getX());
        assertEquals((byte)34, ((ClientboundSetEntityDataPacket)packets.get(1)).packedItems().getFirst().value());
        assertTrue(((ClientboundSetEquipmentPacket)packets.get(2)).getSlots().stream().allMatch(p -> p.getSecond().isEmpty()));
        assertSame(limb, packets.get(3));
    }
    @Test void delayedFlushStillOrdersAnchorBeforeModelAndNeverShowsVanillaBody() {
        var relay=relay();
        var held=new ArrayList<Runnable>();
        var gate=new ChannelOutboundHandlerAdapter() {
            @Override public void write(ChannelHandlerContext c,Object m,ChannelPromise p) {
                held.add(()->c.write(m,p));
            }
        };
        var channel=new EmbeddedChannel(relay,gate);
        try {
            channel.writeAndFlush(add(LIMB, 999));
            channel.writeAndFlush(flags(OWNER, 8));
            assertNull(channel.readOutbound());
            // Release the write backlog after the server has progressed. No spawn callback is run.
            held.forEach(Runnable::run);channel.flushOutbound();
            var spawn=flat(channel.readOutbound());
            assertEquals(ANCHOR, ((ClientboundAddEntityPacket)spawn.getFirst()).getId());
            var update=flat(channel.readOutbound());
            assertEquals((byte)40, ((ClientboundSetEntityDataPacket)update.getFirst()).packedItems().getFirst().value());
        } finally { channel.finishAndReleaseAll(); }
    }
    @Test void ownerFlagsArePreservedAndForeignPlayersAreUntouched() {
        var relay=relay();
        var foreign=flags(43, 9);
        assertSame(foreign,relay.rewrite(foreign));
        var hidden=(ClientboundSetEntityDataPacket)flat(relay.rewrite(flags(OWNER,0x49))).getFirst();
        assertEquals((byte)0x69,hidden.packedItems().getFirst().value());
        var already=flags(OWNER,0x69);
        assertSame(already,relay.rewrite(already));
    }
    @Test void delayedEquipmentUpdatesCannotRevealVanillaArmor() {
        var slots=List.of(com.mojang.datafixers.util.Pair.of(net.minecraft.world.entity.EquipmentSlot.HEAD,
                new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.DIAMOND_HELMET)));
        var incoming=new ClientboundSetEquipmentPacket(OWNER,slots);
        var rewritten=(ClientboundSetEquipmentPacket)flat(relay().rewrite(incoming)).getFirst();
        assertTrue(rewritten.getSlots().stream().allMatch(p -> p.getSecond().isEmpty()));
        assertFalse(incoming.getSlots().getFirst().getSecond().isEmpty());
        var other=new ClientboundSetEquipmentPacket(43,slots);
        assertSame(other,relay().rewrite(other));
    }

    @Test void cameraRespawnRecreatesAnchorButOrdinaryModelResendsDoNotDuplicateIt() {
        var relay=relay();
        var limb=add(LIMB,999);
        assertEquals(4,flat(relay.rewrite(limb)).size());
        assertSame(limb,relay.rewrite(limb));
        var respawn=new ClientboundRespawnPacket(null,(byte)0);
        assertSame(respawn,relay.rewrite(respawn));
        assertEquals(4,flat(relay.rewrite(limb)).size());
    }
    @Test void closingRelayRestoresOriginalFlagsAndDoesNotAffectReplacement() {
        var relay=relay();var channel=new EmbeddedChannel(relay);
        try {
            var restore=flags(OWNER,2);
            channel.pipeline().remove(relay);
            channel.writeOutbound(restore);
            assertSame(restore,channel.readOutbound());
            var replacement=relay();channel.pipeline().addLast(replacement);
            channel.writeOutbound(add(LIMB,999));
            assertEquals(4,flat(channel.readOutbound()).size());
        } finally { channel.finishAndReleaseAll(); }
    }
}
