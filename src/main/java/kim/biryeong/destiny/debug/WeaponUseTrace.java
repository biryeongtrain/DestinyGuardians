package kim.biryeong.destiny.debug;

import com.google.gson.JsonObject;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.weapon.WeaponModels;
import kim.biryeong.destiny.weapon.WeaponProfile;
import net.minecraft.server.level.ServerPlayer;

/** Bounded, explicitly selected QA observer. Never changes use state or sends packets. */
public final class WeaponUseTrace {
    private static final boolean ENABLED = Boolean.getBoolean("destiny.weapon.useTrace");
    private static final String PLAYER = System.getProperty("destiny.weapon.useTrace.player", "");
    private static final TraceLimit LIMIT = new TraceLimit(4096);

    private WeaponUseTrace() {}

    public static boolean selected(ServerPlayer player) {
        return ENABLED && !PLAYER.isEmpty() && player != null
                && PLAYER.equals(player.getGameProfile().name());
    }

    /** The caller supplies an existing runtime view; no binding or gameplay queries occur here. */
    public static void record(ServerPlayer player, String event, int sequence,
                              boolean bound, boolean holding, long heldUntil, double firingDeadline) {
        if (!selected(player) || !LIMIT.take()) return;
        var held = player.getMainHandItem();
        var entry = WeaponItems.entry(held);
        var out = new JsonObject();
        out.addProperty("event", event);
        out.addProperty("index", LIMIT.count());
        out.addProperty("wallMs", System.currentTimeMillis());
        out.addProperty("nanoTime", System.nanoTime());
        out.addProperty("serverTick", player.level().getServer().getTickCount());
        out.addProperty("sequence", sequence);
        out.addProperty("usingItem", player.isUsingItem());
        out.addProperty("useMatchesHeld", player.getUseItem() == held);
        out.addProperty("heldIdentity", System.identityHashCode(held));
        out.addProperty("weapon", entry.map(e -> e.id()).orElse("none"));
        out.addProperty("twoHanded", WeaponModels.twoHanded(held));
        out.addProperty("rounds", entry.map(e -> WeaponItems.magazine(held, WeaponProfile.forEntry(e)).rounds()).orElse(-1));
        out.addProperty("runtimeBound", bound);
        out.addProperty("holding", holding);
        out.addProperty("heldUntil", heldUntil);
        out.addProperty("firingDeadline", firingDeadline);
        DestinyGuardians.LOGGER.info("[W107 use trace] {}", out);
    }

    /** No unbounded map, queue, clock mutation, thread or log payload storage. */
    public static final class TraceLimit {
        private final int maximum;
        private int count;
        public TraceLimit(int maximum) {
            if (maximum < 1 || maximum > 4096) throw new IllegalArgumentException("trace maximum");
            this.maximum = maximum;
        }
        public synchronized boolean take() {
            if (count >= maximum) return false;
            count++;
            return true;
        }
        public synchronized int count() { return count; }
    }
}
