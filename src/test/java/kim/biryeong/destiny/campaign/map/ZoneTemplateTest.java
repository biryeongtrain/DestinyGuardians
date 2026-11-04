package kim.biryeong.destiny.campaign.map;

import kim.biryeong.destiny.campaign.RisingServices;
import org.junit.jupiter.api.Test;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.GZIPOutputStream;

import static org.junit.jupiter.api.Assertions.*;

/** W300 zone template format, bounds, marker grammar and budgeted placement (no Minecraft world needed). */
class ZoneTemplateTest {

    /** Minimal encoder mirroring scripts/campaign/rising_maps.py write_zone(). */
    static byte[] encode(int sx, int sy, int sz, List<String> palette, int[] cells) throws IOException {
        var raw = new ByteArrayOutputStream();
        try (var out = new DataOutputStream(new GZIPOutputStream(raw))) {
            out.write(ZoneTemplate.MAGIC);
            out.writeInt(sx); out.writeInt(sy); out.writeInt(sz);
            out.writeShort(palette.size());
            for (String p : palette) { byte[] b = p.getBytes(StandardCharsets.UTF_8); out.writeShort(b.length); out.write(b); }
            List<int[]> runs = new ArrayList<>();
            for (int i = 0; i < cells.length; ) {
                int j = i; while (j < cells.length && cells[j] == cells[i]) j++;
                runs.add(new int[]{cells[i], j - i}); i = j;
            }
            out.writeInt(runs.size());
            for (int[] r : runs) { varint(out, r[0]); varint(out, r[1]); }
        }
        return raw.toByteArray();
    }

    static void varint(DataOutputStream out, int v) throws IOException {
        while ((v & ~0x7F) != 0) { out.writeByte((v & 0x7F) | 0x80); v >>>= 7; }
        out.writeByte(v);
    }

    static final List<String> PALETTE = List.of("minecraft:air", "minecraft:smooth_stone",
            "minecraft:iron_bars[east=true,north=false,south=false,west=true]", "minecraft:waxed_copper_bulb[lit=false,powered=false]");

    /** 37 x 20 x 33 volume (sections are partial on every axis) with a deterministic pattern. */
    static int[] pattern(int sx, int sy, int sz) {
        int[] c = new int[sx * sy * sz];
        for (int y = 0; y < sy; y++) for (int z = 0; z < sz; z++) for (int x = 0; x < sx; x++) {
            int v = y == 0 ? 1 : ((x * 7 + y * 3 + z * 5) % 11 == 0 ? 2 : 0);
            if (x == 36 && y == 19 && z == 32) v = 3;
            c[(y * sz + z) * sx + x] = v;
        }
        return c;
    }

    @Test void roundTripPreservesEveryCell() throws IOException {
        int sx = 37, sy = 20, sz = 33;
        int[] cells = pattern(sx, sy, sz);
        ZoneTemplate t = ZoneTemplate.decode("test", new ByteArrayInputStream(encode(sx, sy, sz, PALETTE, cells)));
        assertEquals(sx, t.sizeX()); assertEquals(sy, t.sizeY()); assertEquals(sz, t.sizeZ());
        assertEquals(PALETTE, t.palette());
        long blocks = 0;
        for (int y = 0; y < sy; y++) for (int z = 0; z < sz; z++) for (int x = 0; x < sx; x++) {
            int v = cells[(y * sz + z) * sx + x];
            assertEquals(v, t.paletteIndexAt(x, y, z), "cell " + x + "," + y + "," + z);
            if (v != 0) blocks++;
        }
        assertEquals(blocks, t.blockCount());
        assertEquals(0, t.paletteIndexAt(-1, 0, 0));
        assertEquals(0, t.paletteIndexAt(sx, 0, 0));
        // only non-empty sections are stored: y in [0,20) -> 2 section layers, all columns non-empty
        assertTrue(t.sectionCount() <= 3 * 2 * 3);
    }

