package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.Fx;
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
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** W321 batch-B facade: Target Lock, Envious Assassin/Arsenal, Harmony, Under-Over, Golden Tricorn,
 * Lasting Impression, Timed Payload, Reservoir Burst, Explosive Head, Cluster Bomb, Chain Reaction.
 * Central hooks call this class once per hook point. Main server thread only. State is per player
 * and per exact item identity; no item NBT is written except reserve-funded Envious magazine credit. */
public final class PerkBatchB {
    private static final String P = "";
    private static final int MAX_TASKS = 512;
    private static final Map<UUID, PlayerState> PLAYERS = new HashMap<>();
    private PerkBatchB() {}

    private static final class StackState {
        final PerkBatchBMath.TargetLock lock = new PerkBatchBMath.TargetLock();
        final PerkBatchBMath.Tricorn tricorn = new PerkBatchBMath.Tricorn();
        long harmonyUntil = Long.MIN_VALUE / 4;
        int enviousKills;
        final Set<ItemStack> arsenalSources = Collections.newSetFromMap(new IdentityHashMap<>());
        boolean reservoirFull;
        long reservoirLatchUntil = Long.MIN_VALUE / 4;
    }
    private record Task(long due, ServerLevel level, Runnable action) {}
    private static final class PlayerState {
        final ServerPlayer owner;
        final ServerLevel level;
        final IdentityHashMap<ItemStack, StackState> stacks = new IdentityHashMap<>();
        final List<Task> tasks = new ArrayList<>();
        long lastKill = Long.MIN_VALUE / 4;
        ItemStack lastKillStack;
        PlayerState(ServerPlayer owner) { this.owner = owner; this.level = owner.level(); }
        StackState of(ItemStack stack) { return stacks.computeIfAbsent(stack, ignored -> new StackState()); }
    }

