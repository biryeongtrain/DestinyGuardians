package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.down.GuardianDown;
import kim.biryeong.minigamelib.music.MusicPacks;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import static kim.biryeong.destiny.strike.devils.DevilsPlan.Zone;

/** Server-thread session adapter. Generation-owned cameras and callbacks never outlive their encounter. */
public final class DevilsSession implements DevilsDirector.Host, DevilsRecovery.Host, DevilsActors.Environment {
    private enum State { PREPARING, ADMITTING, RUNNING, DRAINING, CLOSED }
    private final MinecraftServer server;
    private final DevilsInstances instances;
    private final DevilsInstances.Instance instance;
    private final List<UUID> ids;
    private final Set<UUID> departed = new HashSet<>();
    private final DevilsRoster roster;
    private final DevilsWorldBuild build;
    private final DevilsDirector director;
    private final DevilsActors actors;
    private final DevilsRecovery recovery;
    private final DevilsSupplies supplies;
    private final DevilsSupplyStations supplyStations;
    private final Set<UUID> supplySneaking = new HashSet<>();
    private final Map<UUID, Zone> pendingSupplyReset = new HashMap<>();
    private final Map<UUID, kim.biryeong.destiny.activity.presentation.ObjectiveGuide> guides = new HashMap<>();
    private final DevilsLair.Presentation presentation;
    private final DevilsMusic music = new DevilsMusic();
    private DevilsVoicePlayback voice;
    private DevilsDirector.Cue speaking;
    private final Map<UUID, GuardianDown.Options> downOptions = new HashMap<>();
    private final Map<UUID, Vec3> downBodies = new HashMap<>();
    private final Map<UUID, Vec3> supportedPositions = new HashMap<>();
    private final Map<UUID, DevilsRecovery.Revival> revivals = new HashMap<>();
    private final Map<UUID, Integer> deviceHolds = new HashMap<>();
    private final Set<UUID> joining = new HashSet<>();
    private final Set<UUID> joinPlaced = new HashSet<>();
    private final List<AABB> reservations = new ArrayList<>();
    private final Map<String, DevilsSpatial.Search> spawnSearches = new HashMap<>();
    private DevilsDirector.ActorRef deferredSpawn;
    private final DevilsSpawnTelegraphs spawnTelegraphs = new DevilsSpawnTelegraphs();
    private final Map<String, Integer> spawnLead = new HashMap<>();
    private final Set<String> problems = new HashSet<>();
    private State state = State.PREPARING;
    private long createdAt, admittedAt, gatherAt = -1, completeAt = -1;
    private boolean resetPlacement;

    DevilsSession(MinecraftServer server, DevilsInstances instances, DevilsInstances.Instance instance,
                  List<ServerPlayer> players) {
        this.server = server; this.instances = instances; this.instance = instance;
        this.ids = players.stream().map(ServerPlayer::getUUID).toList();
        roster = new DevilsRoster(ids); build = new DevilsWorldBuild(instance.level());
        director = new DevilsDirector(this); recovery = new DevilsRecovery(instance.id(), ids, this);
        supplies = new DevilsSupplies(ids);
        supplyStations = new DevilsSupplyStations(instance.level());
        actors = new DevilsActors(instance.level(), () -> director, this);
        voice = newVoice(); presentation = DevilsLair.presentationFor(this);
        recovery.reset(director.generation(), Zone.RY); createdAt = server.getTickCount();
        instances.own(instance, build::close); instances.own(instance, actors::close);
        instances.own(instance, recovery::close); instances.own(instance, () -> voice.close());
        instances.own(instance, presentation::close);
        instances.own(instance, supplies::close);
        instances.own(instance, () -> { guides.values().forEach(kim.biryeong.destiny.activity.presentation.ObjectiveGuide::clear); guides.clear(); });
        instances.own(instance, music::close);
        instances.own(instance, supplyStations::close);
    }
    private DevilsVoicePlayback newVoice() {
        return new DevilsVoicePlayback(this::players, token -> {
            var cue = speaking;
            if (cue != null && cue.serial() == token && cue.generation() == director.generation()) {
                speaking = null; director.cueFinished(cue);
            }
        });
    }
    public UUID id() { return instance.id(); }
    public ServerLevel level() { return instance.level(); }
    public DevilsDirector director() { return director; }
    public boolean member(UUID id) { return ids.contains(id) && !departed.contains(id); }
    public boolean closed() { return state == State.CLOSED; }
    public boolean running() { return state == State.RUNNING; }
    private boolean readyLivingAudience(ServerPlayer p) { return running() && !joining.contains(p.getUUID()) && !resetPlacement
            && p.level() == level() && recovery.token(p.getUUID()).isEmpty() && ready(p); }
    public boolean allows(ServerPlayer p) { return readyLivingAudience(p) && !presentation.hidden(p); }
    public String status() { var s = director.snapshot(); return state + " / " + s.phase() + " / " + s.occupied() + "/" + s.zone().actorCap(); }
    public List<ServerPlayer> players() {
        return ids.stream().filter(this::member).map(id -> server.getPlayerList().getPlayer(id))
                .filter(Objects::nonNull).filter(p -> !p.hasDisconnected()).toList();
    }
    @Override public List<ServerPlayer> participants() { return players().stream().filter(this::allows)
            .filter(p -> p.level() == level()).toList(); }

