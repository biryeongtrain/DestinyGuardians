package kim.biryeong.destiny.loot;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ManualAttachment;
import eu.pb4.polymer.virtualentity.api.elements.InteractionElement;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import eu.pb4.polymer.virtualentity.api.elements.TextDisplayElement;
import eu.pb4.polymer.virtualentity.api.elements.VirtualElement;
import kim.biryeong.destiny.economy.Economy;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.FontDescription;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.Style;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Brightness;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Display;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.util.ArrayList;
import java.util.List;

/**
 * A personal activity reward chest (Destiny chests are per player: everyone sees only their own, even at the same
 * spot). Shared by strikes, dungeons and raids; the activity only chooses the place, the table and the Glimmer.
 *
 * <p>Timeline: transmats in ({@link #ARRIVE}), idles with a prompt, opens on use or after standing at it for
 * {@link #STAND_TICKS}: the lid springs open and the rewards burst out. Each engram/weapon arcs to the ground and
 * becomes a normal personal {@link WorldDrop}; the Glimmer shards scatter, then home in on the Guardian and are
 * credited once all arrive. The open chest lingers and transmats out. Model: Khvostov golden chest
 * (scripts/loot/build_chest_models.py), body and hinged lid as two displays.
 */
public final class LootChest {
    static final int STAND_TICKS = 30, ARRIVE = 10, BURST_AT = 4, FLIGHT = 16, LINGER = 20 * 12, VANISH = 9;
    static final int GOLD = 0xE3C46B, GLIMMER = 0x7FE3FF;
    /** Lid hinge relative to the chest base, chest-local (front = +z). */
    static final float HINGE_Y = .557f, HINGE_Z = -.39f, OPEN = (float) Math.toRadians(104), OVERSHOOT = (float) Math.toRadians(116);
    /** Item displays turn FIXED models half a turn about Y; undone so model south is the chest's front. */
    private static final float FLIP = (float) Math.PI;
    private static final FontDescription.Resource FONT = new FontDescription.Resource(Identifier.fromNamespaceAndPath("destiny", "econ_text"));

    final ServerPlayer owner;
    final ServerLevel level;
    final String table, source;
    final Vec3 pos;
    final float yaw;
    final long glimmer;
    private final Quaternionf facing;
    private final ElementHolder holder = new ElementHolder();
    private final ItemDisplayElement body, lid;
    private final TextDisplayElement prompt;
    private final List<Flight> flights = new ArrayList<>();
    private final List<Shard> shards = new ArrayList<>();
    private int age, standing, openedAt = -1, vanishAt = -1, shardsHome;
    private boolean promptShown, closing;
    private final ChestRewards rewards;
    boolean opened, done;

    /** {@code yaw}: the direction the chest's front faces (Minecraft yaw). */
    LootChest(ServerPlayer owner, Vec3 at, float yaw, String table, long glimmer, String source) {
        this.owner = owner; this.level = owner.level(); this.pos = at; this.yaw = yaw; this.table = table;
        this.glimmer = Math.max(0, glimmer); this.source = source;
        this.rewards = new ChestRewards(LootTables.table(table)
                .map(t -> LootRoller.roll(t, owner.getRandom())).orElse(List.of()));
        this.facing = new Quaternionf().rotateY((float) Math.toRadians(-yaw));
        body = part("reward_chest_body");
        lid = part("reward_chest_lid");
        prompt = new TextDisplayElement(Component.empty());
        prompt.setBillboardMode(Display.BillboardConstraints.CENTER);
        prompt.setBackground(0xA0101418);
        prompt.setBrightness(new Brightness(15, 15));
        prompt.setTranslation(new Vector3f(0, 1.45f, 0));
        prompt.setScale(new Vector3f(0));
        prompt.setInterpolationDuration(3);
        prompt.setLineWidth(240);
        prompt.setViewRange(1f);
        holder.addElement(body); holder.addElement(lid); holder.addElement(prompt);
        var hit = new InteractionElement(new VirtualElement.InteractionHandler() {
            @Override public void interact(ServerPlayer p, InteractionHand hand, Vec3 at, boolean secondary) { if (p == owner) open(); }
            @Override public void attack(ServerPlayer p) { if (p == owner) open(); }
        });
        hit.setSize(1.2f, .85f);
        hit.setResponse(true);
        holder.addElement(hit);
        pose(.02f, 0, 0);
        new ManualAttachment(holder, level, () -> pos);
        holder.startWatching(owner);
        LootSounds.chestArrive(owner, pos);
    }

