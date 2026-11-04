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

/** Live-state projection and actual 26.3 asset parsers; no runtime adapter or framebuffer claim. */
class MultikillClipHudW165Test {
    private static final String NAME = "perk_multikill_clip_w165";
    private static final Path ASSETS = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/weapons/w165/hud/multikill_clip");
    private static final Path TEXTURE = ASSETS.resolve("textures/item/hud/" + NAME + ".png");
    private static final Path MODEL = ASSETS.resolve("models/gui/hud/" + NAME + ".json");
    private static final Path ITEM = ASSETS.resolve("items/gui/hud/" + NAME + ".json");
    private static final List<WeaponPerkRows.Kind> PRIORITY = List.of(
            MEMENTO_MORI, HONED_EDGE, KILL_CLIP, MULTIKILL_CLIP, RAMPAGE, ONE_FOR_ALL,
            SURROUNDED, SWASHBUCKLER, OUTLAW, ARCHERS_TEMPO, NO_DISTRACTIONS, FEEDING_FRENZY);

    private static WeaponPerkRows.Snapshot mkc(int stacks, int ticks) {
        return new WeaponPerkRows.Snapshot(0, 0, 0, 0, 0, 0, 0,
                false, 0, 0, 0, false, 0, 0, stacks, ticks);
    }

    private static WeaponPerkRows.Snapshot snapshot(Set<WeaponPerkRows.Kind> active) {
        return new WeaponPerkRows.Snapshot(
                active.contains(KILL_CLIP) ? 99 : 0, active.contains(OUTLAW) ? 87 : 0,
                active.contains(RAMPAGE) ? 3 : 0, active.contains(RAMPAGE) ? 61 : 0,
                active.contains(ARCHERS_TEMPO) ? 43 : 0, active.contains(MEMENTO_MORI) ? 6 : 0,
                active.contains(HONED_EDGE) ? 4 : 0, active.contains(NO_DISTRACTIONS),
                active.contains(FEEDING_FRENZY) ? 5 : 0, active.contains(FEEDING_FRENZY) ? 101 : 0,
                active.contains(ONE_FOR_ALL) ? 199 : 0, active.contains(SURROUNDED),
                active.contains(SWASHBUCKLER) ? 5 : 0, active.contains(SWASHBUCKLER) ? 89 : 0,
                active.contains(MULTIKILL_CLIP) ? 3 : 0, active.contains(MULTIKILL_CLIP) ? 100 : 0);
    }

