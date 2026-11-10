package kim.biryeong.destiny.world;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class DestinyWorldDistancesTest {
    @Test void absentAndMalformedSettingsUseBoundedDefaults() {
        assertEquals(new DestinyWorldDistances.Limits(8, 6), DestinyWorldDistances.parse(null, null));
        assertEquals(new DestinyWorldDistances.Limits(8, 6), DestinyWorldDistances.parse("bad", "999999999999999999"));
    }

    @Test void explicitCapsAreConfigurableWithinNativeBounds() {
        assertEquals(new DestinyWorldDistances.Limits(12, 4), DestinyWorldDistances.parse("12", "4"));
        assertEquals(new DestinyWorldDistances.Limits(2, 32), DestinyWorldDistances.parse("-1", "1000"));
        assertEquals(new DestinyWorldDistances.Limits(32, 2), DestinyWorldDistances.parse("32", "0"));
    }
}
