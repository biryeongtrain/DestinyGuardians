package kim.biryeong.destiny.campaign;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.campaign.GuardianRisesProgress.Stage;
import kim.biryeong.destiny.campaign.RisingServices.Handle;
import kim.biryeong.destiny.campaign.RisingServices.Marker;
import kim.biryeong.destiny.campaign.RisingServices.Zone;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.CharacterLoadouts;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.inventory.WeaponScreen;
import kim.biryeong.destiny.sound.ActivityMusic;
import kim.biryeong.destiny.tutorial.Tutorial;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.*;

/**
 * Entry flow and instance director for "A Guardian Rises" (W300). Replaces the first-time tutorial when
 * {@code -Ddestiny.guardianRises} is not {@code false}. One private Fantasy instance per Guardian; zones are
 * prepared under a shared tick budget, the player only enters a READY instance, and every world callback is
 * checked against the run's progress token. Depends only on {@link RisingServices}; absent services fail
 * safely with a message (the run waits, an operator can {@code /destiny rising skip|abort}).
 */
public final class RisingCampaign {
    /** Shared build budget per server tick across every instance (nanoseconds). */
    static final long BUILD_BUDGET_NANOS = 2_000_000L;
    /**
     * Budget while the head job's Guardian waits in the pre-mission blackout (nothing to simulate for them yet).
     * Target: blackout to Ghost scan within ~5 s. Still shared and capped well under the 50 ms tick.
     */
    static final long ENTRY_BUILD_BUDGET_NANOS = 16_000_000L;
    static final int RECONNECT_GRACE = 20 * 120;
    static final int ZONE_SPACING = 4096;
    static final int ZONE_Y = 64;
    private static final int GHOST = 0x8FE3FF;
    /** Darkness while the instance is prepared; the opening scan applies its own blackout on entry. */
    private static final net.minecraft.resources.Identifier BLACKOUT = DestinyGuardians.id("guardian_rises/blackout");

