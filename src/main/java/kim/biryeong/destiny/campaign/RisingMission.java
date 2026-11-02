package kim.biryeong.destiny.campaign;

import kim.biryeong.destiny.campaign.GuardianRisesProgress.Stage;
import kim.biryeong.destiny.campaign.RisingServices.Handle;
import kim.biryeong.destiny.campaign.RisingServices.Marker;
import kim.biryeong.destiny.campaign.RisingServices.Zone;
import net.minecraft.world.phys.Vec3;

import java.util.*;

/**
 * Stage script of one Guardian Rises run. Server-thread, tick driven, and free of Minecraft world types: every
 * world effect goes through {@link Host}, which the campaign implements with {@link RisingServices} and tests
 * implement with fakes. Callbacks from presentation/encounters are bound to the progress token current when
 * they were issued, so a death, skip or restart can never be advanced by a stale event.
 *
 * <p>Stage beats, voice placement, trigger radii and fallbacks are original design; the line ids are the
 * extracted Korean Ghost WEM tags (see docs/design/guardian-rises/director.md).
 */
public final class RisingMission {
    /** Bumped when the mission changes enough that every account should play it once more. */
    public static final int REVISION = 1;
    public static final String FLAG = "destiny.guardianRises";
    static final int OPENING_TIMEOUT = 20 * 120; // opening (~16 s) + A/D class choice (auto-confirms at 45 s)
    static final int DEPARTURE_TIMEOUT = 20 * 60;
    static final int MISSING_DATA_GRACE = 100;
    static final int ARENA_FALLBACK = 20 * 30;
    /** Weapon pickup reach (Vision r3: a route passing the cache at exactly 2.5 m did not collect it). */
    static final double PICKUP_RADIUS = 3.0;
    static final String RIFLE_PROP = "rifle", CACHE_PROP = "shotgun_cache";

    public static boolean enabled() { return enabled(System.getProperty(FLAG)); }
    static boolean enabled(String value) { return value == null || !value.trim().equalsIgnoreCase("false"); }
    /** Legacy tutorial completion never counts; a finished run is never forced again. */
    public static boolean required(int completedRevision, boolean active) { return completedRevision < REVISION && !active; }

    public enum Hint { NONE, LOOK, MOVE, GRAB, EQUIP_MENU, FIRE, AIM, RELOAD, SWAP, FIGHT, WAIT }
    public record Objective(String chapter, String title, int count, int goal, Hint hint, Vec3 target) { }

    /** World side of a run. Marker lookups are scoped to one zone of this run's instance. */
    public interface Host {
        Optional<Marker> marker(Zone zone, String id);
        List<Marker> markers(Zone zone, String prefix);
        Vec3 position();
        boolean zoneReady(Zone zone);
        /** Queue (or prioritise) a budgeted build. Never places blocks in view of the player. */
        void prepareZone(Zone zone);
        /** Fade and teleport to a marker of a ready zone. */
        void place(Zone zone, Marker anchor);
        /** Returns duration ticks; 0 when unknown or the presentation service is absent. */
        int voice(String lineId);
        /** Null when the presentation service is unavailable. */
        Handle openingScan(Runnable done);
        default Handle openingScan(Vec3 vista, Runnable done) { return openingScan(done); }
        Handle ghostScan(Vec3 target, int ticks, Runnable done);
        Handle departure(Vec3 shipPos, float shipYaw, Runnable done);
        /** Parked Dock 13 ship (owner-only). Departure takes it over. Null when unavailable. */
        default Handle shipProp(Vec3 shipPos, float shipYaw) { return null; }
        /** Owner-only weapon pickup marker ("rifle" | "shotgun_cache"). Null when unavailable. */
        default RisingServices.PickupHandle pickup(Vec3 pos, float yaw, String kind) { return null; }
        void grantRifle();
        void grantShotgun();
        boolean ownsRifle();
        boolean holdingRifle();
        RisingEncounters.Spawner spawner(Zone zone);
        /** Return loans, leave for the Tower and store the revision. True once the player safely left. */
        boolean finish();
        void startMusic();
        void notice(String text);
        /** Content/service problem: logged for operators, shown once to the player. */
        void problem(String text);
        /** Persist {@link #snapshot()}. */
        void saved();
        /** False while a new Guardian has no class yet; the Ghost asks right after the opening scan. */
        default boolean classKnown() { return true; }
        /** Ghost asks which Guardian the player was (clickable choice, E-menu hint). Repeated asks are throttled by the host. */
        default void askClass() { }
        /** Class-specific Ghost line pair after a late choice (54/53, 56/59, 58/5e). */
        default void classLines() { }
        /** Switch every light.* marker of {@code phase} in {@code zone} to its lit block state. Idempotent. */
        default void lights(Zone zone, String phase) { }
        /** Presentation only (Skiff reinforcement arrival); never affects spawning. */
        default void waveIncoming(Zone zone, int index, List<RisingEncounters.Slot> wave, int ticks) { }
        default void waveSpawned(Zone zone, int index, List<RisingEncounters.Slot> wave) { }
    }

