package kim.biryeong.destiny.strike.exodus;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.activity.presentation.ActivityFailurePresentation;
import kim.biryeong.destiny.activity.presentation.GuideRoute;
import kim.biryeong.destiny.activity.presentation.ObjectiveGuide;
import kim.biryeong.destiny.activity.strike.*;
import kim.biryeong.destiny.campaign.presentation.ObjectiveTracker;
import kim.biryeong.destiny.down.GuardianDown;
import kim.biryeong.destiny.strike.devils.*;
import kim.biryeong.minigamelib.music.MusicPacks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.*;

/**
 * One fireteam's walk through Exodus Crash. The whole map is one connected world: beats start where the fireteam
 * reaches them and nothing moves a player except a wipe back to the beat they were on. Server-thread owned.
 */
public final class ExodusSession implements StrikeRun, ActorDirector, DevilsActors.Environment, DevilsRecovery.Host {
    private enum State { PREPARING, ADMITTING, RUNNING, DRAINING, CLOSED }
    private enum BeatState { WAITING, ACTIVE }
    private record Charge(Vec3 at) { }

    static final double TRIGGER_RADIUS = 14, TRIGGER_HEIGHT = 12, DELIVER_RADIUS = 5, PICKUP_RADIUS = 1.8, HACK_RADIUS = 24;
    static final int MAX_ALIVE = 16, SPAWN_GAP = 8, FIELD_DOWN_TICKS = 25 * 20, BOSS_CHARGES = 3, GRACE_TICKS = 60;
    private static final DevilsPlan.Zone ZONE = DevilsPlan.Zone.RF;

    private final MinecraftServer server;
    private final StrikeInstances instances;
    private final StrikeInstances.Instance instance;
    private final List<UUID> ids;
    private final Set<UUID> departed = new HashSet<>();
    private final StrikeRoster roster;
    private final StrikeWorldBuild<ExodusPlan.Zone> build;
    private final DevilsActors actors;
    private final DevilsRecovery recovery;
    private final ActivityFailurePresentation failure;
    private final ExodusMusic music = new ExodusMusic();
    private final ExodusPlan.Data plan = ExodusPlan.data();
    private final Map<String, List<kim.biryeong.destiny.campaign.RisingServices.Marker>> lanes = new HashMap<>();
    private final Map<UUID, ObjectiveGuide> guides = new HashMap<>();
    private final Map<UUID, GuardianDown.Options> downOptions = new HashMap<>();
    private final Map<UUID, Vec3> downBodies = new HashMap<>(), supported = new HashMap<>();
    private final Map<UUID, DevilsRecovery.Revival> revivals = new HashMap<>();
    private final Set<UUID> joining = new HashSet<>(), joinPlaced = new HashSet<>();
    private final Deque<String> speech = new ArrayDeque<>();
    private StrikeVoicePlayback voice;

    // Encounter state. Everything here is reset by a checkpoint reset; `generation` fences stale actor callbacks.
    private final Map<DevilsDirector.ActorRef, DevilsPlan.Kind> live = new HashMap<>();
    private final Map<DevilsDirector.ActorRef, Vec3> lastAt = new HashMap<>();
    private final Deque<DevilsPlan.Kind> queue = new ArrayDeque<>();
    private final Set<String> carrierSlots = new HashSet<>();
    private final List<Charge> ground = new ArrayList<>();
    private final Map<UUID, Boolean> carrying = new HashMap<>();
    private final List<AABB> reserved = new ArrayList<>();
    private final Random random = new Random();
    private long generation = 1;
    private int beatIndex, spawnSeq, round, killed, delivered, hackTicks, fieldDownTicks, graceUntil, nextSpawnAt;
    private BeatState beatState = BeatState.WAITING;
    private boolean fieldUp = true, bossDead, firstChargeSpoken, started, chargeDoneSpoken;
    private State state = State.PREPARING;
    private long createdAt, admittedAt, completeAt = -1;
    private boolean resetPlacement;
    private StrikeBriefingGate briefingGate;
    private final Set<String> problems = new HashSet<>();

    ExodusSession(MinecraftServer server, StrikeInstances instances, StrikeInstances.Instance instance, List<ServerPlayer> players) {
        this.server = server; this.instances = instances; this.instance = instance;
        this.ids = players.stream().map(ServerPlayer::getUUID).toList();
        roster = new StrikeRoster(ids, ExodusPlan.MIN_PLAYERS, ExodusPlan.PLAYERS);
        build = new StrikeWorldBuild<>(ExodusPlan.Zone.class, z -> ExodusMaps.begin(instance.level(), z));
        recovery = new DevilsRecovery(instance.id(), ids, this);
        failure = new ActivityFailurePresentation(instance.id());
        actors = new DevilsActors(instance.level(), () -> this, this);
        voice = ExodusVoice.playback(this::players, token -> { });
        recovery.reset(generation, ZONE); createdAt = server.getTickCount();
        instances.own(instance, build::close); instances.own(instance, actors::close);
        instances.own(instance, recovery::close); instances.own(instance, () -> voice.close());
        instances.own(instance, music::close); instances.own(instance, failure::close);
        instances.own(instance, () -> { guides.values().forEach(ObjectiveGuide::clear); guides.clear(); });
    }

