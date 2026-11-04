package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class OverflowMagazineW193Test {
    private WeaponProfile profile(boolean infinite) {
        return new WeaponProfile(WeaponProfile.Mode.HITSCAN,1,3,10,infinite?0:20,30,40,0,1,1,0,0,0,0,false,infinite);
    }
    @Test void finiteTopUpSpendsRealReservesAndPreservesEveryRound() {
        var m=new WeaponMagazine(profile(false),5,8,10);
        long total=m.total();
        assertEquals(18,m.reloadOverflow(25));
        assertEquals(23,m.rounds());assertEquals(0,m.reserve());assertEquals(0,m.overflow());
        assertEquals(total,m.total());assertEquals(23,m.loadedLimit());
        assertEquals(0,m.reloadOverflow(25));assertEquals(0,m.reloadOverflow(20));
    }
    @Test void overBaseCannotGenerateNegativeRefundsOrReloadAgain() {
        var m=new WeaponMagazine(profile(false),10,20);m.reloadOverflow(20);
        long total=m.total();
        assertEquals(0,m.generateLoaded(2));assertEquals(0,m.reload());assertFalse(m.canReload());
        assertEquals(20,m.rounds());assertEquals(total,m.total());
        for(int i=0;i<11;i++)assertTrue(m.consume());
        assertTrue(m.canReload());assertEquals(1,m.reload());assertEquals(10,m.rounds());
        assertEquals(total-11,m.total());
    }
    @Test void authorizedRoundTripRestoresLoadedButRevocationConservesAsDebt() {
        var p=profile(false);var m=new WeaponMagazine(p,10,20);m.reloadOverflow(25);
        var saved=new WeaponMagazine(p,m.rounds(),m.reserve(),m.overflow(),m.loadedLimit());
        assertEquals(25,saved.rounds());assertEquals(m.total(),saved.total());
        var revoked=new WeaponMagazine(p,m.rounds(),m.reserve(),m.overflow());
        assertEquals(10,revoked.rounds());assertEquals(m.total(),revoked.total());
    }
    @Test void primaryOverloadIsFiniteMagazineAndDoesNotUnlockFutureFreeRefills() {
        var m=new WeaponMagazine(profile(true),10,0);
        assertEquals(10,m.reloadOverflow(20));assertEquals(20,m.rounds());
        assertTrue(m.consume(20));assertFalse(m.consume());
        assertEquals(10,m.reload());assertEquals(10,m.rounds());
    }
    @Test void legacyPrimaryDebtIsRetiredBeforeInfiniteSupply() {
        var m=new WeaponMagazine(profile(true),10,0,Long.MAX_VALUE-10);
        assertEquals(15,m.reloadOverflow(25));assertEquals(Long.MAX_VALUE,m.total());
        assertEquals(Long.MAX_VALUE-25,m.overflow());
    }
}