    private ItemDisplayElement part(String model) {
        var stack = new ItemStack(Items.PAPER);
        stack.set(DataComponents.ITEM_MODEL, Identifier.parse("destiny:loot/" + model));
        var e = new ItemDisplayElement(stack);
        e.setItemDisplayContext(ItemDisplayContext.FIXED);
        e.setBrightness(new Brightness(13, 15));
        e.setViewRange(2f);
        return e;
    }

    /** Body and lid at {@code scale}, lid opened by {@code angle} radians, interpolated over {@code ticks}. */
    private void pose(float scale, float angle, int ticks) {
        body.setInterpolationDuration(ticks); lid.setInterpolationDuration(ticks);
        body.setScale(new Vector3f(scale));
        body.setTranslation(new Vector3f(0, .5f * scale, 0));
        body.setLeftRotation(new Quaternionf(facing).rotateY(FLIP));
        var hinge = new Vector3f(0, HINGE_Y, HINGE_Z).rotate(facing).mul(scale);
        lid.setScale(new Vector3f(scale));
        lid.setTranslation(hinge);
        lid.setLeftRotation(new Quaternionf(facing).rotateX(-angle).rotateY(FLIP));
        body.startInterpolation(); lid.startInterpolation();
    }

    boolean tick() {
        if (done) return false;
        age++;
        if (closing) { if (age % 20 == 0) close(true); return !done; }
        if (owner.hasDisconnected() || owner.isRemoved() || owner.level() != level || age > 20 * 120) { close(true); return !done; }
        if (age <= ARRIVE) arriving();
        else if (!opened) idle();
        else opening();
        holder.tick();
        if (vanishAt >= 0 && age - vanishAt >= VANISH) { finish(); return false; }
        return !done;
    }

    private void arriving() {
        if (age == 2) pose(1.06f, 0, ARRIVE - 3);
        if (age == ARRIVE - 1) pose(1f, 0, 3);
        double h = age / (double) ARRIVE * 1.1;
        for (int i = 0; i < 6; i++) {
            double a = age * .9 + i * Math.PI / 3, r = .75 - age * .03;
            level.sendParticles(owner, ParticleTypes.END_ROD, true, false, pos.x + Math.cos(a) * r, pos.y + h, pos.z + Math.sin(a) * r, 1, 0, 0, 0, 0);
        }
        if (age == ARRIVE) level.sendParticles(owner, new DustParticleOptions(GOLD, 1.3f), true, false, pos.x, pos.y + .4, pos.z, 24, .5, .3, .5, 0);
    }

    private void idle() {
        double d = owner.position().distanceTo(pos);
        boolean near = owner.isAlive() && d < 1.6;
        standing = near ? standing + 1 : Math.max(0, standing - 2);
        if (standing >= STAND_TICKS) { open(); return; }
        if (age % 5 == 0 && d > 5) {   // a soft gold beam so the chest is found from across the arena
            for (int i = 0; i < 3; i++)
                level.sendParticles(owner, new DustParticleOptions(GOLD, .9f), true, false, pos.x, pos.y + 1.1 + ((age / 5 + i * 3) % 9) * .45, pos.z, 1, .05, .05, .05, 0);
        }
        boolean show = d < 6;
        if (show != promptShown || (show && age % 2 == 0)) {
            promptShown = show;
            prompt.setScale(new Vector3f(show ? .9f : 0));
            if (show) prompt.setText(promptText());
            prompt.startInterpolationIfDirty();
        }
    }

    private Component promptText() {
        MutableComponent out = Component.literal("보상 상자\n").withStyle(text(GOLD));
        if (standing > 0) {
            int filled = Math.min(10, standing * 10 / STAND_TICKS);
            out.append(Component.literal("■".repeat(filled)).withStyle(text(0xF2F4F6)));
            out.append(Component.literal("■".repeat(10 - filled)).withStyle(text(0x4A5058)));
        } else out.append(Component.literal("[우클릭] 열기").withStyle(text(0xF2F4F6)));
        return out;
    }
    private static Style text(int color) { return Style.EMPTY.withFont(FONT).withColor(color).withItalic(false); }

    void open() {
        if (opened || done || closing || age < ARRIVE || !owner.isAlive() || owner.isSpectator()
                || owner.hasDisconnected() || owner.level() != level || owner.position().distanceToSqr(pos) > 16) return;
        opened = true; openedAt = age;
        prompt.setScale(new Vector3f(0)); prompt.startInterpolation();
        pose(1f, OVERSHOOT, 4);
        LootSounds.chest(owner, pos);
    }