    // ---- StrikeRun ------------------------------------------------------------------------------------------------
    @Override public UUID id() { return instance.id(); }
    @Override public ServerLevel level() { return instance.level(); }
    @Override public boolean member(UUID id) { return ids.contains(id) && !departed.contains(id); }
    @Override public boolean closed() { return state == State.CLOSED; }
    @Override public boolean running() { return state == State.RUNNING; }
    @Override public boolean briefing() { return briefingGate != null; }
    @Override public float loadProgress() {
        return switch (state) { case PREPARING -> (float) (build.progress() * .88); case ADMITTING -> .92f; default -> .96f; };
    }
    private boolean ready(ServerPlayer p) { return p.connection.hasClientLoaded() && MusicPacks.ready(p); }
    private boolean readyLiving(ServerPlayer p) {
        return running() && !joining.contains(p.getUUID()) && !resetPlacement && !failure.state().wiping()
                && p.level() == level() && recovery.token(p.getUUID()).isEmpty() && ready(p);
    }
    @Override public boolean allows(ServerPlayer p) { return readyLiving(p); }
    public String status() {
        return state + " / " + beat().id() + " " + beatState + " / live " + live.size() + " / charges " + delivered + " / gen " + generation;
    }
    public List<ServerPlayer> players() {
        return ids.stream().filter(this::member).map(id -> server.getPlayerList().getPlayer(id))
                .filter(Objects::nonNull).filter(p -> !p.hasDisconnected()).toList();
    }
    @Override public List<ServerPlayer> participants() { return players().stream().filter(this::allows).toList(); }
    private ExodusPlan.Beat beat() { return plan.beats().get(Math.min(beatIndex, plan.beats().size() - 1)); }

    @Override public void tick(long now, long buildBudget) {
        if (state == State.CLOSED) return;
        if (state == State.DRAINING) { drain(); return; }
        for (var outsider : List.copyOf(level().players())) if (!member(outsider.getUUID())) {
            if (!ExodusCrash.restore(outsider) || outsider.level() == level()) {
                var target = server.overworld(); var at = Vec3.atBottomCenterOf(target.getRespawnData().pos());
                ExodusCrash.cleanup(outsider);
                outsider.teleportTo(target, at.x, at.y, at.z, Set.of(), 0, 0, true);
            }
        }
        reserved.clear();
        roster.expire(now);
        for (var m : roster.members()) if (m.expired()) departed.add(m.id());
        if (roster.abandoned(now) || ids.stream().noneMatch(this::member)) { stop("화력팀 접속 종료"); return; }
        if (state == State.PREPARING) {
            if (now - createdAt > 12000) { stop("맵 준비 시간 초과"); return; }
            build.tick(buildBudget);
            if (build.state() == StrikeWorldBuild.State.FAILED || build.state() == StrikeWorldBuild.State.CANCELLED) { stop("맵 준비 실패"); return; }
            if (build.state() != StrikeWorldBuild.State.READY) return;
            if (players().size() != StrikeAdmission.count(roster.members(), this::member) || players().stream().anyMatch(p -> !ready(p))) return;
            if (!place(players(), checkpoint(), true)) return;
            instances.ready(instance); state = State.ADMITTING; admittedAt = now; return;
        }
        if (state == State.ADMITTING) {
            if (now - admittedAt > 1200) { stop("입장 확인 시간 초과"); return; }
            for (var p : players()) roster.ready(p.getUUID(), p.level() == level() && ready(p));
            if (!StrikeAdmission.ready(roster.members(), this::member)) return;
            state = State.RUNNING; instances.running(instance); syncPresence();
            briefingGate = new StrikeBriefingGate(now);
        }
        if (briefingGate != null && state == State.RUNNING
                && briefingGate.ready(now, players().stream().anyMatch(kim.biryeong.destiny.fireteam.Fireteams::dark))) {
            briefingGate = null; started = true; graceUntil = (int) now + 40;
            say(ExodusVoice.opening("B00"));
        }
        for (var p : players()) {
            if (joining.contains(p.getUUID())) {
                if (!ready(p)) continue;
                if (!joinPlaced.contains(p.getUUID())) {
                    if (!place(List.of(p), checkpoint(), false)) continue;
                    joinPlaced.add(p.getUUID()); roster.ready(p.getUUID(), false); continue;
                }
                joining.remove(p.getUUID()); joinPlaced.remove(p.getUUID()); roster.ready(p.getUUID(), true);
                var option = downOptions.get(p.getUUID());
                if (recovery.token(p.getUUID()).isPresent() && option != null) restoreDown(p, option);
            } else if (p.level() != level()) leave(p);
            else if (recovery.token(p.getUUID()).isPresent() && !GuardianDown.active(p)) {
                var option = downOptions.get(p.getUUID()); if (option != null) restoreDown(p, option);
            }
        }
        if (!resetPlacement && !failure.state().wiping()) checkFalls();
        if (state != State.RUNNING) return;
        syncPresence();
        failure.scope(generation, "WORLD", restricted());
        recovery.restricted(restricted());
        if (failure.state().wiping()) { tickWipe(now); return; }
        boolean offline = roster.connected() == 0 || resetPlacement;
        var pause = StrikePausePolicy.forPresence(offline, players().stream().anyMatch(this::readyLiving), !participants().isEmpty());
        actors.tick(pause.actors());
        if (resetPlacement) {
            if (place(players(), checkpoint(), false)) { resetPlacement = false; resetRecovery(); graceUntil = (int) now + GRACE_TICKS; }
            return;
        }
        if (!offline) {
            inputs(); recovery.tick(); syncReviveAudio();
            if (failure.state().wiping()) { tickWipe(now); return; }
            if (state != State.RUNNING) return;
            if (!pause.progress()) {
                voice.tick();
                if (!voice.playing() && !speech.isEmpty()) voice.start(++speechSerial, speech.poll());
                if (started) encounter(now);
            }
        }
        music.tick(ExodusMusic.section(beat().kind(), beatState == BeatState.ACTIVE, completeAt >= 0),
                players().stream().filter(p -> p.level() == level() && !joining.contains(p.getUUID())).toList(), System.nanoTime());
        guides(now);
        failure.render(players().stream().filter(p -> p.level() == level() && !joining.contains(p.getUUID()) && ready(p)).toList(),
                p -> false, now, recovery.snapshot().wipeRemaining());
        if (now % 4 == 0) for (var p : players()) if (p.level() == level()) hud(p);
        if (completeAt >= 0 && now - completeAt >= 600 && !voice.playing() && speech.isEmpty()) stop("공격전 완료");
    }
    private long speechSerial;
    private void say(List<String> lines) { speech.addAll(lines); }
    private boolean restricted() { return beatState == BeatState.ACTIVE && completeAt < 0; }

