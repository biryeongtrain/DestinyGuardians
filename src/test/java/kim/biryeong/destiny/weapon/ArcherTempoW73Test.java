package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ArcherTempoW73Test {
    @Test void exactSingleSelectedBaseSocketIsNotAnEnhancedOrCatalystOrRepriseGrant() {
        assertEquals(java.util.List.of(new WeaponPerks.Roll("whispering_slab",211938782L,3,201365942L,1885424927L)),ArcherTempoProfile.rolls());
        assertThrows(UnsupportedOperationException.class,()->ArcherTempoProfile.rolls().clear());
        assertEquals(567,ArcherTempoProfile.timing(WeaponCatalog.find("whispering_slab").orElseThrow()).baseDrawMs());
        assertEquals(12,ArcherTempoProfile.timing(WeaponCatalog.find("whispering_slab").orElseThrow()).baseDrawTicks());
        assertEquals(9,ArcherTempoProfile.timing(WeaponCatalog.find("whispering_slab").orElseThrow()).acceleratedTicks());
        assertEquals(11,ArcherTempoProfile.timing(WeaponCatalog.find("biting_winds").orElseThrow()).acceleratedTicks());
    }
    @Test void precisionHitStartsExactSixtyTickWindowAndReadsCannotRefreshIt() {
        var c=new ArcherTempoCycle();assertEquals(0,c.remaining(100));c.precisionHit(100);
        for(int i=0;i<60;i++)for(int j=0;j<20;j++)assertEquals(60-i,c.remaining(100+i));
        assertEquals(1,c.remaining(159));assertEquals(0,c.remaining(160));assertEquals(0,c.remaining(10000));
    }
    @Test void anotherPrecisionHitRefreshesButDoesNotStackDuration() {
        var c=new ArcherTempoCycle();c.precisionHit(100);c.precisionHit(159);
        assertEquals(60,c.remaining(159));assertEquals(1,c.remaining(218));assertEquals(0,c.remaining(219));
        c.precisionHit(219);assertEquals(60,c.remaining(219));
    }
    @Test void invalidClockOverflowAndBackwardQueriesCannotCreateAnEnormousWindow() {
        var c=new ArcherTempoCycle();c.precisionHit(-1);assertEquals(0,c.remaining(0));
        c.precisionHit(Long.MAX_VALUE-59);assertEquals(0,c.remaining(Long.MAX_VALUE-59));
        c.precisionHit(100);assertEquals(0,c.remaining(99));assertEquals(0,c.remaining(-1));
        c.precisionHit(Long.MAX_VALUE-60);assertEquals(1,c.remaining(Long.MAX_VALUE-1));assertEquals(0,c.remaining(Long.MAX_VALUE));
    }
    @Test void scaleRawMillisecondsBeforeRoundingNotRoundedBaseTicks() {
        assertEquals(10,ArcherTempoProfile.acceleratedTicks(612));
        assertEquals(9,ArcherTempoProfile.acceleratedTicks(567));
        assertEquals(8,ArcherTempoProfile.acceleratedTicks(501));
        assertNotEquals((int)Math.ceil(Math.ceil(501/50.)*.75),ArcherTempoProfile.acceleratedTicks(501));
        assertEquals(1,ArcherTempoProfile.acceleratedTicks(1));
        assertThrows(IllegalArgumentException.class,()->ArcherTempoProfile.acceleratedTicks(0));
        assertThrows(IllegalArgumentException.class,()->ArcherTempoProfile.acceleratedTicks(60001));
    }
    @Test void onlyChargeDurationChangesAndPartialDrawUsesAcceleratedNormalizedProgress() {
        var e=WeaponCatalog.find("whispering_slab").orElseThrow();var p=WeaponProfile.forEntry(e);
        var accelerated=ArcherTempoProfile.accelerated(e,p);
        assertTrue(accelerated.chargeTicks()<p.chargeTicks());
        for(var component:WeaponProfile.class.getRecordComponents()) {
            if(component.getName().equals("chargeTicks"))continue;
            try {assertEquals(component.getAccessor().invoke(p),component.getAccessor().invoke(accelerated),component.getName());}
            catch(ReflectiveOperationException ex) {throw new AssertionError(ex);}
        }
        assertSame(accelerated,WeaponBowDraw.shot(accelerated,accelerated.chargeTicks()));
        assertEquals(p,WeaponProfile.forEntry(e));
        var slow=WeaponBowDraw.shot(p,accelerated.chargeTicks());
        assertTrue(slow.damage()<accelerated.damage());assertTrue(slow.speed()<accelerated.speed());
        var half=WeaponBowDraw.shot(accelerated,accelerated.chargeTicks()/2);
        assertTrue(half.damage()>0 && half.damage()<accelerated.damage());
        assertEquals(p.reloadTicks(),half.reloadTicks());assertEquals(p.magazine(),half.magazine());
    }
    @Test void fullAcceleratedArrowStillPaysOneAndNockKeepsBaseDeadline() {
        var e=WeaponCatalog.find("whispering_slab").orElseThrow();var p=WeaponProfile.forEntry(e);
        var boosted=ArcherTempoProfile.accelerated(e,p);var c=new WeaponCycle();var m=new WeaponMagazine(p,1,0);
        assertTrue(c.startCharge(100));assertFalse(c.charged(100+boosted.chargeTicks()-1,boosted.chargeTicks()));
        assertTrue(c.charged(100+boosted.chargeTicks(),boosted.chargeTicks()));
        assertTrue(c.fire(100+boosted.chargeTicks(),boosted,m));assertEquals(0,m.rounds());
        assertFalse(c.fire(100+boosted.chargeTicks(),boosted,m));
        long nockAt=100+boosted.chargeTicks();assertTrue(c.startReload(nockAt,p,m));
        assertFalse(c.finishReload(nockAt+p.firstReloadTicks()-1,m));assertEquals(0,m.rounds());
        assertTrue(c.finishReload(nockAt+p.firstReloadTicks(),m));assertEquals(1,m.rounds());
    }
    @Test void unsupportedBowAndAlreadyModifiedProfileCannotBeAcceleratedAgain() {
        var e=WeaponCatalog.find("whispering_slab").orElseThrow();var p=WeaponProfile.forEntry(e);
        assertThrows(IllegalArgumentException.class,()->ArcherTempoProfile.accelerated(e,ArcherTempoProfile.accelerated(e,p)));
        var unsupported=WeaponCatalog.find("biting_winds").orElseThrow();
        assertThrows(IllegalArgumentException.class,()->ArcherTempoProfile.accelerated(unsupported,WeaponProfile.forEntry(unsupported)));
        assertEquals(60,ArcherTempoProfile.perk().durationTicks());assertEquals(.75,ArcherTempoProfile.perk().drawScalar());
    }
}
