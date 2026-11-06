package kim.biryeong.destiny.down;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.tutorial.TutorialGhost;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundAddEntityPacket;
import net.minecraft.network.protocol.game.ClientboundEntityPositionSyncPacket;
import net.minecraft.network.protocol.game.ClientboundRemoveEntitiesPacket;
import net.minecraft.network.protocol.game.ClientboundSetEntityDataPacket;
import net.minecraft.network.protocol.game.ClientboundSetEquipmentPacket;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.stats.Stats;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.decoration.Mannequin;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ResolvableProfile;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.BiFunction;

/**
 * W303 global Guardian Down: Destiny-style death everywhere (survival worlds, campaign, any mode that does not
 * own its own death flow). The killing blow is cancelled, the Guardian's body stays on the ground (a client-side
 * player mannequin, prone), a private camera pulls back over it, the Ghost transmats in above the body and opens its
 * shell, and the Guardian Down HUD shows the killer and the revive ring. Once the Ghost has gathered enough Light the
 * player holds SPACE to be revived where they fell (or SHIFT to return to their respawn point); unsafe spots
 * (void, lava) always return to the respawn point. Nothing drops; the death still counts in statistics.
 *
 * <p>Modes may claim a death through {@link #register(BiFunction)}: return {@link Options#VANILLA} to keep the
 * native death (Crucible owns its own five-second scene), or Options with an {@code onRevive} hook (the campaign
 * restarts its encounter at the checkpoint). Set {@code -Ddestiny.guardianDown=false} to disable globally.
 */
public final class GuardianDown {
    public static final Identifier EFFECT = DestinyGuardians.id("crucible/guardian_down");
    private static final Identifier SFX_DOWN = DestinyGuardians.id("tutorial.ghost.chirp2");
    private static final Identifier SFX_TRANSMAT = DestinyGuardians.id("guardian_rises.sfx.transmat");
    static final int HOLD_TICKS = 12, OUTRO_TICKS = 28, PROTECT_TICKS = 40;
    public static final int REVIVE_MOTION_TICKS = 33;

    /** How a downed Guardian comes back. */
    public record Options(boolean vanilla, int readyTicks, boolean manual, boolean checkpoint, String status,
                          java.util.function.Consumer<ServerPlayer> onRevive, int protectionTicks, boolean breakProtectionOnAttack,
                          boolean externallyScheduled) {
        public Options(boolean vanilla, int readyTicks, boolean manual, boolean checkpoint, String status,
                       java.util.function.Consumer<ServerPlayer> onRevive) {
            this(vanilla, readyTicks, manual, checkpoint, status, onRevive, PROTECT_TICKS, false, false);
        }
        public Options(boolean vanilla, int readyTicks, boolean manual, boolean checkpoint, String status,
                       java.util.function.Consumer<ServerPlayer> onRevive, int protectionTicks, boolean breakProtectionOnAttack) {
            this(vanilla, readyTicks, manual, checkpoint, status, onRevive, protectionTicks, breakProtectionOnAttack, false);
        }
        public Options {
            if (readyTicks < 0 || protectionTicks < 0) throw new IllegalArgumentException("Negative revival timing");
        }
        public static final Options VANILLA = new Options(true, 0, false, false, "", null);
        /** Open world: 5 s for the Ghost, then hold SPACE (revive here) or SHIFT (respawn point). */
        public static final Options WORLD = new Options(false, 100, true, true, "고스트가 당신의 빛을 모으는 중", null);
        public static Options checkpoint(int readyTicks, java.util.function.Consumer<ServerPlayer> onRevive) {
            return new Options(false, readyTicks, true, false, "고스트가 체크포인트로 빛을 되돌리는 중", onRevive);
        }
    }

    private static final List<BiFunction<ServerPlayer, DamageSource, Options>> RULES = new CopyOnWriteArrayList<>();
    private static final Map<UUID, Down> ACTIVE = new HashMap<>();
    private record Protection(ServerPlayer player, int until, boolean breakOnAttack) { }
    private static final Map<UUID, Protection> PROTECTED = new HashMap<>();
    private static final List<TutorialGhost> FADING = new ArrayList<>();
    private static final Map<TutorialGhost, Integer> FADE_UNTIL = new HashMap<>();
    private static boolean initialized;

    private GuardianDown() {}

    public static void register(BiFunction<ServerPlayer, DamageSource, Options> rule) { RULES.add(rule); }