    private void opening() {
        int t = age - openedAt;
        if (t == 4) pose(1f, OPEN, 5);
        if (t == BURST_AT) burst();
        for (var it = flights.iterator(); it.hasNext(); ) if (it.next().tick(t)) it.remove();
        for (var it = shards.iterator(); it.hasNext(); ) if (it.next().tick()) it.remove();
        if (t > BURST_AT && shardsHome > 0 && shards.isEmpty()) creditGlimmer();
        if (t > 6 && t < 60 && t % 4 == 0)   // Glimmer shimmer rising out of the open chest
            level.sendParticles(owner, new DustParticleOptions(GLIMMER, .7f), true, false, pos.x, pos.y + .65, pos.z, 2, .3, .08, .3, 0);
        if (vanishAt < 0 && t > LINGER && flights.isEmpty() && shards.isEmpty()) {
            vanishAt = age;
            pose(.02f, OPEN, VANISH);
            LootSounds.chestLeave(owner, pos);
            level.sendParticles(owner, ParticleTypes.END_ROD, true, false, pos.x, pos.y + .5, pos.z, 18, .45, .35, .45, .02);
        }
    }

    private void burst() {
        var rewards = this.rewards.all();
        int best = GOLD, bestTier = -1; boolean exotic = false;
        for (int i = 0; i < rewards.size(); i++) {
            var r = rewards.get(i);
            if (Loot.exotic(r)) exotic = true;
            if (Loot.rarity(r).ordinal() > bestTier) { bestTier = Loot.rarity(r).ordinal(); best = Loot.color(r); }
            double spread = rewards.size() == 1 ? 0 : (i / (rewards.size() - 1.0) - .5) * Math.toRadians(130);
            flights.add(new Flight(i, r, landing(spread, 2.2 + (i % 2) * .4)));
        }
        int pieces = glimmer <= 0 ? 0 : (int) Math.clamp(glimmer / 4, 6, 16);
        for (int i = 0; i < pieces; i++) shards.add(new Shard(i));
        shardsHome = pieces;
        if (pieces == 0) creditGlimmer();
        level.sendParticles(owner, new DustParticleOptions(lighten(best), 1.2f), true, false, pos.x, pos.y + .8, pos.z, 22, .35, .35, .35, 0);
        level.sendParticles(owner, ParticleTypes.END_ROD, true, false, pos.x, pos.y + .7, pos.z, 16, .15, .25, .15, .12);
        LootSounds.burst(owner, pos, exotic);
    }

    /** Ground point {@code radius} in front of the chest, {@code spread} radians off its facing; walls pull it in. */
    private Vec3 landing(double spread, double radius) {
        for (double r = radius; r > .8; r -= .3) {
            var dir = new Vector3f((float) Math.sin(spread), 0, (float) Math.cos(spread)).rotate(facing);
            var at = pos.add(dir.x * r, 0, dir.z * r);
            var floor = Loot.floor(level, at, 3);
            if (floor != null && Math.abs(floor.y - pos.y) < 2.1) return floor;
        }
        return pos;
    }

    /** Rarity colours are dark (legendary purple, rare navy); particles read as debris unless lifted toward white. */
    static int lighten(int rgb) {
        int r = rgb >> 16 & 255, g = rgb >> 8 & 255, b = rgb & 255;
        return (r + (255 - r) * 11 / 20) << 16 | (g + (255 - g) * 11 / 20) << 8 | (b + (255 - b) * 11 / 20);
    }

    private void creditGlimmer() {
        if (shardsHome < 0) return;
        shardsHome = -1;
        if (glimmer > 0) Economy.reward(owner, glimmer, source);
    }

    /** Retire presentation and mail every reward not yet transferred, including pre-burst rewards. */
    void close(boolean deliver) {
        if (done) return;
        closing = true;
        holder.destroy();
        flights.clear(); shards.clear();
        if (!deliver) { finish(); return; }
        creditGlimmer();
        boolean delivered = rewards.drain(r -> Economy.postmaster(owner.getUUID(), owner.getGameProfile().name(),
                Loot.mailStack(r), source + " · 미회수 보상"));
        Economy.save(false);
        // A full mailbox must not silently consume the entitlement. Retry while the server is running.
        if (delivered) finish();
    }

    private void finish() { done = true; holder.destroy(); }

    /** An engram or weapon arcing out of the chest to its landing point, where it becomes a {@link WorldDrop}. */
    private final class Flight {
        final LootRoller.Reward reward;
        final int rewardIndex;
        final Vec3 to;
        final ItemDisplayElement item;
        final int start = BURST_AT;
        final float lift = (float) (.75 + Math.random() * .25);