    @Test void fourteenArgumentSnapshotsDefaultOnlyTheNewFieldsToZero() {
        var old = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89);
        var extended = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 0, 0);
        assertEquals(extended, old);
        assertEquals(0, old.multikillClipStacks());
        assertEquals(0, old.multikillClipTicks());
        assertEquals(WeaponPerkRows.project(extended), WeaponPerkRows.project(old));
        assertEquals(List.of(MEMENTO_MORI, HONED_EDGE, KILL_CLIP, RAMPAGE),
                WeaponPerkRows.project(old).stream().map(WeaponPerkRows.Row::kind).toList());
    }

    @Test void everyValidStackHasItsActualCountAndFullHundredTickCountdown() {
        for (int stacks = 1; stacks <= 3; stacks++) {
            for (int ticks = 100; ticks >= 1; ticks--) {
                var rows = WeaponPerkRows.project(mkc(stacks, ticks));
                assertEquals(1, rows.size());
                var row = rows.getFirst();
                assertEquals(MULTIKILL_CLIP, row.kind());
                assertEquals(stacks, row.count());
                assertEquals(stacks, row.displayCount());
                assertEquals(ticks, row.ticks());
                assertEquals((ticks + 19) / 20, row.seconds());
                assertEquals(NAME, row.label());
                assertEquals(0, row.slot()); assertEquals(778, row.y());
            }
            assertTrue(WeaponPerkRows.project(mkc(stacks, 0)).isEmpty());
        }
        // Projection does not truncate observed positive time or overflow its ceiling.
        assertEquals(107374183, WeaponPerkRows.project(mkc(1, Integer.MAX_VALUE)).getFirst().seconds());
        // Weaker replacement must immediately show the new state, without a cached maximum.
        WeaponPerkRows.project(mkc(3, 1));
        assertEquals(1, WeaponPerkRows.project(mkc(1, 100)).getFirst().displayCount());
    }

    @Test void invalidCountsAndNonpositiveTimesFailClosedAndFreeTheSlot() {
        for (int stacks : new int[]{Integer.MIN_VALUE, -1, 0, 1, 2, 3, 4, Integer.MAX_VALUE}) {
            for (int ticks : new int[]{Integer.MIN_VALUE, -1, 0, 1, 100, Integer.MAX_VALUE}) {
                boolean valid = stacks >= 1 && stacks <= 3 && ticks > 0;
                assertEquals(valid, !WeaponPerkRows.project(mkc(stacks, ticks)).isEmpty(), stacks + "/" + ticks);
                if (!valid) {
                    var state = new WeaponPerkRows.Snapshot(0, 20, 0, 0, 0, 0, 0,
                            false, 0, 0, 0, false, 0, 0, stacks, ticks);
                    var rows = WeaponPerkRows.project(state);
                    assertEquals(1, rows.size()); assertEquals(OUTLAW, rows.getFirst().kind());
                    assertEquals(0, rows.getFirst().slot());
                }
            }
        }
    }

    @Test void all4096ActivationSetsKeepFourStableContiguousSlotsWithMkcAfterKillClip() {
        for (int mask = 0; mask < (1 << PRIORITY.size()); mask++) {
            var active = EnumSet.noneOf(WeaponPerkRows.Kind.class);
            for (int bit = 0; bit < PRIORITY.size(); bit++)
                if ((mask & (1 << bit)) != 0) active.add(PRIORITY.get(bit));
            var state = snapshot(active);
            var rows = WeaponPerkRows.project(state);
            assertEquals(PRIORITY.stream().filter(active::contains).limit(4).toList(),
                    rows.stream().map(WeaponPerkRows.Row::kind).toList(), "mask " + mask);
            assertEquals(rows, WeaponPerkRows.project(state));
            assertTrue(rows.size() <= 4);
            for (int slot = 0; slot < rows.size(); slot++) {
                assertEquals(slot, rows.get(slot).slot());
                assertEquals(778 - 32 * slot, rows.get(slot).y());
            }
        }
    }

    @Test void expiryStowPreemptionAndUnknownNodesRemoveAllEightMkcNodesDeterministically() {
        var expected = List.of("marker", "label", "x", "count", "minutes", "colon", "tens", "ones")
                .stream().map(s -> "destiny:hud_perk_multikill_clip_" + s).toList();
        assertEquals(WeaponPerkRows.Layout.STACKED_TIMER, MULTIKILL_CLIP.layout);
        assertTrue(MULTIKILL_CLIP.layout.timed()); assertTrue(MULTIKILL_CLIP.layout.counted());
        assertEquals(expected, MULTIKILL_CLIP.nodeIds());
        var existing = new ArrayList<>(expected.reversed());
        existing.add("destiny:hud_perk_multikill_clip_obsolete");
        existing.add("destiny:hud_ammo_label");
        existing.add("destiny:hud_perks_unrelated");
        assertEquals(List.of("destiny:hud_perk_multikill_clip_obsolete"),
                WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(mkc(2, 21)), existing));
        var removed = existing.stream().filter(s -> s.startsWith(WeaponPerkRows.PREFIX)).sorted().toList();
        for (var inactive : List.of(mkc(2, 0), mkc(0, 0), mkc(4, 100)))
            assertEquals(removed, WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(inactive), existing));

        var crowded = EnumSet.allOf(WeaponPerkRows.Kind.class);
        var rows = WeaponPerkRows.project(snapshot(crowded));
        assertEquals(MULTIKILL_CLIP, rows.getLast().kind());
        assertEquals(682, rows.getLast().y());
        crowded.remove(MULTIKILL_CLIP);
        var promoted = WeaponPerkRows.project(snapshot(crowded));
        assertEquals(RAMPAGE, promoted.getLast().kind());
        assertEquals(removed, WeaponPerkRows.nodesToRemove(promoted, existing));
        // MKC also moves up when a preceding row disappears, with unchanged runtime ticks.
        crowded.add(MULTIKILL_CLIP); crowded.remove(KILL_CLIP);
        var moved = WeaponPerkRows.project(snapshot(crowded)).get(2);
        assertEquals(MULTIKILL_CLIP, moved.kind()); assertEquals(100, moved.ticks());
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
        assertEquals("W165", manifest.get("stage").getAsString());
        assertEquals("MULTIKILL CLIP", manifest.get("label").getAsString());
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
        var source = ART.resolve("label-source.svg");
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
            assertEquals(Set.of("label-source.svg", "manifest.json"),
                    paths.map(p -> p.getFileName().toString()).collect(Collectors.toSet()));
        }
    }

    @Test void pngAndSelfContainedSvgDecodeToIdenticalUnclippedWhiteCoverage() throws Exception {
        var image = ImageIO.read(TEXTURE.toFile()); assertNotNull(image);
        assertEquals(118, image.getWidth()); assertEquals(24, image.getHeight());
        var factory = DocumentBuilderFactory.newInstance();
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        var svg = factory.newDocumentBuilder().parse(ART.resolve("label-source.svg").toFile());
        assertEquals("118", svg.getDocumentElement().getAttribute("width"));
        assertEquals("24", svg.getDocumentElement().getAttribute("height"));
        assertEquals("MULTIKILL CLIP - original W165 generated label", svg.getElementsByTagName("title").item(0).getTextContent());
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
