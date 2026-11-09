package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.combat.*;
import kim.biryeong.destiny.crucible.CrucibleRuntime;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Base DDC support traits, W327. Event-driven, exact-stack/session authority; no query grants.
 * Pending emissions remain valid while stowed and owned, but edit/removal/class/world changes revoke.
 * No invented Volatile/Jolt substitutes. Loose Change accepts only confirmed attributed debuffs.
 */
public final class PerkExpansionSupport {
    private static final List<String> IDS = List.of("loose_change", "heal_clip", "headstone", "repulsor_brace", "strategist", "permeability");
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final Object level, runtime;
        final GuardianData data;
        final GuardianClass guardianClass;
        final boolean loadout;
        long observed;
        final IdentityHashMap<ItemStack, Source> sources = new IdentityHashMap<>();
        Session(ServerPlayer p) {
            owner = p; level = p.level(); data = data(p); guardianClass = data.guardianClass();
            loadout = WeaponLoadout.enabled(p); observed = now(p);
            runtime = Guardians.runtimeIfPresent(p).orElse(null);
        }
    }
    private static final class Source {
        final Session session;
        final ItemStack stack;
        final WeaponCatalog.Entry entry;
        final Map<String, WeaponPerks.Roll> rolls;
        final PerkExpansionSupportCycle cycle = new PerkExpansionSupportCycle();
        long stowedTick = Long.MIN_VALUE;
        Source(Session session, ItemStack stack, WeaponCatalog.Entry entry) {
            this.session = session; this.stack = stack; this.entry = entry; rolls = rolls(stack);
        }
        boolean has(String id) { return rolls.containsKey(id); }
    }
    public static final class Token {
        public static final Token NONE = new Token(null);
        private final Source source;
        private final WeaponEnergyCredit.Corpses<LivingEntity> corpses = new WeaponEnergyCredit.Corpses<>();
        private Token(Source source) { this.source = source; }
    }
    public static final class ClassToken {
        public static final ClassToken NONE = new ClassToken(null, null, null, null);
        private final Source source;
        private final Ability ability, superAbility;
        private final OsmosisCycle.Token conversion;
        private boolean consumed;
        private ClassToken(Source source, Ability ability, Ability superAbility, OsmosisCycle.Token conversion) {
            this.source = source; this.ability = ability; this.superAbility = superAbility; this.conversion = conversion;
        }
    }
    private PerkExpansionSupport() {}
    private static GuardianData data(ServerPlayer p) { return p.getAttachedOrElse(Guardians.DATA, null); }
    private static long now(ServerPlayer p) { return p.level().getGameTime(); }
    private static boolean ownerValid(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
        var data = data(p); var runtime = Guardians.runtimeIfPresent(p).orElse(null);
        return data != null && data.guardianClass() != GuardianClass.NONE && runtime != null
                && runtime.superSession == null && WeaponLoadout.canUse(p);
    }
    private static boolean sessionValid(ServerPlayer p, Session s) {
        return s != null && s.owner == p && ownerValid(p) && s.level == p.level() && s.data == data(p)
                && now(p) >= s.observed && s.loadout == WeaponLoadout.enabled(p)
                && s.guardianClass == s.data.guardianClass() && s.runtime == Guardians.runtimeIfPresent(p).orElse(null);
    }
    private static boolean owns(ServerPlayer p, ItemStack stack) {
        if (stack == null || stack.isEmpty()) return false;
        boolean canonical = !WeaponLoadout.enabled(p)
                || WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == stack);
        return equippedIdentity(stack, stack.getCount(), p.getInventory().getContainerSize(),
                p.getInventory()::getItem, canonical);
    }
    /** Exact physical equipped object: backpack/offhand and aliased identities cannot carry credit.
     * The canonical flag is sampled from WeaponLoadout only when that mode is enabled. */
    static boolean equippedIdentity(Object stack, int count, int size,
                                    java.util.function.IntFunction<?> item, boolean canonical) {
        if (stack == null || count != 1 || !canonical) return false;
        int identities = 0, index = -1;
        for (int i = 0; i < size; i++) if (item.apply(i) == stack) { identities++; index = i; }
        return identities == 1 && index >= 0 && index < 9;
    }
    private static boolean held(ServerPlayer p, ItemStack stack) {
        int slot = p.getInventory().getSelectedSlot();
        return slot >= 0 && slot < 9 && p.getMainHandItem() == stack && p.getInventory().getItem(slot) == stack
            && (!WeaponLoadout.enabled(p) || WeaponLoadout.equipped(p).stream().anyMatch(e -> e.stack() == stack));
    }
    private static Map<String, WeaponPerks.Roll> rolls(ItemStack stack) {
        var out = new HashMap<String, WeaponPerks.Roll>();
        for (String id : IDS) WeaponPerks.selected(stack, id).ifPresent(r -> out.put(id, r));
        return Map.copyOf(out);
    }
    private static boolean current(ServerPlayer p, Source source) {
        return owns(p, source.stack) && WeaponItems.entry(source.stack).filter(source.entry::equals).isPresent()
                && source.rolls.equals(rolls(source.stack));
    }
    private static boolean valid(ServerPlayer p, Source source) {
        return p != null && source != null && SESSIONS.get(p.getUUID()) == source.session
                && sessionValid(p, source.session) && source.session.sources.get(source.stack) == source && current(p, source);
    }
    private static Source bind(ServerPlayer p, ItemStack stack) {
        if (!ownerValid(p) || !owns(p, stack)) return null;
        var entry = WeaponItems.entry(stack).orElse(null);
        if (entry == null || rolls(stack).isEmpty()) return null;
        Session s = SESSIONS.get(p.getUUID());
        if (!sessionValid(p, s)) { s = new Session(p); SESSIONS.put(p.getUUID(), s); }
        Source source = s.sources.get(stack);
        if (source == null || !current(p, source)) {
            source = new Source(s, stack, entry); s.sources.put(stack, source);
        }
        return source;
    }
    public static void update(ServerPlayer p) {
        if (p == null) return;
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) {
            if (!sessionValid(p, s)) SESSIONS.remove(p.getUUID(), s);
            else {
                s.observed = now(p);
                s.sources.values().removeIf(source -> !current(p, source));
                for (Source source : s.sources.values()) if (!held(p, source.stack)) source.cycle.stow();
            }
        }
    }
    /** Once per actually paid emission; same token travels through direct and splash callbacks. */
    public static Token capture(ServerPlayer p) {
        update(p);
        if (!ownerValid(p) || !held(p, p.getMainHandItem())) return Token.NONE;
        Source source = bind(p, p.getMainHandItem());
        return source == null ? Token.NONE : new Token(source);
    }
    /** BEFORE damage/death clears target statuses. No Volatile exists in the current status engine. */
    public static boolean before(LivingEntity target) {
        return target != null && (Statuses.has(target, Keyword.WEAKENED)
                || Statuses.has(target, Keyword.SUPPRESSED));
    }
    /** Only actual positive-damage final blows, normalized owner target; precision=false for splash. */
    public static void killed(ServerPlayer p, Token token, LivingEntity corpse, boolean precision, boolean voidDebuffed) {
        if (token == null || token == Token.NONE || corpse == null || p == null) return;
        update(p);
        Source s = token.source;
        if (!valid(p, s) || corpse.level() != p.level() || corpse.isAlive() || !token.corpses.admit(corpse)) return;
        long now = now(p);
        if (s.has("heal_clip")) s.cycle.killed(now);
        if (s.has("headstone") && precision && s.cycle.canCrystal(now)) {
            // DDC tier3/4/Guardian -> existing local MINIBOSS/BOSS/GUARDIAN taxonomy.
            // ELITE/rank-and-file and unmapped vehicles retain medium; no health-based guessing.
            var rank = CombatantRank.of(corpse);
            boolean large = rank == CombatantRank.MINIBOSS || rank == CombatantRank.BOSS || rank == CombatantRank.GUARDIAN;
            if (StasisCrystals.spawn(p, p.level(), corpse.position(), large ? 1.4 : 1.0))
                s.cycle.crystalSpawned(now);
        }
        if (s.has("repulsor_brace") && voidDebuffed) TemporaryVoidOvershield.grant(p, 160);
        if (s.has("strategist")) {
            Ability ability = ability(p, AbilitySlot.CLASS_ABILITY);
            if (ability != null) {
                int percent = Set.of("fusion_rifle", "glaive", "shotgun", "sniper_rifle").contains(s.entry.family()) ? 20 : 10;
                var credits = WeaponEnergyCredit.cooldowns(List.of(new WeaponEnergyCredit.Cooldown<>(
                        AbilitySlot.CLASS_ABILITY, ability.cooldownTicks(), s.session.data.cooldown(AbilitySlot.CLASS_ABILITY))), percent);
                credits.forEach(s.session.data::setCooldown);
            }
        }
        CombatHud.update(p);
    }
    /** Call after accepted owner-attributed Scorch/Weaken/Suppress/Freeze etc.; never on damage alone. */
    public static void debuffApplied(ServerPlayer p, LivingEntity target) {
        update(p);
        if (!ownerValid(p) || target == null || target.level() != p.level() || target == p) return;
        for (int i=0; i<9; i++) {
            ItemStack stack = p.getInventory().getItem(i);
            if (WeaponPerks.selected(stack, "loose_change").isEmpty()) continue;
            Source source = bind(p, stack);
            if (source != null) source.cycle.debuffed(now(p));
        }
    }
    public static void reloadFinished(ServerPlayer p, ItemStack stack) {
        update(p);
        if (p == null) return;
        Session session = SESSIONS.get(p.getUUID());
        Source s = session == null ? null : session.sources.get(stack);
        if (!valid(p, s) || !held(p, stack) || !s.has("heal_clip") || !s.cycle.reload(now(p))) return;
        ElementalCure.apply(p, 2);
        for (ServerPlayer ally : p.level().players()) {
            if (ally != p && ally.isAlive() && p.distanceToSqr(ally) <= 225 && CrucibleRuntime.friendly(p, ally))
                ElementalCure.apply(ally, 1);
        }
        CombatHud.update(p);
    }
    private static Ability ability(ServerPlayer p, AbilitySlot slot) {
        var data = data(p); if (data == null) return null;
        var id = data.loadout().map(l -> l.get(slot)).orElse(null);
        var a = id == null ? null : AbilityRegistry.get(id).orElse(null);
        return a != null && a.slot() == slot && a.guardianClass() == data.guardianClass() ? a : null;
    }
    private static WeaponCharacteristics.Damage element(Ability a) {
        return a == null ? null : switch(a.element()) {
            case ARC -> WeaponCharacteristics.Damage.ARC;
            case SOLAR -> WeaponCharacteristics.Damage.SOLAR;
            case VOID -> WeaponCharacteristics.Damage.VOID;
            case KINETIC -> null;
        };
    }
    public static ClassToken classAccepted(ServerPlayer p) {
        update(p);
        if (!ownerValid(p) || !held(p, p.getMainHandItem())) return ClassToken.NONE;
        Source s = bind(p, p.getMainHandItem());
        Ability a = ability(p, AbilitySlot.CLASS_ABILITY), superAbility = ability(p, AbilitySlot.SUPER);
        if (s == null || !s.has("permeability") || a == null || element(superAbility) == null || s.stowedTick >= now(p)) return ClassToken.NONE;
        return new ClassToken(s, a, superAbility, s.cycle.accepted(element(superAbility)));
    }
    public static int classUsed(ServerPlayer p, ClassToken token) {
        if (token == null || token == ClassToken.NONE || token.consumed) return 0;
        token.consumed = true; update(p);
        Source s = token.source;
        if (!valid(p, s) || !held(p, s.stack) || s.stowedTick >= now(p)
                || token.ability != ability(p, AbilitySlot.CLASS_ABILITY) || token.superAbility != ability(p, AbilitySlot.SUPER)) return 0;
        var profile = WeaponProfile.forEntry(s.entry);
        var ammo = WeaponItems.magazine(s.stack, profile);
        int moved = s.cycle.classUsed(token.conversion, ammo, WeaponComponents.profile(s.stack, profile).magazine());
        if (moved > 0) {
            WeaponRuntime.cancelForGrenadeRefill(p, s.stack);
            WeaponItems.save(s.stack, ammo); p.getInventory().setChanged(); p.containerMenu.broadcastChanges();
        }
        CombatHud.update(p); return moved;
    }
    private static Source queried(ServerPlayer p, ItemStack stack) {
        if (p == null) return null;
        var session = SESSIONS.get(p.getUUID());
        Source s = session == null ? null : session.sources.get(stack);
        return valid(p, s) && held(p, stack) ? s : null;
    }
    public static int reloadBonus(ServerPlayer p, ItemStack stack) {
        Source s = queried(p, stack); return s != null && s.has("loose_change") && s.cycle.loose(now(p)) ? 50 : 0;
    }
    public static double adsMovementScalar(ServerPlayer p, ItemStack stack, double base) {
        return reloadBonus(p, stack) > 0 ? 1 - (1-base)*.8 : base;
    }
    public static WeaponCharacteristics.Damage damage(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry,
                                                      WeaponCharacteristics.Damage fallback) {
        Source s = queried(p, stack);
        return s != null && s.entry.equals(entry) && s.has("permeability") && s.stowedTick < now(p) ? s.cycle.damage(fallback) : fallback;
    }
    /** remainingTicks=-1 means active until stow, never a fabricated countdown. */
    public record Buff(String id, int stacks, int remainingTicks) {}
    public static List<Buff> buffs(ServerPlayer p) {
        if (!ownerValid(p)) return List.of();
        var out = new ArrayList<Buff>();
        Source s = queried(p, p.getMainHandItem());
        if (s != null) {
            long now = now(p);
            int loose = s.cycle.looseRemaining(now), heal = s.cycle.healRemaining(now);
            if (s.has("loose_change") && loose > 0) out.add(new Buff("loose_change", 1, loose));
            if (s.has("heal_clip") && heal > 0) out.add(new Buff("heal_clip", 1, heal));
            if (s.has("permeability") && s.cycle.converted() && s.stowedTick < now)
                out.add(new Buff("permeability", 1, -1));
        }
        int shield = TemporaryVoidOvershield.remaining(p);
        if (shield > 0) out.add(new Buff("repulsor_brace", 1, shield));
        return List.copyOf(out);
    }
    public static void stowing(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        var session = SESSIONS.get(p.getUUID());
        if (session == null || session.owner != p) return;
        Source s = session.sources.get(stack);
        if (s != null) { s.cycle.stow(); s.stowedTick = now(p); }
    }
    public static void edited(ItemStack stack) { SESSIONS.values().forEach(s -> s.sources.remove(stack)); }
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        var s = SESSIONS.get(p.getUUID()); if (s != null && s.owner == p) s.sources.remove(stack);
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        var s = SESSIONS.get(p.getUUID()); if (s != null && s.owner == p) SESSIONS.remove(p.getUUID(), s);
    }
    public static void clear() { SESSIONS.clear(); }
}
