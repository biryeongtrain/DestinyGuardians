package kim.biryeong.destiny.strike.devils;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import kim.biryeong.destiny.activity.reinforcement.ReinforcementQueue;
import kim.biryeong.destiny.activity.reinforcement.SpawnAttemptBudget;
import java.util.Set;

import static kim.biryeong.destiny.strike.devils.DevilsPlan.*;

/**
 * One server-thread director per fireteam. World/pack readiness, party membership, down/revive,
 * spatial spawn validation and persistent reward delivery belong to the host. No difficulty input
 * exists: admission allows one to three ready players, and subsequent losses never rescale the plan.
 */
public final class DevilsDirector implements ActorDirector, AutoCloseable {
    public enum Phase {
        READY(Zone.RY), BRIEFING(Zone.RY), RY_APPROACH(Zone.RY), RY_CLEAR(Zone.RY),
        RF_ENTRY(Zone.RF), RF_DEVICE(Zone.RF), RF_HACK(Zone.RF), RF_DEFENSE1(Zone.RF),
        RF_INTERMISSION1(Zone.RF), RF_DEFENSE2(Zone.RF), RF_INTERMISSION2(Zone.RF),
        RF_DEFENSE3(Zone.RF), RF_CLEAR(Zone.RF), BL_BATTLE(Zone.BL), BL_CLEAR(Zone.BL),
        SP_GUARD(Zone.SP), SP_INTRO(Zone.SP), SP_DAMAGE1(Zone.SP), SP_SHIELD1(Zone.SP),
        SP_RECOVER1(Zone.SP), SP_DAMAGE2(Zone.SP), SP_SHIELD2(Zone.SP), SP_RECOVER2(Zone.SP),
        SP_DAMAGE3(Zone.SP), COMPLETE(Zone.SP), CLOSED(Zone.SP);
        private final Zone zone;
        Phase(Zone zone) { this.zone = zone; }
        public Zone zone() { return zone; }
        public boolean damagePhase() { return this == SP_DAMAGE1 || this == SP_DAMAGE2 || this == SP_DAMAGE3; }
        public boolean shieldPhase() { return this == SP_SHIELD1 || this == SP_SHIELD2; }
    }
    public enum SlotState { RESERVED, LIVE, LOST, DEFEATED, RETIRED }
    public enum Retirement { CHECKPOINT, TRANSITION, BOSS_DEFEATED, CLOSED }
    public record ActorRef(long generation, String slotId, int incarnation) { }
    public record Spawn(Slot slot, ActorRef ref, double health, double shield) { }
    public record Cue(long generation, long serial, String lineId) { }
    /** ticks includes valid queue wait; false means no valid audio, permitting the explicit subtitle fallback. */
    public record CuePlayback(boolean available, int ticks) {
        public CuePlayback {
            if (ticks < 0 || available && ticks == 0) throw new IllegalArgumentException("Invalid playback length");
        }
        public static CuePlayback unavailable() { return new CuePlayback(false, 60); }
        public static CuePlayback playing(int ticks) { return new CuePlayback(true, ticks); }
    }
    public record SlotView(Slot slot, ActorRef ref, SlotState state, double health, double shield, int failures) { }
    public record Snapshot(long generation, Phase phase, Zone zone, long tick, long phaseTicks,
                           int live, int reserved, int activePacks, int pendingPacks, int defeated,
                           int defenseDefeated, int shieldServitors, boolean deviceReady, boolean paused,
                           double sepiksHealth, List<SlotView> slots) {
        public Snapshot { slots = List.copyOf(slots); }
        public int occupied() { return live + reserved; }
    }

