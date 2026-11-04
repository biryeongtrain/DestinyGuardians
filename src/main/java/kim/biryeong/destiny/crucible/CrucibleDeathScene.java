package kim.biryeong.destiny.crucible;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.tutorial.TutorialGhost;
import net.minecraft.network.protocol.game.ClientboundAddEntityPacket;
import net.minecraft.network.protocol.game.ClientboundRemoveEntitiesPacket;
import net.minecraft.network.protocol.game.ClientboundSetEntityDataPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/** Server-owned five-second death view. All entities are private packets, never world/save entries. */
public final class CrucibleDeathScene {
    public static final int RESPAWN_TICKS = 100;
    public static final Identifier EFFECT = DestinyGuardians.id("crucible/guardian_down");
    private static final Map<UUID, CrucibleDeathScene> ACTIVE = new HashMap<>();

    public record Death(ServerLevel level, Vec3 ghost, float yaw, int until, String killer) { }

    private final ServerPlayer player;
    private final Death death;
    private final Display.ItemDisplay camera;
    private TutorialGhost ghost;
    private boolean ownedEffect;
    private int startedAt = -1;

    private CrucibleDeathScene(ServerPlayer player, Death death) {
        this.player = player;
        this.death = death;
        camera = new Display.ItemDisplay(EntityTypes.ITEM_DISPLAY, death.level());
        camera.setNoGravity(true);
        camera.setSilent(true);
        Vec3 at = death.ghost();
        // Prefer the player's previous facing; near walls choose a side with room for the shell.
        for (float turn : new float[]{0, 90, -90, 180}) {
            Vec3 direction = Vec3.directionFromRotation(0, death.yaw() + turn);
            Vec3 desired = death.ghost().subtract(direction.scale(3.4)).add(0, .7, 0);
            Vec3 candidate = clip(player, death, desired);
            if (candidate.distanceToSqr(death.ghost()) > at.distanceToSqr(death.ghost())) at = candidate;
            if (at.distanceToSqr(death.ghost()) >= 3.24) break;
        }
        Vec3 look = death.ghost().subtract(at);
        camera.setPos(at);
        camera.setYRot((float) Math.toDegrees(Math.atan2(-look.x, look.z)));
        camera.setXRot((float) -Math.toDegrees(Math.atan2(look.y, look.horizontalDistance())));
    }

    private static Vec3 clip(ServerPlayer player, Death death, Vec3 desired) {
        Vec3 origin = death.ghost(), delta = desired.subtract(origin);
        double fraction = 1;
        for (double x : new double[]{-.18, 0, .18}) for (double y : new double[]{-.18, 0, .18}) {
            Vec3 offset = new Vec3(x, y, 0);
            var hit = death.level().clip(new ClipContext(origin.add(offset), desired.add(offset),
                    ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
            if (hit.getType() != HitResult.Type.MISS)
                fraction = Math.min(fraction, Math.max(0, (hit.getLocation().distanceTo(origin.add(offset)) - .22) / delta.length()));
        }
        return origin.add(delta.scale(fraction));
    }

    public static boolean active(ServerPlayer player) {
        var scene = ACTIVE.get(player.getUUID());
        return scene != null && scene.player == player;
    }

    /** Prevent sneak/attack spectator camera changes from escaping an owned death view. */
    public static boolean blocksCameraChange(ServerPlayer player, Entity requested) {
        var scene = ACTIVE.get(player.getUUID());
        return scene != null && scene.player == player && player.level() == scene.death.level()
                && requested != scene.camera;
    }

    public static void start(ServerPlayer player, Death death) {
        stop(player);
        var scene = new CrucibleDeathScene(player, death);
        ACTIVE.put(player.getUUID(), scene);
        try {
            player.setGameMode(GameType.SPECTATOR);
            Vec3 at = scene.camera.position();
            if (!player.teleportTo(death.level(), at.x, at.y, at.z, Set.of(), scene.camera.getYRot(), scene.camera.getXRot(), false))
                throw new IllegalStateException("Death camera transfer refused");
            player.setDeltaMovement(Vec3.ZERO);
            player.fallDistance = 0;
            player.connection.send(new ClientboundAddEntityPacket(scene.camera.getId(), scene.camera.getUUID(),
                    at.x, at.y, at.z, scene.camera.getXRot(), scene.camera.getYRot(), scene.camera.getType(), 0, Vec3.ZERO, scene.camera.getYRot()));
            var data = scene.camera.getEntityData().getNonDefaultValues();
            if (data != null) player.connection.send(new ClientboundSetEntityDataPacket(scene.camera.getId(), data));
            player.setCamera(scene.camera);
            scene.ghost = new TutorialGhost(player, death.ghost());
            scene.ghost.anchor(death.ghost());
            scene.ghost.deploy(at);
            scene.ownedEffect = player.addPostEffect(EFFECT);
            if (scene.ownedEffect) CrucibleRecovery.markDeathEffect(player);
            tick(player, player.level().getServer().getTickCount());
        } catch (RuntimeException error) {
            stop(player);
            throw error;
        }
    }

    public static void tick(ServerPlayer player, int now) {
        var scene = ACTIVE.get(player.getUUID());
        if (scene == null || scene.player != player) return;
        if (player.hasDisconnected() || player.isRemoved() || !player.isAlive() || player.level() != scene.death.level()) {
            stop(player);
            return;
        }
        scene.ghost.tick(now);
        if (scene.startedAt < 0) scene.startedAt = now;
        if ((now & 1) == 0) kim.biryeong.destiny.down.GuardianDown.externalHud(player, now - scene.startedAt,
                Math.max(0, scene.death.until() - now), RESPAWN_TICKS, scene.death.killer(), "팀 스폰 지점에서 자동 부활");
    }

    public static void stop(ServerPlayer player) {
        var scene = ACTIVE.get(player.getUUID());
        if (scene == null || scene.player != player) return;
        ACTIVE.remove(player.getUUID());
        if (scene.ghost != null) scene.ghost.destroy();
        if (scene.ownedEffect) {
            player.removePostEffect(EFFECT);
            CrucibleRecovery.clearDeathEffect(player);
        }
        CrucibleUi.remove(player);
        kim.biryeong.destiny.down.GuardianDown.clearExternalHud(player);
        if (player.getCamera() == scene.camera) player.setCamera(player);
        if (!player.hasDisconnected()) player.connection.send(new ClientboundRemoveEntitiesPacket(scene.camera.getId()));
        scene.camera.discard();
    }
}
