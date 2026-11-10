package kim.biryeong.destiny.weapon;

import net.minecraft.nbt.*;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.component.CustomData;

import java.util.*;

/** Bounded, thread-confined projections of immutable CUSTOM_DATA components; never owns stacks or players. */
final class WeaponReadCache {
    static final int COMPONENT_LIMIT = 256;
    static final int POOL_LIMIT = 2048;
    static final int SELECTION_LIMIT = 256;
    private static final String[] SOCKET_KEYS = new String[64];
    static {
        for (int socket = 0; socket < SOCKET_KEYS.length; socket++) SOCKET_KEYS[socket] = Integer.toString(socket);
    }
    private static final ThreadLocal<Cache> LOCAL = ThreadLocal.withInitial(Cache::new);

    private WeaponReadCache() { }

    private static final class Cache {
        final IdentityHashMap<CustomData, Snapshot> components = new IdentityHashMap<>();
        final Map<PoolKey, List<WeaponPerks.Roll>> pools = new HashMap<>();
    }
    private record PoolKey(WeaponCatalog.Entry entry, String perk) { }

    static Snapshot read(CustomData component) {
        var cache = LOCAL.get().components;
        var result = cache.get(component);
        if (result != null) return result;
        result = new Snapshot(component.copyTag());
        if (cache.size() >= COMPONENT_LIMIT) cache.clear();
        cache.put(component, result);
        return result;
    }

    static List<WeaponPerks.Roll> pool(WeaponCatalog.Entry entry, String perk) {
        return LOCAL.get().pools.get(new PoolKey(entry, perk));
    }

    static List<WeaponPerks.Roll> rememberPool(WeaponCatalog.Entry entry, String perk, List<WeaponPerks.Roll> rolls) {
        // Resolve profile classes before insertion: class initialization can recursively inspect another pool.
        var immutable = List.copyOf(rolls);
        var cache = LOCAL.get().pools;
        if (cache.size() >= POOL_LIMIT) cache.clear();
        cache.put(new PoolKey(entry, perk), immutable);
        return immutable;
    }

    static final class Snapshot {
        private final Optional<WeaponCatalog.Entry> entry;
        private final Identifier model;
        private final boolean live, twoHanded, malformedSockets;
        private final long rounds, reserve, overflow, loadedLimit, legacyHash;
        private final int legacySocket;
        private final Map<Integer, Long> sockets;
        private final Map<String, Optional<WeaponPerks.Roll>> selections = new HashMap<>();

        private Snapshot(CompoundTag tag) {
            entry = tag.getString(WeaponModels.TAG).flatMap(WeaponCatalog::find);
            model = entry.map(e -> Identifier.parse(e.item_model())).orElse(null);
            live = tag.getBooleanOr(WeaponItems.LIVE, false);
            twoHanded = tag.getString(WeaponModels.GRIP_TAG).filter(WeaponModels.Grip.TWO_HAND.name()::equals).isPresent();
            rounds = count(tag, WeaponItems.ROUNDS);
            reserve = count(tag, WeaponItems.RESERVE);
            overflow = count(tag, WeaponItems.OVERFLOW);
            loadedLimit = count(tag, WeaponItems.LOADED_LIMIT);
            legacySocket = tag.get(WeaponPerks.SOCKET_KEY) instanceof IntTag index ? index.intValue() : -1;
            legacyHash = tag.get(WeaponPerks.HASH_KEY) instanceof LongTag hash ? hash.longValue() : -1;
            var modern = tag.get(WeaponPerks.SLOTS_KEY);
            malformedSockets = modern != null && !(modern instanceof CompoundTag);
            var selected = new HashMap<Integer, Long>();
            if (modern instanceof CompoundTag slots) {
                // All supported pool sockets are in [0,63]; preserve invalid-value override of legacy data.
                for (int socket = 0; socket < 64; socket++) {
                    var value = slots.get(SOCKET_KEYS[socket]);
                    if (value != null) selected.put(socket, value instanceof LongTag hash ? hash.longValue() : -1L);
                }
            }
            sockets = Map.copyOf(selected);
        }

        Optional<WeaponCatalog.Entry> entry(Identifier currentModel) {
            return model != null && model.equals(currentModel) ? entry : Optional.empty();
        }
        boolean live() { return live; }
        boolean twoHanded() { return twoHanded; }
        long rounds() { return rounds; }
        long reserve() { return reserve; }
        long overflow() { return overflow; }
        long loadedLimit() { return loadedLimit; }
        long savedHash(int socket) {
            if (malformedSockets) return -1;
            return sockets.getOrDefault(socket, legacySocket == socket ? legacyHash : -1);
        }
        Optional<WeaponPerks.Roll> selected(String id) { return selections.get(id); }
        Optional<WeaponPerks.Roll> rememberSelected(String id, Optional<WeaponPerks.Roll> selected) {
            if (selections.size() >= SELECTION_LIMIT) selections.clear();
            selections.put(id, selected);
            return selected;
        }
    }

    private static long count(CompoundTag tag, String key) {
        return switch (tag.get(key)) {
            case ByteTag value -> Math.max(0, value.longValue());
            case ShortTag value -> Math.max(0, value.longValue());
            case IntTag value -> Math.max(0, value.longValue());
            case LongTag value -> Math.max(0, value.longValue());
            case null, default -> 0;
        };
    }
}
