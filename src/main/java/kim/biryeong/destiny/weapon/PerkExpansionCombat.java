package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.GuardianData;
import kim.biryeong.destiny.guardian.GuardianRuntime;
import kim.biryeong.destiny.guardian.Guardians;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;

import java.util.*;

/** W327 six base traits. The runtime supplies paid emissions, actual damage and accepted ability events.
 * The only item writes here are reserve-funded Reconstruction/Rewind transactions. Server-thread only. */
public final class PerkExpansionCombat {
    public static final String REWIND = "rewind_rounds", RECONSTRUCTION = "reconstruction",
            PRECISION = "precision_instrument", WARM_UP = "successful_warm_up", DUAL_LOADER = "dual_loader",
            DESPERATE = "desperate_measures";
    public static final List<String> IDS = List.of(REWIND, RECONSTRUCTION, PRECISION, WARM_UP, DUAL_LOADER, DESPERATE);
    private static final Map<UUID, PlayerState> PLAYERS = new HashMap<>();

    private static final class PlayerState {
        final ServerPlayer owner;
        final ServerLevel level;
        final GuardianData data;
        final GuardianRuntime runtime;
        final GuardianClass guardianClass;
        final IdentityHashMap<ItemStack, Slot> slots = new IdentityHashMap<>();
        ItemStack held;
        long observed;
        PlayerState(ServerPlayer p) {
            owner = p; level = p.level(); data = p.getAttachedOrElse(Guardians.DATA, null);
            runtime = Guardians.runtimeIfPresent(p).orElse(null);
            guardianClass = data == null ? null : data.guardianClass();
            held = p.getMainHandItem(); observed = now(p);
        }
    }
    private static final class Slot {
        final ItemStack stack;
        final WeaponCatalog.Entry entry;
        final Map<String, WeaponPerks.Roll> rolls;
        final PerkExpansionCombatCycle cycle;
        final Set<LivingEntity> corpses = Collections.newSetFromMap(new WeakHashMap<>());
        Slot(ItemStack stack, WeaponCatalog.Entry entry, Map<String, WeaponPerks.Roll> rolls, long now) {
            this.stack = stack; this.entry = entry; this.rolls = rolls; cycle = new PerkExpansionCombatCycle(now);
        }
        boolean has(String id) { return rolls.containsKey(id); }
    }

    /** Immutable firing-time multipliers with an opaque once-only accounting receipt. */
    public static final class Token {
        public static final Token NONE = new Token(null, null, null, 1, 1, false);
        private final PlayerState player;
        private final Slot slot;
        private final PerkExpansionCombatCycle.Emission emission;
        private final float damage, precision;
        private final boolean direct;
        private Token(PlayerState player, Slot slot, PerkExpansionCombatCycle.Emission emission,
                      float damage, float precision, boolean direct) {
            this.player = player; this.slot = slot; this.emission = emission;
            this.damage = damage; this.precision = precision; this.direct = direct;
        }
        public float multiplier() { return damage; }
        public float precisionMultiplier() { return direct ? precision : 1; }
        public Token splash() { return slot == null || !direct ? this : new Token(player, slot, emission, damage, 1, false); }
    }

