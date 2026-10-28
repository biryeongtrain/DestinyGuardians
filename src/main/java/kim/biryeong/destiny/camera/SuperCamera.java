package kim.biryeong.destiny.camera;

import io.netty.buffer.Unpooled;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.protocol.game.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/** Experimental vanilla combat camera. No spectator mode, real mount, or player setCamera/teleport per tick.
 * The owner alone sees a fake passenger mount, enabling vanilla's unconditional passenger Rot packets.
 * Native server player physics consumes key state; client position/ground claims are ignored during ownership.
 * All methods run on the server thread.
 */
public final class SuperCamera {
    private static final Map<UUID, Session> ACTIVE = new HashMap<>();
    public static final boolean ENABLED = Boolean.parseBoolean(System.getProperty("destiny.superCamera", "true"));
    private static final int ROTATION_TIMEOUT = 40;

    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final boolean bow;
        final Display.ItemDisplay mount, camera;
        final net.minecraft.world.item.ItemStack swordStack;
        Vec3 previous;
        Vec3 physicsStart;
        int lastRotation, rotations;
        int movementUnlockTick;

        Session(ServerPlayer owner, Element element,net.minecraft.world.item.ItemStack swordStack) {
            this.owner = owner;
            this.swordStack=swordStack;
            bow = element == Element.VOID;
            level = owner.level();
            mount = marker(owner);
            camera = marker(owner);
            previous = owner.position();
            lastRotation = level.getServer().getTickCount();
        }
    }

    private SuperCamera() { }

    private static Display.ItemDisplay marker(ServerPlayer p) {
        Display.ItemDisplay e = new Display.ItemDisplay(EntityTypes.ITEM_DISPLAY, p.level());
        e.setPos(p.position());
        e.setNoGravity(true);
        ((kim.biryeong.destiny.mixin.DisplayCameraAccessor) e).destiny$setCameraInterpolation(1);
        e.setSilent(true);
        return e; // Never add to the world, entity tracker, save data, or other viewers.
    }

    public static boolean active(ServerPlayer p) { return ACTIVE.containsKey(p.getUUID()); }
    public static boolean swordActive(ServerPlayer p) {
        Session s=ACTIVE.get(p.getUUID());return s!=null&&s.swordStack!=null;
    }
    public static void stopSword(ServerPlayer p) {
        if(swordActive(p))stop(p);
    }
    public static int activeCount() { return ACTIVE.size(); }
    /** Session-owned input gate, not a teleport/freeze: gravity and existing impulses remain native. */
    public static void blockMovement(ServerPlayer p, int ticks) {
        Session s = ACTIVE.get(p.getUUID());
        if (s != null && !s.bow) s.movementUnlockTick = s.level.getServer().getTickCount() + Math.max(0, ticks);
    }

    public static boolean movementBlocked(ServerPlayer p) {
        Session s = ACTIVE.get(p.getUUID());
        return s != null && s.level.getServer().getTickCount() < s.movementUnlockTick;
    }
    public static int rotations(ServerPlayer p) {
        Session s = ACTIVE.get(p.getUUID());
        return s == null ? 0 : s.rotations;
    }
    public static Vec3 cameraPosition(ServerPlayer p) {
        Session s = ACTIVE.get(p.getUUID());
        return s == null ? p.getEyePosition() : s.camera.position();
    }

    /** Solar is a strict no-op. Returns false before consuming energy if an unsupported state is occupied. */
    public static boolean start(ServerPlayer p, Element element) {
        if (element == Element.SOLAR || !ENABLED) return true;
        if (element != Element.ARC && element != Element.VOID) return true;
        return startSession(p,element,null);
    }

    /** All Titan/Warlock supers use the normal rear camera, including Solar. Golden Gun keeps start(). */
    public static boolean startThirdPerson(ServerPlayer p) {
        return !ENABLED || startSession(p, Element.KINETIC, null);
    }

    /** Sword stays third-person while this exact held stack is selected, not only during a swing. */
    public static boolean startSword(ServerPlayer p) {
        if(!ENABLED||!kim.biryeong.destiny.weapon.SwordItems.isSword(p.getMainHandItem())
                ||AbilityService.inSuper(p)||!kim.biryeong.destiny.weapon.WeaponLoadout.canUse(p))return false;
        Session s=ACTIVE.get(p.getUUID());
        if(s!=null)return s.swordStack==p.getMainHandItem();
        return startSession(p,Element.KINETIC,p.getMainHandItem());
    }

    private static boolean startSession(ServerPlayer p,Element element,net.minecraft.world.item.ItemStack swordStack) {
        if (p.isPassenger() || p.isSpectator() || p.isDeadOrDying() || p.isSleeping()
                || p.getAbilities().flying || p.isFallFlying() || p.hasDisconnected()
                || p.getCamera() != p || CameraViews.get(p) != null) return false;
        stop(p);
        Session s = new Session(p, element,swordStack);
        ACTIVE.put(p.getUUID(), s);
        try {
            updatePositions(s);
            spawn(p, s.mount);
            spawn(p, s.camera);
            p.connection.send(passengers(s.mount.getId(), p.getId()));
            p.connection.send(new ClientboundSetActionBarTextPacket(Component.empty()));
            p.connection.send(new ClientboundSetCameraPacket(s.camera));
            PlayerAnimations.refreshOwnerVisibility(p);
            return true;
        } catch (RuntimeException e) {
            stop(p);
            DestinyGuardians.LOGGER.warn("Super camera start failed: {}", e.toString());
            return false;
        }
    }

    private static void spawn(ServerPlayer p, Display.ItemDisplay e) {
        Vec3 v = e.position();
        p.connection.send(new ClientboundAddEntityPacket(e.getId(), e.getUUID(), v.x, v.y, v.z,
                e.getXRot(), e.getYRot(), e.getType(), 0, Vec3.ZERO, e.getYRot()));
        var data = e.getEntityData().getNonDefaultValues();
        if (data != null) p.connection.send(new ClientboundSetEntityDataPacket(e.getId(), data));
    }

    private static ClientboundSetPassengersPacket passengers(int vehicle, int... riders) {
        FriendlyByteBuf b = new FriendlyByteBuf(Unpooled.buffer());
        try {
            b.writeVarInt(vehicle);
            b.writeVarIntArray(riders);
            return ClientboundSetPassengersPacket.STREAM_CODEC.decode(b);
        } finally { b.release(); }
    }

    /** Called immediately before the one native Player.tick from ServerPlayer.doTick. Never moves twice. */
    public static void beforePhysics(ServerPlayer p) {
        Session s = ACTIVE.get(p.getUUID());
        if (s == null) return;
        s.physicsStart = p.position();
        Input in = p.getLastClientInput();
        if (movementBlocked(p)) {
            p.xxa = 0;
            p.zza = 0;
            p.setJumping(false);
            p.setShiftKeyDown(false);
            p.setSprinting(false);
            return;
        }
        var v = CameraMath.input(in.forward(), in.backward(), in.left(), in.right(), in.shift());
        p.xxa = v.strafe();
        p.zza = v.forward();
        p.setJumping(in.jump());
        p.setShiftKeyDown(in.shift());
        p.setSprinting(in.sprint() && in.forward() && !in.shift() && p.getFoodData().getFoodLevel() > 6);
    }

    /** Server players normally bookkeep falls in handleMovePlayer, which our ownership cancels.
     * Use only the native collision-resolved delta, once after each native tick, never packet ground flags.
     */
    public static void afterPhysics(ServerPlayer p) {
        Session s = ACTIVE.get(p.getUUID());
        if (s == null || s.physicsStart == null) return;
        Vec3 from = s.physicsStart;
        s.physicsStart = null;
        if (p.level() != s.level || p.getCamera() != p || CameraViews.get(p) != null
                || !p.isAlive() || p.isPassenger()) return;
        Vec3 delta = p.position().subtract(from);
        if (delta.lengthSqr() <= 64) p.doCheckFallDamage(delta.x, delta.y, delta.z, p.onGround());
    }

    /** True consumes every move packet while owned, even spoofed position/ground/NaN claims.
     * Rotation is the only accepted field. Native server collision/gravity/fall state stays authoritative.
     */
    public static boolean move(ServerPlayer p, ServerboundMovePlayerPacket packet) {
        Session s = ACTIVE.get(p.getUUID());
        if (s == null) return false;
        if (packet.hasRotation()) {
            float yaw = packet.getYRot(p.getYRot()), pitch = packet.getXRot(p.getXRot());
            if (Float.isFinite(yaw) && Float.isFinite(pitch)) {
                p.setYRot(Mth.wrapDegrees(yaw));
                p.setXRot(Mth.clamp(pitch, -90, 90));
                p.setYHeadRot(p.getYRot());
                s.lastRotation = s.level.getServer().getTickCount();
                s.rotations++;
            }
        }
        return true;
    }

    /** After animation tick: retain final Void release/recovery even after gameplay has ended. */
    public static void tick(MinecraftServer server) {
        for (Session s : java.util.List.copyOf(ACTIVE.values())) {
            if (s.level.getServer() != server) continue;
            ServerPlayer p = s.owner;
            boolean foreign = p.getCamera() != p || CameraViews.get(p) != null;
            boolean invalid = p.isRemoved() || !p.isAlive() || p.hasDisconnected() || p.level() != s.level
                    || p.isSpectator() || p.isSleeping() || p.isPassenger() || p.getAbilities().flying || p.isFallFlying();
            boolean timedOut = server.getTickCount() - s.lastRotation > ROTATION_TIMEOUT;
            boolean teleported = p.position().distanceToSqr(s.previous) > 64;
            if(s.swordStack!=null&&(p.getMainHandItem()!=s.swordStack
                    ||!kim.biryeong.destiny.weapon.WeaponLoadout.canUse(p)||AbilityService.inSuper(p))) {
                release(s,!foreign&&p.level()==s.level);
                PlayerAnimations.stopSword(p);
                continue;
            }
            if (foreign || invalid || timedOut || teleported) {
                // Remove our control BEFORE ending the super; no recursive ownership or delayed camera resurrection.
                release(s, !foreign && p.level() == s.level);
                if(s.swordStack==null) {
                    if (AbilityService.inSuper(p)) AbilityService.endSuper(p);
                    PlayerAnimations.stop(p);
                } else PlayerAnimations.stopSword(p);
                if (timedOut) DestinyGuardians.LOGGER.warn("Super camera rotation timed out for {}; safe release", p.getName().getString());
                continue;
            }
            if (s.swordStack==null && !AbilityService.inSuper(p) && !PlayerAnimations.isPlaying(p)) {
                stop(p);
                continue;
            }
            updatePositions(s);
            p.connection.send(ClientboundEntityPositionSyncPacket.of(s.mount));
            p.connection.send(ClientboundEntityPositionSyncPacket.of(s.camera));
            // Sneak can locally dismount a fake mount. Reassert ownership; rotation watchdog handles failures.
            p.connection.send(passengers(s.mount.getId(), p.getId()));
            if (p.getLastClientInput().shift()) p.connection.send(new ClientboundSetActionBarTextPacket(Component.empty()));
            s.previous = p.position();
        }
    }

    private static void updatePositions(Session s) {
        ServerPlayer p = s.owner;
        Vec3 eye = p.getEyePosition();
        var target = s.bow
                ? CameraMath.desiredBow(eye.x, eye.y, eye.z, p.getYRot(), p.getXRot())
                : CameraMath.desired(eye.x, eye.y, eye.z, p.getYRot(), p.getXRot());
        Vec3 desired = new Vec3(target.x(), target.y(), target.z());
        Vec3 delta = desired.subtract(eye);
        double fraction = 1;
        // A small volume, not just a centre ray: keep camera near-plane corners in front of walls.
        for (double x : new double[]{-0.18, 0, 0.18}) {
            for (double y : new double[]{-0.18, 0, 0.18}) {
                Vec3 offset = new Vec3(x, y, 0);
                var hit = s.level.clip(new ClipContext(eye.add(offset), desired.add(offset),
                        ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
                if (hit.getType() != HitResult.Type.MISS) {
                    double distance = hit.getLocation().distanceTo(eye.add(offset));
                    fraction = Math.min(fraction, Math.max(0, (distance - 0.22) / delta.length()));
                }
            }
        }
        Vec3 camera = eye.add(delta.scale(fraction));
        // Vanilla player's vehicle attachment offset is -0.6; the virtual seat compensates it.
        s.mount.setPos(p.position().add(0, 0.6, 0));
        s.camera.setPos(camera);
        s.camera.setYRot(p.getYRot());
        s.camera.setXRot(p.getXRot());
    }

    public static void stop(ServerPlayer p) {
        Session s = ACTIVE.get(p.getUUID());
        if (s != null) release(s, p.getCamera() == p && CameraViews.get(p) == null && p.level() == s.level);
    }

    private static void release(Session s, boolean restore) {
        ServerPlayer p = s.owner;
        if (!ACTIVE.remove(p.getUUID(), s)) return;
        p.xxa = 0;
        p.zza = 0;
        p.setJumping(false);
        if (!p.hasDisconnected()) {
            if (restore) p.connection.send(new ClientboundSetCameraPacket(p));
            p.connection.send(passengers(s.mount.getId()));
            p.connection.send(new ClientboundRemoveEntitiesPacket(s.mount.getId(), s.camera.getId()));
            // A single authoritative resync on return, never per tick. Do not teleport a dead/new-world player.
            if (restore && p.isAlive() && !p.isRemoved()) {
                Vec3 velocity=p.getDeltaMovement();
                p.teleportTo(p.getX(),p.getY(),p.getZ());
                p.setDeltaMovement(velocity);
            }
        }
        PlayerAnimations.refreshOwnerVisibility(p);
    }
}
