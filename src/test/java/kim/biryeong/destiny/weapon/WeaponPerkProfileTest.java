package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class WeaponPerkProfileTest {
    @Test void eighteenExactSelectedItemsHavePermittedBaseTraitSocketsNotEveryWeapon() {
        var rolls = WeaponPerks.rolls();
        assertEquals(18, rolls.size()); assertEquals(18, rolls.stream().map(WeaponPerks.Roll::id).distinct().count());
        assertEquals(70, WeaponPerks.stowedTicks());
        var slots = new HashSet<WeaponSlot>();
        for (var roll : rolls) {
            var e = WeaponCatalog.find(roll.id()).orElseThrow(); var meta = WeaponCharacteristics.of(e);
            assertEquals(meta.bungieHash(), roll.hash()); assertEquals(WeaponPerks.HASH, roll.perkHash());
            assertFalse(meta.exotic()); assertNotEquals("sword", e.family()); slots.add(meta.slot());
        }
        assertEquals(Set.of(WeaponSlot.KINETIC, WeaponSlot.ENERGY, WeaponSlot.POWER), slots);
        assertFalse(rolls.stream().anyMatch(r -> r.id().equals("austringer")));
    }
    @Test void runtimeRowsExactlyMatchPinnedNonFakeCurrentlyRollableWeaponSocketEvidence() throws Exception {
        var evidence = JsonParser.parseString(Files.readString(Path.of("art/weapons/w60/references/socket-pools.json"))).getAsJsonObject();
        assertEquals(63, evidence.get("selectedCount").getAsInt()); assertEquals(18, evidence.get("supportedCount").getAsInt());
        var rows = evidence.getAsJsonArray("weapons"); assertEquals(WeaponPerks.rolls().size(), rows.size());
        var found = new HashSet<String>();
        for (var element : rows) {
            var r = element.getAsJsonObject(); var plug = r.getAsJsonObject("plugSetItem");
            assertFalse(r.get("isFakePlugSet").getAsBoolean()); assertTrue(plug.get("currentlyCanRoll").getAsBoolean());
            assertEquals(4241085061L, r.get("socketCategoryHash").getAsLong());
            assertEquals(WeaponPerks.HASH, plug.get("plugItemHash").getAsLong());
            var matching = WeaponPerks.rolls().stream().filter(roll -> roll.id().equals(r.get("id").getAsString())
                    && roll.socket() == r.get("socket").getAsInt()).findFirst().orElseThrow();
            assertEquals(matching.hash(), r.get("hash").getAsLong());
            assertEquals(matching.plugSetHash(), r.getAsJsonObject("socketEntry").get("randomizedPlugSetHash").getAsLong());
            assertEquals(matching.plugSetHash(), r.get("plugSetHash").getAsLong());
            assertTrue(found.add(matching.id() + ":" + matching.socket()));
        }
    }
    @Test void absoluteTimeIsCommunityMeasurementAndEnhancedIsNotSilentlyGranted() throws Exception {
        var timing = JsonParser.parseString(Files.readString(Path.of("art/weapons/w60/references/timing.json"))).getAsJsonObject();
        assertTrue(timing.getAsJsonObject("primaryChange").get("primary").getAsBoolean());
        assertFalse(timing.getAsJsonObject("baseMeasurement").get("primary").getAsBoolean());
        assertFalse(timing.getAsJsonObject("enhancedMeasurement").get("implemented").getAsBoolean());
        assertEquals(WeaponPerks.stowedTicks(), timing.get("baseSeconds").getAsDouble() * timing.get("ticksPerSecond").getAsInt());
        assertTrue(WeaponPerks.rolls().stream().noneMatch(r -> r.perkHash() == 3528046508L));
        assertThrows(UnsupportedOperationException.class, () -> WeaponPerks.rolls().clear());
    }
}
