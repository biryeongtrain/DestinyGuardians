package kim.biryeong.destiny.ability.hunter;

import kim.biryeong.destiny.ability.Motion;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.ShadowshotTiming;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

/** A single draw's small, collision-resolved hop, not a flight ability.
 * Never changes gravity, abilities, pose/hitbox, fall distance, or horizontal velocity.
 * The session owns this object: ending/cancelling it leaves vanilla gravity in charge.
 */
final class ShadowshotLift {
    // Full-draw ground-fit root delta H20(+.3899) -> H21(-2.9683), in blocks.
    static final double RELEASE_DROP = (.3899 + 2.9683) / 16;
    private final ServerLevel level;
    private final Vec3 origin;
    private final int started;
    private final double targetY;
    private int lastTick;
    private boolean finished;

    ShadowshotLift(ServerPlayer player) {
        level = player.level();
        origin = player.position();
        started = lastTick = level.getServer().getTickCount();
        targetY = origin.y + (player.onGround() ? .60 : .15);
        finished = !eligible(player);
    }

    private boolean eligible(ServerPlayer player) {
        return player.level() == level && player.isAlive() && !player.isRemoved() && !player.hasDisconnected()
                && SuperCamera.active(player) && !player.isSpectator() && !player.isPassenger()
                && !player.getAbilities().flying && !player.isFallFlying() && !player.isNoGravity()
                && !player.isInWater() && !player.isInLava();
    }

    void tick(ServerPlayer player) {
        if (finished) return;
        int now = level.getServer().getTickCount();
        if (now == lastTick) return;
        lastTick = now;
        int elapsed = now - started;
        if (elapsed >= ShadowshotTiming.RELEASE_TICKS || !eligible(player)
                || player.position().distanceToSqr(origin) > 16 || player.getY() > targetY + .3
                || !level.noCollision(player, player.getBoundingBox().move(0, .25, 0))) {
            finished = true;
            return;
        }
        // One preparation tick lets the crouched pose read before the small lift.
        if (elapsed < 2) return;
        Vec3 old = player.getDeltaMovement();
        // A deliberate air jump/other strong knockback relinquishes this cosmetic assist.
        if (old.y > .4) { finished = true; return; }
        Motion.setVelocity(player, new Vec3(old.x, verticalSpeed(targetY - player.getY()), old.z));
    }

    static double verticalSpeed(double remaining) {
        return Math.clamp(remaining, -.06, .22);
    }

    static Vec3 releasePoint(ServerPlayer player) {
        return player.getEyePosition().add(0, -RELEASE_DROP, 0);
    }
}
