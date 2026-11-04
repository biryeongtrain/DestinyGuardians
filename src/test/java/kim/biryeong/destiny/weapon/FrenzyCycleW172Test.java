package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class FrenzyCycleW172Test {
    private static FrenzyCycle fresh(){return new FrenzyCycle(240,100,144);}
    private static void prime(FrenzyCycle c){c.damage(0);c.damage(90);c.damage(180);c.damage(239);c.update(240);}
    @Test void exactlyTwelveSecondsOfContinuousRealCombatGrantsFullSevenPointTwoSeconds(){
        var c=fresh();c.damage(0);c.damage(90);c.damage(180);c.damage(239);
        assertEquals(239,c.combatTicks(239));assertEquals(0,c.remaining(239));
        c.update(240);assertEquals(144,c.remaining(240));assertEquals(240,c.combatTicks(240));
        c.update(241);assertEquals(143,c.remaining(241));
    }
    @Test void fiveSecondGapResetsPrimingButNotTheAlreadyEarnedBuff(){
        var c=fresh();c.damage(0);c.damage(99);c.damage(199);c.update(240);
        assertEquals(41,c.combatTicks(240));assertEquals(0,c.remaining(240));
        prime(c=fresh());c.update(339);assertEquals(0,c.combatTicks(339));assertEquals(45,c.remaining(339));
        c.update(384);assertEquals(0,c.remaining(384));
    }
    @Test void realDamageRefreshesWhileQueriesAndUpdatesDoNot(){
        var c=fresh();prime(c);for(int i=0;i<100;i++){c.remaining(260);c.combatTicks(260);c.update(260);}
        assertEquals(124,c.remaining(260));c.damage(260);assertEquals(144,c.remaining(260));
        c.update(403);assertEquals(1,c.remaining(403));c.update(404);assertEquals(0,c.remaining(404));
    }
    @Test void lateDamageWithinEarnedBuffRefreshesEvenAfterFiveSecondCombatGap(){
        var c=fresh();prime(c);c.update(340);assertEquals(44,c.remaining(340));
        c.damage(350);assertEquals(144,c.remaining(350));assertEquals(0,c.combatTicks(350));
        c.update(494);assertEquals(0,c.remaining(494));
    }
    @Test void isolatedEventsAndDryTimeNeverAccumulateTwelveSeconds(){
        var c=fresh();for(long t=0;t<3000;t+=100){c.damage(t);assertEquals(0,c.remaining(t));}
        c.update(8000);assertEquals(0,c.combatTicks(8000));assertEquals(0,c.remaining(8000));
    }
    @Test void sameTickEventsDoNotMultiplyDurationOrAdvancePriming(){
        var c=fresh();for(int i=0;i<100;i++)c.damage(0);assertEquals(0,c.combatTicks(0));
        prime(c);for(int i=0;i<100;i++)c.damage(240);assertEquals(144,c.remaining(240));
    }
    @Test void backwardsClockAndExplicitResetDiscardProgress(){
        var c=fresh();prime(c);c.update(20);assertEquals(0,c.remaining(20));assertEquals(0,c.combatTicks(20));
        c.damage(20);assertEquals(0,c.remaining(20));prime(c);c.reset();assertEquals(0,c.remaining(240));
        assertThrows(IllegalArgumentException.class,()->c.update(-1));
    }
    @Test void deadlineOverflowIsBoundedAndNegativeReadsAreInert(){
        var c=new FrenzyCycle(1,100,144);c.damage(Long.MAX_VALUE-3);c.update(Long.MAX_VALUE-2);
        assertEquals(2,c.remaining(Long.MAX_VALUE-2));assertEquals(0,c.remaining(Long.MAX_VALUE));
        assertEquals(0,c.remaining(-1));assertEquals(0,c.combatTicks(-1));
    }
    @Test void invalidDurationsRejected(){
        assertThrows(IllegalArgumentException.class,()->new FrenzyCycle(0,100,144));
        assertThrows(IllegalArgumentException.class,()->new FrenzyCycle(240,0,144));
        assertThrows(IllegalArgumentException.class,()->new FrenzyCycle(240,100,0));
    }
}
