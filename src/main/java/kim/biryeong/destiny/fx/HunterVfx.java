package kim.biryeong.destiny.fx;

import kim.biryeong.destiny.DestinyGuardians;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.animation.AnimationIterator;
import kr.toxicity.model.api.animation.AnimationModifier;
import kr.toxicity.model.api.mod.platform.ModLocation;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.DummyTracker;
import kr.toxicity.model.api.tracker.ModelScaler;
import kr.toxicity.model.api.tracker.TrackerModifier;
import kr.toxicity.model.api.tracker.TrackerUpdateAction;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/** Bounded, cosmetic location trackers. All entry points are called on the server thread. */
public final class HunterVfx {
    private static final int MAX_PER_OWNER = 4;
    private static final int MAX_TOTAL = 24;
    private static final int MAX_DURATION = 200;
    private static final int VIEWER_INTERVAL = 5;
    private static final double VIEW_DISTANCE_SQUARED = 48 * 48;
    // Insertion order is also eviction order. BetterModel callbacks never mutate this list.
    private static final List<Effect> ACTIVE = new ArrayList<>();
    private static final Set<String> MISSING_MODELS = new HashSet<>();

    public enum Kind {
        ARC_FLASH("destiny_vfx_arc_h13", 16),
        ARC_STRIKE("destiny_vfx_arc_h13", 16),
        SOLAR_BURST("destiny_vfx_solar_h13", 22),
        SOLAR_KNIFE("destiny_vfx_solar_h13", 22),
        VOID_VORTEX("destiny_vfx_vortex_h13", MAX_DURATION),
        VOID_SMOKE("destiny_vfx_smoke_h13", MAX_DURATION);

        private final String modelName;
        private final int maxDuration;

        Kind(String modelName, int maxDuration) {
            this.modelName = modelName;
            this.maxDuration = maxDuration;
        }

        public String modelName() {
            return modelName;
        }

        private boolean looping() {
            return this == VOID_VORTEX || this == VOID_SMOKE;
        }

        private String animation() {
            return looping() ? "loop" : "spawn";
        }
    }

    private static final class Effect {
        final ServerPlayer owner;
        final ServerLevel level;
        final Vec3 position;
        final Kind kind;
        final double radius;
        final int duration;
        final int startedAt;
        final Map<UUID, ModPlayer> viewers = new HashMap<>();
        DummyTracker tracker;
        int nextViewerRefresh = VIEWER_INTERVAL;

        Effect(ServerPlayer owner, ServerLevel level, Vec3 position, Kind kind, double radius, int duration) {
            this.owner = owner;
            this.level = level;
            this.position = position;
            this.kind = kind;
            this.radius = radius;
            this.duration = duration;
            this.startedAt = level.getServer().getTickCount();
        }

        int age() {
            return level.getServer().getTickCount() - startedAt;
        }
    }

    private HunterVfx() {
    }

    public static String modelName(Kind kind) {
        return kind.modelName();
    }

    /** Starts a visual only; an unavailable renderer or any backend failure leaves no active entry. */
    public static boolean play(ServerPlayer owner, ServerLevel level, Vec3 pos, Kind kind,
                               double radius, int durationTicks) {
        float scale = (float) radius;
        if (owner == null || level == null || pos == null || kind == null || durationTicks <= 0
                || !Double.isFinite(pos.x) || !Double.isFinite(pos.y) || !Double.isFinite(pos.z)
                || !Double.isFinite(radius) || !Float.isFinite(scale) || scale <= 0
                || (kind.looping() && (float) (radius * 0.01) <= 0)
                || !validOwner(owner, level)) {
            return false;
        }

        Effect effect = new Effect(owner, level, pos, kind, radius,
                Math.min(durationTicks, Math.min(MAX_DURATION, kind.maxDuration)));
        boolean retained = false;
        try {
            var renderer = BetterModel.model(kind.modelName()).orElse(null);
            if (renderer == null) {
                if (MISSING_MODELS.add(kind.modelName())) {
                    DestinyGuardians.LOGGER.warn("Hunter VFX model is unavailable: {}", kind.modelName());
                }
                return false;
            }
            if (renderer.animation(kind.animation()).isEmpty()) {
                return false;
            }
            // Make room before allocating another backend tracker, including during construction.
            evictFor(owner);
            // Capture the tracker before the factory's create event, so a failing event can be cleaned up.
            effect.tracker = renderer.create(ModLocation.of(level, pos), TrackerModifier.DEFAULT,
                    tracker -> effect.tracker = tracker);
            updateScale(effect, 0);
            effect.tracker.update(TrackerUpdateAction.brightness(15, 15));
            var type = kind.looping() ? AnimationIterator.Type.LOOP : AnimationIterator.Type.PLAY_ONCE;
            if (!effect.tracker.animate(kind.animation(), new AnimationModifier(0, 0, type))) {
                return false;
            }
            refreshViewers(effect);
            if (effect.tracker.isClosed()) {
                return false;
            }
            ACTIVE.add(effect);
            retained = true;
            return true;
        } catch (RuntimeException e) {
            DestinyGuardians.LOGGER.warn("Hunter VFX {} failed: {}", kind.modelName(), e.toString());
            return false;
        } finally {
            if (!retained) {
                closeTracker(effect);
            }
        }
    }