    public record Saved(GuardianRisesProgress.Snapshot progress, boolean rifle, boolean shotgun) { }

    /**
     * story lines (W301) survive a stage change and still play, in order, after the player has moved on;
     * barks (lost-player nudges, combat chatter) are dropped once their stage is over.
     */
    private record Line(String id, Stage stage, boolean story) { }

    private final Host host;
    private final GuardianRisesProgress progress;
    private boolean rifle, shotgun;
    private Zone zone;
    private Zone pendingZone;
    private List<String> pendingAnchor = List.of();
    private Handle handle;
    /** Dock 13 parked ship; independent of {@link #handle} (scans/departure come and go around it). */
    private Handle ship;
    private boolean shipTried;
    /** Weapon pickup marker; independent of {@link #handle} and {@link #ship}. */
    private RisingServices.PickupHandle pickup;
    private String pickupKind;
    private boolean pickupTried;
    private RisingEncounters.Run run;
    private RisingEncounters.Decor decor;
    private final Deque<Line> lines = new ArrayDeque<>();
    private int voiceUntil;
    private int clock;
    private int stageStart;
    private boolean a, b, c, done;
    private int at = -1;
    private boolean finishing;
    private int finishRetry;
    private boolean lostCueGiven;
    private boolean paused;
    private final Set<String> reported = new HashSet<>();

    public RisingMission(UUID instance, Saved saved, Host host) {
        this.host = Objects.requireNonNull(host);
        this.progress = new GuardianRisesProgress(instance, saved.progress());
        this.rifle = saved.rifle();
        this.shotgun = saved.shotgun();
    }

    // ---- public surface --------------------------------------------------------------------------------

    public Stage stage() { return progress.stage(); }
    public Zone zone() { return zone; }
    public boolean placing() { return pendingZone != null; }
    public boolean complete() { return progress.stage() == Stage.COMPLETE; }
    public boolean finishing() { return finishing; }
    public GuardianRisesProgress progress() { return progress; }
    public Saved snapshot() { return new Saved(progress.snapshot(), rifle, shotgun); }
    public Optional<RisingEncounters.Run> encounter() { return Optional.ofNullable(run).filter(RisingEncounters.Run::current); }
    public boolean rifleGranted() { return rifle; }
    public boolean shotgunGranted() { return shotgun; }

    /** Start (or restore from checkpoint) inside a ready instance. */
    public void begin(int now) {
        clock = now;
        if (!complete() && progress.snapshot().musicStarted()) host.startMusic();
        enter(progress.stage(), true);
    }

    public void tick(int now) {
        clock = now;
        if (paused || complete()) return;
        if (pendingZone != null) {
            if (!host.zoneReady(pendingZone)) { host.prepareZone(pendingZone); return; }
            var target = pendingZone;
            var anchor = find(target, pendingAnchor);
            pendingZone = null;
            if (anchor.isEmpty()) {
                report("anchor:" + target, "구역 " + target + "의 도착 지점 마커가 없습니다: " + pendingAnchor);
                anchor = host.markers(target, "").stream().findFirst();
            }
            if (anchor.isPresent()) {
                zone = target;
                host.place(target, anchor.get());
                next(target).ifPresent(host::prepareZone);
            } else {
                report("empty:" + target, "구역 " + target + "에 마커가 하나도 없습니다.");
                return;
            }
        }
        if (run != null) run.tick(now);
        speak(now);
        step(now);
    }

