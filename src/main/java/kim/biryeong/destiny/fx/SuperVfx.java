package kim.biryeong.destiny.fx;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ChunkAttachment;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.guardian.Element;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Brightness;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;

/** Ultimate cosmetics only. BetterModel owns bursts; one Polymer display stretches each thin beam. */
public final class SuperVfx {
    private static final int MAX_BEAMS_PER_OWNER = 4;
    private static final int MAX_BEAMS_TOTAL = 24;
    private static final double MAX_LENGTH = 96;
    private static final List<Beam> BEAMS = new ArrayList<>();

    private static final class Beam {
        final ServerPlayer owner;
        final ServerLevel level;
        final Vec3 start;
        final LivingEntity target;
        final double radius;
        final ElementHolder holder;
        final ItemDisplayElement display;
        final Vec3 fixedEnd;
        int expires;

        Beam(ServerPlayer owner, Vec3 start, Vec3 end, LivingEntity target, double radius, int ticks) {
            this.owner = owner;
            this.level = owner.level();
            this.start = start;
            this.fixedEnd = end;
            this.target = target;
            this.radius = radius;
            this.expires = level.getServer().getTickCount() + ticks;
            holder = new ElementHolder();
            display = new AbilityDisplayElement(owner, beamItem(target == null ? "solar_trail" : "void_link"));
            display.setItemDisplayContext(ItemDisplayContext.NONE);
            display.setBillboardMode(Display.BillboardConstraints.FIXED);
            display.setBrightness(new Brightness(15, 15));
            display.setViewRange(0.75f);
            display.setTeleportDuration(1);
            holder.addElement(display);
        }

        boolean valid() {
            return validOwner(owner, level) && level.getServer().getTickCount() < expires
                    && (target == null || (target.isAlive() && !target.isRemoved() && target.level() == level
                    && target.position().distanceToSqr(start) <= radius * radius));
        }

        void update() {
            Vec3 end = target == null ? fixedEnd : target.position().add(0, target.getBbHeight() / 2, 0);
            Vec3 delta = end.subtract(start);
            // Authored model length is one block along -Z. Width must not grow with distance.
            display.setScale(new Vector3f(target == null ? 4 : 3.5f, target == null ? 4 : 3.5f,
                    (float) Math.min(MAX_LENGTH, delta.length())));
            display.setLeftRotation(SimProjectile.flightRotation(delta));
            holder.tick();
        }
    }

    private SuperVfx() { }

    public static ItemStack beamItem(String name) {
        ItemStack stack = new ItemStack(Items.STICK);
        stack.set(DataComponents.ITEM_MODEL, DestinyGuardians.id("fx/" + name + "_h15"));
        return stack;
    }

    /** H26 flourish accent at its authored contact; cosmetic only, no strike or damage. */
    public static void arcDeploy(ServerPlayer player) {
        accent(() -> SuperEnergyVfx.strike(player));
        Fx.sound(player.level(), player.position(), net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP, .9f, .8f);
    }

    public static void arcSweep(ServerPlayer player, double reach) {
        accent(() -> SuperEnergyVfx.strike(player));
        HunterVfx.play(player, player.level(), player.position().add(0, 1.1, 0), HunterVfx.Kind.ARC_SWEEP,
                reach * 0.85, 12, 0, player.getYRot() + 180);
        accent(() -> H20SuperVfx.arcStrike(player, reach));
    }

    public static void arcHit(ServerPlayer player, LivingEntity target) {
        HunterVfx.play(player, player.level(), target.position().add(0, target.getBbHeight() / 2, 0),
                HunterVfx.Kind.ARC_STRIKE, 0.65, 12);
    }

    public static void solarShot(ServerPlayer player, Vec3 from, Vec3 impact) {
        HunterVfx.play(player, player.level(), from, HunterVfx.Kind.SOLAR_MUZZLE, 0.65, 9);
        HunterVfx.play(player, player.level(), impact, HunterVfx.Kind.SOLAR_IMPACT, 1.0, 14);
        trail(player, from, impact, 10);
        accent(() -> H20SuperVfx.solarShot(player, from));
    }

    /** Call after successful super activation/limb setup. One cosmetic prop cue per owner, 420t watchdog. */
    public static boolean materialize(ServerPlayer owner, Element element) {
        boolean started = H20SuperVfx.materialize(owner, element);
        if (started) accent(() -> SuperEnergyVfx.start(owner, element));
        return started;
    }

