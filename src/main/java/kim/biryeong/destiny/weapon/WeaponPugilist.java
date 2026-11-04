package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Main-thread paid weapon kills / caller-confirmed actual melee damage only.
 * No generic kill/input listener and no HUD writes. Master owns dispatch and final timing wrappers.
 * Energy is a flat fraction of the FULL authored Minecraft melee cooldown, not remaining time
 * or live Destiny tier scaling. Timing reads never bind, scan entities, refresh, or create data.
 */
public final class WeaponPugilist {
    private static final Map<UUID, IdentityHashMap<ItemStack, Session>> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final WeaponCatalog.Entry entry;
        final WeaponPerks.Roll roll;
        final GuardianData data;
        final GuardianRuntime runtime;
        final GuardianClass guardianClass;
        final PugilistCycle cycle = new PugilistCycle();
        long observed;
        Session(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry entry, WeaponPerks.Roll roll) {
            owner = p; level = p.level(); this.stack = stack; this.entry = entry; this.roll = roll;
            data = p.getAttachedOrElse(Guardians.DATA, null);
            runtime = Guardians.runtimeIfPresent(p).orElseThrow();
            guardianClass = data.guardianClass(); observed = now(p);
        }
    }
    public static final class Token {
        public static final Token NONE = new Token(null);
        private final Session source;
        private final WeaponEnergyCredit.Corpses<LivingEntity> corpses=new WeaponEnergyCredit.Corpses<>();
        private Token(Session source) { this.source = source; }
    }
    public static final class MeleeToken {
        public static final MeleeToken NONE = new MeleeToken(null, null, null);
        private final Session source;
        private final Ability melee;
        private final PugilistCycle.Melee contact;
        private MeleeToken(Session source, Ability melee, PugilistCycle.Melee contact) {
            this.source = source; this.melee = melee; this.contact = contact;
        }
    }
    private WeaponPugilist() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static void thread(ServerPlayer p) {
        if (p != null && !p.level().getServer().isSameThread())
            throw new IllegalStateException("Pugilist is main server thread owned");
    }
    private static boolean ownerValid(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        var runtime = Guardians.runtimeIfPresent(p).orElse(null);
        return data != null && data.guardianClass() != null && data.guardianClass() != GuardianClass.NONE
            && runtime != null && runtime.superSession == null;
    }
    private static boolean owned(ServerPlayer p, ItemStack stack) {
        if (stack == null || stack.isEmpty()) return false;
        if (WeaponLoadout.enabled(p) && WeaponLoadout.equipped(p).stream().noneMatch(e -> e.stack() == stack)) return false;
        for (int i = 0; i < p.getInventory().getContainerSize(); i++)
            if (p.getInventory().getItem(i) == stack) return true;
        return false;
    }
    private static boolean held(ServerPlayer p, Session s) {
        int slot = p.getInventory().getSelectedSlot();
        return slot >= 0 && slot < 9 && p.getMainHandItem() == s.stack
            && p.getInventory().getItem(slot) == s.stack && WeaponLoadout.canUse(p);
    }
    private static boolean valid(ServerPlayer p, Session s) {
        if (!ownerValid(p)) return false;
        var sessions = SESSIONS.get(p.getUUID());
        return sessions != null && sessions.get(s.stack) == s && s.owner == p && s.level == p.level()
            && now(p) >= s.observed && owned(p, s.stack)
            && p.getAttachedOrElse(Guardians.DATA, null) == s.data && s.data.guardianClass() == s.guardianClass
            && Guardians.runtimeIfPresent(p).orElse(null) == s.runtime
            && WeaponItems.entry(s.stack).filter(s.entry::equals).isPresent()
            && WeaponPerks.selected(s.stack, PugilistProfile.ID).filter(s.roll::equals).isPresent();
    }
    /** Exact equipped ID must resolve to a registered MELEE of this Guardian's current class.
     * AbilityService.equipped alone accepts wrong-slot/class IDs and creates GuardianData.
     */
    private static Ability melee(GuardianData data) {
        if (data == null || data.guardianClass() == null || data.guardianClass() == GuardianClass.NONE) return null;
        var id = data.loadout().map(l -> l.get(AbilitySlot.MELEE)).orElse(null);
        if (id == null) return null;
        var ability = AbilityRegistry.get(id).orElse(null);
        return ability != null && id.equals(ability.id()) && ability.slot() == AbilitySlot.MELEE
            && ability.guardianClass() == data.guardianClass() ? ability : null;
    }
    /** Permanently revoke observed invalid ownership/lifecycle. Stow preserves paid kill tokens. */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> s.owner == p && !valid(p, s));
        for (var s : sessions.values()) {
            if (s.owner != p) continue;
            if (!held(p, s)) s.cycle.stow();
            s.cycle.update(now(p));
            s.observed = now(p);
        }
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    private static Session bind(ServerPlayer p) {
        if (p == null) return null;
        update(p);
        if (!ownerValid(p) || !WeaponLoadout.canUse(p) || now(p) < 0) return null;
        var stack = p.getMainHandItem();
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, PugilistProfile.ID).orElse(null);
        int slot = p.getInventory().getSelectedSlot();
        if (slot < 0 || slot >= 9 || p.getInventory().getItem(slot) != stack || !owned(p, stack)
            || !PugilistProfile.supports(entry) || roll == null || !PugilistProfile.rolls().contains(roll)
            || !entry.id().equals(roll.id())) return null;
        return SESSIONS.computeIfAbsent(p.getUUID(), ignored -> new IdentityHashMap<>())
            .computeIfAbsent(stack, ignored -> new Session(p, stack, entry, roll));
    }
    /** Call only after the production shot has paid its cartridge. Source survives ordinary stow. */
    public static Token capture(ServerPlayer p) {
        var s = bind(p);
        return s == null ? Token.NONE : new Token(s);
    }
    /** Ceiling to whole ticks, based on FULL authored cooldown. Never grant negative cooldown. */
    public static int grantTicks(int fullCooldownTicks, int percent) {
        if (fullCooldownTicks <= 0 || percent <= 0 || percent > 100) return 0;
        return (int)Math.min(Integer.MAX_VALUE, ((long)fullCooldownTicks * percent + 99) / 100);
    }
    /** Caller has confirmed positive actual loss and final blow on an eligible enemy.
     * Each paid emission shares its corpse ledger across direct/payload callbacks.
     * The ledger ends with that emission instead of retaining every lifetime kill in the weapon session.
     */
    public static void killed(ServerPlayer p, Token token, LivingEntity corpse) {
        if (p == null || token == null || token.source == null || corpse == null) return;
        update(p);
        var s = token.source;
        if (!valid(p, s) || corpse == p || corpse.level() != s.level || corpse.isAlive()
            || !token.corpses.admit(corpse)) return;
        var melee = melee(s.data);
        int remaining = s.data.cooldown(AbilitySlot.MELEE);
        if (melee == null || remaining <= 0) return;
        int credit = grantTicks(melee.cooldownTicks(), PugilistProfile.energyPercent(s.entry));
        if (credit > 0) {
            s.data.setCooldown(AbilitySlot.MELEE, Math.max(0, remaining - credit));
            CombatHud.update(p);
        }
    }
    /** Original held source captured once at an accepted registered class-matching melee. */
    public static MeleeToken meleeAccepted(ServerPlayer p) {
        if (!ownerValid(p)) return MeleeToken.NONE;
        thread(p);
        var ability = melee(p.getAttachedOrElse(Guardians.DATA, null));
        if (ability == null) return MeleeToken.NONE;
        var s = bind(p);
        if (s == null) return MeleeToken.NONE;
        var contact = s.cycle.meleeAccepted(now(p));
        return contact == null ? MeleeToken.NONE : new MeleeToken(s, ability, contact);
    }
    /** AFTER positive actual melee HP/absorption loss; lethal contacts also qualify.
     * Repeated contact callbacks cannot extend time. A genuinely new accepted melee can.
     */
    public static void meleeConfirmed(ServerPlayer p, MeleeToken token, LivingEntity target) {
        if (p == null || token == null || token.source == null || target == null) return;
        update(p);
        var s = token.source;
        if (valid(p, s) && held(p, s) && target != p && target.level() == s.level
            && token.melee == melee(s.data)) s.cycle.meleeConfirmed(now(p), token.contact, target.getUUID());
    }
    private static Session active(ServerPlayer p, ItemStack stack) {
        if (p == null) return null;
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        return s != null && valid(p, s) && held(p, s) && s.cycle.remaining(now(p)) > 0 ? s : null;
    }
    public static int remaining(ServerPlayer p) {
        var s = p == null ? null : active(p, p.getMainHandItem());
        return s == null ? 0 : s.cycle.remaining(now(p));
    }
    /** Pure public actual-contact probe; selected roll alone never creates a buff. */
    public static int handlingBonus(ServerPlayer p) {
        return remaining(p) > 0 ? PugilistProfile.handlingBonus() : 0;
    }
    private static boolean co(Session s, String id) {
        return WeaponPerks.selected(s.stack, id).filter(r -> PugilistProfile.compatible(s.entry, id, r)).isPresent();
    }
    private static int threats(ServerPlayer p, Session s) {
        return co(s, ThreatDetectorProfile.ID) ? WeaponThreatDetector.stacks(p) : 0;
    }
    private static int totalBonus(ServerPlayer p, Session s, int threats) {
        int total = PugilistProfile.handlingBonus();
        if (co(s, SurplusProfile.ID)) total += SurplusProfile.handlingBonus(WeaponSurplus.stacks(p));
        if (co(s, StatsForAllProfile.ID) && WeaponStatsForAll.ownedRemaining(p, s.stack) > 0) total += 35;
        return total + ThreatDetectorProfile.handlingBonus(threats);
    }
    /** MASTER: wrap the final handling result with this, preserving existing companions.
     * Read outgoing stow duration before calling stowing(). Already accepted durations stay fixed.
     */
    public static int handlingTicks(ServerPlayer p, ItemStack stack, boolean ready, int base) {
        var s = active(p, stack);
        if (s == null) return base;
        int threats = threats(p, s);
        return PugilistProfile.handlingTicks(s.entry, totalBonus(p, s, threats),
            ThreatDetectorProfile.handlingScalar(threats), ready);
    }
    /** MASTER: outermost ADS wrapper; TD has no ADS scalar. Snapshot only if legally co-selected. */
    public static int adsTicks(ServerPlayer p, WeaponCatalog.Entry entry, int base, boolean entering) {
        var s = p == null ? null : active(p, p.getMainHandItem());
        if (s == null || !s.entry.equals(entry)) return base;
        return PugilistProfile.adsTicks(entry, totalBonus(p, s, threats(p, s)),
            entering && co(s, SnapshotAimProfile.ID));
    }
    /** Cancel live handling and pending melee even for a same-tick away-and-back swap. */
    public static void stowing(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && s.owner == p) s.cycle.stow();
    }
    public static void edited(ItemStack stack) {
        if (stack == null) return;
        var it = SESSIONS.values().iterator();
        while (it.hasNext()) {
            var sessions = it.next(); sessions.remove(stack);
            if (sessions.isEmpty()) it.remove();
        }
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        var s = sessions == null ? null : sessions.get(stack);
        if (s != null && s.owner == p) sessions.remove(stack);
        if (sessions != null && sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        thread(p);
        var sessions = SESSIONS.get(p.getUUID());
        if (sessions == null) return;
        sessions.values().removeIf(s -> s.owner == p);
        if (sessions.isEmpty()) SESSIONS.remove(p.getUUID());
    }
    public static void clear() { SESSIONS.clear(); }
}