    void tick(long now, long buildBudget) {
        if (state == State.CLOSED) return;
        if (state == State.DRAINING) { drain(); return; }
        reservations.clear();
        pruneSpawnTelegraphs(director.snapshot());
        for (var outsider : List.copyOf(level().players())) if (!member(outsider.getUUID())) {
            if (!DevilsLair.restore(outsider) || outsider.level() == level()) {
                var target = server.overworld(); var at = Vec3.atBottomCenterOf(target.getRespawnData().pos());
                DevilsLair.cleanup(outsider);
                outsider.teleportTo(target, at.x, at.y, at.z, Set.of(), 0, 0, true);
            }
        }
        roster.expire(now);
        for (var m : roster.members()) if (m.expired()) departed.add(m.id());
        if (roster.abandoned(now) || players().isEmpty() && ids.stream().noneMatch(this::member)) { stop("화력팀 접속 종료"); return; }
        if (state == State.PREPARING) {
            if (now - createdAt > 12000) { stop("맵 준비 시간 초과"); return; }
            build.tick(buildBudget);
            if (build.state() == DevilsWorldBuild.State.FAILED || build.state() == DevilsWorldBuild.State.CANCELLED) {
                stop("맵 준비 실패"); return;
            }
            if (build.state() != DevilsWorldBuild.State.READY) return;
            if (!supplyStations.prepare()) { problem("Safe supply station placement unavailable"); return; }
            if (players().size() != ids.size() || players().stream().anyMatch(p -> !ready(p))) return;
            if (!place(Zone.RY, players(), true)) return;
            instances.ready(instance); state = State.ADMITTING; admittedAt = now; return;
        }
        if (state == State.ADMITTING) {
            if (now - admittedAt > 1200) { stop("입장 확인 시간 초과"); return; }
            for (var p : players()) roster.ready(p.getUUID(), p.level() == level() && ready(p));
            if (!roster.allReady()) return;
            state = State.RUNNING; instances.running(instance); syncPresence(); director.begin(ids.size());
        }
        for (var p : players()) {
            if (joining.contains(p.getUUID())) {
                if (!ready(p)) continue;
                if (!joinPlaced.contains(p.getUUID())) {
                    if (!place(director.phase().zone(), List.of(p), false)) continue;
                    joinPlaced.add(p.getUUID()); roster.ready(p.getUUID(), false); continue;
                }
                joining.remove(p.getUUID()); joinPlaced.remove(p.getUUID()); roster.ready(p.getUUID(), true);
                // A downed reconnect must restore the existing down scene, never become alive merely by joining.
                var token = recovery.token(p.getUUID());
                if (token.isPresent()) {
                    var options = downOptions.get(p.getUUID());
                    if (options != null) restoreDown(p, options);
                }
            } else if (p.level() != level()) { leave(p); }
            else if (recovery.token(p.getUUID()).isPresent() && !GuardianDown.active(p)) {
                var option = downOptions.get(p.getUUID()); if (option != null) restoreDown(p, option);
            }
        }
        if (!resetPlacement) checkFalls();
        if (state != State.RUNNING) return;
        syncPresence();
        boolean paused = roster.connected() == 0 || resetPlacement;
        boolean noTargets = participants().isEmpty();
        var pause = DevilsPausePolicy.forPresence(paused, players().stream().anyMatch(this::readyLivingAudience), !noTargets);
        director.pause(pause.progress()); actors.tick(pause.actors());
        if (resetPlacement) {
            if (place(director.phase().zone(), players(), false)) { resetPlacement = false; resetRecovery(); }
            return;
        }
        if (!paused) {
            inputs(); recovery.tick(); syncReviveAudio();
            if (resetPlacement || state != State.RUNNING) return;
            if (!pause.progress()) voice.tick();
            director.tick(); transition(now);
        }
        presentation.tick(this, paused);
        music.tick(director.phase(), players().stream().filter(p -> p.level() == level() && !joining.contains(p.getUUID())).toList(), System.nanoTime());
        guides(now);
        if (now % 4 == 0) for (var p : players()) if (p.level() == level()) {
            DevilsObjectives.render(p, director.snapshot(), atDevice(p), GuardianDown.active(p) || presentation.hidden(p),
                    allows(p) && supplyStations.lookingAt(p, director.phase().zone()),
                    supplies.available(p.getUUID(), director.phase().zone()),
                    remainingSeconds(gatherAt, 300, now), remainingSeconds(completeAt, 600, now), voice.playing());

        }
        if (completeAt >= 0 && now - completeAt >= 600 && !voice.playing()) stop("공격전 완료");
    }
    /** Shared waypoint + breadcrumb guidance; hidden while downed, in cinematics or still being placed. */
    private void guides(long now) {
        var target = DevilsGuide.target(director.phase(), (zone, id) -> DevilsMaps.anchor(zone, id, DevilsWorldBuild.origin(zone)).pos());
        for (var p : players()) {
            if (p.level() != level()) continue;
            var guide = guides.get(p.getUUID());
            if (guide != null && guide.owner() != p) { guide.clear(); guide = null; }
            if (guide == null) guides.put(p.getUUID(), guide = new kim.biryeong.destiny.activity.presentation.ObjectiveGuide(p));
            boolean hidden = joining.contains(p.getUUID()) || GuardianDown.active(p) || presentation.hidden(p)
                    || recovery.token(p.getUUID()).isPresent();
            guide.tick(target, hidden, (int) now);
        }
    }
    private void clearGuide(ServerPlayer p) { var g = guides.remove(p.getUUID()); if (g != null) g.clear(); }
    static int remainingSeconds(long startedAt, int durationTicks, long now) {
        if (startedAt < 0) return -1;
        return (int) ((Math.max(0L, durationTicks - Math.max(0L, now - startedAt)) + 19) / 20);
    }
    private boolean ready(ServerPlayer p) { return p.connection.hasClientLoaded() && MusicPacks.ready(p); }
    private boolean supported(ServerPlayer p, Vec3 at) {
        return contains(director.phase().zone(), at) && DevilsSpatial.groundedPlayer(level(), p, at);
    }
    private void checkFalls() {
        Zone zone = director.phase().zone();
        var origin = DevilsWorldBuild.origin(zone); var size = DevilsMaps.dimensions(zone);
        for (var p : participants()) {
            Vec3 at = p.position();
            // No ceiling kill plane: class jumps may rise above the authored map volume.
            boolean outside = at.y < origin.getY() - 4 || at.x < origin.getX() || at.z < origin.getZ()
                    || at.x >= origin.getX() + size.getX() || at.z >= origin.getZ() + size.getZ();
            if (!outside) {
                if (p.onGround() && supported(p, at)) supportedPositions.put(p.getUUID(), at);
                continue;
            }
            Vec3 body = supportedPositions.get(p.getUUID());
            if (body == null || !supported(p, body)) {
                var seat = DevilsSpatial.seat(level(), zone, origin, p, ids.indexOf(p.getUUID()), List.of());
                if (seat.isEmpty()) { stop("추락 후 안전한 부활 지점을 찾지 못했습니다."); return; }
                body = seat.get().pos();
            }
            var option = downed(p);
            if (option == null) continue;
            downBodies.put(p.getUUID(), body);
            DevilsLair.cleanup(p);
            if (!GuardianDown.fallOwned(p, option, body)) restoreDown(p, option);
        }
    }
    private void syncPresence() {
        for (var m : roster.members()) recovery.presence(m.id(), m.connected() && member(m.id()), m.ready() && !joining.contains(m.id()));
    }
    private boolean place(Zone zone, List<ServerPlayer> group, boolean initial) {
        var points = new LinkedHashMap<ServerPlayer, DevilsSpatial.Point>(); var boxes = new ArrayList<AABB>();
        for (var p : group) {
            var point = DevilsSpatial.seat(level(), zone, DevilsWorldBuild.origin(zone), p, ids.indexOf(p.getUUID()), boxes);
            if (point.isEmpty()) { problem("Safe checkpoint seat unavailable in " + zone); return false; }
            points.put(p, point.get()); boxes.add(DevilsSpatial.bodyAt(p, point.get().pos()));
        }
        for (var e : points.entrySet()) {
            var p = e.getKey(); var at = e.getValue();
            if (initial) DevilsLair.saveReturn(p);
            cancelDown(p); DevilsLair.cleanup(p);
            if (!p.teleportTo(level(), at.pos().x, at.pos().y, at.pos().z, Set.of(), at.yaw(), 0, true)) {
                stop("안전한 이동을 완료하지 못했습니다."); return false;
            }
            p.setGameMode(GameType.SURVIVAL); p.setHealth(p.getMaxHealth());
            supportedPositions.put(p.getUUID(), at.pos());
            supplies.entry(p, zone);
            if (pendingSupplyReset.remove(p.getUUID()) == zone) supplies.reset(p, zone);
            roster.ready(p.getUUID(), !initial); p.clearFire();
        }
        return true;
    }
    private void transition(long now) {
        Zone next = switch (director.phase()) { case RY_CLEAR -> Zone.RF; case RF_CLEAR -> Zone.BL; case BL_CLEAR -> Zone.SP; default -> null; };
        if (next == null) { gatherAt = -1; return; }
        var living = participants(); if (living.isEmpty()) { gatherAt = -1; return; }
        Zone zone = director.phase().zone();
        String exit = zone == Zone.RY ? "RY.OUT" : zone.name() + ".EXIT";
        var at = DevilsMaps.anchor(zone, exit, DevilsWorldBuild.origin(zone)).pos();
        long gathered = living.stream().filter(p -> p.position().distanceToSqr(at) <= 36).count();
        if (gathered == 0) { gatherAt = -1; return; }
        if (gatherAt < 0) gatherAt = now;
        if (gathered != living.size() && now - gatherAt < 300) return;
        if (place(next, players(), false) && director.arrive(next)) { resetRecovery(); gatherAt = -1; }
    }
    private boolean atDevice(ServerPlayer p) { return director.phase() == DevilsDirector.Phase.RF_DEVICE && p.level() == level()
            && p.position().distanceToSqr(DevilsMaps.anchor(Zone.RF, "RF.G", DevilsWorldBuild.origin(Zone.RF)).pos()) <= 9; }
    private void inputs() {
        for (var p : players()) {
            boolean freshSneak = p.isShiftKeyDown() && supplySneaking.add(p.getUUID());
            if (!p.isShiftKeyDown()) supplySneaking.remove(p.getUUID());
            var token = recovery.token(p.getUUID());
            if (token.isPresent()) { if (p.getLastClientInput().jump()) recovery.self(token.get()); continue; }
            if (!allows(p)) continue;
            var zone = director.phase().zone();
            if (supplyStations.lookingAt(p, zone)) {
                deviceHolds.remove(p.getUUID());
                if (freshSneak && supplies.use(p, zone))
                    p.connection.send(new net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket(Component.literal("탄약 보급 완료")));
            }
            int held = p.isShiftKeyDown() && atDevice(p) ? deviceHolds.getOrDefault(p.getUUID(), 0) + 1 : 0;
            deviceHolds.put(p.getUUID(), held);
            if (held >= 40 && director.snapshot().deviceReady()) { director.interact(); deviceHolds.clear(); }
            for (var target : players()) {
                var down = recovery.token(target.getUUID()); if (down.isEmpty()) continue;
                var option = downOptions.get(target.getUUID()); if (option == null) continue;
                var body = GuardianDown.bodyOwned(target, option); if (body.isEmpty()) continue;
                Vec3 aim = body.get().add(0, .75, 0);
                if (p.position().distanceToSqr(body.get()) <= 9 && level().clip(new ClipContext(p.getEyePosition(), aim,
                        ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p)).getType() == HitResult.Type.MISS) {
                    recovery.hold(p.getUUID(), down.get()); break;
                }
            }
        }
    }
    private void syncReviveAudio() {
        for (var member : recovery.snapshot().members()) {
            var player = server.getPlayerList().getPlayer(member.player());
            var option = downOptions.get(member.player());
            if (player != null && option != null)
                GuardianDown.progressOwned(player, option, member.helper(), member.holdTicks(), players());
        }
    }
    GuardianDown.Options downed(ServerPlayer p) {
        if (!running() || p.level() != level() || !member(p.getUUID()) || joining.contains(p.getUUID())) return null;
        if (recovery.down(p.getUUID(), director.generation()).isEmpty()) return null;
        kim.biryeong.destiny.down.FireteamReviveAudio.announce(p, players());
        roster.down(p.getUUID(), true); downBodies.put(p.getUUID(), p.position());
        return downOptions.computeIfAbsent(p.getUUID(), id -> new GuardianDown.Options(false, director.phase().zone() == Zone.RY ? 100 : 600, true,
                false, "악마의 소굴", this::reviveFinished, 60, true, true));
    }
    @Override public boolean revive(DevilsRecovery.Revival request) {
        var p = server.getPlayerList().getPlayer(request.down().player());
        if (p == null || p.level() != level() || request.down().generation() != director.generation()) return false;
        var option = downOptions.get(p.getUUID()); if (option == null) return false;
        revivals.put(p.getUUID(), request);
        if (GuardianDown.reviveOwned(p, option)) return true;
        revivals.remove(p.getUUID(), request); return false;
    }
    private void reviveFinished(ServerPlayer p) {
        var request = revivals.remove(p.getUUID());
        if (request == null || request.down().generation() != director.generation() || !running() || p.level() != level()) return;
        boolean safe = supported(p, p.position());
        if (!safe) {
            var point = DevilsSpatial.seat(level(), director.phase().zone(), DevilsWorldBuild.origin(director.phase().zone()),
                    p, ids.indexOf(p.getUUID()), List.of());
            if (point.isEmpty() || !p.teleportTo(level(), point.get().pos().x, point.get().pos().y,
                    point.get().pos().z, Set.of(), point.get().yaw(), 0, true)) {
                recovery.failed(request); p.setGameMode(GameType.SPECTATOR); return;
            }
        }
        if (!recovery.revived(request)) return;
        roster.down(p.getUUID(), false); downOptions.remove(p.getUUID()); downBodies.remove(p.getUUID());
        GuardianDown.clearExternalHud(p);
    }
    @Override public void cancel(DevilsRecovery.Revival request) {
        UUID id = request.down().player(); if (!revivals.remove(id, request)) return;
        var p = server.getPlayerList().getPlayer(id); if (p != null) cancelDown(p);
    }
    private void cancelDown(ServerPlayer p) {
        var option = downOptions.get(p.getUUID()); if (option != null) GuardianDown.cancelOwned(p, option);
        GuardianDown.clearExternalHud(p);
    }
    private void restoreDown(ServerPlayer p, GuardianDown.Options option) {
        Vec3 body = downBodies.getOrDefault(p.getUUID(), p.position());
        if (!contains(director.phase().zone(), body)) body = p.position();
        int remaining = recovery.snapshot().members().stream().filter(m -> m.player().equals(p.getUUID()))
                .mapToInt(DevilsRecovery.Member::readyIn).findFirst().orElse(option.readyTicks());
        if (!GuardianDown.resumeOwned(p, option, body, remaining)) {
            p.setGameMode(GameType.SPECTATOR);
            problem("Owned down scene could not resume for " + p.getUUID());
        }
    }
    @Override public void wipe(long generation) {
        if (generation == director.generation() && running()) director.resetCheckpoint("화력팀 전멸");
    }
    @Override public void checkpointReset(Zone zone, long generation, String reason) {
        problem("Checkpoint reset " + zone + ": " + reason);
        resetPlacement = true; director.pause(true);
        for (var id : ids) if (member(id)) pendingSupplyReset.put(id, zone);
        for (var p : players()) cancelDown(p);
    }
    private void resetRecovery() {
        recovery.reset(director.generation(), director.phase().zone());
        downOptions.clear(); downBodies.clear(); revivals.clear(); deviceHolds.clear();
        for (var m : roster.members()) roster.down(m.id(), false);
        syncPresence();
    }
    public void introFinished(long generation) { if (running()) director.introFinished(generation); }
    @Override public boolean spawn(DevilsDirector.Spawn spawn) {
        deferredSpawn = null;
        boolean accepted = running() && !resetPlacement && actors.spawn(spawn);
        if (accepted) spawnLead.remove(spawn.slot().id());
        var search = spawnSearches.get(spawn.slot().id());
        if (!accepted && (spawnTelegraphs.get(director.generation(), spawn.slot().id()) != null
                || search != null && (search.pending() || search.waiting()))) deferredSpawn = spawn.ref();
        else spawnSearches.remove(spawn.slot().id());
        return accepted;
    }
    @Override public boolean spawnDeferred(DevilsDirector.ActorRef ref) { return ref.equals(deferredSpawn); }
    @Override public boolean managesSpawnTelegraphs() { return true; }
    @Override public int spawnRetryTicks(DevilsDirector.ActorRef ref) {
        var warning = spawnTelegraphs.get(ref.generation(), ref.slotId());
        if (warning != null) return (int)Math.clamp(warning.readyAt() - director.snapshot().tick(), 1, 20);
        var search = spawnSearches.get(ref.slotId());
        return search != null && search.waiting() ? 10 : 1;
    }
    @Override public void retire(DevilsDirector.ActorRef actor, DevilsDirector.Retirement reason) { actors.retire(actor, reason); }
    @Override public Optional<Vec3> spawnPoint(DevilsPlan.Slot slot, DevilsMob probe) {
        var occupied = new ArrayList<>(reservations);
        occupied.addAll(spawnTelegraphs.reservations(slot.id()));
        var warning = spawnTelegraphs.get(director.generation(), slot.id());
        if (warning != null) {
            if (!warning.ready(director.snapshot().tick())) return Optional.empty();
            boolean valid = DevilsSpatial.recheck(level(), slot, DevilsWorldBuild.origin(slot.zone()), probe,
                    warning.point().pos(), participants(), occupied);
            spawnTelegraphs.remove(slot.id());
            presentation.cancelSpawnTelegraph(director.generation(), slot.id());
            if (valid) {
                reservations.add(warning.body());
                return Optional.of(warning.point().pos());
            }
        }
        var point = DevilsSpatial.spawn(level(), slot, DevilsWorldBuild.origin(slot.zone()), probe, participants(), occupied,
                spawnSearches.computeIfAbsent(slot.id(), ignored -> new DevilsSpatial.Search()), detail -> problem("Spawn " + slot.id() + ": " + detail));
        if (point.isPresent()) {
            var selected = point.orElseThrow();
            int lead = spawnLead.getOrDefault(slot.id(), slot.ordinary() ? DevilsPlan.TELEGRAPH_TICKS : DevilsPlan.FLYING_TELEGRAPH_TICKS);
            // A failed presentation call must not arm a countdown that could activate silently.
            presentation.spawnTelegraph(this, director.generation(), slot.id(), selected.pos(), DevilsSpatial.flying(slot.kind()));
            spawnTelegraphs.begin(director.generation(), slot.id(), selected, DevilsSpatial.bodyAt(probe, selected.pos()), director.snapshot().tick(), lead);
        }
        return Optional.empty();
    }
    private void pruneSpawnTelegraphs(DevilsDirector.Snapshot snapshot) {
        var pending = snapshot.slots().stream().filter(s -> s.state()==DevilsDirector.SlotState.RESERVED || s.state()==DevilsDirector.SlotState.LOST)
                .map(s -> s.slot().id()).collect(java.util.stream.Collectors.toSet());
        for (var slot : spawnTelegraphs.retain(snapshot.generation(), pending)) presentation.cancelSpawnTelegraph(snapshot.generation(), slot);
        spawnLead.keySet().retainAll(pending);
    }

