package kim.biryeong.destiny.test;

import it.unimi.dsi.fastutil.longs.Long2ObjectMap;
import it.unimi.dsi.fastutil.longs.LongSet;
import kim.biryeong.destiny.campaign.RisingCampaign;
import kim.biryeong.destiny.world.TemporaryActivityLevel;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ChunkMap;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.players.NameAndId;
import net.minecraft.util.ProblemReporter;
import net.minecraft.util.ProgressListener;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.TagValueInput;
import net.minecraft.world.phys.Vec3;
import xyz.nucleoid.fantasy.Fantasy;
import xyz.nucleoid.fantasy.RuntimeLevel;
import xyz.nucleoid.fantasy.RuntimeLevelConfig;
import xyz.nucleoid.fantasy.RuntimeLevelHandle;
import xyz.nucleoid.fantasy.util.VoidChunkGenerator;

import java.util.UUID;

/** Native save entry points, actual chunk unload/reload, and player checkpoint disk persistence. */
public final class TemporaryActivityLevelGameTests {
    private static void check(GameTestHelper h, boolean ok, String why) {
        h.assertTrue(ok, Component.literal(why));
    }

    private static RuntimeLevelHandle world(GameTestHelper h, boolean optimized) {
        var server = h.getLevel().getServer();
        var config = new RuntimeLevelConfig()
                .setGenerator(new VoidChunkGenerator(server.registryAccess().getOrThrow(Biomes.THE_VOID)))
                .setShouldTickTime(false);
        if (optimized) config.setLevelConstructor(TemporaryActivityLevel::new);
        var handle = Fantasy.get(server).openTemporaryLevel(
                Identifier.fromNamespaceAndPath("destiny-test", "save_policy_" + UUID.randomUUID()), config);
        handle.setTickWhenEmpty(true);
        TestCleanup.register(h, handle::delete);
        return handle;
    }

    /** Native ServerLevel.save calls these; the fixture does not replace native serialization. */
    private static final class SaveProgress implements ProgressListener {
        int stages;
        @Override public void progressStartNoAbort(Component text) { stages++; }
        @Override public void progressStart(Component text) { stages++; }
        @Override public void progressStage(Component text) { stages++; }
        @Override public void progressStagePercentage(int value) { }
        @Override public void stop() { }
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=60)
    public void periodicBulkSaveIsSkippedWithoutChangingNativeUnloadFlagOrTower(GameTestHelper h) {
        boolean rejected = false;
        try { new TemporaryActivityLevel(null, null, null, RuntimeLevel.Style.PERSISTENT); }
        catch (IllegalArgumentException expected) { rejected = true; }
        check(h, rejected, "Persistent construction fails before creating native world resources");
        var temporary = world(h, true).asLevel();
        var ordinary = world(h, false).asLevel();
        var skipped = new SaveProgress(); var nativeSave = new SaveProgress();
        temporary.save(skipped, false, false);
        ordinary.save(nativeSave, false, false);
        check(h, skipped.stages == 0 && nativeSave.stages > 0,
                "Only the owned policy skips the actual native bulk save boundary");
        check(h, !temporary.noSave && !ordinary.noSave,
                "Native chunk unload processing remains enabled for both levels");
        var tower = TowerSpawnWorld.open(h.getLevel().getServer());
        check(h, !(tower instanceof TemporaryActivityLevel) && !tower.noSave,
                "Permanent Tower does not acquire the disposable activity save policy");
        var towerSave = new SaveProgress(); tower.save(towerSave, false, false);
        check(h, towerSave.stages > 0, "Tower still reaches native persistent world serialization");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=1500)
    public void modifiedBlockSurvivesActualNativeChunkUnloadAndReloadWithoutBulkSave(GameTestHelper h) {
        var level = world(h, true).asLevel();
        var at = new BlockPos(2, 64, 2);
        level.setBlock(at, Blocks.GOLD_BLOCK.defaultBlockState(), 3);
        var before = level.getChunk(0, 0);
        check(h, before.isUnsaved(), "Changed chunk starts dirty");
        level.save(null, false, false);
        check(h, before.isUnsaved(), "Skipped bulk save does not serialize or acknowledge the dirty chunk");
        // No fixture tickets or forced unloads: the native UNKNOWN request expires normally.
        // Retaining this Java object does not keep the chunk in ChunkMap.
        int[] ticks = {0};
        h.onEachTick(() -> {
            // Other coordinates can retain work/tickets. Require this exact coordinate to
            // leave every native holder/unload set, rather than global ChunkMap quiescence.
            var state = targetState(level, before.getPos().pack());
            if (++ticks[0] % 200 == 0)
                kim.biryeong.destiny.DestinyGuardians.LOGGER.info(
                        "[TemporarySave QA] target={} dirty={} globalWork={} tickets={}", state,
                        before.isUnsaved(), level.getChunkSource().chunkMap.hasWork(),
                        level.getChunkSource().getDataStorage().get(net.minecraft.world.level.TicketStorage.TYPE)
                                .getTickets(before.getPos().pack()));
            if (!state.removed()) return;
            check(h, level.getChunkSource().getChunkNow(0, 0) == null,
                    "Native unload processing removed the full chunk");
            check(h, !before.isUnsaved(), "Native unload acknowledged serialization of the edited chunk");
            check(h, !level.noSave, "Unloading never required changing the native noSave flag");
            var restored = level.getChunk(0, 0);
            check(h, restored != before, "The same chunk coordinate reloads into a new native chunk object");
            check(h, restored.getBlockState(at).is(Blocks.GOLD_BLOCK),
                    "Individual native unload serialization preserves the edited block in a live instance");
            h.succeed();
        });
    }

