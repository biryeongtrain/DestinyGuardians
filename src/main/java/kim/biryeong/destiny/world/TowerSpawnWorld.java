package kim.biryeong.destiny.world;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.AttackBlockCallback;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.fabricmc.fabric.api.event.player.UseItemCallback;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.permissions.Permissions;
import net.minecraft.stats.Stats;
import net.minecraft.world.Difficulty;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.clock.WorldClocks;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BucketItem;
import net.minecraft.world.item.SolidBucketItem;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.dimension.BuiltinDimensionTypes;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import xyz.nucleoid.fantasy.Fantasy;
import xyz.nucleoid.fantasy.RuntimeLevel;
import xyz.nucleoid.fantasy.RuntimeLevelConfig;
import xyz.nucleoid.fantasy.RuntimeLevelHandle;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

/** Server-only persistent hub; never changes the overworld spawn, terrain, rules, or player mode. */
public final class TowerSpawnWorld {
    public static final Identifier ID = Identifier.fromNamespaceAndPath("destiny", "tower");
    public static final ResourceKey<Level> KEY = ResourceKey.create(Registries.DIMENSION, ID);
    private static boolean initialized;
    private static State state;
    private static final Map<UUID, Integer> RETRY_AFTER = new HashMap<>();
    private static final Map<UUID, ServerPlayer> PENDING_JOINS = new HashMap<>();
    private record State(MinecraftServer server, RuntimeLevelHandle handle, TowerVoxelMap map, TowerDetailPass details, TowerMaterialPass materials,
                         TowerBakedMaterialPass baked) {}
    private TowerSpawnWorld() {}

    /** Exact 26.3 server hooks: all vanilla explosion entry points dispatch here. */
    private static final class TowerLevel extends RuntimeLevel {
        private TowerLevel(MinecraftServer server, ResourceKey<Level> key, RuntimeLevelConfig config, Style style) {
            super(server, key, config, style);
        }
        @Override public boolean canSpreadFireAround(BlockPos pos) { return false; }
        @Override public void explode(net.minecraft.world.entity.Entity source,
                net.minecraft.world.damagesource.DamageSource damageSource,
                net.minecraft.world.level.ExplosionDamageCalculator calculator,
                double x, double y, double z, float radius, boolean fire, Level.ExplosionInteraction interaction,
                net.minecraft.core.particles.ParticleOptions smallParticle, net.minecraft.core.particles.ParticleOptions largeParticle,
                net.minecraft.util.random.WeightedList<net.minecraft.core.particles.ExplosionParticleInfo> blockParticles,
                net.minecraft.core.Holder<net.minecraft.sounds.SoundEvent> sound) {
            // Hub explosions cannot damage blocks, create fire, or knock players into the void.
        }
    }

    public static boolean enabled() { return Boolean.parseBoolean(System.getProperty("destiny.tower.enabled", "true")); }

