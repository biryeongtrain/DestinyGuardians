package kim.biryeong.destiny.campaign;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/**
 * Master-owned integration contract for the Guardian Rises campaign (W300).
 * Lanes implement these interfaces and register once at init; the mission director only
 * depends on this file. Changing a signature requires a master contract revision.
 * All calls happen on the server thread.
 */
public final class RisingServices {
    private RisingServices() {}

    /** BetterModel model names (config/bettermodel/models/NAME.bbmodel) and their required clips. */
    public static final class Models {
        public static final String GHOST = "rg_ghost";
        public static final String DREG = "rg_dreg";
        public static final String VANDAL = "rg_vandal";
        public static final String CAPTAIN = "rg_captain";
        public static final String SHANK = "rg_shank";
        public static final String WALKER = "rg_walker";
        public static final String SKIFF = "rg_skiff";
        public static final String SHIP = "rg_ship";
        /** Every Fallen infantry model provides these clips. */
        public static final List<String> INFANTRY_CLIPS = List.of(
                "idle", "walk", "run", "shoot", "melee", "hit", "stagger", "death", "spawn");
        public static final List<String> SHANK_CLIPS = List.of("idle", "fly", "shoot", "hit", "death");
        public static final List<String> WALKER_CLIPS = List.of(
                "idle", "walk", "fire", "leg_break", "stagger", "weakpoint_open", "recover", "death");
        public static final List<String> GHOST_CLIPS = List.of(
                "idle", "scan", "speak", "shell_open", "shell_close", "transmat", "look");
        public static final List<String> SKIFF_CLIPS = List.of("idle", "arrive", "drop", "depart");
        public static final List<String> SHIP_CLIPS = List.of("idle", "power_up", "takeoff");
        private Models() {}
    }

    /** Ordered mission zones. Marker ids below are stable across lanes. */
    public enum Zone { GATEWAY, BREACH, DIVIDE, DOCK13 }

    /**
     * Marker id grammar (lower-case): spawn.player, ghost.scan, checkpoint.STAGE,
     * trigger.NAME (tags radius/height), enemy.ENCOUNTER.N (tag kind=dreg|vandal|captain|shank|walker),
     * prop.NAME (rifle, shotgun_cache, ship), exit.ZONE, light.NAME.
     */
    public record Marker(String id, Vec3 pos, float yaw, Map<String, String> tags) {
        public Marker {
            Objects.requireNonNull(id); Objects.requireNonNull(pos); tags = Map.copyOf(tags);
        }
    }

    public interface Markers {
        List<Marker> all();
        default Optional<Marker> get(String id) {
            return all().stream().filter(m -> m.id().equals(id)).findFirst();
        }
        default List<Marker> prefix(String prefix) {
            return all().stream().filter(m -> m.id().startsWith(prefix)).toList();
        }
    }

    /** Budgeted placement. Step until done; never place in view of a player before READY. */
    public interface ZoneBuild {
        boolean step(long nanoBudget);
        double progress();
        void cancel();
    }

    public interface Zones {
        /** Markers are in world coordinates of a zone placed at origin. */
        ZoneBuild begin(ServerLevel level, Zone zone, BlockPos origin);
        Markers markers(Zone zone, BlockPos origin);
    }

    public enum FallenKind { DREG, VANDAL, CAPTAIN, SHANK, WALKER }

    public interface FallenListener {
        void defeated(LivingEntity entity);
        /** Removed without a kill (void, unload, discard). Director respawns or resets. */
        void lost(LivingEntity entity);
    }

    /** Mission tuning separate from PvP. 1.0 is baseline. */
    public record Difficulty(double health, double damage, double accuracy) {
        public static final Difficulty FIRST_MISSION = new Difficulty(1.0, 0.6, 0.55);
    }

    public interface Fallen {
        LivingEntity spawn(ServerLevel level, FallenKind kind, Vec3 pos, float yaw, Difficulty tuning,
                           FallenListener listener);
        /** Activate (true) or freeze AI for scripted/hidden enemies. */
        void setActive(LivingEntity entity, boolean active);
    }

    /** Presentation handle owned by one player. close() is idempotent and restores camera/post state. */
    public interface Handle extends AutoCloseable {
        boolean finished();
        @Override void close();
    }

    /** Pickup prop handle. collect() is close() with the pickup flash/sound; both are idempotent. */
    public interface PickupHandle extends Handle {
        void collect();
    }

    public interface Presentation {
        /** Darkness, Ghost scans the Guardian, light returns. done runs once, also on early close. */
        Handle openingScan(ServerPlayer player, Vec3 guardianEye, Runnable done);
        /** W301: as above; {@code vista} (nullable) is where the Ghost points out "Fallen territory" (the wall). */
        default Handle openingScan(ServerPlayer player, Vec3 guardianEye, Vec3 vista, Runnable done) {
            return openingScan(player, guardianEye, done);
        }
        /** Ghost scan of a point of interest (door, ship). */
        Handle ghostScan(ServerPlayer player, Vec3 target, int ticks, Runnable done);
        /**
         * Ship power-up, takeoff and fade. done fires when the screen is black. If a {@link #shipProp} is open
         * for this player, departure takes over that ship (never two ships). The black then survives the
         * Tower teleport and the presentation plays its own arrival fade-in in the destination world.
         */
        Handle departure(ServerPlayer player, Vec3 shipPos, float shipYaw, Runnable done);
        /**
         * Persistent owner-only parked ship (Dock 13 search and defense). Lit, idle, engines dark.
         * close() removes it unless {@link #departure} already took it over. Never null when the service exists.
         */
        Handle shipProp(ServerPlayer player, Vec3 shipPos, float shipYaw);
        /**
         * Owner-only weapon pickup marker: kind "rifle" (glowing rifle lying on the floor) or "shotgun_cache"
         * (Fallen crate with the shotgun on top), light column and a near outline. close() removes it
         * silently; {@link PickupHandle#collect()} removes it with the pickup flash and sound.
         */
        PickupHandle pickup(ServerPlayer player, Vec3 pos, float yaw, String kind);
        /** Plays a Korean voice line with subtitle; returns duration ticks, 0 if unknown. */
        int voice(ServerPlayer player, String lineId);
        void stopAll(ServerPlayer player);
    }

    /** Line ids are the lower-case WEM tag, e.g. 80b75f50. Sound event: destiny:guardian_rises.voice.ID */
    public static final class Voice {
        public static String soundEvent(String lineId) { return "guardian_rises.voice." + lineId; }
        private Voice() {}
    }

    private static Zones zones;
    private static Fallen fallen;
    private static Presentation presentation;

    public static void register(Zones value) { zones = once(zones, value); }
    public static void register(Fallen value) { fallen = once(fallen, value); }
    public static void register(Presentation value) { presentation = once(presentation, value); }
    public static Optional<Zones> zones() { return Optional.ofNullable(zones); }
    public static Optional<Fallen> fallen() { return Optional.ofNullable(fallen); }
    public static Optional<Presentation> presentation() { return Optional.ofNullable(presentation); }

    private static <T> T once(T current, T value) {
        Objects.requireNonNull(value);
        if (current != null && current != value) throw new IllegalStateException("Service already registered");
        return value;
    }
}