    public interface Host {
        /** Validate ground, body clearance, route, distance >=12 and encounter bounds before accepting.
         * A false result must leave no entity behind. Deliver actor events after this call returns. */
        boolean spawn(Spawn spawn);
        /** The host yielded its search budget or a valid pad is temporarily occupied. */
        default boolean spawnDeferred(ActorRef actor) { return false; }
        /** Budget slices resume next tick; transient occupancy may back off to let other slots proceed. */
        default int spawnRetryTicks(ActorRef actor) { return 1; }
        /** Live hosts warn at the selected pad; fixture hosts may retain the original reservation countdown. */
        default boolean managesSpawnTelegraphs() { return false; }
        /** Neutral removal only: no kills, ammo, super energy or loot. Idempotent for an actor reference. */
        void retire(ActorRef actor, Retirement reason);
        /** Required cues must never silently drop from the audio queue. Report true completion with the same token. */
        CuePlayback cue(Cue cue);
        /** Remove text-only playback before its continuation can dispatch another cue. */
        default void cueFallbackFinished(Cue cue) { }
        /** Cancel only this generation's speech/locks/telegraphs; cancellation is not completion. */
        default void cancelGeneration(long generation) { }
        default void incoming(long generation, List<Slot> slots, int ticks) { }
        default void phaseChanged(Snapshot snapshot) { }
        /** Restore this zone's immutable checkpoint baseline, not a new supply allowance. */
        default void checkpointReset(Zone zone, long generation, String reason) { }
        /** Called once after the actual current Sepiks death event, never on zero health observation alone. */
        default void completed(long generation) { }
        default void problem(String message) { }
    }

    private static final class Actor {
        final Slot slot;
        SlotState state = SlotState.RESERVED;
        int incarnation, failures;
        double health, shield;
        long spawnAt;
        Actor(Slot slot, long spawnAt) {
            this.slot = slot; this.spawnAt = spawnAt;
            health = slot.kind().health(); shield = slot.kind().shield();
        }
        boolean occupied() { return state == SlotState.LIVE || state == SlotState.RESERVED || state == SlotState.LOST; }
    }
    private record Speech(String lineId, Runnable continuation, long generation) { }
    private static final class Speaking {
        final Cue token;
        final Runnable continuation;
        CuePlayback playback;
        long expires;
        Speaking(Cue token, Runnable continuation) { this.token = token; this.continuation = continuation; }
    }

    private final Host host;
    private final Map<String, Actor> actors = new LinkedHashMap<>();
    private final ReinforcementQueue<Pack> packs = new ReinforcementQueue<>();
    private final SpawnAttemptBudget<String> spawnBudget = new SpawnAttemptBudget<>(SPAWNS_PER_TICK);
    private final Deque<Speech> speech = new ArrayDeque<>();
    private final Set<String> phaseRequired = new LinkedHashSet<>();
    private Speaking speaking;
    private Phase phase = Phase.READY;
    /** Sepiks falls, the reward chest appears, and only then does Zavala speak: a beat of silence reads as an ending. */
    public static final int COMPLETION_SPEECH_DELAY = 120;
    private long generation = 1, clock, phaseAt, cueSerial, completionSpeechAt = -1;
    private boolean paused, deviceReady, gateFinished, completionSent;
    private int defeated, defenseDefeated;

    public DevilsDirector(Host host) { this.host = Objects.requireNonNull(host); }
    public Phase phase() { return phase; }
    @Override public boolean damagePhase() { return phase.damagePhase(); }
    @Override public boolean shieldPhase() { return phase.shieldPhase(); }
    public long generation() { return generation; }
    public boolean begin(int readyPlayers) {
        if (phase != Phase.READY || readyPlayers < MIN_PLAYERS || readyPlayers > PLAYERS) return false;
        transition(Phase.BRIEFING);
        speak("80b59f27", () -> startPacks(Phase.RY_APPROACH, Zone.RY, "approach", 160));
        return true;
    }

    /** The host calls only after all connected living members assemble in the already-built next zone. */
    public boolean arrive(Zone next) {
        if (!(phase == Phase.RY_CLEAR && next == Zone.RF || phase == Phase.RF_CLEAR && next == Zone.BL
                || phase == Phase.BL_CLEAR && next == Zone.SP)) return false;
        invalidate(Retirement.TRANSITION);
        startZone(next);
        return true;
    }

