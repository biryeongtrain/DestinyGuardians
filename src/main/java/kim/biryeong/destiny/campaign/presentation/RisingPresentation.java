package kim.biryeong.destiny.campaign.presentation;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.campaign.RisingServices;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.network.protocol.game.ClientboundGameEventPacket;
import net.minecraft.network.protocol.game.ClientboundPlayerAbilitiesPacket;
import net.minecraft.network.protocol.game.ClientboundPlayerRotationPacket;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Abilities;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.*;

/**
 * W300 Guardian Rises presentation service (opening scan, Ghost companion, departure, voice/subtitles).
 * {@link #init()} registers it with {@link RisingServices}. Everything runs on the server thread and is
 * owner-private: post effects, sounds, subtitles, Ghost and light fan are sent only to the owning player.
 *
 * <p>No client mod: the camera is the player's own view. A cinematic lock freezes movement (attribute
 * modifiers + position anchor) and, while the HUD should be hidden, tells only that client it is in
 * spectator mode with zero fly/walk speed (hides hotbar, hand and crosshair; server game mode is
 * unchanged). Every lock, post effect and blindness this class adds is removed exactly once on
 * close, death, disconnect, world change into a non-campaign world, or server stop.
 */
public final class RisingPresentation implements RisingServices.Presentation {
    static final Identifier BLACKOUT = DestinyGuardians.id("guardian_rises/blackout");
    static final Identifier SCAN = DestinyGuardians.id("guardian_rises/scan");
    static final Identifier REVIVE = DestinyGuardians.id("guardian_rises/revive");
    static final Identifier SHIP_FLASH = DestinyGuardians.id("guardian_rises/ship_flash");
    static final Identifier FADE = DestinyGuardians.id("guardian_rises/fade");
    static final List<Identifier> POSTS = List.of(BLACKOUT, SCAN, REVIVE, SHIP_FLASH, FADE);
    /** Set false to keep the vanilla HUD during cinematics (lock still freezes movement). */
    static final boolean HIDE_HUD = true;

    private static final RisingPresentation INSTANCE = new RisingPresentation();
    private static final Map<UUID, List<Scene>> SCENES = new HashMap<>();
    private static final Map<UUID, Lock> LOCKS = new HashMap<>();
    /** Departure reached black: the black is kept through the Tower teleport, then an arrival curtain fades in. */
    private static final Map<UUID, Integer> ARRIVAL = new HashMap<>();
    /** Combat HUD stays hidden until this server tick (staggered return after a cinematic). */
    private static final Map<UUID, Integer> HUD_HOLD = new HashMap<>();
    static final int ARRIVAL_HOLD = 40, ARRIVAL_FADE = 30, ARRIVAL_TIMEOUT = 20 * 30, ENTRY_HOLD = 10, ENTRY_FADE = 20;
    static final String ARRIVAL_LINE = "rg.arrival.tower";
    private static boolean initialized;

    private RisingPresentation() {}

