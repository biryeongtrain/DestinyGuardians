package kim.biryeong.destiny.crucible;

import org.junit.jupiter.api.Test;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import static org.junit.jupiter.api.Assertions.*;

class CrucibleSoundsW260Test {
    @Test void captureAndAdvantageAreRelativeToTheListenerAndDoNotRepeat() {
        UUID a=UUID.randomUUID(),b=UUID.randomUUID();
        var match=new ControlMatch(new ControlMatch.Config(150,1000,0,10,1,1,1,600));
        match.join(a);match.join(b);match.tick(Map.of());
        var before=match.snapshot();match.tick(Map.of("A",Set.of(a)));var after=match.snapshot();
        assertEquals("capture_a",CrucibleSounds.zoneCue(a,before,after));
        assertNull(CrucibleSounds.zoneCue(b,before,after));
        before=after;match.tick(Map.of("B",Set.of(a)));after=match.snapshot();
        assertEquals("advantage",CrucibleSounds.zoneCue(a,before,after));
        assertEquals("enemy_advantage",CrucibleSounds.zoneCue(b,before,after));
        before=after;match.tick(Map.of("C",Set.of(a)));after=match.snapshot();
        assertEquals("power_play",CrucibleSounds.zoneCue(a,before,after));
        assertEquals("enemy_power_play",CrucibleSounds.zoneCue(b,before,after));
        assertNull(CrucibleSounds.zoneCue(a,after,after));
        before=after;match.tick(Map.of("A",Set.of(b)));after=match.snapshot();
        assertEquals("lost_a",CrucibleSounds.zoneCue(a,before,after));
        assertNull(CrucibleSounds.zoneCue(UUID.randomUUID(),before,after));
    }
}
