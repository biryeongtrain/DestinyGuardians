package kim.biryeong.destiny.test;

import io.netty.buffer.Unpooled;
import kim.biryeong.destiny.world.DestinyWorldDistances;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetChunkCacheRadiusPacket;
import net.minecraft.network.protocol.game.ClientboundSetSimulationDistancePacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ChunkMap;
import net.minecraft.server.level.DistanceManager;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.dimension.BuiltinDimensionTypes;
import net.minecraft.world.phys.Vec3;
import xyz.nucleoid.fantasy.Fantasy;
import xyz.nucleoid.fantasy.RuntimeLevelConfig;
import xyz.nucleoid.fantasy.RuntimeLevelHandle;
import xyz.nucleoid.fantasy.util.VoidChunkGenerator;

import java.util.List;
import java.util.UUID;

/** Per-level native ticket radii and real client packet correction; no global server configuration edits persist. */
public final class DestinyWorldDistanceGameTests {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static RuntimeLevelHandle world(GameTestHelper h) {
        var server = h.getLevel().getServer();
        var config = new RuntimeLevelConfig().setDimensionType(BuiltinDimensionTypes.OVERWORLD)
                .setGenerator(new VoidChunkGenerator(server.registryAccess().getOrThrow(Biomes.THE_VOID)))
                .setShouldTickTime(false);
        var handle = Fantasy.get(server).openTemporaryLevel(
                Identifier.fromNamespaceAndPath("destiny-test", "distance_" + UUID.randomUUID()), config);
        handle.setTickWhenEmpty(false);
        return handle;
    }

    private static int nativeView(ServerLevel level) {
        try {
            var field = ChunkMap.class.getDeclaredField("serverViewDistance"); field.setAccessible(true);
            return field.getInt(level.getChunkSource().chunkMap);
        } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }

    private static int nativeSimulation(ServerLevel level) {
        try {
            var field = DistanceManager.class.getDeclaredField("simulationDistance"); field.setAccessible(true);
            return field.getInt(level.getChunkSource().chunkMap.getDistanceManager());
        } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=40)
    public void ownedNativeRadiiRemainBoundedWhilePublicWorldSettingsAndBlocksSurvive(GameTestHelper h) {
        var server = h.getLevel().getServer(); var list = server.getPlayerList();
        int oldView = list.getViewDistance(), oldSimulation = list.getSimulationDistance();
        RuntimeLevelHandle managed = null, ordinary = null;
        try {
            list.setViewDistance(32); list.setSimulationDistance(32);
            managed = world(h); ordinary = world(h);
            var level = managed.asLevel(); var publicLevel = ordinary.asLevel();
            var marker = new BlockPos(0, 64, 0);
            level.setBlock(marker, Blocks.GOLD_BLOCK.defaultBlockState(), 3);
            DestinyWorldDistances.manage(level);
            int view = Math.min(32, DestinyWorldDistances.configuredViewDistance());
            int simulation = Math.min(view, DestinyWorldDistances.configuredSimulationDistance());
            check(h, nativeView(level) == view && nativeSimulation(level) == simulation,
                    "Native ChunkMap and DistanceManager use bounded owned-level radii");
            check(h, nativeView(publicLevel) == 32 && nativeSimulation(publicLevel) == 32,
                    "An unregistered Fantasy/public world retains the actual global distances");
            list.setViewDistance(32); list.setSimulationDistance(32);
            check(h, nativeView(level) == view && nativeSimulation(level) == simulation,
                    "Native PlayerList global rewrites cannot expand the owned level");
            check(h, level.getBlockState(marker).is(Blocks.GOLD_BLOCK), "Distance policy never removes authored blocks");
            list.setViewDistance(2);
            check(h, nativeView(level) == 2 && nativeSimulation(level) == 2,
                    "A smaller global view is preserved and simulation does not exceed the effective view");
        } finally {
            if (managed != null) managed.delete();
            if (ordinary != null) ordinary.delete();
            list.setViewDistance(oldView); list.setSimulationDistance(oldSimulation);
        }
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=40)
    public void nativeClientPacketsCorrectGlobalResetsAndRestoreOnLeavingOwnedWorld(GameTestHelper h) {
        var server = h.getLevel().getServer(); var list = server.getPlayerList();
        int oldView = list.getViewDistance(), oldSimulation = list.getSimulationDistance();
        var handle = world(h); var level = handle.asLevel();
        var p = TestPlayers.create(h, new Vec3(2.5, 2, 6.5), 0, 0); var origin = p.level();
        List<ServerPlayer> members = level.players();
        try {
            list.setViewDistance(32); list.setSimulationDistance(32);
            DestinyWorldDistances.manage(level);
            p.setServerLevel(level); members.add(p); list.getPlayers().add(p); TestPlayers.drain(p);
            DestinyWorldDistances.synchronize(p);
            int view = DestinyWorldDistances.effectiveViewDistance(level);
            int simulation = DestinyWorldDistances.effectiveSimulationDistance(level);
            packets(h, p, view, simulation, false);
            DestinyWorldDistances.synchronize(p);
            check(h, TestPlayers.outbound(p).isEmpty(), "Unchanged per-connection distance projection is silent");
            list.setViewDistance(32);
            packets(h, p, view, simulation, true);
            list.setSimulationDistance(32);
            packets(h, p, view, simulation, false);
            members.remove(p); p.setServerLevel(origin);
            DestinyWorldDistances.synchronize(p);
            packets(h, p, 32, 32, false);
            DestinyWorldDistances.synchronize(p);
            check(h, TestPlayers.outbound(p).isEmpty(), "Returning to public world releases the connection projection");
        } finally {
            members.remove(p); list.getPlayers().remove(p); p.setServerLevel(origin);
            DestinyWorldDistances.synchronize(p);
            TestPlayers.remove(p); handle.delete();
            list.setViewDistance(oldView); list.setSimulationDistance(oldSimulation);
        }
        h.succeed();
    }