    // ---- Encounter ------------------------------------------------------------------------------------------------
    private Vec3 triggerAt(ExodusPlan.Beat b) { return ExodusMaps.world(b.trigger()); }
    private Vec3 generatorAt(ExodusPlan.Beat b) {
        if (b.generator() != null) return ExodusMaps.world(b.generator());
        return ExodusMaps.anchor("WORLD.CHEST").pos();
    }
    private boolean chargeSession() {
        var b = beat();
        return beatState == BeatState.ACTIVE && (b.kind() == ExodusPlan.BeatKind.CHARGE || b.kind() == ExodusPlan.BeatKind.BOSS && fieldUp);
    }
    private int chargeNeed() { return beat().kind() == ExodusPlan.BeatKind.BOSS ? BOSS_CHARGES : beat().need(); }
    private static boolean vex(DevilsPlan.Kind k) {
        return switch (k) { case GOBLIN, HOBGOBLIN, HARPY, MINOTAUR, CYCLOPS -> true; default -> false; };
    }

    private void encounter(long now) {
        if (completeAt >= 0) return;
        var b = beat();
        if (beatState == BeatState.WAITING) {
            if (now < graceUntil) return;
            Vec3 at = triggerAt(b);
            for (var p : participants()) {
                Vec3 d = p.position().subtract(at);
                if (Math.abs(d.y) <= TRIGGER_HEIGHT && d.x * d.x + d.z * d.z <= TRIGGER_RADIUS * TRIGGER_RADIUS) { startBeat(); return; }
            }
            return;
        }
        for (var mob : actors.actors()) if (mob.reference() != null) lastAt.put(mob.reference(), mob.position());
        pump(now);
        switch (b.kind()) {
            case ADVANCE -> finishBeat();
            case COMBAT -> { if (queue.isEmpty() && live.isEmpty()) finishBeat(); }
            case CHARGE -> {
                chargeTick();
                if (delivered >= b.need()) { say(List.of(ExodusVoice.CHARGE_DONE)); finishBeat(); }
            }
            case DEFEND -> {
                refill(now);
                boolean near = participants().stream().anyMatch(p -> p.position().distanceToSqr(generatorAt(b)) <= HACK_RADIUS * HACK_RADIUS);
                if (near) hackTicks++;
                generatorFx(b, (double) hackTicks / (b.seconds() * 20));
                if (hackTicks >= b.seconds() * 20) finishBeat();
            }
            case BOSS -> {
                if (bossDead) { finishBeat(); return; }
                if (fieldUp) {
                    chargeTick();
                    if (delivered >= BOSS_CHARGES) {
                        fieldUp = false; delivered = 0; fieldDownTicks = FIELD_DOWN_TICKS; carrierSlots.clear();
                        level().playSound(null, BlockPos.containing(generatorAt(b)), SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 3f, 1f);
                        for (var p : players()) p.connection.send(new net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket(
                                Component.literal("스텔스 장 과부하! 지금 파이키스를 공격하세요")));
                    }
                } else if (--fieldDownTicks <= 0) {
                    fieldUp = true; say(List.of(ExodusVoice.FIELD_BACK));
                    level().playSound(null, BlockPos.containing(generatorAt(b)), SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 3f, .8f);
                }
                if (!fieldUp && queue.isEmpty() && live.size() < 3) refill(now);
            }
        }
    }

