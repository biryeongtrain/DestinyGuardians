package kim.biryeong.destiny.ability.warlock;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.*;

import java.util.*;

/** Server-only classic Warlock abilities. No Hunter animation or physics ownership. */
public final class WarlockAbilities {
    public static final Identifier JUMP = id("jump"), CLASS_ABILITY = id("class_ability");
    public static final Identifier ARC_GRENADE = id("arc_grenade"), SOLAR_GRENADE = id("solar_grenade"), VOID_GRENADE = id("void_grenade");
    public static final Identifier ARC_MELEE = id("arc_melee"), SOLAR_MELEE = id("solar_melee"), VOID_MELEE = id("void_melee");
    public static final Identifier ARC_SUPER = id("arc_super"), SOLAR_SUPER = id("solar_super"), VOID_SUPER = id("void_super");
    private static final Map<ServerPlayer, Lease> OWNERS = new IdentityHashMap<>();
    private WarlockAbilities() {}
    private static Identifier id(String path) { return DestinyGuardians.id("warlock/" + path); }

    public static void register() {
        AbilityRegistry.register(new WarlockJump(JUMP));
        AbilityRegistry.register(new WarlockClassAbility(CLASS_ABILITY));
        for (Element e : List.of(Element.ARC, Element.SOLAR, Element.VOID)) {
            AbilityRegistry.register(new WarlockGrenade(grenade(e), e));
            AbilityRegistry.register(new WarlockMelee(melee(e), e));
            AbilityRegistry.register(new WarlockSuper(superId(e), e));
        }
        WarlockExpandedSupers.register();
    }
    private static Identifier grenade(Element e) { return e == Element.SOLAR ? SOLAR_GRENADE : e == Element.VOID ? VOID_GRENADE : ARC_GRENADE; }
    private static Identifier melee(Element e) { return e == Element.SOLAR ? SOLAR_MELEE : e == Element.VOID ? VOID_MELEE : ARC_MELEE; }
    private static Identifier superId(Element e) { return e == Element.SOLAR ? SOLAR_SUPER : e == Element.VOID ? VOID_SUPER : ARC_SUPER; }
    public static Loadout preset(Element e) {
        return new Loadout(Map.of(AbilitySlot.JUMP, JUMP, AbilitySlot.CLASS_ABILITY, CLASS_ABILITY,
                AbilitySlot.GRENADE, grenade(e), AbilitySlot.MELEE, melee(e), AbilitySlot.SUPER, superId(e)));
    }
    /** Called once by the shared lifecycle, separate from SuperSession.tick(). */
    public static void tick(MinecraftServer server) {
        for (Lease lease : List.copyOf(OWNERS.values())) {
            if (!lease.valid()) cleanup(lease.owner);
            else lease.emissions.removeIf(SimProjectile::isDone);
        }
        WarlockJump.tick();
        WarlockClassAbility.tick();
        WarlockGrenade.tick();
        WarlockMelee.tick();
        WarlockSuper.tickEffects();
    }
    public static void cleanup(ServerPlayer player) {
        Lease lease = OWNERS.remove(player);
        if (lease != null) lease.cancelled = true;
        WarlockJump.cleanup(player);
        WarlockClassAbility.cleanup(player);
        WarlockGrenade.cleanup(player);
        WarlockMelee.cleanup(player);
        WarlockSuper.cleanup(player);
        if (lease != null) {
            lease.emissions.forEach(SimProjectile::cancel);
            lease.emissions.clear();
        }
    }
    public static void clearAll() {
        for (ServerPlayer player : List.copyOf(OWNERS.keySet())) cleanup(player);
    }
    static Lease acquire(ServerPlayer p, Ability ability) {
        if (!p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()
                || Guardians.data(p).guardianClass() != GuardianClass.WARLOCK
                || !Objects.equals(Guardians.data(p).loadout().map(l -> l.get(ability.slot())).orElse(null), ability.id())) return null;
        Lease old = OWNERS.get(p);
        if (old != null && !old.valid()) cleanup(p);
        return OWNERS.computeIfAbsent(p, Lease::new);
    }
    static final class Lease {
        final ServerPlayer owner;
        final ServerLevel level;
        final GuardianRuntime runtime;
        final GuardianData data;
        final Loadout loadout;
        final Set<SimProjectile> emissions = Collections.newSetFromMap(new IdentityHashMap<>());
        boolean cancelled;
        Lease(ServerPlayer p) {
            owner = p; level = p.level(); runtime = Guardians.runtime(p); data = Guardians.data(p);
            loadout = data.loadout().orElseThrow();
        }
        boolean valid() {
            return !cancelled && owner.isAlive() && !owner.isRemoved() && !owner.isSpectator()
                    && !owner.hasDisconnected() && owner.level() == level
                    && owner.getAttachedOrElse(Guardians.DATA, null) == data
                    && Guardians.runtimeIfPresent(owner).orElse(null) == runtime
                    && data.guardianClass() == GuardianClass.WARLOCK && data.loadout().filter(loadout::equals).isPresent();
        }
    }
    static SimProjectile own(Lease lease, SimProjectile projectile) {
        lease.emissions.add(projectile);
        return projectile;
    }
    static double value(Ability ability, String name, double fallback, double min, double max) {
        double value = ability.param(name, fallback);
        return Double.isFinite(value) ? Math.clamp(value, min, max) : fallback;
    }
    static int ticks(Ability ability, String name, int fallback, int min, int max) {
        return (int) value(ability, name, fallback, min, max);
    }
    static boolean enemy(ServerPlayer p, LivingEntity target) {
        return target.level() == p.level() && Combat.isEnemy(p, target) && !p.isAlliedTo(target)
                && !(target instanceof TamableAnimal tame && tame.isTame());
    }
    static Vec3 center(LivingEntity target) { return target.position().add(0, target.getBbHeight() * .5, 0); }
    static boolean visible(Lease lease, Vec3 from, Vec3 to) {
        return lease.valid() && lease.level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, lease.owner)).getType() == HitResult.Type.MISS;
    }
    static List<LivingEntity> targets(Lease lease, Vec3 origin, double radius) {
        if (!lease.valid()) return List.of();
        return Combat.enemiesNear(lease.level, lease.owner, origin, radius).stream()
                .filter(e -> enemy(lease.owner, e) && visible(lease, origin, center(e))).limit(32).toList();
    }
    /** Offset to the incoming side of a wall, so splash never originates inside/behind it. */
    static Vec3 impactPoint(HitResult hit) {
        if (hit instanceof BlockHitResult block) {
            var d = block.getDirection();
            Vec3 n = new Vec3(d.getStepX(), d.getStepY(), d.getStepZ());
            return hit.getLocation().add(n.scale(.06));
        }
        return hit.getLocation();
    }
    static LivingEntity aimed(Lease lease, double range) {
        Vec3 eye = lease.owner.getEyePosition(), look = lease.owner.getLookAngle();
        return targets(lease, eye, range).stream()
                .filter(e -> {
                    Vec3 delta = center(e).subtract(eye);
                    double along = delta.dot(look);
                    return along > 0 && along <= range && delta.subtract(look.scale(along)).lengthSqr() <= .85 * .85;
                }).min(Comparator.comparingDouble(e -> center(e).distanceToSqr(eye))).orElse(null);
    }
}
