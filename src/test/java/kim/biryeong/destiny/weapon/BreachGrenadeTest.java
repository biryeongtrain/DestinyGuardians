package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class BreachGrenadeTest {
    @Test void exactOfficialSelectedLightweightOnly() {
        var all=WeaponCatalog.all().stream().filter(BreachGrenade::supports).toList();
        assertEquals(1,all.size());
        assertEquals("salvager_s_salvo",all.getFirst().id());
        assertEquals(2060863616L,WeaponCharacteristics.of(all.getFirst()).bungieHash());
        assertEquals(474269988L,BreachGrenade.INTRINSIC_HASH);
        assertFalse(BreachGrenade.supports(null));
    }
    @Test void waveAndHeavyAndEveryOtherWeaponExcluded() {
        for(var e:WeaponCatalog.all())
            assertEquals(e.id().equals("salvager_s_salvo"),BreachGrenade.supports(e),e.id());
    }
    @Test void releaseAtArmingBoundaryRequestsExactlyOneExplosion() {
        var f=new BreachGrenade();
        assertTrue(f.controlled());assertFalse(f.detonate());
        f.release(BreachGrenade.ARM_TICKS);
        assertFalse(f.controlled());assertTrue(f.detonate());
        f.release(0);assertTrue(f.detonate());
    }
    @Test void earlyReleaseIsConsumedAndNotBufferedForLater() {
        for(int age=-1;age<BreachGrenade.ARM_TICKS;age++) {
            var f=new BreachGrenade();f.release(age);
            assertFalse(f.controlled());assertFalse(f.detonate());
            f.release(100);assertFalse(f.detonate());
        }
    }
    @Test void cancellationIsNotAReleaseEvenAfterArming() {
        var f=new BreachGrenade();f.detach();f.release(1000);
        assertFalse(f.controlled());assertFalse(f.detonate());
    }
    @Test void laterCancellationDoesNotUndoAlreadyAcceptedRelease() {
        var f=new BreachGrenade();f.release(100);f.detach();
        assertTrue(f.detonate());
    }
    @Test void sixFacesReflectNormalAndDampTangentsWithoutEnergyGain() {
        for(int axis=0;axis<3;axis++)for(int sign:new int[]{-1,1}) {
            int[] n=new int[3];n[axis]=sign;
            var r=BreachGrenade.reflect(1.5,-.8,.25,n[0],n[1],n[2]);
            double[] in={1.5,-.8,.25},out={r.x(),r.y(),r.z()};
            for(int i=0;i<3;i++)assertEquals(in[i]*BreachGrenade.RESTITUTION*(i==axis?-1:1),out[i],1e-12);
            assertTrue(r.x()*r.x()+r.y()*r.y()+r.z()*r.z()<1.5*1.5+.8*.8+.25*.25);
        }
    }
    @Test void invalidReflectionDataRejected() {
        assertThrows(IllegalArgumentException.class,()->BreachGrenade.reflect(Double.NaN,0,0,0,1,0));
        assertThrows(IllegalArgumentException.class,()->BreachGrenade.reflect(0,Double.POSITIVE_INFINITY,0,0,1,0));
        assertThrows(IllegalArgumentException.class,()->BreachGrenade.reflect(0,0,0,1,1,0));
        assertThrows(IllegalArgumentException.class,()->BreachGrenade.reflect(0,0,0,0,0,0));
        assertThrows(IllegalArgumentException.class,()->BreachGrenade.reflect(0,0,0,Integer.MIN_VALUE,0,0));
    }
    @Test void retainedOfficialDefinitionsMatchExactSocketAndHoldReleaseText() throws Exception {
        var base=java.nio.file.Path.of("art/weapons/w82/references");
        var item=com.google.gson.JsonParser.parseString(java.nio.file.Files.readString(base.resolve("bungie-2060863616.json"))).getAsJsonObject();
        var intrinsic=com.google.gson.JsonParser.parseString(java.nio.file.Files.readString(base.resolve("bungie-474269988.json"))).getAsJsonObject();
        assertEquals(BreachGrenade.WEAPON_HASH,item.get("hash").getAsLong());
        assertEquals(BreachGrenade.INTRINSIC_HASH,intrinsic.get("hash").getAsLong());
        assertEquals(BreachGrenade.INTRINSIC_HASH,item.getAsJsonObject("sockets").getAsJsonArray("socketEntries")
                .get(0).getAsJsonObject().get("singleInitialItemHash").getAsLong());
        var description=intrinsic.getAsJsonObject("displayProperties").get("description").getAsString();
        assertTrue(description.contains("release to detonate"));
        assertTrue(description.contains("remote detonation"));
    }

}