    @Test void rejectsBadHeaderPaletteAndRuns() throws IOException {
        int[] one = {1};
        assertThrows(IOException.class, () -> ZoneTemplate.decode("x", new ByteArrayInputStream(encode(0, 1, 1, PALETTE, new int[0]))));
        assertThrows(IOException.class, () -> ZoneTemplate.decode("x", new ByteArrayInputStream(encode(1, 999, 1, PALETTE, one))));
        assertThrows(IOException.class, () -> ZoneTemplate.decode("x", new ByteArrayInputStream(
                encode(1, 1, 1, List.of("minecraft:air", "minecraft:command_block"), one))));
        assertThrows(IOException.class, () -> ZoneTemplate.decode("x", new ByteArrayInputStream(
                encode(1, 1, 1, List.of("minecraft:stone", "minecraft:stone"), one))));
        // runs shorter than the volume
        assertThrows(IOException.class, () -> ZoneTemplate.decode("x", new ByteArrayInputStream(encode(2, 1, 1, PALETTE, one))));
        // palette index beyond the palette
        assertThrows(IOException.class, () -> ZoneTemplate.decode("x", new ByteArrayInputStream(encode(1, 1, 1, PALETTE, new int[]{9}))));
        assertThrows(IOException.class, () -> ZoneTemplate.decode("x", new ByteArrayInputStream("garbage".getBytes())));
    }

    @Test void paletteWhitelist() {
        assertTrue(ZonePalette.allowed("minecraft:smooth_stone_slab[type=bottom]"));
        assertTrue(ZonePalette.allowed("minecraft:barrier"));
        assertFalse(ZonePalette.allowed("minecraft:chest"));
        assertFalse(ZonePalette.allowed("minecraft:stone[foo=bar"));
        assertFalse(ZonePalette.allowed("other:stone"));
    }

    /** In-memory target; chunks become "loaded" one ensureLoaded call after being requested. */
    static final class MemoryTarget implements ZoneTemplate.Target {
        final Map<Long, Integer> placed = new HashMap<>();
        final Set<Long> requested = new HashSet<>();
        int duplicates, columns;
        boolean closed;
        @Override public boolean ensureLoaded(int minX, int minZ, int maxX, int maxZ) {
            long key = ((long) (minX >> 4) << 32) | (minZ >> 4 & 0xffffffffL);
            return !requested.add(key);
        }
        @Override public void set(int x, int y, int z, int paletteIndex) {
            if (placed.put(((long) x << 40) | ((long) y << 20) | z, paletteIndex) != null) duplicates++;
        }
        @Override public void columnDone(int minX, int minZ, int maxX, int maxZ) { columns++; }
        boolean prefetching = true;
        @Override public void prefetch(int minX, int minZ, int maxX, int maxZ) {
            if (prefetching) requested.add(((long) (minX >> 4) << 32) | (minZ >> 4 & 0xffffffffL));
        }
        @Override public void close() { closed = true; }
    }

    @Test void upcomingColumnsArePrefetchedSoLargeBudgetsDoNotStallPerColumn() throws IOException {
        int sx = 160, sy = 20, sz = 160; // 100 columns, more than one prefetch window
        int[] cells = pattern(sx, sy, sz);
        ZoneTemplate t = ZoneTemplate.decode("test", new ByteArrayInputStream(encode(sx, sy, sz, PALETTE, cells)));
        int[] stalls = new int[2];
        for (int k = 0; k < 2; k++) {
            var target = new MemoryTarget();
            target.prefetching = k == 0;
            var build = t.begin(target);
            while (!build.step(Long.MAX_VALUE / 4)) assertTrue(++stalls[k] < 10_000);
            assertEquals(t.blockCount(), target.placed.size());
        }
        assertTrue(stalls[0] <= 4, "prefetched build stalls only on window refills: " + stalls[0]);
        assertTrue(stalls[1] >= 100, "without prefetch every column stalls: " + stalls[1]);
    }

    @Test void budgetedStepTerminatesAndPlacesEachBlockOnce() throws IOException {
        int sx = 37, sy = 20, sz = 33;
        int[] cells = pattern(sx, sy, sz);
        ZoneTemplate t = ZoneTemplate.decode("test", new ByteArrayInputStream(encode(sx, sy, sz, PALETTE, cells)));
        var target = new MemoryTarget();
        var build = t.begin(target);
        int steps = 0;
        double last = -1;
        while (!build.step(0)) {
            assertTrue(build.progress() >= last, "progress is monotonic");
            last = build.progress();
            assertTrue(++steps < 100_000, "zero-budget steps must still make progress");
        }
        assertTrue(build.step(0), "finished builds stay finished");
        assertEquals(1.0, build.progress());
        assertEquals(t.blockCount(), target.placed.size());
        assertEquals(0, target.duplicates);
        assertTrue(target.closed);
        assertEquals(9, target.columns); // 3 x 3 section columns
        for (var e : target.placed.entrySet()) {
            long k = e.getKey();
            int x = (int) (k >>> 40), y = (int) ((k >>> 20) & 0xFFFFF), z = (int) (k & 0xFFFFF);
            assertEquals(cells[(y * sz + z) * sx + x], e.getValue());
        }
        // a large budget finishes in one call once chunks are loaded
        var target2 = new MemoryTarget();
        var b2 = t.begin(target2);
        int calls = 0;
        while (!b2.step(5_000_000_000L)) calls++;
        assertTrue(calls <= 9, "only chunk-load waits interrupt an unbounded step");
    }

