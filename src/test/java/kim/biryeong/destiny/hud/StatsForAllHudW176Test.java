package kim.biryeong.destiny.hud;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import javax.xml.parsers.DocumentBuilderFactory;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.EnumSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import static kim.biryeong.destiny.hud.WeaponPerkRows.Kind.*;
import static org.junit.jupiter.api.Assertions.*;

/** Bounded standalone W176 projection and asset tests; native runtime integration belongs to master. */
class StatsForAllHudW176Test {
    private static final String NAME = "perk_stats_for_all_w176";
    private static final Path ASSETS = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/hud/w176");
    private static final Path TEXTURE = ASSETS.resolve("textures/item/hud/" + NAME + ".png");
    private static final Path MODEL = ASSETS.resolve("models/gui/hud/" + NAME + ".json");
    private static final Path ITEM = ASSETS.resolve("items/gui/hud/" + NAME + ".json");
    private static final List<WeaponPerkRows.Kind> PREFIX = List.of(
            MEMENTO_MORI, HONED_EDGE, KILL_CLIP, MULTIKILL_CLIP, RAMPAGE, ONE_FOR_ALL,
            SURROUNDED, SWASHBUCKLER, OUTLAW, ARCHERS_TEMPO, NO_DISTRACTIONS,
            RAPID_HIT, FEEDING_FRENZY, PERPETUAL_MOTION, TAP_THE_TRIGGER, FRENZY, ADRENALINE_JUNKIE, FOCUSED_FURY);

    private static WeaponPerkRows.Snapshot snapshot(Set<WeaponPerkRows.Kind> active, int ticks) {
        // Actual canonical 25-argument source call; earlier fields retain their original order.
        return new WeaponPerkRows.Snapshot(
                active.contains(KILL_CLIP) ? 99 : 0, active.contains(OUTLAW) ? 87 : 0,
                active.contains(RAMPAGE) ? 3 : 0, active.contains(RAMPAGE) ? 61 : 0,
                active.contains(ARCHERS_TEMPO) ? 43 : 0, active.contains(MEMENTO_MORI) ? 6 : 0,
                active.contains(HONED_EDGE) ? 4 : 0, active.contains(NO_DISTRACTIONS),
                active.contains(FEEDING_FRENZY) ? 5 : 0, active.contains(FEEDING_FRENZY) ? 101 : 0,
                active.contains(ONE_FOR_ALL) ? 199 : 0, active.contains(SURROUNDED),
                active.contains(SWASHBUCKLER) ? 5 : 0, active.contains(SWASHBUCKLER) ? 89 : 0,
                active.contains(MULTIKILL_CLIP) ? 3 : 0, active.contains(MULTIKILL_CLIP) ? 100 : 0,
                active.contains(RAPID_HIT) ? 5 : 0, active.contains(RAPID_HIT) ? 47 : 0,
                active.contains(PERPETUAL_MOTION) ? 2 : 0,
                active.contains(TAP_THE_TRIGGER) ? 12 : 0, active.contains(FRENZY) ? 144 : 0,
                active.contains(ADRENALINE_JUNKIE) ? 5 : 0, active.contains(ADRENALINE_JUNKIE) ? 90 : 0,
                active.contains(FOCUSED_FURY) ? 220 : 0, ticks);
    }

    private static WeaponPerkRows.Snapshot stats(int ticks) { return snapshot(Set.of(), ticks); }

