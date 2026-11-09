package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.combat.Keyword;
import kim.biryeong.destiny.combat.Statuses;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.guardian.Guardians;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import java.util.function.Supplier;

/** W323 batch D facade: Turnabout, Counterattack, Flash Counter, Tilting at Windmills, Valiant Charge,
 * Duelist's Trance, Cold Steel, Unstoppable Force, Master of Arms. Main server thread only.
 * Per-owner state; buffs are bound to the exact source item identity (see {@link PerkBatchDCycle}). */
public final class PerkBatchD {
    private static final Identifier TILT_ID = DestinyGuardians.id("tilting_at_windmills_w323");
    private static final Identifier TURNABOUT_ID = DestinyGuardians.id("turnabout_overshield_w323");
    private static final Map<UUID, Owner> OWNERS = new HashMap<>();
    private static PerkBatchDCycle.Config config;
    private static Boolean pendingHeavy;
    private static final class Owner {
        final ServerPlayer player;
        final PerkBatchDCycle cycle = new PerkBatchDCycle(config());
        long updated = Long.MIN_VALUE, overshieldUntil = -1;
        ItemStack pendingBlast;
        float overshieldOwned, overshieldObserved;
        Owner(ServerPlayer p) { player = p; }
    }
    /** Paid emission snapshot of the source item's batch D traits. */
    public record Token(ServerPlayer owner, ItemStack source, boolean sword, boolean glaive, boolean heavy,
                        boolean turnabout, boolean coldSteel, boolean duelist, boolean masterOfArms) {
        public static final Token NONE = new Token(null, null, false, false, false, false, false, false, false);
    }
    /** Target state observed immediately before a weapon damage transaction. */
    public record Pre(float absorption, float health, boolean inSuper) {
        static final Pre NONE = new Pre(0, 0, false);
    }
    private PerkBatchD() {}

    private static PerkBatchDCycle.Config config() {
        if (config == null) config = PerkBatchDCycle.Config.profile();
        return config;
    }
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    static boolean has(ItemStack stack, String id) {
        return stack != null && !stack.isEmpty() && PerkBatchDProfile.owns(id) && WeaponPerks.selected(stack, id).isPresent();
    }
    private static boolean family(ItemStack stack, String family) {
        return WeaponItems.entry(stack).filter(e -> e.family().equals(family)).isPresent();
    }
    private static boolean valid(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected();
    }
    private static Owner owner(ServerPlayer p, boolean create) {
        var o = OWNERS.get(p.getUUID());
        if (o != null && o.player != p) { release(o); OWNERS.remove(p.getUUID()); o = null; }
        if (o == null && create) { o = new Owner(p); OWNERS.put(p.getUUID(), o); }
        return o;
    }
    private static boolean guardPerks(ItemStack stack) {
        return has(stack, PerkBatchDProfile.COUNTERATTACK) || has(stack, PerkBatchDProfile.FLASH_COUNTER)
                || has(stack, PerkBatchDProfile.VALIANT_CHARGE) || has(stack, PerkBatchDProfile.DUELISTS_TRANCE)
                || has(stack, PerkBatchDProfile.TILTING) || has(stack, PerkBatchDProfile.UNSTOPPABLE_FORCE);
    }

