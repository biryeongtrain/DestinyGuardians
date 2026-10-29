package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.world.TowerChunkGenerator;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import net.minecraft.gametest.framework.GameTestHelper;

/** Explicit tower-only suite. Run manually in a disposable server with destiny.tower.enabled=true. */
public final class TowerW232GameTests {
    private static final String FLOOR = "destiny-test:floor", ENV = "destiny-test:w90_isolated";
    private static void check(GameTestHelper h, boolean ok, String message) { h.assertTrue(ok, Component.literal(message)); }

    @GameTest(structure=FLOOR, environment=ENV, maxTicks=100, manualOnly=true)
    public void persistentOpenHasIndependentRulesAndFiniteSparseGeneration(GameTestHelper h) {
        var server = h.getLevel().getServer();
        var previousSpawn = server.getRespawnData();
        var previousRules = server.overworld().getGameRules();
        boolean previousMobSpawning = previousRules.get(GameRules.SPAWN_MOBS);
        var tower = TowerSpawnWorld.open(server);
        check(h, TowerSpawnWorld.open(server) == tower, "Repeated persistent open reuses the same level");
        check(h, tower.getGameRules() != previousRules && tower.clockManager() != server.clockManager(), "Hub owns rules and clock");
        check(h, previousSpawn.equals(server.getRespawnData()) && previousRules.get(GameRules.SPAWN_MOBS) == previousMobSpawning,
                "Existing spawn and game rules are untouched");
        check(h, !tower.getGameRules().get(GameRules.SPAWN_MOBS) && !tower.getGameRules().get(GameRules.ADVANCE_TIME), "No spawning or clock advancement");
        var generator = (TowerChunkGenerator) tower.getChunkSource().getGenerator();
        var map = generator.map(); var b = map.manifest().bounds();
        check(h, tower.getWorldBorder().getCenterZ() == (b.minZ() + b.maxZ() + 1) / 2.0, "Negative-Z bounds determine border center");
        check(h, generator.blockAt(b.maxX()+1, b.maxY(), b.maxZ()).isAir(), "Outside finite map is void");
        check(h, generator.getBaseHeight(b.maxX()+1, b.maxZ()+1, Heightmap.Types.WORLD_SURFACE, tower, null) == tower.getMinY(), "Empty column has no terrain");
        BlockPos spawn = BlockPos.containing(TowerSpawnWorld.safeSpawn(tower, map).orElseThrow());
        check(h, TowerSpawnWorld.isSafeArrival(tower, Vec3.atBottomCenterOf(spawn)), "Loaded chunk has floor and headroom");
        int[] checked = {0};
        map.forChunk(spawn.getX() >> 4, spawn.getZ() >> 4, (x,y,z,index) -> {
            if (checked[0]++ < 8) check(h, tower.getBlockState(new BlockPos(x,y,z)).equals(generator.blockAt(x,y,z)), "Generated blocks preserve palette states");
        });
        check(h, checked[0] > 0, "Spawn chunk contains real source geometry");
        h.succeed();
    }

    @GameTest(structure=FLOOR, environment=ENV, maxTicks=100, manualOnly=true)
    public void transferCleansAbilitiesPreservesModeAndProtectsOnlyTower(GameTestHelper h) {
        var tower = TowerSpawnWorld.open(h.getLevel().getServer());
        var player = TestPlayers.create(h, new Vec3(2.5,1,6.5), 0, 0, "TowerTransfer");
        TestCleanup.register(h, () -> {
            player.level().removePlayerImmediately(player, Entity.RemovalReason.DISCARDED);
            TestPlayers.remove(player);
        });
        check(h, TowerSpawnWorld.mayModify(h.getLevel(), player), "Existing game world is not protected by hub policy");
        check(h, TowerSpawnWorld.teleport(player), "Safe transfer succeeds");
        check(h, player.level() == tower && player.gameMode() == GameType.SURVIVAL, "Transfer preserves mode");
        check(h, !SuperCamera.active(player) && player.getCamera() == player
                && Guardians.runtime(player).superSession == null, "Active ability and camera ownership retired");
        BlockPos floor = player.blockPosition().below();
        var state = tower.getBlockState(floor);
        check(h, !PlayerBlockBreakEvents.BEFORE.invoker().beforeBlockBreak(tower, player, floor, state, null), "Normal player cannot break hub blocks");
        check(h, !ServerLivingEntityEvents.ALLOW_DAMAGE.invoker().allowDamage(player, tower.damageSources().generic(), 4), "Hub player damage is rejected");
        float health = player.getHealth();
        tower.explode(null, player.getX(), player.getY(), player.getZ(), 8, true, Level.ExplosionInteraction.TNT);
        check(h, tower.getBlockState(floor).equals(state) && player.getHealth() == health, "Explosion leaves source blocks and player intact");
        check(h, !tower.canSpreadFireAround(floor), "Fire spread is disabled in hub");
        player.setGameMode(GameType.CREATIVE);
        check(h, TowerSpawnWorld.teleport(player) && player.gameMode() == GameType.CREATIVE, "Creative transfer preserves mode");
        check(h, !TowerSpawnWorld.mayModify(tower, player), "Creative alone does not grant admin editing");
        AbilityService.cleanup(player);
        h.succeed();
    }

