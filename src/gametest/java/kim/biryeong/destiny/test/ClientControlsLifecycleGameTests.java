package kim.biryeong.destiny.test;

import kim.biryeong.destiny.input.ClientControls;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

import java.util.function.Function;

/** Synchronous callback invalidation and same-UUID connection ownership regressions. */
public final class ClientControlsLifecycleGameTests {
    @SuppressWarnings("unchecked")
    private static Function<ServerPlayer, ClientControls.Capability> detector() {
        try {
            var field = ClientControls.class.getDeclaredField("detector");
            field.setAccessible(true);
            return (Function<ServerPlayer, ClientControls.Capability>) field.get(null);
        } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=30)
    public void clearedSessionDuringDetectionSkipsTickAndMountPrediction(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2.5, 2, 6.5), 0, 0);
        var server = h.getLevel().getServer();
        var players = server.getPlayerList().getPlayers();
        var original = detector();
        try {
            // Invalidate precisely between session creation and the old tick's map lookup.
            ClientControls.setDetector(player -> {
                if (player != p) return original.apply(player);
                ClientControls.forget(player);
                return new ClientControls.Capability(true, "4.2.0");
            });
            players.add(p);
            ClientControls.tick(server);
            h.assertTrue(!ClientControls.mountPrediction(p) && !ClientControls.gcb(p),
                    Component.literal("Retired session cannot crash tick or enable stale capabilities"));
        } finally {
            players.remove(p);
            ClientControls.setDetector(original);
            ClientControls.forget(p);
            TestPlayers.remove(p);
        }
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=30)
    public void replacementConnectionDoesNotInheritOrLoseCapabilitiesToOldCleanup(GameTestHelper h) {
        var old = TestPlayers.create(h, new Vec3(2.5, 2, 6.5), 0, 0);
        var fresh = TestPlayers.create(h, new Vec3(3.5, 2, 6.5), 0, 0);
        var fixtureId = fresh.getUUID();
        fresh.setUUID(old.getUUID());
        var original = detector();
        try {
            ClientControls.setDetector(player -> player == old
                    ? new ClientControls.Capability(true, "4.2.0") : player == fresh
                    ? new ClientControls.Capability(false, "") : original.apply(player));
            h.assertTrue(ClientControls.gcb(old), Component.literal("Original connection detects GCB"));
            h.assertTrue(!ClientControls.gcb(fresh), Component.literal("Same UUID with a new connection starts fresh"));
            ClientControls.setDetector(player -> player == fresh
                    ? new ClientControls.Capability(true, "4.2.0") : original.apply(player));
            h.assertTrue(ClientControls.mountPrediction(fresh), Component.literal("Fresh handshake enables prediction"));
            ClientControls.setDetector(player -> player == fresh
                    ? new ClientControls.Capability(false, "") : original.apply(player));
            ClientControls.forget(old);
            h.assertTrue(ClientControls.mountPrediction(fresh),
                    Component.literal("Late cleanup from old connection cannot erase the fresh handshake"));
        } finally {
            ClientControls.setDetector(original);
            ClientControls.forget(old);
            ClientControls.forget(fresh);
            fresh.setUUID(fixtureId);
            TestPlayers.remove(old);
            TestPlayers.remove(fresh);
        }
        h.succeed();
    }
}
