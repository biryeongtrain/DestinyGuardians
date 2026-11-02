package kim.biryeong.destiny.campaign.presentation;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ManualAttachment;
import eu.pb4.polymer.virtualentity.api.elements.BlockDisplayElement;
import eu.pb4.polymer.virtualentity.api.elements.DisplayElement;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.campaign.RisingLoadout;
import kim.biryeong.destiny.campaign.RisingServices;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponModels;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Brightness;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.util.ArrayList;
import java.util.List;

/**
 * Weapon pickup marker (original W300 staging; the extraction has no pickup VFX). Owner-only Polymer
 * displays at a fixed point: the real weapon item model (WeaponModels.create, same as the granted loan),
 * full bright; a Fallen crate of block displays for the cache; a soft cyan dust column; a glow outline
 * once the owner is within {@link #OUTLINE_RANGE}. {@link #collect()} flashes and plays the transmat sound.
 */
final class Pickup extends RisingPresentation.Scene implements RisingServices.PickupHandle {
    static final String RIFLE = "rifle", CACHE = "shotgun_cache";
    static final double OUTLINE_RANGE = 6.0;
    /** Clearance for the current fixed-context Khvostov/Stubborn Oak models, including their bob. */
    static final float WEAPON_LIFT = .15f;
    static final int CYAN = 0x4FE3FF;

    private final Vec3 pos;
    private final float yaw;
    private final String kind;
    private final ElementHolder holder = new ElementHolder();
    private final List<DisplayElement> outlined = new ArrayList<>();
    private ItemDisplayElement weapon;
    private ServerLevel level;
    private boolean outline;

    Pickup(ServerPlayer player, Vec3 pos, float yaw, String kind) {
        super(player, null);
        this.pos = aboveSurface(player.level(), pos);
        this.yaw = yaw;
        this.kind = CACHE.equals(kind) ? CACHE : RIFLE;
    }

    /** Imported prop markers may sit inside the voxel floor or a low supply box. Snap upward
     * through that local support only; stop at the first air gap so ceilings are never selected. */
    private static Vec3 aboveSurface(ServerLevel level, Vec3 marker) {
        BlockPos base = BlockPos.containing(marker);
        double y = marker.y;
        for (int dy = 0; dy < 3; dy++) {
            BlockPos block = base.above(dy);
            var shape = level.getBlockState(block).getCollisionShape(level, block);
            if (shape.isEmpty()) break;
            y = Math.max(y, block.getY() + shape.max(Direction.Axis.Y));
        }
        return new Vec3(marker.x, y, marker.z);
    }

    @Override void begin() {
        level = player.level();
        String id = kind.equals(CACHE) ? RisingLoadout.SHOTGUN : RisingLoadout.RIFLE;
        ItemStack stack = WeaponCatalog.find(id).map(WeaponModels::create).orElse(ItemStack.EMPTY);
        if (stack.isEmpty()) DestinyGuardians.LOGGER.warn("Guardian Rises: pickup weapon {} missing from catalog", id);
        else kim.biryeong.destiny.weapon.WeaponSkins.apply(stack, kind.equals(CACHE) ? RisingLoadout.SHOTGUN_SKIN : RisingLoadout.RIFLE_SKIN);
        weapon = new ItemDisplayElement(stack);
        weapon.setItemDisplayContext(ItemDisplayContext.FIXED);
        weapon.setBrightness(new Brightness(15, 15));
        weapon.setInterpolationDuration(3);
        weapon.setViewRange(1.5f);
        weapon.setGlowColorOverride(CYAN);
        holder.addElement(weapon);
        outlined.add(weapon);
        if (kind.equals(CACHE)) crate();
        place(0);
        new ManualAttachment(holder, level, () -> pos);
        holder.startWatching(player);
    }

