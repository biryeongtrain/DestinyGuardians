package kim.biryeong.destiny.strike.exodus;

import kim.biryeong.destiny.activity.strike.StrikeMaps;
import org.junit.jupiter.api.Test;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;

class ExodusPlanTest {
    @Test void beatsFormOneWalkWithEveryRequiredAnchor() throws Exception {
        var plan = ExodusPlan.data();
        assertEquals(12, plan.beats().size());
        assertEquals(ExodusPlan.BeatKind.BOSS, plan.beats().getLast().kind());
        try (var in = getClass().getResourceAsStream("/data/destiny/exodus_crash/zones/markers.json")) {
            var parsed = ExodusMaps.maps().parse(new InputStreamReader(in, StandardCharsets.UTF_8));
            var markers = parsed.get(ExodusPlan.Zone.WORLD);
            for (var id : new String[]{"WORLD.IN", "WORLD.IN.0", "WORLD.IN.1", "WORLD.IN.2", "WORLD.OUT", "WORLD.CHEST"})
                assertTrue(markers.stream().anyMatch(m -> m.id().equals(id)), id);
            for (var beat : plan.beats()) {
                if (beat.kind() == ExodusPlan.BeatKind.ADVANCE) continue;
                long lane = markers.stream().filter(m -> ("WORLD." + beat.id()).equals(m.tags().get("lane"))).count();
                assertTrue(lane >= 12, beat.id() + " spawn cells " + lane);
                assertTrue(beat.enemies() > 0, beat.id());
            }
        }
        int previous = -1;
        for (var beat : plan.beats()) {
            int at = nearestRoute(plan, beat);
            assertTrue(at >= previous, beat.id() + " is out of walking order");
            previous = at;
        }
    }
    private static int nearestRoute(ExodusPlan.Data plan, ExodusPlan.Beat beat) {
        int best = 0; double d = Double.MAX_VALUE;
        for (int i = 0; i < plan.route().size(); i++) {
            double v = plan.route().get(i).distanceToSqr(beat.trigger());
            if (v < d) { d = v; best = i; }
        }
        return best;
    }
    @Test void chargeAndDefendBeatsHaveWhatTheyNeed() {
        for (var beat : ExodusPlan.data().beats()) switch (beat.kind()) {
            case CHARGE -> { assertTrue(beat.need() > 0 && beat.generator() != null, beat.id()); assertFalse(beat.gate().isEmpty(), beat.id()); }
            case DEFEND -> { assertTrue(beat.seconds() > 0 && beat.generator() != null, beat.id()); }
            default -> { }
        }
    }
    @Test void voiceTableIsPackagedAndEveryTriggerLineExists() {
        assertEquals(62, ExodusVoice.catalog().lines().size());
        for (var line : ExodusVoice.catalog().lines().values()) assertTrue(ExodusVoice.catalog().packaged(line), line.id());
        for (var beat : ExodusPlan.data().beats()) for (var id : ExodusVoice.opening(beat.id()))
            assertTrue(ExodusVoice.catalog().line(id).isPresent(), beat.id() + " " + id);
        for (var id : java.util.List.of(ExodusVoice.FIRST_CHARGE, ExodusVoice.CHARGE_DONE, ExodusVoice.FIELD_BACK))
            assertTrue(ExodusVoice.catalog().line(id).isPresent(), id);
        for (var id : ExodusVoice.COMPLETE) assertTrue(ExodusVoice.catalog().line(id).isPresent(), id);
    }
}
