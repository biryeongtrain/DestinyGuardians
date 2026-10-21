package kim.biryeong.destiny.fx;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ChunkAttachment;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import kim.biryeong.destiny.combat.Combat;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Brightness;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;
import org.joml.Quaternionf;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/**
 * 엔티티 등록 없이 서버에서 계산하는 투사체. 보이는 모습은 Polymer 가상 item_display.
 * 수류탄·칼 투척·연막탄에 쓴다.
 */
public final class SimProjectile {
    private static final List<SimProjectile> ACTIVE = new ArrayList<>();

    private final ServerLevel level;
    private final ServerPlayer owner;
    private final Vec3 origin;
    private Vec3 pos;
    private Vec3 velocity;
    private final double gravity;
    private int life;
    private final int trailColor;
    private final Consumer<HitResult> onImpact;
    private final ElementHolder holder;
    private final ItemDisplayElement display;
    private final boolean directional;
    private boolean done;

    private SimProjectile(ServerPlayer owner, Vec3 pos, Vec3 velocity, double gravity, int life, ItemStack visual,
                          float scale, int trailColor, Consumer<HitResult> onImpact) {
        this.level = owner.level();
        this.owner = owner;
        this.origin = pos;
        this.pos = pos;
        this.velocity = velocity;
        this.gravity = gravity;
        this.life = life;
        this.trailColor = trailColor;
        this.onImpact = onImpact;
        this.holder = new ElementHolder();
        this.display = new ItemDisplayElement(visual);
        // Authored 3D props follow flight, rather than turning into camera-facing sprites.
        // Legacy vanilla sprites (e.g. Shadowshot's arrow) retain their previous presentation.
        this.directional = visual.has(DataComponents.ITEM_MODEL);
        display.setItemDisplayContext(ItemDisplayContext.NONE);
        display.setBillboardMode(directional ? Display.BillboardConstraints.FIXED : Display.BillboardConstraints.CENTER);
        if (directional) display.setLeftRotation(flightRotation(velocity));
        display.setScale(new Vector3f(scale));
        display.setBrightness(new Brightness(15, 15));
        display.setTeleportDuration(1);
        holder.addElement(display);
        ChunkAttachment.ofTicking(holder, level, pos);
    }

    public static SimProjectile launch(ServerPlayer owner, Vec3 pos, Vec3 velocity, double gravity, int life,
                                       ItemStack visual, float scale, int trailColor, Consumer<HitResult> onImpact) {
        SimProjectile p = new SimProjectile(owner, pos, velocity, gravity, life, visual, scale, trailColor, onImpact);
        ACTIVE.add(p);
        return p;
    }

    public static void tickAll(MinecraftServer server) {
        if (ACTIVE.isEmpty()) {
            return;
        }
        for (SimProjectile p : List.copyOf(ACTIVE)) {
            p.tick();
        }
        ACTIVE.removeIf(p -> p.done);
    }

    public static void clearAll() {
        ACTIVE.forEach(SimProjectile::discard);
        ACTIVE.clear();
    }

    public static void discardOwned(ServerPlayer owner) {
        ACTIVE.removeIf(p -> {
            if (p.owner != owner) return false;
            p.discard();
            return true;
        });
    }

    public static int activeCount(ServerPlayer owner) {
        return (int) ACTIVE.stream().filter(p -> p.owner == owner && !p.done).count();
    }

    public boolean isDone() { return done; }

    public static int activeCount() {
        return ACTIVE.size();
    }

    private void tick() {
        if (done) {
            return;
        }
        if (!owner.isAlive() || owner.isRemoved() || owner.level() != level) {
            discard();
            return;
        }
        Vec3 next = pos.add(velocity);
        HitResult hit = level.clip(new ClipContext(pos, next, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, owner));
        Vec3 end = hit.getType() == HitResult.Type.MISS ? next : hit.getLocation();
        EntityHitResult entityHit = ProjectileUtil.getEntityHitResult(level, owner, pos, end,
                new net.minecraft.world.phys.AABB(pos, end).inflate(0.6),
                e -> e instanceof LivingEntity && Combat.isEnemy(owner, e), 0.3f);
        if (entityHit != null) {
            hit = entityHit;
            end = entityHit.getLocation();
        }
        Fx.line(level, pos, end, trailColor, 0.4, 0.8f);
        pos = end;
        display.setOffset(pos.subtract(origin));
        if (directional) display.setLeftRotation(flightRotation(velocity));
        holder.tick();
        if (hit.getType() != HitResult.Type.MISS) {
            finish(hit);
            return;
        }
        velocity = velocity.add(0, -gravity, 0).scale(0.99);
        if (--life <= 0) {
            finish(new BlockHitResult(pos, net.minecraft.core.Direction.UP, net.minecraft.core.BlockPos.containing(pos), false));
        }
    }

    private void finish(HitResult hit) {
        done = true;
        discard();
        onImpact.accept(hit);
    }

    private void discard() {
        done = true;
        holder.destroy();
    }

    public Vec3 position() {
        return pos;
    }

    /** Align authored -Z with flight, compensating ItemDisplayRenderer's built-in Y=PI. */
    public static Quaternionf flightRotation(Vec3 velocity) {
        if (velocity.lengthSqr() < 1.0e-10) return new Quaternionf().rotationY((float) Math.PI);
        Vec3 direction = velocity.normalize();
        return new Quaternionf().rotationTo(0, 0, -1,
                (float) direction.x, (float) direction.y, (float) direction.z).rotateY((float) Math.PI);
    }
}