    /** One paid emission/contact. NONE for non-weapons. Splash copies never earn direct-only bonuses. */
    public static final class Token {
        public static final Token NONE = new Token(null, null, null, null, Set.of(), false, false, 0);
        private final ServerPlayer owner;
        private final ServerLevel level;
        private final ItemStack stack;
        private final WeaponCatalog.Entry entry;
        private final Set<String> perks;
        private final boolean splash, reservoir;
        private final int depth;
        private Token(ServerPlayer owner, ServerLevel level, ItemStack stack, WeaponCatalog.Entry entry,
                      Set<String> perks, boolean splash, boolean reservoir, int depth) {
            this.owner = owner; this.level = level; this.stack = stack; this.entry = entry; this.perks = perks;
            this.splash = splash; this.reservoir = reservoir; this.depth = depth;
        }
        public boolean has(String id) { return perks.contains(id); }
        /** Explosive/perk splash of the same emission: keeps buffs, drops direct-only effects. */
        public Token splash() {
            return owner == null || splash ? this : new Token(owner, level, stack, entry, perks, true, reservoir, depth);
        }
        private Token deeper() { return new Token(owner, level, stack, entry, perks, true, false, depth + 1); }
    }

    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected();
    }
    private static PlayerState state(ServerPlayer p) {
        var s = PLAYERS.get(p.getUUID());
        if (s == null || s.owner != p || s.level != p.level()) {
            s = new PlayerState(p);
            PLAYERS.put(p.getUUID(), s);
        }
        return s;
    }
    private static PlayerState existing(ServerPlayer p) {
        var s = p == null ? null : PLAYERS.get(p.getUUID());
        return s != null && s.owner == p && s.level == p.level() ? s : null;
    }
    /** Batch-B traits actually selected on this exact stack, without NBT reads for unrelated weapons. */
    public static Set<String> selected(ItemStack stack) {
        var entry = WeaponItems.entry(stack).orElse(null);
        if (entry == null) return Set.of();
        Set<String> result = null;
        for (var id : PerkBatchBProfile.IDS) {
            if (PerkBatchBProfile.rolls(id).stream().noneMatch(r -> r.id().equals(entry.id()))) continue;
            if (WeaponPerks.selected(stack, id).isPresent()) {
                if (result == null) result = new HashSet<>();
                result.add(id);
            }
        }
        return result == null ? Set.of() : Set.copyOf(result);
    }
    private static boolean has(ItemStack stack, String id) {
        var entry = WeaponItems.entry(stack).orElse(null);
        return entry != null && PerkBatchBProfile.rolls(id).stream().anyMatch(r -> r.id().equals(entry.id()))
            && WeaponPerks.selected(stack, id).isPresent();
    }
    private static List<ItemStack> equipped(ServerPlayer p) {
        if (WeaponLoadout.enabled(p)) return WeaponLoadout.equipped(p).stream().map(WeaponLoadout.Equipped::stack).toList();
        var result = new ArrayList<ItemStack>();
        for (int i = 0; i < 9; i++) {
            var s = p.getInventory().getItem(i);
            if (!s.isEmpty() && WeaponItems.entry(s).isPresent()) result.add(s);
        }
        return result;
    }
    private static boolean equippedContains(List<ItemStack> list, ItemStack stack) {
        for (var s : list) if (s == stack) return true;
        return false;
    }
    static double v(String id, String key) { return PerkBatchBProfile.value(id, key); }
    static int t(String id, String key) { return PerkBatchBProfile.ticks(id, key); }

    /** AFTER successful payment, BEFORE damage. */
    public static Token capture(ServerPlayer p) {
        if (!ownerValid(p) || AbilityService.inSuper(p) || !WeaponLoadout.canUse(p)) return Token.NONE;
        var stack = p.getMainHandItem();
        var entry = WeaponItems.entry(stack).orElse(null);
        if (entry == null) return Token.NONE;
        var perks = selected(stack);
        boolean reservoir = false;
        if (perks.contains(PerkBatchBProfile.RESERVOIR_BURST)) {
            var st = state(p).of(stack);
            long now = now(p);
            if (now < st.reservoirLatchUntil) reservoir = true;
            else if (st.reservoirFull) {
                st.reservoirFull = false;
                st.reservoirLatchUntil = now + t(PerkBatchBProfile.RESERVOIR_BURST, "burstLatchTicks");
                reservoir = true;
            }
        }
        return new Token(p, p.level(), stack, entry, perks, false, reservoir, 0);
    }
    private static boolean valid(ServerPlayer owner, Token token) {
        return token != null && token.owner != null && token.owner == owner && token.level == owner.level() && ownerValid(owner);
    }

    /** Pure scalar for one target, applied once inside WeaponRuntime's DamageTraits multiplier. */
    public static float multiplier(ServerPlayer owner, Token token, LivingEntity target) {
        if (!valid(owner, token) || token.perks.isEmpty() || target == null) return 1f;
        var ps = existing(owner);
        var st = ps == null ? null : ps.stacks.get(token.stack);
        long now = now(owner);
        boolean pvp = target instanceof ServerPlayer;
        float m = 1f;
        if (!token.splash && st != null && token.has(PerkBatchBProfile.TARGET_LOCK)) {
            String id = PerkBatchBProfile.TARGET_LOCK;
            m *= PerkBatchBMath.targetLockMultiplier(st.lock.hits(now, t(id, "hitGapTicks")),
                WeaponProfile.forEntry(token.entry).magazine(), v(id, "startFraction"), v(id, "endFraction"),
                v(id, pvp ? "pvpStart" : "pveStart"), v(id, pvp ? "pvpEnd" : "pveEnd"));
        }
        if (st != null && token.has(PerkBatchBProfile.HARMONY) && now < st.harmonyUntil)
            m *= (float)v(PerkBatchBProfile.HARMONY, "damageMultiplier");
        if (st != null && token.has(PerkBatchBProfile.GOLDEN_TRICORN))
            m *= st.tricorn.multiplier(now, v(PerkBatchBProfile.GOLDEN_TRICORN, "weaponKillMultiplier"),
                v(PerkBatchBProfile.GOLDEN_TRICORN, "abilityKillMultiplier"));
        if (token.reservoir) m *= (float)v(PerkBatchBProfile.RESERVOIR_BURST, "damageMultiplier");
        if (!token.splash && token.has(PerkBatchBProfile.UNDER_OVER) && target.getAbsorptionAmount() > 0)
            m *= (float)v(PerkBatchBProfile.UNDER_OVER, pvp ? "guardianOvershieldMultiplier" : "combatantShieldMultiplier");
        return m;
    }

    /** AFTER positive actual loss. Every weapon emission reports, so other-weapon traits can observe it. */
    public static void confirmed(ServerPlayer owner, Token token, LivingEntity target, float actual) {
        if (!valid(owner, token) || !(actual > 0)) return;
        long now = now(owner);
        if (!token.splash && token.has(PerkBatchBProfile.TARGET_LOCK))
            state(owner).of(token.stack).lock.hit(now, t(PerkBatchBProfile.TARGET_LOCK, "hitGapTicks"));
        var held = owner.getMainHandItem();
        var loadout = equipped(owner);
        if (!equippedContains(loadout, token.stack)) return;
        for (var other : loadout)
            if (other != token.stack && other != held && has(other, PerkBatchBProfile.ENVIOUS_ARSENAL))
                state(owner).of(other).arsenalSources.add(token.stack);
    }

    /** AFTER positive actual loss AND an attributable final blow. */
    public static void killed(ServerPlayer owner, Token token, LivingEntity target) {
        if (!valid(owner, token) || target == null || target == owner) return;
        var ps = state(owner);
        long now = now(owner);
        ps.lastKill = now; ps.lastKillStack = token.stack;
        var held = owner.getMainHandItem();
        var loadout = equipped(owner);
        if (equippedContains(loadout, token.stack))
            for (var other : loadout)
                if (other != token.stack && other != held && has(other, PerkBatchBProfile.ENVIOUS_ASSASSIN))
                    ps.of(other).enviousKills++;
        if (token.has(PerkBatchBProfile.GOLDEN_TRICORN) && token.stack == held)
            ps.of(token.stack).tricorn.weaponKill(now, t(PerkBatchBProfile.GOLDEN_TRICORN, "weaponKillTicks"));
        if (token.has(PerkBatchBProfile.CHAIN_REACTION)
                && token.depth < t(PerkBatchBProfile.CHAIN_REACTION, "maxDepth"))
            chainReaction(owner, token, target);
        if (token.reservoir && !token.splash && token.depth == 0) reservoirExplosion(owner, token, target);
    }

    /** Combat.damage final blow attributed to an ability; promotes an active Golden Tricorn of the same element. */
    public static void abilityKilled(ServerPlayer source, Element element) {
        var ps = existing(source);
        if (ps == null || element == null) return;
        var held = source.getMainHandItem();
        var st = ps.stacks.get(held);
        var entry = WeaponItems.entry(held).orElse(null);
        if (st == null || entry == null || !has(held, PerkBatchBProfile.GOLDEN_TRICORN)) return;
        var damage = WeaponCharacteristics.of(entry).damage();
        boolean light = damage == WeaponCharacteristics.Damage.ARC || damage == WeaponCharacteristics.Damage.SOLAR
            || damage == WeaponCharacteristics.Damage.VOID;
        if (!light || element(entry) != element) return;
        st.tricorn.abilityKill(now(source), t(PerkBatchBProfile.GOLDEN_TRICORN, "abilityKillTicks"));
    }

    /** Accepted held-item change (WeaponHandling.select): stow effects and ready effects. */
    public static void selecting(ServerPlayer p, ItemStack outgoing, ItemStack incoming) {
        if (!ownerValid(p)) return;
        var ps = existing(p);
        if (ps != null && outgoing != null) {
            var out = ps.stacks.get(outgoing);
            if (out != null) { out.lock.reset(); out.tricorn.clear(); out.reservoirFull = false; out.reservoirLatchUntil = Long.MIN_VALUE / 4; }
        }
        if (incoming == null || incoming == outgoing) return;
        var perks = selected(incoming);
        if (perks.isEmpty()) return;
        ps = state(p);
        var st = ps.of(incoming);
        long now = now(p);
        var entry = WeaponItems.entry(incoming).orElseThrow();
        if (perks.contains(PerkBatchBProfile.HARMONY) && ps.lastKillStack != null && ps.lastKillStack != incoming
                && PerkBatchBMath.harmonyActivates(now, ps.lastKill, t(PerkBatchBProfile.HARMONY, "windowTicks")))
            st.harmonyUntil = now + t(PerkBatchBProfile.HARMONY, "durationTicks");
        boolean changed = false;
        if (perks.contains(PerkBatchBProfile.ENVIOUS_ASSASSIN) && st.enviousKills > 0) {
            int kills = st.enviousKills; st.enviousKills = 0;
            String id = PerkBatchBProfile.ENVIOUS_ASSASSIN;
            var profile = WeaponProfile.forEntry(entry);
            var ammo = WeaponItems.magazine(incoming, profile);
            double perKill = WeaponCharacteristics.of(entry).ammo() == WeaponAmmoType.PRIMARY
                ? v(id, "primaryPerKill") : v(id, "specialPerKill");
            int target = PerkBatchBMath.enviousTarget(ammo.rounds(), profile.magazine(), kills, perKill,
                v(id, "perActivationCap"), v(id, "totalCapMagazines"));
            int moved = target <= ammo.rounds() ? 0 : target <= profile.magazine()
                ? ammo.reloadRounds(target - ammo.rounds()) : ammo.reloadOverflow(target);
            if (moved > 0) { WeaponItems.save(incoming, ammo); changed = true; }
        }
        if (perks.contains(PerkBatchBProfile.ENVIOUS_ARSENAL)) {
            var loadout = equipped(p);
            int sources = (int)st.arsenalSources.stream().filter(s -> s != incoming && equippedContains(loadout, s)).count();
            st.arsenalSources.clear();
            if (PerkBatchBMath.arsenalReady(sources, t(PerkBatchBProfile.ENVIOUS_ARSENAL, "requiredOtherWeapons"))) {
                var ammo = WeaponItems.magazine(incoming, WeaponProfile.forEntry(entry));
                if (ammo.reload() > 0) { WeaponItems.save(incoming, ammo); changed = true; }
            }
        }
        if (changed) { p.getInventory().setChanged(); p.containerMenu.broadcastChanges(); }
    }

    /** Server tick: Reservoir full observation and due deferred detonations. */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        var ps = existing(p);
        if (ps == null) {
            var stale = PLAYERS.get(p.getUUID());
            if (stale != null && stale.owner == p) PLAYERS.remove(p.getUUID()); // level change drops pending work
            return;
        }
        if (!ownerValid(p)) { ps.tasks.clear(); return; }
        var held = p.getMainHandItem();
        var entry = WeaponItems.entry(held).orElse(null);
        if (entry != null && has(held, PerkBatchBProfile.RESERVOIR_BURST)) {
            var profile = WeaponProfile.forEntry(entry);
            ps.of(held).reservoirFull = WeaponItems.magazine(held, profile).rounds() >= profile.magazine();
        }
        long now = now(p);
        if (ps.tasks.isEmpty()) return;
        var due = new ArrayList<Task>();
        ps.tasks.removeIf(task -> { if (task.due > now) return false; due.add(task); return true; });
        for (var task : due) if (task.level == p.level() && ownerValid(p)) task.action.run();
    }
    /** Deferred detonation owned by the shooter; dropped on death, disconnect, dimension change or cleanup. */
    public static void schedule(ServerPlayer owner, int delayTicks, Runnable action) {
        if (!ownerValid(owner) || action == null) return;
        var ps = state(owner);
        if (ps.tasks.size() >= MAX_TASKS) return;
        ps.tasks.add(new Task(now(owner) + Math.max(1, delayTicks), owner.level(), action));
    }

    // ---- Projectile/hitscan plans read by WeaponRuntime ----
    /** Fraction of body-equivalent impact moved into a Timed Payload, or 0. */
    public static float timedPayload(ServerPlayer p, WeaponCatalog.Entry entry) {
        return entry != null && ownerValid(p) && p.getMainHandItem() != null && has(p.getMainHandItem(), PerkBatchBProfile.TIMED_PAYLOAD)
            ? (float)v(PerkBatchBProfile.TIMED_PAYLOAD, "payloadFraction") : 0f;
    }
    public static int timedPayloadDelay() { return t(PerkBatchBProfile.TIMED_PAYLOAD, "delayTicks"); }
    public static float explosiveHead(Token token) {
        return token != null && token.has(PerkBatchBProfile.EXPLOSIVE_HEAD) ? (float)v(PerkBatchBProfile.EXPLOSIVE_HEAD, "payloadFraction") : 0f;
    }
    public static int explosiveHeadDelay(double travelled) {
        String id = PerkBatchBProfile.EXPLOSIVE_HEAD;
        return PerkBatchBMath.explosiveHeadDelay(travelled, v(id, "ticksPerBlock"), t(id, "minDelayTicks"), t(id, "maxDelayTicks"));
    }
    /** PvE payload bonus (+30%); PvP payload keeps its budget. */
    public static float payloadBonus(String id, LivingEntity target) {
        return target instanceof ServerPlayer ? 1f : 1f + (float)v(id, "payloadBonusPve");
    }
    public static double payloadRadius(String id) { return v(id, "radius"); }
    public static float payloadFloor(String id) { return id.equals(PerkBatchBProfile.TIMED_PAYLOAD) ? (float)v(id, "splashFloor") : .3f; }
    public record Rocket(int lastingDelay, double radiusScale, float damageScale, int clusterBombs,
                         float clusterFraction, double clusterRadius, double clusterSpread, int clusterMin, int clusterMax) {
        public static final Rocket NONE = new Rocket(0, 1, 1, 0, 0, 0, 0, 0, 0);
    }
    public static Rocket rocket(Token token) {
        if (token == null || token.perks.isEmpty()) return Rocket.NONE;
        boolean li = token.has(PerkBatchBProfile.LASTING_IMPRESSION), cb = token.has(PerkBatchBProfile.CLUSTER_BOMB);
        if (!li && !cb) return Rocket.NONE;
        String l = PerkBatchBProfile.LASTING_IMPRESSION, c = PerkBatchBProfile.CLUSTER_BOMB;
        return new Rocket(li ? t(l, "delayTicks") : 0, li ? v(l, "blastRadiusScale") : 1, li ? (float)v(l, "damageMultiplier") : 1,
            cb ? t(c, "bombs") : 0, cb ? (float)v(c, "fractionEach") : 0, cb ? v(c, "radius") : 0,
            cb ? v(c, "spread") : 0, cb ? t(c, "minDelayTicks") : 0, cb ? t(c, "maxDelayTicks") : 0);
    }

    public record Contact(LivingEntity target, Vec3 point, float fraction) {}
    private static boolean enemy(ServerPlayer owner, LivingEntity target) {
        return target != owner && Combat.isEnemy(owner, target) && !owner.isAlliedTo(target)
            && !(target instanceof TamableAnimal tame && tame.isTame()) && target.isAlive();
    }
    /** Radial contacts with occlusion; the attached/primary target always takes the full fraction. */
    public static List<Contact> contacts(ServerPlayer owner, ServerLevel level, Vec3 center, LivingEntity primary,
                                         double full, double max, double floor) {
        if (owner == null || level == null || center == null || !level.hasChunkAt(BlockPos.containing(center))) return List.of();
        var found = level.getEntitiesOfClass(LivingEntity.class, AABB.ofSize(center, max * 2, max * 2, max * 2),
            e -> enemy(owner, e) && e.getBoundingBox().getCenter().distanceTo(center) <= max);
        if (primary != null && primary.level() == level && enemy(owner, primary) && !found.contains(primary)) found.add(primary);
        found.sort(Comparator.comparingDouble(e -> e.getBoundingBox().getCenter().distanceToSqr(center)));
        var result = new ArrayList<Contact>();
        for (var target : found) {
            Vec3 point = target.getBoundingBox().getCenter();
            if (target != primary) {
                var wall = level.clip(new ClipContext(center, point, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, owner));
                if (wall.getType() != HitResult.Type.MISS && center.distanceToSqr(wall.getLocation()) + 1e-6 < center.distanceToSqr(point)) continue;
            }
            float f = target == primary ? 1f : PerkBatchBMath.falloff(center.distanceTo(point), full, max, floor);
            if (f > 0) result.add(new Contact(target, point, f));
            if (result.size() >= 128) break;
        }
        return result;
    }

    static Element element(WeaponCatalog.Entry entry) {
        return switch (WeaponCharacteristics.of(entry).damage()) {
            case ARC -> Element.ARC; case SOLAR -> Element.SOLAR; case VOID -> Element.VOID; default -> Element.KINETIC;
        };
    }
    /** Perk-owned elemental explosion through Combat.damage (attributed to the weapon, never recursive shots).
     * Kills feed back into this facade only (Chain Reaction can chain to the depth cap). */
    private static void explode(ServerPlayer owner, Token token, Vec3 center, LivingEntity exclude, float fraction,
                                double full, double max, double floor) {
        var level = token.level;
        var element = element(token.entry);
        var profile = WeaponProfile.forEntry(token.entry);
        var attribution = AmmoGeneration.weapon(token.entry);
        var child = token.deeper();
        try (var emission = Combat.emission(new Object())) {
            for (var c : contacts(owner, level, center, null, full, max, floor)) {
                if (c.target() == exclude) continue;
                float requested = CrucibleDamage.base(token.entry, c.target(), profile.damage()) * fraction * c.fraction();
                float before = Combat.damagePool(c.target());
                boolean killed = Combat.damage(level, owner, c.target(), requested, element, attribution);
                float actual = before - Combat.damagePool(c.target());
                if (!(actual > 0)) continue;
                kim.biryeong.destiny.hud.WeaponHitHud.confirm(owner, actual, killed);
                WeaponDamageNumbers.confirm(owner, level, c.point(), actual, false);
                if (killed) killed(owner, child, Combat.damageOwner(c.target()));
            }
        }
        Fx.burst(level, center, element, 18, .3);
        Fx.ring(level, center, Math.max(1, full), WeaponCharacteristics.of(token.entry).damage().color(), 20);
        DestinySounds.at(level, center, DestinySounds.weaponKey(token.entry, "impact"), .6f);
    }
    private static void chainReaction(ServerPlayer owner, Token token, LivingEntity corpse) {
        if (corpse.level() != token.level) return;
        String id = PerkBatchBProfile.CHAIN_REACTION;
        boolean power = WeaponCharacteristics.of(token.entry).ammo() == WeaponAmmoType.HEAVY;
        explode(owner, token, corpse.getBoundingBox().getCenter(), corpse, (float)v(id, "fraction"),
            v(id, power ? "powerFullRadius" : "specialFullRadius"), v(id, power ? "powerMaxRadius" : "specialMaxRadius"), 0);
    }
    private static void reservoirExplosion(ServerPlayer owner, Token token, LivingEntity corpse) {
        if (corpse.level() != token.level) return;
        String id = PerkBatchBProfile.RESERVOIR_BURST;
        double r = v(id, "radius");
        explode(owner, token, corpse.getBoundingBox().getCenter(), corpse, (float)v(id, "explosionFraction"), r * .5, r, .3);
    }

    /** Read-only HUD/debug probe of the held weapon's batch-B state. */
    public static String status(ServerPlayer p) {
        var ps = existing(p);
        var st = ps == null ? null : ps.stacks.get(p.getMainHandItem());
        if (st == null) return P;
        long now = now(p);
        return "lock=" + st.lock.hits(now, 4) + " tricorn=" + st.tricorn.level(now) + " harmony=" + (now < st.harmonyUntil)
            + " envious=" + st.enviousKills + " arsenal=" + st.arsenalSources.size();
    }
    public static void edited(ItemStack stack) {
        if (stack == null) return;
        for (var ps : PLAYERS.values()) {
            ps.stacks.remove(stack);
            for (var st : ps.stacks.values()) st.arsenalSources.remove(stack);
            if (ps.lastKillStack == stack) ps.lastKillStack = null;
        }
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        var ps = existing(p);
        if (ps == null || stack == null) return;
        ps.stacks.remove(stack);
        for (var st : ps.stacks.values()) st.arsenalSources.remove(stack);
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        var ps = PLAYERS.get(p.getUUID());
        if (ps != null && ps.owner == p) PLAYERS.remove(p.getUUID());
    }
    public static void clear() { PLAYERS.clear(); }
}
