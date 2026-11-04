package kim.biryeong.destiny.campaign.fallen;

import kim.biryeong.destiny.campaign.RisingEncounters;
import kim.biryeong.destiny.campaign.RisingServices.Marker;
import kim.biryeong.destiny.campaign.RisingServices.Zone;
import kim.biryeong.destiny.campaign.map.ZoneTemplate;
import kim.biryeong.destiny.campaign.fallen.SkiffDrop.Choice;
import kim.biryeong.destiny.campaign.fallen.SkiffDrop.Sky;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.file.*;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Offline W300 r8 scan: runs the Skiff decision (Choice + Sky.find) on the bundled zone templates and markers, through
 * the map lane's loaders, and writes {@code build/skiff-zone-scan.md}. Collision is approximated from palette names.
 */
class SkiffZoneScanTest {
    /** Blocks without a collision box (palette name prefix before '['). Everything else counts as solid. */
    static final Set<String> PASSABLE = Set.of("minecraft:air", "minecraft:cave_air", "minecraft:void_air", "minecraft:light",
            "minecraft:water", "minecraft:lava", "minecraft:short_grass", "minecraft:tall_grass", "minecraft:fern",
            "minecraft:large_fern", "minecraft:dead_bush", "minecraft:vine", "minecraft:torch", "minecraft:wall_torch",
            "minecraft:redstone_torch", "minecraft:redstone_wall_torch", "minecraft:cobweb", "minecraft:rail",
            "minecraft:snow", "minecraft:glow_lichen", "minecraft:sculk_vein", "minecraft:hanging_roots", "minecraft:moss_carpet");

    static final class TemplateGrid implements Sky.Grid {
        final ZoneTemplate t;
        final boolean[] solidPal;
        final Map<Long, Integer> tops = new HashMap<>();
        long lookups;
        TemplateGrid(ZoneTemplate t) {
            this.t = t;
            solidPal = new boolean[t.palette().size()];
            for (int i = 0; i < solidPal.length; i++) solidPal[i] = !PASSABLE.contains(t.palette().get(i).replaceAll("\\[.*", ""));
        }
        @Override public boolean solid(int x, int y, int z) { lookups++; return solidPal[t.paletteIndexAt(x, y, z)]; }
        /** Outside the template the instance world is empty: open sky above the template top and beyond its edges. */
        @Override public boolean sky(int x, int y, int z) { return y > top(x, z); }
        int top(int x, int z) {
            return tops.computeIfAbsent(((long) x << 32) ^ (z & 0xffffffffL), k -> {
                for (int y = t.sizeY() - 1; y >= 0; y--) if (solidPal[t.paletteIndexAt(x, y, z)]) return y;
                return -1;
            });
        }
    }

    @SuppressWarnings("unchecked")
    static Map<Zone, List<Marker>> markers() throws Exception {
        var cls = Class.forName("kim.biryeong.destiny.campaign.map.RisingZones");
        var m = cls.getDeclaredMethod("localMarkers");
        m.setAccessible(true);
        var zones = (Map<Zone, ?>) m.invoke(null);
        var out = new EnumMap<Zone, List<Marker>>(Zone.class);
        for (var e : zones.entrySet()) {
            var acc = e.getValue().getClass().getDeclaredMethod("markers");
            acc.setAccessible(true);
            out.put(e.getKey(), (List<Marker>) acc.invoke(e.getValue()));
        }
        return out;
    }

    record Row(Zone zone, int index, String encounter, int size, boolean eligible, int riders, Vec3 ground,
               boolean skyAbove, Optional<Sky.Spot> spot) { }

    static final Map<String, Long> lookups = new LinkedHashMap<>();

    static List<Row> scan() throws Exception {
        var rows = new ArrayList<Row>();
        var all = markers();
        for (Zone zone : Zone.values()) {
            var ms = all.get(zone).stream().filter(m -> m.id().startsWith("enemy.")).toList();
            var plan = RisingEncounters.plan(ms);
            if (plan.empty()) continue;
            var grid = new TemplateGrid(ZoneTemplate.get(zone));
            for (int i = 0; i < plan.waves().size(); i++) {
                var wave = plan.waves().get(i);
                boolean ok = Choice.skiffWave(zone, i, wave);
                var riders = Choice.dropped(wave);
                Vec3 ground = riders.isEmpty() ? wave.get(0).pos() : Choice.centroid(riders);
                int gx = (int) Math.floor(ground.x), gz = (int) Math.floor(ground.z), gy = (int) Math.floor(ground.y);
                boolean skyAbove = grid.sky(gx, gy + 1, gz);
                String encounter = wave.get(0).encounter();
                Vec3 hint = all.get(zone).stream().filter(m -> m.id().equals(SkiffDrop.hintMarker(encounter))).map(Marker::pos).findFirst().orElse(null);
                var units = Choice.ground(wave, riders).stream().map(RisingEncounters.Slot::pos).toList();
                grid.lookups = 0;
                var spot = ok ? Sky.find(grid, units, ground, hint) : Optional.<Sky.Spot>empty();
                lookups.put(zone + "/" + i, ok ? (long) Sky.lastReads() : 0L);
                rows.add(new Row(zone, i, encounter, wave.size(), ok, riders.size(), ground, skyAbove, spot));
            }
        }
        return rows;
    }

    static String f(Vec3 v) { return String.format(Locale.ROOT, "%.1f, %.1f, %.1f", v.x, v.y, v.z); }

