package kim.biryeong.destiny.crucible;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class CrucibleHealthTest {
    @Test void damageQuietWindowAndShieldDelayAreIndependent() {
        assertEquals(50, CrucibleHealth.recoveredHp(50,34));
        assertEquals(51.5625, CrucibleHealth.recoveredHp(50,35));
        assertEquals(100, CrucibleHealth.recoveredHp(99.9,35));
        assertEquals(150, CrucibleHealth.recoveredHp(150,105));
        assertEquals(151.975, CrucibleHealth.recoveredHp(150,106));
    }
    @Test void cannotReviveOrOverheal() {
        assertEquals(0,CrucibleHealth.recoveredHp(0,500));
        assertEquals(230,CrucibleHealth.recoveredHp(229.9,500));
    }
}
