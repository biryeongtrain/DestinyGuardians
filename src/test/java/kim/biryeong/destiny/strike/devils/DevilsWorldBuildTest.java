package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.campaign.RisingServices;
import org.junit.jupiter.api.Test;
import java.util.ArrayList;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class DevilsWorldBuildTest {
    static class Build implements RisingServices.ZoneBuild {
        int ticks, cancelled;
        public boolean step(long budget) { assertEquals(2000000L, budget); return ++ticks == 2; }
        public double progress() { return ticks / 2d; }
        public void cancel() { cancelled++; }
    }
    @Test void allZonesAreCompleteBeforeAdmissionAndEachTickHonorsOneBudget() {
        var created = new ArrayList<Build>();
        var world = new DevilsWorldBuild(z -> { var b = new Build(); created.add(b); return b; });
        world.tick(0);
        assertTrue(created.isEmpty());
        for (int i = 0; i < 7; i++) { world.tick(2000000); assertEquals(DevilsWorldBuild.State.BUILDING, world.state()); }
        assertEquals(.875, world.progress());
        world.tick(2000000);
        assertEquals(DevilsWorldBuild.State.READY, world.state());
        assertEquals(1, world.progress());
        assertEquals(4, created.size());
        assertEquals(List.of(2,2,2,2), created.stream().map(b -> b.ticks).toList());
        world.tick(2000000);
        assertEquals(8, created.stream().mapToInt(b -> b.ticks).sum());
    }
    @Test void cancellationAndFailedBuilderCannotPublishPartialMap() {
        var part = new Build();
        var world = new DevilsWorldBuild(z -> part);
        world.tick(2000000); world.close(); world.tick(2000000);
        assertEquals(DevilsWorldBuild.State.CANCELLED, world.state());
        assertEquals(1, part.ticks);
        var broken = new Build() { public boolean step(long budget) { return true; } };
        var failed = new DevilsWorldBuild(z -> broken);
        failed.tick(2000000);
        assertEquals(DevilsWorldBuild.State.FAILED, failed.state());
        assertNotNull(failed.failure());
        assertEquals(1, broken.cancelled);
    }
}