    /** Void only: call with actual server-side draw progress each charging tick, not elapsed wall time. */
    public static void charge(ServerPlayer owner, double progress01) { H20SuperVfx.charge(owner, progress01); }

    /** Actual arrow-spawn tick, not button-press tick. Fixed origin prevents a later turn smearing the snap. */
    public static boolean voidRelease(ServerPlayer owner, Vec3 from, Vec3 direction) {
        boolean released = H20SuperVfx.release(owner, from, direction);
        if (released) accent(() -> SuperEnergyVfx.release(owner, from, direction));
        return released;
    }

    /** Observes the real projectile's position after SimProjectile.tickAll; never advances or damages it. */
    public static boolean followArrow(ServerPlayer owner, SimProjectile arrow) {
        return H20SuperVfx.followArrow(owner, arrow);
    }

    /** Normal session end only: finish the prop cue, preserving launched arrows and world-space anchors. */
    public static void dematerialize(ServerPlayer owner, Element element) {
        H20SuperVfx.dematerialize(owner, element);
        accent(() -> SuperEnergyVfx.end(owner));
    }

    /** Separate from activeCount, whose existing contract counts only real Polymer beam holders. */
    public record LifecycleSnapshot(UUID owner, String kind, String phase, int age, int expiresAt) { }
    public static List<LifecycleSnapshot> lifecycleSnapshots() { return H20SuperVfx.snapshots(); }
    public static int lifecycleCount(ServerPlayer owner) { return H20SuperVfx.count(owner); }
    /** H20 authored particle points requested this server tick, not packets/viewers or live GPU particles. */
    public static int lifecycleParticleCount(ServerPlayer owner) { return H20SuperVfx.particleCount(owner); }

    /** Separate from legacy beam/lifecycle telemetry: H25 actually allocates reusable item displays. */
    public record EnergySnapshot(UUID owner, Element element, int displays, String phase, int expiresAt, int lastTick) { }
    public static List<EnergySnapshot> energySnapshots() { return SuperEnergyVfx.snapshots(); }
    public static int energyDisplayCount(ServerPlayer owner) { return SuperEnergyVfx.displays(owner); }
    /** Must run AFTER PlayerAnimations.tick so attachments use the pose just sent this server tick. */
    public static void tickEquipmentEnergy(MinecraftServer server) { SuperEnergyVfx.tick(server); }

    /** Starts one bounded flame tracer, independent of hit/damage logic. */
    public static boolean trail(ServerPlayer owner, Vec3 from, Vec3 to, int ticks) {
        return create(owner, from, to, null, 0, Math.min(10, ticks));
    }

    public static boolean anchor(ServerPlayer owner, Vec3 position, int ticks) {
        if (owner == null || !finite(position) || ticks <= 0) return false;
        boolean started = HunterVfx.play(owner, owner.level(), position.add(0, 0.25, 0),
                HunterVfx.Kind.VOID_ANCHOR, 1.3, ticks);
        // Preserve artist/backend availability semantics; never substitute a new mesh for their model.
        if (started) H20SuperVfx.anchor(owner, position, ticks);
        return started;
    }

    /** Up to three nearest enemies are represented; gameplay still affects every enemy in the radius. */
    public static void tether(ServerPlayer owner, Vec3 anchor, double radius, List<LivingEntity> enemies) {
        enemies.stream().filter(e -> e.isAlive() && !e.isRemoved() && e.level() == owner.level()
                        && e.position().distanceToSqr(anchor) <= radius * radius)
                .sorted(Comparator.comparingDouble(e -> e.position().distanceToSqr(anchor)))
                .limit(3).forEach(target -> link(owner, anchor, target, radius, 12));
    }

    /** Reuses the same display across refreshes and follows the target on every server tick. */
    public static boolean link(ServerPlayer owner, Vec3 anchor, LivingEntity target, double radius, int ticks) {
        if (owner == null || target == null || !finite(anchor) || !Double.isFinite(radius) || radius <= 0
                || radius > MAX_LENGTH || ticks <= 0 || !validOwner(owner, owner.level())
                || target.level() != owner.level() || !target.isAlive() || target.isRemoved()
                || target.position().distanceToSqr(anchor) > radius * radius) return false;
        for (Beam beam : BEAMS) {
            if (beam.owner == owner && beam.target == target && beam.start.equals(anchor) && beam.valid()) {
                beam.expires = owner.level().getServer().getTickCount() + Math.min(12, ticks);
                return true;
            }
        }
        return create(owner, anchor, target.position().add(0, target.getBbHeight() / 2, 0), target, radius,
                Math.min(12, ticks));
    }

