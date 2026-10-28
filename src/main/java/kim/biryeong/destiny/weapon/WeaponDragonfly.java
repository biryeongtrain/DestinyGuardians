package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.fx.HunterVfx;
import kim.biryeong.destiny.fx.WeaponDamageNumbers;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.sound.DestinySounds;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.Collections;
import java.util.Comparator;
import java.util.IdentityHashMap;
import java.util.Set;
import net.minecraft.world.phys.AABB;

/** Precision-final-blow secondary damage, never a new precision hit or a recursive weapon shot.
 * Tokens are local to an emission, not global player state or saved item data.
 */
public final class WeaponDragonfly {
    public static final class Token {
        public static final Token NONE = new Token(null, null, null, null);
        private final ServerPlayer owner;
        private final ServerLevel level;
        private final ItemStack stack;
        private final WeaponCatalog.Entry entry;
        private final WeaponFeedingFrenzy.Token feedingFrenzy;
        private final Set<LivingEntity> detonated = Collections.newSetFromMap(new IdentityHashMap<>());
        private Token(ServerPlayer owner, ServerLevel level, ItemStack stack, WeaponCatalog.Entry entry) {
            this.owner = owner; this.level = level; this.stack = stack; this.entry = entry;
            this.feedingFrenzy = owner == null ? WeaponFeedingFrenzy.Token.NONE : WeaponFeedingFrenzy.capture(owner);
        }
    }
    private WeaponDragonfly() {}

    private static boolean ownerValid(ServerPlayer owner) {
        return owner.isAlive() && !owner.isRemoved() && !owner.isSpectator() && !owner.hasDisconnected()
                && !AbilityService.inSuper(owner);
    }
    public static Token capture(ServerPlayer owner) {
        if (!ownerValid(owner) || !WeaponLoadout.canUse(owner)
                || WeaponPerks.selected(owner.getMainHandItem(), DragonflyProfile.ID).isEmpty()) return Token.NONE;
        var entry = WeaponItems.entry(owner.getMainHandItem()).orElseThrow();
        return new Token(owner, owner.level(), owner.getMainHandItem(), entry);
    }
    private static boolean valid(ServerPlayer owner, Token token) {
        if (token.owner != owner || token.level != owner.level() || !ownerValid(owner)
                || WeaponItems.entry(token.stack).filter(token.entry::equals).isEmpty()
                || WeaponPerks.selected(token.stack, DragonflyProfile.ID).isEmpty()) return false;
        for (int i = 0; i < owner.getInventory().getContainerSize(); i++)
            if (owner.getInventory().getItem(i) == token.stack) return true;
        return false;
    }
    /** Production caller must first observe positive HP/absorption loss and the actual final blow.
     * Stowing a launched shot retains its original trait/element; dropping or editing it invalidates it.
     */
    public static void killed(ServerPlayer owner, Token token, LivingEntity corpse, boolean precision) {
        if (!precision || token == null || !valid(owner, token) || corpse.level() != token.level
                || corpse.isAlive() || !token.detonated.add(corpse)) return;
        var level = token.level;
        var center = corpse.getBoundingBox().getCenter();
        if (!level.hasChunkAt(BlockPos.containing(center))) return;
        var damageType = WeaponCharacteristics.of(token.entry).damage();
        var element = switch (damageType) {
            case ARC -> Element.ARC;
            case SOLAR -> Element.SOLAR;
            case VOID -> Element.VOID;
            default -> throw new IllegalStateException("Unsupported Dragonfly element: " + damageType);
        };
        double radius = DragonflyProfile.radius();
        // Use the SAME geometric center for admission and attenuation. Opening shulkers
        // can move their bounding-box center away from position + height/2.
        var targets = level.getEntitiesOfClass(LivingEntity.class, AABB.ofSize(center, radius * 2, radius * 2, radius * 2),
                        target -> Combat.isEnemy(owner, target)
                                && target.getBoundingBox().getCenter().distanceToSqr(center) <= radius * radius)
                .stream().sorted(Comparator.comparingDouble(target -> target.getBoundingBox().getCenter().distanceToSqr(center)))
                .toList();
        for (var target : targets) {
            if (target == corpse || owner.isAlliedTo(target)
                    || target instanceof TamableAnimal tame && tame.isTame()) continue;
            Vec3 point = target.getBoundingBox().getCenter();
            if (!level.hasChunkAt(BlockPos.containing(point))) continue;
            var wall = level.clip(new ClipContext(center, point, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, owner));
            if (wall.getType() != HitResult.Type.MISS
                    && center.distanceToSqr(wall.getLocation()) + 1e-6 < center.distanceToSqr(point)) continue;
            float requested = damageAt(center.distanceTo(point));
            float before = target.getHealth() + target.getAbsorptionAmount();
            // Do NOT route this back through WeaponRuntime.apply: no recursive explosions,
            // no precision refunds/Outlaw, and no direct-hit damage multiplier applied twice.
            boolean killed=Combat.damage(level, owner, target, requested, element, AmmoGeneration.weapon(token.entry));
            float actual = before - target.getHealth() - target.getAbsorptionAmount();
            if (killed && Float.isFinite(actual) && actual > 0)
                WeaponFeedingFrenzy.killed(owner,token.feedingFrenzy);
            if (Float.isFinite(actual) && actual > 0) {
                kim.biryeong.destiny.hud.WeaponHitHud.confirm(owner, actual, killed);
                WeaponDamageNumbers.confirm(owner, level, point, actual, false);
            }
        }
        Fx.burst(level, center, element, 24, .35);
        Fx.ring(level, center, DragonflyProfile.radius() * .55, damageType.color(), 24);
        HunterVfx.Kind kind = switch (element) {
            case ARC -> HunterVfx.Kind.ARC_FLASH;
            case SOLAR -> HunterVfx.Kind.SOLAR_BURST;
            case VOID -> HunterVfx.Kind.VOID_SMOKE;
            default -> throw new IllegalStateException();
        };
        HunterVfx.play(owner, level, center, kind, 1.2, 12);
        // Explicit provisional reuse from the supplied audio archive, not an exact Dragonfly recording.
        DestinySounds.at(level, center, "hunter." + element.getSerializedName() + ".grenade.impact", .65f);
    }
    /** Local Minecraft HP curve, not original Destiny damage units. Outside the radius is zero. */
    public static float damageAt(double distance) {
        if (!Double.isFinite(distance) || distance < 0 || distance > DragonflyProfile.radius()) return 0;
        return DragonflyProfile.damage() * (float)Math.max(DragonflyProfile.falloffFloor(),
                1 - distance / DragonflyProfile.radius());
    }
}
