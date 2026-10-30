package kim.biryeong.destiny.fx;

import io.netty.buffer.Unpooled;
import io.netty.channel.embedded.EmbeddedChannel;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBundlePacket;
import net.minecraft.network.protocol.game.ClientboundRemoveEntitiesPacket;
import net.minecraft.network.protocol.game.ClientboundSetPassengersPacket;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Pure packet regression against the production MountRelay, not a copied algorithm.
 * No server, real channel, player, world, carrier construction or animation required.
 * Fixed fixtures only: eight tests, at most 32 repeated rewrites, ten seconds per test.
 * Fabric/BM injected bundle-marker preservation and native visibility remain integration checks.
 */
@Timeout(10)
class IntroSelfCarrierW260Test {
    private static final int OWNER = 42, CARRIER = 1000, OTHER_ACTOR = 43;
    private static final int LIMB_A = 101, LIMB_B = 102, HUD = 201, REAL_RIDER = 301, FOREIGN_LIMB = 401;

    @BeforeAll static void bootstrap() {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
    }

    private static IntroSelfCarrier.MountRelay relay() {
        return new IntroSelfCarrier.MountRelay(OWNER, CARRIER, Set.of(LIMB_A, LIMB_B));
    }

    @Test void ownerLimbsMoveToCarrierAndInputIsNotMutated() {
        var incoming = mount(OWNER, LIMB_B, LIMB_A);
        var result = flat(relay().rewrite(incoming));
        assertEquals(2, result.size());
        assertMount(result.get(0), OWNER);
        assertMount(result.get(1), CARRIER, LIMB_B, LIMB_A);
        assertMount(incoming, OWNER, LIMB_B, LIMB_A);
    }

    @Test void hudRealAndForeignPassengersKeepTheirOwnerAndRelativeOrder() {
        var incoming = mount(OWNER, HUD, LIMB_B, REAL_RIDER, LIMB_A, FOREIGN_LIMB);
        var result = flat(relay().rewrite(incoming));
        assertEquals(2, result.size());
        assertMount(result.get(0), OWNER, HUD, REAL_RIDER, FOREIGN_LIMB);
        assertMount(result.get(1), CARRIER, LIMB_B, LIMB_A);
        assertMount(incoming, OWNER, HUD, LIMB_B, REAL_RIDER, LIMB_A, FOREIGN_LIMB);
    }

    @Test void otherActorCarrierAndNonOwnedPacketsRetainObjectIdentity() {
        var relay = relay();
        // Even a colliding display ID must not redirect another vehicle's riders.
        var other = mount(OTHER_ACTOR, LIMB_A, FOREIGN_LIMB, HUD);
        var carrier = mount(CARRIER, LIMB_A, LIMB_B);
        var hudOnly = mount(OWNER, HUD, REAL_RIDER);
        var empty = mount(OWNER);
        var removal = new ClientboundRemoveEntitiesPacket(OWNER, LIMB_A);
        var untouchedBundle = bundle(other, hudOnly, removal);
        for (Packet<?> packet : List.of(other, carrier, hudOnly, empty, removal, untouchedBundle))
            assertSame(packet, relay.rewrite(packet));
        assertSame(hudOnly, new IntroSelfCarrier.MountRelay(OWNER, CARRIER, Set.of()).rewrite(hudOnly));
    }

    @Test void changedBundleIsFlatPreservesPacketOrderAndDoesNotMutateBroadcastSource() {
        var before = new ClientboundRemoveEntitiesPacket(900);
        var own = mount(OWNER, HUD, LIMB_A);
        var other = mount(OTHER_ACTOR, FOREIGN_LIMB);
        var after = new ClientboundRemoveEntitiesPacket(901);
        var incoming = bundle(before, own, other, after);
        var result = flat(relay().rewrite(incoming));
        assertEquals(5, result.size());
        assertSame(before, result.get(0));
        assertMount(result.get(1), OWNER, HUD);
        assertMount(result.get(2), CARRIER, LIMB_A);
        assertSame(other, result.get(3));
        assertSame(after, result.get(4));
        assertEquals(List.of(before, own, other, after), children(incoming));
        assertMount(own, OWNER, HUD, LIMB_A);
    }

