package kim.biryeong.destiny.campaign;

import kim.biryeong.destiny.campaign.RisingServices.FallenKind;
import kim.biryeong.destiny.campaign.RisingServices.Marker;
import net.minecraft.world.phys.Vec3;

import java.util.*;

/**
 * Mission encounters built from {@code enemy.ENCOUNTER.N} markers. Pure server-thread logic: the world side
 * is behind {@link Spawner}, so wave order, sealing, stale callbacks and lost-enemy respawns are unit tested.
 *
 * <p>Wave rules (original design, not decoded from the extraction): each encounter name is one wave in
 * marker order unless a {@code wave=N} tag overrides it; a Walker is always its own final wave. The next wave
 * arrives when at most one enemy of the previous wave remains (none for waves of three or fewer), never on a
 * timer. Every wave is capped at {@link #MAX_ACTIVE} live AI. Progress is sealed only after the final wave has
 * fully spawned, so a failed spawn can never clear combat, and a cleared encounter is never time-based.
 */
public final class RisingEncounters {
    public static final int MAX_ACTIVE = 24;
    static final int WAVE_DELAY = 30;
    static final int RETRY_DELAY = 40;
    static final int RESPAWN_DELAY = 40;

    public record Slot(String markerId, String encounter, FallenKind kind, Vec3 pos, float yaw, int wave) { }
    public record Plan(List<List<Slot>> waves) {
        public Plan { waves = waves.stream().map(List::copyOf).toList(); }
        public int size() { return waves.stream().mapToInt(List::size).sum(); }
        public boolean empty() { return waves.isEmpty(); }
        public boolean hasWalker() { return waves.stream().flatMap(List::stream).anyMatch(s -> s.kind() == FallenKind.WALKER); }
    }

    /** World side. All callbacks arrive on the server thread. */
    public interface Spawner {
        /** Returns the spawned id, or null if the spawn failed (the run retries). */
        UUID spawn(Slot slot, boolean active, Events events);
        void setActive(UUID id, boolean active);
        void discard(UUID id);
        Optional<Vec3> position(UUID id);
    }
    public interface Events {
        void defeated(UUID id);
        void lost(UUID id);
    }
    /** Director cues (voice lines). */
    public interface Cues {
        default void wave(int index, int total, boolean walker) { }
        /** Presentation lead: wave {@code index} will spawn in {@code ticks} unless the previous wave refills. May repeat. */
        default void incoming(int index, int total, List<Slot> wave, int ticks) { }
        /** Presentation: wave {@code index}'s entities were just spawned (failed slots retry separately). */
        default void spawned(int index, int total, List<Slot> wave) { }
        default void defeated(int defeated, int total) { }
        default void spawnFailure(Slot slot, int attempts) { }
    }

    private RisingEncounters() { }

    // ---- planning ----------------------------------------------------------------------------------------

    public static boolean decoration(String encounter) {
        return encounter.contains("dark") || encounter.contains("silhouette");
    }

    /** Combat markers ({@code enemy.*}) of one zone, excluding silhouette decorations. */
    public static Plan plan(List<Marker> markers) { return plan(markers, false); }
    public static Plan decorations(List<Marker> markers) { return plan(markers, true); }

    private static Plan plan(List<Marker> markers, boolean decorations) {
        var order = new LinkedHashMap<String, List<Slot>>();
        var explicit = new TreeMap<Integer, List<Slot>>();
        var walkers = new ArrayList<Slot>();
        var sorted = new ArrayList<>(markers);
        sorted.sort(Comparator.comparing(Marker::id, RisingEncounters::naturalCompare));
        for (Marker m : sorted) {
            String[] parts = m.id().split("\\.");
            if (parts.length < 3 || !parts[0].equals("enemy")) continue;
            String encounter = parts[1];
            if (decoration(encounter) != decorations) continue;
            FallenKind kind = kind(m.tags().get("kind"));
            // map markers carry "order"; "wave" stays the explicit override
            int wave = parseInt(m.tags().get("wave"), parseInt(m.tags().get("order"), -1));
            var slot = new Slot(m.id(), encounter, kind, m.pos(), m.yaw(), wave);
            if (kind == FallenKind.WALKER && !decorations) walkers.add(slot);
            else if (wave >= 0) explicit.computeIfAbsent(wave, k -> new ArrayList<>()).add(slot);
            else order.computeIfAbsent(encounter, k -> new ArrayList<>()).add(slot);
        }
        var waves = new ArrayList<List<Slot>>();
        waves.addAll(explicit.values());
        waves.addAll(order.values());
        if (!walkers.isEmpty()) waves.add(walkers);
        var capped = new ArrayList<List<Slot>>();
        for (var wave : waves) {
            if (wave.isEmpty()) continue;
            capped.add(wave.size() > MAX_ACTIVE ? wave.subList(0, MAX_ACTIVE) : wave);
        }
        return new Plan(capped);
    }

