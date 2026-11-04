package kim.biryeong.destiny.weapon;

import java.nio.file.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Executes the production pure ownership lease. Source boundary assertions verify adapter wiring;
 * these are explicitly not a substitute for Master's real ServerPlayer/FabricGT scenarios. */
class WeaponZenMomentW188Test {
    private static WeaponZenMoment.Identity id(Object[] o, boolean mode, int slot) {
        return new WeaponZenMoment.Identity(o[0],o[1],o[2],o[3],o[4],o[5],mode,slot);
    }
    private static Object[] objects() { return new Object[]{new Object(),new Object(),new Object(),new Object(),new Object(),new Object()}; }
    @Test void exactOriginalOwnerWorldStackDataRuntimeClassRequired() {
        var original=objects(); var identity=id(original,true,0); var lease=new WeaponZenMoment.Lease(identity,10);
        assertTrue(lease.valid(id(original,true,0),10));
        for(int n=0;n<original.length;n++) {
            var changed=original.clone();changed[n]=new Object();
            assertFalse(lease.valid(id(changed,true,0),10),"identity index "+n);
        }
        assertFalse(lease.valid(id(original,false,0),10));
        assertFalse(lease.valid(id(original,true,1),10)); assertFalse(lease.valid(null,10));
    }
    @Test void equalValueCopyAndSameUuidOwnerReplacementCannotBorrow() {
        var original=objects(); original[0]=new String("same uuid");original[2]=new String("same item data");
        var lease=new WeaponZenMoment.Lease(id(original,true,0),10);
        var copy=original.clone();copy[2]=new String("same item data");
        assertFalse(lease.valid(id(copy,true,0),10));
        copy=original.clone();copy[0]=new String("same uuid"); assertFalse(lease.valid(id(copy,true,0),10));
    }
    @Test void revokeIsPermanentEvenWhenClearReselectRestoresSameObjectsInSameTick() {
        var identity=id(objects(),true,0);var old=new WeaponZenMoment.Lease(identity,10);
        old.revoke(); assertFalse(old.valid(identity,10)); old.observe(10); assertFalse(old.valid(identity,10));
        assertFalse(old.valid(identity,11)); assertTrue(new WeaponZenMoment.Lease(identity,10).valid(identity,10));
    }
    @Test void clockRollbackRejectedAndQueriesDoNotMoveObservedTime() {
        var identity=id(objects(),false,8);var lease=new WeaponZenMoment.Lease(identity,10);
        assertFalse(lease.valid(identity,9)); assertFalse(lease.valid(identity,-1));
        assertTrue(lease.valid(identity,15)); assertTrue(lease.valid(identity,10));
        lease.observe(15);assertFalse(lease.valid(identity,14));assertTrue(lease.valid(identity,15));
    }
    @Test void nullOwnerAndNoPaidSourceStayNeutral() {
        assertSame(WeaponZenMoment.Token.NONE,WeaponZenMoment.capture(null));
        assertEquals(0,WeaponZenMoment.stackUnits(null));assertEquals(0,WeaponZenMoment.stacks(null));
        assertEquals(0,WeaponZenMoment.remaining(null)); assertEquals(1,WeaponZenMoment.flinchScalar(null));
        WeaponZenMoment.confirmed(null,WeaponZenMoment.Token.NONE,null,1);
        WeaponZenMoment.confirmed(null,null,null,1);WeaponZenMoment.update(null);
        WeaponZenMoment.changed(null,null);WeaponZenMoment.cleanup(null);WeaponZenMoment.clear();
    }
    private static String source() throws Exception {
        return Files.readString(Path.of("src/main/java/kim/biryeong/destiny/weapon/WeaponZenMoment.java"));
    }
    @Test void adapterRequiresCanonicalSelectedBaseSingleOriginalAndLiveContext() throws Exception {
        String s=source();
        for(String guard:List.of("!p.isRemoved()","!p.isSpectator()","!p.hasDisconnected()","r.superSession == null",
                "WeaponLoadout.canUse(p)","stack.getCount() == 1","p.getInventory().getItem(slot) == stack",
                "p.getMainHandItem() == stack","s.owner == p","s.level == p.level()","s.lease.valid(identity(p), now(p))",
                "getAttachedOrElse(Guardians.DATA, null)","data.guardianClass()","WeaponLoadout.enabled(p)",
                "ZenMomentProfile.supports(entry)","ZenMomentProfile.rolls().contains(roll)","filter(s.entry::equals)","filter(s.roll::equals)"))
            assertTrue(s.contains(guard),guard);
        assertFalse(s.contains("Guardians.data(")); assertFalse(s.contains("getAttachedOrCreate("));
    }
    @Test void confirmedIsTheOnlyCreditMutationAndAcceptsLethalEnemies() throws Exception {
        String s=source();
        assertEquals(1,s.split("s.cycle.confirmed",-1).length-1);
        for(String guard:List.of("token.source","!Float.isFinite(actualPositiveDamage)","actualPositiveDamage <= 0",
                "valid(p, s)","target.level() == s.level","target instanceof Enemy || target instanceof Mob",
                "!p.isAlliedTo(target)","tame.isTame()","target instanceof Player","target instanceof ArmorStand")) assertTrue(s.contains(guard),guard);
        assertFalse(s.contains("target.isAlive()"));
        for(String forbidden:List.of("stabilityBonus(","recoilScalar(","accuracyScalar(","WeaponAiming.shot(","WeaponItems.save(","broadcastChanges(","System.currentTimeMillis","new Thread")) assertFalse(s.contains(forbidden),forbidden);
    }
    @Test void allRemovalPathsRevokeLeaseAndDebugReadsNeverCreateSessions() throws Exception {
        String s=source();
        for(String name:List.of("edited(ItemStack", "changed(ServerPlayer", "cleanup(ServerPlayer", "clear()")) {
            int start=s.indexOf("public static void "+name);assertTrue(start>=0);
            int end=s.indexOf("public static void",start+1);if(end<0)end=s.length();
            assertTrue(s.substring(start,end).contains("lease.revoke()"),name);
        }
        int a=s.indexOf("private static Session active"), b=s.indexOf("public static void edited",a);
        String reads=s.substring(a,b);
        for(String write:List.of("computeIfAbsent","new Session",".confirmed(",".observe(","update(p)")) assertFalse(reads.contains(write),write);
    }
}