    @Test void cancelIsIdempotentAndStops() throws IOException {
        int[] cells = pattern(37, 20, 33);
        ZoneTemplate t = ZoneTemplate.decode("test", new ByteArrayInputStream(encode(37, 20, 33, PALETTE, cells)));
        var target = new MemoryTarget();
        var build = t.begin(target);
        build.step(0); build.step(0);
        int before = target.placed.size();
        build.cancel(); build.cancel();
        assertTrue(target.closed);
        assertTrue(build.step(Long.MAX_VALUE));
        assertEquals(before, target.placed.size());
        assertTrue(build.progress() < 1.0);
    }

    @Test void markerGrammarAndValidation() throws IOException {
        String ok = """
            {"schema":1,"zones":{%s}}""";
        StringBuilder zones = new StringBuilder();
        for (var z : RisingServices.Zone.values()) {
            if (zones.length() > 0) zones.append(',');
            zones.append('"').append(ZoneTemplate.resourceName(z)).append("\":{\"size\":[10,10,10],\"markers\":[")
                    .append("{\"id\":\"spawn.player\",\"pos\":[1.5,2,3.5],\"yaw\":-90},")
                    .append("{\"id\":\"enemy.first.0\",\"pos\":[2.5,2,3.5],\"yaw\":0,\"tags\":{\"kind\":\"dreg\",\"order\":\"1\"}},")
                    .append("{\"id\":\"trigger.rifle\",\"pos\":[2.5,2,3.5],\"yaw\":0,\"tags\":{\"radius\":\"2.5\"}}]}");
        }
        var parsed = RisingZones.parse(new StringReader(ok.formatted(zones)));
        var gw = parsed.get(RisingServices.Zone.GATEWAY);
        assertEquals(3, gw.markers().size());
        assertEquals("dreg", gw.markers().get(1).tags().get("kind"));
        assertEquals(-90f, gw.markers().get(0).yaw());

        for (String bad : List.of(
                "{\"id\":\"Enemy.first.0\",\"pos\":[1,1,1],\"yaw\":0,\"tags\":{\"kind\":\"dreg\"}}",
                "{\"id\":\"enemy.first.0\",\"pos\":[1,1,1],\"yaw\":0,\"tags\":{\"kind\":\"tank\"}}",
                "{\"id\":\"enemy.first\",\"pos\":[1,1,1],\"yaw\":0,\"tags\":{\"kind\":\"dreg\"}}",
                "{\"id\":\"spawn.player\",\"pos\":[50,1,1],\"yaw\":0}")) {
            String json = ok.formatted(zones.toString().replace(
                    "{\"id\":\"trigger.rifle\",\"pos\":[2.5,2,3.5],\"yaw\":0,\"tags\":{\"radius\":\"2.5\"}}", bad));
            assertThrows(IOException.class, () -> RisingZones.parse(new StringReader(json)), bad);
        }
    }

    /** Bundled data: every zone decodes under the whitelist and every marker lies inside its zone. */
    @Test void bundledZonesAndMarkersAreConsistent() throws IOException {
        Map<RisingServices.Zone, RisingZones.LocalZone> markers;
        try (var in = getClass().getResourceAsStream(RisingZones.MARKERS_RESOURCE)) {
            assertNotNull(in, "markers.json bundled");
            markers = RisingZones.parse(new InputStreamReader(in, StandardCharsets.UTF_8));
        }
        long total = 0;
        for (var zone : RisingServices.Zone.values()) {
            String path = ZoneTemplate.RESOURCE_DIR + ZoneTemplate.resourceName(zone) + ".zone";
            ZoneTemplate t;
            try (var in = getClass().getResourceAsStream(path)) {
                assertNotNull(in, path);
                t = ZoneTemplate.decode(zone.name(), in);
            }
            total += t.blockCount();
            var local = markers.get(zone);
            assertEquals(t.sizeX(), local.sizeX()); assertEquals(t.sizeY(), local.sizeY()); assertEquals(t.sizeZ(), local.sizeZ());
            var ids = local.markers().stream().map(RisingServices.Marker::id).toList();
            assertTrue(ids.contains("spawn.player"), zone + " spawn");
            for (var m : local.markers()) {
                if (m.tags().containsKey("free") || m.id().startsWith("prop.") || m.id().startsWith("ghost.")) continue;
                int x = (int) Math.floor(m.pos().x), y = (int) Math.floor(m.pos().y), z = (int) Math.floor(m.pos().z);
                if (m.id().startsWith("light.")) {
                    // ceiling bulbs are always present (lit or unlit); floor lanterns only when lit from the start
                    if (m.tags().get("mount").equals("ceiling") || m.tags().get("phase").equals("always"))
                        assertTrue(t.palette().get(t.paletteIndexAt(x, y, z)).startsWith(
                                ZonePalette.blockId(m.tags().get("block"))), zone + " " + m.id() + " fixture present");
                    continue;
                }
                // feet cell and head cell free, support below (standable)
                assertTrue(passable(t, x, y, z) && passable(t, x, y + 1, z), zone + " " + m.id() + " has headroom");
                assertFalse(passable(t, x, y - 1, z), zone + " " + m.id() + " stands on a block");
            }
        }
        assertTrue(total > 0);
    }