    public boolean interact() {
        if (paused || phase != Phase.RF_DEVICE || !deviceReady) return false;
        deviceReady = false;
        transition(Phase.RF_HACK);
        speak("80b59f26", () -> startPacks(Phase.RF_DEFENSE1, Zone.RF, "defense1", REINFORCEMENT_GAP));
        return true;
    }

    /** Pause only for the whole-party offline policy; one member disconnecting must not call this. */
    public void pause(boolean value) { paused = value; }

    public void tick() {
        if (phase == Phase.CLOSED || phase == Phase.READY || paused) return;
        clock++;
        long before = generation;
        tickSpeech();
        if (before != generation || phase == Phase.CLOSED) return;
        if (completionSpeechAt >= 0 && phase == Phase.COMPLETE && clock >= completionSpeechAt) {
            completionSpeechAt = -1;
            speak("80b59f28", null);
        }
        if (phase == Phase.RF_INTERMISSION1 && gateFinished && phaseAge() >= INTERMISSION_TICKS)
            startPacks(Phase.RF_DEFENSE2, Zone.RF, "defense2", REINFORCEMENT_GAP);
        else if (phase == Phase.RF_INTERMISSION2 && gateFinished && phaseAge() >= INTERMISSION_TICKS)
            startPacks(Phase.RF_DEFENSE3, Zone.RF, "defense3", REINFORCEMENT_GAP);
        else if (phase == Phase.SP_INTRO && gateFinished && phaseAge() >= 80) enterDamage(1);
        else if (phase == Phase.SP_INTRO && phaseAge() >= 280) {
            resetCheckpoint("Sepiks awakening did not complete");
            return;
        }
        else if (phase == Phase.SP_RECOVER1 && phaseAge() >= 40) enterDamage(2);
        else if (phase == Phase.SP_RECOVER2 && phaseAge() >= 40) enterDamage(3);
        reserveNextPack();
        spawnBudget.run(actors.values(), a -> a.slot.id(),
                a -> (a.state == SlotState.RESERVED || a.state == SlotState.LOST) && clock >= a.spawnAt, actor -> {
            actor.incarnation++;
            ActorRef ref = reference(actor);
            boolean accepted;
            try { accepted = host.spawn(new Spawn(actor.slot, ref, actor.health, actor.shield)); }
            catch (RuntimeException ex) { accepted = false; host.problem("Spawn failed " + actor.slot.id() + ": " + ex.getMessage()); }
            if (before != generation || phase == Phase.CLOSED) return false;
            if (accepted) {
                actor.state = SlotState.LIVE;
                // A blocked doorway may postpone a pack. Measure the gap from its actual arrival,
                // not its original reservation, so delayed packs cannot arrive in a burst.
                if (actor.slot.ordinary()) packs.arrived(actor.slot.packId(), clock, TELEGRAPH_TICKS);
            }
            else if (host.spawnDeferred(ref)) {
                // Reservation and original telegraph remain valid; no entity or failure was produced.
                actor.spawnAt = clock + Math.clamp(host.spawnRetryTicks(ref), 1, 20);
            }
            else {
                actor.failures++;
                actor.spawnAt = clock + TELEGRAPH_TICKS;
                if (actor.failures >= 3) { resetCheckpoint("Three failed placements: " + actor.slot.id()); return false; }
            }
            return true;
        });
        if (before != generation || phase == Phase.CLOSED) return;
        advanceIfDefeated();
    }

    private void startZone(Zone zone) {
        defeated = defenseDefeated = 0;
        switch (zone) {
            case RY -> {
                transition(Phase.BRIEFING);
                speak("80b59f27", () -> startPacks(Phase.RY_APPROACH, Zone.RY, "approach", 160));
            }
            case RF -> {
                startPacks(Phase.RF_ENTRY, zone, "entry", 60);
                speak("80b59f22", null);
            }
            case BL -> {
                transition(Phase.BL_BATTLE);
                reserveSpecial(walker()); reserveSpecial(brig(1)); reserveSpecial(brig(2));
                enqueue(packs(zone, "entry"), 60, true);
                speak("80b59f23", null);
            }
            case SP -> {
                transition(Phase.SP_GUARD);
                reserveSpecial(sepiks());
                enqueue(packs(zone, "guard"), 60, true);
                speak("80b59f1f", null);
            }
        }
    }

