package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Pure production cycle tests plus source-contract checks; real player authority requires master actualGT. */
class WeaponQuickdrawW185Test {
    @Test void exactTickZeroNineteenTwentyAndReadsCannotArmOrExtend() {
        var c=new QuickdrawCycle();var source=new Object();
        assertEquals(0,c.remaining(source,100));c.update(100,true,false);assertEquals(0,c.remaining(source,100));
        c.selected(source,100,true);
        for(int i=0;i<100;i++) { assertEquals(20,c.remaining(source,100));assertEquals(1,c.remaining(source,119)); }
        assertEquals(0,c.remaining(source,120));c.update(120,true,false);assertEquals(0,c.remaining(source,119));
    }
    @Test void sameIdentityCannotRefreshButRealAwayAndBackCanRearm() {
        var c=new QuickdrawCycle();var a=new Object();var b=new Object();
        c.selected(a,100,true);c.selected(a,119,true);assertEquals(1,c.remaining(a,119));
        c.aimInput(true);c.selected(a,119,true);assertEquals(0,c.remaining(a,119));
        c.selected(b,119,false);assertEquals(0,c.remaining(b,119));
        c.selected(a,119,true);assertEquals(20,c.remaining(a,119));assertEquals(0,c.remaining(b,119));
    }
    @Test void adsPressReleaseWithinSameTickPermanentlyCancelsEvenDuringHandling() {
        var c=new QuickdrawCycle();var a=new Object();c.selected(a,100,true);
        c.aimInput(false);assertEquals(20,c.remaining(a,100));
        c.aimInput(true);c.aimInput(false);c.update(100,true,false);
        assertEquals(0,c.remaining(a,100));assertEquals(0,c.remaining(a,119));
        c.selected(a,101,true);assertEquals(0,c.remaining(a,101));
    }
    @Test void sourceContextOrAdsInvalidationCannotRecoverWithoutSelection() {
        for(int scenario=0;scenario<3;scenario++) {
            var c=new QuickdrawCycle();var a=new Object();c.selected(a,100,true);
            c.update(scenario==2?99:101,scenario!=0,scenario==1);
            c.update(102,true,false);assertEquals(0,c.remaining(a,102));
            c.selected(a,102,true);assertEquals(0,c.remaining(a,102));
            c.clear();assertEquals(0,c.remaining(a,102));c.selected(a,103,true);assertEquals(20,c.remaining(a,103));
        }
    }
    @Test void identityNotEqualityAndInvalidClockCannotGrant() {
        var c=new QuickdrawCycle();var a=new String("same");var b=new String("same");
        c.selected(a,10,true);assertEquals(0,c.remaining(b,10));c.selected(b,11,true);assertEquals(20,c.remaining(b,11));
        for(long tick:new long[]{-1,Long.MIN_VALUE,Long.MAX_VALUE,Long.MAX_VALUE-19}) {
            c.clear();c.selected(a,tick,true);assertEquals(0,c.remaining(a,tick));
        }
        c.clear();c.selected(a,Long.MAX_VALUE-20,true);assertEquals(20,c.remaining(a,Long.MAX_VALUE-20));assertEquals(0,c.remaining(a,Long.MAX_VALUE));
    }
    @Test void absentOwnerAllWrappersPreserveBaseAndDoNotArm() {
        WeaponQuickdraw.clear();WeaponQuickdraw.selected(null,null);WeaponQuickdraw.aimInput(null,true);
        WeaponQuickdraw.update(null);WeaponQuickdraw.changed(null,null);WeaponQuickdraw.cleanup(null);WeaponQuickdraw.edited(null);
        assertEquals(0,WeaponQuickdraw.remaining(null));
        assertEquals(17,WeaponQuickdraw.handlingTicks(null,null,true,17));assertEquals(23,WeaponQuickdraw.handlingTicks(null,null,false,23));
        WeaponQuickdraw.clear();
    }
    @Test void productionReadPathsDoNotMutateArmOrGrantUnrelatedStats() throws Exception {
        String source=Files.readString(Path.of("src/main/java/kim/biryeong/destiny/weapon/WeaponQuickdraw.java"));
        String reads=source.substring(source.indexOf("public static int remaining"),source.indexOf("public static void edited"));
        for(String forbidden:List.of("new Session","SESSIONS.put","SESSIONS.remove","cycle.selected(","cycle.update(","cycle.clear(","cycle.aimInput(",".set(","Guardians.data(","Guardians.runtime(")) assertFalse(reads.contains(forbidden),forbidden);
        for(String forbidden:List.of("WeaponAiming.aiming","adsTicks(","reloadTicks(","damageMultiplier(","System.currentTimeMillis","getAttachedOrCreate","cancelUseForSkill","WeaponHandling.blocked"))assertFalse(source.contains(forbidden),forbidden);
        assertTrue(source.contains("QuickdrawProfile.compatible(s.entry,ThreatDetectorProfile.ID,r)"));
        assertTrue(source.contains("p.getMainHandItem() == stack ? WeaponThreatDetector.stacks(p) : s.incomingThreats"));
        assertFalse(reads.contains("selectionSample("));
        String selection=source.substring(source.indexOf("public static void selected"),source.indexOf("public static void aimInput"));
        assertTrue(selection.indexOf("QuickdrawProfile.rolls().contains(roll)") < selection.indexOf("WeaponThreatDetector.selectionSample(p,incoming)"));
        assertTrue(selection.contains("QuickdrawProfile.compatible(entry,ThreatDetectorProfile.ID,r)"));
    }
    @Test void runtimeAuthorityIncludesOwnerWorldInventoryRollAndExistingContext() throws Exception {
        String source=Files.readString(Path.of("src/main/java/kim/biryeong/destiny/weapon/WeaponQuickdraw.java"));
        for(String guard:List.of("s.owner != p","s.level != p.level()","WeaponAiming.requested(p)","p.getInventory().getItem(s.slot) != s.stack",
            "data != s.data","runtime != s.runtime","runtime.lastActionTick.equals(s.actions)","p.getMainHandItem() == s.stack",
            "p.getInventory().getSelectedSlot() == s.slot","WeaponLoadout.canUse(p)","now(p) == s.selectedAt",
            "p.getMainHandItem() == s.outgoing","e.stack() == stack","QuickdrawProfile.rolls().contains(roll)","filter(s.roll::equals)"))assertTrue(source.contains(guard),guard);
    }
}
