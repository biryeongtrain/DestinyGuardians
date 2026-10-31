package kim.biryeong.destiny.tutorial;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.EntityAttachment;
import eu.pb4.polymer.virtualentity.api.elements.BlockDisplayElement;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.util.Brightness;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.util.Collection;

/**
 * The player's Ghost companion: a two-shell, star-shaped drone with a glowing eye, built from three
 * display cubes. It hovers at an anchor (the awakening reveal) or beside the player's shoulder and
 * spins faster while it is speaking. Cosmetic only; no collision, no entity.
 */
final class TutorialGhost {
    private static final class Attachment extends EntityAttachment {
        final ServerPlayer owner;
        Attachment(ElementHolder holder, ServerPlayer owner) { super(holder, owner, true); this.owner = owner; attach(); }
        @Override public void updateCurrentlyTracking(Collection<ServerGamePacketListenerImpl> watching) {
            super.updateCurrentlyTracking(watching.stream().filter(c -> c != owner.connection).toList());
            if (!owner.isRemoved() && !owner.hasDisconnected()) holder().startWatching(owner);
        }
    }

    private final ServerPlayer owner;
    private final ElementHolder holder = new ElementHolder();
    private final BlockDisplayElement outer, inner, eye;
    private Vec3 position;
    private Vec3 anchor;
    private float spin;
    private int speakingUntil;

    TutorialGhost(ServerPlayer owner, Vec3 start) {
        this.owner = owner;
        this.position = start;
        outer = cube(Blocks.CONCRETE.pick(DyeColor.WHITE).defaultBlockState(), .30f);
        inner = cube(Blocks.CONCRETE.pick(DyeColor.LIGHT_GRAY).defaultBlockState(), .26f);
        eye = cube(Blocks.SEA_LANTERN.defaultBlockState(), .11f);
        holder.addElement(outer);
        holder.addElement(inner);
        holder.addElement(eye);
        new Attachment(holder, owner);
        holder.startWatching(owner);
        place();
    }

    private static BlockDisplayElement cube(BlockState state, float size) {
        var e = new BlockDisplayElement(state);
        e.setScale(new Vector3f(size));
        e.setBrightness(new Brightness(15, 15));
        e.setInterpolationDuration(2);
        e.setTeleportDuration(2);
        e.setViewRange(2);
        return e;
    }

    /** Fixed world anchor, or null to follow the player's shoulder. */
    void anchor(Vec3 world) { this.anchor = world; }
    void speak(int untilTick) { speakingUntil = untilTick; }
    Vec3 position() { return position; }

    void tick(int now) {
        Vec3 target;
        if (anchor != null) target = anchor.add(0, Math.sin(now / 12.0) * .08, 0);
        else {
            double yaw = Math.toRadians(owner.getYRot());
            Vec3 right = new Vec3(-Math.cos(yaw), 0, -Math.sin(yaw));
            Vec3 forward = new Vec3(-Math.sin(yaw), 0, Math.cos(yaw));
            // Ahead and to the right of the view, slightly above eye level: in sight, never on the lens.
            target = owner.position().add(right.scale(1.25)).add(forward.scale(2.1)).add(0, owner.getEyeHeight() + .45 + Math.sin(now / 12.0) * .06, 0);
        }
        position = position.distanceToSqr(target) > 64 ? target : position.lerp(target, .3);
        spin += now < speakingUntil ? .35f : .06f;
        place();
        holder.tick();
    }

    private void place() {
        Vec3 offset = position.subtract(owner.position());
        // Face the player: the eye points from the ghost to the player's eyes.
        Vec3 look = owner.getEyePosition().subtract(position);
        float yaw = (float) Math.atan2(look.x, look.z);
        float pitch = (float) -Math.atan2(look.y, Math.sqrt(look.x * look.x + look.z * look.z));
        var facing = new Quaternionf().rotateY(yaw).rotateX(pitch);
        set(outer, offset, new Quaternionf(facing).rotateZ(spin).rotateX(.785f).rotateY(.785f), .15f);
        set(inner, offset, new Quaternionf(facing).rotateZ(-spin * .7f + .785f), .13f);
        var eyeOffset = offset.add(new Vec3(facing.transform(new Vector3f(0, 0, .29f))));
        set(eye, eyeOffset, facing, .055f);
    }

    /** Entity-attached displays sit at the player's feet; place the ghost through display translation
     * (interpolated metadata), as GlaiveShieldVfx does, rather than the attachment offset. */
    private static void set(BlockDisplayElement e, Vec3 offset, Quaternionf rotation, float half) {
        e.setLeftRotation(rotation);
        e.setTranslation(rotation.transform(new Vector3f(-half, -half, -half))
                .add((float) offset.x, (float) offset.y, (float) offset.z));
        e.startInterpolationIfDirty();
    }

    void destroy() { holder.destroy(); }
}
