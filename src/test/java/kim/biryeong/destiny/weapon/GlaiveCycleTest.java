package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class GlaiveCycleTest {
    @Test void threeFreeSwingsDoubleOnlyTheFinisherAndRespectCadence() {
        var c=new GlaiveCycle();c.bind(0,0);
        assertEquals(1,c.melee(0));assertEquals(0,c.melee(0));assertEquals(0,c.melee(11));
        assertEquals(1,c.melee(12));assertEquals(2,c.melee(24));assertEquals(1,c.melee(36));assertEquals(0,c.energy());
    }
    @Test void comboTimesOutButBindingDoesNotEraseAttackDeadlines() {
        var c=new GlaiveCycle();c.bind(0,0);c.melee(0);c.melee(12);c.bind(0,13);
        assertEquals(0,c.melee(13));assertEquals(1,c.melee(24));assertEquals(1,c.melee(55));
    }
    @Test void shotHasFourTickMeleeRecoveryEvenAcrossSwaps() {
        var c=new GlaiveCycle();c.bind(0,0);c.shot(20);c.bind(0,21);
        assertEquals(0,c.melee(23));assertEquals(1,c.melee(24));
    }
    @Test void fourConfirmedProjectileHitsFillOneItem() {
        var c=new GlaiveCycle();c.bind(0,0);for(int i=0;i<4;i++)c.hit();assertEquals(100000,c.energy());c.hit();assertEquals(100000,c.energy());
    }
    @Test void heldRegenerationIsOnePercentPerSecondWithoutOfflineCatchupOrDoubleTick() {
        var c=new GlaiveCycle();c.bind(0,0);for(int i=1;i<=20;i++)c.tick(i,false,false);
        assertEquals(1000,c.energy());c.tick(20,false,false);assertEquals(1000,c.energy());
        c.bind(c.energy(),1000);c.tick(1001,false,false);assertEquals(1050,c.energy());
    }
    @Test void guardDrainsOncePerTickAndExhaustionNeedsRelease() {
        var c=new GlaiveCycle();c.bind(1250,0);c.tick(1,true,false);assertTrue(c.guarding());assertEquals(625,c.energy());
        c.tick(1,true,false);assertEquals(625,c.energy());c.tick(2,true,false);assertFalse(c.guarding());
        c.hit();c.tick(3,true,false);assertFalse(c.guarding());assertEquals(25000,c.energy());
        c.tick(4,false,false);c.tick(5,true,false);assertTrue(c.guarding());
    }
    @Test void reloadAndMeleePreventGuardWithoutConsumingAmmoOrGrantingFreeGuard() {
        var c=new GlaiveCycle();c.bind(100000,0);c.tick(1,true,true);assertFalse(c.guarding());
        c.melee(1);c.tick(2,true,false);assertFalse(c.guarding());c.tick(13,true,false);assertTrue(c.guarding());
    }
    @Test void corruptStoredEnergyClampsAndStopRemovesProtection() {
        var c=new GlaiveCycle();c.bind(-7,0);assertEquals(0,c.energy());c.bind(Integer.MAX_VALUE,1);assertEquals(100000,c.energy());
        c.tick(2,true,false);assertTrue(c.guarding());c.stop();assertFalse(c.guarding());assertEquals(99375,c.energy());
    }
}
