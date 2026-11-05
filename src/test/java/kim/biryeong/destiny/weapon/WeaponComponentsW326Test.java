package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.*;

class WeaponComponentsW326Test {
    /** User request: green = barrel + magazine, blue = barrel + magazine + one trait. */
    @Test void tierColumns() {
        assertEquals(2, WeaponRarity.UNCOMMON.componentColumns());
        assertEquals(0, WeaponRarity.UNCOMMON.traitColumns());
        assertEquals(2, WeaponRarity.RARE.componentColumns());
        assertEquals(1, WeaponRarity.RARE.traitColumns());
    }

    /** Every Red War low-tier skin base can roll both columns, so a green/blue drop always shows two plugs. */
    @Test void everyW325BaseHasBothPools() throws Exception {
        var reg = JsonParser.parseString(Files.readString(Path.of("art/weapons/w325/registry.json"))).getAsJsonArray();
        assertFalse(WeaponComponents.all().isEmpty());
        for (var w : reg) {
            var o = w.getAsJsonObject();
            if (o.get("tier").getAsString().equals("common")) continue;
            var entry = WeaponCatalog.find(o.get("base").getAsString()).orElseThrow();
            for (var slot : WeaponComponents.Slot.values())
                assertFalse(WeaponComponents.pool(entry, slot).isEmpty(), entry.id() + " " + slot);
        }
    }

    @Test void magazineStatToRounds() {
        assertEquals(32, WeaponComponents.magazine(32, 0));
        assertTrue(WeaponComponents.magazine(32, 30) > 32);          // Extended Mag
        assertTrue(WeaponComponents.magazine(32, -20) < 32);
        assertEquals(1, WeaponComponents.magazine(1, 30));           // rockets keep one round
        assertTrue(WeaponComponents.magazine(4, -100) >= 1);
    }
}