    /** Guardian down: reset the encounter and resume from the checkpoint. */
    public void onDeath() {
        if (complete() || finishing) return;
        if (progress.stage() == Stage.DEPARTURE) { enter(Stage.DEPARTURE, false); return; }
        retire();
        progress.restartCheckpoint();
        host.saved();
        enter(progress.stage(), true);
    }

    /** Operator QA jump. Grants what earlier stages would have granted. */
    public boolean skip(Stage target) {
        if (complete() || finishing || target == Stage.COMPLETE) return false;
        retire();
        if (!progress.forceStage(target)) return false;
        if (target.ordinal() > Stage.ARM_YOURSELF.ordinal() && !rifle) { rifle = true; host.grantRifle(); }
        if (target.ordinal() > Stage.SUPPLY_CACHE.ordinal() && !shotgun) { shotgun = true; host.grantShotgun(); }
        host.saved();
        enter(target, true);
        return true;
    }

    /** The owner disconnected: freeze enemies and drop cinematics; nothing advances while paused. */
    public void pause() {
        if (paused) return;
        paused = true;
        closeHandle();
        closeShip();
        closePickup();
        lines.clear();
        if (run != null) run.setActive(false);
    }

    /** The owner came back inside the grace window. Re-run interrupted beats without duplicating enemies. */
    public void resume(int now, boolean reposition) {
        clock = now;
        if (!paused) return;
        paused = false;
        if (!complete() && progress.snapshot().musicStarted()) host.startMusic();
        if (run != null) run.setActive(true);
        Stage stage = progress.stage();
        if (reposition) {
            zone = null;
            enter(stage, true);
            return;
        }
        switch (stage) {
            case GHOST_SCAN, DEPARTURE -> enter(stage, false);
            case BREACH_DARK -> { if (b && !done) { b = false; } }
            case SHIP_DEFENSE -> shipScan();
            default -> { }
        }
    }

    /** Remove everything this run owns from the world (instance closing). Idempotent. */
    public void close() {
        retire();
        lines.clear();
    }

    /** The player is lost for 45 s: one contextual Ghost nudge per stage. */
    public void lostCue() {
        if (lostCueGiven || paused || complete()) return;
        lostCueGiven = true;
        bark(progress.stage() == Stage.GATEWAY ? "80b75f79" : "80b75f76");
    }

