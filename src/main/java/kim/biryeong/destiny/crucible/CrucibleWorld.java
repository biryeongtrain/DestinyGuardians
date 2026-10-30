package kim.biryeong.destiny.crucible;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ChunkAttachment;
import eu.pb4.polymer.virtualentity.api.elements.TextDisplayElement;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Difficulty;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.clock.WorldClocks;
import net.minecraft.world.entity.Display;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.dimension.BuiltinDimensionTypes;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.phys.Vec3;
import net.minecraft.network.chat.Component;
import xyz.nucleoid.fantasy.*;
import java.util.*;

/** A disposable arena built from bundled baked blocks, never edits the Tower or overworld. */
public final class CrucibleWorld {
    public static final Identifier ID = DestinyGuardians.id("crucible_control");
    private static Arena current;
    private static boolean initialized;
    private CrucibleWorld() { }
    public record Position(Vec3 position, float yaw) { }
    public record Zone(String id, Vec3 position, double radius) { }

    public static final class Arena {
        private final RuntimeLevelHandle handle;
        private final CrucibleMap map;
        private final List<Zone> zones;
        private final List<ElementHolder> markers = new ArrayList<>();
        private Arena(RuntimeLevelHandle handle, CrucibleMap map) {
            this.handle = handle; this.map = map;
            zones = map.manifest().zones().stream().map(z -> new Zone(z.key(), vec(z.center()), z.radius())).toList();
        }
        public ServerLevel level() { return handle.asLevel(); }
        public String name() { return map.manifest().name(); }
        public int returnBelowY() { return map.manifest().returnBelowY(); }
        public List<Zone> zones() { return zones; }
        public CrucibleMap.Manifest manifest() { return map.manifest(); }
        public Position spawn(ControlMatch.Team team, int ordinal) {
            List<CrucibleMap.Spawn> candidates = team == ControlMatch.Team.ALPHA ? manifest().alphaSpawns() : manifest().bravoSpawns();
            Position result = null; double bestDistance = -1;
            for (int i=0;i<candidates.size();i++) {
                var candidate = candidates.get(Math.floorMod(ordinal+i,candidates.size()));
                Vec3 point = vec(candidate);
                if (!TowerSpawnWorld.isSafeArrival(level(), point)) continue;
                double distance = level().players().stream().filter(p -> p.isAlive() && CrucibleRuntime.team(p) != null && CrucibleRuntime.team(p) != team)
                        .mapToDouble(p -> p.position().distanceToSqr(point)).min().orElse(1_000_000);
                if (distance > bestDistance) { bestDistance=distance;result=new Position(point,candidate.yaw()); }
            }
            if (result == null) throw new IllegalStateException("안전한 시련의 장 스폰이 없습니다.");
            return result;
        }
        private void markZones() {
            for (Zone zone : zones) {
                ElementHolder holder = new ElementHolder();
                var text = new TextDisplayElement(Component.literal("◇ " + zone.id()).withColor(0xF1EDE1));
                text.setBillboardMode(Display.BillboardConstraints.CENTER);
                text.setBackground(0x60000000);
                text.setScale(new org.joml.Vector3f(1.3f));
                holder.addElement(text);
                ChunkAttachment.ofTicking(holder, level(), zone.position().add(0,3,0));
                markers.add(holder);
            }
        }
        /** Particle wireframe per zone: ground ring, capture-progress arc, cylinder lines, tall beam. Colours are per viewer. */
        public void updateZones(ControlMatch.Snapshot snapshot) {
            if (snapshot.phase() != ControlMatch.Phase.PLAYING || snapshot.tick() % 2 != 0) return;
            long t = snapshot.tick();
            for (var viewer : level().players()) {
                var own = snapshot.members().get(viewer.getUUID()); if (own == null) continue;
                for (Zone zone : zones) {
                    double dist2 = viewer.position().distanceToSqr(zone.position());
                    if (dist2 > 110 * 110) continue;
                    var zs = snapshot.zones().get(zone.id());
                    var owner = zs.owner();
                    int color = owner == null ? 0xE5E3DB : owner == own ? 0x4FD6FF : 0xFF4545;
                    boolean capturing = zs.capturingTeam() != null && zs.progress() > .01;
                    int capColor = !capturing ? color : zs.contested() ? 0xFFFFFF : zs.capturingTeam() == own ? 0x4FD6FF : 0xFF4545;
                    Vec3 c = zone.position(); double r = zone.radius(), h = manifest().zones().stream()
                            .filter(z -> z.key().equals(zone.id())).findFirst().map(CrucibleMap.Zone::height).orElse(4.0);
                    // tall beam: visible across the whole arena
                    double top = 16 + 2 * Math.sin(t / 10.0);
                    for (double y = 0; y < top; y += .7)
                        dot(viewer, color, y > top - 3 ? 1.1f : 1.6f, c.x, c.y + y, c.z);
                    if (dist2 > 64 * 64) continue;
                    int n = 64;
                    for (int i = 0; i < n; i++) {
                        double a = i * 2 * Math.PI / n;
                        dot(viewer, color, 1.2f, c.x + Math.cos(a) * r, c.y + .12, c.z + Math.sin(a) * r);
                    }
                    // top ring + vertical lines make a readable cylinder
                    for (int i = 0; i < 32; i++) {
                        double a = i * Math.PI / 16 + t / 40.0;
                        dot(viewer, color, 1.0f, c.x + Math.cos(a) * r, c.y + h, c.z + Math.sin(a) * r);
                    }
                    for (int k = 0; k < 8; k++) {
                        double a = k * Math.PI / 4;
                        for (double y = .5; y < h; y += .6)
                            dot(viewer, color, .9f, c.x + Math.cos(a) * r, c.y + y, c.z + Math.sin(a) * r);
                    }
                    if (capturing) { // progress arc, thicker, inside the ring
                        int steps = (int) (zs.progress() * n);
                        for (int i = 0; i < steps; i++) {
                            double a = -Math.PI / 2 + i * 2 * Math.PI / n;
                            for (double rr = r - .8; rr <= r - .3; rr += .25)
                                dot(viewer, capColor, 1.3f, c.x + Math.cos(a) * rr, c.y + .2, c.z + Math.sin(a) * rr);
                        }
                    }
                }
            }
        }
        private void dot(net.minecraft.server.level.ServerPlayer viewer, int color, float size, double x, double y, double z) {
            level().sendParticles(viewer, Fx.dust(color, size), true, true, x, y, z, 1, 0, 0, 0, 0);
        }
        private void closeMarkers() { markers.forEach(ElementHolder::destroy); markers.clear(); }
    }