    /** Bundled guidance routes: every zone present, waypoints on walkable floor inside the zone, 3-6 blocks apart. */
    @Test void bundledRoutesAreWalkable() throws IOException {
        com.google.gson.JsonObject zones;
        try (var in = getClass().getResourceAsStream(ZoneTemplate.RESOURCE_DIR + "routes.json")) {
            assertNotNull(in, "routes.json bundled");
            zones = com.google.gson.JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8))
                    .getAsJsonObject().getAsJsonObject("zones");
        }
        for (var zone : RisingServices.Zone.values()) {
            ZoneTemplate t;
            try (var in = getClass().getResourceAsStream(ZoneTemplate.RESOURCE_DIR + ZoneTemplate.resourceName(zone) + ".zone")) {
                t = ZoneTemplate.decode(zone.name(), in);
            }
            var pts = zones.getAsJsonArray(ZoneTemplate.resourceName(zone));
            assertNotNull(pts, zone + " route");
            assertTrue(pts.size() >= 2);
            double[] prev = null;
            for (var e : pts) {
                var a = e.getAsJsonArray();
                assertEquals(4, a.size());
                double x = a.get(0).getAsDouble(), y = a.get(1).getAsDouble(), z = a.get(2).getAsDouble();
                int j = a.get(3).getAsInt();
                assertTrue(j == 0 || j == 1);
                int bx = (int) Math.floor(x), by = (int) Math.ceil(y), bz = (int) Math.floor(z);
                assertTrue(passable(t, bx, by, bz) && passable(t, bx, by + 1, bz), zone + " waypoint free " + x + "," + y + "," + z);
                assertFalse(passable(t, bx, by - 1, bz), zone + " waypoint on floor " + x + "," + y + "," + z);
                if (prev != null) {
                    double d = Math.hypot(x - prev[0], z - prev[1]);
                    assertTrue(d >= 2.99 && d <= 6.01, zone + " spacing " + d);
                }
                prev = new double[]{x, z};
            }
            // The route must end inside its final objective, using the director's trigger test
            // (horizontal radius, vertical height; RisingMission.near).
            String last = Map.of(RisingServices.Zone.GATEWAY, "exit.breach", RisingServices.Zone.BREACH, "exit.divide",
                    RisingServices.Zone.DIVIDE, "exit.dock13", RisingServices.Zone.DOCK13, "trigger.ship").get(zone);
            var m = markers().get(zone).markers().stream().filter(k -> k.id().equals(last)).findFirst().orElseThrow();
            var end = pts.get(pts.size() - 1).getAsJsonArray();
            double r = Double.parseDouble(m.tags().get("radius"));
            double h = Double.parseDouble(m.tags().getOrDefault("height", String.valueOf(Math.max(3, r))));
            double dx = end.get(0).getAsDouble() - m.pos().x, dz = end.get(2).getAsDouble() - m.pos().z;
            assertTrue(dx * dx + dz * dz <= r * r && Math.abs(end.get(1).getAsDouble() - m.pos().y) <= h,
                    zone + " route ends inside " + last);
        }
    }

    private static Map<RisingServices.Zone, RisingZones.LocalZone> markers() throws IOException {
        try (var in = ZoneTemplateTest.class.getResourceAsStream(RisingZones.MARKERS_RESOURCE)) {
            return RisingZones.parse(new InputStreamReader(in, StandardCharsets.UTF_8));
        }
    }

    private static boolean passable(ZoneTemplate t, int x, int y, int z) {
        String s = t.palette().get(t.paletteIndexAt(x, y, z));
        return s.equals("minecraft:air") || s.equals("minecraft:light") || s.startsWith("minecraft:light[");
    }
}