    /** TTL and owner guards run independently of ability Tasks and BetterModel's animation scheduler. */
    public static void tick(MinecraftServer server) {
        var iterator = ACTIVE.iterator();
        while (iterator.hasNext()) {
            Effect effect = iterator.next();
            if (effect.level.getServer() != server) {
                continue;
            }
            boolean remove = false;
            try {
                int age = effect.age();
                remove = age >= effect.duration || !validOwner(effect.owner, effect.level)
                        || effect.tracker.isClosed();
                if (!remove) {
                    if (effect.kind.looping()) {
                        updateScale(effect, age);
                    }
                    if (age >= effect.nextViewerRefresh) {
                        refreshViewers(effect);
                        effect.nextViewerRefresh = age + VIEWER_INTERVAL;
                    }
                }
            } catch (RuntimeException e) {
                DestinyGuardians.LOGGER.warn("Hunter VFX {} update failed: {}", effect.kind.modelName(), e.toString());
                remove = true;
            }
            if (remove) {
                iterator.remove();
                closeTracker(effect);
            }
        }
    }

    public static void cancelOwned(ServerPlayer owner) {
        if (owner == null) return;
        var iterator = ACTIVE.iterator();
        while (iterator.hasNext()) {
            Effect effect = iterator.next();
            if (effect.owner.getUUID().equals(owner.getUUID())) {
                iterator.remove();
                closeTracker(effect);
            }
        }
    }

    public static void clearAll() {
        List<Effect> effects = new ArrayList<>(ACTIVE);
        ACTIVE.clear();
        effects.forEach(HunterVfx::closeTracker);
    }

    public static int activeCount() {
        return ACTIVE.size();
    }

    public static int activeCount(ServerPlayer owner) {
        if (owner == null) return 0;
        return (int) ACTIVE.stream().filter(effect -> effect.owner.getUUID().equals(owner.getUUID())).count();
    }

    private static boolean validOwner(ServerPlayer owner, ServerLevel level) {
        // GameTest owners need not belong to PlayerList; only actual viewers must be connected there.
        return owner.level() == level && !owner.isRemoved() && !owner.isDeadOrDying() && !owner.hasDisconnected();
    }

    private static void updateScale(Effect effect, int age) {
        double factor = effect.kind.looping()
                ? Math.max(0.01, Math.min(1, Math.min((age + 1) / 4.0, (effect.duration - age) / 8.0)))
                : 1;
        // Authored radius is 16 Blockbench units = one block, so no unit conversion is needed.
        effect.tracker.scaler(ModelScaler.value((float) (effect.radius * factor)));
    }

    private static void refreshViewers(Effect effect) {
        Map<UUID, ServerPlayer> nearby = new HashMap<>();
        for (ServerPlayer player : effect.level.getServer().getPlayerList().getPlayers()) {
            if (player.connection != null && !player.hasDisconnected() && !player.isRemoved()
                    && player.level() == effect.level
                    && player.position().distanceToSqr(effect.position) <= VIEW_DISTANCE_SQUARED) {
                nearby.put(player.getUUID(), player);
            }
        }
        var iterator = effect.viewers.entrySet().iterator();
        while (iterator.hasNext()) {
            var entry = iterator.next();
            ServerPlayer player = nearby.get(entry.getKey());
            if (player == null || entry.getValue().source() != player.connection) {
                effect.tracker.remove(entry.getValue());
                iterator.remove();
            }
        }
        for (ServerPlayer player : nearby.values()) {
            ModPlayer viewer = effect.viewers.computeIfAbsent(player.getUUID(), id -> ModPlayer.of(player.connection));
            if (!effect.tracker.isSpawned(viewer)) {
                effect.tracker.spawn(viewer);
            }
        }
    }

    private static void evictFor(ServerPlayer owner) {
        if (activeCount(owner) >= MAX_PER_OWNER) {
            for (int i = 0; i < ACTIVE.size(); i++) {
                if (ACTIVE.get(i).owner.getUUID().equals(owner.getUUID())) {
                    closeTracker(ACTIVE.remove(i));
                    break;
                }
            }
        }
        while (ACTIVE.size() >= MAX_TOTAL) {
            closeTracker(ACTIVE.removeFirst());
        }
    }

    private static void closeTracker(Effect effect) {
        if (effect.tracker == null) return;
        // Remove individually first: one broken connection must not prevent the remaining viewers' cleanup.
        for (ModPlayer viewer : effect.viewers.values()) {
            try {
                effect.tracker.remove(viewer);
            } catch (RuntimeException e) {
                DestinyGuardians.LOGGER.warn("Hunter VFX {} viewer cleanup failed: {}", effect.kind.modelName(), e.toString());
            }
        }
        effect.viewers.clear();
        try {
            effect.tracker.close();
        } catch (RuntimeException e) {
            DestinyGuardians.LOGGER.warn("Hunter VFX {} close failed: {}", effect.kind.modelName(), e.toString());
        }
    }
}