    public static void init() {
        if (initialized) return;
        initialized = true;
        RisingServices.register(INSTANCE);
        ServerTickEvents.END_SERVER_TICK.register(RisingPresentation::tick);
        kim.biryeong.destiny.hud.CombatHud.cinematic = RisingPresentation::hudHidden;
        kim.biryeong.destiny.weapon.ProfileWeaponView.suppressed = p -> hudHidden(p) || kim.biryeong.destiny.down.GuardianDown.active(p);
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> reset(handler.getPlayer()));
        ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
            if (entity instanceof ServerPlayer p) reset(p);
        });
        ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.register(RisingPresentation::changedLevel);
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            for (var list : List.copyOf(SCENES.values())) for (var s : List.copyOf(list)) s.close();
            SCENES.clear();
            ARRIVAL.clear();
            DEFERRED.clear();
            HUD_HOLD.clear();
            for (var lock : List.copyOf(LOCKS.values())) lock.release();
            LOCKS.clear();
            GhostCompanion.clearAll();
            RisingAudio.clearAll();
            RisingSubtitles.clearAll();
        });
    }

    /** Campaign instances are Fantasy worlds named destiny:guardian_rises/&lt;uuid&gt; (GuardianRisesInstances). */
    static boolean campaign(ServerLevel level) {
        var id = level.dimension().identifier();
        return id.getNamespace().equals(DestinyGuardians.MOD_ID) && id.getPath().startsWith("guardian_rises/");
    }

    // ---------------------------------------------------------------- RisingServices.Presentation

    @Override public RisingServices.Handle openingScan(ServerPlayer player, Vec3 guardianEye, Runnable done) {
        return openingScan(player, guardianEye, null, done);
    }

    @Override public RisingServices.Handle openingScan(ServerPlayer player, Vec3 guardianEye, Vec3 vista, Runnable done) {
        return start(new OpeningScan(player, guardianEye, vista, done));
    }

    @Override public RisingServices.Handle ghostScan(ServerPlayer player, Vec3 target, int ticks, Runnable done) {
        return start(new GhostScan(player, target, Math.max(10, ticks), done));
    }

    @Override public RisingServices.Handle departure(ServerPlayer player, Vec3 shipPos, float shipYaw, Runnable done) {
        return start(new Departure(player, shipPos, shipYaw, done));
    }

    @Override public RisingServices.PickupHandle pickup(ServerPlayer player, Vec3 pos, float yaw, String kind) {
        for (var old : scenes(player, Pickup.class)) if (old.kind().equals(kind)) old.close(); // one per kind
        return start(new Pickup(player, pos, yaw, kind));
    }

    @Override public RisingServices.Handle shipProp(ServerPlayer player, Vec3 shipPos, float shipYaw) {
        scenes(player, ShipProp.class).forEach(Scene::close); // one parked ship per player
        return start(new ShipProp(player, shipPos, shipYaw));
    }

    /**
     * Queues a Ghost line (id = lower-case WEM tag, e.g. 80b75f5c). Returns ticks until it has finished,
     * including any wait behind the current line; 0 for unknown ids. In a campaign world this also
     * makes sure the Ghost companion is present to mouth the line.
     */
    @Override public int voice(ServerPlayer player, String lineId) {
        if (campaign(player.level())) GhostCompanion.ensure(player, null);
        return RisingAudio.voice(player, lineId);
    }

    /**
     * Stops every scene, lock, voice and the Ghost. After a departure has reached black the black itself is
     * kept (the director calls this right before the Tower teleport); the arrival curtain then fades in.
     */
    @Override public void stopAll(ServerPlayer player) {
        boolean arriving = ARRIVAL.containsKey(player.getUUID());
        var list = SCENES.remove(player.getUUID());
        if (list != null) for (var s : List.copyOf(list)) s.close();
        var lock = LOCKS.remove(player.getUUID());
        if (lock != null) lock.release();
        RisingAudio.stopAll(player);
        GhostCompanion.remove(player);
        if (player.hasDisconnected()) return;
        for (var id : POSTS) if (!(arriving && id.equals(FADE))) player.removePostEffect(id);
        for (var id : Curtain.STEPS) if (!id.equals(FADE)) player.removePostEffect(id);
        if (arriving && !player.getPostEffects().contains(FADE)) player.addPostEffect(FADE);
        if (arriving) holdHud(player, ARRIVAL_TIMEOUT);
    }

    /** Death/disconnect: nothing is carried over, including a pending arrival black. */
    private static void reset(ServerPlayer player) {
        ARRIVAL.remove(player.getUUID());
        DEFERRED.remove(player.getUUID());
        HUD_HOLD.remove(player.getUUID());
        INSTANCE.stopAll(player);
    }

    private static void changedLevel(ServerPlayer player, ServerLevel from, ServerLevel to) {
        boolean had = GhostCompanion.existing(player).isPresent();
        if (!campaign(to)) {
            GhostCompanion.remove(player);
            RisingAudio.ambient(player, false);
            // The post-effect list survives the respawn (ServerPlayer re-sends it); the client's own
            // "loading terrain" screen cannot be suppressed by the server, but it now opens and closes on black.
            if (ARRIVAL.remove(player.getUUID()) != null) arrive(player);
            return;
        }
        if (had) GhostCompanion.ensure(player, null);
        if (!campaign(from) && !SCENES.containsKey(player.getUUID()))
            start(new Curtain(player, ENTRY_HOLD, ENTRY_FADE, null)); // entry transfer: no pop-in before the opening
    }

    private static void arrive(ServerPlayer player) {
        HUD_HOLD.remove(player.getUUID());
        var curtain = new Curtain(player, ARRIVAL_HOLD, ARRIVAL_FADE, ARRIVAL_LINE,
                Component.literal("임무 완료").withStyle(st -> st.withColor(0xF4F6F8).withBold(true)),
                Component.literal("━━━━━━   떠오르는 수호자   ━━━━━━").withColor(0xC9B98A));
        var queued = DEFERRED.remove(player.getUUID());
        if (queued != null) curtain.after.addAll(queued);
        start(curtain);
    }

    /** Messages that would cover the arrival curtain wait for its end (title card first, then chat). */
    private static final Map<UUID, List<Component>> DEFERRED = new HashMap<>();

    /**
     * Sends {@code message} after the arrival curtain when one is pending or running, otherwise now.
     * Used by the campaign's completion chat line.
     */
    public static void afterArrival(ServerPlayer player, Component message) {
        if (player.hasDisconnected()) return;
        var running = scenes(player, Curtain.class);
        if (!running.isEmpty()) { running.getLast().after.add(message); return; }
        if (ARRIVAL.containsKey(player.getUUID())) {
            DEFERRED.computeIfAbsent(player.getUUID(), k -> new ArrayList<>()).add(message);
            return;
        }
        player.sendSystemMessage(message);
    }

    /** Called by a departure that reached black. */
    static void arrivalPending(ServerPlayer player) {
        ARRIVAL.put(player.getUUID(), player.level().getServer().getTickCount());
    }

    static void clearArrival(ServerPlayer player) { ARRIVAL.remove(player.getUUID()); }

    /** True when something other than {@code except} owns the black FADE grade. */
    static boolean wantsBlack(ServerPlayer player, Scene except) {
        if (ARRIVAL.containsKey(player.getUUID())) return true;
        for (var s : scenes(player, Scene.class)) if (s != except && s.holdsBlack()) return true;
        return false;
    }

    static <T extends Scene> List<T> scenes(ServerPlayer player, Class<T> type) {
        var list = SCENES.get(player.getUUID());
        if (list == null) return List.of();
        var out = new ArrayList<T>();
        for (var s : list) if (type.isInstance(s) && !s.closed) out.add(type.cast(s));
        return out;
    }

    /** Ends any running entry/arrival curtain (a cinematic that owns its own grade takes over). */
    static void closeCurtains(ServerPlayer player) { scenes(player, Curtain.class).forEach(Scene::close); }

    /** Combat HUD hidden: cinematic lock active or a staggered return still pending. */
    public static boolean hudHidden(ServerPlayer p) {
        if (cinematic(p) || kim.biryeong.destiny.down.GuardianDown.active(p)) return true;
        Integer until = HUD_HOLD.get(p.getUUID());
        if (until == null) return false;
        if (p.level().getServer().getTickCount() < until) return true;
        HUD_HOLD.remove(p.getUUID());
        return false;
    }

    static void holdHud(ServerPlayer p, int ticks) {
        HUD_HOLD.merge(p.getUUID(), p.level().getServer().getTickCount() + ticks, Math::max);
    }

    private static <T extends Scene> T start(T scene) {
        SCENES.computeIfAbsent(scene.player.getUUID(), k -> new ArrayList<>()).add(scene);
        scene.begin();
        return scene;
    }

    private static void tick(MinecraftServer server) {
        int now = server.getTickCount();
        for (var list : List.copyOf(SCENES.values()))
            for (var s : List.copyOf(list)) {
                if (s.closed) continue;
                try { s.step(now); }
                catch (RuntimeException e) {
                    DestinyGuardians.LOGGER.error("Guardian Rises scene failed; restoring player", e);
                    s.close();
                }
            }
        for (var lock : List.copyOf(LOCKS.values())) lock.tick(now);
        for (var e : List.copyOf(ARRIVAL.entrySet())) {
            // Tower move keeps failing (director retries): never leave the player under black forever.
            if (now - e.getValue() < ARRIVAL_TIMEOUT) continue;
            ARRIVAL.remove(e.getKey());
            var p = server.getPlayerList().getPlayer(e.getKey());
            if (p != null) arrive(p);
        }
        GhostCompanion.tickAll(now);
        RisingAudio.tick(now);
        RisingSubtitles.tick(now);
    }

    private static final Map<ServerLevel, long[]> TIME = new WeakHashMap<>();

    /**
     * Best estimate of the game time the client feeds into post shaders (Globals.GameTime).
     * Fantasy instances created with setShouldTickTime(false) keep the level game time frozen; the client
     * then counts up locally and is re-synced to the frozen value every 20 server ticks, i.e. it sees
     * frozen + (tick % 20). The shader periods are 20 ticks so both cases stay seamless.
     */
    static long clientTime(ServerLevel level) {
        int now = level.getServer().getTickCount();
        long game = level.getGameTime();
        var t = TIME.computeIfAbsent(level, k -> new long[]{game, now, 0});
        if (t[1] != now) {
            t[2] = game == t[0] && now - t[1] == 1 ? 1 : game == t[0] ? t[2] : 0;
            t[0] = game;
            t[1] = now;
        }
        return t[2] == 1 ? game + Math.floorMod(now, 20) : game;
    }

    /** True while this player's view is in cinematic (HUD hidden) mode. */
    static boolean cinematic(ServerPlayer p) {
        var lock = LOCKS.get(p.getUUID());
        return lock != null && lock.player == p && lock.hud;
    }

    static Lock lock(ServerPlayer p) {
        var lock = LOCKS.get(p.getUUID());
        if (lock == null || lock.player != p) {
            if (lock != null) lock.release();
            lock = new Lock(p);
            LOCKS.put(p.getUUID(), lock);
        }
        lock.users++;
        return lock;
    }

    static void unlock(Lock lock) {
        if (--lock.users > 0) return;
        LOCKS.remove(lock.player.getUUID(), lock);
        lock.release();
    }

    /** Sets the client view rotation (and the server's copy so the next movement packet agrees). */
    static void look(ServerPlayer p, float yaw, float pitch) {
        if (p.hasDisconnected()) return;
        p.setYRot(yaw);
        p.setXRot(pitch);
        p.setYHeadRot(yaw);
        p.connection.send(new ClientboundPlayerRotationPacket(yaw, false, pitch, false));
    }

    static float yawTo(Vec3 from, Vec3 to) {
        return (float) Math.toDegrees(-Math.atan2(to.x - from.x, to.z - from.z));
    }

    static float pitchTo(Vec3 from, Vec3 to) {
        Vec3 d = to.subtract(from);
        return (float) Math.toDegrees(-Math.atan2(d.y, Math.sqrt(d.x * d.x + d.z * d.z)));
    }

    static void removePosts(ServerPlayer p, Identifier... ids) {
        if (!p.hasDisconnected()) for (var id : ids) p.removePostEffect(id);
    }

    /** Swaps the owned cinematic grade: removes the other owned grades, then adds {@code id}. */
    static void post(ServerPlayer p, Identifier id) {
        if (p.hasDisconnected()) return;
        for (var other : POSTS) if (!other.equals(id)) p.removePostEffect(other);
        if (id != null && !p.getPostEffects().contains(id)) p.addPostEffect(id);
    }

    // ---------------------------------------------------------------- shared scene/lock infrastructure

    /** A timed, owner-private presentation. done runs exactly once (natural end or early close). */
    abstract static class Scene implements RisingServices.Handle {
        final ServerPlayer player;
        private final Runnable done;
        final int startTick;
        boolean closed, finished, doneRan;

        Scene(ServerPlayer player, Runnable done) {
            this.player = Objects.requireNonNull(player);
            this.done = done == null ? () -> {} : done;
            this.startTick = player.level().getServer().getTickCount();
        }

        abstract void begin();
        /** t = ticks since start. */
        abstract void update(int t, int now);
        /** Restores everything this scene owns. Called once. */
        abstract void restore();
        /** True while this scene keeps the FADE grade on purpose. */
        boolean holdsBlack() { return false; }

        final void step(int now) {
            if (player.hasDisconnected() || player.isRemoved()) { close(); return; }
            update(now - startTick, now);
        }

        /** Marks natural completion and runs done (once). The scene may keep owning state until close. */
        final void complete() {
            finished = true;
            runDone();
        }

        /** Natural completion that also releases everything. */
        final void completeAndClose() {
            complete();
            close();
        }

        private void runDone() {
            if (doneRan) return;
            doneRan = true;
            try { done.run(); }
            catch (RuntimeException e) { DestinyGuardians.LOGGER.error("Guardian Rises done callback failed", e); }
        }

        @Override public final boolean finished() { return finished; }

        @Override public final void close() {
            if (closed) return;
            closed = true;
            var list = SCENES.get(player.getUUID());
            if (list != null) { list.remove(this); if (list.isEmpty()) SCENES.remove(player.getUUID(), list); }
            try { restore(); }
            catch (RuntimeException e) { DestinyGuardians.LOGGER.error("Guardian Rises restore failed", e); }
            runDone();
        }
    }

    /** Movement freeze + optional hidden HUD. Reference counted per player; released exactly once. */
    static final class Lock {
        private static final Identifier SPEED = DestinyGuardians.id("guardian_rises_cinematic_speed");
        private static final Identifier JUMP = DestinyGuardians.id("guardian_rises_cinematic_jump");
        final ServerPlayer player;
        int users;
        boolean hud;
        private boolean released, savedMayfly, mayflyChanged;
        private AttributeModifier speed, jump;
        private Vec3 anchor;
        private Vec3 restorePos;
        private ServerLevel restoreLevel;

        Lock(ServerPlayer player) {
            this.player = player;
            anchor = player.position();
            var s = player.getAttribute(Attributes.MOVEMENT_SPEED);
            if (s != null && !s.hasModifier(SPEED)) {
                speed = new AttributeModifier(SPEED, -1, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
                s.addTransientModifier(speed);
            }
            var j = player.getAttribute(Attributes.JUMP_STRENGTH);
            if (j != null && !j.hasModifier(JUMP)) {
                jump = new AttributeModifier(JUMP, -1, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
                j.addTransientModifier(jump);
            }
            player.setDeltaMovement(Vec3.ZERO);
        }

        /** Moves the anchor (cinematic camera spot). The original spot is restored on release if still in that level. */
        void relocate(Vec3 pos, float yaw, float pitch) {
            if (restorePos == null) { restorePos = player.position(); restoreLevel = player.level(); }
            anchor = pos;
            player.connection.teleport(pos.x, pos.y, pos.z, yaw, pitch);
            player.resetFallDistance();
        }

        void hideHud(boolean value) {
            if (!HIDE_HUD || hud == value || released) return;
            hud = value;
            if (value) {
                if (!mayflyChanged) { savedMayfly = player.getAbilities().mayfly; mayflyChanged = true; }
                // Server-side: no "flying is not enabled" kick while the client hovers as a spectator.
                player.getAbilities().mayfly = true;
                spoof();
            } else unspoof();
        }

        private void spoof() {
            if (player.hasDisconnected()) return;
            player.connection.send(new ClientboundGameEventPacket(ClientboundGameEventPacket.CHANGE_GAME_MODE,
                    GameType.SPECTATOR.getId()));
            var a = new Abilities();
            a.invulnerable = true; a.mayfly = true; a.flying = true;
            a.setFlyingSpeed(0f); a.setWalkingSpeed(0f);
            player.connection.send(new ClientboundPlayerAbilitiesPacket(a));
        }

        private void unspoof() {
            if (player.hasDisconnected()) return;
            player.connection.send(new ClientboundGameEventPacket(ClientboundGameEventPacket.CHANGE_GAME_MODE,
                    player.gameMode.getGameModeForPlayer().getId()));
            if (mayflyChanged) { player.getAbilities().mayfly = savedMayfly; mayflyChanged = false; }
            player.onUpdateAbilities();
            player.connection.teleport(player.getX(), player.getY(), player.getZ(), player.getYRot(), player.getXRot());
        }

        void tick(int now) {
            if (released || player.hasDisconnected()) return;
            // Re-assert: another system may have re-sent real abilities or the client may have drifted.
            if (hud && now % 10 == 0) spoof();
            if (player.position().distanceToSqr(anchor) > .09) {
                player.connection.teleport(anchor.x, anchor.y, anchor.z, player.getYRot(), player.getXRot());
                player.setDeltaMovement(Vec3.ZERO);
            }
            player.resetFallDistance();
        }

        void release() {
            if (released) return;
            released = true;
            var s = player.getAttribute(Attributes.MOVEMENT_SPEED);
            if (s != null && speed != null && s.getModifier(SPEED) == speed) s.removeModifier(SPEED);
            var j = player.getAttribute(Attributes.JUMP_STRENGTH);
            if (j != null && jump != null && j.getModifier(JUMP) == jump) j.removeModifier(JUMP);
            if (hud) { hud = false; unspoof(); }
            if (mayflyChanged) { player.getAbilities().mayfly = savedMayfly; mayflyChanged = false; if (!player.hasDisconnected()) player.onUpdateAbilities(); }
            if (restorePos != null && player.level() == restoreLevel && !player.hasDisconnected() && player.isAlive()) {
                player.connection.teleport(restorePos.x, restorePos.y, restorePos.z, player.getYRot(), player.getXRot());
                player.resetFallDistance();
            }
        }
    }

    /** Ghost flies to a point of interest and sweeps it. No input lock. */
    private static final class GhostScan extends Scene {
        private final Vec3 target;
        private final int ticks;

        GhostScan(ServerPlayer player, Vec3 target, int ticks, Runnable done) {
            super(player, done);
            this.target = target;
            this.ticks = ticks;
        }

        @Override void begin() {
            var g = GhostCompanion.ensure(player, null);
            g.scan(target, null, ticks, 1.4, 2.0, true);
            RisingAudio.sfxAt(player, "scan_loop", target, .9f, 1f, 24f);
        }

        @Override void update(int t, int now) {
            if (t > 0 && t % 80 == 0 && t < ticks - 20) RisingAudio.sfxAt(player, "scan_loop", target, .9f, 1f, 24f);
            if (t >= ticks) completeAndClose();
        }

        @Override void restore() {
            GhostCompanion.existing(player).ifPresent(g -> { if (g.scanning()) g.follow(); });
        }
    }

    /**
     * W300 Vision r1: dummy trackers otherwise sample no light and render near-black even at noon.
     * Bones ending in _glow are full bright; the rest get a readable block-light floor and full sky light.
     */
    static void light(kr.toxicity.model.api.tracker.Tracker tracker, int floor) {
        var body = kr.toxicity.model.api.tracker.TrackerUpdateAction.brightness(floor, 15);
        var glow = kr.toxicity.model.api.tracker.TrackerUpdateAction.brightness(15, 15);
        tracker.update(kr.toxicity.model.api.tracker.TrackerUpdateAction.perBone(
                bone -> bone.name().name().endsWith("_glow") ? glow : body));
    }
}