    public Objective objective() {
        Stage stage = progress.stage();
        return switch (stage) {
            case GHOST_SCAN -> new Objective("부활", "고스트를 바라보세요", 0, 1, Hint.LOOK, null);
            case GATEWAY -> new Objective("관문", "장벽으로 향하세요", 0, 1, Hint.MOVE, pos(Zone.GATEWAY, "exit.breach", "trigger.wall"));
            case BREACH_DARK -> new Objective("돌파구", "어둠 속을 나아가세요", 0, 1, Hint.MOVE, pos(Zone.BREACH, "trigger.rifle", "prop.rifle"));
            case ARM_YOURSELF -> !rifle
                    ? new Objective("무장", "소총을 집으세요", 0, 1, Hint.GRAB, pos(Zone.BREACH, "prop.rifle", "trigger.rifle"))
                    : new Objective("무장", "소총을 손에 드세요", host.holdingRifle() ? 1 : 0, 1, Hint.EQUIP_MENU, null);
            case BREACH_FIGHT -> new Objective("돌파구", "몰락자를 처치하세요", run == null ? 0 : run.defeated(),
                    run == null ? 0 : run.total(), Hint.FIRE, nearestEnemy());
            case SUPPLY_CACHE -> !shotgun
                    ? new Objective("보급품", "은닉품을 챙기세요", 0, 1, Hint.GRAB, pos(Zone.BREACH, "prop.shotgun_cache", "trigger.cache"))
                    : new Objective("보급품", "돌파구를 빠져나가세요", 1, 1, Hint.SWAP, pos(Zone.BREACH, "exit.divide", "trigger.breach_exit"));
            case DIVIDE_WALKER -> run == null
                    ? new Objective("분할선", "전장으로 나아가세요", 0, 1, Hint.MOVE, pos(Zone.DIVIDE, "trigger.walker_arena"))
                    : new Objective("분할선", run.plan().hasWalker() ? "보행 탱크와 몰락자를 처치하세요" : "몰락자를 처치하세요",
                    run.defeated(), run.total(), Hint.FIGHT, nearestEnemy());
            case DOCK_13 -> zone == Zone.DOCK13
                    ? new Objective("13번 부두", "우주선 신호를 찾으세요", 0, 1, Hint.MOVE, pos(Zone.DOCK13, "trigger.ship", "prop.ship"))
                    : new Objective("13번 부두", "신호를 따라 부두로 가세요", 0, 1, Hint.MOVE, pos(Zone.DIVIDE, "exit.dock13", "trigger.dock_enter"));
            case SHIP_DEFENSE -> new Objective("13번 부두", "고스트가 시동을 거는 동안 버티세요", run == null ? 0 : run.defeated(),
                    run == null ? 0 : run.total(), Hint.FIGHT, nearestEnemy());
            case DEPARTURE -> new Objective("출발", "탑으로 향합니다", 0, 1, Hint.WAIT, null);
            case COMPLETE -> new Objective("완료", "탑에 도착했습니다", 1, 1, Hint.NONE, null);
        };
    }

    // ---- stage beats -----------------------------------------------------------------------------------

    private void enter(Stage stage, boolean place) {
        closeHandle();
        lines.removeIf(l -> l.stage() != stage && (!l.story() || l.stage().ordinal() < stage.ordinal() - 1));
        stageStart = clock;
        a = b = c = done = false;
        at = -1;
        lostCueGiven = false;
        if (place) go(anchorZone(stage), anchors(stage));
        applyLights(stage);
        switch (stage) {
            // The wake-up monologue (OpeningScan, c104b) ends on "이제 움직여야 해요"; the video continues with 64.
            case GATEWAY -> { say("80b75f64"); say("80b75f60"); }
            case BREACH_DARK -> { say("80b75f55"); say("80b75f5d"); }
            case ARM_YOURSELF -> { if (!rifle) say("80b75f50"); }
            case SUPPLY_CACHE -> { say("80b75f5c"); if (!shotgun) say("80b75f67"); }
            case DIVIDE_WALKER -> say("80b75f81");
            case DOCK_13 -> say("80b75f82");
            case SHIP_DEFENSE -> say("80b75f77");
            case DEPARTURE -> say("80b75f75");
            default -> { }
        }
    }

