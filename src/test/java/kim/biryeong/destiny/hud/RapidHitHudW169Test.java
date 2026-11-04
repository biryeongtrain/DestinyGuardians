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

/** Observed Rapid Hit rows and real 26.3 parsers; live adapter integration belongs to master. */
class RapidHitHudW169Test {
    private static final String NAME = "perk_rapid_hit_w169";
    private static final Path ASSETS = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/hud/w169");
    private static final Path TEXTURE = ASSETS.resolve("textures/item/hud/" + NAME + ".png");
    private static final Path MODEL = ASSETS.resolve("models/gui/hud/" + NAME + ".json");
    private static final Path ITEM = ASSETS.resolve("items/gui/hud/" + NAME + ".json");
    private static final List<WeaponPerkRows.Kind> PRIORITY = List.of(
            MEMENTO_MORI, HONED_EDGE, KILL_CLIP, MULTIKILL_CLIP, RAMPAGE, ONE_FOR_ALL,
            SURROUNDED, SWASHBUCKLER, OUTLAW, ARCHERS_TEMPO, NO_DISTRACTIONS, RAPID_HIT, FEEDING_FRENZY);

    private static WeaponPerkRows.Snapshot rapid(int stacks, int ticks) {
        return snapshot(Set.of(RAPID_HIT), stacks, ticks);
    }

    private static WeaponPerkRows.Snapshot snapshot(Set<WeaponPerkRows.Kind> active) {
        return snapshot(active, 5, 47);
    }

    private static WeaponPerkRows.Snapshot snapshot(Set<WeaponPerkRows.Kind> active, int stacks, int ticks) {
        return new WeaponPerkRows.Snapshot(
                active.contains(KILL_CLIP) ? 99 : 0, active.contains(OUTLAW) ? 87 : 0,
                active.contains(RAMPAGE) ? 3 : 0, active.contains(RAMPAGE) ? 61 : 0,
                active.contains(ARCHERS_TEMPO) ? 43 : 0, active.contains(MEMENTO_MORI) ? 6 : 0,
                active.contains(HONED_EDGE) ? 4 : 0, active.contains(NO_DISTRACTIONS),
                active.contains(FEEDING_FRENZY) ? 5 : 0, active.contains(FEEDING_FRENZY) ? 101 : 0,
                active.contains(ONE_FOR_ALL) ? 199 : 0, active.contains(SURROUNDED),
                active.contains(SWASHBUCKLER) ? 5 : 0, active.contains(SWASHBUCKLER) ? 89 : 0,
                active.contains(MULTIKILL_CLIP) ? 3 : 0, active.contains(MULTIKILL_CLIP) ? 100 : 0,
                active.contains(RAPID_HIT) ? stacks : 0, active.contains(RAPID_HIT) ? ticks : 0);
    }

