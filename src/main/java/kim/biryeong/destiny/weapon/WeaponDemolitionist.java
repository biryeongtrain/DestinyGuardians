package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Paid final blows and actual grenade release only. No generic onKill or manual reload callback.
 * Flat baseline chunk -> authored Minecraft cooldown is an approximation, not live D2 tier/stat scaling.
 * The 60-tick refill lock is owner-wide locally; source does not prove instance vs owner scope.
 */
public final class WeaponDemolitionist {
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final Map<UUID, ReloadLock> RELOADS = new HashMap<>();
    private record ReloadLock(ServerPlayer owner, ServerLevel level, long deadline) {}
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final GuardianRuntime runtime;
        final GuardianData data;
        final GuardianClass guardianClass;
        final IdentityHashMap<ItemStack, Source> sources = new IdentityHashMap<>();
        Session(ServerPlayer p) {
            owner=p; level=p.level(); runtime=Guardians.runtime(p); data=Guardians.data(p); guardianClass=data.guardianClass();
        }
    }
    private record Source(Session session, ItemStack stack, WeaponCatalog.Entry entry, WeaponPerks.Roll roll) {}
    public static final class Token {
        public static final Token NONE = new Token(null);
        private final Source source;
        private final Set<LivingEntity> corpses = Collections.newSetFromMap(new IdentityHashMap<>());
        private Token(Source source) { this.source=source; }
    }
    public static final class GrenadeToken {
        public static final GrenadeToken NONE = new GrenadeToken(null);
        private final Source source;
        private boolean consumed;
        private GrenadeToken(Source source) { this.source=source; }
    }
    private WeaponDemolitionist() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && Guardians.isGuardian(p) && !AbilityService.inSuper(p);
    }
    private static boolean validSession(ServerPlayer p, Session s) {
        return s.owner==p && s.level==p.level() && ownerValid(p) && s.runtime==Guardians.runtime(p)
                && s.data==Guardians.data(p) && s.guardianClass==s.data.guardianClass();
    }
    private static boolean owns(ServerPlayer p, ItemStack stack) {
        for (int i=0;i<p.getInventory().getContainerSize();i++) if (p.getInventory().getItem(i)==stack) return true;
        return false;
    }
    private static boolean currentSource(ServerPlayer p, Source source) {
        return owns(p,source.stack) && WeaponItems.entry(source.stack).filter(source.entry::equals).isPresent()
                && WeaponPerks.selected(source.stack,DemolitionistProfile.ID).filter(source.roll::equals).isPresent();
    }
    private static boolean valid(ServerPlayer p, Source source) {
        if (source==null) return false;
        var s=source.session;
        return SESSIONS.get(p.getUUID())==s && validSession(p,s) && s.sources.get(source.stack)==source && currentSource(p,source);
    }
    /** Observed invalid states permanently revoke existing tokens. Unobserved same-tick histories are not tracked. */
    public static void update(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());
        if (s!=null && s.owner==p) {
            if (!validSession(p,s)) SESSIONS.remove(p.getUUID());
            else s.sources.values().removeIf(source -> !currentSource(p,source));
        }
        var lock=RELOADS.get(p.getUUID());
        if (lock!=null && lock.owner==p && (lock.level!=p.level() || !p.isAlive() || now(p)>=lock.deadline))
            RELOADS.remove(p.getUUID());
    }
    private static Source snapshot(ServerPlayer p) {
        update(p);
        if (!ownerValid(p) || !WeaponLoadout.canUse(p)) return null;
        var stack=p.getMainHandItem();
        var selected=WeaponPerks.selected(stack,DemolitionistProfile.ID);
        var entry=WeaponItems.entry(stack);
        if (selected.isEmpty() || entry.isEmpty() || !owns(p,stack)) return null;
        var s=SESSIONS.get(p.getUUID());
        if (s==null || !validSession(p,s)) { s=new Session(p); SESSIONS.put(p.getUUID(),s); }
        var source=s.sources.get(stack);
        if (source==null) { source=new Source(s,stack,entry.get(),selected.get()); s.sources.put(stack,source); }
        return source;
    }
    /** Capture only after the production weapon cycle paid the emission's cartridge. */
    public static Token capture(ServerPlayer p) {
        var source=snapshot(p); return source==null?Token.NONE:new Token(source);
    }
    /** Local ceiling-to-tick policy, using FULL authored cooldown rather than a fraction of remaining. */
    public static int grantTicks(int fullCooldownTicks, int percent) {
        if (fullCooldownTicks<=0 || percent<=0 || percent>100) return 0;
        return (int)Math.min(Integer.MAX_VALUE, ((long)fullCooldownTicks*percent+99)/100);
    }
    /** Caller has observed positive HP/absorption loss AND the final blow. Dedup is per corpse, not per explosion. */
    public static void killed(ServerPlayer p, Token token, LivingEntity corpse) {
        if (token==null || !valid(p,token.source) || corpse.level()!=p.level() || corpse.isAlive()
                || !token.corpses.add(corpse)) return;
        var grenade=AbilityService.equipped(p,AbilitySlot.GRENADE);
        var data=Guardians.data(p);
        int remaining=data.cooldown(AbilitySlot.GRENADE);
        if (remaining<=0 || grenade.isEmpty()) return;
        int amount=grantTicks(grenade.get().cooldownTicks(),DemolitionistProfile.energyPercent(token.source.entry));
        if (amount>0) {
            data.setCooldown(AbilitySlot.GRENADE,Math.max(0,remaining-amount));
            CombatHud.update(p);
        }
    }
    /** Atomic original-weapon snapshot at accepted cast. A swap never redirects its reward. */
    public static GrenadeToken grenadeAccepted(ServerPlayer p) {
        var source=snapshot(p); return source==null?GrenadeToken.NONE:new GrenadeToken(source);
    }
    /** Called AFTER real projectile launch at valid consumed contact, not merely accepted button input.
     * Full/no-reserve releases still spend the opportunity locally. No-op does not emit reload audio/procs.
     */
    public static int grenadeReleased(ServerPlayer p, GrenadeToken token) {
        if (token==null || token==GrenadeToken.NONE || token.consumed) return 0;
        token.consumed=true;
        update(p);
        if (!valid(p,token.source)) return 0;
        long tick=now(p); var lock=RELOADS.get(p.getUUID());
        if (lock!=null && lock.owner==p && lock.level==p.level() && tick<lock.deadline) return 0;
        RELOADS.put(p.getUUID(),new ReloadLock(p,p.level(),tick+DemolitionistProfile.perk().reloadCooldownTicks()));
        var source=token.source;
        var ammo=WeaponItems.magazine(source.stack,WeaponProfile.forEntry(source.entry));
        int moved=ammo.reload(); // reserve/legacy-overflow transfer only; no precision generation or Kill Clip callback.
        if (moved>0) {
            WeaponRuntime.cancelForGrenadeRefill(p,source.stack);
            WeaponItems.save(source.stack,ammo);
            p.getInventory().setChanged(); p.containerMenu.broadcastChanges(); CombatHud.update(p);
        }
        return moved;
    }
    /** Actual direct select/clear edits also revoke stale source tokens, even within one tick.
     * A no-op select never calls this. Inventory drop/reacquire history is still only sampled. */
    static void edited(ItemStack stack) {
        for (var s:SESSIONS.values()) s.sources.remove(stack);
    }
    /** Selection edits revoke old emissions, but NEVER reset the owner-wide refill lockout. */
    public static void changed(ServerPlayer p, ItemStack stack) {
        var s=SESSIONS.get(p.getUUID()); if (s!=null && s.owner==p) s.sources.remove(stack);
    }
    public static void cleanup(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID()); if (s!=null && s.owner==p) SESSIONS.remove(p.getUUID());
        var lock=RELOADS.get(p.getUUID()); if (lock!=null && lock.owner==p) RELOADS.remove(p.getUUID());
    }
    public static void clear() { SESSIONS.clear(); RELOADS.clear(); }
}