    /** Once per player tick (idempotent within a tick): guard edges, deferred blasts, speed, overshield, stow. */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        if (!valid(p)) { cleanup(p); return; }
        var held = p.getMainHandItem();
        var o = owner(p, guardPerks(held));
        if (o == null) return;
        long now = now(p);
        if (o.updated == now) return;
        o.updated = now;
        boolean guarding = family(held, "sword") ? WeaponRuntime.swordStatus(p).map(WeaponRuntime.SwordStatus::guarding).orElse(false)
                : family(held, "glaive") && WeaponRuntime.glaiveStatus(p).map(WeaponRuntime.GlaiveStatus::guarding).orElse(false);
        o.cycle.guard(now, held, guarding);
        var blast = o.pendingBlast; o.pendingBlast = null;
        if (blast != null && blast == held && has(held, PerkBatchDProfile.FLASH_COUNTER)) flashCounter(p, held);
        tilt(p, o.cycle.tilting(now, held) && has(held, PerkBatchDProfile.TILTING));
        overshield(p, o, now);
        if (o.cycle.idle(now) && o.overshieldUntil < 0 && !guardPerks(held)) { release(o); OWNERS.remove(p.getUUID(), o); }
    }

    /** Called by the existing frontal-PvE guard rule with the vanilla amount and the guard-reduced amount. */
    public static float guarded(ServerPlayer p, DamageSource source, float amount, float reduced) {
        if (!valid(p)) return reduced;
        var held = p.getMainHandItem();
        if (!guardPerks(held)) return reduced;
        var o = owner(p, true);
        boolean sword = family(held, "sword");
        var guard = new PerkBatchDCycle.Guard(sword && has(held, PerkBatchDProfile.COUNTERATTACK),
                sword && has(held, PerkBatchDProfile.FLASH_COUNTER), sword && has(held, PerkBatchDProfile.VALIANT_CHARGE),
                !sword && has(held, PerkBatchDProfile.TILTING), !sword && has(held, PerkBatchDProfile.UNSTOPPABLE_FORCE));
        // Deferred one tick: never re-enter the attacker's own hurt/attack transaction.
        if (o.cycle.blocked(now(p), held, guard)) o.pendingBlast = held;
        if (sword && o.cycle.trance(held)) return reduced * (1f - statScale());
        return reduced;
    }
    private static float statScale() {
        return (float) PerkBatchDProfile.value(PerkBatchDProfile.DUELISTS_TRANCE, "localStatScale");
    }
    /** After the sword guard/regeneration step: Duelist's Trance guard endurance and charge rate. */
    public static void swordTick(ServerPlayer p, ItemStack stack, SwordCycle sword) {
        if (p == null || sword == null) return;
        var o = owner(p, false);
        if (o == null || !o.cycle.trance(stack) || !has(stack, PerkBatchDProfile.DUELISTS_TRANCE)) return;
        float scale = statScale();
        if (sword.guarding()) sword.restore(Math.round(SwordCycle.GUARD_DRAIN_PER_TICK * scale));
        else if (sword.rechargeRemaining(now(p)) == 0) sword.restore(Math.round(SwordCycle.REGEN_PER_TICK * scale));
    }
    /** Scopes a sword contact capture so Cold Steel knows light (x40) vs heavy (x60). */
    public static <T> T sword(boolean heavy, Supplier<T> capture) {
        var previous = pendingHeavy;
        pendingHeavy = heavy;
        try { return capture.get(); } finally { pendingHeavy = previous; }
    }
    /** Light sword lunge multiplier; consumes Valiant Charge. */
    public static double lungeScale(ServerPlayer p) {
        if (p == null) return 1;
        var held = p.getMainHandItem();
        var o = owner(p, false);
        if (o == null || !has(held, PerkBatchDProfile.VALIANT_CHARGE)) return 1;
        return o.cycle.consumeValiant(now(p), held) ? PerkBatchDProfile.value(PerkBatchDProfile.VALIANT_CHARGE, "lungeScale") : 1;
    }

    public static Token capture(ServerPlayer p) {
        if (!valid(p)) return Token.NONE;
        var stack = p.getMainHandItem();
        var entry = WeaponItems.entry(stack).orElse(null);
        if (entry == null) return Token.NONE;
        boolean sword = entry.family().equals("sword"), glaive = entry.family().equals("glaive");
        var token = new Token(p, stack, sword, glaive, sword && Boolean.TRUE.equals(pendingHeavy),
                has(stack, PerkBatchDProfile.TURNABOUT), sword && has(stack, PerkBatchDProfile.COLD_STEEL),
                sword && has(stack, PerkBatchDProfile.DUELISTS_TRANCE), has(stack, PerkBatchDProfile.MASTER_OF_ARMS));
        return token.sword || token.glaive || token.turnabout || token.masterOfArms ? token : Token.NONE;
    }
    /** Pure read of the active damage buffs for this paid source. */
    public static float multiplier(ServerPlayer owner, Token token) {
        if (owner == null || token == null || token.owner != owner) return 1f;
        var o = owner(owner, false);
        if (o == null) return 1f;
        long now = now(owner);
        float m = 1f;
        if (token.sword && has(token.source, PerkBatchDProfile.COUNTERATTACK)) m *= o.cycle.counterMultiplier(now, token.source);
        if (token.glaive && has(token.source, PerkBatchDProfile.UNSTOPPABLE_FORCE)) m *= o.cycle.unstoppableMultiplier(now, token.source);
        if (token.masterOfArms) m *= o.cycle.moaMultiplier(now);
        return m;
    }
    public static Pre before(LivingEntity contact) {
        if (contact == null) return Pre.NONE;
        return new Pre(contact.getAbsorptionAmount(), contact.getHealth(),
                contact instanceof ServerPlayer target && Guardians.runtimeIfPresent(target).map(r -> r.superSession != null).orElse(false));
    }
    /** After positive actual loss in the shared weapon apply path. Token may be NONE (perk/ability-free weapon damage). */
    public static void confirmed(ServerPlayer owner, Token token, LivingEntity contact, Pre pre, float actual, boolean killed) {
        if (!valid(owner) || contact == null || !(actual > 0)) return;
        if (killed) owner(owner, true).cycle.weaponKill(now(owner)); // Master of Arms: any weapon final blow.
        if (token == null || token.owner != owner) return;
        if (token.coldSteel && contact.isAlive()) slow(owner, contact, token.heavy);
        if (token.duelist && killed) owner(owner, true).cycle.swordKill(token.source);
        if (token.turnabout && pre != null && shieldBroken(contact, pre)) grantOvershield(owner);
    }
    static boolean shieldBroken(LivingEntity contact, Pre pre) {
        if (contact instanceof Player) {
            float shieldFloor = contact.getMaxHealth() * 100f / 230f;
            return pre.inSuper && pre.health + pre.absorption > shieldFloor + 1e-4f
                    && contact.getHealth() + contact.getAbsorptionAmount() <= shieldFloor;
        }
        return pre.absorption > 0 && contact.getAbsorptionAmount() <= 0;
    }
    private static void slow(ServerPlayer owner, LivingEntity target, boolean heavy) {
        int ticks = PerkBatchDProfile.ticks(PerkBatchDProfile.COLD_STEEL, target instanceof Player ? "pvpSlowTicks" : "pveSlowTicks");
        int amp = PerkBatchDProfile.ticks(PerkBatchDProfile.COLD_STEEL, heavy ? "heavyAmplifier" : "lightAmplifier");
        if (target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, ticks, amp)))
            PerkExpansionSupport.debuffApplied(owner, target);
    }

    private static void flashCounter(ServerPlayer p, ItemStack stack) {
        var entry = WeaponItems.entry(stack).orElse(null);
        if (entry == null || !(p.level() instanceof ServerLevel level)) return;
        String id = PerkBatchDProfile.FLASH_COUNTER;
        double radius = PerkBatchDProfile.value(id, "radius");
        double cone = Math.cos(Math.toRadians(PerkBatchDProfile.value(id, "localConeDegrees")));
        float near = (float) PerkBatchDProfile.value(id, "pointBlankFactor"), far = (float) PerkBatchDProfile.value(id, "maxFactor");
        int disorient = PerkBatchDProfile.ticks(id, "disorientTicks");
        boolean coldSteel = has(stack, PerkBatchDProfile.COLD_STEEL);
        float base = WeaponProfile.forEntry(entry).damage();
        Vec3 center = p.getEyePosition(), look = p.getLookAngle();
        int hits = 0;
        for (var target : Combat.enemiesNear(level, p, center, radius)) {
            if (hits >= SwordArc.MAX_HITS) break;
            if (p.isAlliedTo(target)) continue;
            Vec3 point = target.position().add(0, target.getBbHeight() * .5, 0), delta = point.subtract(center);
            double distance = delta.length();
            if (distance > 1e-6 && look.dot(delta.scale(1 / distance)) < cone) continue;
            if (!level.hasChunkAt(BlockPos.containing(point))) continue;
            var wall = level.clip(new ClipContext(center, point, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
            if (wall.getType() != HitResult.Type.MISS && center.distanceToSqr(wall.getLocation()) + 1e-3 < center.distanceToSqr(point)) continue;
            hits++;
            float factor = near + (far - near) * (float) Math.min(1, distance / radius);
            WeaponRuntime.perkDamage(p, target, base * factor, point, entry);
            if (!target.isAlive()) continue;
            Statuses.apply(p, target, Keyword.BLINDED, disorient);
            if (coldSteel) slow(p, target, true);
        }
        Fx.ring(p, level, p.position().add(0, .5, 0), Math.min(radius, 3), WeaponCharacteristics.of(entry).damage().color(), 24);
    }

    private static void tilt(ServerPlayer p, boolean active) {
        var speed = p.getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed == null) return;
        if (!active) { speed.removeModifier(TILT_ID); return; }
        if (!speed.hasModifier(TILT_ID)) speed.addTransientModifier(new AttributeModifier(TILT_ID,
                PerkBatchDProfile.value(PerkBatchDProfile.TILTING, "speedBonus"), AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
    }

    private static void grantOvershield(ServerPlayer p) {
        var o = owner(p, true);
        var attr = p.getAttribute(Attributes.MAX_ABSORPTION);
        if (attr == null) return;
        reconcile(p, o);
        float cap = p.getMaxHealth() * (float) PerkBatchDProfile.value(PerkBatchDProfile.TURNABOUT, "overshieldHp") / 230f;
        attr.removeModifier(TURNABOUT_ID);
        attr.addTransientModifier(new AttributeModifier(TURNABOUT_ID, cap, AttributeModifier.Operation.ADD_VALUE));
        float before = p.getAbsorptionAmount();
        p.setAbsorptionAmount(before + Math.max(0, cap - o.overshieldOwned));
        o.overshieldOwned += Math.max(0, p.getAbsorptionAmount() - before);
        o.overshieldObserved = p.getAbsorptionAmount();
        o.overshieldUntil = now(p) + PerkBatchDProfile.ticks(PerkBatchDProfile.TURNABOUT, "durationTicks");
    }
    private static void reconcile(ServerPlayer p, Owner o) {
        if (o.overshieldUntil < 0) return;
        o.overshieldOwned = Math.max(0, o.overshieldOwned - Math.max(0, o.overshieldObserved - p.getAbsorptionAmount()));
        o.overshieldObserved = p.getAbsorptionAmount();
    }
    private static void overshield(ServerPlayer p, Owner o, long now) {
        if (o.overshieldUntil < 0) return;
        reconcile(p, o);
        if (now >= o.overshieldUntil || o.overshieldOwned <= 0) removeOvershield(o);
    }
    private static void removeOvershield(Owner o) {
        var p = o.player;
        if (o.overshieldUntil < 0) return;
        reconcile(p, o);
        p.setAbsorptionAmount(Math.max(0, p.getAbsorptionAmount() - o.overshieldOwned));
        var attr = p.getAttribute(Attributes.MAX_ABSORPTION);
        if (attr != null) attr.removeModifier(TURNABOUT_ID);
        o.overshieldOwned = o.overshieldObserved = 0; o.overshieldUntil = -1;
    }
    private static void release(Owner o) {
        removeOvershield(o);
        var speed = o.player.getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) speed.removeModifier(TILT_ID);
    }

    /** Remaining Master of Arms / overshield diagnostics. */
    public static float masterOfArms(ServerPlayer p) {
        var o = p == null ? null : owner(p, false);
        return o == null ? 1f : o.cycle.moaMultiplier(now(p));
    }
    public static void edited(ItemStack stack) {
        if (stack == null) return;
        for (var o : OWNERS.values()) { o.cycle.changed(stack); if (o.pendingBlast == stack) o.pendingBlast = null; }
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        var o = owner(p, false);
        if (o != null) { o.cycle.changed(stack); if (o.pendingBlast == stack) o.pendingBlast = null; }
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        var o = OWNERS.get(p.getUUID());
        if (o == null) return;
        release(o);
        OWNERS.remove(p.getUUID(), o);
    }
    public static void clear() {
        for (var o : OWNERS.values()) release(o);
        OWNERS.clear();
        pendingHeavy = null;
    }
}