    private record TargetState(boolean visible, boolean updating, boolean pendingUnload, boolean dropping) {
        boolean removed() { return !visible && !updating && !pendingUnload && !dropping; }
    }

    private static TargetState targetState(ServerLevel level, long key) {
        var map = level.getChunkSource().chunkMap;
        try {
            return new TargetState(contains(map, "visibleChunkMap", key), contains(map, "updatingChunkMap", key),
                    contains(map, "pendingUnloads", key), contains(map, "toDrop", key));
        } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }

    private static boolean contains(ChunkMap map, String name, long key) throws ReflectiveOperationException {
        var field = ChunkMap.class.getDeclaredField(name); field.setAccessible(true);
        var value = field.get(map);
        return value instanceof Long2ObjectMap<?> chunks ? chunks.containsKey(key) : ((LongSet) value).contains(key);
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=60)
    public void playerListSaveAllStillWritesAndRestoresCampaignCheckpoint(GameTestHelper h) {
        var server = h.getLevel().getServer(); var list = server.getPlayerList();
        var level = world(h, true).asLevel();
        var player = TestPlayers.create(h, new Vec3(2, 2, 2), 0, 0, "SavePolicyTest");
        var restored = TestPlayers.create(h, new Vec3(3, 2, 2), 0, 0, "SavePolicyReload");
        var checkpoint = new RisingCampaign.Stored("BREACH", true, true, false);
        // saveAll iterates actual PlayerList membership; a standalone fake player would not prove it.
        check(h, list.getPlayers().add(player), "Fixture owns a new PlayerList entry");
        try {
            player.setAttached(RisingCampaign.PROGRESS, checkpoint);
            player.setServerLevel(level);
            list.saveAll();
            var tag = list.loadPlayerData(new NameAndId(player.getGameProfile())).orElseThrow();
            restored.load(TagValueInput.create(ProblemReporter.DISCARDING, server.registryAccess(), tag));
            check(h, checkpoint.equals(restored.getAttached(RisingCampaign.PROGRESS)),
                    "PlayerList.saveAll writes the real persistent campaign attachment independently of level saves");
        } finally {
            list.getPlayers().remove(player);
            TestPlayers.remove(player); TestPlayers.remove(restored);
        }
        h.succeed();
    }
}
