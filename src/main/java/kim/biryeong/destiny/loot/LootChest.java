package kim.biryeong.destiny.loot;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ManualAttachment;
import eu.pb4.polymer.virtualentity.api.elements.InteractionElement;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import eu.pb4.polymer.virtualentity.api.elements.VirtualElement;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Brightness;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * A personal reward chest (Destiny activity chests are per player). Right/left click or standing at it for
 * {@link #STAND_TICKS} opens it and rolls its table once. {@link #close(boolean)} with delivery hands an unopened
 * reward over anyway, so leaving an activity never loses it.
 */
public final class LootChest {
    static final int STAND_TICKS = 30;
    static final int GOLD = 0xE3C46B;

    final ServerPlayer owner;
    final ServerLevel level;
    final String table, source;
    final Vec3 pos;
    final float yaw;
    private final ElementHolder holder = new ElementHolder();
    private final ItemDisplayElement chest;
    private int age, standing, openedAt;
    boolean opened, done;

    LootChest(ServerPlayer owner, Vec3 at, float yaw, String table, String source) {
        this.owner = owner; this.level = owner.level(); this.pos = at; this.yaw = yaw; this.table = table; this.source = source;
        chest = new ItemDisplayElement(new ItemStack(Items.CHEST));
        chest.setItemDisplayContext(ItemDisplayContext.FIXED);
        chest.setBrightness(new Brightness(15, 15));
        chest.setScale(new Vector3f(.9f));
        chest.setTranslation(new Vector3f(0, .45f, 0));
        chest.setLeftRotation(new Quaternionf().rotateY((float) Math.toRadians(180 - yaw)));
        chest.setGlowing(true);
        chest.setGlowColorOverride(GOLD);
        chest.setViewRange(2f);
        holder.addElement(chest);
        var hit = new InteractionElement(new VirtualElement.InteractionHandler() {
            @Override public void interact(ServerPlayer p, InteractionHand hand, Vec3 at, boolean secondary) { if (p == owner) open(); }
            @Override public void attack(ServerPlayer p) { if (p == owner) open(); }
        });
        hit.setSize(1.1f, 1f);
        hit.setResponse(true);
        holder.addElement(hit);
        new ManualAttachment(holder, level, () -> pos);
        holder.startWatching(owner);
        LootSounds.drop(owner, pos, false);
    }

    boolean tick() {
        if (done) return false;
        age++;
        if (owner.hasDisconnected() || owner.level() != level) { close(!owner.hasDisconnected()); return false; }
        if (!opened && age % 6 == 0 && owner.getEyePosition().distanceToSqr(pos) > 16)
            level.sendParticles(owner, new DustParticleOptions(GOLD, 1f), true, false, pos.x, pos.y + 1.1, pos.z, 2, .35, .15, .35, 0);
        boolean near = owner.isAlive() && owner.position().distanceToSqr(pos) < 1.4 * 1.4;
        standing = near ? standing + 1 : 0;
        if (!opened && standing >= STAND_TICKS) open();
        if (opened && age - openedAt > 60) { close(false); return false; }
        holder.tick();
        return !done;
    }

    void open() {
        if (opened || done) return;
        opened = true; openedAt = age;
        LootSounds.chest(owner, pos);
        level.sendParticles(owner, new DustParticleOptions(GOLD, 1.6f), true, false, pos.x, pos.y + .8, pos.z, 30, .4, .4, .4, 0);
        Loot.grantTable(owner, table, source);
        chest.setGlowing(false);
        chest.setScale(new Vector3f(.75f));
        chest.startInterpolationIfDirty();
    }

    /** {@code deliver}: grant the unopened reward first (activity ended). */
    void close(boolean deliver) {
        if (done) return;
        if (deliver && !opened && !owner.hasDisconnected()) { opened = true; Loot.grantTable(owner, table, source); }
        done = true;
        holder.destroy();
    }
}
