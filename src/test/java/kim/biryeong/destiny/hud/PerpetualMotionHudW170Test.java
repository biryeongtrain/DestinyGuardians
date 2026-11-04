package kim.biryeong.destiny.hud;

import com.google.gson.JsonObject;
import com.google.gson.JsonParseException;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import static kim.biryeong.destiny.hud.WeaponPerkRows.Kind.*;
import static org.junit.jupiter.api.Assertions.*;

/** Observed Perpetual Motion counts and real 26.3 parsers; live adapter integration belongs to master. */
class PerpetualMotionHudW170Test {
    private static final String NAME = "perk_perpetual_motion_w170";
    private static final Path ASSETS = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/hud/w170");
    private static final Path TEXTURE = ASSETS.resolve("textures/item/hud/" + NAME + ".png");
    private static final Path MODEL = ASSETS.resolve("models/gui/hud/" + NAME + ".json");
    private static final Path ITEM = ASSETS.resolve("items/gui/hud/" + NAME + ".json");
    private static final List<WeaponPerkRows.Kind> PRIORITY = List.of(
            MEMENTO_MORI, HONED_EDGE, KILL_CLIP, MULTIKILL_CLIP, RAMPAGE, ONE_FOR_ALL,
            SURROUNDED, SWASHBUCKLER, OUTLAW, ARCHERS_TEMPO, NO_DISTRACTIONS,
            RAPID_HIT, FEEDING_FRENZY, PERPETUAL_MOTION);

    private static WeaponPerkRows.Snapshot motion(int stacks) {
        return snapshot(Set.of(PERPETUAL_MOTION), stacks);
    }

