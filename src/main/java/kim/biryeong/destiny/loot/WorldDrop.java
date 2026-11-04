package kim.biryeong.destiny.loot;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ManualAttachment;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import kim.biryeong.destiny.weapon.WeaponModels;
import kim.biryeong.destiny.weapon.WeaponItems;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Brightness;
import net.minecraft.world.entity.Display;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * A personal loot drop in the world (Destiny drops are per player): only the owner sees it and walking over it
 * collects it. Engrams float as their glyph; weapons spin as their model. Expires after {@link #LIFE} ticks.
 */
final class WorldDrop {
    static final int LIFE = 20 * 120;
    static final double PICKUP = 1.6;

    final ServerPlayer owner;
    final ServerLevel level;
    final LootRoller.Reward reward;
    final Vec3 pos;
    final int color;
    private final ElementHolder holder = new ElementHolder();
    private final ItemDisplayElement item;
    private int age;
    boolean done;

    WorldDrop(ServerPlayer owner, Vec3 at, LootRoller.Reward reward) {
        this.owner = owner; this.level = owner.level(); this.reward = reward; this.pos = at;
        this.color = Loot.color(reward);
        ItemStack stack;
        if (reward.engram() != null) {
            stack = new ItemStack(Items.PAPER);
            stack.set(DataComponents.ITEM_MODEL, Identifier.parse("destiny:gui/hud/" + Loot.engramIcon(reward.engram())));
        } else stack = WeaponItems.entry(reward.weapon()).map(WeaponModels::create).orElse(ItemStack.EMPTY);
        item = new ItemDisplayElement(stack);
        item.setItemDisplayContext(ItemDisplayContext.FIXED);
        item.setBrightness(new Brightness(15, 15));
        item.setInterpolationDuration(2);
        item.setViewRange(2f);
        item.setGlowing(true);
        item.setGlowColorOverride(color);
        if (reward.engram() != null) item.setBillboardMode(Display.BillboardConstraints.CENTER);
        holder.addElement(item);
        place();
        new ManualAttachment(holder, level, () -> pos);
        holder.startWatching(owner);
        LootSounds.drop(owner, at, Loot.exotic(reward));
    }

    private void place() {
        float bob = (float) Math.sin(age / 12.0) * .08f;
        if (reward.engram() != null) {
            item.setScale(new Vector3f(.55f));
            item.setTranslation(new Vector3f(0, .9f + bob, 0));
            item.setLeftRotation(new Quaternionf().rotateZ(age * .03f));
        } else {
            item.setScale(new Vector3f(.8f));
            item.setTranslation(new Vector3f(0, .7f + bob, 0));
            item.setLeftRotation(new Quaternionf().rotateY(age * .05f));
        }
        item.startInterpolationIfDirty();
    }

    /** @return false when finished (collected, expired or owner gone). */
    boolean tick() {
        if (done) return false;
        age++;
        if (owner.hasDisconnected() || owner.level() != level || age > LIFE) { close(); return false; }
        if ((age & 1) == 0) place();
        if (age % 5 == 0 && owner.getEyePosition().distanceToSqr(pos) > 16) {
            level.sendParticles(owner, new DustParticleOptions(color, .8f), true, false, pos.x, pos.y + .2 + (age / 5 % 8) * .35, pos.z, 1, .04, .08, .04, 0);
        }
        holder.tick();
        if (owner.isAlive() && owner.position().distanceToSqr(pos.x, owner.getY(), pos.z) < PICKUP * PICKUP && Math.abs(owner.getY() - pos.y) < 2.5) {
            if (Loot.collect(owner, reward, "획득")) { close(); return false; }
        }
        return true;
    }

    void close() { if (!done) { done = true; holder.destroy(); } }
}
