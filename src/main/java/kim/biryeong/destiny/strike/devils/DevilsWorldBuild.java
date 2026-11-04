package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.campaign.RisingServices;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import java.util.EnumMap;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;

/** Builds all four isolated zones before admitting the fireteam. Cancellation is never readiness. */
public final class DevilsWorldBuild implements AutoCloseable {
    public enum State { BUILDING, READY, CANCELLED, FAILED }
    private final Function<DevilsPlan.Zone, RisingServices.ZoneBuild> factory;
    private final Map<DevilsPlan.Zone, RisingServices.ZoneBuild> builds = new EnumMap<>(DevilsPlan.Zone.class);
    private int index;
    private State state = State.BUILDING;
    private RuntimeException failure;

    public DevilsWorldBuild(ServerLevel level) { this(z -> DevilsMaps.begin(level, z, origin(z))); }
    DevilsWorldBuild(Function<DevilsPlan.Zone, RisingServices.ZoneBuild> factory) { this.factory = Objects.requireNonNull(factory); }
    public static BlockPos origin(DevilsPlan.Zone zone) { return new BlockPos(256 + zone.ordinal() * 512, 64, 256); }
    public State state() { return state; }
    public RuntimeException failure() { return failure; }
    public double progress() {
        if (state == State.READY) return 1;
        var zones = DevilsPlan.Zone.values();
        var current = index < zones.length ? builds.get(zones[index]) : null;
        return (index + (current == null ? 0 : Math.clamp(current.progress(), 0, 1))) / zones.length;
    }
    /** At most one zone's work each call; the coordinator supplies a shared per-server budget. */
    public void tick(long nanoseconds) {
        if (state != State.BUILDING || nanoseconds <= 0) return;
        try {
            var zones = DevilsPlan.Zone.values();
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
