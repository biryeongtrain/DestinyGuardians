package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.combat.*;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.CombatHud;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

import java.util.*;

/** W322 batch C facade: Genesis, Disruption Break, Shield Disorient, Energy Transfer, Incandescent,
 * Adaptive Munitions, Rimestealer, Crystalline Corpsebloom, Shoot to Loot, Redirection, One-Two Punch.
 * Exactly one call per central hook. Per-player/per-source state is owner-identity scoped; shared
 * combat verbs (shields, rank, vulnerability, freeze, crystals, Frost Armor) live in the combat package.
 * Never damages the owner or allies: every area effect uses Combat.enemiesNear/Combat.damage gates.
 */
public final class PerkBatchC {
    /** One paid emission's source snapshot. Damage type is always captured (Disruption Break
     * vulnerability benefits any Kinetic shooter); perks are only the batch C traits selected then. */
    public static final class Token {
        public static final Token NONE = new Token(null, null, null, null, Set.of());
        final ServerPlayer owner; final ItemStack stack; final WeaponCatalog.Entry entry;
        final WeaponCharacteristics.Damage damage; final Set<String> perks;
        private Token(ServerPlayer owner, ItemStack stack, WeaponCatalog.Entry entry,
                      WeaponCharacteristics.Damage damage, Set<String> perks) {
            this.owner = owner; this.stack = stack; this.entry = entry; this.damage = damage; this.perks = perks;
        }
    }
    /** Per-target transaction observed before damage. */
    public static final class Hit {
        static final Hit NONE = new Hit(Token.NONE, null, CombatantShields.Snapshot.NONE, 0, 1);
        final Token token; final LivingEntity target; final CombatantShields.Snapshot shield;
        final int pellets; final float multiplier;
        private Hit(Token token, LivingEntity target, CombatantShields.Snapshot shield, int pellets, float multiplier) {
            this.token = token; this.target = target; this.shield = shield; this.pellets = pellets; this.multiplier = multiplier;
        }
        public float multiplier() { return multiplier; }
    }
    /** Accepted powered melee snapshot (One-Two Punch). */
    public record MeleeToken(double pve, double pvp) {
        public static final MeleeToken NONE = new MeleeToken(1, 1);
        public float apply(LivingEntity target, float amount) {
            return (float) (amount * (target instanceof Player ? pvp : pve));
        }
    }
    private static final class Source {
        final BatchCRules.Adaptive adaptive = new BatchCRules.Adaptive();
        final BatchCRules.Redirection redirection = new BatchCRules.Redirection();
        final BatchCRules.Corpsebloom bloom = new BatchCRules.Corpsebloom();
    }
    private static final class State {
        final ServerPlayer owner;
        final IdentityHashMap<ItemStack, Source> sources = new IdentityHashMap<>();
        final BatchCRules.OneTwoPunch punch = new BatchCRules.OneTwoPunch();
        ItemStack punchStack; String punchFamily;
        final Set<ItemStack> refills = Collections.newSetFromMap(new IdentityHashMap<>());
        boolean refillAll;
        State(ServerPlayer owner) { this.owner = owner; }
    }
    private record Seeker(ServerPlayer owner, ServerLevel level, Vec3 at, long due) {}
    private static final Map<UUID, State> STATES = new HashMap<>();
    private static final List<Seeker> SEEKERS = new ArrayList<>();
    private static final Random RANDOM = new Random();
    private PerkBatchC() {}

    // ---- registry -------------------------------------------------------------------------
    public static List<String> ids() { return PerkBatchCProfile.ids(); }
    public static boolean has(String id) { return PerkBatchCProfile.has(id); }
    public static List<WeaponPerks.Roll> rolls(String id) { return PerkBatchCProfile.rolls(id); }
    public static String name(String id) { return PerkBatchCProfile.name(id); }

