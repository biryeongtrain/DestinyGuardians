package kim.biryeong.destiny.strike.devils;

import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;

/**
 * Server-thread, three-member recovery policy. The host owns GuardianDown cameras, safe placement
 * and actual health restoration. A dispatched revive is not a living player until its scoped normal
 * completion is acknowledged. No loot, ammunition, super energy or player-count scaling is involved.
 */
public final class DevilsRecovery implements AutoCloseable {
    public static final int NORMAL_SELF_TICKS = 100, SELF_TICKS = 600, ALLY_TICKS = 60;
    public static final int WIPE_TICKS = 160, PROTECTION_TICKS = 60;
    public static final int REVIVE_ACK_TICKS = 100, RETRY_TICKS = 20;

    public enum State { ALIVE, DOWN, REVIVING }
    public enum Method { AUTOMATIC, SELF, ALLY }
    public record DownToken(UUID activity, long generation, UUID player, long life) { }
    public record Revival(DownToken down, long request, Method method, UUID ally) { }
    public record Member(UUID player, boolean online, boolean ready, State state, DownToken down,
                         int downTicks, int readyIn, UUID helper, int holdTicks, int protectedTicks) { }
    public record Snapshot(UUID activity, long generation, DevilsPlan.Zone zone, long tick,
                           int online, int living, int wipeRemaining, boolean wipeIssued, boolean paused,
                           boolean closed, List<Member> members) {
        public Snapshot { members = List.copyOf(members); }
    }
    public interface Host {
        /** Start the scoped revive animation. True means accepted, not completed. */
        boolean revive(Revival revival);
        /** Cancel only this request's owned presentation; do not call revived from cancellation. */
        default void cancel(Revival revival) { }
        /** Once per generation. Reset the director/checkpoint, then reset this policy to that new generation. */
        void wipe(long generation);
        default void problem(String message) { }
    }
    private static final class Slot {
        final UUID id;
        boolean online, ready;
        State state = State.ALIVE;
        DownToken down;
        Revival pending;
        long life, downAt, pendingAt, retryAt, protectedUntil;
        UUID helper;
        int holdTicks;
        Slot(UUID id) { this.id = id; }
    }

    private final UUID activity;
    private final Host host;
    private final Map<UUID, Slot> slots = new LinkedHashMap<>();
    private final Map<UUID, DownToken> holdInputs = new LinkedHashMap<>();
    private long generation, clock, request;
    private DevilsPlan.Zone zone;
    private int wipeTicks;
    private boolean wipeIssued, closed;

    public DevilsRecovery(UUID activity, Collection<UUID> players, Host host) {
        this.activity = Objects.requireNonNull(activity); this.host = Objects.requireNonNull(host);
        Objects.requireNonNull(players);
        for (UUID player : players) {
            Objects.requireNonNull(player);
            if (slots.putIfAbsent(player, new Slot(player)) != null) throw new IllegalArgumentException("Duplicate member");
        }
        if (slots.size() < DevilsPlan.MIN_PLAYERS || slots.size() > DevilsPlan.PLAYERS) throw new IllegalArgumentException("One to three members required");
    }

    /** A new checkpoint/zone invalidates old down and revive tokens before any cancellation callback. */
    public boolean reset(long nextGeneration, DevilsPlan.Zone nextZone) {
        Objects.requireNonNull(nextZone);
        if (closed || nextGeneration <= generation) return false;
        List<Revival> pending = pending();
        generation = nextGeneration; zone = nextZone; wipeTicks = 0; wipeIssued = false;
        holdInputs.clear();
        for (Slot slot : slots.values()) {
            slot.state = State.ALIVE; slot.down = null; slot.pending = null;
            slot.helper = null; slot.holdTicks = 0; slot.protectedUntil = 0; slot.retryAt = 0;
        }
        pending.forEach(this::cancelPresentation);
        return true;
    }

    /** Feed the roster's current connection and world readiness. Reconnect eligibility remains roster-owned. */
    public void presence(UUID player, boolean online, boolean ready) {
        Slot slot = require(player);
        if (closed) return;
        slot.online = online; slot.ready = online && ready;
        if (!slot.online || !slot.ready) {
            cancelHold(player);
            resetHold(slot);
            if (slot.pending != null) cancelPending(slot);
            slot.protectedUntil = 0; // reconnect never renews a protection allowance
        }
        if (living() > 0) wipeTicks = 0;
    }