    @Test void fourteenAndSixteenArgumentConstructorsRetainEveryOldFieldAndDefaultRapidHitToZero() {
        var old14 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89);
        var old16 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 2, 73);
        var extended14 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 0, 0, 0, 0);
        var extended16 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 2, 73, 0, 0);
        assertEquals(extended14, old14); assertEquals(extended16, old16);
        for (var state : List.of(old14, old16)) {
            assertEquals(0, state.rapidHitStacks()); assertEquals(0, state.rapidHitTicks());
            assertTrue(WeaponPerkRows.project(state).stream().noneMatch(r -> r.kind() == RAPID_HIT));
        }
        assertEquals(WeaponPerkRows.project(extended14), WeaponPerkRows.project(old14));
        assertEquals(WeaponPerkRows.project(extended16), WeaponPerkRows.project(old16));
        assertEquals(List.of(MEMENTO_MORI, HONED_EDGE, KILL_CLIP, RAMPAGE),
                WeaponPerkRows.project(old14).stream().map(WeaponPerkRows.Row::kind).toList());
        assertEquals(List.of(MEMENTO_MORI, HONED_EDGE, KILL_CLIP, MULTIKILL_CLIP),
                WeaponPerkRows.project(old16).stream().map(WeaponPerkRows.Row::kind).toList());
    }

    @Test void allFiveStacksShowObservedCountAndTicksThroughLastTickWithNoAssumedDuration() {
        for (int stacks = 1; stacks <= 5; stacks++) {
            for (int ticks = 121; ticks >= 1; ticks--) {
                var rows = WeaponPerkRows.project(rapid(stacks, ticks));
                assertEquals(1, rows.size());
                var row = rows.getFirst();
                assertEquals(RAPID_HIT, row.kind());
                assertEquals(stacks, row.count()); assertEquals(stacks, row.displayCount());
                assertEquals(ticks, row.ticks()); assertEquals((ticks + 19) / 20, row.seconds());
                assertEquals(NAME, row.label());
                assertEquals(0, row.slot()); assertEquals(778, row.y());
            }
            assertTrue(WeaponPerkRows.project(rapid(stacks, 0)).isEmpty());
        }
        assertEquals(107374183,
                WeaponPerkRows.project(rapid(5, Integer.MAX_VALUE)).getFirst().seconds());
        assertThrows(UnsupportedOperationException.class,
                () -> WeaponPerkRows.project(rapid(1, 1)).clear());
    }

    @Test void invalidCountsAndNonpositiveTicksFailClosedAndFreeTheSlot() {
        for (int stacks : new int[]{Integer.MIN_VALUE, -1, 0, 1, 2, 3, 4, 5, 6, Integer.MAX_VALUE}) {
            for (int ticks : new int[]{Integer.MIN_VALUE, -1, 0, 1, 47, Integer.MAX_VALUE}) {
                boolean valid = stacks >= 1 && stacks <= 5 && ticks > 0;
                assertEquals(valid, !WeaponPerkRows.project(rapid(stacks, ticks)).isEmpty(), stacks + "/" + ticks);
                if (!valid) {
                    var rows = WeaponPerkRows.project(snapshot(Set.of(RAPID_HIT, FEEDING_FRENZY), stacks, ticks));
                    assertEquals(1, rows.size()); assertEquals(FEEDING_FRENZY, rows.getFirst().kind());
                    assertEquals(0, rows.getFirst().slot());
                }
            }
        }
    }

    @Test void all8192ActivationSetsKeepFourStableContiguousRowsWithRapidHitInReloadUtility() {
        assertEquals(PRIORITY, List.of(WeaponPerkRows.Kind.values()).subList(0, PRIORITY.size()));
        assertEquals(FEEDING_FRENZY.ordinal() - 1, RAPID_HIT.ordinal());
        assertEquals(4, WeaponPerkRows.MAX_ROWS);
        for (int mask = 0; mask < (1 << PRIORITY.size()); mask++) {
            var active = EnumSet.noneOf(WeaponPerkRows.Kind.class);
            for (int bit = 0; bit < PRIORITY.size(); bit++)
                if ((mask & (1 << bit)) != 0) active.add(PRIORITY.get(bit));
            var state = snapshot(active);
            var rows = WeaponPerkRows.project(state);
            assertEquals(PRIORITY.stream().filter(active::contains).limit(4).toList(),
                    rows.stream().map(WeaponPerkRows.Row::kind).toList(), "mask " + mask);
            assertEquals(rows, WeaponPerkRows.project(state)); assertTrue(rows.size() <= 4);
            for (int slot = 0; slot < rows.size(); slot++) {
                assertEquals(slot, rows.get(slot).slot());
                assertEquals(778 - 32 * slot, rows.get(slot).y());
                if (slot > 0) assertTrue(rows.get(slot - 1).y() - rows.get(slot).y() > 24);
            }
        }
    }

    @Test void preemptionExpiryRefreshAndIndependentSnapshotsNeverCacheCountOrDeadline() {
        var active = EnumSet.of(KILL_CLIP, MULTIKILL_CLIP, OUTLAW, NO_DISTRACTIONS, RAPID_HIT, FEEDING_FRENZY);
        assertTrue(WeaponPerkRows.project(snapshot(active, 5, 1)).stream().noneMatch(r -> r.kind() == RAPID_HIT));
        active.remove(KILL_CLIP);
        var promoted = WeaponPerkRows.project(snapshot(active, 2, 21)).getLast();
        assertEquals(RAPID_HIT, promoted.kind()); assertEquals(3, promoted.slot());
        assertEquals(2, promoted.count()); assertEquals(21, promoted.ticks());
        // A hidden buff that expired must not reappear when a higher-priority row disappears.
        var expired = WeaponPerkRows.project(snapshot(active, 5, 0));
        assertEquals(FEEDING_FRENZY, expired.getLast().kind()); assertEquals(3, expired.getLast().slot());
        active.remove(OUTLAW);
        var moved = WeaponPerkRows.project(snapshot(active, 1, 1)).get(2);
        assertEquals(RAPID_HIT, moved.kind()); assertEquals(1, moved.ticks());
        var independent = rapid(2, 39);
        var expected = WeaponPerkRows.project(independent);
        WeaponPerkRows.project(rapid(5, 1));
        assertEquals(1, WeaponPerkRows.project(rapid(1, 47)).getFirst().count());
        assertEquals(47, WeaponPerkRows.project(rapid(1, 47)).getFirst().ticks());
        WeaponPerkRows.project(rapid(0, 0));
        WeaponPerkRows.project(snapshot(EnumSet.allOf(WeaponPerkRows.Kind.class)));
        assertEquals(expected, WeaponPerkRows.project(independent));
        assertTrue(WeaponPerkRows.project(rapid(5, 0)).isEmpty());
    }

    @Test void expiryStowPreemptionAndUnknownNodesRemoveAllEightRapidHitNodesDeterministically() {
        var expected = List.of("marker", "label", "x", "count", "minutes", "colon", "tens", "ones")
                .stream().map(s -> "destiny:hud_perk_rapid_hit_" + s).toList();
        assertEquals(WeaponPerkRows.Layout.STACKED_TIMER, RAPID_HIT.layout);
        assertTrue(RAPID_HIT.layout.timed()); assertTrue(RAPID_HIT.layout.counted());
        assertEquals(expected, RAPID_HIT.nodeIds());
        var existing = new ArrayList<>(expected.reversed());
        existing.add("destiny:hud_perk_rapid_hit_obsolete");
        existing.add("destiny:hud_ammo_label"); existing.add("destiny:hud_perks_unrelated");
        assertEquals(List.of("destiny:hud_perk_rapid_hit_obsolete"),
                WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(rapid(2, 21)), existing));
        var removed = existing.stream().filter(s -> s.startsWith(WeaponPerkRows.PREFIX)).sorted().toList();
        for (var inactive : List.of(rapid(2, 0), rapid(0, 0), rapid(6, 47), rapid(5, -1),
                snapshot(EnumSet.allOf(WeaponPerkRows.Kind.class))))
            assertEquals(removed, WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(inactive), existing));
        assertTrue(WeaponPerkRows.nodesToRemove(List.of(), removed).stream().allMatch(s -> s.startsWith(WeaponPerkRows.PREFIX)));
        assertTrue(WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(rapid(1, 1)), expected).isEmpty());
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
        assertEquals("W169", manifest.get("stage").getAsString());
        assertEquals("RAPID HIT", manifest.get("label").getAsString());
        assertTrue(manifest.get("provenance").getAsString().contains("not an official Destiny sprite"));
        assertEquals("fcf34b330033e26c06e9bd466bea5a3e4b2f39272972275369beb7d8b257ed57",
                manifest.get("font_sha256").getAsString());
        assertEquals("12.3.0", manifest.get("pillow_version").getAsString());
        assertEquals("2.14.3", manifest.get("freetype_version").getAsString());
        var pack = manifest.getAsJsonObject("pack_files");
        assertEquals(Set.of(TEXTURE.toString(), MODEL.toString(), ITEM.toString()), pack.keySet());
        long bytes = 0;
        for (var entry : pack.entrySet()) {
            byte[] data = Files.readAllBytes(Path.of(entry.getKey())); bytes += data.length;
            assertEquals(entry.getValue().getAsString(), sha(data));
        }
        assertEquals(bytes, manifest.get("pack_bytes").getAsLong()); assertTrue(bytes <= 16384);
        var source = ART.resolve("rapid-hit.svg");
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
            assertEquals(Set.of("rapid-hit.svg", "manifest.json"),
                    paths.map(p -> p.getFileName().toString()).collect(Collectors.toSet()));
        }
    }

    @Test void pngAndSelfContainedSvgDecodeToIdenticalUnclippedWhiteCoverage() throws Exception {
        var image = ImageIO.read(TEXTURE.toFile()); assertNotNull(image);
        assertEquals(118, image.getWidth()); assertEquals(24, image.getHeight());
        var factory = DocumentBuilderFactory.newInstance();
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        var svg = factory.newDocumentBuilder().parse(ART.resolve("rapid-hit.svg").toFile());
        assertEquals("118", svg.getDocumentElement().getAttribute("width"));
        assertEquals("24", svg.getDocumentElement().getAttribute("height"));
        assertEquals("RAPID HIT - original W169 generated label", svg.getElementsByTagName("title").item(0).getTextContent());
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