    public record Stored(String checkpoint, boolean music, boolean rifle, boolean shotgun) {
        static final Codec<Stored> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.STRING.fieldOf("checkpoint").forGetter(Stored::checkpoint),
                Codec.BOOL.optionalFieldOf("music", false).forGetter(Stored::music),
                Codec.BOOL.optionalFieldOf("rifle", false).forGetter(Stored::rifle),
                Codec.BOOL.optionalFieldOf("shotgun", false).forGetter(Stored::shotgun)
        ).apply(i, Stored::new));
    }
    /** In-progress checkpoint (absent when no unfinished run exists). */
    public static final AttachmentType<Stored> PROGRESS = AttachmentRegistry.create(DestinyGuardians.id("guardian_rises_progress"),
            b -> b.persistent(Stored.CODEC).copyOnDeath());
    /** Separate from the legacy tutorial revision: old completion never exempts an account. */
    public static final AttachmentType<Integer> COMPLETED_REVISION = AttachmentRegistry.create(
            DestinyGuardians.id("guardian_rises_completed_revision"),
            b -> b.persistent(Codec.INT).copyOnDeath().initializer(() -> 0));

    enum State { CHOOSING, QUEUED, PREPARING, RUNNING, ENDING }

    private static final Map<UUID, Session> SESSIONS = new LinkedHashMap<>();
    private static final Deque<Job> JOBS = new ArrayDeque<>();
    /**
     * W300 r12: one warm instance whose Gateway is pre-built in idle build time, so a fresh run goes from blackout to
     * the Ghost scan in a few seconds instead of waiting for a ~6-78 s zone build. Adopted by the next mission start.
     */
    static final UUID SPARE_OWNER = new UUID(0x5157_4152_4500L, 0x5741_524DL);
    static final boolean WARM_SPARE = !"false".equalsIgnoreCase(System.getProperty("destiny.guardianRises.warmSpare"));
    private static GuardianRisesInstances.Instance spare;
    private static RisingServices.ZoneBuild spareBuild;
    private static boolean spareBuilt;
    private static int spareRetryAt;
    private static MinecraftServer server;
    private static GuardianRisesInstances instances;
    private static boolean initialized;

    private record Job(Session session, Zone zone) { }

    private RisingCampaign() { }

    // ---- hooks -------------------------------------------------------------------------------------------

    public static void init() {
        if (initialized) return;
        initialized = true;
        ServerLifecycleEvents.SERVER_STARTED.register(s -> {
            server = s;
            instances = new GuardianRisesInstances(s, Integer.getInteger("destiny.guardianRises.capacity", 16));
        });
        ServerLifecycleEvents.SERVER_STOPPING.register(s -> {
            for (var session : List.copyOf(SESSIONS.values())) shutdown(session);
            SESSIONS.clear();
            JOBS.clear();
            closeSpare();
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(s -> { if (server == s) { server = null; instances = null; } });
        ServerTickEvents.END_SERVER_TICK.register(RisingCampaign::tick);
        ServerPlayConnectionEvents.DISCONNECT.register((handler, s) -> disconnected(handler.getPlayer()));
        // W303: deaths go through the global Guardian Down scene; the campaign revives at its checkpoint.
        kim.biryeong.destiny.down.GuardianDown.register(RisingCampaign::downed);
        ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) ->
                !(entity instanceof ServerPlayer p) || !protectedNow(p));
        CommandRegistrationCallback.EVENT.register((dispatcher, access, env) -> dispatcher.register(Commands.literal("destiny")
                .then(Commands.literal("rising")
                        .then(Commands.literal("class").then(Commands.argument("class", StringArgumentType.word())
                                .suggests((c, b) -> SharedSuggestionProvider.suggest(List.of("titan", "hunter", "warlock"), b))
                                .executes(c -> chooseClass(c.getSource(), StringArgumentType.getString(c, "class")))))
                        .then(Commands.literal("start").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .executes(c -> adminStart(c.getSource(), c.getSource().getPlayerOrException(), false))
                                .then(Commands.argument("player", EntityArgument.player())
                                        .executes(c -> adminStart(c.getSource(), EntityArgument.getPlayer(c, "player"), false))
                                        // W301: ignore the stored checkpoint and start again from the opening scan.
                                        .then(Commands.literal("fresh")
                                                .executes(c -> adminStart(c.getSource(), EntityArgument.getPlayer(c, "player"), true)))))
                        .then(Commands.literal("status").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .executes(c -> status(c.getSource())))
                        .then(Commands.literal("skip").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .then(Commands.argument("stage", StringArgumentType.word())
                                        .suggests((c, b) -> SharedSuggestionProvider.suggest(Arrays.stream(Stage.values())
                                                .filter(st -> st != Stage.COMPLETE).map(st -> st.name().toLowerCase(Locale.ROOT)), b))
                                        .executes(c -> skip(c.getSource(), StringArgumentType.getString(c, "stage")))))
                        .then(Commands.literal("abort").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                                .executes(c -> abort(c.getSource(), c.getSource().getPlayerOrException()))
                                .then(Commands.argument("player", EntityArgument.player())
                                        .executes(c -> abort(c.getSource(), EntityArgument.getPlayer(c, "player"))))))));
    }

    public static boolean shouldStart(ServerPlayer p) {
        return RisingMission.enabled() && RisingMission.required(p.getAttachedOrElse(COMPLETED_REVISION, 0), SESSIONS.containsKey(p.getUUID()));
    }

    /** True while the Guardian is inside their running mission instance. */
    public static boolean active(ServerPlayer p) {
        var s = p == null ? null : SESSIONS.get(p.getUUID());
        return s != null && s.state == State.RUNNING && s.instance != null && p.level() == s.instance.level();
    }
    /** Admission ownership includes queued/preparing/ending and reconnect grace. */
    public static boolean participating(ServerPlayer p) {
        return p != null && SESSIONS.containsKey(p.getUUID());
    }
    /** Connected running mission, even during a transfer between its zones. */
    public static boolean running(ServerPlayer p) {
        var s = p == null ? null : SESSIONS.get(p.getUUID());
        return s != null && s.state == State.RUNNING && s.disconnectedAt < 0;
    }
    /** Rise plays once per connected mission session; a restored checkpoint enables it again. */
    public static boolean musicScene(ServerPlayer p) {
        var s = p == null ? null : SESSIONS.get(p.getUUID());
        return s != null && s.musicThisConnection && active(p);
    }
    public static boolean isCampaignLevel(Level level) {
        if (instances == null || level == null) return false;
        for (var s : SESSIONS.values()) if (s.instance != null && s.instance.level() == level) return true;
        return false;
    }
    /** The loan escrow belongs to a run that is still alive (reconnect grace): do not restore it on join. */
    public static boolean holdsLoan(ServerPlayer p) {
        var s = SESSIONS.get(p.getUUID());
        return s != null && s.state == State.RUNNING;
    }
    /** Abilities rest during cinematics; everything else is available as soon as the Light returns. */
    public static boolean allows(ServerPlayer p, AbilitySlot slot) {
        var s = SESSIONS.get(p.getUUID());
        if (s == null || s.mission == null) return true;
        var stage = s.mission.stage();
        boolean ok = !(stage == Stage.GHOST_SCAN || stage == Stage.DEPARTURE || s.mission.placing());
        if (!ok) s.objectives.notice(p, now(), "고스트: 지금은 빛을 모으는 중이에요.");
        return ok;
    }

    /** Player-requested exit (e.g. /튜토리얼 나가기). Progress is kept at the last checkpoint. */
    public static boolean leave(ServerPlayer p) {
        var s = SESSIONS.get(p.getUUID());
        if (s == null) return false;
        end(s, p, true, "임무를 중단했습니다. 마지막 체크포인트가 저장되었습니다.");
        return true;
    }

    /** Null when {@link #start} would queue this player now. Read-only. */
    public static String check(ServerPlayer p) {
        if (kim.biryeong.destiny.strike.devils.DevilsLair.participating(p)) return "공격전에서 나간 뒤 시작하세요.";
        if (server == null || instances == null || !p.level().getServer().isSameThread()) return "서버에서 다시 시도하세요.";
        if (!p.isAlive() || p.isSpectator() || p.hasDisconnected()) return "살아 있는 접속 플레이어만 시작할 수 있습니다.";
        if (kim.biryeong.destiny.crucible.CrucibleRuntime.participating(p)) return "시련의 장에 참가 중에는 시작할 수 없습니다.";
        if (AbilityService.inSuper(p)) return "궁극기 사용 중에는 시작할 수 없습니다.";
        if (kim.biryeong.destiny.down.GuardianDown.active(p)) return "쓰러진 상태에서는 시작할 수 없습니다.";
        if (SESSIONS.containsKey(p.getUUID())) return "이미 진행 중인 임무가 있습니다.";
        if (kim.biryeong.destiny.tutorial.Tutorial.active(p)) return "튜토리얼을 마친 뒤 시작하세요.";
        return null;
    }
    /** The mission placed this player in its instance and is running (its opening presentation owns the view). */
    public static boolean entered(ServerPlayer p) {
        var s = SESSIONS.get(p.getUUID());
        return s != null && s.state == State.RUNNING && s.instance != null && p.level() == s.instance.level();
    }

    /** Queue a run (or resume the stored checkpoint). Returns null on success, or a Korean error. */
    public static String start(ServerPlayer p, boolean replay) {
        if (kim.biryeong.destiny.strike.devils.DevilsLair.participating(p)) return "공격전에서 나간 뒤 시작하세요.";
        if (server == null || instances == null || !p.level().getServer().isSameThread()) return "서버에서 다시 시도하세요.";
        if (!p.isAlive() || p.isSpectator() || p.hasDisconnected()) return "살아 있는 접속 플레이어만 시작할 수 있습니다.";
        if (kim.biryeong.destiny.crucible.CrucibleRuntime.participating(p)) return "시련의 장에 참가 중에는 시작할 수 없습니다.";
        if (AbilityService.inSuper(p)) return "궁극기 사용 중에는 시작할 수 없습니다.";
        var existing = SESSIONS.get(p.getUUID());
        if (existing != null) return existing.state == State.ENDING ? "이전 임무를 정리하는 중입니다. 잠시 후 다시 시도하세요." : null;
        RisingLoadout.restore(p);
        var stored = p.getAttached(PROGRESS);
        Stage checkpoint = Stage.GHOST_SCAN;
        boolean music = false, rifle = false, shotgun = false;
        if (stored != null && !replay) {
            try { checkpoint = Stage.valueOf(stored.checkpoint()); } catch (IllegalArgumentException ignored) { }
            if (!GuardianRisesProgress.isCheckpoint(checkpoint)) checkpoint = Stage.GHOST_SCAN;
            music = stored.music();
            rifle = stored.rifle() && checkpoint.ordinal() >= Stage.ARM_YOURSELF.ordinal();
            shotgun = stored.shotgun() && checkpoint.ordinal() > Stage.SUPPLY_CACHE.ordinal();
        }
        var s = new Session(p.getUUID(), new RisingMission.Saved(new GuardianRisesProgress.Snapshot(checkpoint, music, false), rifle, shotgun));
        // W300: the run opens in darkness with the Ghost scan; a missing class is asked for after the scan.
        s.state = State.QUEUED;
        s.classChosen = Guardians.data(p).guardianClass() != GuardianClass.NONE;
        SESSIONS.put(p.getUUID(), s);
        // Darkness and the waiting card replace any pre-mission prompt; the Ghost speaks only after it finds the Guardian.
        DestinyGuardians.LOGGER.info("[GuardianRises] queued {} from {}", p.getScoreboardName(), checkpoint);
        return null;
    }

    // ---- session -----------------------------------------------------------------------------------------

    static final class Session implements RisingMission.Host {
        final UUID owner;
        final RisingMission.Saved saved;
        State state;
        boolean classChosen;
        boolean blackout;
        GuardianRisesInstances.Instance instance;
        final EnumMap<Zone, RisingServices.ZoneBuild> builds = new EnumMap<>(Zone.class);
        final EnumSet<Zone> built = EnumSet.noneOf(Zone.class);
        final EnumMap<Zone, List<Marker>> markers = new EnumMap<>(Zone.class);
        final EnumMap<Zone, Double> floors = new EnumMap<>(Zone.class);
        final Map<UUID, LivingEntity> enemies = new HashMap<>();
        final RisingObjectives objectives = new RisingObjectives();
        RisingMission mission;
        int disconnectedAt = -1;
        int offeredAt;
        int lastLoadingNotice;
        boolean musicThisConnection;
        boolean entered;
        final Set<String> problems = new HashSet<>();

        Session(UUID owner, RisingMission.Saved saved) { this.owner = owner; this.saved = saved; }

        ServerPlayer player() { return server == null ? null : server.getPlayerList().getPlayer(owner); }
        ServerLevel level() { return instance.level(); }
        BlockPos origin(Zone zone) { return new BlockPos(ZONE_SPACING / 2 + zone.ordinal() * ZONE_SPACING, ZONE_Y, ZONE_SPACING / 2); }

        // -- Host --
        @Override public boolean classKnown() {
            var p = player();
            return p != null && Guardians.data(p).guardianClass() != GuardianClass.NONE;
        }
        @Override public void askClass() {
            var p = player();
            if (p != null) { classChosen = false; offerClasses(p); }
        }
        @Override public void classLines() {
            var p = player();
            if (p == null) return;
            switch (Guardians.data(p).guardianClass()) {
                case TITAN -> { voice("80b75f54"); voice("80b75f53"); }
                case HUNTER -> { voice("80b75f56"); voice("80b75f59"); }
                case WARLOCK -> { voice("80b75f58"); voice("80b75f5e"); }
                default -> { }
            }
        }
        @Override public void waveIncoming(Zone zone, int index, List<RisingEncounters.Slot> wave, int ticks) {
            if (instance != null) kim.biryeong.destiny.campaign.fallen.SkiffDrop.incoming(level(), zone, index, wave, ticks, skiffHint(zone, wave));
        }
        @Override public void waveSpawned(Zone zone, int index, List<RisingEncounters.Slot> wave) {
            if (instance != null) kim.biryeong.destiny.campaign.fallen.SkiffDrop.spawned(level(), zone, index, wave, skiffHint(zone, wave));
        }
        private net.minecraft.world.phys.Vec3 skiffHint(Zone zone, List<RisingEncounters.Slot> wave) {
            if (wave == null || wave.isEmpty()) return null;
            return marker(zone, kim.biryeong.destiny.campaign.fallen.SkiffDrop.hintMarker(wave.get(0).encounter()))
                    .map(Marker::pos).orElse(null);
        }
        @Override public void lights(Zone zone, String phase) {
            if (instance == null) return;
            var level = level();
            for (var m : markers(zone, "light.")) {
                if (!phase.equals(m.tags().get("phase"))) continue;
                String block = m.tags().get("block");
                if (block == null) continue;
                try {
                    var state = net.minecraft.commands.arguments.blocks.BlockStateParser
                            .parseForBlock(net.minecraft.core.registries.BuiltInRegistries.BLOCK, block, false).blockState();
                    var pos = net.minecraft.core.BlockPos.containing(m.pos());
                    if (!level.isLoaded(pos)) continue;
                    var old = level.getBlockState(pos);
                    if (old == state) continue;
                    // fill lights replace air only; mounted bulbs replace their unlit selves
                    if ("fill".equals(m.tags().get("mount")) && !old.isAir() && !old.is(net.minecraft.world.level.block.Blocks.LIGHT)) continue;
                    level.setBlock(pos, state, net.minecraft.world.level.block.Block.UPDATE_CLIENTS);
                } catch (Exception e) {
                    DestinyGuardians.LOGGER.warn("[GuardianRises] bad light marker {} {}", m.id(), block);
                }
            }
        }
        @Override public Optional<Marker> marker(Zone zone, String id) {
            return markersOf(zone).stream().filter(m -> m.id().equals(id)).findFirst();
        }
        @Override public List<Marker> markers(Zone zone, String prefix) {
            return markersOf(zone).stream().filter(m -> m.id().startsWith(prefix)).toList();
        }
        List<Marker> markersOf(Zone zone) {
            var cached = markers.get(zone);
            if (cached != null) return cached;
            var zones = RisingServices.zones();
            if (zones.isEmpty()) return List.of();
            List<Marker> all;
            try { all = List.copyOf(zones.get().markers(zone, origin(zone)).all()); }
            catch (RuntimeException e) { problem("구역 " + zone + " 마커를 읽지 못했습니다: " + e.getMessage()); all = List.of(); }
            markers.put(zone, all);
            floors.put(zone, all.stream().mapToDouble(m -> m.pos().y).min().orElse(origin(zone).getY()));
            return all;
        }
        @Override public Vec3 position() { var p = player(); return p == null ? Vec3.ZERO : p.position(); }
        @Override public boolean zoneReady(Zone zone) { return built.contains(zone); }
        @Override public void prepareZone(Zone zone) { enqueue(this, zone, true); }
        @Override public void place(Zone zone, Marker anchor) {
            var p = player();
            if (p == null || instance == null) return;
            boolean entering = p.level() != level();
            if (entering) cleanupForTeleport(p);
            if (!entering) p.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 30, 0, false, false));
            Vec3 at = anchor.pos();
            p.teleportTo(level(), at.x, at.y, at.z, Set.of(), anchor.yaw(), 0, true);
            p.resetFallDistance();
            p.setDeltaMovement(Vec3.ZERO);
            entered = true;
        }
        @Override public int voice(String lineId) {
            var p = player();
            var pr = RisingServices.presentation();
            if (p == null || pr.isEmpty()) return 0;
            try { return pr.get().voice(p, lineId); } catch (RuntimeException e) { problem("음성 재생 실패 " + lineId + ": " + e.getMessage()); return 0; }
        }
        @Override public Handle openingScan(Runnable done) { return openingScan(null, done); }
        @Override public Handle openingScan(Vec3 vista, Runnable done) {
            var p = player();
            return presentation(pr -> pr.openingScan(p, p.getEyePosition(), vista, done));
        }
        @Override public Handle ghostScan(Vec3 target, int ticks, Runnable done) {
            var p = player();
            return presentation(pr -> pr.ghostScan(p, target, ticks, done));
        }
        @Override public Handle departure(Vec3 shipPos, float shipYaw, Runnable done) {
            var p = player();
            return presentation(pr -> pr.departure(p, shipPos, shipYaw, done));
        }
        @Override public RisingServices.PickupHandle pickup(Vec3 pos, float yaw, String kind) {
            var p = player();
            var pr = RisingServices.presentation();
            if (p == null || pr.isEmpty()) return null;
            try { return pr.get().pickup(p, pos, yaw, kind); }
            catch (RuntimeException e) { problem("연출 실패: " + e.getMessage()); return null; }
        }
        @Override public Handle shipProp(Vec3 shipPos, float shipYaw) {
            var p = player();
            return presentation(pr -> pr.shipProp(p, shipPos, shipYaw));
        }
        private Handle presentation(java.util.function.Function<RisingServices.Presentation, Handle> call) {
            var p = player();
            var pr = RisingServices.presentation();
            if (p == null || pr.isEmpty()) return null;
            try { return call.apply(pr.get()); }
            catch (RuntimeException e) { problem("연출 실패: " + e.getMessage()); return null; }
        }
        @Override public void grantRifle() { var p = player(); if (p != null) RisingLoadout.grantRifle(p); }
        @Override public void grantShotgun() { var p = player(); if (p != null) RisingLoadout.grantShotgun(p); }
        @Override public boolean ownsRifle() { var p = player(); return p != null && RisingLoadout.ownsRifle(p); }
        @Override public boolean holdingRifle() { var p = player(); return p != null && RisingLoadout.holdingRifle(p); }
        @Override public RisingEncounters.Spawner spawner(Zone zone) { return new Spawner(this); }
        @Override public boolean finish() {
            var p = player();
            if (p == null || p.hasDisconnected()) return false;
            RisingLoadout.restore(p);
            RisingObjectives.clear(p);
            RisingServices.presentation().ifPresent(pr -> pr.stopAll(p));
            ActivityMusic.tutorialEnded(p);
            cleanupForTeleport(p);
            boolean moved = TowerSpawnWorld.teleport(p);
            if (!moved) {
                var overworld = server.overworld();
                var spawn = overworld.getRespawnData().pos();
                moved = p.teleportTo(overworld, spawn.getX() + .5, spawn.getY(), spawn.getZ() + .5, Set.of(), 0, 0, true);
            }
            if (!moved) return false;
            p.setAttached(COMPLETED_REVISION, RisingMission.REVISION);
            if (p.getAttachedOrElse(Tutorial.COMPLETED_REVISION, 0) < Tutorial.REQUIRED_REVISION)
                p.setAttached(Tutorial.COMPLETED_REVISION, Tutorial.REQUIRED_REVISION);
            p.removeAttached(PROGRESS);
            // The arrival curtain's "임무 완료" title card and the Ghost's Tower line announce completion; no chat line.
            DestinyGuardians.LOGGER.info("[GuardianRises] {} completed revision {}", p.getScoreboardName(), RisingMission.REVISION);
            return true;
        }
        @Override public void startMusic() { musicThisConnection = true; }
        @Override public void notice(String text) { var p = player(); if (p != null) objectives.notice(p, now(), text); }
        @Override public void problem(String text) {
            if (!problems.add(text)) return;
            DestinyGuardians.LOGGER.warn("[GuardianRises] {}: {}", owner, text);
            var p = player();
            if (p != null) p.sendSystemMessage(Component.literal("⚠ 임무 오류: " + text).withColor(0xFF8A65));
        }
        @Override public void saved() { save(player()); }
        void save(ServerPlayer p) {
            if (p == null || mission == null) return;
            if (mission.complete()) { p.removeAttached(PROGRESS); return; }
            var snap = mission.snapshot();
            p.setAttached(PROGRESS, new Stored(snap.progress().checkpoint().name(), snap.progress().musicStarted(), snap.rifle(), snap.shotgun()));
        }
    }

    /** Fallen service adapter; tracks live entities of this instance for discard/freeze/position. */
    private static final class Spawner implements RisingEncounters.Spawner {
        private final Session session;
        Spawner(Session session) { this.session = session; }
        @Override public UUID spawn(RisingEncounters.Slot slot, boolean active, RisingEncounters.Events events) {
            var fallen = RisingServices.fallen();
            if (fallen.isEmpty()) { session.problem("몰락자 서비스가 등록되지 않았습니다."); return null; }
            if (session.instance == null || session.instance.state() == GuardianRisesInstances.State.CLOSED) return null;
            var listener = new RisingServices.FallenListener() {
                @Override public void defeated(LivingEntity entity) { session.enemies.remove(entity.getUUID()); events.defeated(entity.getUUID()); }
                @Override public void lost(LivingEntity entity) { session.enemies.remove(entity.getUUID()); events.lost(entity.getUUID()); }
            };
            LivingEntity entity = fallen.get().spawn(session.level(), slot.kind(), slot.pos(), slot.yaw(),
                    RisingServices.Difficulty.FIRST_MISSION, listener);
            if (entity == null) return null;
            session.enemies.put(entity.getUUID(), entity);
            if (!active) fallen.get().setActive(entity, false);
            return entity.getUUID();
        }
        @Override public void setActive(UUID id, boolean active) {
            var e = session.enemies.get(id);
            if (e != null) RisingServices.fallen().ifPresent(f -> f.setActive(e, active));
        }
        @Override public void discard(UUID id) {
            var e = session.enemies.remove(id);
            // Enemies already in their death animation (Walker collapse, Fallen ragdoll) finish it themselves;
            // removing them here would cut the kill presentation the moment the stage advances.
            if (e != null && !e.isRemoved() && !(e instanceof net.minecraft.world.entity.LivingEntity l && l.isDeadOrDying())) e.discard();
        }
        @Override public Optional<Vec3> position(UUID id) {
            var e = session.enemies.get(id);
            return e == null || e.isRemoved() ? Optional.empty() : Optional.of(e.position());
        }
    }

    // ---- tick --------------------------------------------------------------------------------------------

    private static int now() { return server == null ? 0 : server.getTickCount(); }

    private static void tick(MinecraftServer s) {
        if (s != server || instances == null) return;
        build();
        if (SESSIONS.isEmpty()) return;
        int now = now();
        int queuePos = 0;
        for (var session : List.copyOf(SESSIONS.values())) {
            try { tickSession(session, now, session.state == State.QUEUED ? ++queuePos : 0); }
            catch (RuntimeException e) {
                DestinyGuardians.LOGGER.error("[GuardianRises] session {} failed", session.owner, e);
                session.problem("임무 처리 중 오류가 발생해 임무를 중단합니다. 마지막 체크포인트는 저장되어 있습니다.");
                var p = session.player();
                end(session, p, true, null);
            }
        }
    }

    private static void tickSession(Session s, int now, int queuePos) {
        var p = s.player();
        if (s.state == State.ENDING) {
            if (p != null && s.instance != null && p.level() == s.instance.level() && now % 40 == 0) evacuate(p);
            if (s.instance == null || instances.close(s.instance)) SESSIONS.remove(s.owner, s);
            return;
        }
        if (p != null && s.state != State.RUNNING) waiting(s, p, now);
        if (p == null) {
            // Queued players simply re-queue on their next join; a running run waits for the grace window.
            if (s.state != State.RUNNING || s.disconnectedAt >= 0 && now - s.disconnectedAt > RECONNECT_GRACE) {
                if (s.mission != null) s.mission.close();
                drop(s);
            }
            return;
        }
        switch (s.state) {
            case CHOOSING -> {
                markReady(s);
                if (Guardians.data(p).guardianClass() != GuardianClass.NONE) {
                    s.classChosen = true;
                    s.state = s.instance == null ? State.QUEUED : State.PREPARING;
                    RisingObjectives.clear(p);
                    p.sendSystemMessage(Component.literal("고스트: 좋아요. 이제 눈을 감아요…").withColor(GHOST));
                } else {
                    if (now % 10 == 0) RisingObjectives.renderClassChoice(p);
                    if (now - s.offeredAt > 20 * 30) offerClasses(p);
                }
                prepare(s);
            }
            case QUEUED -> {
                prepare(s);
                if (s.state == State.QUEUED && now - s.lastLoadingNotice >= 40) {
                    s.lastLoadingNotice = now;
                    RisingObjectives.renderLoading(p, "임무 공간 준비 대기 중 · " + queuePos + "번째");
                }
            }
            case PREPARING -> {
                markReady(s);
                if (s.instance != null && s.instance.state() == GuardianRisesInstances.State.READY) enter(s, p, now);
                else if (now - s.lastLoadingNotice >= 20) {
                    s.lastLoadingNotice = now;
                    var build = s.builds.get(entryZone(s));
                    int pct = build == null ? 0 : (int) Math.round(Math.min(1, Math.max(0, build.progress())) * 100);
                    RisingObjectives.renderLoading(p, "고스트가 당신을 찾고 있어요 · " + pct + "%");
                }
            }
            case RUNNING -> running(s, p, now);
            default -> { }
        }
    }

    /** The entry zone is built: READY frees the single preparation slot even while a class is being chosen. */
    private static void markReady(Session s) {
        if (s.instance != null && s.instance.state() == GuardianRisesInstances.State.PREPARING && s.built.contains(entryZone(s)))
            instances.ready(s.instance);
    }

    /** Before entry the Guardian waits where they are: no damage, no void falls, darkness once a class is chosen. */
    private static void waiting(Session s, ServerPlayer p, int now) {
        if (now % 40 != 0) return;
        p.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 60, 0, false, false));
        p.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 60, 0, false, false));
        p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 60, 0, false, false));
        if (!s.blackout) s.blackout = p.addPostEffect(BLACKOUT);
    }

    private static void evacuate(ServerPlayer p) {
        cleanupForTeleport(p);
        if (!TowerSpawnWorld.teleport(p)) {
            var overworld = server.overworld();
            var spawn = overworld.getRespawnData().pos();
            p.teleportTo(overworld, spawn.getX() + .5, spawn.getY(), spawn.getZ() + .5, Set.of(), 0, 0, true);
        }
    }

    private static void prepare(Session s) {
        if (s.instance != null) return;
        var zones = RisingServices.zones();
        if (zones.isEmpty()) { s.problem("구역 서비스가 등록되지 않아 임무를 준비할 수 없습니다."); return; }
        boolean adopted = spare != null && instances.adopt(spare, SPARE_OWNER, s.owner);
        if (adopted) {
            s.instance = spare;
            if (spareBuilt) {
                s.built.add(Zone.GATEWAY);
                s.markersOf(Zone.GATEWAY);
            } else if (spareBuild != null) s.builds.put(Zone.GATEWAY, spareBuild); // finishes as this run's job
            DestinyGuardians.LOGGER.info("[GuardianRises] {} adopted warm instance (gateway {})", s.owner, spareBuilt ? "built" : "in progress");
            spare = null; spareBuild = null; spareBuilt = false;
        }
        var made = adopted ? Optional.of(s.instance) : instances.prepare(s.owner);
        if (made.isEmpty()) return;
        s.instance = made.get();
        DestinyGuardians.LOGGER.info("[GuardianRises] instance created for {}", s.owner);
        instances.own(s.instance, () -> {
            for (var build : s.builds.values()) build.cancel();
            for (var e : List.copyOf(s.enemies.values())) if (!e.isRemoved()) e.discard();
            s.enemies.clear();
        });
        if (s.state == State.QUEUED) s.state = State.PREPARING;
        enqueue(s, entryZone(s), false);
        // A checkpoint resume elsewhere never returns to the Gateway: drop the half-built warm copy's chunk tickets.
        if (adopted && !s.built.contains(Zone.GATEWAY) && entryZone(s) != Zone.GATEWAY) {
            var partial = s.builds.remove(Zone.GATEWAY);
            if (partial != null) partial.cancel();
        }
    }

    /** Idle-time Gateway pre-build for the next mission start. Only runs when no real build job is queued. */
    private static void warmSpare(long left) {
        if (!WARM_SPARE || !RisingMission.enabled() || instances == null || left <= 0) return;
        var zones = RisingServices.zones();
        if (zones.isEmpty()) return;
        if (spare == null) {
            if (now() < spareRetryAt) return;
            // Never take the single preparation slot from a waiting Guardian.
            for (var s : SESSIONS.values()) if (s.instance == null && s.state != State.ENDING) return;
            var made = instances.prepare(SPARE_OWNER);
            if (made.isEmpty()) { spareRetryAt = now() + 200; return; }
            spare = made.get();
            spareBuilt = false;
            DestinyGuardians.LOGGER.info("[GuardianRises] warming spare instance {}", spare.id());
        }
        if (spareBuilt) return;
        try {
            if (spareBuild == null) spareBuild = zones.get().begin(spare.level(), Zone.GATEWAY, gatewayOrigin());
            if (spareBuild.step(left)) {
                spareBuilt = true;
                DestinyGuardians.LOGGER.info("[GuardianRises] spare instance {} ready (gateway built)", spare.id());
            }
        } catch (RuntimeException e) {
            DestinyGuardians.LOGGER.error("[GuardianRises] spare build failed", e);
            closeSpare();
            spareRetryAt = now() + 20 * 60;
        }
    }

    private static BlockPos gatewayOrigin() {
        return new BlockPos(ZONE_SPACING / 2 + Zone.GATEWAY.ordinal() * ZONE_SPACING, ZONE_Y, ZONE_SPACING / 2);
    }

    private static void closeSpare() {
        if (spareBuild != null) spareBuild.cancel();
        if (spare != null && instances != null) instances.close(spare);
        spare = null; spareBuild = null; spareBuilt = false;
    }

    private static Zone entryZone(Session s) { return RisingMission.anchorZone(s.saved.progress().checkpoint()); }

    private static void enter(Session s, ServerPlayer p, int now) {
        instances.running(s.instance);
        s.state = State.RUNNING;
        RisingObjectives.clear(p);
        p.removeEffect(MobEffects.BLINDNESS);
        p.removeEffect(MobEffects.DARKNESS);
        p.removeEffect(MobEffects.SLOW_FALLING);
        if (s.blackout) { p.removePostEffect(BLACKOUT); s.blackout = false; }
        RisingLoadout.stow(p);
        Guardians.data(p).setSuperEnergy(0f);
        s.mission = new RisingMission(s.instance.id(), s.saved, s);
        if (s.saved.rifle()) RisingLoadout.grantRifle(p);
        if (s.saved.shotgun()) RisingLoadout.grantShotgun(p);
        s.mission.begin(now);
        s.mission.tick(now);
        DestinyGuardians.LOGGER.info("[GuardianRises] {} entered instance {} at {}", p.getScoreboardName(), s.instance.id(), s.mission.stage());
    }

    private static void running(Session s, ServerPlayer p, int now) {
        if (s.disconnectedAt >= 0) {
            // Back inside the grace window (the join itself finished last tick).
            boolean inside = p.level() == s.level();
            s.disconnectedAt = -1;
            s.musicThisConnection = false;
            s.mission.resume(now, !inside);
            if (!inside) RisingLoadout.stow(p);
            if (s.mission.rifleGranted()) RisingLoadout.grantRifle(p);
            if (s.mission.shotgunGranted()) RisingLoadout.grantShotgun(p);
            p.sendSystemMessage(Component.literal("고스트: 돌아왔군요. 계속 가요.").withColor(GHOST));
        }
        if (s.entered && p.level() != s.level() && !s.mission.placing()) {
            // Left through /tower, /tp or a portal: keep the checkpoint and retire the instance.
            end(s, p, false, "임무 공간을 벗어났습니다. 다음 접속 시 마지막 체크포인트에서 이어집니다.");
            return;
        }
        s.mission.tick(now);
        if (s.mission.complete()) {
            DestinyGuardians.LOGGER.info("[GuardianRises] {} complete; closing {}", p.getScoreboardName(), s.instance.id());
            drop(s);
            return;
        }
        if (p.level() == s.level() && s.mission.zone() != null) {
            Zone zone = s.mission.zone();
            s.markersOf(zone);
            double floor = s.floors.getOrDefault(zone, (double) ZONE_Y);
            Vec3 anchor = RisingMission.anchors(s.mission.stage()).stream()
                    .map(id -> s.marker(RisingMission.anchorZone(s.mission.stage()), id)).flatMap(Optional::stream)
                    .filter(m -> RisingMission.anchorZone(s.mission.stage()) == zone).map(Marker::pos).findFirst().orElse(null);
            s.objectives.tick(p, s.mission, now, floor, anchor, zone, Vec3.atLowerCornerOf(s.origin(zone)));
        }
    }

    // ---- builds ------------------------------------------------------------------------------------------

    private static void enqueue(Session s, Zone zone, boolean priority) {
        if (s.built.contains(zone) || s.instance == null) return;
        for (var job : JOBS) if (job.session() == s && job.zone() == zone) return;
        var job = new Job(s, zone);
        if (priority && s.state == State.RUNNING) {
            // Running Guardians waiting at a zone exit go first; the head job keeps its progress.
            var head = JOBS.pollFirst();
            JOBS.addFirst(job);
            if (head != null) JOBS.addFirst(head);
        } else JOBS.addLast(job);
    }

    /** One preparation at a time under the shared budget; never runs ahead of the budget. */
    private static void build() {
        var head = JOBS.peekFirst();
        boolean entry = head != null && head.session().state != State.RUNNING;
        long deadline = System.nanoTime() + (entry ? ENTRY_BUILD_BUDGET_NANOS : BUILD_BUDGET_NANOS);
        if (JOBS.isEmpty()) { warmSpare(deadline - System.nanoTime()); return; }
        while (!JOBS.isEmpty()) {
            long left = deadline - System.nanoTime();
            if (left <= 0) return;
            var job = JOBS.peekFirst();
            var s = job.session();
            if (!SESSIONS.containsValue(s) || s.instance == null || s.state == State.ENDING
                    || s.instance.state() == GuardianRisesInstances.State.CLOSED || s.built.contains(job.zone())) {
                JOBS.pollFirst();
                continue;
            }
            var zones = RisingServices.zones();
            if (zones.isEmpty()) return;
            var build = s.builds.get(job.zone());
            try {
                if (build == null) {
                    build = zones.get().begin(s.level(), job.zone(), s.origin(job.zone()));
                    s.builds.put(job.zone(), build);
                    DestinyGuardians.LOGGER.info("[GuardianRises] zone {} build start", job.zone());
                }
                if (build.step(left)) {
                    s.built.add(job.zone());
                    JOBS.pollFirst();
                    s.markersOf(job.zone());
                    DestinyGuardians.LOGGER.info("[GuardianRises] zone {} ready for {}", job.zone(), s.owner);
                } else return;
            } catch (RuntimeException e) {
                JOBS.pollFirst();
                DestinyGuardians.LOGGER.error("[GuardianRises] zone {} build failed", job.zone(), e);
                s.problem("구역 " + job.zone() + " 생성 실패: " + e.getMessage());
                end(s, s.player(), true, null);
                return;
            }
        }
    }

    // ---- lifecycle ---------------------------------------------------------------------------------------

    private static void disconnected(ServerPlayer p) {
        var s = SESSIONS.get(p.getUUID());
        if (s == null) return;
        if (s.state == State.RUNNING && s.mission != null && !s.mission.complete()) {
            s.save(p);
            s.mission.pause();
            s.disconnectedAt = now();
            s.musicThisConnection = false;
            RisingServices.presentation().ifPresent(pr -> pr.stopAll(p));
        } else if (s.state != State.RUNNING) drop(s);
    }

    /** Mission over for this instance (complete, abort, left, expired). The player must already be out. */
    private static void drop(Session s) {
        if (s.mission != null) s.mission.close();
        s.state = State.ENDING;
        if (s.instance == null || instances == null || instances.close(s.instance)) SESSIONS.remove(s.owner, s);
    }

    /** Return the Guardian safely (loans, HUD, music) and retire the instance. */
    private static void end(Session s, ServerPlayer p, boolean toTower, String message) {
        if (s.mission != null) { s.saved(); s.mission.close(); }
        if (p != null && !p.hasDisconnected()) {
            RisingLoadout.restore(p);
            RisingObjectives.clear(p);
            RisingServices.presentation().ifPresent(pr -> pr.stopAll(p));
            ActivityMusic.tutorialEnded(p);
            if (toTower && s.instance != null && p.level() == s.instance.level()) evacuate(p);
            p.removeEffect(MobEffects.SLOW_FALLING);
            if (message != null) p.sendSystemMessage(Component.literal(message).withColor(GHOST));
        }
        drop(s);
    }

    private static void shutdown(Session s) {
        var p = s.player();
        if (s.mission != null) { s.saved(); s.mission.close(); }
        if (p != null) { RisingObjectives.clear(p); RisingServices.presentation().ifPresent(pr -> pr.stopAll(p)); }
        // close() defers while the player is still inside (true at SERVER_STOPPING): release chunk tickets of
        // unfinished builds now, or stopServer waits forever on the forced chunk loads.
        for (var build : s.builds.values()) build.cancel();
        // Loans stay in persistent escrow and are restored on the next join; temporary levels die with the server.
        if (s.instance != null && instances != null) instances.close(s.instance);
    }

    private static kim.biryeong.destiny.down.GuardianDown.Options downed(ServerPlayer p,
                                                                       net.minecraft.world.damagesource.DamageSource source) {
        var s = SESSIONS.get(p.getUUID());
        if (s == null || s.state != State.RUNNING || s.mission == null || p.level() != s.level()) return null;
        AbilityService.cleanup(p);
        WeaponRuntime.cleanup(p);
        DestinyGuardians.LOGGER.info("[GuardianRises] {} downed at {} by {}; checkpoint {}", p.getScoreboardName(),
                p.blockPosition(), source.getMsgId(), s.mission.stage());
        return kim.biryeong.destiny.down.GuardianDown.Options.checkpoint(60, RisingCampaign::revived);
    }

    /** Ghost revive finished: restart the encounter at its checkpoint (same as the old instant revive). */
    private static void revived(ServerPlayer p) {
        var s = SESSIONS.get(p.getUUID());
        if (s == null || s.state != State.RUNNING || s.mission == null || p.level() != s.level()) return;
        p.setHealth(p.getMaxHealth());
        p.clearFire();
        p.resetFallDistance();
        p.setDeltaMovement(Vec3.ZERO);
        DestinyGuardians.LOGGER.info("[GuardianRises] {} revived; restarting {}", p.getScoreboardName(), s.mission.stage());
        s.mission.onDeath();
    }

    private static boolean protectedNow(ServerPlayer p) {
        var s = SESSIONS.get(p.getUUID());
        if (s == null || s.state == State.ENDING) return false;
        if (s.state != State.RUNNING) return true;
        if (s.mission == null) return false;
        var stage = s.mission.stage();
        return s.mission.placing() || s.mission.finishing() || stage == Stage.GHOST_SCAN || stage == Stage.GATEWAY
                || stage == Stage.BREACH_DARK || stage == Stage.DEPARTURE;
    }

    private static void cleanupForTeleport(ServerPlayer p) {
        AbilityService.cleanup(p);
        WeaponRuntime.cleanup(p);
        if (WeaponScreen.active(p)) WeaponScreen.close(p);
        CameraViews.stop(p);
        p.setCamera(p);
        p.stopRiding();
        p.stopUsingItem();
        p.closeContainer();
        p.resetFallDistance();
        p.setDeltaMovement(Vec3.ZERO);
    }

    // ---- class choice and commands -----------------------------------------------------------------------

    private static void offerClasses(ServerPlayer p) {
        var s = SESSIONS.get(p.getUUID());
        if (s != null) s.offeredAt = now();
        var line = Component.literal("고스트: 당신은 어떤 수호자였나요?  ").withColor(GHOST);
        line.append(option("타이탄", "titan", 0xE0703A, "방벽을 세우는 투사"));
        line.append(Component.literal("  "));
        line.append(option("헌터", "hunter", 0x4FB0E0, "위험을 감수하는 개척자"));
        line.append(Component.literal("  "));
        line.append(option("워록", "warlock", 0xE0C04F, "빛을 읽는 학자"));
        p.sendSystemMessage(line);
        p.sendSystemMessage(Component.literal("직업은 E 키 장비 메뉴에서 언제든 변경할 수 있습니다.").withColor(0xA9B2BC));
    }

    private static Component option(String name, String id, int color, String blurb) {
        return Component.literal("[" + name + "]").withStyle(st -> st.withColor(color).withBold(true)
                .withClickEvent(new ClickEvent.RunCommand("/destiny rising class " + id))
                .withHoverEvent(new HoverEvent.ShowText(Component.literal(blurb))));
    }

    private static int chooseClass(CommandSourceStack source, String id) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        var p = source.getPlayerOrException();
        var s = SESSIONS.get(p.getUUID());
        boolean asked = s != null && s.state == State.RUNNING && s.mission != null
                && s.mission.stage() == Stage.GHOST_SCAN && Guardians.data(p).guardianClass() == GuardianClass.NONE;
        if (s == null || s.state == State.ENDING || s.state == State.RUNNING && !asked) {
            source.sendFailure(Component.literal("직업은 E 키 장비 메뉴에서 바꿀 수 있습니다."));
            return 0;
        }
        GuardianClass cls;
        try { cls = GuardianClass.valueOf(id.toUpperCase(Locale.ROOT)); } catch (IllegalArgumentException e) { cls = GuardianClass.NONE; }
        if (cls == GuardianClass.NONE) { source.sendFailure(Component.literal("titan, hunter, warlock 중에서 고르세요.")); return 0; }
        String error = CharacterLoadouts.selectClass(p, cls);
        if (error != null) { source.sendFailure(Component.literal(error)); return 0; }
        return 1;
    }

    private static int adminStart(CommandSourceStack source, ServerPlayer target, boolean fresh) {
        if (SESSIONS.containsKey(target.getUUID())) { source.sendFailure(Component.literal("이미 진행 중인 임무가 있습니다.")); return 0; }
        String error = start(target, fresh);
        if (error != null) { source.sendFailure(Component.literal(error)); return 0; }
        source.sendSuccess(() -> Component.literal("떠오르는 수호자 대기열에 추가: " + target.getScoreboardName()), true);
        return 1;
    }

    private static int skip(CommandSourceStack source, String stageName) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        var p = source.getPlayerOrException();
        var s = SESSIONS.get(p.getUUID());
        if (s == null || s.mission == null || s.state != State.RUNNING) { source.sendFailure(Component.literal("진행 중인 임무가 없습니다. /destiny rising start")); return 0; }
        Stage stage;
        try { stage = Stage.valueOf(stageName.toUpperCase(Locale.ROOT)); } catch (IllegalArgumentException e) { source.sendFailure(Component.literal("알 수 없는 단계입니다.")); return 0; }
        if (!s.mission.skip(stage)) { source.sendFailure(Component.literal("이 단계로 이동할 수 없습니다.")); return 0; }
        source.sendSuccess(() -> Component.literal("단계 이동: " + stage), true);
        return 1;
    }

    private static int abort(CommandSourceStack source, ServerPlayer target) {
        var s = SESSIONS.get(target.getUUID());
        if (s == null) { source.sendFailure(Component.literal("진행 중인 임무가 없습니다.")); return 0; }
        end(s, target, true, "관리자가 임무를 중단했습니다. 마지막 체크포인트가 저장되었습니다.");
        source.sendSuccess(() -> Component.literal("임무 중단: " + target.getScoreboardName()), true);
        return 1;
    }

    private static int status(CommandSourceStack source) {
        var out = new StringBuilder("떠오르는 수호자 · 세션 " + SESSIONS.size() + " · 빌드 대기 " + JOBS.size()
                + " · 인스턴스 " + (instances == null ? 0 : instances.instances().size()));
        for (var s : SESSIONS.values()) {
            var p = s.player();
            out.append("\n- ").append(p == null ? s.owner.toString() : p.getScoreboardName()).append(' ').append(s.state);
            if (s.instance != null) out.append(" inst=").append(s.instance.state()).append(" built=").append(s.built);
            if (s.mission != null) {
                out.append(" stage=").append(s.mission.stage()).append(" cp=").append(s.mission.progress().checkpoint())
                        .append(" zone=").append(s.mission.zone()).append(" enemies=").append(s.mission.progress().enemiesRemaining())
                        .append(" live=").append(s.enemies.size());
                if (s.mission.placing()) out.append(" placing");
            }
            if (s.disconnectedAt >= 0) out.append(" offline=").append((now() - s.disconnectedAt) / 20).append('s');
            if (!s.problems.isEmpty()) out.append(" problems=").append(s.problems.size());
        }
        source.sendSuccess(() -> Component.literal(out.toString()), false);
        return 1;
    }
}