    private static boolean create(ServerPlayer owner, Vec3 from, Vec3 to, LivingEntity target, double radius, int ticks) {
        if (owner == null || !finite(from) || !finite(to) || ticks <= 0 || !validOwner(owner, owner.level())
                || from.distanceToSqr(to) < 1.0e-8 || from.distanceToSqr(to) > MAX_LENGTH * MAX_LENGTH) return false;
        while (activeCount(owner) >= MAX_BEAMS_PER_OWNER) {
            for (int i = 0; i < BEAMS.size(); i++) if (BEAMS.get(i).owner == owner) {
                close(BEAMS.remove(i));
                break;
            }
        }
        while (BEAMS.size() >= MAX_BEAMS_TOTAL) close(BEAMS.removeFirst());
        Beam beam = null;
        boolean retained = false;
        try {
            beam = new Beam(owner, from, to, target, radius, ticks);
            ChunkAttachment.ofTicking(beam.holder, owner.level(), from);
            beam.update();
            BEAMS.add(beam);
            retained = true;
            return true;
        } catch (RuntimeException e) {
            DestinyGuardians.LOGGER.warn("Ultimate beam failed: {}", e.toString());
            return false;
        } finally {
            if (!retained && beam != null) close(beam);
        }
    }

    public static void tick(MinecraftServer server) {
        H20SuperVfx.tick(server);
        var iterator = BEAMS.iterator();
        while (iterator.hasNext()) {
            Beam beam = iterator.next();
            if (beam.level.getServer() != server) continue;
            try {
                if (beam.valid()) {
                    beam.update();
                    continue;
                }
            } catch (RuntimeException e) {
                DestinyGuardians.LOGGER.warn("Ultimate beam update failed: {}", e.toString());
            }
            iterator.remove();
            close(beam);
        }
    }

    public static void cancelOwned(ServerPlayer owner) {
        SuperEnergyVfx.cancel(owner);
        H20SuperVfx.cancelOwned(owner);
        var iterator = BEAMS.iterator();
        while (iterator.hasNext()) {
            Beam beam = iterator.next();
            if (beam.owner == owner) {
                iterator.remove();
                close(beam);
            }
        }
    }

    /** End only this anchor's refreshed links, without removing unrelated trails or another anchor. */
    public static void cancelLinks(ServerPlayer owner, Vec3 anchor) {
        H20SuperVfx.cancelAnchor(owner, anchor);
        var iterator = BEAMS.iterator();
        while (iterator.hasNext()) {
            Beam beam = iterator.next();
            if (beam.owner == owner && beam.target != null && beam.start.equals(anchor)) {
                iterator.remove();
                close(beam);
            }
        }
    }

    public static void clearAll() {
        SuperEnergyVfx.clear();
        H20SuperVfx.clearAll();
        var beams = new ArrayList<>(BEAMS);
        BEAMS.clear();
        beams.forEach(SuperVfx::close);
    }

    public static int activeCount() { return BEAMS.size(); }
    public static int activeCount(ServerPlayer owner) {
        return (int) BEAMS.stream().filter(b -> b.owner == owner).count();
    }

    private static boolean validOwner(ServerPlayer owner, ServerLevel level) {
        return owner.level() == level && owner.isAlive() && !owner.isRemoved() && !owner.hasDisconnected();
    }

    private static boolean finite(Vec3 p) {
        return p != null && Double.isFinite(p.x) && Double.isFinite(p.y) && Double.isFinite(p.z);
    }

    private static void accent(Runnable action) {
        try { action.run(); }
        catch (RuntimeException failure) {
            DestinyGuardians.LOGGER.warn("H20 ultimate accent failed: {}", failure.toString());
        }
    }

    private static void close(Beam beam) {
        try { beam.holder.destroy(); }
        catch (RuntimeException e) { DestinyGuardians.LOGGER.warn("Ultimate beam cleanup failed: {}", e.toString()); }
    }
}
