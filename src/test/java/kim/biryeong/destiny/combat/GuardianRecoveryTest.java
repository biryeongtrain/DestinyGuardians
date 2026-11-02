package kim.biryeong.destiny.combat;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class GuardianRecoveryTest {
    @Test void pveHealthAndShieldsHaveIndependentDelaysAndFractionalSteps() {
        assertEquals(50, GuardianRecovery.recoveredHp(50, 34));
        assertEquals(51.0945, GuardianRecovery.recoveredHp(50, 35), 0.000001);
        assertEquals(70, GuardianRecovery.recoveredHp(69.9, 35));
        assertEquals(100, GuardianRecovery.recoveredHp(100, 105));
        assertEquals(101.975, GuardianRecovery.recoveredHp(100, 106));
    }

    @Test void recoveryNeverResurrectsOrOverfills() {
        assertEquals(0, GuardianRecovery.recoveredHp(0, 500));
        assertEquals(200, GuardianRecovery.recoveredHp(199.9, 500));
        assertEquals(200, GuardianRecovery.recoveredHp(200, 500));
        assertTrue(Double.isNaN(GuardianRecovery.recoveredHp(Double.NaN, 500)));
    }
}
