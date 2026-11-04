package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.GuardianData;
import kim.biryeong.destiny.guardian.GuardianRuntime;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.CombatHud;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

/** Wellspring/Thresh paid weapon-final-blow credit. No generic AbilityService.onKill call.
 * All authority observations are read-only: they never create guardian attachments/runtime.
 * Master captures after paid ranged/Sword emission, excludes glaive melee, and carries the SAME
 * token into direct and payload/splash damage. Only positive actual-damage final blows call killed.
 */
public final class WeaponEnergyPerks {
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final GuardianRuntime runtime;
        final GuardianData data;
        final GuardianClass guardianClass;
        final IdentityHashMap<ItemStack, Source> sources = new IdentityHashMap<>();
        Session(ServerPlayer p, GuardianData data, GuardianRuntime runtime) {
            owner = p; level = p.level(); this.data = data; this.runtime = runtime;
            guardianClass = data.guardianClass();
        }
    }
    private record Source(Session session, ItemStack stack, WeaponCatalog.Entry entry,
                          WeaponPerks.Roll wellspring, WeaponPerks.Roll thresh) {}
    public static final class Token {
        public static final Token NONE = new Token(null);
        private final Source source;
        private final WeaponEnergyCredit.Corpses<LivingEntity> corpses;
        private Token(Source source) {
            this.source = source;
            corpses = source == null ? null : new WeaponEnergyCredit.Corpses<>();
        }
    }
    private WeaponEnergyPerks() {}
    private static GuardianData data(ServerPlayer p) { return p.getAttachedOrElse(Guardians.DATA, null); }
    private static boolean ownerValid(ServerPlayer p) {
        if (p == null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
        var data = data(p);
        var runtime = Guardians.runtimeIfPresent(p).orElse(null);
        return data != null && data.guardianClass() != null && data.guardianClass() != GuardianClass.NONE
            && runtime != null && runtime.superSession == null;
    }
    private static boolean validSession(ServerPlayer p, Session s) {
        return s.owner == p && s.level == p.level() && ownerValid(p) && s.data == data(p)
            && s.runtime == Guardians.runtimeIfPresent(p).orElse(null) && s.guardianClass == s.data.guardianClass();
    }
    private static boolean owns(ServerPlayer p, ItemStack stack) {
        if (stack.isEmpty()) return false;
        for (int i = 0; i < p.getInventory().getContainerSize(); i++)
            if (p.getInventory().getItem(i) == stack) return true;
        return false;
    }
    private static WeaponPerks.Roll wellspring(ItemStack stack, WeaponCatalog.Entry entry) {
        return WellspringProfile.supports(entry) ? WeaponPerks.selected(stack, WellspringProfile.ID)
            .filter(r -> r.id().equals(entry.id()) && WellspringProfile.rolls().contains(r)).orElse(null) : null;
    }
    private static WeaponPerks.Roll thresh(ItemStack stack, WeaponCatalog.Entry entry) {
        return ThreshProfile.supports(entry) ? WeaponPerks.selected(stack, ThreshProfile.ID)
            .filter(r -> r.id().equals(entry.id()) && ThreshProfile.rolls().contains(r)).orElse(null) : null;
    }
    private static boolean currentSource(ServerPlayer p, Source source) {
        return owns(p, source.stack) && WeaponItems.entry(source.stack).filter(source.entry::equals).isPresent()
            && Objects.equals(source.wellspring, wellspring(source.stack, source.entry))
            && Objects.equals(source.thresh, thresh(source.stack, source.entry));
    }
    private static boolean valid(ServerPlayer p, Source source) {
        if (p == null || source == null) return false;
        var session = source.session;
        return SESSIONS.get(p.getUUID()) == session && validSession(p, session)
            && session.sources.get(source.stack) == source && currentSource(p, source);
    }
    /** Sample once per tick/lifecycle boundary. Observed removal, edit, invalid owner, Super,
     * dimension, class, attachment or runtime replacement permanently revokes old emissions.
     * Stowing an unchanged original object while still owned is allowed for in-flight shots.
     */
    public static void update(ServerPlayer p) {
        if (p == null) return;
        var session = SESSIONS.get(p.getUUID());
        if (session == null || session.owner != p) return;
        if (!validSession(p, session)) SESSIONS.remove(p.getUUID());
        else session.sources.values().removeIf(source -> !currentSource(p, source));
    }
    /** AFTER the production cycle actually paid a cartridge/Sword swing. Never for glaive melee,
     * dry fire, cancelled charge, or abilities. Capture itself grants no energy.
     */
    public static Token capture(ServerPlayer p) {
        update(p);
        if (!ownerValid(p) || !WeaponLoadout.canUse(p)) return Token.NONE;
        var stack = p.getMainHandItem();
        int selected = p.getInventory().getSelectedSlot();
        if (selected < 0 || selected >= 9 || p.getInventory().getItem(selected) != stack || !owns(p, stack)) return Token.NONE;
        var entry = WeaponItems.entry(stack).orElse(null);
        if (entry == null) return Token.NONE;
        var wellspring = wellspring(stack, entry);
        var thresh = thresh(stack, entry);
        if (wellspring == null && thresh == null) return Token.NONE;
        var session = SESSIONS.get(p.getUUID());
        if (session == null || !validSession(p, session)) {
            session = new Session(p, data(p), Guardians.runtimeIfPresent(p).orElseThrow());
            SESSIONS.put(p.getUUID(), session);
        }
        var source = session.sources.get(stack);
        if (source == null) {
            source = new Source(session, stack, entry, wellspring, thresh);
            session.sources.put(stack, source);
        }
        return new Token(source);
    }
    private static boolean grantWellspring(GuardianData data) {
        var loadout = data.loadout().orElse(null);
        if (loadout == null) return false;
        var abilities = new ArrayList<WeaponEnergyCredit.Cooldown<AbilitySlot>>();
        for (var slot : new AbilitySlot[]{AbilitySlot.GRENADE, AbilitySlot.MELEE, AbilitySlot.CLASS_ABILITY}) {
            var id = loadout.get(slot);
            if (id == null) continue;
            var ability = AbilityRegistry.get(id).orElse(null);
            if (ability == null || !id.equals(ability.id()) || ability.slot() != slot
                || ability.guardianClass() != data.guardianClass()) continue;
            abilities.add(new WeaponEnergyCredit.Cooldown<>(slot, ability.cooldownTicks(), data.cooldown(slot)));
        }
        var credits = WeaponEnergyCredit.cooldowns(abilities, WellspringProfile.energyPercent());
        credits.forEach(data::setCooldown);
        return !credits.isEmpty();
    }
    /** Caller has confirmed positive actual HP/absorption loss and death, not predicted damage.
     * Dedup is per corpse per paid emission, so one payload can reward distinct killed victims.
     */
    public static void killed(ServerPlayer p, Token token, LivingEntity corpse) {
        if (token == null || token == Token.NONE) return;
        update(p);
        if (!valid(p, token.source) || corpse == null || corpse.level() != p.level() || corpse.isAlive()
            || !token.corpses.admit(corpse)) return;
        var source = token.source;
        var data = source.session.data;
        boolean changed = source.wellspring != null && grantWellspring(data);
        if (source.thresh != null) {
            float before = data.superEnergy();
            float after = WeaponEnergyCredit.superEnergy(before, ThreshProfile.energyPercent(source.entry));
            if (Float.compare(before, after) != 0) {
                data.setSuperEnergy(after);
                changed = true;
            }
        }
        if (changed) CombatHud.update(p);
    }
    /** Real selection edits revoke immediately, including edit-away-and-back in one tick. */
    public static void edited(ItemStack stack) {
        for (var session : SESSIONS.values()) session.sources.remove(stack);
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        if (p == null) return;
        var session = SESSIONS.get(p.getUUID());
        if (session != null && session.owner == p) session.sources.remove(stack);
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        var session = SESSIONS.get(p.getUUID());
        if (session != null && session.owner == p) SESSIONS.remove(p.getUUID());
    }
    public static void clear() { SESSIONS.clear(); }
}