    @Test void canonical25FieldNamesTypesAndValuesPreserveAllEightLegacySourceContracts() throws Exception {
        var old14 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89);
        var old16 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89, 2, 73);
        var old18 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39);
        var old19 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 2);
        var old20 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 2, 12);
        var old21 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 2, 12, 144);
        var old23 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 2, 12, 144, 5, 90);
        var old24 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 2, 12, 144, 5, 90, 220);
        var canonical = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 2, 12, 144, 5, 90, 220, 200);
        Object[] values = {99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 2, 12, 144, 5, 90, 220, 200, 0, 0, 0};
        var names = List.of("killClipTicks", "outlawTicks", "rampageStacks", "rampageTicks",
                "archerTempoTicks", "mementoMoriRounds", "honedEdgeCharge", "noDistractions",
                "feedingFrenzyStacks", "feedingFrenzyTicks", "oneForAllTicks", "surrounded",
                "swashbucklerStacks", "swashbucklerTicks", "multikillClipStacks", "multikillClipTicks",
                "rapidHitStacks", "rapidHitTicks", "perpetualMotionStacks", "tapTheTriggerTicks",
                "frenzyTicks", "adrenalineJunkieStacks", "adrenalineJunkieTicks", "focusedFuryTicks", "statsForAllTicks", "heatingUpStacks", "heatingUpTicks", "threatDetectorStacks");
        var components = java.util.Arrays.copyOf(WeaponPerkRows.Snapshot.class.getRecordComponents(), 28);
        assertEquals(28, components.length);
        assertEquals(names, Arrays.stream(components).map(c -> c.getName()).toList());
        for (int i = 0; i < components.length; i++) {
            assertEquals(i == 7 || i == 11 ? boolean.class : int.class, components[i].getType());
            assertEquals(values[i], components[i].getAccessor().invoke(canonical), names.get(i));
        }
        var states = List.of(old14, old16, old18, old19, old20, old21, old23, old24);
        int[] arities = {14, 16, 18, 19, 20, 21, 23, 24};
        for (int n = 0; n < states.size(); n++) {
            var state = states.get(n);
            for (int i = 0; i < components.length; i++)
                assertEquals(i < arities[n] ? values[i] : 0, components[i].getAccessor().invoke(state),
                        "arity " + arities[n] + " field " + names.get(i));
            assertEquals(0, state.statsForAllTicks());
            assertTrue(WeaponPerkRows.project(state).stream().noneMatch(r -> r.kind() == STATS_FOR_ALL));
        }
        assertEquals(Set.of(14, 16, 18, 19, 20, 21, 23, 24, 25, 27, 28, 29, 35, 38, 40), Arrays.stream(
                WeaponPerkRows.Snapshot.class.getDeclaredConstructors()).map(c -> c.getParameterCount()).collect(Collectors.toSet()));
        // W173 callers still expose both actual AJ fields, with no accidental Stats for All.
        var legacyAj = new WeaponPerkRows.Snapshot(0, 0, 0, 0, 0, 0, 0, false, 0, 0, 0, false, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 90);
        assertEquals(List.of(ADRENALINE_JUNKIE), WeaponPerkRows.project(legacyAj).stream().map(WeaponPerkRows.Row::kind).toList());
    }

    @Test void legacy24KeepsFocusedFuryIndependentAndStatsNeverExposesTargetProgress() {
        var legacyFury = new WeaponPerkRows.Snapshot(0, 0, 0, 0, 0, 0, 0, false, 0, 0, 0, false,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 220);
        assertEquals(220, legacyFury.focusedFuryTicks());
        assertEquals(0, legacyFury.statsForAllTicks());
        assertEquals(List.of(FOCUSED_FURY), WeaponPerkRows.project(legacyFury).stream().map(WeaponPerkRows.Row::kind).toList());
        assertEquals(List.of(FOCUSED_FURY, STATS_FOR_ALL), WeaponPerkRows.project(snapshot(Set.of(FOCUSED_FURY), 200))
                .stream().map(WeaponPerkRows.Row::kind).toList());
        // The feed consumes remaining ticks only. Target progress belongs to runtime and cannot manufacture a row.
        assertTrue(WeaponPerkRows.project(stats(0)).isEmpty());
        for (int ticks : new int[]{2, 3, 200}) {
            var row = WeaponPerkRows.project(stats(ticks)).getFirst();
            assertEquals(0, row.count()); assertEquals(0, row.displayCount());
            assertEquals(NAME, row.label());
            assertFalse(row.kind().nodeIds().contains(STATS_FOR_ALL.nodeId("x")));
            assertFalse(row.kind().nodeIds().contains(STATS_FOR_ALL.nodeId("count")));
        }
    }

    @Test void everyValidTickShowsObservedValueAndCeilOneThroughTenSeconds() {
        for (int ticks = 1; ticks <= 200; ticks++) {
            var state = stats(ticks);
            var rows = WeaponPerkRows.project(state); assertEquals(1, rows.size());
            var row = rows.getFirst();
            assertEquals(STATS_FOR_ALL, row.kind()); assertEquals(NAME, row.label());
            assertEquals(0, row.count()); assertEquals(0, row.displayCount());
            assertEquals(ticks, row.ticks()); assertEquals((ticks + 19) / 20, row.seconds());
            assertTrue(row.seconds() >= 1 && row.seconds() <= 10);
            assertEquals(0, row.slot()); assertEquals(778, row.y());
            assertEquals(rows, WeaponPerkRows.project(state));
            assertThrows(UnsupportedOperationException.class, rows::clear);
        }
        assertThrows(NullPointerException.class, () -> WeaponPerkRows.project(null));
    }

    @Test void zeroNegativeOutOfBoundsAndOverflowHideWithoutClampingOrLeakingState() {
        for (int ticks : new int[]{Integer.MIN_VALUE, -200, -1, 0, 201, 202, Integer.MAX_VALUE}) {
            var state = stats(ticks);
            assertEquals(ticks, state.statsForAllTicks());
            assertTrue(WeaponPerkRows.project(state).isEmpty(), "ticks " + ticks);
            assertEquals(List.of(ADRENALINE_JUNKIE), WeaponPerkRows.project(snapshot(Set.of(ADRENALINE_JUNKIE), ticks))
                    .stream().map(WeaponPerkRows.Row::kind).toList());
        }
        var independent = stats(7); var expected = WeaponPerkRows.project(independent);
        for (int ticks : new int[]{200, 181, 180, 21, 20, 1, 0, -1, 201}) {
            WeaponPerkRows.project(snapshot(EnumSet.allOf(WeaponPerkRows.Kind.class), ticks));
            assertEquals(expected, WeaponPerkRows.project(independent));
            assertEquals(7, independent.statsForAllTicks());
        }
    }

    @Test void nineteenthKindPreservesEighteenKindPrefixAndCapForEveryOlderSubset() {
        assertTrue(WeaponPerkRows.Kind.values().length >= 21);
        assertEquals(PREFIX, List.of(WeaponPerkRows.Kind.values()).subList(0, 18));
        assertEquals(18, STATS_FOR_ALL.ordinal()); assertEquals(4, WeaponPerkRows.MAX_ROWS);
        for (var kind : PREFIX)
            assertEquals(List.of(kind), WeaponPerkRows.project(snapshot(Set.of(kind), 0)).stream().map(WeaponPerkRows.Row::kind).toList());
        for (int mask = 0; mask < (1 << PREFIX.size()); mask++) {
            var active = EnumSet.noneOf(WeaponPerkRows.Kind.class);
            for (int bit = 0; bit < PREFIX.size(); bit++) if ((mask & (1 << bit)) != 0) active.add(PREFIX.get(bit));
            var before = WeaponPerkRows.project(snapshot(active, 0));
            var after = WeaponPerkRows.project(snapshot(active, 200));
            var expected = new ArrayList<>(PREFIX.stream().filter(active::contains).toList());
            expected.add(STATS_FOR_ALL);
            assertEquals(expected.stream().limit(4).toList(), after.stream().map(WeaponPerkRows.Row::kind).toList());
            assertEquals(before, after.stream().filter(r -> r.kind() != STATS_FOR_ALL).toList());
            for (int slot = 0; slot < after.size(); slot++) {
                assertEquals(slot, after.get(slot).slot()); assertEquals(778 - 32 * slot, after.get(slot).y());
            }
        }
    }

    @Test void hiddenBuffPromotesAtCurrentTicksThenExpiryAndReconciliationRemoveAllNodes() {
        var crowded = EnumSet.of(OUTLAW, RAPID_HIT, FRENZY, ADRENALINE_JUNKIE);
        var hidden = WeaponPerkRows.project(snapshot(crowded, 200));
        assertTrue(hidden.stream().noneMatch(r -> r.kind() == STATS_FOR_ALL));
        assertEquals(STATS_FOR_ALL.nodeIds().stream().sorted().toList(), WeaponPerkRows.nodesToRemove(hidden, STATS_FOR_ALL.nodeIds()));
        crowded.remove(OUTLAW);
        var rows = WeaponPerkRows.project(snapshot(crowded, 21));
        var promoted = rows.getLast();
        assertEquals(STATS_FOR_ALL, promoted.kind()); assertEquals(21, promoted.ticks()); assertEquals(2, promoted.seconds());
        assertEquals(3, promoted.slot()); assertEquals(682, promoted.y());
        assertEquals(ADRENALINE_JUNKIE, WeaponPerkRows.project(snapshot(crowded, 0)).getLast().kind());
        assertEquals(STATS_FOR_ALL.nodeIds().stream().sorted().toList(), WeaponPerkRows.nodesToRemove(
                WeaponPerkRows.project(snapshot(crowded, 0)), STATS_FOR_ALL.nodeIds()));
        assertEquals(STATS_FOR_ALL.nodeIds().stream().sorted().toList(), WeaponPerkRows.nodesToRemove(List.of(), STATS_FOR_ALL.nodeIds()));
    }

    @Test void timerHasSixStableUniqueNodesAndReconcilesStaleCountAndUnknownSuffixes() {
        var suffixes = List.of("marker", "label", "minutes", "colon", "tens", "ones");
        var expected = suffixes.stream().map(s -> "destiny:hud_perk_stats_for_all_" + s).toList();
        assertEquals(WeaponPerkRows.Layout.TIMER, STATS_FOR_ALL.layout);
        assertTrue(STATS_FOR_ALL.layout.timed()); assertFalse(STATS_FOR_ALL.layout.counted());
        assertEquals(expected, STATS_FOR_ALL.nodeIds());
        var existing = new ArrayList<>(expected.reversed());
        var stale = List.of(STATS_FOR_ALL.nodeId("unknown"), STATS_FOR_ALL.nodeId("x"), STATS_FOR_ALL.nodeId("count"));
        existing.addAll(stale); existing.add("destiny:hud_ammo_label"); existing.add("destiny:hud_perks_unrelated");
        for (int ticks : new int[]{1, 20, 21, 180, 181, 200})
            assertEquals(stale.stream().sorted().toList(), WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(stats(ticks)), existing));
        var all = existing.stream().filter(s -> s.startsWith(WeaponPerkRows.PREFIX)).sorted().toList();
        for (var state : List.of(stats(0), stats(-1), stats(201), snapshot(EnumSet.allOf(WeaponPerkRows.Kind.class), 200)))
            assertEquals(all, WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(state), existing));
        assertEquals(all, WeaponPerkRows.nodesToRemove(List.of(), existing));
        // Retention uses unique node IDs; preserve the existing sorted-removal policy even for duplicate inputs.
        var duplicates = List.of(STATS_FOR_ALL.nodeId("marker"), STATS_FOR_ALL.nodeId("marker"),
                STATS_FOR_ALL.nodeId("count"), STATS_FOR_ALL.nodeId("count"), "destiny:hud_perks_unrelated");
        assertEquals(List.of(STATS_FOR_ALL.nodeId("count"), STATS_FOR_ALL.nodeId("count")),
                WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(stats(200)), duplicates));
        assertEquals(duplicates.stream().filter(id -> id.startsWith(WeaponPerkRows.PREFIX)).sorted().toList(),
                WeaponPerkRows.nodesToRemove(List.of(), duplicates));
        var nodes = Arrays.stream(WeaponPerkRows.Kind.values()).flatMap(k -> k.nodeIds().stream()).toList();
        assertEquals(nodes.size(), Set.copyOf(nodes).size());
        // Reconciliation retains exactly the live four rows across the complete feed, not only W176.
        var visible = WeaponPerkRows.project(snapshot(EnumSet.of(OUTLAW, FRENZY, ADRENALINE_JUNKIE), 200));
        var retained = visible.stream().flatMap(r -> r.kind().nodeIds().stream()).collect(Collectors.toSet());
        assertEquals(nodes.stream().filter(id -> !retained.contains(id)).sorted().toList(), WeaponPerkRows.nodesToRemove(visible, nodes));
    }

    @Test void itemModelTextureGraphHasCustomTintAndExistingTimerGeometry() throws Exception {
        var graph = json(ITEM).getAsJsonObject("model");
        assertEquals("minecraft:model", graph.get("type").getAsString());
        assertEquals("destiny:gui/hud/" + NAME, graph.get("model").getAsString());
        assertEquals(JsonParser.parseString("[{\"type\":\"minecraft:custom_model_data\",\"index\":0,\"default\":16777215}]"), graph.get("tints"));
        var model = json(MODEL);
        assertFalse(model.get("ambientocclusion").getAsBoolean()); assertEquals("front", model.get("gui_light").getAsString());
        assertEquals("destiny:item/hud/" + NAME, model.getAsJsonObject("textures").get("0").getAsString());
        assertEquals("#0", model.getAsJsonObject("textures").get("particle").getAsString());
        assertEquals(1, model.getAsJsonArray("elements").size());
        var element = model.getAsJsonArray("elements").get(0).getAsJsonObject();
        assertEquals(JsonParser.parseString("[0,0,8]"), element.get("from"));
        assertEquals(JsonParser.parseString("[16,16,8]"), element.get("to"));
        assertFalse(element.get("shade").getAsBoolean());
        var faces = element.getAsJsonObject("faces"); assertEquals(Set.of("north", "south"), faces.keySet());
        for (var face : faces.entrySet()) {
            assertEquals("#0", face.getValue().getAsJsonObject().get("texture").getAsString());
            assertEquals(0, face.getValue().getAsJsonObject().get("tintindex").getAsInt());
            assertEquals(JsonParser.parseString("[0,0,16,16]"), face.getValue().getAsJsonObject().get("uv"));
        }
        assertEquals(8, 168 - 94 / 2 - (104 + 18 / 2));
        assertEquals(12, 232 - 10 / 2 - (168 + 94 / 2));
        assertTrue(32 > 24);
        for (Path resource : List.of(ITEM, MODEL, TEXTURE)) {
            try (var stream = getClass().getResourceAsStream("/assets/destiny/" + ASSETS.relativize(resource))) {
                assertNotNull(stream, resource.toString()); assertArrayEquals(Files.readAllBytes(resource), stream.readAllBytes());
            }
        }
    }

    @Test void exactlyThreePackAssetsAndOriginalSourceHavePinnedHashesAndTruthfulContract() throws Exception {
        var manifest = json(ART.resolve("manifest.json"));
        assertEquals("W176", manifest.get("stage").getAsString());
        assertEquals("STATS FOR ALL", manifest.get("label").getAsString());
        assertEquals(JsonParser.parseString("[94,24]"), manifest.get("size"));
        assertTrue(manifest.get("provenance").getAsString().contains("not an official Destiny sprite"));
        assertEquals("fcf34b330033e26c06e9bd466bea5a3e4b2f39272972275369beb7d8b257ed57", manifest.get("font_sha256").getAsString());
        assertEquals("Arial Narrow Bold", manifest.get("font_family").getAsString());
        assertEquals(22, manifest.get("font_size_px").getAsInt()); assertEquals(4, manifest.get("supersampling").getAsInt());
        assertEquals("BASIC", manifest.get("layout_engine").getAsString());
        assertEquals("12.3.0", manifest.get("pillow_version").getAsString());
        assertEquals("2.14.3", manifest.get("freetype_version").getAsString());
        var contract = manifest.getAsJsonObject("runtime_contract");
        assertEquals("TIMER", contract.get("layout").getAsString());
        assertEquals(JsonParser.parseString("[1,200]"), contract.get("valid_ticks"));
        assertEquals(4, contract.get("max_rows").getAsInt());
        assertTrue(contract.get("seconds").getAsString().contains("0:01..0:10"));
        assertTrue(contract.get("priority").getAsString().contains("FOCUSED_FURY"));
        assertTrue(contract.get("activation").getAsString().contains("no manufactured activation or counter"));
        assertTrue(contract.get("activation").getAsString().contains("no 2/3 target-progress row"));
        assertTrue(contract.get("integration").getAsString().contains("WeaponStatsForAll.remaining"));
        assertTrue(contract.get("marker").getAsString().contains("Green"));
        assertTrue(contract.get("integration").getAsString().contains("twenty-fifth"));
        assertTrue(contract.get("native_validation").getAsString().contains("Pending master"));
        assertEquals(6, contract.getAsJsonArray("native_queue").size());
        assertEquals(STATS_FOR_ALL.layout.suffixes, contract.getAsJsonArray("node_suffixes").asList().stream().map(v -> v.getAsString()).toList());
        assertTrue(manifest.get("horizontal_scale").getAsDouble() > 0.5 && manifest.get("horizontal_scale").getAsDouble() < 1.0);
        var pack = manifest.getAsJsonObject("pack_files");
        assertEquals(Set.of(TEXTURE.toString(), MODEL.toString(), ITEM.toString()), pack.keySet());
        long bytes = 0;
        for (var entry : pack.entrySet()) {
            byte[] data = Files.readAllBytes(Path.of(entry.getKey())); bytes += data.length;
            assertEquals(entry.getValue().getAsString(), sha(data));
        }
        assertEquals(bytes, manifest.get("pack_bytes").getAsLong()); assertTrue(bytes <= 16384);
        var source = ART.resolve("stats-for-all.svg");
        assertEquals(Set.of(source.toString()), manifest.getAsJsonObject("source_files").keySet());
        assertEquals(sha(Files.readAllBytes(source)), manifest.getAsJsonObject("source_files").get(source.toString()).getAsString());
        var found = new java.util.HashSet<String>();
        for (String folder : List.of("items/gui/hud", "models/gui/hud", "textures/gui/hud", "textures/item/hud")) {
            if (!Files.isDirectory(ASSETS.resolve(folder))) continue;
            try (var paths = Files.list(ASSETS.resolve(folder))) {
                paths.filter(p -> p.getFileName().toString().startsWith(NAME)).forEach(p -> found.add(p.toString()));
            }
        }
        assertEquals(pack.keySet(), found);
        try (var paths = Files.list(ART)) {
            assertEquals(Set.of("stats-for-all.svg", "manifest.json"), paths.map(p -> p.getFileName().toString()).collect(Collectors.toSet()));
        }
    }

    @Test void pngAndSelfContainedSvgDecodeToIdenticalUnclippedWhiteCoverage() throws Exception {
        var image = ImageIO.read(TEXTURE.toFile()); assertNotNull(image);
        assertEquals(94, image.getWidth()); assertEquals(24, image.getHeight());
        var factory = DocumentBuilderFactory.newInstance();
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        var svg = factory.newDocumentBuilder().parse(ART.resolve("stats-for-all.svg").toFile());
        assertEquals("94", svg.getDocumentElement().getAttribute("width")); assertEquals("24", svg.getDocumentElement().getAttribute("height"));
        assertEquals("STATS FOR ALL - original W176 generated label", svg.getElementsByTagName("title").item(0).getTextContent());
        assertEquals(0, svg.getElementsByTagName("image").getLength()); assertEquals(0, svg.getElementsByTagName("text").getLength());
        int[][] coverage = new int[24][94];
        var rects = svg.getElementsByTagName("rect"); assertTrue(rects.getLength() > 100);
        for (int i = 0; i < rects.getLength(); i++) {
            var rect = (org.w3c.dom.Element) rects.item(i);
            int x = Integer.parseInt(rect.getAttribute("x")), y = Integer.parseInt(rect.getAttribute("y"));
            int width = Integer.parseInt(rect.getAttribute("width"));
            assertEquals("1", rect.getAttribute("height")); assertEquals("white", rect.getAttribute("fill"));
            int alpha = (int) Math.round(Double.parseDouble(rect.getAttribute("fill-opacity")) * 255);
            for (int dx = 0; dx < width; dx++) coverage[y][x + dx] = alpha;
        }
        int visible = 0, antialias = 0, solid = 0;
        for (int y = 0; y < 24; y++) for (int x = 0; x < 94; x++) {
            int pixel = image.getRGB(x, y), alpha = pixel >>> 24;
            assertEquals(0xffffff, pixel & 0xffffff); assertEquals(coverage[y][x], alpha);
            if (alpha > 0) visible++;
            if (alpha > 0 && alpha < 255) antialias++;
            if (alpha == 255) solid++;
            if (x == 0 || x == 93 || y == 0 || y == 23) assertEquals(0, alpha);
        }
        assertTrue(visible > 500 && visible < 1900); assertTrue(antialias > 100 && solid > 25);
    }

    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }

    private static String sha(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
}
