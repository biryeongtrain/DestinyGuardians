package kim.biryeong.destiny.strike.exodus;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.activity.strike.StrikeZone;
import kim.biryeong.destiny.strike.devils.DevilsPlan;
import net.minecraft.core.BlockPos;
import net.minecraft.world.phys.Vec3;

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Exodus Crash's authored progression: twelve beats along one continuous walk from the arrival pad to the boss pad.
 * The table is generated next to the map ({@code scripts/strikes/build_exodus_maps.py}); positions are map-local.
 */
public final class ExodusPlan {
    public static final int MIN_PLAYERS = 1, PLAYERS = 3;
    /** The map is one connected zone: there is nothing to teleport between. */
    public enum Zone implements StrikeZone {
        WORLD("world");
        private final String resourceName;
        Zone(String resourceName) { this.resourceName = resourceName; }
        @Override public String resourceName() { return resourceName; }
    }
    public enum BeatKind { ADVANCE, COMBAT, CHARGE, DEFEND, BOSS }
    public record Wave(DevilsPlan.Kind kind, int count) { }
    public record Beat(String id, BeatKind kind, String title, String shortTitle, Vec3 trigger, List<Wave> waves,
                       int need, int seconds, List<BlockPos> gate, Vec3 generator) {
        public Beat { waves = List.copyOf(waves); gate = List.copyOf(gate); }
        public int enemies() { return waves.stream().mapToInt(Wave::count).sum(); }
    }
    public record Data(List<Beat> beats, List<Vec3> route) { }

    private static volatile Data data;
    private ExodusPlan() { }

    public static Data data() {
        var value = data;
        if (value == null) synchronized (ExodusPlan.class) {
            if (data == null) data = load();
            value = data;
        }
        return value;
    }

    static Data load() {
        try (var in = ExodusPlan.class.getResourceAsStream("/data/destiny/exodus_crash/beats.json")) {
            if (in == null) throw new IOException("Missing exodus_crash/beats.json");
            var root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
            var route = new ArrayList<Vec3>();
            for (var p : root.getAsJsonArray("route")) route.add(vec(p.getAsJsonArray(), 0));
            var beats = new ArrayList<Beat>();
            for (var value : root.getAsJsonArray("beats")) {
                JsonObject b = value.getAsJsonObject();
                var waves = new ArrayList<Wave>();
                if (b.has("waves")) for (var w : b.getAsJsonArray("waves")) {
                    var pair = w.getAsJsonArray();
                    waves.add(new Wave(DevilsPlan.Kind.valueOf(pair.get(0).getAsString().toUpperCase(Locale.ROOT)), pair.get(1).getAsInt()));
                }
                var gate = new ArrayList<BlockPos>();
                if (b.has("gate")) for (var c : b.getAsJsonObject("gate").getAsJsonArray("cells")) {
                    JsonArray a = c.getAsJsonArray();
                    gate.add(new BlockPos(a.get(0).getAsInt(), a.get(1).getAsInt(), a.get(2).getAsInt()));
                }
                beats.add(new Beat(b.get("id").getAsString(), BeatKind.valueOf(b.get("kind").getAsString()),
                        b.get("title").getAsString(), b.get("short").getAsString(), vec(b.getAsJsonArray("trigger"), 0),
                        waves, b.has("need") ? b.get("need").getAsInt() : 0, b.has("seconds") ? b.get("seconds").getAsInt() : 0,
                        gate, b.has("generator") ? vec(b.getAsJsonArray("generator"), 0) : null));
            }
            if (beats.isEmpty() || route.size() < 2) throw new IOException("Empty Exodus plan");
            return new Data(List.copyOf(beats), List.copyOf(route));
        } catch (IOException e) { throw new UncheckedIOException(e); }
    }
    private static Vec3 vec(JsonArray a, int from) {
        return new Vec3(a.get(from).getAsDouble(), a.get(from + 1).getAsDouble(), a.get(from + 2).getAsDouble());
    }
}