    private void startPacks(Phase next, Zone zone, String group, int gap) {
        transition(next);
        enqueue(packs(zone, group), gap, true);
    }
    private void enqueue(List<Pack> list, int gap, boolean required) {
        for (Pack pack : list) if (packs.enqueue(pack.id(), pack, gap, clock)) {
            if (required) for (Slot slot : pack.slots()) phaseRequired.add(slot.id());
        }
    }
    private void enqueue(String id) { enqueue(List.of(DevilsPlan.pack(id)), REINFORCEMENT_GAP, false); }

    private void reserveNextPack() {
        var pack = packs.reserve(clock, candidate -> {
            if (actors.values().stream().anyMatch(a -> a.slot.ordinary() && a.occupied()
                    && !packs.hasArrived(a.slot.packId()))) return false;
            if (activePackCount() >= phase.zone().packCap() || occupied() + candidate.slots().size() > phase.zone().actorCap()) return false;
            // Keep shield capacity free throughout the lair.
            return phase.zone() != Zone.SP || ordinaryOccupied() + candidate.slots().size() <= 20;
        });
        if (pack == null) return;
        var slots = pack.slots();
        for (Slot slot : slots) actors.put(slot.id(), new Actor(slot, clock + (host.managesSpawnTelegraphs() ? 0 : TELEGRAPH_TICKS)));
        host.incoming(generation, slots, TELEGRAPH_TICKS);
    }
    private void reserveSpecial(Slot slot) {
        if (actors.containsKey(slot.id())) return;
        if (occupied() >= phase.zone().actorCap()) throw new IllegalStateException("Mandatory actor reservation exceeded cap");
        actors.put(slot.id(), new Actor(slot, clock + (host.managesSpawnTelegraphs() ? 0 : FLYING_TELEGRAPH_TICKS)));
        host.incoming(generation, List.of(slot), FLYING_TELEGRAPH_TICKS);
    }

    @Override public void defeated(ActorRef ref) {
        Actor actor = live(ref);
        if (actor == null) return;
        // Invulnerable intro/shield actors cannot manufacture progression via an administrative kill.
        if (actor.slot.kind() == Kind.SEPIKS && phase != Phase.SP_DAMAGE3) {
            resetCheckpoint("Sepiks died outside its final damage phase");
            return;
        }
        actor.state = SlotState.DEFEATED;
        actor.health = 0; actor.shield = 0;
        defeated++;
        if (actor.slot.packId() != null && actor.slot.packId().startsWith("RF-defense")) defenseDefeated++;
        if (actor.slot.kind() == Kind.WALKER) {
            cancelQueuedBlastReinforcements();
            if (speaking == null && speech.isEmpty()) speak("80b59f1e", null);
        }
        if (phase == Phase.BL_BATTLE && dead("BL-brig-1") && dead("BL-brig-2") && !dead("BL-walker"))
            enqueue("BL-reinforce-4");
        if (actor.slot.kind() == Kind.SEPIKS) complete();
        else advanceIfDefeated();
    }

    public void lost(ActorRef ref, double health) {
        Actor actor = live(ref);
        if (actor != null) lost(ref, health, actor.shield);
    }
    @Override public void lost(ActorRef ref, double health, double shield) {
        Actor actor = live(ref);
        if (actor == null) return;
        if (!validHealth(actor, health, shield)) { resetCheckpoint("Invalid lost actor health: " + ref.slotId()); return; }
        actor.health = health; actor.shield = shield;
        actor.state = SlotState.LOST;
        actor.failures++;
        if (actor.failures >= 3) { resetCheckpoint("Repeated lost slot: " + actor.slot.id()); return; }
        actor.spawnAt = clock + (host.managesSpawnTelegraphs() ? 0 : TELEGRAPH_TICKS);
        host.incoming(generation, List.of(actor.slot), TELEGRAPH_TICKS);
    }