    private void startBeat() {
        var b = beat();
        beatState = BeatState.ACTIVE; spawnSeq = 0; round = 0; killed = 0; delivered = 0; hackTicks = 0; nextSpawnAt = 0;
        queue.clear(); carrierSlots.clear(); ground.clear(); carrying.clear(); fieldUp = true; bossDead = false;
        firstChargeSpoken = false; chargeDoneSpoken = false;
        enqueueWave(b);
        if (!b.id().equals("B00")) say(ExodusVoice.opening(b.id()));
        for (var p : players()) p.sendSystemMessage(Component.literal("§b" + b.shortTitle()), true);
    }
    private void enqueueWave(ExodusPlan.Beat b) {
        round++;
        if (b.kind() == ExodusPlan.BeatKind.BOSS && round > 1) return; // later boss rounds only add carriers
        // Boss first, then heavies, so the elite is not queued behind a swarm.
        var kinds = new ArrayList<DevilsPlan.Kind>();
        for (var w : b.waves()) for (int i = 0; i < w.count(); i++) kinds.add(w.kind());
        kinds.sort(Comparator.comparingDouble((DevilsPlan.Kind k) -> -k.health()));
        queue.addAll(kinds);
    }
    /** Keeps a defend phase or an Arc phase supplied: a fresh round once the field is thin. */
    private void refill(long now) {
        var b = beat();
        if (b.kind() == ExodusPlan.BeatKind.DEFEND) {
            if (queue.isEmpty() && live.size() <= 3) enqueueWave(b);
        } else if (b.kind() == ExodusPlan.BeatKind.BOSS) {
            if (queue.isEmpty() && live.values().stream().noneMatch(ExodusSession::vex)) {
                for (int i = 0; i < BOSS_CHARGES; i++) queue.add(DevilsPlan.Kind.HOBGOBLIN);
                for (int i = 0; i < 2; i++) queue.add(DevilsPlan.Kind.DREG);
            }
        }
    }
    private void chargeTick() {
        var b = beat();
        int need = chargeNeed();
        long carried = carrying.values().stream().filter(v -> v).count();
        long available = delivered + carried + ground.size() + carrierSlots.size();
        if (queue.isEmpty() && live.isEmpty() && available < need) {
            // Not enough charge carriers left alive: send in more Vex that carry one.
            for (long i = available; i < need; i++) queue.add(DevilsPlan.Kind.HOBGOBLIN);
        }
        Vec3 gen = generatorAt(b);
        generatorFx(b, (double) delivered / Math.max(1, need));
        for (var p : participants()) {
            if (!carrying.getOrDefault(p.getUUID(), false)) {
                for (var it = ground.iterator(); it.hasNext(); ) {
                    var c = it.next();
                    Vec3 d = p.position().subtract(c.at());
                    if (d.x * d.x + d.z * d.z <= PICKUP_RADIUS * PICKUP_RADIUS && Math.abs(d.y) <= 2.5) {
                        it.remove(); carrying.put(p.getUUID(), true);
                        level().playSound(null, p.blockPosition(), SoundEvents.EXPERIENCE_ORB_PICKUP, SoundSource.PLAYERS, 1f, 1.6f);
                        break;
                    }
                }
            } else if (p.position().distanceToSqr(gen) <= DELIVER_RADIUS * DELIVER_RADIUS) {
                carrying.put(p.getUUID(), false); delivered++;
                level().playSound(null, BlockPos.containing(gen), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 2f, 1f + delivered * .12f);
                level().sendParticles(ParticleTypes.ELECTRIC_SPARK, gen.x, gen.y + 1.5, gen.z, 60, .8, 1.2, .8, .4);
            }
        }
        if (level().getGameTime() % 4 == 0) {
            for (var c : ground) level().sendParticles(ParticleTypes.ELECTRIC_SPARK, c.at().x, c.at().y + .6, c.at().z, 4, .25, .35, .25, .03);
            for (var c : ground) level().sendParticles(ParticleTypes.END_ROD, c.at().x, c.at().y + 1.2, c.at().z, 1, .05, .5, .05, .01);
            for (var p : players()) if (carrying.getOrDefault(p.getUUID(), false))
                level().sendParticles(ParticleTypes.ELECTRIC_SPARK, p.getX(), p.getY() + 2.2, p.getZ(), 3, .25, .15, .25, .02);
            for (var e : lastAt.entrySet()) if (carrierSlots.contains(e.getKey().slotId()) && live.containsKey(e.getKey()))
                level().sendParticles(ParticleTypes.ELECTRIC_SPARK, e.getValue().x, e.getValue().y + 2.4, e.getValue().z, 3, .3, .2, .3, .04);
        }
    }
    private void generatorFx(ExodusPlan.Beat b, double progress) {
        if (level().getGameTime() % 10 != 0) return;
        Vec3 g = generatorAt(b);
        level().sendParticles(ParticleTypes.END_ROD, g.x, g.y + 1 + progress * 2, g.z, 3, .3, .6, .3, .01);
        for (int i = 0; i < 8; i++) {
            double a = i * Math.PI / 4 + level().getGameTime() * .05;
            level().sendParticles(ParticleTypes.ELECTRIC_SPARK, g.x + Math.cos(a) * 1.6, g.y + .4, g.z + Math.sin(a) * 1.6, 1, 0, .1, 0, .02);
        }
    }

    private void pump(long now) {
        if (queue.isEmpty() || now < nextSpawnAt || live.size() >= MAX_ALIVE) return;
        var kind = queue.peek();
        String slotId = beat().id() + "/" + round + "-" + (++spawnSeq);
        var slot = new DevilsPlan.Slot(slotId, ZONE, beat().id(), kind, "WORLD." + beat().id(), spawnSeq - 1);
        var ref = new DevilsDirector.ActorRef(generation, slotId, 0);
        var spawn = new DevilsDirector.Spawn(slot, ref, kind.health(), kind.shield());
        live.put(ref, kind);
        if (actors.spawn(spawn)) {
            queue.poll(); nextSpawnAt = (int) now + SPAWN_GAP;
            if (chargeSession() && vex(kind)) {
                long carried = carrying.values().stream().filter(v -> v).count();
                long available = delivered + carried + ground.size() + carrierSlots.size();
                if (available < chargeNeed()) carrierSlots.add(slotId);
            }
        } else { live.remove(ref); spawnSeq--; nextSpawnAt = (int) now + 10; }
    }

