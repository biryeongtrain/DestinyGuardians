package kim.biryeong.destiny.tutorial;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.EntityAttachment;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.util.Brightness;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.util.Collection;

/** Owner-private Generalist Shell derivative. Eleven displays, interpolated at 10 Hz. */
final class TutorialGhost {
    private static final class Attachment extends EntityAttachment {
        final ServerPlayer owner;
        Attachment(ElementHolder holder, ServerPlayer owner) { super(holder, owner, false); this.owner = owner; attach(); }
        @Override public void updateCurrentlyTracking(Collection<ServerGamePacketListenerImpl> watching) {
            for (var connection : java.util.List.copyOf(watching))
                if (connection != owner.connection) holder().stopWatching(connection);
            if (!owner.isRemoved() && !owner.hasDisconnected()) holder().startWatching(owner);
        }
    }

    private final ServerPlayer owner;
    private final ElementHolder holder = new ElementHolder();
    private final java.util.List<ItemDisplayElement> parts = new java.util.ArrayList<>();
    private float openness;
    private Vec3 position;
    private Vec3 anchor;
    private int speakingUntil;

    TutorialGhost(ServerPlayer owner, Vec3 start) {
        this.owner = owner;
        this.position = start;
        add("eye_lens_emissive");
        add("innercore_frame");
        add("innercore_sphere");
        add("outershell_1d04de8c");
        add("outershell_28b4d4c7");
        add("outershell_54703d26");
        add("outershell_5cc2cf05");
        add("outershell_5d17056f");
        add("outershell_9b1a9b66");
        add("outershell_bbb26ac5");
        add("outershell_eaa747df");
        new Attachment(holder, owner);
        holder.startWatching(owner);
        place();
    }

    private void add(String name) {
        var stack = new ItemStack(Items.PAPER);
        stack.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny", "tutorial/ghost/" + name));
        var e = new ItemDisplayElement(stack);
        e.setItemDisplayContext(ItemDisplayContext.NONE);
        e.setScale(new Vector3f(.72f));
        e.setBrightness(name.startsWith("eye") ? new Brightness(15, 15) : new Brightness(10, 12));
        // ItemDisplayRenderer rotates every item by PI around Y after the display transform.
        // Cancel that rotation so the exported +Z eye actually faces the owner.
        e.setRightRotation(new Quaternionf().rotateY((float) Math.PI));
        e.setInterpolationDuration(2);
        e.setTeleportDuration(2);
        e.setViewRange(2);
        parts.add(e);
        holder.addElement(e);
    }

    /** Fixed world anchor, or null to follow the player's shoulder. */
    void anchor(Vec3 world) { this.anchor = world; }
    void speak(int untilTick) { speakingUntil = untilTick; }
    Vec3 position() { return position; }

    void tick(int now) {
        if ((now & 1) != 0) return;
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
        openness += ((now < speakingUntil ? .28f : 0f) - openness) * .22f;
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
        for (int i = 0; i < parts.size(); i++) {
            var part = parts.get(i);
            var local = i < 3 ? new Vector3f() : new Vector3f(RADIAL[i]).mul(openness);
            facing.transform(local);
            part.setLeftRotation(facing);
            part.setTranslation(local.add((float) offset.x, (float) offset.y, (float) offset.z));
            part.startInterpolationIfDirty();
        }
    }

    private static final Vector3f[] RADIAL = {
        new Vector3f(0.0000000f,-0.0000000f,0.1925601f),
        new Vector3f(0.0000144f,0.0038257f,0.0346197f),
        new Vector3f(0.0000000f,0.0000000f,0.0000000f),
        new Vector3f(0.0066247f,0.2229442f,0.1193567f),
        new Vector3f(0.0074831f,0.2204300f,-0.1217252f),
        new Vector3f(0.2324386f,-0.0026568f,0.1419273f),
        new Vector3f(-0.2330984f,0.0144807f,0.1403276f),
        new Vector3f(0.2335264f,-0.0031903f,-0.1380431f),
        new Vector3f(-0.2322059f,0.0091602f,-0.1399293f),
        new Vector3f(-0.0071468f,-0.2115252f,0.1238535f),
        new Vector3f(-0.0062720f,-0.2140460f,-0.1172277f)
    };

    void destroy() { holder.destroy(); }
}
