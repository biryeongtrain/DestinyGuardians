package kim.biryeong.destiny.tutorial;

import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Difficulty;
import net.minecraft.world.clock.WorldClocks;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.dimension.BuiltinDimensionTypes;
import net.minecraft.world.level.gamerules.GameRules;
import xyz.nucleoid.fantasy.Fantasy;
import xyz.nucleoid.fantasy.RuntimeLevelConfig;
import xyz.nucleoid.fantasy.RuntimeLevelHandle;
import xyz.nucleoid.fantasy.util.VoidChunkGenerator;

import java.util.ArrayList;
import java.util.List;

/** A temporary void world holding one private lane per tutorial player. Never touches the Tower or overworld. */
final class TutorialWorld {
    static final net.minecraft.resources.Identifier ID = DestinyGuardians.id("tutorial");
    private static RuntimeLevelHandle handle;
    private static final List<TutorialCourse> LANES = new ArrayList<>();
    private static final List<Boolean> USED = new ArrayList<>();

    private TutorialWorld() { }

    static ServerLevel open(MinecraftServer server) {
        if (handle != null && handle.asLevel().getServer() == server) return handle.asLevel();
        var config = new RuntimeLevelConfig()
                .setDimensionType(BuiltinDimensionTypes.OVERWORLD)
                .setGenerator(new VoidChunkGenerator(server.registryAccess().getOrThrow(Biomes.THE_VOID)))
                .setDifficulty(Difficulty.NORMAL)
                .setMirrorOverworldGameRules(false).setMirrorOverworldClocks(false).setMirrorOverworldDifficulty(false)
                .setShouldTickTime(false).setClockTime(WorldClocks.OVERWORLD, 23200, true)
                .setGameRule(GameRules.ADVANCE_WEATHER, false)
                .setGameRule(GameRules.SPAWN_MOBS, false).setGameRule(GameRules.SPAWN_MONSTERS, false)
                .setGameRule(GameRules.SPAWN_PATROLS, false).setGameRule(GameRules.SPAWN_PHANTOMS, false)
                .setGameRule(GameRules.SPAWN_WANDERING_TRADERS, false).setGameRule(GameRules.MOB_GRIEFING, false)
                .setGameRule(GameRules.TNT_EXPLODES, false).setGameRule(GameRules.PROJECTILES_CAN_BREAK_BLOCKS, false)
                .setGameRule(GameRules.FIRE_SPREAD_RADIUS_AROUND_PLAYER, 0).setGameRule(GameRules.RANDOM_TICK_SPEED, 0)
                .setGameRule(GameRules.BLOCK_DROPS, false).setGameRule(GameRules.MOB_DROPS, false)
                .setGameRule(GameRules.ENTITY_DROPS, false).setGameRule(GameRules.PVP, false)
                .setGameRule(GameRules.FALL_DAMAGE, false).setGameRule(GameRules.KEEP_INVENTORY, true);
        handle = Fantasy.get(server).openTemporaryLevel(ID, config);
        handle.asLevel().getWorldBorder().setSize(60_000);
        LANES.clear();
        USED.clear();
        DestinyGuardians.LOGGER.info("튜토리얼 월드 준비 완료: {}", ID);
        return handle.asLevel();
    }

    static boolean isTutorial(Level level) {
        return handle != null && level == handle.asLevel();
    }

    static TutorialCourse acquire(MinecraftServer server) {
        ServerLevel level = open(server);
        for (int i = 0; i < LANES.size(); i++) if (!USED.get(i)) { USED.set(i, true); return LANES.get(i); }
        var course = new TutorialCourse(level, LANES.size());
        LANES.add(course);
        USED.add(true);
        return course;
    }

    static void release(TutorialCourse course) {
        int i = LANES.indexOf(course);
        if (i >= 0) USED.set(i, false);
        course.destroyDecorations();
    }

    static void tickDecorations(long tick) {
        for (int i = 0; i < LANES.size(); i++) if (USED.get(i)) LANES.get(i).tickDecorations(tick);
    }

    static void stopped(MinecraftServer server) {
        if (handle != null && handle.asLevel().getServer() == server) {
            LANES.forEach(TutorialCourse::destroyDecorations);
            LANES.clear();
            USED.clear();
            handle = null;
        }
    }
}