    /** Accepted grenade/melee captures every original equipped Desperate Measures source. */
    public static final class AbilityToken {
        public static final AbilityToken NONE = new AbilityToken(null, null, null, List.of());
        private final PlayerState player;
        private final AbilitySlot kind;
        private final Identifier ability;
        private final List<Slot> slots;
        private AbilityToken(PlayerState player, AbilitySlot kind, Identifier ability, List<Slot> slots) {
            this.player = player; this.kind = kind; this.ability = ability; this.slots = List.copyOf(slots);
        }
    }
    public record Buff(String id, int stacks, int remainingTicks) {}
    private PerkExpansionCombat() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && !AbilityService.inSuper(p);
    }
    private static boolean equipped(ServerPlayer p, ItemStack stack) {
        if (stack == null || stack.isEmpty() || stack.getCount() != 1) return false;
        int identities = 0, index = -1;
        for (int i = 0; i < p.getInventory().getContainerSize(); i++)
            if (p.getInventory().getItem(i) == stack) { identities++; index = i; }
        return identities == 1 && index >= 0 && index < 9 && (!WeaponLoadout.enabled(p)
                || WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == stack));
    }
    private static Map<String, WeaponPerks.Roll> selected(ItemStack stack) {
        var result = new LinkedHashMap<String, WeaponPerks.Roll>();
        for (String id : IDS) WeaponPerks.selected(stack, id).ifPresent(r -> result.put(id, r));
        return Map.copyOf(result);
    }
    private static boolean valid(ServerPlayer p, PlayerState state) {
        if (state == null || !ownerValid(p) || state.owner != p || state.level != p.level()
                || PLAYERS.get(p.getUUID()) != state || now(p) < state.observed) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        return state.data == data && state.runtime == Guardians.runtimeIfPresent(p).orElse(null)
                && state.guardianClass == (data == null ? null : data.guardianClass());
    }
    private static boolean valid(ServerPlayer p, PlayerState state, Slot slot) {
        return slot != null && valid(p, state) && state.slots.get(slot.stack) == slot && equipped(p, slot.stack)
                && WeaponItems.entry(slot.stack).filter(slot.entry::equals).isPresent()
                && selected(slot.stack).equals(slot.rolls);
    }
    private static PlayerState existing(ServerPlayer p) {
        var s = p == null ? null : PLAYERS.get(p.getUUID());
        return valid(p, s) ? s : null;
    }
    private static Slot owned(ServerPlayer p, ItemStack stack) {
        var state = existing(p);
        var slot = state == null ? null : state.slots.get(stack);
        return valid(p, state, slot) ? slot : null;
    }
    /** Explicit tick/event observation. No getter or HUD read creates slots or transfers ammunition. */
    public static void update(ServerPlayer p) { observe(p, true); }
    private static void observe(ServerPlayer p, boolean transfer) {
        if (!ownerValid(p)) { cleanup(p); return; }
        var state = PLAYERS.get(p.getUUID());
        if (!valid(p, state)) { state = new PlayerState(p); PLAYERS.put(p.getUUID(), state); }
        final var current = state;
        current.slots.values().removeIf(slot -> !valid(p, current, slot));
        for (int i = 0; i < 9; i++) {
            var stack = p.getInventory().getItem(i);
            if (!equipped(p, stack) || current.slots.containsKey(stack)) continue;
            var entry = WeaponItems.entry(stack).orElse(null);
            if (entry == null || entry.family().equals("sword")) continue;
            var rolls = selected(stack);
            if (!rolls.isEmpty()) current.slots.put(stack, new Slot(stack, entry, rolls, now(p)));
        }
        if (current.held != p.getMainHandItem()) {
            var outgoing = current.slots.get(current.held);
            if (outgoing != null) outgoing.cycle.stow();
            current.held = p.getMainHandItem();
        }
        current.observed = now(p);
        if (!transfer) return;
        for (var slot : current.slots.values()) {
            slot.cycle.expire(now(p));
            if (!slot.has(RECONSTRUCTION) && !slot.has(REWIND)) continue;
            var profile = WeaponProfile.forEntry(slot.entry);
            var effective = WeaponComponents.profile(slot.stack, profile);
            var ammo = WeaponItems.magazine(slot.stack, profile);
            boolean reloading = WeaponRuntime.reloadOwnedBy(p, slot.stack);
            int moved = 0;
            if (slot.has(RECONSTRUCTION)) {
                int target = slot.cycle.reconstruction(now(p), effective.magazine(), ammo.rounds(), reloading);
                moved += PerkExpansionCombatCycle.fund(ammo, effective.magazine(), target);
            }
            if (slot.has(REWIND) && !reloading)
                moved += transferRewind(slot.cycle, now(p), effective.magazine(), ammo, adaptiveLfr(slot.entry), WeaponRuntime.burstOwnedBy(p,slot.stack));
            if (moved > 0) WeaponItems.save(slot.stack, ammo);
        }
    }
    private static boolean adaptiveLfr(WeaponCatalog.Entry e) {
        return e.family().equals("linear_fusion_rifle") && e.frame().equals("adaptive_burst");
    }
    private static boolean charged(WeaponCatalog.Entry e) {
        return e.family().equals("bow") || e.family().equals("fusion_rifle") || e.family().equals("linear_fusion_rifle");
    }
    /** Call once per emitted bullet/bolt, after the runtime saved its ammo debit. Pellets share one token. */
    public static Token paid(ServerPlayer p, WeaponCatalog.Entry entry, int roundsBefore, boolean firstOfBurst) {
        observe(p, false);
        if (!ownerValid(p) || !WeaponLoadout.canUse(p) || roundsBefore < 1) return Token.NONE;
        var state = existing(p); var slot = owned(p, p.getMainHandItem());
        if (slot == null || !slot.entry.equals(entry)) return Token.NONE;
        long tick = now(p);
        float damage = slot.has(DESPERATE) ? (float)slot.cycle.damageMultiplier(tick) : 1;
        float precision = slot.has(PRECISION) ? (float)slot.cycle.precisionMultiplier(tick) : 1;
        boolean spent = firstOfBurst || !WeaponProfile.forEntry(entry).sharedBurstAmmo();
        var receipt = slot.cycle.paid(tick, spent, firstOfBurst, slot.has(PRECISION));
        return new Token(state, slot, receipt, damage, precision, true);
    }
    /** Runtime has already checked enemy policy and normalized the damage owner, before it died. */
    public static void confirmed(ServerPlayer p, Token token, LivingEntity target, float actual, boolean killed) {
        if (token == null || token.slot == null || target == null || target == p || !Float.isFinite(actual) || actual <= 0
                || target.level() != token.player.level || !valid(p, token.player, token.slot)
                || (token.direct && token.emission.resolved)
                || now(p) < token.emission.accepted || now(p) - token.emission.accepted > PerkExpansionCombatCycle.MAX_FLIGHT_TICKS) return;
        var slot = token.slot;
        if (token.direct) slot.cycle.hit(token.emission, now(p), adaptiveLfr(slot.entry),
                slot.entry.frame().equals("heavy_burst"), charged(slot.entry));
        if (killed && (!target.isAlive() || target.isDeadOrDying()) && slot.corpses.add(target))
            slot.cycle.weaponKill(now(p), slot.has(WARM_UP) && p.getMainHandItem() == slot.stack && WeaponLoadout.canUse(p), slot.has(DESPERATE));
    }
    /** Terminal hitscan/projectile callback, after every direct target. Splash tokens never resolve originals. */
    public static void resolved(ServerPlayer p, Token token) {
        if (token == null || !token.direct || !valid(p, token.player, token.slot)) return;
        if (token.slot.cycle.resolved(token.emission, now(p))) refillRewind(p, token.slot);
    }
    private static void refillRewind(ServerPlayer p, Slot slot) {
        if (!slot.has(REWIND) || WeaponRuntime.reloadOwnedBy(p, slot.stack)) return;
        var profile = WeaponProfile.forEntry(slot.entry);
        var effective = WeaponComponents.profile(slot.stack, profile);
        var ammo = WeaponItems.magazine(slot.stack, profile);
        if (transferRewind(slot.cycle, now(p), effective.magazine(), ammo, adaptiveLfr(slot.entry), WeaponRuntime.burstOwnedBy(p,slot.stack)) > 0) WeaponItems.save(slot.stack, ammo);
    }
    /** Shared-ammo bursts still own future uncaptured bolts. Do not close their magazine early.
     * The final bolt resolves after WeaponCycle decrements burstLeft, so it can transfer immediately.
     * The periodic update covers cancellation/timeout without introducing query-side mutation. */
    static int transferRewind(PerkExpansionCombatCycle cycle, long tick, int capacity,
                              WeaponMagazine ammo, boolean adaptiveLfr, boolean burstPending) {
        if (burstPending) return 0;
        return ammo.reloadRounds(cycle.rewind(tick,capacity,ammo.rounds(),adaptiveLfr));
    }
    /** Positive actual manual/dodge reload only; not canceled/dry reload, Reconstruction or Rewind. */
    public static void reloaded(ServerPlayer p, ItemStack stack) {
        var slot = owned(p, stack);
        if (slot != null) slot.cycle.resetMagazine();
    }
    /** Only automatic empty-mag reload should wait for in-flight Rewind accounting; manual reload stays available. */
    public static boolean awaitingRewind(ServerPlayer p, ItemStack stack) {
        var slot = owned(p, stack);
        if (slot == null || !slot.has(REWIND)) return false;
        var profile = WeaponProfile.forEntry(slot.entry);
        int capacity = WeaponComponents.profile(stack, profile).magazine();
        return WeaponItems.magazine(stack, profile).rounds() == 0 && slot.cycle.awaitingRewind(capacity);
    }
    /** Pure composition; normal magazines and unrelated weapons keep their original plan. */
    public static WeaponReloadPolicy.Plan reloadPlan(ServerPlayer p, ItemStack stack, WeaponReloadPolicy.Plan base) {
        if (!ownerValid(p) || !equipped(p, stack) || !base.incremental()
                || WeaponItems.entry(stack).filter(e -> e.family().equals("shotgun")).isEmpty()
                || WeaponPerks.selected(stack, DUAL_LOADER).isEmpty()) return base;
        return dualLoader(base);
    }
    static WeaponReloadPolicy.Plan dualLoader(WeaponReloadPolicy.Plan base) {
        return !base.incremental() ? base : new WeaponReloadPolicy.Plan(base.firstTicks(), base.intervalTicks(), Math.min(3, base.roundsPerInsert() + 1));
    }
    /** Accepted reload's profile has matching explicit granularity; WeaponCycle's safety check remains strict. */
    public static WeaponProfile reloadProfile(WeaponProfile p, WeaponReloadPolicy.Plan plan) {
        if (p.shellReload() != plan.incremental()) throw new IllegalArgumentException("Cannot change reload kind");
        return new WeaponProfile(p.mode(), p.damage(), p.intervalTicks(), p.magazine(), p.reserve(), plan.intervalTicks(),
                p.range(), p.chargeTicks(), p.burst(), p.pellets(), p.spread(), p.speed(), p.gravity(), p.blastRadius(),
                p.automatic(), p.infiniteReserve(), p.cadenceTicks(), p.burstSpacingTicks(), p.sharedBurstAmmo(),
                p.shellReload(), plan.firstTicks(), plan.roundsPerInsert());
    }
    /** Query at accepted charge/draw start. Never changes an in-progress charge's deadline. */
    public static int chargeTicks(ServerPlayer p, WeaponCatalog.Entry entry, int base) {
        if (!ownerValid(p) || !WeaponLoadout.canUse(p) || !charged(entry)) return base;
        var slot = owned(p, p.getMainHandItem());
        return slot == null || !slot.entry.equals(entry) || !slot.has(WARM_UP) ? base : slot.cycle.chargeTicks(now(p), base);
    }
    /** Capture after a real accepted GRENADE or MELEE use, before delayed release/damage. */
    public static AbilityToken acceptedAbility(ServerPlayer p, AbilitySlot kind) {
        if (kind != AbilitySlot.GRENADE && kind != AbilitySlot.MELEE) return AbilityToken.NONE;
        observe(p, false);
        var state = existing(p);
        if (state == null || state.data == null || state.guardianClass == GuardianClass.NONE || state.runtime == null) return AbilityToken.NONE;
        var ability = state.data.loadout().map(l -> l.get(kind)).orElse(null);
        if (ability == null) return AbilityToken.NONE;
        return new AbilityToken(state, kind, ability, state.slots.values().stream().filter(s -> s.has(DESPERATE)).toList());
    }
    /** Explicit, attributed positive grenade/melee kill only. Supers, environmental and generic ability kills excluded. */
    public static void abilityKilled(ServerPlayer p, AbilityToken token, LivingEntity corpse) {
        if (token == null || !valid(p, token.player) || corpse == null || corpse == p || corpse.level() != p.level()
                || (corpse.isAlive() && !corpse.isDeadOrDying())) return;
        if (!Objects.equals(token.ability, token.player.data.loadout().map(l -> l.get(token.kind)).orElse(null))) return;
        for (var slot : token.slots)
            if (valid(p, token.player, slot) && slot.corpses.add(corpse)) slot.cycle.abilityKill(now(p));
    }
    public static List<Buff> buffs(ServerPlayer p) {
        if (!ownerValid(p) || !WeaponLoadout.canUse(p)) return List.of();
        var slot = owned(p, p.getMainHandItem());
        if (slot == null) return List.of();
        long tick = now(p); var out = new ArrayList<Buff>();
        if (slot.has(PRECISION) && slot.cycle.precisionStacks(tick) > 0)
            out.add(new Buff(PRECISION, slot.cycle.precisionStacks(tick), slot.cycle.precisionRemaining(tick)));
        if (slot.has(WARM_UP) && slot.cycle.warmRemaining(tick) > 0)
            out.add(new Buff(WARM_UP, 1, slot.cycle.warmRemaining(tick)));
        if (slot.has(DESPERATE) && slot.cycle.desperateStacks(tick) > 0)
            out.add(new Buff(DESPERATE, slot.cycle.desperateStacks(tick), slot.cycle.desperateRemaining(tick)));
        return List.copyOf(out);
    }
    public static void stowing(ServerPlayer p, ItemStack stack) { var slot = owned(p, stack); if (slot != null) slot.cycle.stow(); }
    public static void changed(ServerPlayer p, ItemStack stack) {
        var state = p == null ? null : PLAYERS.get(p.getUUID());
        if (state != null && state.owner == p) state.slots.remove(stack);
    }
    public static void edited(ItemStack stack) { PLAYERS.values().forEach(s -> s.slots.remove(stack)); }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        var state = PLAYERS.get(p.getUUID());
        if (state != null && state.owner == p) PLAYERS.remove(p.getUUID());
    }
    public static void clear() { PLAYERS.clear(); }
}