        Flight(int rewardIndex, LootRoller.Reward reward, Vec3 to) {
            this.rewardIndex = rewardIndex;
            this.reward = reward; this.to = to;
            item = new ItemDisplayElement(WorldDrop.displayStack(reward));
            item.setItemDisplayContext(ItemDisplayContext.FIXED);
            item.setBrightness(new Brightness(15, 15));
            item.setGlowing(true);
            item.setGlowColorOverride(Loot.color(reward));
            item.setViewRange(2f);
            place(0);
            holder.addElement(item);
        }

        private void place(double u) {
            WorldDrop.pose(item, reward, 0, 0);
            var end = to.subtract(pos);
            var base = item.getTranslation();
            double arc = 4 * (1.2 + lift) * u * (1 - u);
            var p = new Vector3f((float) (end.x * u), (float) (.35 + (end.y + base.y() - .35) * u + arc), (float) (end.z * u));
            item.setTranslation(p);
            item.setScale(new Vector3f(item.getScale()).mul((float) (.35 + .65 * Math.min(1, u * 2.5))));
            item.setLeftRotation(new Quaternionf().rotateY((float) ((1 - u) * Math.PI * 3)).mul(item.getLeftRotation()));
            item.setInterpolationDuration(2);
            item.startInterpolation();
        }

        /** @return true once landed. */
        boolean tick(int t) {
            int f = t - start;
            if (f < FLIGHT && f % 2 == 0) place(f / (double) FLIGHT);
            if (f % 3 == 0 && f < FLIGHT) {
                var e = item.getTranslation();
                level.sendParticles(owner, new DustParticleOptions(lighten(Loot.color(reward)), .7f), true, false, pos.x + e.x(), pos.y + e.y(), pos.z + e.z(), 1, 0, 0, 0, 0);
            }
            if (f < FLIGHT) return false;
            land();
            return true;
        }

        void land() {
            holder.removeElement(item);
            rewards.transfer(rewardIndex, r -> { Loot.dropAt(owner, to, r); return true; });
        }
    }

    /** One Glimmer shard: bursts out, bounces, hovers, then streaks to the Guardian. */
    private final class Shard {
        final ItemDisplayElement item;
        final int index, homeAt;
        final Vector3f p = new Vector3f(), v = new Vector3f(), spin = new Vector3f();
        final Quaternionf rot = new Quaternionf();
        int life, homing = -1;

        Shard(int index) {
            this.index = index;
            var rng = owner.getRandom();
            double a = rng.nextDouble() * Math.PI * 2, out = .07 + rng.nextDouble() * .09;
            var dir = new Vector3f((float) Math.sin(a), 0, (float) Math.cos(a) * .6f + .4f).normalize();  // biased to the front
            dir.rotate(facing);
            p.set(dir.x * .2f, .45f, dir.z * .2f);
            v.set(dir.x * (float) out, (float) (.26 + rng.nextDouble() * .12), dir.z * (float) out);
            spin.set((float) rng.nextGaussian() * .3f, (float) rng.nextGaussian() * .3f, (float) rng.nextGaussian() * .3f);
            homeAt = 22 + index * 2 + rng.nextInt(4);
            var stack = new ItemStack(Items.PAPER);
            stack.set(DataComponents.ITEM_MODEL, Identifier.parse("destiny:loot/glimmer"));
            item = new ItemDisplayElement(stack);
            item.setItemDisplayContext(ItemDisplayContext.FIXED);
            item.setBrightness(new Brightness(15, 15));
            item.setScale(new Vector3f(.3f + rng.nextFloat() * .08f));
            item.setViewRange(1.5f);
            item.setInterpolationDuration(2);
            apply();
            holder.addElement(item);
        }

        private void apply() {
            item.setTranslation(new Vector3f(p));
            item.setLeftRotation(new Quaternionf(rot));
            item.startInterpolation();
        }

        /** @return true once collected. */
        boolean tick() {
            life++;
            rot.rotateXYZ(spin.x, spin.y, spin.z);
            if (life < homeAt) {
                v.y -= .045f; p.add(v);
                if (p.y < .12f) { p.y = .12f; v.y = Math.abs(v.y) * .35f; v.x *= .55f; v.z *= .55f; }
                if (life > 12) { v.x *= .8f; v.z *= .8f; }
            } else {
                if (homing < 0) homing = 0;
                homing++;
                var target = owner.position().add(0, 1.05, 0).subtract(pos);
                var to = new Vector3f((float) target.x, (float) target.y, (float) target.z).sub(p);
                float k = Math.min(1f, .16f + homing * .07f);
                if (to.length() < .5f || homing > 18) {
                    holder.removeElement(item);
                    LootSounds.glimmer(owner, 1.1f + .045f * index);
                    return true;
                }
                p.add(to.mul(k));
            }
            apply();
            return false;
        }
    }
}
