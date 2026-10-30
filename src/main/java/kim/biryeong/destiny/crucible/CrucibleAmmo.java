package kim.biryeong.destiny.crucible;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ManualAttachment;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import kim.biryeong.destiny.fx.AmmoBrickVisual;
import kim.biryeong.destiny.weapon.*;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Brightness;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.ItemDisplayContext;
import org.joml.Vector3f;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Server-thread-only Control ammunition. Runtime calls arrive after inventory restoration,
 * died before native respawn, tickArena once per match tick, tick per current player,
 * guard before firing and equipmentChanged after an actual inventory mutation.
 * W273: each accepted life gets Special 2 (trace 30) per equipped weapon. Death with
 * loaded/reserve Special leaves one shared field pickup; no Special meter/timed crates.
 * Shared pickups outlive their donor's death/respawn/exit, expire after 60s, and are
 * collectible by either living, active team. Heavy remains personal and unchanged.
 */
public final class CrucibleAmmo {
    private static CrucibleAmmoRules.Config config = CrucibleAmmoRules.Config.localDefaults();
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final List<SharedBrick> SHARED = new ArrayList<>();
    private static final Set<UUID> INITIALIZED = new HashSet<>();
    private static long round = -1;
    private static CrucibleWorld.Arena currentArena;
    private record Saved(WeaponCatalog.Entry weapon, int rounds, int reserve, long overflow) { }
    private record SharedBrick(ServerLevel level, Vec3 at, long expires, ElementHolder visual) { }
    private record Brick(WeaponAmmoType type, boolean crate, Vec3 at, long expires, ElementHolder visual) { }
    private static final class Session {
        ServerPlayer owner;
        final IdentityHashMap<ItemStack, WeaponCatalog.Entry> known = new IdentityHashMap<>();
        final EnumMap<WeaponSlot, ItemStack> equipped = new EnumMap<>(WeaponSlot.class);
        final Map<Integer, Saved> respawn = new HashMap<>();
        final List<Brick> bricks = new ArrayList<>();
        Vec3 spawn, lastSafe;
        int heavyWave = -1;
        boolean dead, reconciling;
        Session(ServerPlayer owner) { this.owner = owner; this.spawn = owner.position(); }
    }
    private CrucibleAmmo() { }
    /** Configuration changes apply immediately; configure before match start for stable tuning. */
    public static void configure(CrucibleAmmoRules.Config value) { config = Objects.requireNonNull(value); }
    /** firstLife is advisory only: repeated intro/fresh callbacks cannot mint an allocation. */
    public static void arrive(ServerPlayer p, boolean firstLife) {
        if (!CrucibleRuntime.currentParticipant(p) || !p.isAlive() || p.isRemoved() || p.hasDisconnected()) return;
        observeRound(CrucibleRuntime.snapshot().round());
        Session s = SESSIONS.get(p.getUUID());
        boolean fresh = s == null;
        if (fresh) { s = new Session(p); SESSIONS.put(p.getUUID(), s); }
        WeaponRuntime.cancelUseForSkill(p);
        boolean changed = false;
        boolean respawning = s.dead;
        if (respawning) {
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
        }
        if (s.owner != p) destroyBricks(s);
        s.owner = p; s.spawn = p.position();
        s.lastSafe = AmmoEconomy.safePosition(p.level(), p.position()).orElse(null);
        changed |= reconcile(p, s);
        if (respawning || fresh && INITIALIZED.add(p.getUUID())) {
            for (var e : WeaponLoadout.equipped(p)) if (e.characteristics().ammo() == WeaponAmmoType.SPECIAL) {
                int amount = CrucibleAmmoRules.starting(e.weapon().family());
                var profile = WeaponProfile.forEntry(e.weapon());
                WeaponItems.save(e.stack(), new WeaponMagazine(profile, Math.min(amount, profile.magazine()),
                        Math.max(0, amount - profile.magazine())));
                changed = true;
            }
        }
        if (changed) sync(p);
    }
    /** Called for the current dead object before native keepInventory copies its inventory.
     * Mark the epoch dead before emitting anything: duplicate death notifications pay nothing. */
    public static void died(ServerPlayer p) {
        Session s = owned(p);
        if (s == null || s.dead || p.isAlive() || !CrucibleRuntime.currentParticipant(p)) return;
        WeaponRuntime.cancelUseForSkill(p);
        boolean changed = reconcile(p, s);
        boolean hadSpecial = WeaponLoadout.equipped(p).stream()
                .filter(e -> e.characteristics().ammo() == WeaponAmmoType.SPECIAL)
                .anyMatch(e -> {
                    var ammo = WeaponItems.magazine(e.stack(), WeaponProfile.forEntry(e.weapon()));
                    return (long) ammo.rounds() + ammo.reserve() > 0;
                });
        s.dead = true;
        for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
            ItemStack stack = p.getInventory().getItem(i);
            var e = WeaponItems.entry(stack).orElse(null);
            if (e == null || !finite(e)) continue;
            var profile = WeaponProfile.forEntry(e);
            var ammo = WeaponItems.magazine(stack, profile);
            var retained = new WeaponMagazine(profile, 0, 0);
            if (ammo.total() != 0) { WeaponItems.save(stack, retained); changed = true; }
            s.respawn.put(i, new Saved(e, retained.rounds(), retained.reserve(), retained.overflow()));
        }
        destroyBricks(s); // Personal Heavy pickups still end with their owner's life.
        if (hadSpecial) dropShared(s);
        if (changed) sync(p);
    }
    public static void leave(ServerPlayer p) {
        Session s = owned(p); if (s == null) return;
        destroyBricks(s); SESSIONS.remove(p.getUUID());
        for (var b : SHARED) b.visual().stopWatching(p);
        if (SESSIONS.isEmpty()) destroyShared();
        // INITIALIZED survives a same-round leave/rejoin: no new starting grant.
    }
    public static void clear() {
        SESSIONS.values().forEach(CrucibleAmmo::destroyBricks);
        destroyShared();
        SESSIONS.clear(); INITIALIZED.clear(); round = -1; currentArena = null;
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
    private static Session owned(ServerPlayer p) {
        Session s = SESSIONS.get(p.getUUID()); return s != null && s.owner == p ? s : null;
    }
    private static void sync(ServerPlayer p) { p.getInventory().setChanged(); p.containerMenu.broadcastChanges(); }
    private static void destroyBricks(Session s) { s.bricks.forEach(b -> b.visual().destroy()); s.bricks.clear(); }

    /** Legacy Combat callbacks intentionally cannot fund a Special meter or duplicate a death brick. */
    public static void afterDamage(ServerPlayer source, LivingEntity target, AmmoGeneration generation, float before, float after) { }
    public static void afterGlaiveDamage(ServerPlayer source, LivingEntity target, float before, float after) { }

    private static boolean pickupEligible(ServerPlayer p) {
        return CrucibleRuntime.currentParticipant(p) && CrucibleRuntime.canAct(p)
                && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected();
    }
    private static void destroyShared() {
        SHARED.forEach(b -> b.visual().destroy()); SHARED.clear();
    }
    private static void refreshViewers(SharedBrick b) {
        var viewers = new HashSet<net.minecraft.server.network.ServerGamePacketListenerImpl>();
        for (var s : SESSIONS.values()) {
            var p = s.owner;
            if (p.level() == b.level() && pickupEligible(p)) viewers.add(p.connection);
        }
        for (var watcher : List.copyOf(b.visual().getWatchingPlayers()))
            if (!viewers.contains(watcher)) b.visual().stopWatching(watcher);
        for (var watcher : viewers) b.visual().startWatching(watcher);
    }
    private static ElementHolder sharedVisual(ServerLevel level, Vec3 at) {
        var holder = new ElementHolder();
        new ManualAttachment(holder, level, () -> at);
        var item = new ItemStack(Items.PAPER);
        item.set(DataComponents.ITEM_MODEL, kim.biryeong.destiny.DestinyGuardians.id("fx/ammo_brick_special_w42"));
        var display = new ItemDisplayElement(item);
        display.setItemDisplayContext(ItemDisplayContext.NONE);
        display.setScale(new Vector3f(AmmoBrickVisual.SCALE));
        display.setTranslation(new Vector3f(0, AmmoBrickVisual.SCALE * .5f, 0));
        display.setBrightness(new Brightness(15, 15));
        display.setViewRange(1); holder.addElement(display); holder.tick();
        return holder;
    }
    private static void dropShared(Session s) {
        var p = s.owner;
        var snapshot = CrucibleRuntime.snapshot();
        if (currentArena == null || p.level() != currentArena.level()
                || snapshot.phase() != ControlMatch.Phase.PLAYING || snapshot.paused()) return;
        // A void/liquid death uses the last verified field position, then its safe arrival point.
        var safe = AmmoEconomy.safePosition(p.level(), p.position());
        if (safe.isEmpty() && s.lastSafe != null) safe = AmmoEconomy.safePosition(p.level(), s.lastSafe);
        if (safe.isEmpty()) safe = AmmoEconomy.safePosition(p.level(), s.spawn);
        if (safe.isEmpty()) return; // Never force-load chunks or place a pickup in solid/unsafe terrain.
        Vec3 at = safe.get();
        var b = new SharedBrick(p.level(), at, p.level().getGameTime() + CrucibleAmmoRules.BRICK_TICKS,
                sharedVisual(p.level(), at));
        SHARED.add(b); refreshViewers(b);
    }
    private static boolean inReach(ServerPlayer p, Vec3 at) {
        return p.position().distanceToSqr(at) <= 2.25
                && p.level().clip(new ClipContext(p.position().add(0, .4, 0), at,
                ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p)).getType() == HitResult.Type.MISS;
    }
    private static boolean spawn(Session s, WeaponAmmoType type, Vec3 at, boolean crate) {
        if (s.bricks.size() >= config.maxBricks()) return false;
        var safe = AmmoEconomy.safePosition(s.owner.level(), at); if (safe.isEmpty()) return false;
        var pos = safe.get();
        s.bricks.add(new Brick(type, crate, pos, s.owner.level().getGameTime() + CrucibleAmmoRules.BRICK_TICKS,
                AmmoBrickVisual.create(s.owner, type, pos)));
        return true;
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
        for (var it = SHARED.iterator(); it.hasNext();) {
            var b = it.next();
            if (snapshot.phase() != ControlMatch.Phase.PLAYING || b.level() != arena.level()
                    || now >= b.expires() || !b.level().hasChunkAt(BlockPos.containing(b.at()))) {
                b.visual().destroy(); it.remove();
            } else refreshViewers(b);
        }
        if (snapshot.phase() != ControlMatch.Phase.PLAYING || snapshot.paused()) return;
        int heavy = snapshot.phaseTicks() < CrucibleAmmoRules.HEAVY_FIRST_TICKS ? -1
                : (snapshot.phaseTicks() - CrucibleAmmoRules.HEAVY_FIRST_TICKS) / CrucibleAmmoRules.HEAVY_REPEAT_TICKS;
        for (var s : SESSIONS.values()) {
            if (!snapshot.members().containsKey(s.owner.getUUID()) || s.owner.level() != arena.level() || s.dead) continue;
            // Late join gets only current wave, never a backlog. Unsafe positions retry.
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
            destroyShared();
            SESSIONS.clear(); INITIALIZED.clear();
        }
        round = next;
        return reset;
    }
    public static void tick(ServerPlayer p) {
        Session s = owned(p); if (s == null || s.dead) return;
        boolean changed = reconcile(p, s);
        long now = p.level().getGameTime();
        boolean active = pickupEligible(p);
        if (active) s.lastSafe = AmmoEconomy.safePosition(p.level(), p.position()).orElse(s.lastSafe);
        if (active) for (var it = SHARED.iterator(); it.hasNext();) {
            var b = it.next();
            if (b.level() != p.level() || now >= b.expires() || !p.level().hasChunkAt(BlockPos.containing(b.at()))) continue;
            if (inReach(p, b.at()) && grant(p, WeaponAmmoType.SPECIAL, false)) {
                b.visual().destroy(); it.remove(); changed = true;
            }
        }
        for (var it = s.bricks.iterator(); it.hasNext();) {
            Brick b = it.next();
            boolean expired = now >= b.expires() || !p.level().hasChunkAt(BlockPos.containing(b.at()));
            boolean picked = false;
            if (!expired && active && inReach(p, b.at())) {
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
            if (type == WeaponAmmoType.HEAVY) amount = CrucibleAmmoRules.split(amount, weapons.size());
            int gained = e.weapon().family().equals("sword") ? ammo.addLoaded(amount) : ammo.addReserve(amount);
            if (gained > 0) { WeaponItems.save(e.stack(), ammo); changed = true; }
        }
        return changed; // Full pools keep the shell; partial acceptance consumes one allotment.
    }
    public static double meter(ServerPlayer p) { return 0; }
    /** Read-only diagnostics: Heavy remains personal; Special has one shared position per death. */
    public static List<Vec3> sharedPositions(ServerPlayer p) {
        if (!CrucibleRuntime.currentParticipant(p)) return List.of();
        return SHARED.stream().filter(b -> b.level() == p.level()).map(SharedBrick::at).toList();
    }
    public static int bricks(ServerPlayer p) {
        Session s = owned(p); return s == null ? 0 : s.bricks.size() + sharedPositions(p).size();
    }
}