    /** Duplicate death reports return the original token without restarting its clock. */
    public Optional<DownToken> down(UUID player, long encounterGeneration) {
        Slot slot = require(player);
        if (!current(encounterGeneration) || wipeIssued || !slot.online || !slot.ready) return Optional.empty();
        if (slot.down != null) return Optional.of(slot.down);
        cancelHold(player);
        slot.down = new DownToken(activity, generation, player, ++slot.life);
        slot.state = State.DOWN; slot.downAt = clock; slot.protectedUntil = 0; slot.retryAt = 0;
        return Optional.of(slot.down);
    }

    public Optional<DownToken> token(UUID player) { return Optional.ofNullable(require(player).down); }

    /** Player-requested self revive. Normal zones require 5 seconds; restricted zones require 30 seconds. */
    public boolean self(DownToken token) {
        Slot slot = owned(token);
        return slot != null && slot.state == State.DOWN && readyIn(slot) == 0 && attempt(slot, Method.SELF, null);
    }

    /**
     * Submit once before each tick while the same valid ally interaction is held. The host validates
     * distance, line of sight and same world; leaving proximity for one tick resets progress.
     * Duplicate submissions cannot accelerate progress, and one ally cannot revive two targets at once.
     */
    public boolean hold(UUID ally, DownToken token) {
        Slot helper = slots.get(ally), target = owned(token);
        if (helper == null || target == null || !canHelp(helper, target)) return false;
        holdInputs.put(ally, token);
        return true;
    }
    public void cancelHold(UUID ally) {
        holdInputs.remove(ally);
        for (Slot slot : slots.values()) if (ally.equals(slot.helper)) resetHold(slot);
    }

    public void tick() {
        if (closed || zone == null || wipeIssued) { holdInputs.clear(); return; }
        if (online() == 0) { holdInputs.clear(); slots.values().forEach(this::resetHold); return; }
        clock++;
        long startedGeneration = generation;
        for (Slot slot : slots.values()) {
            if (slot.pending != null && clock - slot.pendingAt >= REVIVE_ACK_TICKS) {
                host.problem("Revival completion timed out: " + slot.id);
                cancelPending(slot);
            }
            if (!current(startedGeneration) || wipeIssued) return;
            if (slot.state != State.DOWN || !slot.online || !slot.ready) { resetHold(slot); continue; }
            UUID helper = null;
            // Stable roster order makes simultaneous rescue input deterministic; it never combines progress.
            for (Slot candidate : slots.values()) if (slot.down.equals(holdInputs.get(candidate.id)) && canHelp(candidate, slot)) {
                helper = candidate.id; break;
            }
            if (helper == null) resetHold(slot);
            else {
                slot.holdTicks = helper.equals(slot.helper) ? slot.holdTicks + 1 : 1;
                slot.helper = helper;
                if (slot.holdTicks >= ALLY_TICKS) attempt(slot, Method.ALLY, helper);
            }
            if (!current(startedGeneration) || wipeIssued) return;
            if (!current(startedGeneration) || wipeIssued) return;
        }
        holdInputs.clear();
        // A pending animation is not a living Guardian. A successful callback immediately cancels the wipe.
        if (zone != DevilsPlan.Zone.RY && living() == 0 && slots.values().stream().anyMatch(s -> s.online && s.state != State.ALIVE)) {
            if (++wipeTicks >= WIPE_TICKS) {
                wipeIssued = true;
                List<Revival> pending = pending();
                for (Slot slot : slots.values()) { slot.pending = null; resetHold(slot); }
                pending.forEach(this::cancelPresentation);
                host.wipe(generation);
            }
        } else wipeTicks = 0;
    }

    private boolean attempt(Slot slot, Method method, UUID ally) {
        if (closed || wipeIssued || slot.state != State.DOWN || !slot.online || !slot.ready || clock < slot.retryAt) return false;
        Revival revival = new Revival(slot.down, ++request, method, ally);
        slot.pending = revival; slot.pendingAt = clock; slot.state = State.REVIVING;
        resetHold(slot);
        boolean accepted;
        try { accepted = host.revive(revival); }
        catch (RuntimeException ex) { accepted = false; host.problem("Revival rejected: " + ex.getMessage()); }
        if (!accepted && revival.equals(slot.pending)) {
            slot.pending = null; slot.state = State.DOWN; slot.retryAt = clock + RETRY_TICKS;
        }
        return accepted;
    }

