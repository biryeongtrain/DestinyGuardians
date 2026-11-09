package kim.biryeong.destiny.combat;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ChunkAttachment;
import eu.pb4.polymer.virtualentity.api.elements.BlockDisplayElement;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.guardian.Element;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Brightness;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;

import java.util.ArrayList;
import java.util.List;

/** Shared Stasis crystals (W322; first used by Crystalline Corpsebloom/Rimestealer).
 * Explicit local policy (W322 mechanics.stasisCrystal): a medium crystal freezes enemies of its
 * creator on formation, lives 10 s, and any Guardian's weapon ray, blast or nearby hit shatters it,
 * dealing Kinetic damage around it as that shatterer. Visual is a virtual block display (never saved).
 */
public final class StasisCrystals {
    private static final class Crystal {
        final ServerLevel level; final Vec3 position; final long expires; final ElementHolder holder; final double bodyRadius;
        Crystal(ServerLevel level, Vec3 position, long expires, ElementHolder holder, double bodyRadius) {
            this.level = level; this.position = position; this.expires = expires; this.holder = holder; this.bodyRadius = bodyRadius;
        }
        Vec3 center() { return position.add(0, bodyRadius, 0); }
    }
    private static final List<Crystal> CRYSTALS = new ArrayList<>();
    private StasisCrystals() {}
    private static kim.biryeong.destiny.weapon.PerkBatchCProfile.CrystalRule rule() {
        return kim.biryeong.destiny.weapon.PerkBatchCProfile.crystal();
    }

    /** Grow a crystal for {@code owner}; formation freezes only that owner's enemies. */
    public static boolean spawn(ServerPlayer owner, ServerLevel level, Vec3 at) {
        return spawn(owner, level, at, 1.0);
    }
    /** Headstone size extension. Scale is local geometry only; existing formation/shatter tuning stays shared. */
    public static boolean spawn(ServerPlayer owner, ServerLevel level, Vec3 at, double scale) {
        if (!Double.isFinite(scale) || scale < .5 || scale > 2) return false;
        if (owner == null || level == null || owner.level() != level || !owner.isAlive() || at == null
                || !level.hasChunkAt(BlockPos.containing(at))) return false;
        var r = rule();
        if (CRYSTALS.stream().filter(c -> c.level == level).count() >= r.maxPerLevel()) return false;
        var holder = new ElementHolder();
        var block = new BlockDisplayElement(Blocks.BLUE_ICE.defaultBlockState());
        double bodyRadius = r.bodyRadius() * scale;
        float w = (float) (bodyRadius * 2), h = (float) (bodyRadius * 2.4);
        block.setScale(new Vector3f(w, h, w));
        block.setTranslation(new Vector3f(-w / 2, 0, -w / 2));
        block.setBrightness(new Brightness(12, 15));
        block.setViewRange(2);
        holder.addElement(block);
        ChunkAttachment.ofTicking(holder, level, at);
        CRYSTALS.add(new Crystal(level, at, level.getGameTime() + r.lifetimeTicks(), holder, bodyRadius));
        for (var e : Combat.enemiesNear(level, owner, at.add(0, bodyRadius, 0), r.formationRadius()))
            StasisStatus.freeze(owner, e, r.freezeTicks());
        level.playSound(null, BlockPos.containing(at), SoundEvents.GLASS_PLACE, SoundSource.PLAYERS, .9f, .6f);
        return true;
    }
    /** Closest distance from point to segment. Pure helper. */
    public static double segmentDistance(Vec3 from, Vec3 to, Vec3 point) {
        Vec3 d = to.subtract(from);
        double len = d.lengthSqr();
        double t = len < 1e-9 ? 0 : Math.clamp(point.subtract(from).dot(d) / len, 0, 1);
        return from.add(d.scale(t)).distanceTo(point);
    }
    /** Weapon ray crossing a crystal body. @return number of crystals shattered by {@code by}. */
    public static int shatterAlong(ServerPlayer by, Vec3 from, Vec3 to) {
        if (by == null || CRYSTALS.isEmpty()) return 0;
        return shatter(by, c -> segmentDistance(from, to, c.center()) <= c.bodyRadius);
    }
    /** Blast or contact near a crystal. @return number of crystals shattered by {@code by}. */
    public static int shatterNear(ServerPlayer by, Vec3 center, double radius) {
        if (by == null || CRYSTALS.isEmpty() || center == null) return 0;
        return shatter(by, c -> c.center().distanceTo(center) <= radius + c.bodyRadius);
    }
    private static int shatter(ServerPlayer by, java.util.function.Predicate<Crystal> hit) {
        var level = by.level();
        var r = rule();
        var hits = new ArrayList<Crystal>();
        for (var it = CRYSTALS.iterator(); it.hasNext();) {
            var c = it.next();
            if (c.level != level || c.expires <= level.getGameTime() || !hit.test(c)) continue;
            it.remove(); hits.add(c);
        }
        for (var c : hits) {
            c.holder.destroy();
            Vec3 center = c.center();
            Fx.burst(level, center, Element.KINETIC, 24, .6);
            level.playSound(null, BlockPos.containing(center), SoundEvents.GLASS_BREAK, SoundSource.PLAYERS, 1f, .7f);
            for (var e : Combat.enemiesNear(level, by, center, r.shatterRadius()))
                Combat.damage(level, by, e, (float) r.shatterDamage(), Element.KINETIC);
        }
        return hits.size();
    }
    public static int count(ServerLevel level) { return (int) CRYSTALS.stream().filter(c -> c.level == level).count(); }
    public static void tick(MinecraftServer server) {
        for (var it = CRYSTALS.iterator(); it.hasNext();) {
            var c = it.next();
            if (c.level.getServer() != server || c.expires > c.level.getGameTime()) continue;
            c.holder.destroy(); it.remove();
        }
    }
    public static void clear() { CRYSTALS.forEach(c -> c.holder.destroy()); CRYSTALS.clear(); }
}