    private static WeaponPerkRows.Snapshot snapshot(Set<WeaponPerkRows.Kind> active, int stacks) {
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
                active.contains(PERPETUAL_MOTION) ? stacks : 0);
    }

    @Test void fourteenSixteenAndEighteenArgumentConstructorsPreserveEveryFieldAndZeroDefaultNewCounts() {
        var old14 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89);
        var old16 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 2, 73);
        var old18 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39);
        var expected14 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 0, 0, 0, 0, 0);
        var expected16 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 2, 73, 0, 0, 0);
        var expected18 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 0);
        assertEquals(expected14, old14); assertEquals(expected16, old16); assertEquals(expected18, old18);
        for (var state : List.of(old14, old16, old18)) {
            assertEquals(0, state.perpetualMotionStacks());
            assertTrue(WeaponPerkRows.project(state).stream().noneMatch(r -> r.kind() == PERPETUAL_MOTION));
        }
        assertEquals(0, old14.multikillClipStacks()); assertEquals(0, old14.multikillClipTicks());
        assertEquals(0, old16.rapidHitStacks()); assertEquals(0, old16.rapidHitTicks());
        assertEquals(List.of(MEMENTO_MORI, HONED_EDGE, KILL_CLIP, RAMPAGE),
                WeaponPerkRows.project(old14).stream().map(WeaponPerkRows.Row::kind).toList());
        assertEquals(WeaponPerkRows.project(expected16), WeaponPerkRows.project(old16));
        assertEquals(WeaponPerkRows.project(expected18), WeaponPerkRows.project(old18));
    }

    @Test void onlyOneAndTwoAreVisibleWithoutAnyCountdown() {
        for (int count : new int[]{Integer.MIN_VALUE, -2, -1, 0, 1, 2, 3, 5, Integer.MAX_VALUE}) {
            var state = motion(count);
            var rows = WeaponPerkRows.project(state);
            assertEquals(count == 1 || count == 2, !rows.isEmpty(), "count " + count);
            if (rows.isEmpty()) continue;
            var row = rows.getFirst();
            assertEquals(PERPETUAL_MOTION, row.kind()); assertEquals(NAME, row.label());
            assertEquals(count, row.count()); assertEquals(count, row.displayCount());
            assertEquals(0, row.ticks()); assertEquals(0, row.seconds());
            assertEquals(0, row.slot()); assertEquals(778, row.y());
            assertEquals(rows, WeaponPerkRows.project(state));
            assertThrows(UnsupportedOperationException.class, rows::clear);
        }
        // A lower-priority valid count still promotes past a malformed Rapid Hit state.
        var malformedRapid = new WeaponPerkRows.Snapshot(0, 0, 0, 0, 0, 0, 0,
                false, 0, 0, 0, false, 0, 0, 0, 0, 6, 100, 2);
        assertEquals(PERPETUAL_MOTION, WeaponPerkRows.project(malformedRapid).getFirst().kind());
        assertThrows(NullPointerException.class, () -> WeaponPerkRows.project(null));
    }

    @Test void countdownValuesOfOtherRowsNeverBecomeAPerpetualDuration() {
        for (int unrelatedTicks : new int[]{Integer.MIN_VALUE, -1, 0, 1, 40, 200, Integer.MAX_VALUE}) {
            var state = new WeaponPerkRows.Snapshot(unrelatedTicks, 0, 0, 0, 0, 0, 0,
                    false, 0, 0, 0, false, 0, 0, 0, 0, 0, 0, 2);
            var row = WeaponPerkRows.project(state).getLast();
            assertEquals(PERPETUAL_MOTION, row.kind()); assertEquals(2, row.displayCount());
            assertEquals(0, row.ticks()); assertEquals(0, row.seconds());
            assertFalse(row.kind().layout.timed());
        }
        assertEquals("perpetualMotionStacks", WeaponPerkRows.Snapshot.class.getRecordComponents()[18].getName());
        assertTrue(WeaponPerkRows.Snapshot.class.getRecordComponents().length >= 28);
    }

    @Test void all16384ActivationSetsKeepOldOrderFourRowCapAndUtilityAppend() {
        // Later utility rows may append; retain every original14priority/subset assertion.
        assertEquals(PRIORITY, List.of(WeaponPerkRows.Kind.values()).subList(0, PRIORITY.size()));
        assertEquals(FEEDING_FRENZY.ordinal() + 1, PERPETUAL_MOTION.ordinal());
        assertEquals(4, WeaponPerkRows.MAX_ROWS);
        for (int mask = 0; mask < (1 << PRIORITY.size()); mask++) {
            var active = EnumSet.noneOf(WeaponPerkRows.Kind.class);
            for (int bit = 0; bit < PRIORITY.size(); bit++)
                if ((mask & (1 << bit)) != 0) active.add(PRIORITY.get(bit));
            var state = snapshot(active, 2);
            var rows = WeaponPerkRows.project(state);
            assertEquals(PRIORITY.stream().filter(active::contains).limit(4).toList(),
                    rows.stream().map(WeaponPerkRows.Row::kind).toList(), "mask " + mask);
            assertEquals(rows, WeaponPerkRows.project(state));
            for (int slot = 0; slot < rows.size(); slot++) {
                assertEquals(slot, rows.get(slot).slot());
                assertEquals(778 - 32 * slot, rows.get(slot).y());
                if (slot > 0) assertTrue(rows.get(slot - 1).y() - rows.get(slot).y() > 24);
            }
            // Projection never changes an earlier row to make room for the appended utility.
            active.remove(PERPETUAL_MOTION);
            var legacyRows = WeaponPerkRows.project(snapshot(active, 0));
            assertEquals(legacyRows, rows.stream().filter(r -> r.kind() != PERPETUAL_MOTION).toList());
        }
    }

    @Test void hiddenCountsPromoteFromCurrentSnapshotAndNeverCacheStateAcrossPlayers() {
        var crowded = EnumSet.of(OUTLAW, NO_DISTRACTIONS, RAPID_HIT, FEEDING_FRENZY, PERPETUAL_MOTION);
        assertTrue(WeaponPerkRows.project(snapshot(crowded, 2)).stream().noneMatch(r -> r.kind() == PERPETUAL_MOTION));
        crowded.remove(OUTLAW);
        var promoted = WeaponPerkRows.project(snapshot(crowded, 1)).getLast();
        assertEquals(PERPETUAL_MOTION, promoted.kind()); assertEquals(3, promoted.slot());
        assertEquals(1, promoted.displayCount()); assertEquals(0, promoted.ticks());
        assertEquals(FEEDING_FRENZY, WeaponPerkRows.project(snapshot(crowded, 0)).getLast().kind());
        var independent = motion(2);
        var expected = WeaponPerkRows.project(independent);
        for (int count : new int[]{2, 1, 0, -1, 3, 2}) {
            WeaponPerkRows.project(motion(count));
            WeaponPerkRows.project(snapshot(EnumSet.allOf(WeaponPerkRows.Kind.class), count));
            assertEquals(expected, WeaponPerkRows.project(independent));
        }
        assertEquals(1, WeaponPerkRows.project(motion(1)).getFirst().displayCount());
        assertTrue(WeaponPerkRows.project(motion(0)).isEmpty());
    }

    @Test void exactlyFourCountNodesRetainMembershipAndRemoveStaleTimerAndUnknownSuffixes() {
        var expected = List.of("marker", "label", "x", "count").stream()
                .map(s -> "destiny:hud_perk_perpetual_motion_" + s).toList();
        assertEquals(WeaponPerkRows.Layout.COUNT, PERPETUAL_MOTION.layout);
        assertTrue(PERPETUAL_MOTION.layout.counted()); assertFalse(PERPETUAL_MOTION.layout.timed());
        assertEquals(expected, PERPETUAL_MOTION.nodeIds());
        var obsolete = List.of("minutes", "colon", "tens", "ones", "unknown").stream()
                .map(PERPETUAL_MOTION::nodeId).toList();
        var existing = new ArrayList<>(expected.reversed()); existing.addAll(obsolete);
        existing.add("destiny:hud_ammo_label"); existing.add("destiny:hud_perks_unrelated");
        for (int count : new int[]{1, 2})
            assertEquals(obsolete.stream().sorted().toList(),
                    WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(motion(count)), existing));
        var removed = existing.stream().filter(s -> s.startsWith(WeaponPerkRows.PREFIX)).sorted().toList();
        for (int invalid : new int[]{0, -1, 3, Integer.MIN_VALUE, Integer.MAX_VALUE})
            assertEquals(removed, WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(motion(invalid)), existing));
        assertEquals(removed, WeaponPerkRows.nodesToRemove(
                WeaponPerkRows.project(snapshot(EnumSet.allOf(WeaponPerkRows.Kind.class), 2)), existing));
        // Adapter supplies no visible rows when stowed/unequipped: all feed nodes must clean up.
        assertEquals(removed, WeaponPerkRows.nodesToRemove(List.of(), existing));
        assertTrue(WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(motion(1)), expected).isEmpty());
        var allNodes = PRIORITY.stream().flatMap(k -> k.nodeIds().stream()).toList();
        assertEquals(allNodes.size(), Set.copyOf(allNodes).size());
    }

    @Test void actual26ItemCodecAndCuboidParserAcceptLabelAndRejectMalformedControls() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap(); ItemTintSources.bootstrap();
        var graph = json(ITEM).getAsJsonObject("model");
        var decoded = ItemModels.CODEC.parse(JsonOps.INSTANCE, graph);
        assertTrue(decoded.isSuccess(), () -> decoded.error().toString());
        var invalid = graph.deepCopy();
        invalid.getAsJsonArray("tints").get(0).getAsJsonObject().addProperty("type", "destiny:invalid_tint");
        assertFalse(ItemModels.CODEC.parse(JsonOps.INSTANCE, invalid).isSuccess());
        assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(MODEL))));
        var broken = json(MODEL);
        broken.getAsJsonArray("elements").get(0).getAsJsonObject().add("from", JsonParser.parseString("[0,0]"));
        assertThrows(JsonParseException.class, () -> CuboidModel.fromStream(new StringReader(broken.toString())));
        assertEquals("destiny:gui/hud/" + NAME, graph.get("model").getAsString());
        assertEquals(JsonParser.parseString("[{\"type\":\"minecraft:custom_model_data\",\"index\":0,\"default\":16777215}]"),
                graph.get("tints"));
        var model = json(MODEL);
        assertEquals("destiny:item/hud/" + NAME, model.getAsJsonObject("textures").get("0").getAsString());
        assertEquals("#0", model.getAsJsonObject("textures").get("particle").getAsString());
        var faces = model.getAsJsonArray("elements").get(0).getAsJsonObject().getAsJsonObject("faces");
        assertEquals(Set.of("north", "south"), faces.keySet());
        for (var face : faces.entrySet()) {
            assertEquals(0, face.getValue().getAsJsonObject().get("tintindex").getAsInt());
            assertEquals(JsonParser.parseString("[0,0,16,16]"), face.getValue().getAsJsonObject().get("uv"));
        }
    }

    @Test void exactlyThreePackAssetsAndOriginalSourceHavePinnedHashesWithinBudget() throws Exception {
        var manifest = json(ART.resolve("manifest.json"));
        assertEquals("W170", manifest.get("stage").getAsString());
        assertEquals("PERPETUAL MOTION", manifest.get("label").getAsString());
        assertTrue(manifest.get("provenance").getAsString().contains("not an official Destiny sprite"));
        assertEquals("fcf34b330033e26c06e9bd466bea5a3e4b2f39272972275369beb7d8b257ed57",
                manifest.get("font_sha256").getAsString());
        assertEquals("12.3.0", manifest.get("pillow_version").getAsString());
        assertEquals("2.14.3", manifest.get("freetype_version").getAsString());
        var contract = manifest.getAsJsonObject("runtime_contract");
        assertEquals("COUNT", contract.get("layout").getAsString());
        assertEquals(JsonParser.parseString("[1,2]"), contract.get("stacks"));
        assertEquals(4, contract.get("max_rows").getAsInt());
        assertTrue(contract.get("remaining_ticks").getAsString().contains("no buff duration"));
        assertTrue(contract.get("marker").getAsString().contains("Green"));
        assertTrue(manifest.get("horizontal_scale").getAsDouble() > 0.5);
        assertTrue(manifest.get("horizontal_scale").getAsDouble() < 1.0);
        var pack = manifest.getAsJsonObject("pack_files");
        assertEquals(Set.of(TEXTURE.toString(), MODEL.toString(), ITEM.toString()), pack.keySet());
        long bytes = 0;
        for (var entry : pack.entrySet()) {
            byte[] data = Files.readAllBytes(Path.of(entry.getKey())); bytes += data.length;
            assertEquals(entry.getValue().getAsString(), sha(data));
        }
        assertEquals(bytes, manifest.get("pack_bytes").getAsLong()); assertTrue(bytes <= 16384);
        var source = ART.resolve("perpetual-motion.svg");
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
            assertEquals(Set.of("perpetual-motion.svg", "manifest.json"),
                    paths.map(p -> p.getFileName().toString()).collect(Collectors.toSet()));
        }
    }

    @Test void pngAndSelfContainedSvgDecodeToIdenticalUnclippedWhiteCoverage() throws Exception {
        var image = ImageIO.read(TEXTURE.toFile()); assertNotNull(image);
        assertEquals(118, image.getWidth()); assertEquals(24, image.getHeight());
        var factory = DocumentBuilderFactory.newInstance();
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        var svg = factory.newDocumentBuilder().parse(ART.resolve("perpetual-motion.svg").toFile());
        assertEquals("118", svg.getDocumentElement().getAttribute("width"));
        assertEquals("24", svg.getDocumentElement().getAttribute("height"));
        assertEquals("PERPETUAL MOTION - original W170 generated label", svg.getElementsByTagName("title").item(0).getTextContent());
        assertEquals(0, svg.getElementsByTagName("image").getLength());
        assertEquals(0, svg.getElementsByTagName("text").getLength());
        int[][] coverage = new int[24][118];
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
        for (int y = 0; y < 24; y++) for (int x = 0; x < 118; x++) {
            int pixel = image.getRGB(x, y), alpha = pixel >>> 24;
            assertEquals(0xffffff, pixel & 0xffffff); assertEquals(coverage[y][x], alpha);
            if (alpha > 0) visible++;
            if (alpha > 0 && alpha < 255) antialias++;
            if (alpha == 255) solid++;
            if (x == 0 || x == 117 || y == 0 || y == 23) assertEquals(0, alpha);
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
