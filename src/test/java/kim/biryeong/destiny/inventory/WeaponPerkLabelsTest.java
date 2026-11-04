package kim.biryeong.destiny.inventory;

import kim.biryeong.destiny.weapon.WeaponPerks;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/** Every registered perk has a Korean label after all label sources load (static init order, duplicates). */
class WeaponPerkLabelsTest {
    @Test void everyPerkIsLabelled() {
        var unlabelled = WeaponPerks.ids().stream().filter(id -> WeaponPerkLabels.name(id).equals(id)).toList();
        assertEquals(java.util.List.of(), unlabelled);
    }
}
