package kim.biryeong.destiny.debug;

import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Read-only QA projection contract, not real-client HUD acceptance. */
class WeaponMoriStatusW160Test {
    private static String command() throws Exception {
        String source = Files.readString(Path.of("src/main/java/kim/biryeong/destiny/debug/DebugCommands.java"));
        int start = source.indexOf("Commands.literal(\"weapon-presentation-status\")");
        int end = source.indexOf("Commands.literal(\"critical-hud-status\")", start);
        assertTrue(start >= 0 && end > start);
        return source.substring(start, end);
    }

    @Test void readsAuthoritativeRoundsAndPrefixBoundedNodeCount() throws Exception {
        String source = command();
        assertTrue(source.contains("\" mori=\" + kim.biryeong.destiny.weapon.WeaponAce.rounds(p)"));
        assertTrue(source.contains("\" moriPips=\" + kim.biryeong.minigamelib.displayhud.DisplayHud.getHuds(p).keySet().stream()"));
        assertTrue(source.contains(".filter(id -> id.startsWith(kim.biryeong.destiny.hud.AceReticleCounter.PREFIX)).count()"));
    }

    @Test void statusNeverCreatesTicksOrGrantsTheStateItReads() throws Exception {
        String source = command();
        for (String forbidden : new String[]{"WeaponAce.update(", "WeaponAce.shot(", "WeaponAce.confirmedKill(",
                "WeaponAce.instantReload(", "AceReticleCounter.update(", "AceReticleCounter.remove(",
                "DisplayHud.spawn(", "WeaponRuntime.tickPlayer(", "WeaponHandling.tick("}) {
            assertFalse(source.contains(forbidden), forbidden);
        }
    }
}
