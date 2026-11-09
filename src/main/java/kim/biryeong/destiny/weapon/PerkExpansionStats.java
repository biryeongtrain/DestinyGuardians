package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.combat.Keyword;
import kim.biryeong.destiny.combat.Statuses;
import kim.biryeong.destiny.crucible.CrucibleRuntime;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.GuardianData;
import kim.biryeong.destiny.guardian.GuardianRuntime;
import kim.biryeong.destiny.guardian.Guardians;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.item.ItemStack;

import java.util.*;

/** W327 six base traits. The central runtime owns scheduling and source attribution.
 * Numeric/HUD reads do not bind sessions, sample proximity, or refresh timers.
 * Uncertain DDC cone/aim-assist quantities are intentionally not simulated. */
public final class PerkExpansionStats {
    public static final String KEEP_AWAY = "keep_away", LONE_WOLF = "lone_wolf",
            ENLIGHTENED_ACTION = "enlightened_action", EDDY_CURRENT = "eddy_current",
            PERFECT_FLOAT = "perfect_float", OFFHAND_STRIKE = "offhand_strike";
    public static final List<String> IDS = List.of(KEEP_AWAY, LONE_WOLF, ENLIGHTENED_ACTION,
            EDDY_CURRENT, PERFECT_FLOAT, OFFHAND_STRIKE);
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();

    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final GuardianData data;
        final GuardianRuntime runtime;
        final GuardianClass guardianClass;
        final IdentityHashMap<ItemStack, Slot> slots = new IdentityHashMap<>();
        final Set<LivingEntity> corpses = Collections.newSetFromMap(new WeakHashMap<>());
        ItemStack held;
        long observed = -1;
        Session(ServerPlayer p) {
            owner = p; level = p.level(); data = p.getAttachedOrElse(Guardians.DATA, null);
            runtime = Guardians.runtimeIfPresent(p).orElse(null); guardianClass = data.guardianClass();
        }
    }
    private static final class Slot {
        final ItemStack stack;
        final WeaponCatalog.Entry entry;
        final Map<String, WeaponPerks.Roll> selection;
        final PerkExpansionStatsCycle cycle = new PerkExpansionStatsCycle();
        long stowGeneration;
        Slot(ItemStack stack, WeaponCatalog.Entry entry, Map<String, WeaponPerks.Roll> selection) {
            this.stack = stack; this.entry = entry; this.selection = selection;
        }
        boolean has(String id) { return selection.containsKey(id); }
    }
    /** Per-paid-emission receipt; mutable acceptance flag is solely duplicate-hit suppression. */
    public static final class Token {
        public static final Token NONE = new Token(null, null);
        private final Session session;
        private final Slot slot;
        private final long stowGeneration;
        private boolean hit;
        private Token(Session session, Slot slot) {
            this.session = session; this.slot = slot;
            stowGeneration = slot == null ? -1 : slot.stowGeneration;
        }
    }
    /** remainingTicks=-1 denotes a current proximity effect; positive values are actual timer remainder. */
    public record Buff(String id, int stacks, int remainingTicks) {}
    private PerkExpansionStats() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean eligible(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        var runtime = Guardians.runtimeIfPresent(p).orElse(null);
        return data != null && data.guardianClass() != null && data.guardianClass() != GuardianClass.NONE
                && runtime != null && runtime.superSession == null;
    }
    private static boolean valid(ServerPlayer p, Session s) {
        if (!eligible(p) || s == null || s.owner != p || s.level != p.level()) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        return data == s.data && data.guardianClass() == s.guardianClass
                && Guardians.runtimeIfPresent(p).orElse(null) == s.runtime && now(p) >= s.observed;
    }
    private static List<ItemStack> equipped(ServerPlayer p) {
        return PerkBatchA.equipped(p);
    }
    private static Map<String, WeaponPerks.Roll> selection(ItemStack stack) {
        var map = new HashMap<String, WeaponPerks.Roll>();
        for (String id : IDS) WeaponPerks.selected(stack, id).ifPresent(r -> map.put(id, r));
        return Map.copyOf(map);
    }
    private static boolean valid(ServerPlayer p, Session s, Slot slot) {
        return valid(p, s) && slot != null && s.slots.get(slot.stack) == slot && slot.stack.getCount() == 1
                && equipped(p).stream().anyMatch(stack -> stack == slot.stack)
                && WeaponItems.entry(slot.stack).filter(slot.entry::equals).isPresent()
                && slot.selection.equals(selection(slot.stack));
    }
    private static boolean nearbyEnemy(ServerPlayer p) {
        return !p.level().getEntitiesOfClass(LivingEntity.class, p.getBoundingBox().inflate(15),
                e -> e.distanceToSqr(p) <= 225 && !e.isRemoved() && Combat.isEnemy(p, e)).isEmpty();
    }
    private static boolean nearbyAlly(ServerPlayer p) {
        for (var other : p.level().players())
            if (other != p && other.isAlive() && !other.isRemoved() && !other.isSpectator() && !other.hasDisconnected()
                    && CrucibleRuntime.friendly(p, other) && other.distanceToSqr(p) <= 225) return true;
        return false;
    }
    /** Tick and accepted aim/reload boundary. Sampling is event-owned, never a numeric getter. */
    public static void update(ServerPlayer p) {
        if (!eligible(p)) { cleanup(p); return; }
        var s = SESSIONS.get(p.getUUID());
        if (!valid(p, s)) { s = new Session(p); SESSIONS.put(p.getUUID(), s); }
        var equipped = equipped(p);
        s.slots.keySet().removeIf(stack -> equipped.stream().noneMatch(e -> e == stack));
        for (var stack : equipped) {
            var entry = WeaponItems.entry(stack).orElse(null);
            var selected = selection(stack);
            var slot = s.slots.get(stack);
            if (entry == null || selected.isEmpty()) { s.slots.remove(stack); continue; }
            if (slot == null || !slot.entry.equals(entry) || !slot.selection.equals(selected))
                s.slots.put(stack, new Slot(stack, entry, selected));
        }
        long tick = now(p);
        var held = p.getMainHandItem();
        if (s.held != held) {
            var outgoing = s.slots.get(s.held);
            if (outgoing != null) { outgoing.stowGeneration++; outgoing.cycle.stowed(tick); }
            s.held = held;
        }
        if (s.slots.isEmpty()) { SESSIONS.remove(p.getUUID(), s); return; }
        boolean enemy = s.slots.values().stream().anyMatch(v -> v.has(KEEP_AWAY)) && nearbyEnemy(p);
        boolean ally = s.slots.values().stream().anyMatch(v -> v.has(LONE_WOLF)) && nearbyAlly(p);
        boolean amplified = Statuses.has(p, Keyword.AMPLIFIED);
        for (var slot : s.slots.values()) slot.cycle.sample(tick,
                held == slot.stack && WeaponLoadout.canUse(p), p.isSprinting(), amplified, enemy, ally);
        s.observed = tick;
    }
    private static Slot owned(ServerPlayer p, ItemStack stack) {
        var s = p == null ? null : SESSIONS.get(p.getUUID());
        var slot = s == null ? null : s.slots.get(stack);
        return valid(p, s, slot) ? slot : null;
    }
    private static Slot held(ServerPlayer p) {
        if (!eligible(p) || !WeaponLoadout.canUse(p) || AbilityService.inSuper(p)) return null;
        return owned(p, p.getMainHandItem());
    }
    public static Token capture(ServerPlayer p) {
        update(p);
        var slot = held(p);
        return slot == null ? Token.NONE : new Token(SESSIONS.get(p.getUUID()), slot);
    }
    private static boolean valid(ServerPlayer p, Token token) {
        return token != null && token != Token.NONE && token.session == SESSIONS.get(p.getUUID())
                && valid(p, token.session, token.slot);
    }
    /** Post-damage policy also admits a just-killed enemy, whose alive flag is now false. */
    private static boolean combatTarget(ServerPlayer p, LivingEntity target) {
        if (target == null || target == p || target.level() != p.level()) return false;
        if (target instanceof ServerPlayer player) return CrucibleRuntime.enemies(p, player);
        return target instanceof Mob && !p.isAlliedTo(target)
                && !(target instanceof TamableAnimal tame && tame.isTame());
    }
    /** Only positive, direct damage from the paid source. Splash must use Token.NONE.
     * One emission can prime Enlightened Action once, independent of pellets/multipart contacts. */
    public static void confirmed(ServerPlayer p, Token token, LivingEntity damageOwner, float actualLoss, boolean killed) {
        if (p == null || !Float.isFinite(actualLoss) || actualLoss <= 0 || !valid(p, token)
                || !combatTarget(p, damageOwner)) return;
        var slot = token.slot;
        long tick = now(p);
        if (!token.hit) {
            token.hit = true;
            if (slot.has(ENLIGHTENED_ACTION) && !slot.entry.family().equals("bow"))
                slot.cycle.hit(tick, slot.entry.family().equals("hand_cannon") ? 3 : 1);
        }
        if (killed && (!damageOwner.isAlive() || damageOwner.isDeadOrDying())
                && token.session.corpses.add(damageOwner) && slot.has(OFFHAND_STRIKE)
                && token.stowGeneration == slot.stowGeneration && p.getMainHandItem() == slot.stack)
            slot.cycle.kill(tick);
    }
    /** Call from the actual-loss damage observer alongside WeaponFrenzy.dealt, once per transaction. */
    public static void dealt(ServerPlayer p, LivingEntity target, DamageSource source, float actualLoss) {
        if (!eligible(p) || source == null || source.getEntity() != p || !Float.isFinite(actualLoss)
                || actualLoss <= 0 || !combatTarget(p, target)) return;
        damageEvent(p);
    }
    /** Entity-attributed enemy damage; self/environment/friendly damage cannot prime Perfect Float. */
    public static void received(ServerPlayer p, DamageSource source, float actualLoss) {
        if (!eligible(p) || source == null || !Float.isFinite(actualLoss) || actualLoss <= 0
                || !(source.getEntity() instanceof LivingEntity attacker) || !combatTarget(p, attacker)) return;
        damageEvent(p);
    }
    private static void damageEvent(ServerPlayer p) {
        update(p);
        var s = SESSIONS.get(p.getUUID());
        if (s != null) for (var slot : s.slots.values())
            if (slot.has(PERFECT_FLOAT)) slot.cycle.damage(now(p));
    }
    private static boolean hip(ServerPlayer p) { return !WeaponAiming.aimInput(p) && WeaponAiming.progress(p) <= 0; }
    private static boolean offhand(ServerPlayer p, Slot slot) {
        return slot != null && slot.has(OFFHAND_STRIKE) && hip(p) && slot.cycle.offhandRemaining(now(p)) > 0;
    }
    public static int rangeBonus(ServerPlayer p) {
        var s = held(p); return s != null && s.has(KEEP_AWAY) && s.cycle.keepAway(now(p)) ? 10 : 0;
    }
    public static int stabilityBonus(ServerPlayer p) { return offhand(p, held(p)) ? 30 : 0; }
    public static float falloffScalar(ServerPlayer p) { return offhand(p, held(p)) ? 1.45f : 1f; }
    public static int airborneBonus(ServerPlayer p) {
        var s = held(p); if (s == null) return 0;
        return (s.has(LONE_WOLF) ? s.cycle.alone(now(p)) ? 30 : 15 : 0)
                + (s.has(PERFECT_FLOAT) && s.cycle.floatRemaining(now(p)) > 0 ? 30 : 0);
    }
    public static float flinchScalar(ServerPlayer p) {
        var s = held(p); return s != null && s.has(PERFECT_FLOAT) && s.cycle.floatRemaining(now(p)) > 0 ? .65f : 1f;
    }
    private static int enlightened(Slot s, long tick) { return s.has(ENLIGHTENED_ACTION) ? s.cycle.enlightenedBonus(tick) : 0; }
    private static double handlingScalar(Slot s, long tick) { return s.has(EDDY_CURRENT) && s.cycle.eddyRemaining(tick) > 0 ? .95 : 1; }
    public static int handlingTicks(ServerPlayer p, ItemStack stack, boolean ready, int base) {
        var s = owned(p, stack); if (s == null) return base;
        return WeaponStatCurves.handlingTicks(s.entry.id(), ready, base, enlightened(s, now(p)), handlingScalar(s, now(p)));
    }
    public static int adsTicks(ServerPlayer p, WeaponCatalog.Entry entry, int base, boolean entering) {
        var s = held(p); if (s == null || !s.entry.equals(entry) || !entering) return base;
        double scalar = s.has(LONE_WOLF) ? s.cycle.alone(now(p)) ? .8 : .9 : 1;
        return WeaponStatCurves.adsTicks(entry.id(), base, enlightened(s, now(p)), scalar);
    }
    public static WeaponReloadPolicy.Plan plan(ServerPlayer p, WeaponCatalog.Entry entry, WeaponReloadPolicy.Plan base) {
        var s = held(p); if (s == null || !s.entry.equals(entry)) return base;
        long tick = now(p);
        int bonus = enlightened(s, tick) + (s.has(KEEP_AWAY) && s.cycle.keepAway(tick) ? 30 : 0)
                + (s.has(EDDY_CURRENT) ? s.cycle.eddyReload(tick) : 0);
        double scalar = handlingScalar(s, tick);
        return new WeaponReloadPolicy.Plan(WeaponStatCurves.reloadTicks(entry.id(), base.firstTicks(), bonus, scalar),
                WeaponStatCurves.reloadTicks(entry.id(), base.intervalTicks(), bonus, scalar), base.roundsPerInsert());
    }
    public static List<Buff> buffs(ServerPlayer p) {
        var s = held(p); if (s == null) return List.of();
        long tick = now(p); var out = new ArrayList<Buff>();
        if (s.has(KEEP_AWAY) && s.cycle.keepAway(tick)) out.add(new Buff(KEEP_AWAY, 1, -1));
        if (s.has(LONE_WOLF) && s.cycle.alone(tick)) out.add(new Buff(LONE_WOLF, 1, -1));
        if (s.has(ENLIGHTENED_ACTION) && s.cycle.enlightenedRemaining(tick) > 0)
            out.add(new Buff(ENLIGHTENED_ACTION, s.cycle.enlightenedStacks(tick), s.cycle.enlightenedRemaining(tick)));
        if (s.has(EDDY_CURRENT) && s.cycle.eddyRemaining(tick) > 0)
            out.add(new Buff(EDDY_CURRENT, 1, s.cycle.eddyRemaining(tick)));
        if (s.has(PERFECT_FLOAT) && s.cycle.floatRemaining(tick) > 0)
            out.add(new Buff(PERFECT_FLOAT, 1, s.cycle.floatRemaining(tick)));
        if (offhand(p, s)) out.add(new Buff(OFFHAND_STRIKE, 1, s.cycle.offhandRemaining(tick)));
        return List.copyOf(out);
    }
    /** Call AFTER computing outgoing stow duration; observe same-tick away/back transitions. */
    public static void stowing(ServerPlayer p, ItemStack stack) {
        var s = owned(p, stack);
        if (s != null) { s.stowGeneration++; s.cycle.stowed(now(p)); }
    }
    public static void edited(ItemStack stack) { for (var s : SESSIONS.values()) s.slots.remove(stack); }
    public static void changed(ServerPlayer p, ItemStack stack) {
        var s = p == null ? null : SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) s.slots.remove(stack);
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) SESSIONS.remove(p.getUUID(), s);
    }
    public static void clear() { SESSIONS.clear(); }
}