    @Override public boolean contains(Zone zone, Vec3 feet) { return DevilsMaps.contains(zone, DevilsWorldBuild.origin(zone), feet); }
    @Override public void sound(DevilsMob mob,String event) { sound(mob,event,mob.position()); }
    @Override public void sound(DevilsMob mob,String event,Vec3 at) {
        if(running() && mob.level()==level()) DevilsCombatSounds.play(level(),players(),mob.kind(),event,at);
    }
    @Override public Optional<Vec3> sepiksWarp(DevilsMob sepiks) {
        var occupied = new ArrayList<>(reservations);
        occupied.addAll(spawnTelegraphs.reservations(""));
        var point = DevilsSpatial.warp(level(), DevilsWorldBuild.origin(Zone.SP), sepiks, participants(), occupied);
        point.ifPresent(p -> reservations.add(DevilsSpatial.bodyAt(sepiks, p.pos()))); return point.map(DevilsSpatial.Point::pos);
    }
    @Override public boolean commitSepiksWarp(DevilsMob sepiks, Vec3 destination) {
        var occupied = new ArrayList<>(reservations);
        occupied.addAll(spawnTelegraphs.reservations(""));
        if (!DevilsSpatial.recheckWarp(level(), DevilsWorldBuild.origin(Zone.SP), sepiks, destination, participants(), occupied)) return false;
        reservations.add(DevilsSpatial.bodyAt(sepiks, destination));
        return true;
    }
    @Override public DevilsDirector.CuePlayback cue(DevilsDirector.Cue cue) {
        int duration = voice.start(cue.serial(), cue.lineId());
        speaking = cue;
        return duration <= 0 ? DevilsDirector.CuePlayback.unavailable() : DevilsDirector.CuePlayback.playing(duration);
    }
    @Override public void cueFallbackFinished(DevilsDirector.Cue cue) {
        if (cue.equals(speaking)) { speaking = null; voice.close(); }
    }
    @Override public void cancelGeneration(long generation) {
        music.close();
        spawnSearches.clear(); spawnTelegraphs.clear(); spawnLead.clear(); deferredSpawn = null;
        players().forEach(kim.biryeong.destiny.sound.ActivityMusic::devilsEnded);
        players().forEach(DevilsCombatSounds::stop);
        speaking = null; voice.close(); voice = newVoice(); presentation.cancelGeneration(generation);
    }
    @Override public void phaseChanged(DevilsDirector.Snapshot snapshot) { pruneSpawnTelegraphs(snapshot); presentation.phase(this, snapshot); }
    @Override public void incoming(long generation, List<DevilsPlan.Slot> slots, int ticks) {
        if (generation != director.generation() || !running()) return;
        for (var slot : slots) spawnLead.put(slot.id(), ticks);
        try { presentation.incoming(this, generation, List.copyOf(slots), ticks); }
        catch (RuntimeException error) { problem("Incoming presentation failed: " + error); }
    }
    @Override public void spawned(DevilsDirector.Spawn spawn, Vec3 at) {
        if (running() && spawn.ref().generation() == director.generation()) presentation.spawned(this, spawn, at);
    }
    @Override public void completed(long generation) {
        if (!running() || completeAt >= 0 || generation != director.generation()) return;
        completeAt = server.getTickCount();
        // Downed members still earned completion loot; combat targeting excludes them.
        var recipients = players().stream().filter(p -> p.level() == level()).toList();
        var spot = rewardChestSpot();
        if (spot == null) kim.biryeong.destiny.loot.Loot.activityComplete("devils_lair", recipients, "악마의 소굴");
        else kim.biryeong.destiny.loot.Loot.activityComplete("devils_lair", recipients, "악마의 소굴", spot.getKey(), spot.getValue());
    }
    /** QA: run the completion hook (reward chests) without fighting to the end. */
    void qaComplete() {
        if (running() && completeAt < 0 && place(Zone.SP, players(), false)) director.complete();
    }
    /** Sepiks's arena centre on the floor, front turned to the arena entrance (null: map not ready). */
    private java.util.Map.Entry<Vec3, Float> rewardChestSpot() {
        try {
            var origin = DevilsWorldBuild.origin(Zone.SP);
            var centre = DevilsMaps.anchor(Zone.SP, "SP.C", origin).pos();
            var entry = DevilsMaps.anchor(Zone.SP, "SP.IN", origin).pos();
            var floor = kim.biryeong.destiny.loot.Loot.floor(level(), centre, 24);
            if (floor == null) return null;
            var d = entry.subtract(centre);
            return java.util.Map.entry(floor, (float) Math.toDegrees(Math.atan2(-d.x, d.z)));
        } catch (RuntimeException error) { problem("Reward chest spot failed: " + error); return null; }
    }
    @Override public void problem(String message) { if (problems.add(message)) DestinyGuardians.LOGGER.warn("[DevilsLair {}] {}", id(), message); }
    void disconnected(ServerPlayer p, long now) {
        DevilsCombatSounds.stop(p); music.remove(p);
        supplySneaking.remove(p.getUUID());
        supplies.leave(p);
        joinPlaced.remove(p.getUUID()); joining.remove(p.getUUID());
        var option = downOptions.get(p.getUUID());
        if (option != null) GuardianDown.bodyOwned(p, option).ifPresent(body -> downBodies.put(p.getUUID(), body));
        roster.disconnected(p.getUUID(), now); recovery.presence(p.getUUID(), false, false);
        voice.disconnected(p); presentation.disconnected(p); DevilsObjectives.remove(p); clearGuide(p);
        GuardianDown.clearExternalHud(p);
    }
    boolean rejoin(ServerPlayer p, long now) {
        if (!member(p.getUUID()) || state == State.DRAINING || state == State.CLOSED) return false;
        if (roster.rejoin(p.getUUID(), now) != DevilsRoster.Join.ACCEPTED) { departed.add(p.getUUID()); return false; }
        supplies.reconnect(p);
        if (state == State.RUNNING) joining.add(p.getUUID());
        return true;
    }
    void leave(ServerPlayer p) {
        if (!member(p.getUUID())) return;
        DevilsCombatSounds.stop(p); music.remove(p);
        supplies.leave(p); pendingSupplyReset.remove(p.getUUID());
        cancelDown(p); DevilsObjectives.remove(p); clearGuide(p); voice.disconnected(p); presentation.disconnected(p);
        roster.disconnected(p.getUUID(), server.getTickCount()); recovery.presence(p.getUUID(), false, false);
        departed.add(p.getUUID()); DevilsLair.restore(p);
        if (state != State.RUNNING || ids.stream().noneMatch(this::member)) stop("화력팀 이탈");
    }
    void stop(String reason) {
        if (state == State.CLOSED || state == State.DRAINING) return;
        state = State.DRAINING; kim.biryeong.destiny.loot.Loot.activityClosed(players()); music.close(); director.close(); recovery.close(); actors.close(); build.close(); presentation.close(); voice.close(); supplies.close(); supplyStations.close();
        for (var p : players()) { cancelDown(p); DevilsObjectives.remove(p); clearGuide(p); p.sendSystemMessage(Component.literal(reason)); }
    }
    void drain() {
        if (state != State.DRAINING) return;
        // Include outsiders and departed participants: deleting a world with any player still inside is forbidden.
        for (var p : List.copyOf(level().players())) {
            cancelDown(p); DevilsObjectives.remove(p);
            if (!DevilsLair.restore(p) || p.level() == level()) {
                var target = server.overworld(); var at = Vec3.atBottomCenterOf(target.getRespawnData().pos());
                p.teleportTo(target, at.x, at.y, at.z, Set.of(), 0, 0, true);
            }
        }
        if (!level().players().isEmpty()) return;
        if (instances.close(instance)) state = State.CLOSED;
    }
}
