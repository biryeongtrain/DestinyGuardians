package kim.biryeong.destiny.weapon;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.component.CustomData;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;

import static org.junit.jupiter.api.Assertions.*;

class WeaponReadCacheScaleTest {
    private static CompoundTag source() {
        var tag = new CompoundTag();
        tag.putString(WeaponModels.TAG, "austringer");
        tag.putBoolean(WeaponItems.LIVE, true);
        return tag;
    }

    @Test void identityReplacementAndCurrentModelValidationHaveNoTimeBasedStaleness() {
        var tag = source();
        var component = CustomData.of(tag);
        var first = WeaponReadCache.read(component);
        assertSame(first, WeaponReadCache.read(component));
        assertTrue(first.live());
        assertEquals("austringer", first.entry(Identifier.parse("destiny:weapon/austringer")).orElseThrow().id());
        assertTrue(first.entry(Identifier.parse("destiny:weapon/beloved")).isEmpty());
        assertTrue(first.entry(null).isEmpty());
        tag.putBoolean(WeaponItems.LIVE, false);
        tag.putString(WeaponModels.TAG, "beloved");
        assertTrue(first.live(), "Source edits cannot mutate CustomData.of or an immutable projection");
        var replacement = WeaponReadCache.read(CustomData.of(tag));
        assertNotSame(first, replacement);
        assertFalse(replacement.live());
        assertEquals("beloved", replacement.entry(Identifier.parse("destiny:weapon/beloved")).orElseThrow().id());
    }

    @Test void integralAmmoAndSocketTypesPreserveLegacyOverrideRules() {
        var tag = source();
        tag.putByte(WeaponItems.ROUNDS, (byte) 7);
        tag.putShort(WeaponItems.RESERVE, (short) 23);
        tag.putLong(WeaponItems.OVERFLOW, Long.MAX_VALUE);
        tag.putInt(WeaponItems.LOADED_LIMIT, 40);
        tag.putInt(WeaponPerks.SOCKET_KEY, 12);
        tag.putLong(WeaponPerks.HASH_KEY, 1234);
        var legacy = WeaponReadCache.read(CustomData.of(tag));
        assertEquals(7, legacy.rounds());
        assertEquals(23, legacy.reserve());
        assertEquals(Long.MAX_VALUE, legacy.overflow());
        assertEquals(40, legacy.loadedLimit());
        assertEquals(1234, legacy.savedHash(12));
        assertEquals(-1, legacy.savedHash(13));

        var slots = new CompoundTag();
        slots.putLong("13", 5678);
        slots.putString("12", "1234");
        tag.put(WeaponPerks.SLOTS_KEY, slots);
        tag.putDouble(WeaponItems.ROUNDS, Double.NaN);
        tag.putLong(WeaponItems.RESERVE, -1);
        tag.putString(WeaponItems.OVERFLOW, "100");
        var modern = WeaponReadCache.read(CustomData.of(tag));
        assertEquals(0, modern.rounds());
        assertEquals(0, modern.reserve());
        assertEquals(0, modern.overflow());
        assertEquals(-1, modern.savedHash(12), "Malformed explicit modern socket blocks legacy fallback");
        assertEquals(5678, modern.savedHash(13));
        slots.remove("12");
        tag.put(WeaponPerks.SLOTS_KEY, slots);
        assertEquals(1234, WeaponReadCache.read(CustomData.of(tag)).savedHash(12));
        tag.putString(WeaponPerks.SLOTS_KEY, "corrupt");
        assertEquals(-1, WeaponReadCache.read(CustomData.of(tag)).savedHash(12));
        tag.remove(WeaponPerks.SLOTS_KEY);
        tag.putLong(WeaponPerks.SOCKET_KEY, 12);
        assertEquals(-1, WeaponReadCache.read(CustomData.of(tag)).savedHash(12), "Legacy socket remains IntTag-only");
    }

    @Test void threadLocalSnapshotsCannotShareMutableMemoizationAcrossSerializationThreads() {
        var component = CustomData.of(source());
        var local = WeaponReadCache.read(component);
        local.rememberSelected("example", Optional.empty());
        var other = CompletableFuture.supplyAsync(() -> WeaponReadCache.read(component)).join();
        assertNotSame(local, other);
        assertNull(other.selected("example"));
        assertSame(local, WeaponReadCache.read(component));
    }

    @Test void componentPoolAndArbitraryPerkMemoizationAreBoundedAndPoolsCannotBeMutated() {
        var component = CustomData.of(source());
        var old = WeaponReadCache.read(component);
        for (int i = 0; i <= WeaponReadCache.COMPONENT_LIMIT; i++) {
            var tag = source(); tag.putInt("nonce", i);
            WeaponReadCache.read(CustomData.of(tag));
        }
        assertNotSame(old, WeaponReadCache.read(component));
        var entry = WeaponCatalog.find("austringer").orElseThrow();
        var roll = new WeaponPerks.Roll(entry.id(), 1, 12, 2, 3);
        var returned = WeaponReadCache.rememberPool(entry, "sentinel", List.of(roll));
        assertThrows(UnsupportedOperationException.class, () -> returned.add(roll));
        for (int i = 0; i <= WeaponReadCache.POOL_LIMIT; i++)
            WeaponReadCache.rememberPool(entry, "untrusted_" + i, List.of());
        assertNull(WeaponReadCache.pool(entry, "sentinel"));
        var snapshot = WeaponReadCache.read(component);
        snapshot.rememberSelected("sentinel", Optional.of(roll));
        for (int i = 0; i <= WeaponReadCache.SELECTION_LIMIT; i++)
            snapshot.rememberSelected("untrusted_" + i, Optional.empty());
        assertNull(snapshot.selected("sentinel"));
    }
}