    // ---- helpers ---------------------------------------------------------------------------
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected();
    }
    private static boolean owns(ServerPlayer p, ItemStack stack) {
        if (stack == null || stack.isEmpty()) return false;
        var inv = p.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++) if (inv.getItem(i) == stack) return true;
        return false;
    }
    private static State state(ServerPlayer p) {
        var s = STATES.get(p.getUUID());
        if (s == null || s.owner != p) { s = new State(p); STATES.put(p.getUUID(), s); }
        return s;
    }
    private static Source source(ServerPlayer p, ItemStack stack) { return state(p).sources.computeIfAbsent(stack, k -> new Source()); }
    /** Still owned, same canonical weapon and the trait still selected on that exact object. */
    private static boolean active(ServerPlayer p, Token t, String id) {
        return t != null && t != Token.NONE && t.owner == p && t.perks.contains(id) && ownerValid(p)
                && owns(p, t.stack) && WeaponItems.entry(t.stack).filter(t.entry::equals).isPresent()
                && WeaponPerks.selected(t.stack, id).isPresent();
    }
    private static Vec3 center(LivingEntity e) { return e.position().add(0, e.getBbHeight() * .5, 0); }

    // ---- damage path -----------------------------------------------------------------------
    /** Capture once per paid emission/contact, together with the other DamageTraits. */
    public static Token capture(ServerPlayer p) {
        if (p == null) return Token.NONE;
        var stack = p.getMainHandItem();
        var entry = WeaponItems.entry(stack).orElse(null);
        if (entry == null) return Token.NONE;
        var damage = WeaponOsmosis.damage(p, stack, entry);
        if (!PerkBatchCProfile.rolledBy(entry.id())) return new Token(p, stack, entry, damage, Set.of());
        var perks = new HashSet<String>();
        for (var id : ids()) if (WeaponPerks.selected(stack, id).isPresent()) perks.add(id);
        return new Token(p, stack, entry, damage, Set.copyOf(perks));
    }
    /** Before damage, once per target transaction. Shared Kinetic vulnerability, Adaptive
     * Munitions and Redirection (consumed even if the hit is later immune: DDC row 182). */
    public static Hit before(ServerPlayer owner, Token token, LivingEntity target, int pellets) {
        if (owner == null || token == null || target == null) return Hit.NONE;
        var shield = CombatantShields.snapshot(target);
        double m = 1;
        if (token.damage == WeaponCharacteristics.Damage.KINETIC)
            m *= DamageVulnerability.multiplier(target, WeaponCharacteristics.Damage.KINETIC);
        if (token != Token.NONE && token.owner == owner) {
            if (shield.shielded() && !shield.matches(token.damage) && active(owner, token, PerkBatchCProfile.ADAPTIVE_MUNITIONS)) {
                var r = PerkBatchCProfile.adaptive();
                m *= source(owner, token.stack).adaptive.multiplier(true, r.perHit(token.entry.family()), r.cap(token.entry.family()));
            }
            var rank = CombatantRank.of(target);
            if (rank != null && rank.powerful() && active(owner, token, PerkBatchCProfile.REDIRECTION)) {
                var r = PerkBatchCProfile.redirection();
                int consumed = source(owner, token.stack).redirection.consume(r.consume());
                m *= BatchCRules.Redirection.multiplier(consumed, r.consume(), r.bonusPerStack(), r.maxBonus());
            }
        }
        return new Hit(token, target, shield, pellets, (float) m);
    }
    /** After positive actual HP/absorption loss on the damage owner. */
    public static void after(ServerPlayer owner, Hit hit, float actual, boolean killed) {
        if (owner == null || hit == null || hit == Hit.NONE || hit.target == null || !(actual > 0)) return;
        var t = hit.token; var target = hit.target;
        // Any weapon contact next to a crystal shatters it (covers projectile/wave contacts).
        int shattered = StasisCrystals.shatterNear(owner, center(target), .5);
        if (t == Token.NONE || t.owner != owner || t.perks.isEmpty()) return;
        var shield = hit.shield;
        boolean matching = shield.matches(t.damage);
        boolean broke = shield.broken(target);
        // Genesis
        if (active(owner, t, PerkBatchCProfile.GENESIS)) {
            if (matching && WeaponCharacteristics.of(t.entry).slot() == WeaponSlot.ENERGY) {
                var ammo = WeaponItems.magazine(t.stack, WeaponProfile.forEntry(t.entry));
                if (ammo.generateLoaded(PerkBatchCProfile.genesis().ammoPerMatchingHit()) > 0) {
                    WeaponItems.save(t.stack, ammo);
                    owner.getInventory().setChanged(); owner.containerMenu.broadcastChanges();
                }
            }
            if (broke) state(owner).refills.add(t.stack);
        }
        if (broke && active(owner, t, PerkBatchCProfile.DISRUPTION_BREAK)) {
            var r = PerkBatchCProfile.disruption();
            DamageVulnerability.apply(target, WeaponCharacteristics.Damage.KINETIC, r.kineticMultiplier(), r.ticks());
        }
        if (broke && matching && active(owner, t, PerkBatchCProfile.SHIELD_DISORIENT)) {
            var r = PerkBatchCProfile.disorient();
            for (var e : Combat.enemiesNear(owner.level(), owner, center(target), r.radius()))
                Statuses.apply(owner, e, Keyword.BLINDED, r.ticks());
            if (target.isAlive()) Statuses.apply(owner, target, Keyword.BLINDED, r.ticks());
        }
        if (active(owner, t, PerkBatchCProfile.ADAPTIVE_MUNITIONS))
            source(owner, t.stack).adaptive.hit(shield.shielded(), matching);
        if (CombatantRank.of(target) == CombatantRank.RANK_AND_FILE && active(owner, t, PerkBatchCProfile.REDIRECTION)) {
            var r = PerkBatchCProfile.redirection();
            source(owner, t.stack).redirection.gain(r.gain(), r.maxStacks());
        }
        if (active(owner, t, PerkBatchCProfile.ONE_TWO_PUNCH)) {
            var r = PerkBatchCProfile.oneTwoPunch();
            if (BatchCRules.OneTwoPunch.qualifies(hit.pellets, WeaponProfile.forEntry(t.entry).pellets(), r.pellets())) {
                var s = state(owner); s.punch.grant(now(owner), r.windowTicks()); s.punchStack = t.stack; s.punchFamily = t.entry.family();
            }
        }
        if (killed && !target.isAlive()) killed(owner, t, target);
        rimestealer(owner, t, shattered);
    }
    private static void killed(ServerPlayer owner, Token t, LivingEntity corpse) {
        if (active(owner, t, PerkBatchCProfile.INCANDESCENT)) incandescent(owner, corpse);
        if (active(owner, t, PerkBatchCProfile.CRYSTALLINE_CORPSEBLOOM)) {
            var r = PerkBatchCProfile.corpsebloom();
            if (source(owner, t.stack).bloom.kill(now(owner), r.windowTicks())) {
                double a = RANDOM.nextDouble() * Math.PI * 2;
                Vec3 at = corpse.position().add(Math.cos(a) * r.seekerDistance(), 0, Math.sin(a) * r.seekerDistance());
                SEEKERS.add(new Seeker(owner, owner.level(), at, owner.level().getGameTime() + r.seekerTicks()));
                Fx.line(owner.level(), center(corpse), at.add(0, .3, 0), 0x688DCB, .4, .6f);
            }
        }
        if (StasisStatus.frozen(corpse) && active(owner, t, PerkBatchCProfile.RIMESTEALER))
            FrostArmor.grant(owner, PerkBatchCProfile.rimestealer().frostArmorStacks());
    }
    private static void rimestealer(ServerPlayer owner, Token t, int shattered) {
        if (shattered > 0 && active(owner, t, PerkBatchCProfile.RIMESTEALER))
            FrostArmor.grant(owner, shattered * PerkBatchCProfile.rimestealer().frostArmorStacks());
    }
    private static void incandescent(ServerPlayer owner, LivingEntity corpse) {
        var r = PerkBatchCProfile.incandescent();
        var rank = CombatantRank.of(corpse);
        boolean strong = rank != null && (rank.powerful() || rank == CombatantRank.GUARDIAN);
        double radius = strong ? r.powerfulRadius() : r.radius();
        int ticks = (strong ? r.powerfulScorchStacks() : r.scorchStacks()) * r.ticksPerScorchStack();
        var level = owner.level(); Vec3 at = center(corpse);
        Fx.burst(owner, level, at, Element.SOLAR, strong ? 50 : 30, radius / 3);
        Fx.ring(owner, level, at, radius, Element.SOLAR.glow(), 24);
        for (var e : Combat.enemiesNear(level, owner, at, radius)) {
            if (e == corpse) continue;
            float amount = BatchCRules.points(r.damagePoints(), PerkBatchCProfile.energyTransfer().guardianHp(),
                    e instanceof Player ? e.getMaxHealth() : 20f);
            Combat.damage(level, owner, e, amount, Element.SOLAR);
            if (e.isAlive()) Statuses.scorch(owner, e, ticks);
        }
    }
    /** Hitscan pellet segments of one paid emission: Shoot to Loot bricks and crystal shatter. */
    public static void traced(ServerPlayer owner, Token token, List<Vec3[]> segments) {
        if (owner == null || segments == null || segments.isEmpty()) return;
        int shattered = 0;
        for (var seg : segments) shattered += StasisCrystals.shatterAlong(owner, seg[0], seg[1]);
        if (token == null || token == Token.NONE || token.owner != owner) return;
        rimestealer(owner, token, shattered);
        if (active(owner, token, PerkBatchCProfile.SHOOT_TO_LOOT)) {
            int picked = 0;
            for (var seg : segments)
                picked += AmmoEconomy.collectAlong(owner, seg[0], seg[1], PerkBatchCProfile.shootToLoot().brickHitRadius());
            if (picked > 0) state(owner).refillAll = true;
        }
    }
    /** Projectile blast center: crystals inside the blast shatter. */
    public static void blast(ServerPlayer owner, Token token, Vec3 center, double radius) {
        if (owner == null || center == null) return;
        int shattered = StasisCrystals.shatterNear(owner, center, radius);
        if (token != null && token != Token.NONE && token.owner == owner) rimestealer(owner, token, shattered);
    }

    // ---- melee ------------------------------------------------------------------------------
    /** Accepted powered melee: consumes an active One-Two Punch window. */
    public static MeleeToken meleeAccepted(ServerPlayer p) {
        if (!ownerValid(p)) return MeleeToken.NONE;
        var s = STATES.get(p.getUUID());
        if (s == null || s.owner != p || !s.punch.consume(now(p)) || !owns(p, s.punchStack)) return MeleeToken.NONE;
        var r = PerkBatchCProfile.oneTwoPunch();
        return "hand_cannon".equals(s.punchFamily)
                ? new MeleeToken(r.handCannonMultiplier(), r.handCannonPvpMultiplier())
                : new MeleeToken(r.shotgunMultiplier(), r.shotgunPvpMultiplier());
    }
    /** Pure HUD/diagnostic probe. */
    public static boolean punchReady(ServerPlayer p) {
        var s = p == null ? null : STATES.get(p.getUUID());
        return s != null && s.owner == p && s.punch.active(now(p));
    }
    public static int redirectionStacks(ServerPlayer p, ItemStack stack) {
        var s = p == null ? null : STATES.get(p.getUUID());
        var src = s == null || s.owner != p ? null : s.sources.get(stack);
        return src == null ? 0 : src.redirection.stacks();
    }

    // ---- incoming damage (Energy Transfer) -----------------------------------------------
    /** After actual positive loss (PlayerDamageMixin). Requires an active sword guard. */
    public static void damaged(ServerPlayer p, DamageSource source, float loss) {
        if (!ownerValid(p) || source == null || !(loss > 0)) return;
        var stack = p.getMainHandItem();
        var entry = WeaponItems.entry(stack).orElse(null);
        if (entry == null || !SwordItems.isSword(stack) || WeaponPerks.selected(stack, PerkBatchCProfile.ENERGY_TRANSFER).isEmpty()) return;
        if (!WeaponRuntime.swordStatus(p).map(WeaponRuntime.SwordStatus::guarding).orElse(false)) return;
        boolean blocked = WeaponRuntime.frontalMob(p, source);
        boolean melee = source.getEntity() instanceof Mob && source.getDirectEntity() == source.getEntity();
        double percent = BatchCRules.energyTransferPercent(loss, blocked, melee, p.getMaxHealth(), PerkBatchCProfile.energyTransfer());
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        var loadout = data == null ? null : data.loadout().orElse(null);
        var id = loadout == null ? null : loadout.get(AbilitySlot.CLASS_ABILITY);
        var ability = id == null ? null : AbilityRegistry.get(id).orElse(null);
        if (ability == null || ability.slot() != AbilitySlot.CLASS_ABILITY || ability.guardianClass() != data.guardianClass()) return;
        int before = data.cooldown(AbilitySlot.CLASS_ABILITY);
        int after = BatchCRules.cooldownAfter(ability.cooldownTicks(), before, percent);
        if (after != before) { data.setCooldown(AbilitySlot.CLASS_ABILITY, after); CombatHud.update(p); }
    }

    // ---- lifecycle --------------------------------------------------------------------------
    /** Once per server tick (WeaponRuntime.tick). Shared verbs, seekers and deferred refills. */
    public static void tick(MinecraftServer server) {
        DamageVulnerability.tick(server); StasisStatus.tick(server); StasisCrystals.tick(server); FrostArmor.tick(server);
        for (var it = SEEKERS.iterator(); it.hasNext();) {
            var s = it.next();
            if (s.level.getServer() != server) continue;
            if (!ownerValid(s.owner) || s.owner.level() != s.level) { it.remove(); continue; }
            if (s.level.getGameTime() < s.due) continue;
            it.remove();
            // Seeker settles on the first collider within 4 blocks below (local policy).
            var floor = s.level.clip(new net.minecraft.world.level.ClipContext(s.at.add(0, 1, 0), s.at.add(0, -4, 0),
                    net.minecraft.world.level.ClipContext.Block.COLLIDER, net.minecraft.world.level.ClipContext.Fluid.NONE, s.owner));
            StasisCrystals.spawn(s.owner, s.level, floor.getType() == net.minecraft.world.phys.HitResult.Type.MISS ? s.at : floor.getLocation());
        }
        for (var p : server.getPlayerList().getPlayers()) update(p);
    }
    private static void update(ServerPlayer p) {
        var s = STATES.get(p.getUUID());
        if (s == null || s.owner != p) return;
        if (!ownerValid(p)) { s.refills.clear(); s.refillAll = false; return; }
        var targets = new ArrayList<ItemStack>(s.refills);
        s.refills.clear();
        if (s.refillAll) {
            s.refillAll = false;
            if (WeaponLoadout.enabled(p)) for (var e : WeaponLoadout.equipped(p)) targets.add(e.stack());
            else targets.add(p.getMainHandItem());
        }
        boolean changed = false;
        var seen = Collections.newSetFromMap(new IdentityHashMap<ItemStack, Boolean>());
        for (var stack : targets) if (seen.add(stack)) changed |= refill(p, stack);
        if (changed) { p.getInventory().setChanged(); p.containerMenu.broadcastChanges(); }
    }
    /** Reserve-only magazine refill, never a manual reload proc. */
    private static boolean refill(ServerPlayer p, ItemStack stack) {
        if (!owns(p, stack) || SwordItems.isSword(stack) || WeaponIzanagi.charge(stack) > 0) return false;
        var entry = WeaponItems.entry(stack).orElse(null);
        if (entry == null) return false;
        var ammo = WeaponItems.magazine(stack, WeaponProfile.forEntry(entry));
        if (!ammo.canReload()) return false;
        WeaponRuntime.cancelForTraitRefill(p, stack);
        if (ammo.reload() <= 0) return false;
        WeaponItems.save(stack, ammo);
        return true;
    }
    /** Accepted stow: One-Two Punch is removed on stow; Redirection persists (DDC). */
    public static void stowing(ServerPlayer p, ItemStack outgoing) {
        var s = p == null ? null : STATES.get(p.getUUID());
        if (s != null && s.owner == p && s.punchStack == outgoing) { s.punch.clear(); s.punchStack = null; }
    }
    public static void edited(ItemStack stack) {
        for (var s : STATES.values()) {
            s.sources.remove(stack); s.refills.remove(stack);
            if (s.punchStack == stack) { s.punch.clear(); s.punchStack = null; }
        }
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        var s = p == null ? null : STATES.get(p.getUUID());
        if (s == null || s.owner != p) return;
        s.sources.remove(stack); s.refills.remove(stack);
        if (s.punchStack == stack) { s.punch.clear(); s.punchStack = null; }
    }
    /** Death/disconnect/respawn/dimension: replacement player objects keep their own state. */
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        var s = STATES.get(p.getUUID());
        if (s != null && s.owner == p) STATES.remove(p.getUUID());
        SEEKERS.removeIf(k -> k.owner == p);
        FrostArmor.cleanup(p);
    }
    public static void clear() {
        STATES.clear(); SEEKERS.clear();
        StasisCrystals.clear(); StasisStatus.clear(); DamageVulnerability.clear(); FrostArmor.clear();
    }
}