    private static final class ArenaLevel extends RuntimeLevel {
        ArenaLevel(MinecraftServer server, ResourceKey<Level> key, RuntimeLevelConfig config, Style style) { super(server,key,config,style); }
        @Override public boolean canSpreadFireAround(net.minecraft.core.BlockPos pos) { return false; }
        @Override public void explode(net.minecraft.world.entity.Entity source,
                net.minecraft.world.damagesource.DamageSource damageSource,
                net.minecraft.world.level.ExplosionDamageCalculator calculator,
                double x,double y,double z,float radius,boolean fire,Level.ExplosionInteraction interaction,
                net.minecraft.core.particles.ParticleOptions small,net.minecraft.core.particles.ParticleOptions large,
                net.minecraft.util.random.WeightedList<net.minecraft.core.particles.ExplosionParticleInfo> blockParticles,
                net.minecraft.core.Holder<net.minecraft.sounds.SoundEvent> sound) {
            // Ability/weapon blasts use Combat; no vanilla explosion may erase the finite arena.
        }
    }
    public static void init() {
        if (initialized) return; initialized=true;
        Registry.register(BuiltInRegistries.CHUNK_GENERATOR,DestinyGuardians.id("crucible_voxels"),CrucibleChunkGenerator.CODEC);
        PlayerBlockBreakEvents.BEFORE.register((level,p,pos,state,entity) -> !isArena(level));
        UseBlockCallback.EVENT.register((p,level,hand,hit) -> isArena(level) ? InteractionResult.FAIL : InteractionResult.PASS);
        ServerLifecycleEvents.SERVER_STOPPING.register(s -> {
            if(current!=null && current.level().getServer()==s) {
                current.handle.setTickWhenEmpty(true);
                current.closeMarkers();
            }
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(s -> { if(current!=null && current.level().getServer()==s)current=null; });
    }
    public static boolean isArena(Level level) { return level.dimension().identifier().equals(ID); }
    public static Arena open(MinecraftServer server) {
        if (!server.isSameThread()) throw new IllegalStateException("Arena opens on server thread only");
        if (current != null && current.level().getServer()==server) return current;
        CrucibleMap map = CrucibleChunkGenerator.bundledMap();
        var config = new RuntimeLevelConfig().setLevelConstructor(ArenaLevel::new)
                .setDimensionType(BuiltinDimensionTypes.OVERWORLD)
                .setGenerator(new CrucibleChunkGenerator(server.registryAccess().getOrThrow(Biomes.THE_VOID),map))
                .setDifficulty(Difficulty.NORMAL).setMirrorOverworldGameRules(false).setMirrorOverworldClocks(false).setMirrorOverworldDifficulty(false)
                .setShouldTickTime(false).setClockTime(WorldClocks.OVERWORLD,6000,true)
                .setGameRule(GameRules.ADVANCE_WEATHER,false).setGameRule(GameRules.SPAWN_MOBS,false)
                .setGameRule(GameRules.SPAWN_MONSTERS,false).setGameRule(GameRules.SPAWN_PATROLS,false)
                .setGameRule(GameRules.SPAWN_PHANTOMS,false).setGameRule(GameRules.MOB_GRIEFING,false)
                .setGameRule(GameRules.TNT_EXPLODES,false).setGameRule(GameRules.PROJECTILES_CAN_BREAK_BLOCKS,false)
                .setGameRule(GameRules.FIRE_SPREAD_RADIUS_AROUND_PLAYER,0).setGameRule(GameRules.RANDOM_TICK_SPEED,0)
                .setGameRule(GameRules.BLOCK_DROPS,false).setGameRule(GameRules.PVP,true)
                .setGameRule(GameRules.KEEP_INVENTORY,true).setGameRule(GameRules.IMMEDIATE_RESPAWN,false)
                .setGameRule(GameRules.NATURAL_HEALTH_REGENERATION,false);
        var handle=Fantasy.get(server).openTemporaryLevel(ID,config);
        var arena=new Arena(handle,map);
        arena.level().getWorldBorder().setCenter(0,0);arena.level().getWorldBorder().setSize(map.manifest().worldBorder());
        try { arena.spawn(ControlMatch.Team.ALPHA,0);arena.spawn(ControlMatch.Team.BRAVO,0);arena.markZones(); }
        catch(RuntimeException error) {arena.closeMarkers();handle.delete();throw error;}
        handle.setTickWhenEmpty(false);current=arena;
        DestinyGuardians.LOGGER.info("시련의 장 준비: {} / {} blocks",map.manifest().name(),map.blockCount());
        return arena;
    }
    public static Vec3 vec(CrucibleMap.Spawn p) { return new Vec3(p.x(),p.y(),p.z()); }
}