    /** Apply to the runtime's already-balanced incoming damage; never multiplies weapon damage. */
    @Override public double allowedDamage(ActorRef ref, double currentHealth, double requested) {
        Actor actor = live(ref);
        if (actor == null || paused || !(requested > 0) || !Double.isFinite(requested)
                || !(currentHealth > 0) || !Double.isFinite(currentHealth)) return 0;
        if (actor.slot.kind() != Kind.SEPIKS) return requested;
        if (!phase.damagePhase()) return 0;
        double threshold = phase == Phase.SP_DAMAGE1 ? Kind.SEPIKS.health() * .67
                : phase == Phase.SP_DAMAGE2 ? Kind.SEPIKS.health() * .33 : 0;
        return Math.min(requested, Math.max(0, currentHealth - threshold));
    }

    /** Notify only after runtime damage is accepted; zero HP is not a substitute for a real death event. */
    public void healthChanged(ActorRef ref, double health) {
        Actor actor = live(ref);
        if (actor != null) healthChanged(ref, health, actor.shield);
    }
    @Override public void healthChanged(ActorRef ref, double health, double shield) {
        Actor actor = live(ref);
        if (actor == null || !Double.isFinite(health) || health < 0 || health > actor.slot.kind().health()
                || !Double.isFinite(shield) || shield < 0 || shield > actor.slot.kind().shield()) return;
        actor.health = health; actor.shield = shield;
        if (actor.slot.kind() == Kind.WALKER && phase == Phase.BL_BATTLE && health > 0) {
            if (health <= Kind.WALKER.health() * .75) enqueue("BL-reinforce-1");
            if (health <= Kind.WALKER.health() * .50) enqueue("BL-reinforce-2");
            if (health <= Kind.WALKER.health() * .25) enqueue("BL-reinforce-3");
        }
        if (actor.slot.kind() == Kind.SEPIKS) {
            if (phase == Phase.SP_DAMAGE1 && health <= Kind.SEPIKS.health() * .67) enterShield(1);
            else if (phase == Phase.SP_DAMAGE2 && health <= Kind.SEPIKS.health() * .33) enterShield(2);
        }
    }

    private void enterShield(int index) {
        transition(index == 1 ? Phase.SP_SHIELD1 : Phase.SP_SHIELD2);
        for (int i = 1; i <= 3; i++) reserveSpecial(servitor(index, i));
        enqueue("SP-shield-" + index);
    }
    private void enterDamage(int index) {
        transition(switch (index) { case 1 -> Phase.SP_DAMAGE1; case 2 -> Phase.SP_DAMAGE2; default -> Phase.SP_DAMAGE3; });
        enqueue("SP-damage-" + index);
    }

    private void advanceIfDefeated() {
        if (phase == Phase.BL_BATTLE && dead("BL-walker") && dead("BL-brig-1") && dead("BL-brig-2")) {
            retireOrdinary(Retirement.BOSS_DEFEATED);
            transition(Phase.BL_CLEAR);
            return;
        }
        if (phase.shieldPhase()) {
            int shield = phase == Phase.SP_SHIELD1 ? 1 : 2;
            if (dead(servitor(shield, 1).id()) && dead(servitor(shield, 2).id()) && dead(servitor(shield, 3).id()))
                transition(shield == 1 ? Phase.SP_RECOVER1 : Phase.SP_RECOVER2);
            return;
        }
        if (phaseRequired.isEmpty() || !phaseRequired.stream().allMatch(this::dead)) return;
        switch (phase) {
            case RY_APPROACH -> transition(Phase.RY_CLEAR);
            case RF_ENTRY -> {
                transition(Phase.RF_DEVICE);
                speak("80b59f1d", () -> deviceReady = true);
            }
            case RF_DEFENSE1 -> {
                transition(Phase.RF_INTERMISSION1);
                speak("80b59f25", () -> speak("80b59f20", () -> gateFinished = true));
            }
            case RF_DEFENSE2 -> {
                transition(Phase.RF_INTERMISSION2);
                speak("80b59f21", () -> gateFinished = true);
            }
            case RF_DEFENSE3 -> {
                // Remain in defense until the actual barrier-release line is done.
                phaseRequired.clear();
                speak("80b59f24", () -> transition(Phase.RF_CLEAR));
            }
            case SP_GUARD -> {
                transition(Phase.SP_INTRO);
                // Host phaseChanged starts the <=4s awakening. This is a gameplay animation gate, not a voice clip.
            }
            default -> { }
        }
    }