    static FallenKind kind(String tag) {
        if (tag == null) return FallenKind.DREG;
        try { return FallenKind.valueOf(tag.trim().toUpperCase(Locale.ROOT)); }
        catch (IllegalArgumentException e) { return FallenKind.DREG; }
    }
    private static int parseInt(String value, int fallback) {
        if (value == null) return fallback;
        try { return Integer.parseInt(value.trim()); } catch (NumberFormatException e) { return fallback; }
    }
    static int naturalCompare(String a, String b) {
        String[] x = a.split("\\."), y = b.split("\\.");
        for (int i = 0; i < Math.min(x.length, y.length); i++) {
            int c;
            if (x[i].matches("\\d+") && y[i].matches("\\d+")) c = Long.compare(Long.parseLong(x[i]), Long.parseLong(y[i]));
            else c = x[i].compareTo(y[i]);
            if (c != 0) return c;
        }
        return Integer.compare(x.length, y.length);
    }

    // ---- runtime -----------------------------------------------------------------------------------------

    /** Frozen, unregistered scenery enemies (Breach silhouettes). */
    public static final class Decor {
        private final Spawner spawner;
        private final List<UUID> ids = new ArrayList<>();
        private boolean discarded;
        public Decor(Spawner spawner, Plan plan) {
            this.spawner = Objects.requireNonNull(spawner);
            Events ignore = new Events() {
                @Override public void defeated(UUID id) { ids.remove(id); }
                @Override public void lost(UUID id) { ids.remove(id); }
            };
            for (var wave : plan.waves()) for (var slot : wave) {
                UUID id = spawner.spawn(slot, false, ignore);
                if (id != null) ids.add(id);
            }
        }
        public int size() { return ids.size(); }
        public void discard() {
            if (discarded) return;
            discarded = true;
            for (UUID id : List.copyOf(ids)) spawner.discard(id);
            ids.clear();
        }
    }

    /** One attempt at an encounter, bound to the progress token that was current when it started. */
    public static final class Run {
        private final GuardianRisesProgress progress;
        private final GuardianRisesProgress.Token token;
        private final Plan plan;
        private final Spawner spawner;
        private final Cues cues;
        private final Map<UUID, Slot> alive = new LinkedHashMap<>();
        private final Map<UUID, Integer> waveOf = new HashMap<>();
        private final Deque<Pending> pending = new ArrayDeque<>();
        private int nextWave;
        private int thinSince = -1;
        private int clock;
        private int defeated;
        private boolean finished;

        private record Pending(Slot slot, int wave, UUID replaces, int at, int attempts) { }

        public Run(GuardianRisesProgress progress, Plan plan, Spawner spawner, Cues cues, int now) {
            this.progress = Objects.requireNonNull(progress);
            this.token = progress.token();
            this.plan = Objects.requireNonNull(plan);
            this.spawner = Objects.requireNonNull(spawner);
            this.cues = cues == null ? new Cues() { } : cues;
            this.clock = now;
        }

        public GuardianRisesProgress.Token token() { return token; }
        public Plan plan() { return plan; }
        public int total() { return plan.size(); }
        public int defeated() { return defeated; }
        public int alive() { return alive.size(); }
        public int wavesSpawned() { return nextWave; }
        public boolean current() { return !finished && progress.owns(token); }
        public List<UUID> aliveIds() { return List.copyOf(alive.keySet()); }
        public Optional<Vec3> nearest(Vec3 from) {
            Vec3 best = null;
            for (UUID id : alive.keySet()) {
                var pos = spawner.position(id);
                if (pos.isPresent() && (best == null || pos.get().distanceToSqr(from) < best.distanceToSqr(from))) best = pos.get();
            }
            return Optional.ofNullable(best);
        }