    @Test void nestedInputWithOwnedMountProducesNoNestedOutputBundles() {
        // Synthetic nesting exercises recursion; this invalid wire shape must not be emitted.
        var other = mount(OTHER_ACTOR, FOREIGN_LIMB);
        var own = mount(OWNER, LIMB_B, HUD);
        var untouchedNested = bundle(other);
        var inner = bundle(untouchedNested, own);
        var incoming = bundle(inner, other);
        var result = flat(relay().rewrite(incoming));
        assertEquals(4, result.size());
        assertSame(other, result.get(0));
        assertMount(result.get(1), OWNER, HUD);
        assertMount(result.get(2), CARRIER, LIMB_B);
        assertSame(other, result.get(3));
        assertEquals(List.of(inner, other), children(incoming));
        assertEquals(List.of(untouchedNested, own), children(inner));
        assertEquals(List.of(other), children(untouchedNested));
    }

    @Test void repeatedSnapshotsStayBoundedAndAlreadyRewrittenPacketsAreUnchanged() {
        var relay = relay();
        var incoming = mount(OWNER, LIMB_A, HUD, LIMB_B);
        for (int snapshot = 0; snapshot < 32; snapshot++) {
            var rewritten = relay.rewrite(incoming);
            var result = flat(rewritten);
            assertEquals(2, result.size());
            assertMount(result.get(0), OWNER, HUD);
            assertMount(result.get(1), CARRIER, LIMB_A, LIMB_B);
            assertSame(rewritten, relay.rewrite(rewritten));
        }
        var noOp = bundle(mount(OTHER_ACTOR, LIMB_A), mount(OWNER, HUD));
        assertSame(noOp, relay.rewrite(noOp));
    }

    @Test void relayOwnsAnImmutableDisplayIdSnapshot() {
        var ids = new HashSet<>(Set.of(LIMB_A));
        var relay = new IntroSelfCarrier.MountRelay(OWNER, CARRIER, ids);
        ids.clear(); ids.add(LIMB_B);
        var result = flat(relay.rewrite(mount(OWNER, LIMB_A, LIMB_B)));
        assertMount(result.get(0), OWNER, LIMB_B);
        assertMount(result.get(1), CARRIER, LIMB_A);
    }

    @Test void embeddedOutboundUsesProductionWriteAndRemovalRestoresPassThrough() {
        var relay = relay();
        var channel = new EmbeddedChannel(relay);
        try {
            Object foreignMessage = new Object();
            assertTrue(channel.writeOutbound(foreignMessage));
            assertSame(foreignMessage, channel.readOutbound());
            var incoming = mount(OWNER, HUD, LIMB_A);
            assertTrue(channel.writeOutbound(incoming));
            Packet<?> rewritten = channel.readOutbound();
            var result = flat(rewritten);
            assertMount(result.get(0), OWNER, HUD);
            assertMount(result.get(1), CARRIER, LIMB_A);
            assertNull(channel.readOutbound());
            channel.pipeline().remove(relay);
            assertTrue(channel.writeOutbound(incoming));
            assertSame(incoming, channel.readOutbound());
            assertNull(channel.readOutbound());
            channel.checkException();
        } finally { channel.finishAndReleaseAll(); }
    }

    private static ClientboundSetPassengersPacket mount(int vehicle, int... riders) {
        FriendlyByteBuf buffer = new FriendlyByteBuf(Unpooled.buffer());
        try {
            buffer.writeVarInt(vehicle);
            buffer.writeVarIntArray(riders);
            return ClientboundSetPassengersPacket.STREAM_CODEC.decode(buffer);
        } finally { buffer.release(); }
    }

    @SafeVarargs private static ClientboundBundlePacket bundle(Packet<? super ClientGamePacketListener>... packets) {
        return new ClientboundBundlePacket(List.of(packets));
    }

    private static List<Packet<? super ClientGamePacketListener>> children(ClientboundBundlePacket bundle) {
        var packets = new ArrayList<Packet<? super ClientGamePacketListener>>();
        bundle.subPackets().forEach(packets::add);
        return packets;
    }

    private static List<Packet<? super ClientGamePacketListener>> flat(Packet<?> packet) {
        var packets = children(assertInstanceOf(ClientboundBundlePacket.class, packet));
        for (var child : packets) assertFalse(child instanceof ClientboundBundlePacket, "Nested output bundle");
        return packets;
    }

    private static void assertMount(Packet<?> packet, int vehicle, int... riders) {
        var mount = assertInstanceOf(ClientboundSetPassengersPacket.class, packet);
        assertEquals(vehicle, mount.getVehicle());
        assertArrayEquals(riders, mount.getPassengers());
    }
}
