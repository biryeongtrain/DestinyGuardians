package kim.biryeong.destiny.activity.strike;

import kim.biryeong.destiny.campaign.RisingServices;
import java.util.EnumMap;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;

/** Builds every zone of a strike's isolated world before the fireteam is admitted. Cancellation is never readiness. */
public class StrikeWorldBuild<Z extends Enum<Z> & StrikeZone> implements AutoCloseable {
    public enum State { BUILDING, READY, CANCELLED, FAILED }
    private final Z[] zones;
    private final Function<Z, RisingServices.ZoneBuild> factory;
    private final Map<Z, RisingServices.ZoneBuild> builds;
    private int index;
    private State state = State.BUILDING;
    private RuntimeException failure;

    public StrikeWorldBuild(Class<Z> zoneType, Function<Z, RisingServices.ZoneBuild> factory) {
        this.zones = zoneType.getEnumConstants();
        if (zones.length == 0) throw new IllegalArgumentException("A strike needs at least one zone");
        this.factory = Objects.requireNonNull(factory);
        this.builds = new EnumMap<>(zoneType);
    }
    public State state() { return state; }
    public RuntimeException failure() { return failure; }
    public double progress() {
        if (state == State.READY) return 1;
        var current = index < zones.length ? builds.get(zones[index]) : null;
        return (index + (current == null ? 0 : Math.clamp(current.progress(), 0, 1))) / zones.length;
    }
    /** At most one zone's work each call; the coordinator supplies a shared per-server budget. */
    public void tick(long nanoseconds) {
        if (state != State.BUILDING || nanoseconds <= 0) return;
        try {
            var zone = zones[index];
            var build = builds.computeIfAbsent(zone, z -> Objects.requireNonNull(factory.apply(z)));
            if (build.step(nanoseconds)) {
                if (build.progress() < 1) throw new IllegalStateException("Cancelled/incomplete zone reported completion: " + zone);
                index++;
                if (index == zones.length) state = State.READY;
            }
        } catch (RuntimeException e) {
            failure = e;
            state = State.FAILED;
            cancelBuilders();
        }
    }
    @Override public void close() {
        if (state == State.BUILDING) state = State.CANCELLED;
        cancelBuilders();
    }
    private void cancelBuilders() {
        for (var build : builds.values()) {
            try { build.cancel(); }
            catch (RuntimeException e) { if (failure == null) failure = e; else if (failure != e) failure.addSuppressed(e); }
        }
    }
}