        public void tick(int now) {
            clock = now;
            if (!current()) return;
            // Retry failed spawns and respawn lost enemies first.
            for (int i = pending.size(); i > 0; i--) {
                var next = pending.poll();
                if (now < next.at()) { pending.add(next); continue; }
                spawnSlot(next, now);
            }
            if (nextWave < plan.waves().size()) {
                if (!previousWaveThin()) thinSince = -1;
                else {
                    if (thinSince < 0) {
                        thinSince = now;
                        if (nextWave > 0) presentation(() -> cues.incoming(nextWave, plan.waves().size(), plan.waves().get(nextWave), WAVE_DELAY));
                    }
                    if (nextWave == 0 || now >= thinSince + WAVE_DELAY) {
                        int index = nextWave++;
                        thinSince = -1;
                        var wave = plan.waves().get(index);
                        cues.wave(index, plan.waves().size(), wave.stream().anyMatch(s -> s.kind() == FallenKind.WALKER));
                        for (var slot : wave) spawnSlot(new Pending(slot, index, null, now, 0), now);
                        presentation(() -> cues.spawned(index, plan.waves().size(), wave));
                    }
                }
            }
            if (nextWave == plan.waves().size() && pending.stream().noneMatch(p -> p.replaces() == null)
                    && !progress.sealed()) progress.sealEncounter(token);
        }

        /** Presentation cues never affect spawning. */
        private static void presentation(Runnable cue) {
            try { cue.run(); } catch (RuntimeException ignored) { }
        }

        private boolean previousWaveThin() {
            if (nextWave == 0) return true;
            int wave = nextWave - 1;
            if (pending.stream().anyMatch(p -> p.wave() == wave)) return false;
            int size = plan.waves().get(wave).size();
            long left = waveOf.values().stream().filter(w -> w == wave).count();
            return left <= (size > 3 ? 1 : 0);
        }

        private void spawnSlot(Pending p, int now) {
            Events events = new Events() {
                @Override public void defeated(UUID id) { onDefeated(id); }
                @Override public void lost(UUID id) { onLost(id); }
            };
            UUID id;
            try { id = spawner.spawn(p.slot(), true, events); }
            catch (RuntimeException e) { id = null; }
            if (id == null) {
                int attempts = p.attempts() + 1;
                cues.spawnFailure(p.slot(), attempts);
                pending.add(new Pending(p.slot(), p.wave(), p.replaces(), now + RETRY_DELAY, attempts));
                return;
            }
            boolean ok = p.replaces() == null ? progress.registerEnemy(token, id) : progress.replaceEnemy(token, p.replaces(), id);
            if (!ok) { spawner.discard(id); return; }
            alive.put(id, p.slot());
            waveOf.put(id, p.wave());
        }

        private void onDefeated(UUID id) {
            if (!current() || alive.remove(id) == null) return;
            waveOf.remove(id);
            if (progress.enemyDefeated(token, id)) {
                defeated++;
                cues.defeated(defeated, total());
            }
        }

        private void onLost(UUID id) {
            if (!current()) return;
            Slot slot = alive.remove(id);
            if (slot == null) return;
            Integer wave = waveOf.remove(id);
            // Keep the lost id registered until its replacement exists, so the encounter cannot clear early.
            pending.add(new Pending(slot, wave == null ? 0 : wave, id, clock + RESPAWN_DELAY, 0));
        }

        public boolean cleared() { return current() && progress.encounterCleared(); }

        /** Remove every entity this run owns. Call after the progress generation changed (restart/skip). */
        public void discard() {
            if (finished) return;
            finished = true;
            pending.clear();
            for (UUID id : List.copyOf(alive.keySet())) spawner.discard(id);
            alive.clear();
            waveOf.clear();
        }
        /** Freeze or resume every live enemy (player disconnected / reconnected). */
        public void setActive(boolean active) {
            for (UUID id : alive.keySet()) spawner.setActive(id, active);
        }
    }
}
