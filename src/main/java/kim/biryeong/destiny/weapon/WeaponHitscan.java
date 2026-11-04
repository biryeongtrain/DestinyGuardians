package kim.biryeong.destiny.weapon;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.*;

import java.util.*;
import java.util.function.Predicate;

/** Instant server-authoritative rays against bounded rendered-position estimates, never live entity rewinds. */
public final class WeaponHitscan {
    private static final int MAX_REWIND_TICKS = 5; // At most 250 ms, including native interpolation.
    private static final int MAX_TRACKED_PER_LEVEL = 2048;
    private static final Map<ServerLevel, Map<LivingEntity, History>> HISTORY = new IdentityHashMap<>();
    private static boolean initialized;
    private WeaponHitscan() { }

    public record Contact(HitResult hit, AABB body) { }

    private static final class History {
        final AABB[] boxes = new AABB[MAX_REWIND_TICKS + 2];
        final int[] ticks = new int[boxes.length];
        AABB bounds;
        int next, size;
        void clear() { Arrays.fill(boxes, null); bounds = null; size = next = 0; }
        void record(LivingEntity entity, int tick) {
            if (!entity.isAlive() || entity.isSpectator()) { clear(); return; }
            AABB box = entity.getBoundingBox();
            if (size > 0) {
                int last = (next + boxes.length - 1) % boxes.length;
                if (box.getCenter().distanceToSqr(boxes[last].getCenter()) > 9) clear();
                else if (ticks[last] == tick) { boxes[last] = box; rebuildBounds(); return; }
            }
            boxes[next] = box; ticks[next] = tick;
            next = (next + 1) % boxes.length; size = Math.min(boxes.length, size + 1);
            rebuildBounds();
        }
        void rebuildBounds() {
            double minX=Double.POSITIVE_INFINITY,minY=minX,minZ=minX;
            double maxX=Double.NEGATIVE_INFINITY,maxY=maxX,maxZ=maxX;
            for (AABB box : boxes) if (box != null) {
                minX=Math.min(minX,box.minX); minY=Math.min(minY,box.minY); minZ=Math.min(minZ,box.minZ);
                maxX=Math.max(maxX,box.maxX); maxY=Math.max(maxY,box.maxY); maxZ=Math.max(maxZ,box.maxZ);
            }
            if (bounds==null || bounds.minX!=minX || bounds.minY!=minY || bounds.minZ!=minZ
                    || bounds.maxX!=maxX || bounds.maxY!=maxY || bounds.maxZ!=maxZ)
                bounds=new AABB(minX,minY,minZ,maxX,maxY,maxZ);
        }
        AABB at(LivingEntity entity, int now, double wanted) {
            AABB current = entity.getBoundingBox();
            if (size == 0) return current;
            int last = (next + boxes.length - 1) % boxes.length;
            // Stale history or a teleport since the last sample never leaves a hittable ghost.
            if (now - ticks[last] > 2 || current.getCenter().distanceToSqr(boxes[last].getCenter()) > 9) return current;
            for (int n = 0; n < size; n++) {
                int index = (last + boxes.length - n) % boxes.length;
                if (ticks[index] <= wanted) {
                    if (n == 0 || ticks[index] == wanted) return boxes[index];
                    int newer = (index + 1) % boxes.length;
                    double alpha = (wanted - ticks[index]) / (ticks[newer] - ticks[index]);
                    AABB a = boxes[index], b = boxes[newer];
                    return new AABB(a.minX + (b.minX-a.minX)*alpha, a.minY + (b.minY-a.minY)*alpha,
                            a.minZ + (b.minZ-a.minZ)*alpha, a.maxX + (b.maxX-a.maxX)*alpha,
                            a.maxY + (b.maxY-a.maxY)*alpha, a.maxZ + (b.maxZ-a.maxZ)*alpha);
                }
            }
            // New spawn or reset: don't extrapolate a body into a time before it existed.
            return current;
        }
    }

    public static void init() {
        if (initialized) return;
        initialized = true;
        ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
            if (entity instanceof LivingEntity living) {
                var entities = HISTORY.computeIfAbsent(level, ignored -> new IdentityHashMap<>());
                if (entities.size() < MAX_TRACKED_PER_LEVEL) {
                    var history = new History(); history.record(living, level.getServer().getTickCount());
                    entities.put(living, history);
                }
            }
        });
        ServerEntityEvents.ENTITY_UNLOAD.register((entity, level) -> {
            var entities = HISTORY.get(level);
            if (entities != null) { entities.remove(entity); if (entities.isEmpty()) HISTORY.remove(level); }
        });
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            for (var world : HISTORY.entrySet()) if (world.getKey().getServer() == server)
                for (var entity : world.getValue().entrySet())
                    if (entity.getKey().level() == world.getKey()) entity.getValue().record(entity.getKey(), server.getTickCount());
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> HISTORY.keySet().removeIf(level -> level.getServer() == server));
        net.fabricmc.fabric.api.event.lifecycle.v1.ServerLevelEvents.UNLOAD.register((server, level) -> HISTORY.remove(level));
    }

    /** Only HITSCAN calls this. Explosives, bows, glaives and melee use their existing live collision path. */
    public static Contact trace(ServerPlayer owner, Vec3 from, Vec3 to, float margin, Predicate<Entity> eligible) {
        ServerLevel level = owner.level();
        HitResult wall = level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, owner));
        Vec3 end = wall.getType() == HitResult.Type.MISS ? to : wall.getLocation();
        AABB broad = new AABB(from, end).inflate(margin + .2);
        int now = level.getServer().getTickCount();
        // Ping is the server-measured round trip: outbound target state + inbound firing command.
        double networkTicks = Math.max(0, owner.connection.latency()) / 50.0;
        var candidates = new IdentityHashMap<LivingEntity, AABB>();
        var recorded = HISTORY.getOrDefault(level, Map.of());
        for (var entry : recorded.entrySet()) {
            LivingEntity entity = entry.getKey();
            History history = entry.getValue();
            // Cheap swept bounds first: don't interpolate or evaluate combat relations across the whole world per pellet.
            if ((history.bounds == null || !history.bounds.intersects(broad)) && !entity.getBoundingBox().intersects(broad)) continue;
            if (entity == owner || entity.level() != level || !entity.isAlive() || entity.isSpectator() || !eligible.test(entity)) continue;
            // 26.3 SteppedInterpolationHandler takes its duration from the target EntityType.
            double wanted = now - Math.min(MAX_REWIND_TICKS, Math.max(1, entity.getType().updateInterval()) + networkTicks);
            AABB body = history.at(entity, now, wanted);
            if (body.inflate(margin).intersects(broad)) candidates.put(entity, body);
        }
        // Unrecorded/new/over-capacity entities retain native current-position collision.
        for (var entity : level.getEntities(owner, broad, eligible))
            if (entity instanceof LivingEntity living && !recorded.containsKey(living)) candidates.put(living, living.getBoundingBox());
        Contact result = new Contact(wall, null);
        double closest = from.distanceToSqr(end);
        for (var entry : candidates.entrySet()) {
            AABB expanded = entry.getValue().inflate(margin);
            var point = expanded.contains(from) ? Optional.of(from) : expanded.clip(from, end);
            if (point.isEmpty()) continue;
            double distance = from.distanceToSqr(point.get());
            if (distance + 1e-6 < closest || result.hit().getType() == HitResult.Type.MISS && distance <= closest) {
                closest = distance;
                result = new Contact(new EntityHitResult(entry.getKey(), point.get()), entry.getValue());
            }
        }
        return result;
    }
}