    /** The presentation host reports normal completion of the current awakening; cancelled scenes never call it. */
    public boolean introFinished(long encounterGeneration) {
        if (generation != encounterGeneration || phase != Phase.SP_INTRO) return false;
        gateFinished = true;
        return true;
    }

    private void cancelQueuedBlastReinforcements() {
        packs.cancelQueued(p -> p.id().startsWith("BL-reinforce"));
        // Already telegraphed but unspawned optional members are reservations, not kills.
        for (Actor actor : actors.values()) if (actor.slot.id().startsWith("BL-reinforce") && actor.state != SlotState.LIVE)
            if (actor.occupied()) actor.state = SlotState.RETIRED;
    }
    private void retireOrdinary(Retirement reason) {
        packs.cancelQueued();
        for (Actor actor : actors.values()) if (actor.slot.ordinary() && actor.occupied()) {
            boolean live = actor.state == SlotState.LIVE;
            actor.state = SlotState.RETIRED;
            if (live) host.retire(reference(actor), reason);
        }
    }
    /** Also used by the operator-only completion fixture; production enters through Sepiks defeat. */
    void complete() {
        if (completionSent) return;
        completionSent = true;
        retireOrdinary(Retirement.BOSS_DEFEATED);
        transition(Phase.COMPLETE);
        long completedGeneration = generation;
        host.completed(completedGeneration);
        if (generation == completedGeneration && phase == Phase.COMPLETE) completionSpeechAt = clock + COMPLETION_SPEECH_DELAY;
    }

    private void speak(String id, Runnable continuation) {
        speech.addLast(new Speech(id, continuation, generation));
        dispatchSpeech();
    }
    private void dispatchSpeech() {
        if (speaking != null || speech.isEmpty()) return;
        Speech next = speech.removeFirst();
        if (next.generation != generation) { dispatchSpeech(); return; }
        Speaking active = new Speaking(new Cue(generation, ++cueSerial, next.lineId), next.continuation);
        speaking = active;
        CuePlayback playback;
        try { playback = Objects.requireNonNull(host.cue(active.token)); }
        catch (RuntimeException ex) { host.problem("Unavailable cue " + next.lineId + ": " + ex.getMessage()); playback = CuePlayback.unavailable(); }
        if (speaking != active) return; // a synchronous, explicit completion may have dispatched the next cue
        active.playback = playback;
        active.expires = clock + (playback.available() ? (long) playback.ticks() + 200 : 60);
    }
    private void tickSpeech() {
        var active = speaking;
        if (active == null) { dispatchSpeech(); return; }
        if (active.playback == null || clock < active.expires) return;
        if (!active.playback.available()) {
            host.cueFallbackFinished(active.token);
            finishSpeech(active);
        }
        else {
            host.problem("Voice completion timed out: " + active.token.lineId());
            if (active.continuation != null) resetCheckpoint("Required cue did not complete: " + active.token.lineId());
            else { speaking = null; dispatchSpeech(); }
        }
    }
    public void cueFinished(Cue token) {
        if (speaking == null || token.generation != generation || !speaking.token.equals(token)) return;
        finishSpeech(speaking);
    }
    private void finishSpeech(Speaking active) {
        if (speaking != active) return;
        speaking = null;
        if (active.continuation != null) active.continuation.run();
        dispatchSpeech();
    }
    public void cueCancelled(Cue token) {
        if (speaking == null || token.generation != generation || !speaking.token.equals(token)) return;
        if (speaking.continuation != null) resetCheckpoint("Required cue cancelled: " + token.lineId());
        else { speaking = null; dispatchSpeech(); }
    }