    private void step(int now) {
        if (pendingZone != null) return;
        int age = now - stageStart;
        parkedShip();
        pickups();
        switch (progress.stage()) {
            case GHOST_SCAN -> {
                if (!a) {
                    a = true;
                    if (progress.startMusicOnce()) { host.startMusic(); host.saved(); }
                    var token = progress.token();
                    handle = host.openingScan(pos(Zone.GATEWAY, "exit.breach", "trigger.wall"), () -> { if (progress.owns(token)) done = true; });
                    if (handle == null) { report("presentation", "연출 서비스가 없어 오프닝을 건너뜁니다."); at = now + 40; }
                }
                if (at >= 0 && now >= at) done = true;
                if (!done && handle != null && age > OPENING_TIMEOUT) closeHandle();
                if (done) {
                    closeHandle();
                    // Opening is scan-first: a class is asked for only after the Ghost has found the Guardian.
                    if (!host.classKnown()) { if (!c) { c = true; host.askClass(); } return; }
                    if (c && !b) { b = true; host.classLines(); }
                    advance(false);
                }
            }
            case GATEWAY -> {
                var exit = first(Zone.GATEWAY, "exit.breach", "trigger.wall");
                if (exit.isEmpty()) { missing("exit.breach", age); return; }
                if (near(exit.get(), 3)) advance(true);
            }
            case BREACH_DARK -> {
                if (!a) {
                    a = true;
                    var plan = RisingEncounters.decorations(host.markers(Zone.BREACH, "enemy."));
                    if (!plan.empty()) decor = new RisingEncounters.Decor(host.spawner(Zone.BREACH), plan);
                }
                if (!c && first(Zone.BREACH, "trigger.breach_dark").filter(m -> near(m, 4)).isPresent()) { c = true; say("80b75f80"); }
                if (!b) {
                    var trigger = first(Zone.BREACH, "trigger.rifle");
                    var rifleProp = first(Zone.BREACH, "prop.rifle");
                    boolean reached = trigger.map(m -> near(m, 4)).orElse(false) || rifleProp.map(m -> near(m, 9)).orElse(false);
                    if (trigger.isEmpty() && rifleProp.isEmpty()) { missing("trigger.rifle", age); return; }
                    if (reached) {
                        b = true;
                        Vec3 target = rifleProp.or(() -> trigger).get().pos();
                        var token = progress.token();
                        handle = host.ghostScan(target, 50, () -> { if (progress.owns(token)) done = true; });
                        if (handle == null) done = true;
                    }
                }
                if (done) { closeHandle(); advance(false); }
            }
            case ARM_YOURSELF -> {
                if (!rifle) {
                    var prop = first(Zone.BREACH, "prop.rifle", "trigger.rifle");
                    if (prop.isEmpty()) { missing("prop.rifle", age); if (age > MISSING_DATA_GRACE) grantRifleNow(); return; }
                    if (near(prop.get(), PICKUP_RADIUS)) grantRifleNow();
                    return;
                }
                if (!host.ownsRifle() && now % 40 == 0) host.grantRifle();
                if (!host.holdingRifle()) { at = -1; return; }
                if (at < 0) {
                    at = now + 60;
                    if (!c) { c = true; say("80b75f61"); }
                }
                if (now >= at) advance(false);
            }
            case BREACH_FIGHT -> {
                if (run == null) {
                    if (decor != null) { decor.discard(); decor = null; }
                    run = startRun(Zone.BREACH, i -> {
                        if (i.index() == 0) say("80b75f62");
                        else say(i.walker() ? "80b75f7f" : "80b75f65");
                    }, (d, t) -> { if (t >= 4 && d == t / 2) bark("80b75f6b"); });
                    if (run == null) return;
                }
                if (run.cleared()) advance(false);
            }
            case SUPPLY_CACHE -> {
                if (!shotgun) {
                    var cache = first(Zone.BREACH, "prop.shotgun_cache", "trigger.cache");
                    if (cache.isEmpty()) { missing("prop.shotgun_cache", age); if (age > MISSING_DATA_GRACE) grantShotgunNow(); return; }
                    if (near(cache.get(), PICKUP_RADIUS)) grantShotgunNow();
                    return;
                }
                var exit = first(Zone.BREACH, "exit.divide", "trigger.breach_exit");
                if (exit.isEmpty()) { missing("exit.divide", age); if (age > MISSING_DATA_GRACE) advance(true); return; }
                if (near(exit.get(), 3)) advance(true);
            }
            case DIVIDE_WALKER -> {
                if (run == null) {
                    var arena = first(Zone.DIVIDE, "trigger.walker_arena");
                    if (arena.isPresent() ? near(arena.get(), 8) || age > ARENA_FALLBACK : age > 40) {
                        run = startRun(Zone.DIVIDE, i -> {
                            if (i.walker()) { alert("80b75f78"); alert("80b75f7f"); } // jumps the queue: "조심해요! 보행 탱크에요!" first
                            else if (i.index() > 0) bark("80b75f7b");
                        }, (d, t) -> { });
                    }
                    return;
                }
                if (run.cleared()) advance(false);
            }
            case DOCK_13 -> {
                if (zone != Zone.DOCK13) {
                    if (age == 20 * 15) say("80b75f83");
                    var exit = first(Zone.DIVIDE, "exit.dock13", "trigger.dock_enter");
                    if (exit.isEmpty()) { missing("exit.dock13", age); if (age > MISSING_DATA_GRACE) go(Zone.DOCK13, anchors(Stage.DOCK_13)); return; }
                    if (near(exit.get(), 3)) go(Zone.DOCK13, anchors(Stage.DOCK_13));
                    return;
                }
                if (!a) { a = true; say("80b75f84"); }
                var ship = first(Zone.DOCK13, "trigger.ship");
                var prop = first(Zone.DOCK13, "prop.ship");
                if (ship.isEmpty() && prop.isEmpty()) { missing("trigger.ship", age); if (age > MISSING_DATA_GRACE) advance(false); return; }
                if (ship.map(m -> near(m, 6)).orElse(false) || prop.map(m -> near(m, 12)).orElse(false)) advance(false);
            }
            case SHIP_DEFENSE -> {
                if (run == null) {
                    shipScan();
                    run = startRun(Zone.DOCK13, i -> say(switch (i.index()) {
                        case 0 -> "80b75f7a";
                        case 1 -> "80b75f52";
                        case 2 -> "80b75f74";
                        default -> "80b75f7b";
                    }), (d, t) -> { });
                    if (run == null) return;
                }
                if (run.cleared()) { closeHandle(); advance(false); }
            }
            case DEPARTURE -> {
                if (finishing) {
                    if (now >= finishRetry) {
                        if (host.finish()) {
                            closeHandle();
                            finishing = false;
                            progress.advance(progress.token());
                            host.saved();
                        } else finishRetry = now + 40;
                    }
                    return;
                }
                if (!a && age >= 40) {
                    a = true;
                    var ship = first(Zone.DOCK13, "prop.ship", "trigger.ship");
                    var token = progress.token();
                    Runnable black = () -> { if (progress.owns(token)) done = true; };
                    handle = ship.isPresent() ? host.departure(ship.get().pos(), ship.get().yaw(), black) : null;
                    closeShip(); // departure took the parked ship over (or never got one); never two ships
                    if (handle == null) {
                        report("departure", "출발 연출을 재생할 수 없어 안전한 출발로 진행합니다.");
                        at = now + 60;
                    }
                }
                if (at >= 0 && now >= at) done = true;
                if (!done && handle != null && age > DEPARTURE_TIMEOUT) closeHandle();
                if (done) { finishing = true; finishRetry = now; }
            }
            case COMPLETE -> { }
        }
    }

