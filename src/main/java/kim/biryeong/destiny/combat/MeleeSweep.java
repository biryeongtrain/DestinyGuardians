package kim.biryeong.destiny.combat;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Bounded server contact geometry shared by melee weapons and abilities. No costs, callbacks or locks. */
public final class MeleeSweep {
    public static final int MAX_CANDIDATES = 64, MAX_HITS = 16;
    private MeleeSweep() { }

    public static Vec3 center(LivingEntity target) { return target.getBoundingBox().getCenter(); }
    public static List<LivingEntity> frontal(ServerPlayer player, double reach, double cosine, double height) {
        return sweep(player, player.position(), player.position(), reach, cosine, height);
    }
    /** Each pose is at most half a block apart; LOS is evaluated from that pose, before owner dedup. */
    public static List<LivingEntity> sweep(ServerPlayer player, Vec3 start, Vec3 end,
                                           double reach, double cosine, double height) {
        if (!player.isAlive() || player.isRemoved() || !finite(start) || !finite(end)
                || start.distanceToSqr(end) > 64 || !valid(reach, cosine, height)) return List.of();
        Vec3 facing = Vec3.directionFromRotation(0, player.getYRot());
        Vec3 body = start.add(0, .9, 0);
        AABB search = new AABB(start, end).inflate(reach + 1, height + 2, reach + 1);
        var candidates = player.level().getEntitiesOfClass(LivingEntity.class, search,
                e -> e.level() == player.level() && Combat.isEnemy(player, e)).stream()
                .sorted(Comparator.comparingDouble((LivingEntity e) -> center(e).distanceToSqr(body))
                        .thenComparing(LivingEntity::getUUID)).limit(MAX_CANDIDATES).toList();
        var contacts = new LinkedHashMap<UUID, LivingEntity>();
        int samples = Math.max(1, (int) Math.ceil(start.distanceTo(end) / .5));
        for (int i = 0; i <= samples && contacts.size() < MAX_HITS; i++) {
            Vec3 feet = start.lerp(end, (double) i / samples);
            Vec3 origin = feet.add(0, .9, 0);
            Vec3 eye = feet.add(0, player.getEyeHeight(), 0);
            for (LivingEntity target : candidates) {
                UUID owner = Combat.damageOwner(target).getUUID();
                if (contacts.containsKey(owner)) continue;
                Vec3 to = center(target), delta = to.subtract(origin);
                if (!inside(facing.x, facing.z, delta.x, delta.y, delta.z, reach, cosine, height)
                        || !visible(player, eye, to)) continue;
                contacts.put(owner, target);
                if (contacts.size() == MAX_HITS) break;
            }
        }
        return List.copyOf(contacts.values());
    }
    public static boolean visible(ServerPlayer player, Vec3 from, Vec3 to) {
        if (!finite(from) || !finite(to) || from.distanceToSqr(to) > 256) return false;
        int samples = Math.max(1, (int) Math.ceil(from.distanceTo(to) * 2));
        for (int i = 0; i <= samples; i++) {
            BlockPos pos = BlockPos.containing(from.lerp(to, (double) i / samples));
            if (!player.level().hasChunkAt(pos) || !player.level().getWorldBorder().isWithinBounds(pos)) return false;
        }
        return player.level().clip(new ClipContext(from, to, ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, player)).getType() == HitResult.Type.MISS;
    }
    /** Pure yaw geometry. Negative cosine is reserved for explicitly radial spin/slam shapes. */
    public static boolean inside(double fx, double fz, double x, double y, double z,
                                  double reach, double cosine, double height) {
        if (!Double.isFinite(fx) || !Double.isFinite(fz) || !Double.isFinite(x)
                || !Double.isFinite(y) || !Double.isFinite(z) || !valid(reach, cosine, height)
                || Math.abs(y) > height) return false;
        double direction = Math.hypot(fx, fz), distance = Math.hypot(x, z);
        if (direction < 1e-8 || distance > reach + 1e-8) return false;
        return distance < 1e-8 || fx / direction * x / distance + fz / direction * z / distance + 1e-8 >= cosine;
    }
    private static boolean valid(double reach, double cosine, double height) {
        return Double.isFinite(reach) && Double.isFinite(cosine) && Double.isFinite(height)
                && reach > 0 && reach <= 8 && cosine >= -1 && cosine <= 1 && height >= 0 && height <= 4;
    }
    private static boolean finite(Vec3 v) { return Double.isFinite(v.x) && Double.isFinite(v.y) && Double.isFinite(v.z); }
}
