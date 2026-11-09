package kim.biryeong.destiny.weapon;
import kim.biryeong.destiny.combat.VoidOvershieldPool;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class PerkExpansionSupportShieldTest {
    @Test void cureCooldownRejectsDuplicateActivationAndSecondPulseIsOneShot() {
        var pulse = new kim.biryeong.destiny.combat.CurePulse();
        assertTrue(pulse.accept(100, 3)); assertEquals(0,pulse.pulse(100));
        assertFalse(pulse.accept(100, 6)); assertEquals(0,pulse.pulse(101)); assertEquals(3,pulse.pulse(102)); assertEquals(0,pulse.pulse(103));
        assertFalse(pulse.accept(119,3)); assertTrue(pulse.expired(120)); assertTrue(pulse.accept(120,3));
        assertTrue(pulse.expired(119));
    }
    @Test void expiresOnlyOwnedLayerAndPreservesForeignGainsAndLosses() {
        var pool = new VoidOvershieldPool(10);
        pool.granted(10,14); assertEquals(4,pool.owned());
        pool.observe(20); assertEquals(4,pool.owned()); assertEquals(16,pool.withoutOwned(20));
        pool.observe(18); assertEquals(2,pool.owned()); assertEquals(16,pool.withoutOwned(18));
        pool.observe(5); assertEquals(0,pool.owned()); assertEquals(5,pool.withoutOwned(5));
    }
    @Test void resistanceAppliesOnlyUntilOwnedPortionBreaks() {
        assertEquals(3,VoidOvershieldPool.resisted(10,4),.0001);
        assertEquals(6,VoidOvershieldPool.resisted(20,6),.0001);
        assertEquals(16,VoidOvershieldPool.resisted(30,6),.0001);
        assertEquals(30,VoidOvershieldPool.resisted(30,0),.0001);
    }
    @Test void refreshingAddsOnlyActualGainAndDoesNotOwnExistingForeignAbsorption() {
        var pool = new VoidOvershieldPool(10); pool.granted(10,14); pool.observe(12);
        pool.granted(12,14); assertEquals(4,pool.owned()); assertEquals(10,pool.withoutOwned(14));
        pool.granted(14,14); assertEquals(4,pool.owned());
    }
}