    @Test void bundledZonesGiveBreachAndDockASkiff() throws Exception {
        var rows = scan();
        var md = new StringBuilder("| zone | wave | encounter | size | eligible | riders | drop centroid (zone-local) | sky directly above | result | hover (zone-local) | offset m | seen by | unique block reads |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|\n");
        for (var r : rows)
            md.append(String.format(Locale.ROOT, "| %s | %d | %s | %d | %s | %d | %s | %s | %s | %s | %s | %s | %d |%n", r.zone(), r.index(), r.encounter(), r.size(),
                    r.eligible(), r.riders(), f(r.ground()), r.skyAbove() ? "open" : "roofed",
                    !r.eligible() ? "-" : r.spot().map(s -> s.kind().toString()).orElse("SKIP (no visible sky in 40 m / budget)"),
                    r.spot().map(s -> f(s.hover())).orElse("-"), r.spot().map(s -> String.format(Locale.ROOT, "%.1f", s.offset())).orElse("-"),
                    r.spot().map(s -> String.valueOf(s.seenBy())).orElse("-"), lookups.getOrDefault(r.zone() + "/" + r.index(), 0L)));
        Path out = Path.of("build", "skiff-zone-scan.md");
        Files.createDirectories(out.getParent());
        Files.writeString(out, md);
        System.out.println(md);
        var breach = rows.stream().filter(r -> r.zone() == Zone.BREACH && r.spot().isPresent()).toList();
        var dock = rows.stream().filter(r -> r.zone() == Zone.DOCK13 && r.spot().isPresent()).toList();
        var divide = rows.stream().filter(r -> r.zone() == Zone.DIVIDE && r.encounter().equals("divide_reinforce")).findFirst();
        assertFalse(breach.isEmpty(), "at least one Breach reinforcement gets a Skiff");
        assertFalse(dock.isEmpty(), "the Dock 13 defence wave gets a Skiff");
        assertTrue(divide.isPresent() && divide.get().spot().isPresent(), "Divide (graveyard) reinforcements get a Skiff");
        assertTrue(rows.stream().noneMatch(r -> r.zone() == Zone.GATEWAY && r.eligible()));
    }

    /** Zone-local eye positions of a player standing on the Dock 13 floor (QA spot by the ship; spawn by the gate). */
    static final Vec3 DOCK_SHIP_EYE = new Vec3(184.5, 46 + 1.62, 211.5), DOCK_SPAWN_EYE = new Vec3(215.5, 45 + 1.62, 185.5);

    @Test void dockReinforcementSkiffsAreVisibleFromTheDock() throws Exception {
        var all = markers();
        var plan = RisingEncounters.plan(all.get(Zone.DOCK13).stream().filter(m -> m.id().startsWith("enemy.")).toList());
        var grid = new TemplateGrid(ZoneTemplate.get(Zone.DOCK13));
        var md = new StringBuilder("| wave | encounter | viewer | hint | old rule (hint as-is) hull fits | result | hover | yaw | viewer sees | seen by riders | reads |\n|---|---|---|---|---|---|---|---|---|---|---|\n");
        int visible = 0, reinforcements = 0;
        for (int i = 0; i < plan.waves().size(); i++) {
            var wave = plan.waves().get(i);
            if (!Choice.skiffWave(Zone.DOCK13, i, wave)) continue;
            reinforcements++;
            String encounter = wave.get(0).encounter();
            var riders = Choice.dropped(wave);
            Vec3 ground = Choice.centroid(riders);
            var units = Choice.ground(wave, riders).stream().map(RisingEncounters.Slot::pos).toList();
            Vec3 hint = all.get(Zone.DOCK13).stream().filter(m -> m.id().equals(SkiffDrop.hintMarker(encounter))).map(Marker::pos).findFirst().orElse(null);
            boolean anyViewer = false;
            for (var v : List.of(DOCK_SHIP_EYE, DOCK_SPAWN_EYE)) {
                float yaw = Choice.approachYaw(ground, v);
                String old = "-";
                if (hint != null) {
                    var hv = new Vec3(Math.floor(hint.x) + .5, Math.floor(hint.y), Math.floor(hint.z) + .5);
                    old = Sky.hullFits(grid, hv, Choice.approachYaw(hv, v)) + ", viewer sees " + Sky.viewerSees(grid, v, hv);
                }
                var spot = Sky.find(grid, units, ground, hint, yaw, v);
                anyViewer |= spot.map(Sky.Spot::viewerSees).orElse(false);
                md.append(String.format(Locale.ROOT, "| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d |%n", i, encounter,
                        v == DOCK_SHIP_EYE ? "ship bay (184.5,46,211.5)" : "spawn (215.5,45,185.5)", hint == null ? "-" : f(hint), old,
                        spot.map(x -> x.kind().toString()).orElse("SKIP"), spot.map(x -> f(x.hover())).orElse("-"),
                        spot.map(x -> String.valueOf(Math.round(x.yaw()))).orElse("-"), spot.map(x -> String.valueOf(x.viewerSees())).orElse("-"),
                        spot.map(x -> String.valueOf(x.seenBy())).orElse("-"), Sky.lastReads()));
                assertTrue(spot.isPresent(), "dock wave " + i + " always gets a Skiff");
                assertTrue(spot.get().seenBy() > 0);
                assertTrue(Sky.hullFits(grid, spot.get().hover(), spot.get().yaw()), "whole hull clear of the roof");
            }
            if (anyViewer) visible++;
        }
        Path out = Path.of("build", "skiff-dock-scan.md");
        Files.createDirectories(out.getParent());
        Files.writeString(out, md);
        System.out.println(md);
        assertTrue(reinforcements >= 1);
        assertEquals(reinforcements, visible, "every Dock 13 reinforcement Skiff is in view of a player on the dock floor");
    }
}