    public void resetCheckpoint(String reason) {
        if (phase == Phase.READY || phase == Phase.COMPLETE || phase == Phase.CLOSED) return;
        Zone zone = phase.zone();
        invalidate(Retirement.CHECKPOINT);
        long restartingGeneration = generation;
        host.checkpointReset(zone, restartingGeneration, Objects.requireNonNull(reason));
        if (generation == restartingGeneration && phase != Phase.CLOSED) startZone(zone);
    }
    /** OP-only native QA fixture adapter. Uses normal invalidation/start, never fabricates encounter completion. */
    void qaCheckpoint(Zone zone) {
        if (phase == Phase.CLOSED) return;
        invalidate(Retirement.CHECKPOINT);
        startZone(Objects.requireNonNull(zone));
    }
    private void invalidate(Retirement reason) {
        long old = generation++;
        speaking = null; speech.clear(); packs.reset(); phaseRequired.clear(); completionSpeechAt = -1;
        spawnBudget.reset();
        deviceReady = gateFinished = false;
        List<ActorRef> retiring = actors.values().stream().filter(a -> a.state == SlotState.LIVE)
                .map(a -> new ActorRef(old, a.slot.id(), a.incarnation)).toList();
        actors.clear(); // invalidate before callbacks emitted by cancellation/removal
        host.cancelGeneration(old);
        for (ActorRef ref : retiring) host.retire(ref, reason);
    }
    @Override public void close() {
        if (phase == Phase.CLOSED) return;
        invalidate(Retirement.CLOSED);
        transition(Phase.CLOSED);
    }
    private void transition(Phase next) {
        phase = next; phaseAt = clock; phaseRequired.clear(); gateFinished = false;
        host.phaseChanged(snapshot());
    }
    private long phaseAge() { return clock - phaseAt; }
    private boolean dead(String id) { Actor actor = actors.get(id); return actor != null && actor.state == SlotState.DEFEATED; }
    private ActorRef reference(Actor actor) { return new ActorRef(generation, actor.slot.id(), actor.incarnation); }
    private Actor live(ActorRef ref) {
        if (ref == null || ref.generation != generation || phase == Phase.CLOSED) return null;
        Actor actor = actors.get(ref.slotId);
        return actor != null && actor.state == SlotState.LIVE && actor.incarnation == ref.incarnation ? actor : null;
    }
    private boolean validHealth(Actor actor, double health, double shield) {
        return Double.isFinite(health) && health > 0 && health <= actor.slot.kind().health()
                && Double.isFinite(shield) && shield >= 0 && shield <= actor.slot.kind().shield();
    }
    private int occupied() { return (int) actors.values().stream().filter(Actor::occupied).count(); }
    private int ordinaryOccupied() { return (int) actors.values().stream().filter(a -> a.slot.ordinary() && a.occupied()).count(); }
    private int activePackCount() {
        return (int) actors.values().stream().filter(a -> a.slot.ordinary() && a.occupied()).map(a -> a.slot.packId()).distinct().count();
    }
    public Snapshot snapshot() {
        var slots = new ArrayList<SlotView>();
        int live = 0, reserved = 0, servitors = 0;
        for (Actor actor : actors.values()) {
            slots.add(new SlotView(actor.slot, reference(actor), actor.state, actor.health, actor.shield, actor.failures));
            if (actor.state == SlotState.LIVE) live++;
            else if (actor.state == SlotState.RESERVED || actor.state == SlotState.LOST) reserved++;
            if (actor.slot.kind() == Kind.SERVITOR && actor.occupied()) servitors++;
        }
        Actor sepiks = actors.get("SP-sepiks");
        return new Snapshot(generation, phase, phase.zone(), clock, phaseAge(), live, reserved, activePackCount(), packs.size(),
                defeated, defenseDefeated, servitors, deviceReady, paused, sepiks == null ? Kind.SEPIKS.health() : sepiks.health, slots);
    }
}