    private static void packets(GameTestHelper h, ServerPlayer p, int view, int simulation, boolean globalViewFirst) {
        var packets = TestPlayers.outbound(p);
        var views = packets.stream().filter(ClientboundSetChunkCacheRadiusPacket.class::isInstance)
                .map(ClientboundSetChunkCacheRadiusPacket.class::cast).toList();
        var simulations = packets.stream().filter(ClientboundSetSimulationDistancePacket.class::isInstance)
                .map(ClientboundSetSimulationDistancePacket.class::cast).toList();
        check(h, !views.isEmpty() && !simulations.isEmpty(), "Real client channel receives both distance packet types");
        check(h, views.getLast().getRadius() == view && simulations.getLast().simulationDistance() == simulation,
                "The final advertised values match actual per-level radii");
        if (globalViewFirst) check(h, views.size() >= 2 && views.getFirst().getRadius() == 32,
                "Vanilla global32 broadcast is followed by a forced cap correction even when cached cap is unchanged");
        for (var packet : views) {
            var bytes = new FriendlyByteBuf(Unpooled.buffer());
            try {
                ClientboundSetChunkCacheRadiusPacket.STREAM_CODEC.encode(bytes, packet);
                check(h, ClientboundSetChunkCacheRadiusPacket.STREAM_CODEC.decode(bytes).getRadius() == packet.getRadius()
                        && bytes.readableBytes() == 0, "Native cache-radius packet codec round-trips");
            } finally { bytes.release(); }
        }
        for (var packet : simulations) {
            var bytes = new FriendlyByteBuf(Unpooled.buffer());
            try {
                ClientboundSetSimulationDistancePacket.STREAM_CODEC.encode(bytes, packet);
                check(h, ClientboundSetSimulationDistancePacket.STREAM_CODEC.decode(bytes).simulationDistance() == packet.simulationDistance()
                        && bytes.readableBytes() == 0, "Native simulation-distance packet codec round-trips");
            } finally { bytes.release(); }
        }
    }
}