    public static synchronized void init() {
        if (initialized) return;
        initialized = true;
        ServerLivingEntityEvents.ALLOW_DEATH.register((entity, source, amount) ->
                !(entity instanceof ServerPlayer p) || !intercept(p, source));
        ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) ->
                !(entity instanceof ServerPlayer p) || !protectedNow(p));
        ServerTickEvents.END_SERVER_TICK.register(GuardianDown::tick);
        // QA/admin: drive the revive without client input (vision clients cannot send keys while spectating).
        net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback.EVENT.register((dispatcher, access, env) ->
                dispatcher.register(net.minecraft.commands.Commands.literal("guardiandown")
                        .requires(net.minecraft.commands.Commands.hasPermission(net.minecraft.commands.Commands.LEVEL_GAMEMASTERS))
                        .then(net.minecraft.commands.Commands.literal("effects")
                                .then(net.minecraft.commands.Commands.argument("player", net.minecraft.commands.arguments.EntityArgument.player())
                                        .executes(c -> { var t = net.minecraft.commands.arguments.EntityArgument.getPlayer(c, "player");
                                            c.getSource().sendSuccess(() -> Component.literal("post effects: " + t.getPostEffects()), false); return 1; })))
                        .then(net.minecraft.commands.Commands.literal("revive")
                                .then(net.minecraft.commands.Commands.argument("player", net.minecraft.commands.arguments.EntityArgument.player())
                                        .executes(c -> qaRevive(net.minecraft.commands.arguments.EntityArgument.getPlayer(c, "player"), false))
                                        .then(net.minecraft.commands.Commands.literal("spawn")
                                                .executes(c -> qaRevive(net.minecraft.commands.arguments.EntityArgument.getPlayer(c, "player"), true)))))));
        // A downed player saved by autosave/crash keeps SPECTATOR in its data: recover on next join.
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            ServerPlayer p = handler.getPlayer();
            // Post effects are saved with the player: a down interrupted by disconnect/crash/stop leaves the tint on.
            if (!ACTIVE.containsKey(p.getUUID()) && p.getPostEffects().contains(EFFECT)) p.removePostEffect(EFFECT);
            if (p.entityTags().contains(DOWN_TAG) && !ACTIVE.containsKey(p.getUUID())) {
                p.removeTag(DOWN_TAG);
                if (p.gameMode.getGameModeForPlayer() == GameType.SPECTATOR) {
                    GameType fallback = server.getDefaultGameType();
                    p.setGameMode(fallback == GameType.SPECTATOR ? GameType.SURVIVAL : fallback);
                }
                if (p.getY() < p.level().getMinY()) {
                    // JOIN precedes level registration; a cross-level teleport here double-registers the player.
                    // server.execute would run inline on the server thread; queue for the next tick.
                    PENDING_RESCUE.put(p.getUUID(), p);
                }
                DestinyGuardians.LOGGER.info("[GuardianDown] recovered stale downed state for {}", p.getScoreboardName());
            }
        });
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            PROTECTED.remove(handler.getPlayer().getUUID());
            var d = ACTIVE.get(handler.getPlayer().getUUID());
            if (d != null) d.end(false);
        });
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            for (var d : List.copyOf(ACTIVE.values())) d.end(false);
            for (var g : FADING) g.destroy();
            FADING.clear(); FADE_UNTIL.clear(); PROTECTED.clear();
        });
    }

    static final String DOWN_TAG = "destiny_guardian_down";

    private static final Map<UUID, GuardianDownHud> EXTERNAL = new HashMap<>();

    /** Same Guardian Down HUD for a mode that owns its own death flow (Crucible: automatic team respawn). */
    public static void externalHud(ServerPlayer p, int age, int remaining, int total, String killer, String status) {
        var hud = EXTERNAL.computeIfAbsent(p.getUUID(), k -> new GuardianDownHud(p,
                new GuardianDownHud.Killer(Component.literal(killer), "gd_ghost")));
        float charge = total <= 0 ? 1 : 1 - Math.max(0, remaining) / (float) total;
        hud.render(new GuardianDownHud.Frame(age, charge, 0, false, false, false, (remaining + 19) / 20, 0, status));
    }

    public static void clearExternalHud(ServerPlayer p) {
        var hud = EXTERNAL.remove(p.getUUID());
        if (hud != null) hud.clear();
    }

    private static int qaRevive(ServerPlayer p, boolean spawn) {
        var d = ACTIVE.get(p.getUUID());
        if (d == null) return 0;
        d.revive(p.level().getServer().getTickCount(), spawn);
        return 1;
    }

    public static boolean active(ServerPlayer p) {
        var d = ACTIVE.get(p.getUUID());
        return d != null && d.player == p;
    }

    public static boolean materializing(ServerPlayer player) {
        Down down = ACTIVE.get(player.getUUID());
        return down != null && down.player == player && down.motionAt >= 0 && player.level() == down.level;
    }

    /** Called after vanilla's thread handoff, before applying incoming movement. */
    public static boolean holdReviveMovement(ServerPlayer player) {
        Down down = ACTIVE.get(player.getUUID());
        if (!materializing(player)) return false;
        down.holdMotion();
        return true;
    }

    public static void progressOwned(ServerPlayer player, Options owner, UUID helper, int heldTicks, java.util.Collection<ServerPlayer> audience) {
        Down down = owned(player, owner);
        if (down == null || down.revivingAt >= 0) return;
        down.progress(helper, heldTicks, audience);
    }

    /** Scoped gameplay revival; the activity retains the exact Options object supplied by its rule. */
    public static boolean reviveOwned(ServerPlayer player, Options owner) {
        Down down = owned(player, owner);
        if (down == null || down.revivingAt >= 0) return false;
        down.revive(player.level().getServer().getTickCount(), false);
        return true;
    }

    /** Ends the owned camera without invoking a successful revival callback. Teleport afterwards. */
    public static boolean cancelOwned(ServerPlayer player, Options owner) {
        Down down = owned(player, owner);
        if (down == null) return false;
        down.end(false);
        return true;
    }

    /** Wipe overlay handoff keeps the exact activity-owned camera/input state without a revive callback. */
    public static boolean suppressHudOwned(ServerPlayer player, Options owner, boolean hidden) {
        Down down = owned(player, owner);
        if (down == null) return false;
        down.presentationHidden = hidden;
        if (hidden) down.hud.clear();
        return true;
    }

    /** Activity kill boundaries bypass temporary damage immunity, but retain the owned revival policy.
     * The activity supplies a supported body location so allies can still revive a fallen player. */
    public static boolean fallOwned(ServerPlayer player, Options owner, Vec3 body) {
        if (active(player) || !resumeOwned(player, owner, body)) return false;
        player.awardStat(Stats.DEATHS);
        player.awardStat(Stats.CUSTOM.get(Stats.TIME_SINCE_DEATH), 0);
        player.getCombatTracker().recheckStatus();
        player.setHealth(player.getMaxHealth());
        player.removeAllEffects();
        return true;
    }

    /** Rebuild an activity-owned down scene without recording another death or invoking activity rules. */
    public static boolean resumeOwned(ServerPlayer player, Options owner, Vec3 body) {
        return resumeOwned(player, owner, body, owner == null ? 0 : owner.readyTicks());
    }

    public static boolean resumeOwned(ServerPlayer player, Options owner, Vec3 body, int remainingTicks) {
        if (!player.level().getServer().isSameThread()) throw new IllegalStateException("Revival requires server thread");
        if (owner == null || owner.vanilla() || !owner.externallyScheduled() || remainingTicks < 0
                || body == null || !Double.isFinite(body.x) || !Double.isFinite(body.y) || !Double.isFinite(body.z)
                || player.hasDisconnected() || player.isRemoved() || !player.isAlive()) return false;
        Down current = ACTIVE.get(player.getUUID());
        if (current != null) return current.player == player && current.options == owner && !current.ended;
        var down = new Down(player, player.level(), body, player.getYRot(), owner,
                new GuardianDownHud.Killer(Component.literal(owner.status()), "gd_icon_hostile"),
                player.level().getServer().getTickCount(), false);
        down.readyAt = (long) down.started + remainingTicks;
        ACTIVE.put(player.getUUID(), down);
        PROTECTED.remove(player.getUUID());
        try {
            player.clearFire(); player.resetFallDistance(); player.setDeltaMovement(Vec3.ZERO);
            player.stopUsingItem(); player.closeContainer();
            down.begin();
            return true;
        } catch (RuntimeException error) {
            down.end(false);
            DestinyGuardians.LOGGER.error("Guardian Down resume failed", error);
            return false;
        }
    }

    public static java.util.Optional<Vec3> bodyOwned(ServerPlayer player, Options owner) {
        Down down = owned(player, owner);
        return down == null ? java.util.Optional.empty() : java.util.Optional.of(down.body);
    }

    private static Down owned(ServerPlayer player, Options owner) {
        if (!player.level().getServer().isSameThread()) throw new IllegalStateException("Revival requires server thread");
        Down down = ACTIVE.get(player.getUUID());
        return owner != null && down != null && down.player == player && down.options == owner && !down.ended
                ? down : null;
    }

    /** Call for an accepted attack, including a shot which misses. */
    public static void attacked(ServerPlayer player) {
        Protection protection = PROTECTED.get(player.getUUID());
        if (protection != null && protection.player == player && protection.breakOnAttack)
            PROTECTED.remove(player.getUUID());
    }

    /** The owned death camera may not be swapped by sneak/spectator clicks. */
    public static boolean blocksCameraChange(ServerPlayer p, Entity requested) {
        var d = ACTIVE.get(p.getUUID());
        return d != null && d.player == p && requested != (d.motionAt >= 0 ? p : d.camera);
    }

    static boolean enabled() { return Boolean.parseBoolean(System.getProperty("destiny.guardianDown", "true")); }

    private static boolean protectedNow(ServerPlayer p) {
        if (active(p)) return true;
        Protection protection = PROTECTED.get(p.getUUID());
        if (protection == null) return false;
        if (protection.player == p && p.level().getServer().getTickCount() < protection.until) return true;
        PROTECTED.remove(p.getUUID());
        return false;
    }

    private static boolean intercept(ServerPlayer p, DamageSource source) {
        if (!enabled() || p.hasDisconnected() || p.isSpectator() || p.isCreative()) return false;
        if (active(p)) { p.setHealth(1); return true; }
        Options options = Options.WORLD;
        for (var rule : RULES) {
            Options claimed = rule.apply(p, source);
            if (claimed != null) { options = claimed; break; }
        }
        if (options.vanilla()) return false;
        try {
            start(p, source, options);
            return true;
        } catch (RuntimeException error) {
            DestinyGuardians.LOGGER.error("Guardian Down start failed; using vanilla death", error);
            var d = ACTIVE.remove(p.getUUID());
            if (d != null) d.cleanupVisuals();
            return false;
        }
    }

    // -------------------------------------------------------------------------------------------- lifecycle

    private static void start(ServerPlayer p, DamageSource source, Options options) {
        ServerLevel level = p.level();
        int now = level.getServer().getTickCount();
        Vec3 body = p.position();
        boolean voidDeath = body.y < level.getMinY() - 4 || source.is(net.minecraft.tags.DamageTypeTags.BYPASSES_INVULNERABILITY)
                && body.y < level.getMinY() + 1;
        if (voidDeath) {
            var spawn = respawnPoint(p);
            body = spawn != null ? spawn : new Vec3(body.x, level.getMinY() + 64, body.z);
        } else {
            // Killed mid-air (knockback, ledge): lay the body on the floor below so revive-in-place is safe.
            var floor = ground(level, body);
            if (floor != null) body = floor;
        }
        var killer = describe(source);
        // Native death bookkeeping that does not depend on dropping/respawning.
        p.awardStat(Stats.DEATHS);
        p.awardStat(Stats.CUSTOM.get(Stats.TIME_SINCE_DEATH), 0);
        p.getCombatTracker().recheckStatus();
        // A mode that revives at its own checkpoint keeps its session state; open-world deaths run the same
        // cleanup listeners a native death would (weapons, abilities, HUDs, screens).
        if (options.onRevive() == null) ServerLivingEntityEvents.AFTER_DEATH.invoker().afterDeath(p, source);
        p.setHealth(p.getMaxHealth());
        p.clearFire();
        p.removeAllEffects();
        p.resetFallDistance();
        p.setDeltaMovement(Vec3.ZERO);
        p.stopUsingItem();
        p.closeContainer();
        var d = new Down(p, level, body, p.getYRot(), options, killer, now, voidDeath || unsafe(level, body));
        ACTIVE.put(p.getUUID(), d);
        d.begin();
        DestinyGuardians.LOGGER.info("[GuardianDown] {} down at {} by {} ({}), ready in {} ticks", p.getScoreboardName(),
                p.blockPosition(), source.getMsgId(), killer.name().getString(), options.readyTicks());
    }

    private static final Map<UUID, ServerPlayer> PENDING_RESCUE = new HashMap<>();
    private static void tick(MinecraftServer server) {
        for (var p : List.copyOf(PENDING_RESCUE.values())) {
            if (p.hasDisconnected() || p.isRemoved()) { PENDING_RESCUE.remove(p.getUUID(), p); continue; }
            if (p.level().getEntity(p.getId()) != p) continue;
            PENDING_RESCUE.remove(p.getUUID(), p);
            var spawn = server.overworld().getRespawnData().pos();
            p.teleportTo(server.overworld(), spawn.getX() + .5, spawn.getY(), spawn.getZ() + .5, Set.of(), p.getYRot(), 0, true);
        }
        int now = server.getTickCount();
        for (var d : List.copyOf(ACTIVE.values())) {
            try { d.tick(now); }
            catch (RuntimeException error) {
                DestinyGuardians.LOGGER.error("Guardian Down tick failed; reviving", error);
                d.revive(now, false);
            }
        }
        for (var g : List.copyOf(FADING)) {
            g.tick(now);
            if (now >= FADE_UNTIL.getOrDefault(g, 0)) { g.destroy(); FADING.remove(g); FADE_UNTIL.remove(g); }
        }
    }

    // -------------------------------------------------------------------------------------------- helpers

    private static GuardianDownHud.Killer describe(DamageSource source) {
        Entity e = source.getEntity();
        if (e instanceof net.minecraft.world.entity.projectile.Projectile proj && proj.getOwner() != null) e = proj.getOwner();
        if (e instanceof LivingEntity living) {
            Component name = living.getDisplayName();
            boolean fallen = living.getClass().getName().contains(".campaign.fallen.");
            boolean guardian = living instanceof ServerPlayer;
            return new GuardianDownHud.Killer(name, fallen ? "gd_icon_fallen" : guardian ? "gd_ghost" : "gd_icon_hostile");
        }
        String id = source.getMsgId();
        String label = switch (id) {
            case "fall", "flyIntoWall" -> "낙하";
            case "lava", "inFire", "onFire", "hotFloor", "campfire" -> "화염";
            case "drown" -> "익사";
            case "outOfWorld", "outsideBorder" -> "공허";
            case "explosion", "explosion.player", "fireworks", "badRespawnPoint" -> "폭발";
            case "starve" -> "굶주림";
            case "freeze" -> "동사";
            case "lightningBolt" -> "번개";
            case "cactus", "sweetBerryBush", "stalagmite", "fallingStalactite", "fallingBlock", "anvil" -> "환경 피해";
            case "magic", "indirectMagic", "wither" -> "어둠의 힘";
            case "genericKill", "kill" -> "알 수 없는 힘";
            default -> "환경 피해";
        };
        return new GuardianDownHud.Killer(Component.literal(label), "gd_icon_hazard");
    }

    /** Nearest standable spot in the body's column (feet+head clear, solid below), searching 2 up / 8 down. */
    static Vec3 ground(ServerLevel level, Vec3 at) {
        var base = net.minecraft.core.BlockPos.containing(at);
        // Prefer the floor at or below the feet; only then step up (body sunk into a slab/stair).
        for (int dy : new int[]{0, -1, -2, -3, -4, -5, -6, -7, -8, 1, 2}) {
            var feet = base.offset(0, dy, 0);
            if (feet.getY() <= level.getMinY()) continue;
            var floor = feet.below();
            var floorShape = level.getBlockState(floor).getCollisionShape(level, floor);
            if (floorShape.isEmpty() || !level.getFluidState(floor).isEmpty() && level.getFluidState(floor).is(net.minecraft.tags.FluidTags.LAVA)) continue;
            if (!level.getBlockState(feet).getCollisionShape(level, feet).isEmpty()) continue;
            if (!level.getBlockState(feet.above()).getCollisionShape(level, feet.above()).isEmpty()) continue;
            if (level.getFluidState(feet).is(net.minecraft.tags.FluidTags.LAVA)) continue;
            return new Vec3(at.x, floor.getY() + floorShape.max(net.minecraft.core.Direction.Axis.Y), at.z);
        }
        return null;
    }

    private static boolean unsafe(ServerLevel level, Vec3 at) {
        var pos = net.minecraft.core.BlockPos.containing(at);
        for (int dy = 0; dy >= -1; dy--) {
            var fluid = level.getFluidState(pos.offset(0, dy, 0));
            if (fluid.is(net.minecraft.tags.FluidTags.LAVA)) return true;
        }
        for (int dy = 0; dy <= 6; dy++)
            if (!level.getBlockState(pos.below(dy)).getCollisionShape(level, pos.below(dy)).isEmpty()
                    || !level.getFluidState(pos.below(dy)).isEmpty()) return false;
        return true;
    }

    private static Vec3 respawnPoint(ServerPlayer p) {
        try {
            var t = p.findRespawnPositionAndUseSpawnBlock(false, net.minecraft.world.level.portal.TeleportTransition.DO_NOTHING);
            return t.newLevel() == p.level() ? t.position() : null;
        } catch (RuntimeException e) { return null; }
    }

    private static void sound(ServerPlayer p, Identifier id, Vec3 at, float volume, float pitch) {
        if (p.hasDisconnected()) return;
        p.connection.send(new ClientboundSoundPacket(Holder.direct(SoundEvent.createVariableRangeEvent(id)),
                SoundSource.PLAYERS, at.x, at.y, at.z, volume, pitch, p.getRandom().nextLong()));
    }

    // -------------------------------------------------------------------------------------------- one downed Guardian

    private static final class Down {
        final ServerPlayer player;
        final ServerLevel level;
        final Vec3 body;
        final float yaw;
        final Options options;
        final int started;
        long readyAt;
        final boolean forceRespawnPoint;
        final GameType previousMode;
        final Display.ItemDisplay camera;
        final Mannequin corpse;
        final Set<ServerPlayer> viewers = new java.util.HashSet<>();
        final GuardianDownHud hud;
        TutorialGhost ghost;
        boolean effect, ended;
        int hold, checkpointHold, revivingAt = -1;
        boolean toRespawnPoint;
        boolean presentationHidden;
        int motionAt = -1;
        Vec3 motionAnchor;
        FireteamReviveAudio progressAudio;
        UUID progressHelper;
        java.util.List<ServerPlayer> rescueAudience = List.of();

        void progress(UUID helper, int heldTicks, java.util.Collection<ServerPlayer> audience) {
            rescueAudience = List.copyOf(audience);
            if (!java.util.Objects.equals(helper, progressHelper)) {
                if (motionAt >= 0) cancelPreview();
                stopProgress();
                progressHelper = helper;
                if (helper != null) progressAudio = new FireteamReviveAudio(player, audience, body);
            }
            // Start the 1.6 s source clip + one entry tick inside the 3.024 s rescue sound.
            // The activity still requires the entire uninterrupted ally hold before authorizing success.
            if (helper != null && heldTicks >= OUTRO_TICKS + 1 && motionAt < 0)
                materialize(level.getServer().getTickCount());
        }
        void cancelPreview() {
            kim.biryeong.destiny.fx.PlayerAnimations.stop(player);
            motionAt = -1; motionAnchor = null;
            player.setGameMode(GameType.SPECTATOR);
            Vec3 at = cameraPos(level.getServer().getTickCount() - started);
            player.teleportTo(level, at.x, at.y, at.z, Set.of(), camYaw(at), camPitch(at), true);
            player.setCamera(camera);
            for (var other : level.players())
                if (other == player || other.distanceToSqr(body) < 96 * 96) showCorpse(other);
            ghost = new TutorialGhost(player, body.add(0, 1.15, 0));
            ghost.anchor(body.add(0, 1.15, 0)); ghost.transmat(6); ghost.deploy(at);
            effect = player.addPostEffect(EFFECT);
        }
        void fadeGhost() {
            if (ghost == null) return;
            ghost.vanish(4); FADING.add(ghost);
            FADE_UNTIL.put(ghost, level.getServer().getTickCount() + 6); ghost = null;
        }
        void rescueSound(Identifier event, Vec3 at, float volume, float pitch) {
            var audience = new java.util.LinkedHashSet<>(rescueAudience); audience.add(player);
            for (var listener : audience) if (!listener.hasDisconnected() && listener.level() == level)
                sound(listener, event, listener == player ? listener.getEyePosition() : at, volume, pitch);
        }
        void stopProgress() {
            if (progressAudio != null) progressAudio.close();
            progressAudio = null; progressHelper = null;
        }
        void holdMotion() {
            player.setPos(motionAnchor);
            player.setYRot(yaw); player.setXRot(0); player.setYHeadRot(yaw); player.setYBodyRot(yaw);
            player.setDeltaMovement(Vec3.ZERO); player.resetFallDistance();
        }

        float orbit;

        Down(ServerPlayer player, ServerLevel level, Vec3 body, float yaw, Options options,
             GuardianDownHud.Killer killer, int now, boolean forceRespawnPoint) {
            this.player = player;
            this.level = level;
            this.body = body;
            this.yaw = yaw;
            this.options = options;
            this.started = now;
            this.readyAt = (long) now + options.readyTicks();
            this.forceRespawnPoint = forceRespawnPoint;
            this.previousMode = player.gameMode.getGameModeForPlayer();
            this.hud = new GuardianDownHud(player, killer);
            camera = new Display.ItemDisplay(EntityTypes.ITEM_DISPLAY, level);
            camera.setNoGravity(true);
            camera.setSilent(true);
            corpse = new Mannequin(EntityTypes.MANNEQUIN, level);
            corpse.setComponent(DataComponents.PROFILE, ResolvableProfile.createResolved(player.getGameProfile()));
            corpse.setPos(body.x, body.y, body.z);
            corpse.setYRot(yaw); corpse.setYHeadRot(yaw); corpse.setYBodyRot(yaw);
            corpse.setPose(Pose.SWIMMING);
            corpse.setNoGravity(true);
            hideDescription(corpse);
        }

        Vec3 ghostAt() { return body.add(0, 1.15 + Math.sin((level.getServer().getTickCount() - started) / 14.0) * .05, 0); }

        void begin() {
            player.addTag(DOWN_TAG);
            player.sendOverlayMessage(Component.empty());
            player.setGameMode(GameType.SPECTATOR);
            Vec3 at = cameraPos(0);
            if (!player.teleportTo(level, at.x, at.y, at.z, Set.of(), camYaw(at), camPitch(at), false))
                throw new IllegalStateException("Guardian Down camera transfer refused");
            player.setDeltaMovement(Vec3.ZERO);
            camera.setPos(at);
            camera.setYRot(camYaw(at));
            camera.setXRot(camPitch(at));
            player.connection.send(new ClientboundAddEntityPacket(camera.getId(), camera.getUUID(), at.x, at.y, at.z,
                    camera.getXRot(), camera.getYRot(), camera.getType(), 0, Vec3.ZERO, camera.getYRot()));
            var data = camera.getEntityData().getNonDefaultValues();
            if (data != null) player.connection.send(new ClientboundSetEntityDataPacket(camera.getId(), data));
            player.setCamera(camera);
            for (var other : level.players())
                if (other == player || other.distanceToSqr(body) < 96 * 96) showCorpse(other);
            ghost = new TutorialGhost(player, body.add(0, 1.15, 0));
            ghost.anchor(body.add(0, 1.15, 0));
            ghost.transmat(10);
            ghost.deploy(at);
            effect = player.addPostEffect(EFFECT);
            sound(player, SFX_DOWN, body, .8f, .8f);
            sound(player, SFX_TRANSMAT, body, .6f, 1.2f);
            render(level.getServer().getTickCount());
        }

        void showCorpse(ServerPlayer viewer) {
            if (viewer.hasDisconnected() || !viewers.add(viewer)) return;
            viewer.connection.send(new ClientboundAddEntityPacket(corpse.getId(), corpse.getUUID(), body.x, body.y, body.z,
                    0, yaw, corpse.getType(), 0, Vec3.ZERO, yaw));
            var data = corpse.getEntityData().getNonDefaultValues();
            if (data != null) viewer.connection.send(new ClientboundSetEntityDataPacket(corpse.getId(), data));
            var gear = new ArrayList<com.mojang.datafixers.util.Pair<EquipmentSlot, ItemStack>>();
            for (var slot : new EquipmentSlot[]{EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET})
                gear.add(com.mojang.datafixers.util.Pair.of(slot, player.getItemBySlot(slot).copy()));
            viewer.connection.send(new ClientboundSetEquipmentPacket(corpse.getId(), gear));
        }

        /** Pulls back from 2.6 to 4.4 blocks and rises over two seconds, then drifts slowly around the body. */
        /** Base orbit offset and a top-down blend, chosen once so tight rooms never put the lens in the Ghost. */
        float baseOffset = Float.NaN;
        double overhead;

        void chooseFraming() {
            Vec3 target = body.add(0, .7, 0);
            float best = 0; double bestRoom = -1;
            for (float off : new float[]{0, 40, -40, 80, -80, 125, -125, 180}) {
                double angle = Math.toRadians(yaw + 180 + off);
                Vec3 desired = target.add(-Math.sin(angle) * 4.4, 2.8, Math.cos(angle) * 4.4);
                double room = clip(target, desired).distanceTo(target) - Math.abs(off) / 600.0;
                if (room > bestRoom + .05) { bestRoom = room; best = off; }
            }
            baseOffset = best;
            // Under ~2.6 blocks of clearance a shoulder shot sits inside the Ghost: rise to a high overhead view.
            overhead = bestRoom >= 2.6 ? 0 : Math.min(1, (2.6 - bestRoom) / 1.4);
        }

        Vec3 cameraPos(int age) {
            if (Float.isNaN(baseOffset)) chooseFraming();
            float u = Math.min(1f, age / 40f);
            float e = 1 - (1 - u) * (1 - u) * (1 - u);
            double dist = (2.6 + 1.8 * e) * (1 - .75 * overhead), height = 1.5 + 1.3 * e + 1.6 * overhead;
            double angle = Math.toRadians(yaw + 180 + baseOffset + 28 * e + orbit * (1 - overhead));
            Vec3 target = body.add(0, .7, 0);
            Vec3 desired = target.add(-Math.sin(angle) * dist, height, Math.cos(angle) * dist);
            Vec3 at = clip(target, desired);
            // Never closer than the shell's opened radius to the Ghost.
            Vec3 ghost = ghostAt();
            if (at.distanceTo(ghost) < 1.35) {
                Vec3 up = clip(target, target.add(0, 3.2, 0));
                if (up.distanceTo(ghost) > at.distanceTo(ghost)) at = up;
            }
            return at;
        }

        Vec3 clip(Vec3 origin, Vec3 desired) {
            Vec3 delta = desired.subtract(origin);
            double fraction = 1;
            for (double x : new double[]{-.2, 0, .2}) for (double y : new double[]{-.2, 0, .2}) {
                Vec3 offset = new Vec3(x, y, 0);
                var hit = level.clip(new ClipContext(origin.add(offset), desired.add(offset),
                        ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
                if (hit.getType() != HitResult.Type.MISS)
                    fraction = Math.min(fraction, Math.max(.15, (hit.getLocation().distanceTo(origin.add(offset)) - .25) / delta.length()));
            }
            return origin.add(delta.scale(fraction));
        }

        float camYaw(Vec3 at) {
            Vec3 look = body.add(0, .9, 0).subtract(at);
            return (float) Math.toDegrees(Math.atan2(-look.x, look.z));
        }

        float camPitch(Vec3 at) {
            Vec3 look = body.add(0, .9, 0).subtract(at);
            return (float) -Math.toDegrees(Math.atan2(look.y, look.horizontalDistance()));
        }

        void tick(int now) {
            if (ended) return;
            if (player.hasDisconnected() || player.isRemoved() || player.level() != level) { end(false); return; }
            if (motionAt >= 0) {
                holdMotion();
                if (revivingAt >= 0 && now - motionAt >= REVIVE_MOTION_TICKS) finish(now);
                return;
            }
            int age = now - started;
            if (age > 40) orbit += .12f;
            Vec3 at = cameraPos(age);
            if (age <= 44 || (age & 1) == 0) {
                camera.setPos(at);
                camera.setYRot(camYaw(at));
                camera.setXRot(camPitch(at));
                player.connection.send(ClientboundEntityPositionSyncPacket.of(camera));
                ghost.deploy(at);
            }
            if (player.getCamera() != camera) player.setCamera(camera);
            ghost.anchor(ghostAt());
            ghost.tick(now);
            if ((age % 20) == 0) for (var other : level.players())
                if (other != player && other.distanceToSqr(body) < 96 * 96) showCorpse(other);
            if (revivingAt >= 0) {
                if (now - revivingAt >= OUTRO_TICKS) materialize(now);
                else outro(now);
                return;
            }
            boolean ready = now >= readyAt;
            if (age % 4 == 0 && !ready) level.sendParticles(player, ParticleTypes.END_ROD, true, false,
                    body.x, body.y + 1.15, body.z, 2, .12, .12, .12, .01);
            if (ready && now == readyAt) sound(player, DestinyGuardians.id("tutorial.ghost.chirp1"), body, .7f, 1.1f);
            if (options.externallyScheduled()) {
                // Activity policy owns self/ally/wipe timing; this object only presents and executes revival.
            } else if (options.manual()) {
                var in = player.getLastClientInput();
                if (ready && in.jump()) hold++; else hold = Math.max(0, hold - 2);
                if (ready && options.checkpoint() && in.shift()) checkpointHold++; else checkpointHold = Math.max(0, checkpointHold - 2);
                if (hold >= HOLD_TICKS) { revive(now, false); return; }
                if (checkpointHold >= HOLD_TICKS + 8) { revive(now, true); return; }
            } else if (ready) { revive(now, false); return; }
            if ((age & 1) == 0) render(now);
        }

        void render(int now) {
            if (presentationHidden) { hud.clear(); return; }
            int age = now - started;
            float charge = options.readyTicks() <= 0 ? 1 : Math.min(1f, age / (float) options.readyTicks());
            boolean ready = now >= readyAt;
            hud.render(new GuardianDownHud.Frame(age, charge, Math.min(1f, hold / (float) HOLD_TICKS), ready,
                    options.manual(), options.checkpoint() && !forceRespawnPoint && options.onRevive() == null,
                    (int) Math.max(0, (readyAt - now + 19) / 20), Math.min(1f, checkpointHold / (float) (HOLD_TICKS + 8)),
                    ready ? "고스트가 준비됐습니다" : options.status()));
        }

        void revive(int now, boolean respawnPoint) {
            if (revivingAt >= 0) return;
            revivingAt = now;
            toRespawnPoint = respawnPoint || forceRespawnPoint;
            if (motionAt >= 0) {
                if (now - motionAt >= REVIVE_MOTION_TICKS) finish(now);
                return;
            }
            stopProgress();
            progressAudio = new FireteamReviveAudio(player, rescueAudience, body);
            ghost.open(1.6f);
            hud.revived();
            outro(now);
        }

        /** Light gathers from the Ghost into the body before the Guardian reforms. */
        void outro(int now) {
            float u = (now - revivingAt) / (float) OUTRO_TICKS;
            Vec3 from = body.add(0, 1.15, 0);
            for (int i = 0; i < 4; i++) {
                double t = Math.min(1, u + i * .07);
                Vec3 at = from.lerp(body.add(0, .3, 0), t);
                level.sendParticles(ParticleTypes.END_ROD, at.x, at.y, at.z, 1, .08, .08, .08, .005);
            }
            level.sendParticles(ParticleTypes.GLOW, body.x, body.y + .2, body.z, 3, .35, .05, .35, 0);
        }

        void materialize(int now) {
            Vec3 target = body;
            float faceYaw = yaw;
            if (toRespawnPoint && options.onRevive() == null) {
                var spawn = respawnPoint(player);
                if (spawn != null) target = spawn;
            }
            motionAnchor = target;
            motionAt = now;
            fadeGhost();
            player.setCamera(player);
            player.connection.send(new net.minecraft.network.protocol.game.ClientboundSetCameraPacket(camera));
            hud.clear();
            if (effect) { player.removePostEffect(EFFECT); effect = false; }
            for (var viewer : viewers) if (!viewer.hasDisconnected())
                viewer.connection.send(new ClientboundRemoveEntitiesPacket(corpse.getId()));
            viewers.clear();
            player.setGameMode(previousMode == GameType.SPECTATOR ? GameType.SURVIVAL : previousMode);
            if (options.onRevive() == null) {
                if (!toRespawnPoint) {
                    var floor = ground(level, target);
                    if (floor != null) target = floor;
                    else { var spawn = respawnPoint(player); if (spawn != null) target = spawn; }
                }
                player.teleportTo(level, target.x, target.y, target.z, Set.of(), faceYaw, 0, true);
            } else {
                player.teleportTo(level, body.x, body.y, body.z, Set.of(), faceYaw, 0, true);

            }
            player.setHealth(player.getMaxHealth());
            player.setDeltaMovement(Vec3.ZERO);
            player.resetFallDistance();
            motionAnchor = player.position();
            kim.biryeong.destiny.fx.PlayerAnimations.stop(player);
            kim.biryeong.destiny.fx.PlayerAnimations.play(player, "h15_revive_combat");
            holdMotion();
        }

        void finish(int now) {
            end(true);
            player.teleportTo(level, motionAnchor.x, motionAnchor.y, motionAnchor.z, Set.of(), yaw, 0, true);
            if (options.onRevive() != null) options.onRevive().accept(player);
            FireteamReviveAudio.complete(player, rescueAudience);
            PROTECTED.put(player.getUUID(), new Protection(player, now + options.protectionTicks(), options.breakProtectionOnAttack()));
            Vec3 at = player.position();
            level.sendParticles(net.minecraft.core.particles.ColorParticleOption.create(ParticleTypes.FLASH, 0xFFE6F6FF), at.x, at.y + 1, at.z, 1, 0, 0, 0, 0);
            level.sendParticles(ParticleTypes.END_ROD, at.x, at.y + 1, at.z, 40, .3, .9, .3, .06);
            level.sendParticles(ParticleTypes.GLOW, at.x, at.y + .1, at.z, 24, .6, .02, .6, 0);
            DestinyGuardians.LOGGER.info("[GuardianDown] {} revived at {} ({})", player.getScoreboardName(),
                    player.blockPosition(), toRespawnPoint ? "respawn point" : options.onRevive() != null ? "checkpoint" : "in place");
        }

        void end(boolean revived) {
            if (ended) return;
            ended = true;
            player.removeTag(DOWN_TAG);
            ACTIVE.remove(player.getUUID(), this);
            cleanupVisuals();
            if (!revived && !player.hasDisconnected()) {
                // Disconnect/stop: leave the player alive at the body so the next join is consistent.
                player.setGameMode(previousMode == GameType.SPECTATOR ? GameType.SURVIVAL : previousMode);
            } else if (!revived) {
                player.setGameMode(previousMode == GameType.SPECTATOR ? GameType.SURVIVAL : previousMode);
                player.teleportTo(level, body.x, body.y, body.z, Set.of(), yaw, 0, true);
            }
        }

        void cleanupVisuals() {
            stopProgress();
            if (motionAt >= 0) kim.biryeong.destiny.fx.PlayerAnimations.stop(player);
            hud.clear();
            if (effect || player.getPostEffects().contains(EFFECT)) { player.removePostEffect(EFFECT); effect = false; }
            if (motionAt >= 0 && !player.hasDisconnected())
                player.connection.send(new net.minecraft.network.protocol.game.ClientboundSetCameraPacket(player));
            if (player.getCamera() == camera) {
                ACTIVE.remove(player.getUUID());
                player.setCamera(player);
            }
            for (var v : viewers) if (!v.hasDisconnected())
                v.connection.send(new ClientboundRemoveEntitiesPacket(corpse.getId()));
            viewers.clear();
            if (!player.hasDisconnected()) player.connection.send(new ClientboundRemoveEntitiesPacket(camera.getId()));
            camera.discard();
            corpse.discard();
            if (ghost != null) {
                ghost.vanish(10);
                FADING.add(ghost);
                FADE_UNTIL.put(ghost, level.getServer().getTickCount() + 12);
                ghost = null;
            }
        }
    }

    private static void hideDescription(Mannequin m) {
        try {
            var method = Mannequin.class.getDeclaredMethod("setHideDescription", boolean.class);
            method.setAccessible(true);
            method.invoke(m, true);
        } catch (ReflectiveOperationException | RuntimeException e) {
            DestinyGuardians.LOGGER.debug("Mannequin description could not be hidden", e);
        }
    }
}