    private record WaveCue(int index, int total, boolean walker) { }
    private interface WaveHook { void wave(WaveCue cue); }
    private interface KillHook { void killed(int defeated, int total); }

    private RisingEncounters.Run startRun(Zone where, WaveHook waves, KillHook kills) {
        var plan = RisingEncounters.plan(host.markers(where, "enemy."));
        if (plan.empty()) {
            report("encounter:" + where, "구역 " + where + "의 전투 마커가 없습니다. 관리자가 /destiny rising skip 으로 진행해야 합니다.");
            return null;
        }
        var cues = new RisingEncounters.Cues() {
            @Override public void wave(int index, int total, boolean walker) { waves.wave(new WaveCue(index, total, walker)); }
            @Override public void defeated(int d, int t) { kills.killed(d, t); }
            @Override public void incoming(int index, int total, List<RisingEncounters.Slot> wave, int ticks) { host.waveIncoming(where, index, wave, ticks); }
            @Override public void spawned(int index, int total, List<RisingEncounters.Slot> wave) { host.waveSpawned(where, index, wave); }
            @Override public void spawnFailure(RisingEncounters.Slot slot, int attempts) {
                if (attempts == 5) host.problem("적 생성 실패가 반복됩니다: " + slot.markerId() + " (" + slot.kind() + ")");
            }
        };
        var started = new RisingEncounters.Run(progress, plan, host.spawner(where), cues, clock);
        started.tick(clock);
        return started;
    }

