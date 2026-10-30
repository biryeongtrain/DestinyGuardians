package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.util.OptionalDouble;
import static org.junit.jupiter.api.Assertions.*;

class CrucibleWeaponDamageTest {
    @Test void preservesOfficialOverridesAsAbsoluteDamage() {
        var duke = CrucibleWeaponDamage.find("duke_mk_44").orElseThrow();
        assertEquals(48.7, duke.body(), 1e-9);
        assertEquals(90.1, duke.precision(), 1e-9);
        assertEquals(27.1, CrucibleWeaponDamage.find("gnawing_hunger").orElseThrow().precision(), 1e-9);
        assertEquals(22.0, CrucibleWeaponDamage.find("halfdan_d").orElseThrow().body(), 1e-9);
    }
    @Test void damageUnitsArePerPelletOrBoltNotWholeCartridge() {
        var shotgun = CrucibleWeaponDamage.find("mindbender_s_ambition_adept").orElseThrow();
        assertEquals("per_pellet", shotgun.component());
        assertEquals(27.999, shotgun.body(), 1e-9);
        assertEquals(335.988, shotgun.body() * 12, 1e-9);
        var fusion = CrucibleWeaponDamage.find("hollow_words").orElseThrow();
        assertEquals("per_bolt", fusion.component());
        assertEquals(48.0039, fusion.body(), 1e-9);
    }
    @Test void preservesUnknownIdsAndSeparatesGlaiveMelee() {
        assertTrue(CrucibleWeaponDamage.find("not_a_weapon").isEmpty());
        assertTrue(CrucibleWeaponDamage.find(null).isEmpty());
        var glaive = CrucibleWeaponDamage.find("nezarec_s_whisper").orElseThrow();
        assertEquals(97.04, glaive.melee().orElseThrow(), 1e-9);
        assertTrue(glaive.explosion().isEmpty());
        assertTrue(glaive.body() > glaive.melee().orElseThrow());
    }
    @Test void rejectsNonFiniteOrNonPositiveDamage() {
        assertThrows(IllegalArgumentException.class, () -> new CrucibleWeaponDamage.Row(
                Double.NaN, 1, OptionalDouble.empty(), OptionalDouble.empty(), "per_bullet"));
        assertThrows(IllegalArgumentException.class, () -> new CrucibleWeaponDamage.Row(
                1, 1, OptionalDouble.of(0), OptionalDouble.empty(), "per_bullet"));
    }
}