    @GameTest(structure=FLOOR, environment=ENV, maxTicks=100, manualOnly=true)
    public void blockedArrivalIsRejectedWithoutRepairingTheMap(GameTestHelper h) {
        var tower = TowerSpawnWorld.open(h.getLevel().getServer());
        var map = ((TowerChunkGenerator)tower.getChunkSource().getGenerator()).map();
        Vec3 safe = TowerSpawnWorld.safeSpawn(tower, map).orElseThrow();
        BlockPos head = BlockPos.containing(safe).above();
        var original = tower.getBlockState(head);
        try {
            tower.setBlockAndUpdate(head, Blocks.STONE.defaultBlockState());
            check(h, !TowerSpawnWorld.isSafeArrival(tower, safe), "Occupied headroom is never an arrival");
            var alternative = TowerSpawnWorld.safeSpawn(tower, map);
            check(h, alternative.isEmpty() || !alternative.get().equals(safe), "Search rejects blocked exact spawn");
            check(h, tower.getBlockState(head).is(Blocks.STONE), "Safety lookup does not clear or repair the map");
        } finally { tower.setBlockAndUpdate(head, original); }
        h.succeed();
    }

    @GameTest(structure=FLOOR, environment=ENV, maxTicks=100, manualOnly=true)
    public void fallThresholdReturnsAlivePlayerAndClearsMomentum(GameTestHelper h) {
        var tower = TowerSpawnWorld.open(h.getLevel().getServer());
        var player = TestPlayers.create(h, new Vec3(2.5,1,6.5), 0, 0, "TowerFall");
        TestCleanup.register(h, () -> {
            player.level().removePlayerImmediately(player, Entity.RemovalReason.DISCARDED);
            TestPlayers.remove(player);
        });
        check(h, TowerSpawnWorld.teleport(player), "Player enters tower");
        var map = ((TowerChunkGenerator)tower.getChunkSource().getGenerator()).map();
        int threshold = map.manifest().returnBelowY();
        check(h, threshold == 60, "Courtyard rescue threshold is Y=60");
        player.setPos(player.getX(), threshold + 0.01, player.getZ());
        TowerSpawnWorld.tick(tower.getServer());
        check(h, player.getY() < threshold + 1, "Above threshold is not rescued early");
        player.setPos(player.getX(), threshold, player.getZ());
        player.setDeltaMovement(0, -2, 0);
        TowerSpawnWorld.tick(tower.getServer());
        check(h, TowerSpawnWorld.isSafeArrival(tower, player.position()) && player.getY() > threshold,
                "Exact threshold returns player to safe spawn");
        check(h, player.isAlive() && player.getHealth() == 20 && player.getDeltaMovement().equals(Vec3.ZERO),
                "Rescue preserves health and clears falling momentum");
        player.setPos(player.getX(), threshold - 10, player.getZ());
        TowerSpawnWorld.tick(tower.getServer());
        check(h, TowerSpawnWorld.isSafeArrival(tower, player.position()), "Below threshold also returns safely");
        h.succeed();
    }

    @GameTest(structure=FLOOR, environment=ENV, maxTicks=100, manualOnly=true)
    public void playerAttacksAndCustomDamageAreBlockedOnlyInTower(GameTestHelper h) {
        var tower = TowerSpawnWorld.open(h.getLevel().getServer());
        var attacker = TestPlayers.create(h, new Vec3(2.5,1,6.5), 0, 0, "TowerAttacker");
        var target = TestPlayers.create(h, new Vec3(3.5,1,6.5), 0, 0, "TowerTarget");
        TestCleanup.register(h, () -> {
            for (var p : java.util.List.of(attacker, target)) {
                p.level().removePlayerImmediately(p, Entity.RemovalReason.DISCARDED);
                TestPlayers.remove(p);
            }
        });
        check(h, TowerSpawnWorld.mayAttack(h.getLevel(), target), "Other worlds retain their combat policy");
        check(h, TowerSpawnWorld.teleport(attacker) && TowerSpawnWorld.teleport(target), "Both players enter tower");
        check(h, !tower.getGameRules().get(GameRules.PVP), "Vanilla PvP rule is disabled");
        for (var mode : java.util.List.of(GameType.SURVIVAL, GameType.CREATIVE)) {
            attacker.setGameMode(mode);
            check(h, AttackEntityCallback.EVENT.invoker().interact(attacker, tower, InteractionHand.MAIN_HAND, target, null)
                    == InteractionResult.FAIL, "Melee attack is rejected in both survival and creative");
        }
        float health = target.getHealth();
        target.damageCooldownTime = 7;
        kim.biryeong.destiny.combat.Combat.damage(tower, attacker, target, 10,
                kim.biryeong.destiny.guardian.Element.SOLAR);
        check(h, target.getHealth() == health && target.damageCooldownTime == 7,
                "Custom damage is rejected before touching target combat state");
        target.hurtServer(tower, attacker.damageSources().playerAttack(attacker), 10);
        check(h, target.getHealth() == health, "Vanilla damage cannot hurt hub players");
        h.succeed();
    }
}