    /** Invoke only after successful owned revival/placement, never when closing the camera. */
    public boolean revived(Revival revival) {
        Slot slot = pendingOwner(revival);
        if (slot == null || !slot.online || !slot.ready) return false;
        slot.pending = null; slot.down = null; slot.state = State.ALIVE;
        slot.protectedUntil = clock + PROTECTION_TICKS; slot.retryAt = 0;
        resetHold(slot); wipeTicks = 0;
        return true;
    }
    /** Cancelled/failed presentation leaves the Guardian down and invalidates only that request. */
    public boolean failed(Revival revival) {
        Slot slot = pendingOwner(revival);
        if (slot == null) return false;
        slot.pending = null; slot.state = State.DOWN; slot.retryAt = clock + RETRY_TICKS;
        return true;
    }
    /** Accepted attacks cancel protection even when the shot misses. */
    public void attacked(UUID player, long encounterGeneration) {
        if (!current(encounterGeneration)) return;
        Slot slot = require(player);
        slot.protectedUntil = 0; cancelHold(player);
    }
    public boolean protectedNow(UUID player) {
        Slot slot = require(player);
        return !closed && !wipeIssued && slot.online && slot.ready && slot.state == State.ALIVE && clock < slot.protectedUntil;
    }

    private Slot pendingOwner(Revival revival) {
        if (revival == null) return null;
        Slot slot = owned(revival.down);
        return slot != null && revival.equals(slot.pending) ? slot : null;
    }
    private Slot owned(DownToken token) {
        if (token == null || !current(token.generation) || wipeIssued || !activity.equals(token.activity)) return null;
        Slot slot = slots.get(token.player);
        return slot != null && token.equals(slot.down) ? slot : null;
    }
    private boolean current(long expected) { return !closed && zone != null && generation == expected; }
    private boolean canHelp(Slot helper, Slot target) {
        return !wipeIssued && !helper.id.equals(target.id) && helper.online && helper.ready && helper.state == State.ALIVE
                && target.online && target.ready && target.state == State.DOWN;
    }
    private int readyIn(Slot slot) {
        if (slot.down == null) return 0;
        return (int) Math.max(0, (zone == DevilsPlan.Zone.RY ? NORMAL_SELF_TICKS : SELF_TICKS) - (clock - slot.downAt));
    }
    private void resetHold(Slot slot) { slot.helper = null; slot.holdTicks = 0; }
    private int online() { return (int) slots.values().stream().filter(s -> s.online).count(); }
    private int living() { return (int) slots.values().stream().filter(s -> s.online && s.ready && s.state == State.ALIVE).count(); }
    private Slot require(UUID player) {
        Slot slot = slots.get(player);
        if (slot == null) throw new IllegalArgumentException("Not a strike participant: " + player);
        return slot;
    }
    private List<Revival> pending() { return slots.values().stream().map(s -> s.pending).filter(Objects::nonNull).toList(); }
    private void cancelPending(Slot slot) {
        Revival old = slot.pending;
        slot.pending = null; slot.state = State.DOWN; slot.retryAt = clock + RETRY_TICKS;
        if (old != null) cancelPresentation(old);
    }
    private void cancelPresentation(Revival revival) {
        try { host.cancel(revival); }
        catch (RuntimeException ex) { host.problem("Revival cancellation failed: " + ex.getMessage()); }
    }

    public Snapshot snapshot() {
        var members = new ArrayList<Member>();
        for (Slot slot : slots.values()) members.add(new Member(slot.id, slot.online, slot.ready, slot.state, slot.down,
                slot.down == null ? 0 : (int) Math.min(Integer.MAX_VALUE, clock - slot.downAt), readyIn(slot), slot.helper,
                slot.holdTicks, protectedNow(slot.id) ? (int) (slot.protectedUntil - clock) : 0));
        return new Snapshot(activity, generation, zone, clock, online(), living(),
                wipeIssued ? 0 : wipeTicks == 0 ? -1 : WIPE_TICKS - wipeTicks, wipeIssued, online() == 0, closed, members);
    }
    @Override public void close() {
        if (closed) return;
        List<Revival> pending = pending();
        closed = true; holdInputs.clear();
        for (Slot slot : slots.values()) { slot.pending = null; slot.down = null; slot.protectedUntil = 0; resetHold(slot); }
        pending.forEach(this::cancelPresentation);
    }
}