    public static void init() {
        if (initialized) return;
        initialized = true;
        Registry.register(BuiltInRegistries.CHUNK_GENERATOR,
                Identifier.fromNamespaceAndPath("destiny", "tower_voxels"), TowerChunkGenerator.CODEC);
        ServerLifecycleEvents.SERVER_STARTED.register(server -> {
            if (enabled()) open(server);
            else DestinyGuardians.LOGGER.info("타워 스폰 월드 비활성화: destiny.tower.enabled=false");
        });
        // Fantasy PERSISTENT levels use the normal server save/close path. Never delete or enqueue an unload here.
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            if (state != null && state.server() == server) {
                state.details().close();
                state.materials().close();
                state.baked().close();
            }
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> {
            if (state != null && state.server() == server) { state = null; RETRY_AFTER.clear(); PENDING_JOINS.clear(); }
        });
        CommandRegistrationCallback.EVENT.register((dispatcher, access, environment) ->
                dispatcher.register(Commands.literal("tower").executes(context -> {
                    var source = context.getSource();
                    if (!(source.getEntity() instanceof ServerPlayer player)) {
                        source.sendFailure(Component.literal("플레이어만 /tower 명령어를 사용할 수 있습니다."));
                        return 0;
                    }
                    if (!enabled() || level(source.getServer()).isEmpty()) {
                        source.sendFailure(Component.literal("현재 타워 스폰 월드가 비활성화되어 있습니다."));
                        return 0;
                    }
                    if (!teleport(player)) {
                        source.sendFailure(Component.literal("안전한 타워 도착 지점을 확인하지 못했습니다. 관리자에게 문의해 주세요."));
                        return 0;
                    }
                    source.sendSuccess(() -> Component.literal("타워로 이동했습니다."), false);
                    return 1;
                })));
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> onJoin(handler.getPlayer()));
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            RETRY_AFTER.remove(handler.getPlayer().getUUID());
            PENDING_JOINS.remove(handler.getPlayer().getUUID(), handler.getPlayer());
        });
        ServerPlayerEvents.AFTER_RESPAWN.register((oldPlayer, newPlayer, alive) -> {
            if (!alive && enabled()) teleport(newPlayer);
        });
        // Rescue before player physics/damage. Returning is allowed for creative administrators as well.
        ServerTickEvents.START_SERVER_TICK.register(TowerSpawnWorld::tick);
        PlayerBlockBreakEvents.BEFORE.register((level, player, pos, block, entity) -> mayModify(level, player));
        AttackBlockCallback.EVENT.register((player, level, hand, pos, direction) ->
                mayModify(level, player) ? InteractionResult.PASS : InteractionResult.FAIL);
        AttackEntityCallback.EVENT.register((player, level, hand, target, hit) ->
                mayAttack(level, target) ? InteractionResult.PASS : InteractionResult.FAIL);
        UseBlockCallback.EVENT.register((player, level, hand, hit) ->
                mayModify(level, player) ? InteractionResult.PASS : InteractionResult.FAIL);
        UseItemCallback.EVENT.register((player, level, hand) -> {
            var item = player.getItemInHand(hand).getItem();
            return !mayModify(level, player) && (item instanceof BucketItem || item instanceof SolidBucketItem)
                    ? InteractionResult.FAIL : InteractionResult.PASS;
        });
        ServerEntityEvents.ALLOW_LOAD.register((entity, level, reason, loadedFromDisk) ->
                !isTower(level) || !(entity instanceof Mob));
        ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) ->
                !(entity instanceof ServerPlayer) || !isTower(entity.level()));
    }

    /** Called once per server lifecycle, and explicitly by isolated tower GameTests. */
    public static ServerLevel open(MinecraftServer server) {
        if (!enabled()) throw new IllegalStateException("타워 스폰 월드가 비활성화되어 있습니다.");
        if (!server.isSameThread()) throw new IllegalStateException("Tower must open on the server thread");
        if (state != null && state.server() == server) return state.handle().asLevel();
        ServerLevel existing = server.getLevel(KEY);
        if (existing != null && (!(existing instanceof TowerLevel)
                || !(existing.getChunkSource().getGenerator() instanceof TowerChunkGenerator)))
            throw new IllegalStateException("destiny:tower ID가 다른 월드에서 사용 중입니다. 기존 월드를 변경하지 않습니다.");
        TowerVoxelMap map = existing == null ? TowerChunkGenerator.bundledMap()
                : ((TowerChunkGenerator) existing.getChunkSource().getGenerator()).map();
        var config = new RuntimeLevelConfig()
                .setLevelConstructor(TowerLevel::new)
                .setDimensionType(BuiltinDimensionTypes.OVERWORLD)
                .setGenerator(new TowerChunkGenerator(server.registryAccess().getOrThrow(Biomes.THE_VOID), map))
                .setDifficulty(Difficulty.PEACEFUL)
                .setMirrorOverworldGameRules(false).setMirrorOverworldClocks(false).setMirrorOverworldDifficulty(false)
                .setShouldTickTime(false).setClockTime(WorldClocks.OVERWORLD, 6000, true)
                .setGameRule(GameRules.ADVANCE_WEATHER, false)
                .setGameRule(GameRules.SPAWN_MOBS, false).setGameRule(GameRules.SPAWN_MONSTERS, false)
                .setGameRule(GameRules.SPAWN_PATROLS, false).setGameRule(GameRules.SPAWN_PHANTOMS, false)
                .setGameRule(GameRules.SPAWN_WANDERING_TRADERS, false).setGameRule(GameRules.SPAWN_WARDENS, false)
                .setGameRule(GameRules.SPAWNER_BLOCKS_WORK, false).setGameRule(GameRules.RAIDS, false)
                .setGameRule(GameRules.MOB_GRIEFING, false).setGameRule(GameRules.TNT_EXPLODES, false)
                .setGameRule(GameRules.PROJECTILES_CAN_BREAK_BLOCKS, false)
                .setGameRule(GameRules.FIRE_SPREAD_RADIUS_AROUND_PLAYER, 0).setGameRule(GameRules.RANDOM_TICK_SPEED, 0)
                .setGameRule(GameRules.BLOCK_DROPS, false).setGameRule(GameRules.PVP, false)
                .setGameRule(GameRules.FALL_DAMAGE, false).setGameRule(GameRules.KEEP_INVENTORY, true);
        var handle = Fantasy.get(server).getOrOpenPersistentLevel(ID, config);
        ServerLevel level = handle.asLevel();
        var bounds = map.manifest().bounds();
        level.getWorldBorder().setCenter((bounds.minX() + bounds.maxX() + 1) / 2.0, (bounds.minZ() + bounds.maxZ() + 1) / 2.0);
        level.getWorldBorder().setSize(map.manifest().worldBorder());
        state = new State(server, handle, map, TowerDetailPass.start(level, map), TowerMaterialPass.start(level, map),
                TowerBakedMaterialPass.start(level, map));
        // Arrival remains source/persisted geometry. Details run later in bounded ticks and never repair edits.
        if (safeSpawn(level, map).isEmpty()) throw new IllegalStateException("타워 스폰 주변에 안전한 바닥과 머리 공간이 없습니다.");
        handle.setTickWhenEmpty(false);
        DestinyGuardians.LOGGER.info("타워 영구 월드 준비 완료: {} ({} blocks)", ID, map.blockCount());
        return level;
    }

    public static Optional<ServerLevel> level(MinecraftServer server) {
        return enabled() && state != null && state.server() == server ? Optional.of(state.handle().asLevel()) : Optional.empty();
    }
    public static boolean isTower(Level level) { return state != null && level == state.handle().asLevel(); }
    /** Hub combat is disabled for players, including creative administrators. */
    public static boolean mayAttack(Level level, net.minecraft.world.entity.Entity target) {
        return !isTower(level) || !(target instanceof Player);
    }
    public static boolean mayModify(Level level, Player player) {
        return !isTower(level) || player.isCreative() && player.permissions().hasPermission(Permissions.COMMANDS_ADMIN);
    }

    /** Existing players keep their login location; new player stats identify a first join. */
    public static void onJoin(ServerPlayer player) {
        if (!enabled() || state == null || state.server() != player.level().getServer()) return;
        // Fabric 26.3 JOIN fires inside placeNewPlayer, BEFORE level.addNewPlayer.
        // Changing levels there registers the player in two levels with one lastSectionPos.
        PENDING_JOINS.put(player.getUUID(), player);
    }

    public static void tick(MinecraftServer server) {
        if (!enabled() || state == null || state.server() != server) return;
        state.details().tick();
        // Preserve source-floor support checks: every prop/branch finishes before recoloring.
        if (state.details().isFinished()) state.materials().tick();
        // W245 expects the pinned W243 result; failed/unfinished W243 never unlocks it.
        if (state.materials().isFinished()) state.baked().tick();
        for (var player : java.util.List.copyOf(PENDING_JOINS.values())) {
            PENDING_JOINS.remove(player.getUUID(), player);
            if (player.level().getServer() == server && !player.hasDisconnected() && !player.isRemoved()
                    && server.getPlayerList().getPlayer(player.getUUID()) == player
                    && player.level().getEntity(player.getId()) == player
                    && (player.getStats().getValue(Stats.CUSTOM.get(Stats.PLAY_TIME)) == 0 || isTower(player.level()))) {
                teleport(player);
            }
        }
        int tick = server.getTickCount();
        for (var player : java.util.List.copyOf(state.handle().asLevel().players())) {
            if (player.isAlive() && (player.getY() <= state.map().manifest().returnBelowY()
                    || !player.level().getWorldBorder().isWithinBounds(player.position()))
                    && tick >= RETRY_AFTER.getOrDefault(player.getUUID(), 0)) {
                if (!teleport(player)) {
                    RETRY_AFTER.put(player.getUUID(), tick + 100);
                    player.sendSystemMessage(Component.literal("안전한 타워 귀환 지점을 찾지 못했습니다. /tower 또는 관리자에게 문의해 주세요."));
                }
            }
        }
    }

    public static boolean teleport(ServerPlayer player) {
        if (!enabled() || state == null || state.server() != player.level().getServer()
                || !player.isAlive() || player.isRemoved() || player.hasDisconnected()) return false;
        ServerLevel level = state.handle().asLevel();
        Optional<Vec3> safe = safeSpawn(level, state.map());
        if (safe.isEmpty()) return false;
        AbilityService.cleanup(player);
        WeaponRuntime.cleanup(player);
        CameraViews.stop(player);
        player.setCamera(player);
        player.stopRiding();
        player.stopUsingItem();
        player.closeContainer();
        player.resetFallDistance();
        player.setDeltaMovement(Vec3.ZERO);
        var spawn = state.map().manifest().spawn();
        Vec3 pos = safe.get();
        boolean moved = player.teleportTo(level, pos.x(), pos.y(), pos.z(), Set.of(), spawn.yaw(), spawn.pitch(), true);
        if (moved) { player.resetFallDistance(); player.setDeltaMovement(Vec3.ZERO); RETRY_AFTER.remove(player.getUUID()); }
        return moved;
    }

    public static Optional<Vec3> safeSpawn(ServerLevel level, TowerVoxelMap map) {
        var s = map.manifest().spawn();
        Vec3 exact = new Vec3(s.x(), s.y(), s.z());
        if (isSafeArrival(level, exact)) return Optional.of(exact);
        int x = (int) Math.floor(s.x()), y = (int) Math.floor(s.y()), z = (int) Math.floor(s.z());
        for (int radius = 0; radius <= 8; radius++) {
            for (int dy = 0; dy <= 8; dy++) {
                for (int sign : dy == 0 ? new int[]{1} : new int[]{1, -1}) {
                    for (int dx = -radius; dx <= radius; dx++) for (int dz = -radius; dz <= radius; dz++) {
                        if (Math.max(Math.abs(dx), Math.abs(dz)) != radius) continue;
                        Vec3 candidate = new Vec3(x + dx + 0.5, y + dy * sign, z + dz + 0.5);
                        if (map.manifest().bounds().contains(x + dx, y + dy * sign, z + dz)
                                && isSafeArrival(level, candidate)) return Optional.of(candidate);
                    }
                }
            }
        }
        return Optional.empty();
    }

    public static boolean isSafeArrival(ServerLevel level, Vec3 pos) {
        if (!Double.isFinite(pos.x()) || !Double.isFinite(pos.y()) || !Double.isFinite(pos.z())
                || Math.abs(pos.y() - Math.rint(pos.y())) > 0.001) return false;
        BlockPos feet = BlockPos.containing(pos);
        if (feet.getY() <= level.getMinY() || feet.getY() + 1 > level.getMaxY()) return false;
        AABB body = new AABB(pos.x() - 0.3, pos.y(), pos.z() - 0.3, pos.x() + 0.3, pos.y() + 1.8, pos.z() + 0.3);
        if (!level.getWorldBorder().isWithinBounds(body)) return false;
        // At most four chunks for the player's footprint, loaded before examining support and collision.
        for (int cx = (int) Math.floor(body.minX) >> 4; cx <= (int) Math.floor(body.maxX) >> 4; cx++)
            for (int cz = (int) Math.floor(body.minZ) >> 4; cz <= (int) Math.floor(body.maxZ) >> 4; cz++) level.getChunk(cx, cz);
        BlockPos floor = feet.below();
        var support = level.getBlockState(floor);
        return support.isFaceSturdy(level, floor, Direction.UP) && support.getFluidState().isEmpty()
                && !support.is(Blocks.MAGMA_BLOCK) && !support.is(Blocks.CACTUS)
                && !support.is(Blocks.CAMPFIRE) && !support.is(Blocks.SOUL_CAMPFIRE)
                && level.getBlockState(feet).isAir() && level.getBlockState(feet.above()).isAir()
                && level.noCollision(body);
    }
}
