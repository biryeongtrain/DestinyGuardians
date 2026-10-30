package kim.biryeong.destiny.crucible;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import kim.biryeong.destiny.fx.AmmoBrickVisual;
import kim.biryeong.destiny.weapon.*;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Server-thread-only Control ammunition; no self-registering events and no PvE meter.
 * Main must call arrive after inventory restoration, died BEFORE native respawn,
 * tickArena once per match tick, tick per player, guard before firing, and
 * equipmentChanged AFTER successful inventory equipment mutations. Same-slot selection
 * does not discard ammo. Call leave on exit/disconnect, clear on server shutdown.
 * Glaive melee uses AmmoGeneration.GLAIVE_MELEE; the explicit helper is equivalent.
 * Crates are personal proximity pickups, one allotment per shell, not shared world blocks.
 * Special: first 30s, LOCAL repeat 60s. Heavy: LOCAL 90s then 120s. Both expire in 60s.
 * Master owns research documentation; see CrucibleAmmoRules for sourced/local boundaries.
 */
public final class CrucibleAmmo {
    private static CrucibleAmmoRules.Config config = CrucibleAmmoRules.Config.localDefaults();
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final Map<UUID, Victim> VICTIMS = new HashMap<>();
    private static final Set<UUID> INITIALIZED = new HashSet<>();
    private static long round = -1;
    private static CrucibleWorld.Arena currentArena;
    private record Saved(WeaponCatalog.Entry weapon, int rounds, int reserve, long overflow) { }
    private record Contribution(UUID player, CrucibleAmmoRules.Credit kind, long tick) { }
    private static final class Victim {
        final LivingEntity entity;
        final Map<UUID, Contribution> hits = new LinkedHashMap<>();
        boolean paid;
        long updated;
        Victim(LivingEntity entity) { this.entity = entity; }
    }
    private record Brick(WeaponAmmoType type, boolean crate, Vec3 at, long expires, ElementHolder visual) { }
    private static final class Session {
        ServerPlayer owner;
        final IdentityHashMap<ItemStack, WeaponCatalog.Entry> known = new IdentityHashMap<>();
        final EnumMap<WeaponSlot, ItemStack> equipped = new EnumMap<>(WeaponSlot.class);
        final Map<Integer, Saved> respawn = new HashMap<>();
        final List<Brick> bricks = new ArrayList<>();
        Vec3 spawn;
        double meter;
        int specialWave = -1, heavyWave = -1;
        boolean dead, reconciling;
        Session(ServerPlayer owner) { this.owner = owner; this.spawn = owner.position(); }
    }
    private CrucibleAmmo() { }
    /** Configuration changes apply immediately; configure before match start for stable tuning. */
    public static void configure(CrucibleAmmoRules.Config value) { config = Objects.requireNonNull(value); }
    /** firstLife is advisory only: repeated intro/fresh callbacks cannot mint an allocation. */
    public static void arrive(ServerPlayer p, boolean firstLife) {
        if (!CrucibleRuntime.participating(p)) return;
        observeRound(CrucibleRuntime.snapshot().round());
        Session s = SESSIONS.get(p.getUUID());
        boolean fresh = s == null;
        if (fresh) { s = new Session(p); SESSIONS.put(p.getUUID(), s); }
        WeaponRuntime.cancelUseForSkill(p);
        boolean changed = false;
        if (s.dead) {
            // keepInventory may copy ItemStacks. Only this explicit death -> arrival boundary
            // authorizes replacement identities, by exact saved slot and catalog entry.
            s.known.clear(); s.equipped.clear();
            for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
                ItemStack stack = p.getInventory().getItem(i);
                var e = WeaponItems.entry(stack).orElse(null);
                if (e == null || !finite(e)) continue;
                Saved saved = s.respawn.get(i);
                if (saved != null && saved.weapon().equals(e)) {
                    WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(e),
                            saved.rounds(), saved.reserve(), saved.overflow()));
                    s.known.put(stack, e); changed = true;
                }
            }
            s.respawn.clear(); s.dead = false;
            VICTIMS.remove(p.getUUID());
        }
        if (s.owner != p) destroyBricks(s);
        s.owner = p; s.spawn = p.position();
        changed |= reconcile(p, s);
        if (fresh && INITIALIZED.add(p.getUUID())) {
            int count = specialCount(p);
            for (var e : WeaponLoadout.equipped(p)) if (e.characteristics().ammo() == WeaponAmmoType.SPECIAL) {
                int amount = CrucibleAmmoRules.split(CrucibleAmmoRules.starting(e.weapon().family()), count);
                var profile = WeaponProfile.forEntry(e.weapon());
                WeaponItems.save(e.stack(), new WeaponMagazine(profile, Math.min(amount, profile.magazine()),
                        Math.max(0, amount - profile.magazine())));
                changed = true;
            }
        }
        if (changed) sync(p);
    }
    /** Retention is written before native keepInventory copying. Do NOT remove victim hits here:
     * AFTER_DEATH precedes Combat.afterDamage, which still needs them for kill/assist credit. */
    public static void died(ServerPlayer p) {
        Session s = owned(p); if (s == null || s.dead) return;
        WeaponRuntime.cancelUseForSkill(p);
        boolean changed = reconcile(p, s);
        int count = specialCount(p);
        for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
            ItemStack stack = p.getInventory().getItem(i);
            var e = WeaponItems.entry(stack).orElse(null);
            if (e == null || !finite(e)) continue;
            var profile = WeaponProfile.forEntry(e);
            var ammo = WeaponItems.magazine(stack, profile);
            long keep = WeaponCharacteristics.of(e).ammo() == WeaponAmmoType.SPECIAL
                    ? CrucibleAmmoRules.retained(ammo.total(), CrucibleAmmoRules.split(CrucibleAmmoRules.starting(e.family()), count)) : 0;
            int loaded = (int)Math.min(ammo.rounds(), keep);
            var retained = new WeaponMagazine(profile, loaded, keep - loaded, 0, ammo.loadedLimit());
            if (ammo.total() != retained.total()) { WeaponItems.save(stack, retained); changed = true; }
            s.respawn.put(i, new Saved(e, retained.rounds(), retained.reserve(), retained.overflow()));
        }
        s.dead = true;
        destroyBricks(s); // LOCAL: transient personal pickups end with their owner's life.
        if (changed) sync(p);
    }
    public static void leave(ServerPlayer p) {
        Session s = owned(p); if (s == null) return;
        destroyBricks(s); SESSIONS.remove(p.getUUID());
        VICTIMS.remove(p.getUUID());
        VICTIMS.values().forEach(v -> v.hits.remove(p.getUUID()));
        // INITIALIZED survives a same-round leave/rejoin: no new starting grant.
    }
    public static void clear() {
        SESSIONS.values().forEach(CrucibleAmmo::destroyBricks);
        SESSIONS.clear(); VICTIMS.clear(); INITIALIZED.clear(); round = -1; currentArena = null;
    }
    /** Safe before WeaponLoadout.canUse: never calls canUse or changes selected slot. */
    public static void guard(ServerPlayer p) {
        Session s = owned(p); if (s == null || s.dead) return;
        if (reconcile(p, s)) sync(p);
    }
    public static void equipmentChanged(ServerPlayer p) { guard(p); }
    private static boolean reconcile(ServerPlayer p, Session s) {
        if (s.reconciling) return false;
        s.reconciling = true;
        try { return reconcileInventory(p, s); }
        finally { s.reconciling = false; }
    }
    private static boolean reconcileInventory(ServerPlayer p, Session s) {
        boolean changed = false;
        var equipped = WeaponLoadout.equipped(p);
        var next = new EnumMap<WeaponSlot, ItemStack>(WeaponSlot.class);
        equipped.forEach(e -> next.put(e.slot(), e.stack()));
        boolean swapped = s.equipped.entrySet().stream().anyMatch(e -> next.get(e.getKey()) != e.getValue());
        if (swapped) {
            WeaponRuntime.cancelUseForSkill(p);
            // LOCAL anti-banking policy: any actual equipment replacement clears all
            // equipped finite pools, including the removed item. Selecting a hotbar slot does not.
            for (var stack : s.equipped.values()) changed |= zero(stack);
            for (var stack : next.values()) changed |= zero(stack);
        }
        var present = Collections.newSetFromMap(new IdentityHashMap<ItemStack, Boolean>());
        for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
            ItemStack stack = p.getInventory().getItem(i); present.add(stack);
            var e = WeaponItems.entry(stack).orElse(null);
            if (e == null) { s.known.remove(stack); continue; }
            if (!e.equals(s.known.get(stack))) {
                if (finite(e)) { WeaponRuntime.cancelUseForSkill(p); changed |= zero(stack); }
                s.known.put(stack, e);
            }
            // Backups never bank ammo, even if previously recognized.
            if (next.values().stream().noneMatch(equippedStack -> equippedStack == stack)) changed |= zero(stack);
        }
        s.known.keySet().retainAll(present);
        s.equipped.clear(); s.equipped.putAll(next);
        return changed;
    }
    private static boolean zero(ItemStack stack) {
        var e = WeaponItems.entry(stack).orElse(null);
        if (e == null || !finite(e)) return false;
        var profile = WeaponProfile.forEntry(e);
        if (WeaponItems.magazine(stack, profile).total() == 0) return false;
        WeaponItems.save(stack, new WeaponMagazine(profile, 0, 0)); return true;
    }
    private static boolean finite(WeaponCatalog.Entry e) { return WeaponCharacteristics.of(e).ammo() != WeaponAmmoType.PRIMARY; }
    private static int specialCount(ServerPlayer p) {
        return (int)WeaponLoadout.equipped(p).stream().filter(e -> e.characteristics().ammo() == WeaponAmmoType.SPECIAL).count();
    }
    private static Session owned(ServerPlayer p) {
        Session s = SESSIONS.get(p.getUUID()); return s != null && s.owner == p ? s : null;
    }
    private static void sync(ServerPlayer p) { p.getInventory().setChanged(); p.containerMenu.broadcastChanges(); }
    private static void destroyBricks(Session s) { s.bricks.forEach(b -> b.visual().destroy()); s.bricks.clear(); }

    public static void afterDamage(ServerPlayer source, LivingEntity target, AmmoGeneration generation, float before, float after) {
        if (generation == null) return;
        credit(source, target, CrucibleAmmoRules.Credit.valueOf(generation.kind().name()), before, after);
    }
    public static void afterGlaiveDamage(ServerPlayer source, LivingEntity target, float before, float after) {
        credit(source, target, CrucibleAmmoRules.Credit.GLAIVE_MELEE, before, after);
    }
    private static void credit(ServerPlayer source, LivingEntity target, CrucibleAmmoRules.Credit kind, float before, float after) {
        if (!(target instanceof ServerPlayer victim) || owned(source) == null || owned(victim) == null
                || !CrucibleRuntime.enemies(source, victim) || !Float.isFinite(before) || !Float.isFinite(after)
                || before <= 0 || after >= before) return;
        var snapshot = CrucibleRuntime.snapshot();
        if (snapshot.phase() != ControlMatch.Phase.PLAYING || snapshot.paused()) return;
        long now = source.level().getGameTime();
        Victim v = VICTIMS.get(victim.getUUID());
        if (v == null || v.entity != victim) {
            if (VICTIMS.size() >= 2048) return;
            v = new Victim(victim); VICTIMS.put(victim.getUUID(), v);
        }
        if (v.paid) return;
        v.updated = now;
        if (v.hits.size() < 32 || v.hits.containsKey(source.getUUID()))
            v.hits.put(source.getUUID(), new Contribution(source.getUUID(), kind, now));
        if (victim.isAlive() && !victim.isDeadOrDying()) return;
        v.paid = true;
        for (var hit : v.hits.values()) {
            Session s = SESSIONS.get(hit.player());
            if (s == null || now - hit.tick() > config.assistTicks() || s.owner.level() != victim.level()
                    || !CrucibleRuntime.enemies(s.owner, victim) || specialCount(s.owner) == 0) continue;
            s.meter = Math.min(config.maxBricks(), s.meter + CrucibleAmmoRules.gain(config, hit.kind(), !hit.player().equals(source.getUUID())));
            if (!s.dead) dropOwed(s, victim.position());
        }
    }
    private static boolean spawn(Session s, WeaponAmmoType type, Vec3 at, boolean crate) {
        if (s.bricks.size() >= config.maxBricks()) return false;
        var safe = AmmoEconomy.safePosition(s.owner.level(), at); if (safe.isEmpty()) return false;
        var pos = safe.get();
        s.bricks.add(new Brick(type, crate, pos, s.owner.level().getGameTime() + CrucibleAmmoRules.BRICK_TICKS,
                AmmoBrickVisual.create(s.owner, type, pos)));
        return true;
    }
    private static void dropOwed(Session s, Vec3 at) {
        boolean dropped = false;
        while (s.meter >= 1 && spawn(s, WeaponAmmoType.SPECIAL, at, false)) { s.meter -= 1; dropped = true; }
        if (dropped) for (var viewer : s.owner.level().players())
            if (CrucibleRuntime.enemies(s.owner, viewer))
                viewer.sendSystemMessage(Component.literal("적이 특수 탄약을 생성했습니다."));
    }
    /** Call even in INTRO/RESULTS; round transitions reset once. The first 0 -> 1 round
     * adopts pre-intro arrivals without issuing a second starting grant. */
    public static void tickArena(CrucibleWorld.Arena arena, ControlMatch.Snapshot snapshot) {
        if (currentArena != null && currentArena != arena) clear();
        currentArena = arena;
        if (observeRound(snapshot.round())) {
            for (var p : arena.level().players())
                if (snapshot.members().containsKey(p.getUUID())) arrive(p, true);
        }
        long now = arena.level().getGameTime();
        VICTIMS.values().removeIf(v -> now - v.updated > config.assistTicks());
        if (snapshot.phase() != ControlMatch.Phase.PLAYING || snapshot.paused()) return;
        int special = CrucibleAmmoRules.crateWave(snapshot.phaseTicks(), config);
        int heavy = snapshot.phaseTicks() < CrucibleAmmoRules.HEAVY_FIRST_TICKS ? -1
                : (snapshot.phaseTicks() - CrucibleAmmoRules.HEAVY_FIRST_TICKS) / CrucibleAmmoRules.HEAVY_REPEAT_TICKS;
        for (var s : SESSIONS.values()) {
            if (!snapshot.members().containsKey(s.owner.getUUID()) || s.owner.level() != arena.level() || s.dead) continue;
            // Late join gets only current wave, never a backlog. Unsafe positions retry.
            if (special > s.specialWave && spawn(s, WeaponAmmoType.SPECIAL, s.spawn.add(2, 0, 0), true)) s.specialWave = special;
            if (config.heavyCrates() && heavy > s.heavyWave && spawn(s, WeaponAmmoType.HEAVY, s.spawn.add(-2, 0, 0), true)) s.heavyWave = heavy;
        }
    }
    /** Called before arrival grants too: tickArena cannot reset a grant already issued
     * in the current round. WAITING round zero adopts the first round without minting. */
    private static boolean observeRound(long next) {
        if (round == next) return false;
        boolean reset = round > 0;
        if (reset) {
            SESSIONS.values().forEach(CrucibleAmmo::destroyBricks);
            SESSIONS.clear(); VICTIMS.clear(); INITIALIZED.clear();
        }
        round = next;
        return reset;
    }
    public static void tick(ServerPlayer p) {
        Session s = owned(p); if (s == null || s.dead) return;
        boolean changed = reconcile(p, s);
        long now = p.level().getGameTime();
        boolean active = CrucibleRuntime.participating(p) && CrucibleRuntime.canAct(p)
                && p.isAlive() && !p.isRemoved() && !p.isSpectator();
        // An owed brick from an unsafe kill waits for the next safe confirmed kill, not a free body spawn.
        for (var it = s.bricks.iterator(); it.hasNext();) {
            Brick b = it.next();
            boolean expired = now >= b.expires() || !p.level().hasChunkAt(BlockPos.containing(b.at()));
            boolean picked = false;
            if (!expired && active && p.position().distanceToSqr(b.at()) <= 2.25
                    && p.level().clip(new ClipContext(p.position().add(0, .4, 0), b.at(),
                    ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p)).getType() == HitResult.Type.MISS) {
                picked = grant(p, b.type(), b.crate()); changed |= picked;
            }
            if (expired || picked) { b.visual().destroy(); it.remove(); }
        }
        if (changed) sync(p);
    }
    private static boolean grant(ServerPlayer p, WeaponAmmoType type, boolean crate) {
        var weapons = WeaponLoadout.equipped(p).stream().filter(e -> e.characteristics().ammo() == type).toList();
        boolean changed = false;
        for (var e : weapons) {
            var ammo = WeaponItems.magazine(e.stack(), WeaponProfile.forEntry(e.weapon()));
            int amount = type == WeaponAmmoType.SPECIAL ? CrucibleAmmoRules.specialPayout(e.weapon().family(), crate)
                    : CrucibleAmmoRules.heavyBrick(e.weapon().family());
            amount = CrucibleAmmoRules.split(amount, weapons.size());
            int gained = e.weapon().family().equals("sword") ? ammo.addLoaded(amount) : ammo.addReserve(amount);
            if (gained > 0) { WeaponItems.save(e.stack(), ammo); changed = true; }
        }
        return changed; // Full pools keep the shell; partial acceptance consumes one allotment.
    }
    public static double meter(ServerPlayer p) { Session s = owned(p); return s == null ? 0 : s.meter; }
    public static int bricks(ServerPlayer p) { Session s = owned(p); return s == null ? 0 : s.bricks.size(); }
}
