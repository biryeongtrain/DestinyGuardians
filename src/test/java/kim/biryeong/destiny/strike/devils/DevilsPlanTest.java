package kim.biryeong.destiny.strike.devils;

import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Locale;

import static kim.biryeong.destiny.strike.devils.DevilsPlan.*;
import static org.junit.jupiter.api.Assertions.*;

class DevilsPlanTest {
    @Test void immutablePlanMatchesAuthoredPackManifest() throws Exception {
        var lines = Files.readAllLines(Path.of("docs/design/strikes/devils-lair-3p/encounter-packs.csv"));
        assertEquals(31, packs().size());
        assertEquals(32, lines.size());
        var slots = new HashSet<String>();
        for (String line : lines.subList(1, lines.size())) {
            String[] row = line.split(",");
            Pack pack = pack(row[0]);
            assertEquals(row[1], pack.zone().name());
            assertEquals(row[2], pack.phase());
            assertEquals(row[3], pack.template());
            assertEquals(Integer.parseInt(row[4]), pack.members().size());
            var expected = new LinkedHashMap<Kind, Long>();
            for (String part : row[5].split(";")) {
                String[] pair = part.split(":");
                expected.put(Kind.valueOf(pair[0].toUpperCase(Locale.ROOT)), Long.parseLong(pair[1]));
            }
            for (Kind kind : Kind.values())
                assertEquals(expected.getOrDefault(kind, 0L), pack.members().stream().filter(k -> k == kind).count());
            for (Slot slot : pack.slots()) assertTrue(slots.add(slot.id()));
            assertThrows(UnsupportedOperationException.class, () -> pack.members().clear());
        }
        for (Slot slot : specials()) assertTrue(slots.add(slot.id()));
        assertEquals(258, slots.size());
    }

    @Test void fixedTotalsAndCapsIncludeSpecialActors() {
        int[] total = {24, 112, 59, 63};
        int[] cap = {24, 24, 32, 24};
        for (Zone zone : Zone.values()) {
            long ordinary = packs().stream().filter(p -> p.zone() == zone).mapToInt(p -> p.members().size()).sum();
            long special = specials().stream().filter(s -> s.zone() == zone).count();
            assertEquals(total[zone.ordinal()], ordinary + special);
            assertEquals(cap[zone.ordinal()], zone.actorCap());
        }
        assertEquals(3, PLAYERS);
        assertEquals(8, PACK_SIZE);
        assertEquals(2, SPAWNS_PER_TICK);
        assertEquals(1600, Kind.WALKER.health());
        assertEquals(2200, Kind.SEPIKS.health());
        assertEquals(120, Kind.SERVITOR.health());
        assertEquals(11, Kind.DREG.health());
    }
}