    private void finishBeat() {
        var b = beat();
        retireAll(DevilsDirector.Retirement.TRANSITION, true);
        openGate(b);
        beatState = BeatState.WAITING;
        if (beatIndex >= plan.beats().size() - 1) { complete(); return; }
        beatIndex++;
        graceUntil = (int) server.getTickCount() + 20;
        for (var p : players()) p.sendSystemMessage(Component.literal("§a목표 완료 · " + b.shortTitle()), true);
    }
    private void openGate(ExodusPlan.Beat b) {
        if (b.gate().isEmpty()) return;
        int removed = 0;
        for (var cell : b.gate()) {
            var pos = ExodusMaps.world(cell);
            if (net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(level().getBlockState(pos).getBlock()).getPath().equals("red_stained_glass")) { level().setBlock(pos, Blocks.AIR.defaultBlockState(), 2); removed++; }
        }
        if (removed > 0) {
            var mid = ExodusMaps.world(b.gate().get(b.gate().size() / 2));
            level().playSound(null, mid, SoundEvents.GLASS_BREAK, SoundSource.BLOCKS, 4f, .7f);
            level().playSound(null, mid, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.BLOCKS, 2f, 1.4f);
        }
    }
    private void retireAll(DevilsDirector.Retirement reason, boolean flash) {
        for (var e : List.copyOf(live.entrySet())) {
            var at = lastAt.get(e.getKey());
            if (flash && at != null) level().sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y + 1, at.z, 25, .5, .8, .5, .3);
            actors.retire(e.getKey(), reason);
        }
        live.clear(); lastAt.clear(); queue.clear(); carrierSlots.clear(); ground.clear(); carrying.clear();
    }
    private void complete() {
        if (completeAt >= 0) return;
        completeAt = server.getTickCount();
        say(ExodusVoice.COMPLETE);
        var recipients = players().stream().filter(p -> p.level() == level()).toList();
        var spot = rewardChestSpot();
        if (spot == null) kim.biryeong.destiny.loot.Loot.activityComplete("exodus_crash", recipients, "엑소더스의 추락");
        else kim.biryeong.destiny.loot.Loot.activityComplete("exodus_crash", recipients, "엑소더스의 추락", spot.getKey(), spot.getValue());
    }
    private Map.Entry<Vec3, Float> rewardChestSpot() {
        try {
            var chest = ExodusMaps.anchor("WORLD.CHEST").pos();
            var centre = ExodusMaps.anchor("WORLD.OUT").pos();
            var floor = kim.biryeong.destiny.loot.Loot.floor(level(), chest, 24);
            if (floor == null) return null;
            var d = centre.subtract(chest);
            return Map.entry(floor, (float) Math.toDegrees(Math.atan2(-d.x, d.z)));
        } catch (RuntimeException e) { problem("Reward chest spot failed: " + e); return null; }
    }
    /** Operator/QA: finish the current beat as if it had been played. */
    boolean qaSkip() {
        if (!running() || completeAt >= 0) return false;
        if (beatState == BeatState.WAITING) startBeat();
        if (beat().kind() == ExodusPlan.BeatKind.BOSS) { bossDead = true; }
        finishBeat();
        return true;
    }

    // ---- ActorDirector ---------------------------------------------------------------------------------------------
    @Override public void defeated(DevilsDirector.ActorRef ref) {
        if (ref.generation() != generation) return;
        var kind = live.remove(ref); var at = lastAt.remove(ref);
        if (kind == null) return;
        killed++;
        if (kind == DevilsPlan.Kind.PYKIS) bossDead = true;
        if (carrierSlots.remove(ref.slotId()) && at != null) {
            var floor = kim.biryeong.destiny.loot.Loot.floor(level(), at, 6);
            ground.add(new Charge(floor == null ? at : floor));
            level().playSound(null, BlockPos.containing(at), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 2f, 1.8f);
            if (!firstChargeSpoken) { firstChargeSpoken = true; say(List.of(ExodusVoice.FIRST_CHARGE)); }
        }
    }
    @Override public void lost(DevilsDirector.ActorRef ref, double health, double shield) {
        if (ref.generation() != generation) return;
        var kind = live.remove(ref); lastAt.remove(ref);
        if (kind == null) return;
        carrierSlots.remove(ref.slotId());
        queue.addFirst(kind);
    }
    @Override public double allowedDamage(DevilsDirector.ActorRef ref, double currentHealth, double requested) {
        if (ref.generation() != generation || completeAt >= 0) return 0;
        if (live.get(ref) == DevilsPlan.Kind.PYKIS && (fieldUp || beatState != BeatState.ACTIVE)) {
            var at = lastAt.get(ref);
            if (at != null && level().getGameTime() % 5 == 0) level().sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y + 1.6, at.z, 6, .7, 1, .7, .05);
            return 0;
        }
        return requested;
    }
    @Override public void healthChanged(DevilsDirector.ActorRef ref, double health, double shield) { }

    // ---- DevilsActors.Environment --------------------------------------------------------------------------------
    @Override public Optional<Vec3> spawnPoint(DevilsPlan.Slot slot, DevilsMob probe) {
        var kind = slot.kind();
        var targets = participants();
        if (targets.isEmpty()) return Optional.empty();
        List<Vec3> options = new ArrayList<>();
        if (kind == DevilsPlan.Kind.PYKIS) options.add(ExodusMaps.anchor("WORLD.OUT").pos());
        else for (var m : lane(beat().id())) options.add(m.pos());
        record Scored(Vec3 pos, double distance) { }
        var scored = new ArrayList<Scored>();
        for (var pos : options) {
            if (!level().isPositionEntityTicking(BlockPos.containing(pos))) continue;
            double nearest = targets.stream().mapToDouble(p -> p.position().distanceTo(pos)).min().orElse(0);
            if (kind != DevilsPlan.Kind.PYKIS && (nearest < 12 || nearest > 110)) continue;
            scored.add(new Scored(pos, nearest));
        }
        scored.sort(Comparator.comparingDouble(Scored::distance));
        int window = Math.min(scored.size(), 7);
        var order = new ArrayList<>(scored.subList(0, window));
        Collections.shuffle(order, random);
        order.addAll(scored.subList(window, scored.size()));
        for (var s : order) {
            Vec3 at = s.pos();
            if (DevilsSpatial.flying(kind)) at = at.add(0, 2.5, 0);
            var box = probe.getBoundingBox().move(at.subtract(probe.position()));
            if (!level().noCollision(probe, box) || reserved.stream().anyMatch(box::intersects)) continue;
            reserved.add(box);
            return Optional.of(at);
        }
        return Optional.empty();
    }
    private List<kim.biryeong.destiny.campaign.RisingServices.Marker> lane(String beat) {
        return lanes.computeIfAbsent(beat, id -> ExodusMaps.markers().stream()
                .filter(m -> ("WORLD." + id).equals(m.tags().get("lane"))).toList());
    }
    @Override public boolean contains(DevilsPlan.Zone zone, Vec3 feet) { return ExodusMaps.contains(feet); }
    @Override public Optional<Vec3> sepiksWarp(DevilsMob sepiks) { return Optional.empty(); }
    @Override public void sound(DevilsMob mob, String event) { sound(mob, event, mob.position()); }
    @Override public void sound(DevilsMob mob, String event, Vec3 at) {
        if (running() && mob.level() == level()) {
            try { DevilsCombatSounds.play(level(), players(), mob.kind(), event, at); }
            catch (RuntimeException e) { problem("Combat sound " + event + ": " + e); }
        }
    }
    @Override public void spawned(DevilsDirector.Spawn spawn, Vec3 at) {
        level().sendParticles(ParticleTypes.PORTAL, at.x, at.y + 1, at.z, 30, .4, .8, .4, .6);
    }
    @Override public void problem(String message) { if (problems.add(message)) DestinyGuardians.LOGGER.warn("[ExodusCrash {}] {}", id(), message); }

    // ---- Placement -----------------------------------------------------------------------------------------------
    /** Where a wipe or a rejoin puts the team: the entrance until the first beat is passed, else the active beat's trigger. */
    private Vec3 checkpoint() { return beatIndex == 0 && beatState == BeatState.WAITING ? null : triggerAt(beat()); }
    private boolean place(List<ServerPlayer> group, Vec3 centre, boolean initial) {
        var spots = new ArrayList<Vec3>();
        for (int i = 0; i < group.size(); i++) {
            int seat = ids.indexOf(group.get(i).getUUID());
            Vec3 spot = centre == null ? ExodusMaps.anchor("WORLD.IN." + Math.floorMod(seat, 3)).pos() : stand(centre, spots);
            if (spot == null) { problem("No safe checkpoint seat"); return false; }
            spots.add(spot);
        }
        for (int i = 0; i < group.size(); i++) {
            var p = group.get(i); var at = spots.get(i);
            if (initial) ExodusCrash.saveReturn(p);
            cancelDown(p); ExodusCrash.cleanup(p);
            if (!p.teleportTo(level(), at.x, at.y, at.z, Set.of(), 0, 0, true)) { stop("안전한 이동을 완료하지 못했습니다."); return false; }
            p.setGameMode(GameType.SURVIVAL); p.setHealth(p.getMaxHealth()); p.clearFire();
            supported.put(p.getUUID(), at);
            roster.ready(p.getUUID(), !initial);
        }
        return true;
    }
    /** A clear two-block-high standing cell with solid floor near the given point, away from the cells already chosen. */
    private Vec3 stand(Vec3 centre, List<Vec3> taken) {
        for (int r = 0; r <= 6; r++) for (int dx = -r; dx <= r; dx++) for (int dz = -r; dz <= r; dz++) {
            if (Math.max(Math.abs(dx), Math.abs(dz)) != r) continue;
            for (int dy : new int[]{0, 1, -1, 2, -2, 3, -3}) {
                var pos = BlockPos.containing(centre.x + dx, centre.y + dy, centre.z + dz);
                var floor = pos.below();
                if (!level().getBlockState(floor).isFaceSturdy(level(), floor, net.minecraft.core.Direction.UP)) continue;
                Vec3 at = new Vec3(pos.getX() + .5, pos.getY(), pos.getZ() + .5);
                if (!level().noCollision(new AABB(at.x - .35, at.y, at.z - .35, at.x + .35, at.y + 1.9, at.z + .35))) continue;
                if (taken.stream().anyMatch(t -> t.distanceToSqr(at) < 1.8)) continue;
                return at;
            }
        }
        return null;
    }
    private void checkFalls() {
        var size = ExodusMaps.dimensions(); var o = ExodusMaps.ORIGIN;
        for (var p : participants()) {
            Vec3 at = p.position();
            boolean outside = at.y < o.getY() - 4 || at.x < o.getX() || at.z < o.getZ() || at.x >= o.getX() + size.getX() || at.z >= o.getZ() + size.getZ();
            if (!outside) { if (p.onGround() && level().getGameTime() % 20 == 0) supported.put(p.getUUID(), at); continue; }
            // No walls, no kill: put them back on the last ground they stood on, as the cave floor is not a death.
            Vec3 back = supported.getOrDefault(p.getUUID(), ExodusMaps.anchor("WORLD.IN").pos());
            p.teleportTo(level(), back.x, back.y, back.z, Set.of(), p.getYRot(), 0, true);
            p.resetFallDistance(); p.setDeltaMovement(Vec3.ZERO);
            p.connection.send(new net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket(Component.literal("이탈한 위치에서 복귀했습니다")));
        }
    }

    // ---- Presence / HUD / guide ----------------------------------------------------------------------------------
    private void syncPresence() {
        for (var m : roster.members()) recovery.presence(m.id(), m.connected() && member(m.id()), m.ready() && !joining.contains(m.id()));
    }
    private void hud(ServerPlayer p) {
        var b = beat();
        String objective = b.title(); int count = 0, goal = 0; String key = null, action = null;
        if (completeAt >= 0) objective = "엑소더스 블랙을 정화했습니다";
        else if (beatState == BeatState.ACTIVE) {
            switch (b.kind()) {
                case COMBAT -> { goal = Math.max(1, b.enemies()); count = Math.min(goal, killed); }
                case CHARGE, BOSS -> {
                    if (chargeSession()) {
                        goal = chargeNeed(); count = delivered;
                        objective = carrying.getOrDefault(p.getUUID(), false) ? "전기 구체를 발전기로 가져가세요"
                                : b.kind() == ExodusPlan.BeatKind.BOSS ? "벡스에게서 전기 구체를 획득해 파이키스의 스텔스 장을 무너뜨리세요" : b.title();
                    } else if (b.kind() == ExodusPlan.BeatKind.BOSS) { objective = "스텔스 장이 무너졌습니다! 파이키스를 처치하세요"; }
                }
                case DEFEND -> {
                    goal = b.seconds() * 20; count = Math.min(goal, hackTicks);
                    boolean near = p.position().distanceToSqr(generatorAt(b)) <= HACK_RADIUS * HACK_RADIUS;
                    objective = near ? b.title() : "고스트가 해킹을 계속하려면 수호자가 근처에 있어야 합니다";
                }
                default -> { }
            }
        } else if (beatIndex > 0 || started) objective = b.kind() == ExodusPlan.BeatKind.BOSS ? b.title() : plan.beats().get(Math.max(0, beatIndex)).title();
        boolean hidden = !started || GuardianDown.active(p) || briefingGate != null || joining.contains(p.getUUID())
                || recovery.token(p.getUUID()).isPresent() || failure.state().wiping();
        ObjectiveTracker.render(p, new ObjectiveTracker.View("엑소더스의 추락", b.id() + beatState + completeAt, objective, count, goal,
                key, action, null, null, hidden));
    }
    private void guides(long now) {
        ObjectiveGuide.Target target = null;
        if (started && completeAt < 0) {
            var b = beat();
            if (beatState == BeatState.WAITING) {
                var points = plan.route().stream().map(ExodusMaps::world).toList();
                target = new ObjectiveGuide.Target(b.id() + "/go", triggerAt(b), points.size() >= 2 ? GuideRoute.of(points) : null, ObjectiveGuide.Mode.TRAVEL);
            } else if (chargeSession() || b.kind() == ExodusPlan.BeatKind.DEFEND) {
                target = new ObjectiveGuide.Target(b.id() + "/gen", generatorAt(b), null, ObjectiveGuide.Mode.COMBAT);
            }
        }
        for (var p : players()) {
            if (p.level() != level()) continue;
            var guide = guides.get(p.getUUID());
            if (guide != null && guide.owner() != p) { guide.clear(); guide = null; }
            if (guide == null) guides.put(p.getUUID(), guide = new ObjectiveGuide(p));
            boolean hidden = joining.contains(p.getUUID()) || GuardianDown.active(p) || recovery.token(p.getUUID()).isPresent() || briefingGate != null;
            guide.tick(target, hidden, (int) now);
        }
    }

    // ---- Down / revive / wipe (shared recovery policy) -----------------------------------------------------------
    private void inputs() {
        for (var p : players()) {
            var token = recovery.token(p.getUUID());
            if (token.isPresent()) { if (p.getLastClientInput().jump()) recovery.self(token.get()); continue; }
            if (!allows(p)) continue;
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
            if (player != null && option != null) GuardianDown.progressOwned(player, option, member.helper(), member.holdTicks(), players());
        }
    }
    @Override public GuardianDown.Options downed(ServerPlayer p) {
        if (!running() || p.level() != level() || !member(p.getUUID()) || joining.contains(p.getUUID())) return null;
        var down = recovery.down(p.getUUID(), generation);
        if (down.isEmpty()) return null;
        kim.biryeong.destiny.down.FireteamReviveAudio.announce(p, players());
        roster.down(p.getUUID(), true); downBodies.put(p.getUUID(), p.position());
        if (carrying.put(p.getUUID(), false) == Boolean.TRUE) ground.add(new Charge(p.position()));
        return downOptions.computeIfAbsent(p.getUUID(), id -> new GuardianDown.Options(false, 600, true,
                false, "엑소더스의 추락", this::reviveFinished, 60, true, true));
    }
    @Override public boolean revive(DevilsRecovery.Revival request) {
        var p = server.getPlayerList().getPlayer(request.down().player());
        if (p == null || p.level() != level() || request.down().generation() != generation) return false;
        var option = downOptions.get(p.getUUID()); if (option == null) return false;
        revivals.put(p.getUUID(), request);
        if (GuardianDown.reviveOwned(p, option)) return true;
        revivals.remove(p.getUUID(), request); return false;
    }
    private void reviveFinished(ServerPlayer p) {
        var request = revivals.remove(p.getUUID());
        if (request == null || request.down().generation() != generation || !running() || p.level() != level()) return;
        if (!ExodusMaps.contains(p.position()) || p.position().y < ExodusMaps.ORIGIN.getY()) {
            Vec3 back = supported.getOrDefault(p.getUUID(), ExodusMaps.anchor("WORLD.IN").pos());
            if (!p.teleportTo(level(), back.x, back.y, back.z, Set.of(), 0, 0, true)) { recovery.failed(request); p.setGameMode(GameType.SPECTATOR); return; }
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
        int remaining = recovery.snapshot().members().stream().filter(m -> m.player().equals(p.getUUID()))
                .mapToInt(DevilsRecovery.Member::readyIn).findFirst().orElse(option.readyTicks());
        if (!GuardianDown.resumeOwned(p, option, body, remaining)) { p.setGameMode(GameType.SPECTATOR); problem("Down scene could not resume for " + p.getUUID()); }
        if (failure.state().wiping()) GuardianDown.suppressHudOwned(p, option, true);
    }
    @Override public void wipe(long gen) {
        if (gen != generation || !running() || !failure.beginWipe(gen)) return;
        music.close(); voice.close(); speech.clear();
    }
    private void tickWipe(long now) {
        long gen = generation;
        if (!running() || gen != failure.state().generation()) return;
        actors.tick(true);
        var audience = players().stream().filter(p -> p.level() == level() && !joining.contains(p.getUUID()) && ready(p)).toList();
        for (var p : audience) {
            var owner = downOptions.get(p.getUUID());
            if (owner != null) GuardianDown.suppressHudOwned(p, owner, true);
            ObjectiveTracker.remove(p); var g = guides.remove(p.getUUID()); if (g != null) g.clear();
        }
        boolean recover = failure.tick(gen, !audience.isEmpty());
        failure.render(audience, p -> false, now, recovery.snapshot().wipeRemaining());
        if (recover && running() && gen == generation) checkpointReset();
    }
    /** The team is down: the beat starts over from its trigger with a fresh generation. */
    private void checkpointReset() {
        retireAll(DevilsDirector.Retirement.CHECKPOINT, false);
        generation++; beatState = BeatState.WAITING; delivered = 0; hackTicks = 0; fieldUp = true; bossDead = false;
        voice.close(); speech.clear();
        recovery.reset(generation, ZONE);
        resetPlacement = true;
        for (var p : players()) cancelDown(p);
    }
    private void resetRecovery() {
        recovery.reset(generation, ZONE);
        downOptions.clear(); downBodies.clear(); revivals.clear();
        for (var m : roster.members()) roster.down(m.id(), false);
        syncPresence();
    }

    // ---- Connection lifecycle ------------------------------------------------------------------------------------
    @Override public void disconnected(ServerPlayer p, long now) {
        failure.remove(p); music.remove(p);
        joinPlaced.remove(p.getUUID()); joining.remove(p.getUUID());
        var option = downOptions.get(p.getUUID());
        if (option != null) GuardianDown.bodyOwned(p, option).ifPresent(body -> downBodies.put(p.getUUID(), body));
        if (carrying.put(p.getUUID(), false) == Boolean.TRUE) ground.add(new Charge(p.position()));
        roster.disconnected(p.getUUID(), now); recovery.presence(p.getUUID(), false, false);
        voice.disconnected(p); ObjectiveTracker.remove(p); clearGuide(p);
        GuardianDown.clearExternalHud(p);
    }
    @Override public boolean rejoin(ServerPlayer p, long now) {
        if (!member(p.getUUID()) || state == State.DRAINING || state == State.CLOSED) return false;
        if (roster.rejoin(p.getUUID(), now) != StrikeRoster.Join.ACCEPTED) { departed.add(p.getUUID()); return false; }
        if (state == State.RUNNING) joining.add(p.getUUID());
        return true;
    }
    @Override public void leave(ServerPlayer p) {
        if (!member(p.getUUID())) return;
        failure.remove(p); music.remove(p);
        cancelDown(p); ObjectiveTracker.remove(p); clearGuide(p); voice.disconnected(p);
        roster.disconnected(p.getUUID(), server.getTickCount()); recovery.presence(p.getUUID(), false, false);
        joining.remove(p.getUUID()); joinPlaced.remove(p.getUUID());
        downOptions.remove(p.getUUID()); downBodies.remove(p.getUUID()); supported.remove(p.getUUID()); revivals.remove(p.getUUID());
        departed.add(p.getUUID()); ExodusCrash.restore(p);
        if (ids.stream().noneMatch(this::member)) stop("화력팀 이탈");
    }
    private void clearGuide(ServerPlayer p) { var g = guides.remove(p.getUUID()); if (g != null) g.clear(); }
    @Override public void stop(String reason) {
        if (state == State.CLOSED || state == State.DRAINING) return;
        state = State.DRAINING; failure.close(); kim.biryeong.destiny.loot.Loot.activityClosed(players());
        music.close(); recovery.close(); actors.close(); build.close(); voice.close();
        for (var p : players()) { cancelDown(p); ObjectiveTracker.remove(p); clearGuide(p); p.sendSystemMessage(Component.literal(reason)); }
    }
    @Override public void drain() {
        if (state != State.DRAINING) return;
        for (var p : List.copyOf(level().players())) {
            cancelDown(p); ObjectiveTracker.remove(p);
            if (!ExodusCrash.restore(p) || p.level() == level()) {
                var target = server.overworld(); var at = Vec3.atBottomCenterOf(target.getRespawnData().pos());
                p.teleportTo(target, at.x, at.y, at.z, Set.of(), 0, 0, true);
            }
        }
        if (!level().players().isEmpty()) return;
        if (instances.close(instance)) state = State.CLOSED;
    }
}