    /** Phase lights persist in the world, but zones are rebuilt on restart: re-apply from the stage. */
    private void applyLights(Stage stage) {
        if (stage.ordinal() >= Stage.ARM_YOURSELF.ordinal() && stage.ordinal() <= Stage.SUPPLY_CACHE.ordinal())
            host.lights(Zone.BREACH, "breach_lightup");
        if (stage.ordinal() >= Stage.SHIP_DEFENSE.ordinal()) host.lights(Zone.DOCK13, "ship_scan");
    }

    private void shipScan() {
        host.lights(Zone.DOCK13, "ship_scan");
        closeHandle();
        var ship = first(Zone.DOCK13, "prop.ship", "trigger.ship");
        if (ship.isPresent()) handle = host.ghostScan(ship.get().pos(), 20 * 180, () -> { });
    }

    private void grantRifleNow() {
        collectPickup(RIFLE_PROP);
        rifle = true;
        host.grantRifle();
        host.saved();
    }
    private void grantShotgunNow() {
        collectPickup(CACHE_PROP);
        shotgun = true;
        host.grantShotgun();
        say("80b75f6f");
        host.saved();
    }

    private void advance(boolean nextZone) {
        Stage from = progress.stage();
        if (!progress.advance(progress.token())) return;
        if (run != null) { run.discard(); run = null; }
        host.saved();
        Stage to = progress.stage();
        if (nextZone) {
            Zone target = anchorZone(to);
            go(target, anchors(to));
        }
        if (from != to) enter(to, false);
    }

    // ---- helpers ---------------------------------------------------------------------------------------

    private void go(Zone target, List<String> anchor) {
        pendingZone = target;
        pendingAnchor = anchor;
        if (!host.zoneReady(target)) {
            host.prepareZone(target);
            host.notice("고스트가 앞길을 살피고 있어요…");
        }
    }

    private void retire() {
        closeHandle();
        closeShip();
        closePickup();
        if (run != null) { run.discard(); run = null; }
        if (decor != null) { decor.discard(); decor = null; }
        finishing = false;
    }

    /** Keeps the parked ship up from arriving at Dock 13 until the departure starts. */
    private void parkedShip() {
        Stage stage = progress.stage();
        boolean wanted = zone == Zone.DOCK13 && (stage == Stage.DOCK_13 || stage == Stage.SHIP_DEFENSE
                || stage == Stage.DEPARTURE && !a && !finishing);
        if (!wanted) { if (ship != null && stage != Stage.DEPARTURE) closeShip(); return; }
        if (ship != null || shipTried) return;
        shipTried = true;
        var marker = first(Zone.DOCK13, "prop.ship", "trigger.ship");
        if (marker.isPresent()) ship = host.shipProp(marker.get().pos(), marker.get().yaw());
    }

    /** Rifle marker from BREACH_DARK until the rifle is taken; cache marker in SUPPLY_CACHE until the shotgun. */
    private void pickups() {
        Stage stage = progress.stage();
        String want = null;
        Optional<Marker> where = Optional.empty();
        if (zone == Zone.BREACH && !rifle && (stage == Stage.BREACH_DARK || stage == Stage.ARM_YOURSELF)) {
            want = RIFLE_PROP;
            where = first(Zone.BREACH, "prop.rifle", "trigger.rifle");
        } else if (zone == Zone.BREACH && !shotgun && stage == Stage.SUPPLY_CACHE) {
            want = CACHE_PROP;
            where = first(Zone.BREACH, "prop.shotgun_cache", "trigger.cache");
        }
        if (!Objects.equals(want, pickupKind)) closePickup();
        if (want == null || pickup != null || pickupTried || where.isEmpty()) return;
        pickupTried = true;
        pickupKind = want;
        pickup = host.pickup(where.get().pos(), where.get().yaw(), want);
    }

    private void collectPickup(String kind) {
        var h = pickup;
        if (h == null || !kind.equals(pickupKind)) return;
        pickup = null;
        pickupKind = null;
        pickupTried = false;
        h.collect();
    }

    private void closePickup() {
        var h = pickup;
        pickup = null;
        pickupKind = null;
        pickupTried = false;
        if (h != null) h.close();
    }

    private void closeShip() {
        var h = ship;
        ship = null;
        shipTried = false;
        if (h != null) h.close();
    }

