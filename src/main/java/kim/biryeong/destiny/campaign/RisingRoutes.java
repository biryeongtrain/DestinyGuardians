package kim.biryeong.destiny.campaign;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.activity.presentation.GuideRoute;
import kim.biryeong.destiny.campaign.RisingServices.Zone;
import net.minecraft.world.phys.Vec3;

import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * Walkable guide routes per zone ({@code data/destiny/guardian_rises/zones/routes.json}, produced by the map
 * lane: zone-local feet positions on the floor surface, a {@code jump} flag where the floor rises before the
 * next point). Pure: parsing, origin offset, nearest-waypoint and trail-section selection are unit tested;
 * route math and drawing live in {@link GuideRoute} / GuideTrail. A missing or broken file yields no routes (straight fallback).
 */
public final class RisingRoutes {
    public static final String RESOURCE = "/data/destiny/guardian_rises/zones/routes.json";
    private static volatile Map<Zone, GuideRoute> bundled;

    private RisingRoutes() { }

    /** Zone-local routes from the mod jar, parsed once. Empty when the resource is missing or invalid. */
    public static Map<Zone, GuideRoute> bundled() {
        var cached = bundled;
        if (cached != null) return cached;
        Map<Zone, GuideRoute> result = Map.of();
        try (var in = RisingRoutes.class.getResourceAsStream(RESOURCE)) {
            if (in != null) result = parse(new InputStreamReader(in, StandardCharsets.UTF_8));
        } catch (Exception e) {
            org.slf4j.LoggerFactory.getLogger("destiny").warn("[GuardianRises] routes.json unreadable, using straight guide trail", e);
        }
        bundled = result;
        return result;
    }

    /** World-space route of a zone placed at {@code origin}. */
    public static Optional<GuideRoute> world(Zone zone, Vec3 origin) {
        var local = bundled().get(zone);
        return local == null || !local.usable() ? Optional.empty() : Optional.of(local.offset(origin));
    }

    public static Map<Zone, GuideRoute> parse(Reader reader) {
        JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
        var zones = root.getAsJsonObject("zones");
        var out = new EnumMap<Zone, GuideRoute>(Zone.class);
        if (zones == null) return out;
        for (Zone zone : Zone.values()) {
            var raw = zones.get(zone.name().toLowerCase(Locale.ROOT));
            if (raw == null) continue;
            var points = new ArrayList<GuideRoute.Point>();
            if (raw.isJsonArray()) {
                // compact map export: [[x, y, z, jump], ...]
                for (var element : raw.getAsJsonArray()) {
                    if (!element.isJsonArray() || element.getAsJsonArray().size() < 3) continue;
                    var a = element.getAsJsonArray();
                    try {
                        double x = a.get(0).getAsDouble(), y = a.get(1).getAsDouble(), z = a.get(2).getAsDouble();
                        if (!Double.isFinite(x) || !Double.isFinite(y) || !Double.isFinite(z)) continue;
                        boolean jump = a.size() > 3 && a.get(3).getAsDouble() != 0;
                        points.add(new GuideRoute.Point(new Vec3(x, y, z), jump, null));
                    } catch (RuntimeException e) { /* skip malformed point */ }
                }
                if (points.size() >= 2) out.put(zone, new GuideRoute(points));
                continue;
            }
            if (!raw.isJsonObject() || !raw.getAsJsonObject().has("waypoints")) continue;
            var entry = raw.getAsJsonObject();
            for (var element : entry.getAsJsonArray("waypoints")) {
                var w = element.getAsJsonObject();
                var pos = w.getAsJsonArray("pos");
                if (pos == null || pos.size() != 3) continue;
                double x, y, z;
                try { x = pos.get(0).getAsDouble(); y = pos.get(1).getAsDouble(); z = pos.get(2).getAsDouble(); }
                catch (RuntimeException e) { continue; } // malformed point: skip it, keep the rest of the route
                if (!Double.isFinite(x) || !Double.isFinite(y) || !Double.isFinite(z)) continue;
                boolean jump = w.has("jump") && w.get("jump").getAsBoolean();
                String objective = w.has("objective") ? w.get("objective").getAsString() : null;
                points.add(new GuideRoute.Point(new Vec3(x, y, z), jump, objective));
            }
            if (points.size() >= 2) out.put(zone, new GuideRoute(points));
        }
        return Collections.unmodifiableMap(out);
    }
}
