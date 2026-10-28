package kim.biryeong.destiny.weapon;

import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class InsertRoutingW179Test {
    @Test void sixExactRoutesIncludeDenseLongArmAndShotguns() {
        var routes=Map.of("ikelos_sg_v1_0_1","weapon_insert_w221_ikelos_sg_v1_0_1/ikelos_sg_v1_0_1",
                "parcel_of_stardust_fell_to_earth","weapon_insert_w221_parcel_of_stardust_fell_to_earth/parcel_of_stardust_fell_to_earth",
                "long_arm","weapon_insert_w222_long_arm/long_arm",
                "first_in_last_out","weapon_insert_w208_first_in_last_out/first_in_last_out",
                "mindbender_s_ambition_adept","weapon_insert_w221_mindbender_s_ambition_adept/mindbender_s_ambition_adept",
                "dust_rock_blues","weapon_insert_w207_dust_rock_blues/dust_rock_blues");
        assertEquals("destiny:"+routes.get("long_arm"),WeaponInsertPresentation.model().toString());
        for(var e:WeaponCatalog.all()) {
            assertEquals(routes.containsKey(e.id()),WeaponInsertPresentation.supports(e),e.id());
            if(routes.containsKey(e.id())) assertEquals("destiny:"+routes.get(e.id()),WeaponInsertPresentation.model(e).toString());
            else assertThrows(IllegalArgumentException.class,()->WeaponInsertPresentation.model(e));
        }
        assertFalse(WeaponInsertPresentation.supports(null));
        assertThrows(IllegalArgumentException.class,()->WeaponInsertPresentation.model(null));
    }
    @Test void noCosmeticChangeToIncrementalMechanics() {
        var e=WeaponCatalog.find("mindbender_s_ambition_adept").orElseThrow();
        var profile=WeaponProfile.forEntry(e);
        assertEquals(5,profile.magazine()); assertEquals(16,profile.firstReloadTicks());
        assertEquals(16,profile.reloadTicks()); assertEquals(1,profile.roundsPerInsert());
        assertTrue(profile.shellReload());
        assertEquals(4,WeaponInsertPresentation.SELECTOR_INDEX);
        assertEquals(6,WeaponInsertPresentation.RETURN_TICKS);
    }
}