    private void closeHandle() {
        var h = handle;
        handle = null;
        if (h != null) h.close();
    }

    private void say(String id) { lines.add(new Line(id, progress.stage(), true)); }
    private void bark(String id) { lines.add(new Line(id, progress.stage(), false)); }
    /** Urgent call-out: plays next, ahead of any story backlog. */
    private void alert(String id) { lines.addFirst(new Line(id, progress.stage(), true)); }

    private void speak(int now) {
        if (now < voiceUntil) return;
        Line next;
        while ((next = lines.poll()) != null && !next.story() && next.stage() != progress.stage()) { }
        if (next == null) return;
        int ticks = host.voice(next.id());
        voiceUntil = now + (ticks > 0 ? ticks : 60) + 8;
    }

    private void missing(String id, @SuppressWarnings("unused") int age) {
        report("missing:" + progress.stage() + ":" + id, progress.stage() + " 단계의 마커 " + id + "가 없습니다.");
    }

    private void report(String key, String text) {
        if (reported.add(key)) host.problem(text);
    }

    private Optional<Marker> first(Zone where, String... ids) { return find(where, List.of(ids)); }
    private Optional<Marker> find(Zone where, List<String> ids) {
        for (String id : ids) {
            var m = host.marker(where, id);
            if (m.isPresent()) return m;
        }
        return Optional.empty();
    }
    private Vec3 pos(Zone where, String... ids) { return first(where, ids).map(Marker::pos).orElse(null); }
    private Vec3 nearestEnemy() { return run == null ? null : run.nearest(host.position()).orElse(null); }

    /** Horizontal radius / vertical height from marker tags, falling back to the stage default. */
    boolean near(Marker m, double defaultRadius) {
        double r = tag(m, "radius", defaultRadius);
        double h = tag(m, "height", Math.max(3, r));
        Vec3 p = host.position();
        double dx = p.x - m.pos().x, dz = p.z - m.pos().z;
        return dx * dx + dz * dz <= r * r && Math.abs(p.y - m.pos().y) <= h;
    }
    private static double tag(Marker m, String key, double fallback) {
        String v = m.tags().get(key);
        if (v == null) return fallback;
        try { double d = Double.parseDouble(v); return d > 0 ? d : fallback; } catch (NumberFormatException e) { return fallback; }
    }

    static Zone anchorZone(Stage stage) {
        return switch (stage) {
            case GHOST_SCAN, GATEWAY -> Zone.GATEWAY;
            case BREACH_DARK, ARM_YOURSELF, BREACH_FIGHT, SUPPLY_CACHE -> Zone.BREACH;
            case DIVIDE_WALKER -> Zone.DIVIDE;
            case DOCK_13, SHIP_DEFENSE, DEPARTURE, COMPLETE -> Zone.DOCK13;
        };
    }
    static List<String> anchors(Stage stage) {
        return switch (stage) {
            case GHOST_SCAN, GATEWAY -> List.of("spawn.player", "checkpoint.ghost_scan");
            case BREACH_DARK -> List.of("checkpoint.breach_dark", "spawn.player", "trigger.breach_dark", "checkpoint.arm_yourself");
            case ARM_YOURSELF, BREACH_FIGHT -> List.of("checkpoint.arm_yourself", "trigger.rifle", "prop.rifle", "spawn.player");
            case SUPPLY_CACHE -> List.of("trigger.cache", "prop.shotgun_cache", "checkpoint.arm_yourself", "spawn.player");
            case DIVIDE_WALKER -> List.of("checkpoint.divide_walker", "trigger.divide_enter", "spawn.player");
            case DOCK_13 -> List.of("checkpoint.dock_13", "trigger.dock_enter", "spawn.player");
            case SHIP_DEFENSE, DEPARTURE, COMPLETE -> List.of("trigger.ship", "checkpoint.dock_13", "spawn.player");
        };
    }
    static Optional<Zone> next(Zone zone) {
        int i = zone.ordinal() + 1;
        return i < Zone.values().length ? Optional.of(Zone.values()[i]) : Optional.empty();
    }
}