    /** ~0.9 x 0.5 x 0.6 dark Fallen crate, cyan light straps, shotgun resting on the lid. */
    private void crate() {
        var r = new Quaternionf().rotateY((float) Math.toRadians(-yaw));
        box(Blocks.POLISHED_DEEPSLATE.defaultBlockState(), r, new Vector3f(-.45f, 0, -.3f), new Vector3f(.9f, .42f, .6f), false);
        box(Blocks.POLISHED_BLACKSTONE.defaultBlockState(), r, new Vector3f(-.47f, .42f, -.32f), new Vector3f(.94f, .1f, .64f), false);
        for (float x : new float[]{-.3f, .24f})
            box(Blocks.CONCRETE.cyan().defaultBlockState(), r, new Vector3f(x, .06f, -.31f), new Vector3f(.06f, .3f, .62f), true);
        box(Blocks.CONCRETE.purple().defaultBlockState(), r, new Vector3f(-.12f, .14f, -.315f), new Vector3f(.24f, .12f, .01f), true);
    }

    private void box(BlockState state, Quaternionf rotation, Vector3f from, Vector3f size, boolean lit) {
        var e = new BlockDisplayElement(state);
        e.setLeftRotation(new Quaternionf(rotation));
        e.setTranslation(rotation.transform(new Vector3f(from)));
        e.setScale(size);
        e.setBrightness(lit ? new Brightness(15, 15) : new Brightness(11, 15));
        e.setViewRange(1.5f);
        e.setGlowColorOverride(CYAN);
        holder.addElement(e);
        if (!lit) outlined.add(e);
    }

    @Override void update(int t, int now) {
        if (player.level() != level) { close(); return; }
        if ((t & 1) == 0) place(t);
        boolean near = player.position().distanceToSqr(pos) < OUTLINE_RANGE * OUTLINE_RANGE;
        if (near != outline) { outline = near; for (var e : outlined) e.setGlowing(near); }
        if (t % 4 == 0) column(t);
        holder.tick();
    }

    /** Rifle: lying on the floor with a slight tilt, bobbing 4 cm and turning slowly. Shotgun: on the lid. */
    private void place(int t) {
        float bob = (float) Math.sin(t / 14.0) * .04f;
        float spin = (float) Math.toRadians(-yaw) + t * .012f;
        if (kind.equals(CACHE)) {
            weapon.setScale(new Vector3f(.85f));
            weapon.setLeftRotation(new Quaternionf().rotateY((float) Math.toRadians(-yaw) + .35f).rotateX((float) (-Math.PI / 2)).rotateZ(.08f));
            weapon.setTranslation(new Vector3f(0, .58f + WEAPON_LIFT + bob * .5f, 0));
        } else {
            weapon.setScale(new Vector3f(.95f));
            weapon.setLeftRotation(new Quaternionf().rotateY(spin).rotateX((float) (-Math.PI / 2)).rotateY(.18f));
            weapon.setTranslation(new Vector3f(0, .22f + WEAPON_LIFT + bob, 0));
        }
        weapon.startInterpolationIfDirty();
    }

    /** Soft cyan light column. Never emitted near the owner's eye (screen-filling squares, Vision r2). */
    private void column(int t) {
        if (player.getEyePosition().distanceToSqr(pos) < 2.25) return;
        var dust = new DustParticleOptions(CYAN, .7f);
        double h = (t / 4 % 6) * .45 + .3;
        level.sendParticles(player, dust, true, false, pos.x, pos.y + h, pos.z, 2, .08, .12, .08, 0);
        level.sendParticles(player, new DustParticleOptions(0x2AA8E0, 1.1f), true, false, pos.x, pos.y + .15, pos.z, 1, .25, .02, .25, 0);
    }

    @Override public void collect() {
        if (closed) return;
        if (!player.hasDisconnected() && player.level() == level) {
            var dust = new DustParticleOptions(0xBFF6FF, 1.4f);
            Vec3 c = pos.add(0, kind.equals(CACHE) ? .6 : .3, 0);
            level.sendParticles(player, dust, true, false, c.x, c.y, c.z, 24, .35, .3, .35, 0);
            level.sendParticles(player, new DustParticleOptions(CYAN, .8f), true, false, c.x, c.y + .8, c.z, 16, .08, .8, .08, 0);
            RisingAudio.sfxAt(player, "transmat", c, .8f, 1.25f, 16f);
        }
        completeAndClose();
    }

    String kind() { return kind; }

    @Override void restore() { holder.destroy(); }
}
