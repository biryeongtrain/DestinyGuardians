package kim.biryeong.destiny.hud;

import com.google.gson.JsonObject;
import com.google.gson.JsonParseException;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.resources.FileToIdConverter;
import net.minecraft.resources.Identifier;
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

/** Observed Frenzy ticks and real 26.3 parsers; live adapter integration belongs to master. */
class FrenzyHudW172Test {
    private static final String NAME = "perk_frenzy_w172";
    private static final Path ASSETS = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/hud/w172");
    private static final Path TEXTURE = ASSETS.resolve("textures/item/hud/" + NAME + ".png");
    private static final Path MODEL = ASSETS.resolve("models/gui/hud/" + NAME + ".json");
    private static final Path ITEM = ASSETS.resolve("items/gui/hud/" + NAME + ".json");
    private static final List<WeaponPerkRows.Kind> PRIORITY = List.of(
            MEMENTO_MORI, HONED_EDGE, KILL_CLIP, MULTIKILL_CLIP, RAMPAGE, ONE_FOR_ALL,
            SURROUNDED, SWASHBUCKLER, OUTLAW, ARCHERS_TEMPO, NO_DISTRACTIONS,
            RAPID_HIT, FEEDING_FRENZY, PERPETUAL_MOTION, TAP_THE_TRIGGER);
    private static final List<WeaponPerkRows.Kind> ALL_PRIORITY =
            java.util.stream.Stream.concat(PRIORITY.stream(), java.util.stream.Stream.of(FRENZY)).toList();

    private static WeaponPerkRows.Snapshot frenzy(int ticks) {
        return snapshot(Set.of(), ticks);
    }

    private static WeaponPerkRows.Snapshot snapshot(Set<WeaponPerkRows.Kind> active, int ticks) {
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
                active.contains(TAP_THE_TRIGGER) ? 12 : 0, ticks);
    }

    @Test void allLegacyConstructorsPreserveEveryFieldAndDefaultFrenzyToZero() {
        var old14 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89);
        var old16 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 2, 73);
        var old18 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39);
        var old19 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 2);
        var old20 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 2, 12);
        assertEquals(new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 0, 0, 0, 0, 0, 0, 0), old14);
        assertEquals(new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 2, 73, 0, 0, 0, 0, 0), old16);
        assertEquals(new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 0, 0, 0), old18);
        assertEquals(new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 2, 0, 0), old19);
        assertEquals(new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4,
                true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 2, 12, 0), old20);
        for (var state : List.of(old14, old16, old18, old19, old20)) {
            assertEquals(0, state.frenzyTicks());
            assertTrue(WeaponPerkRows.project(state).stream().noneMatch(r -> r.kind() == FRENZY));
        }
        var components = java.util.Arrays.copyOf(WeaponPerkRows.Snapshot.class.getRecordComponents(), 28);
        assertEquals(28, components.length);
        assertEquals("perpetualMotionStacks", components[18].getName());
        assertEquals("tapTheTriggerTicks", components[19].getName());
        assertEquals("frenzyTicks", components[20].getName());
        assertEquals(int.class, components[20].getType());
    }

    @Test void onlyObservedTicksOneThrough144ProjectWithCeilSecondsOneThroughEight() {
        for (int ticks = 1; ticks <= 144; ticks++) {
            var state = frenzy(ticks);
            var rows = WeaponPerkRows.project(state);
            assertEquals(1, rows.size());
            var row = rows.getFirst();
            assertEquals(FRENZY, row.kind()); assertEquals(NAME, row.label());
            assertEquals(ticks, row.ticks()); assertEquals((ticks + 19) / 20, row.seconds());
            assertEquals(0, row.count()); assertEquals(0, row.displayCount());
            assertEquals(0, row.slot()); assertEquals(778, row.y());
            assertEquals(rows, WeaponPerkRows.project(state));
            assertThrows(UnsupportedOperationException.class, rows::clear);
        }
        for (int invalid : new int[]{Integer.MIN_VALUE, -144, -1, 0, 145, 160, 240, Integer.MAX_VALUE})
            assertTrue(WeaponPerkRows.project(frenzy(invalid)).isEmpty(), "ticks " + invalid);
        assertThrows(NullPointerException.class, () -> WeaponPerkRows.project(null));
    }

    @Test void unrelatedCountdownsOrCountsNeverActivateFrenzyAndProjectionDoesNotCacheOrCount() {
        var earlier = EnumSet.copyOf(ALL_PRIORITY); earlier.remove(FRENZY);
        for (var kind : earlier) {
            var rows = WeaponPerkRows.project(snapshot(Set.of(kind), 0));
            assertEquals(List.of(kind), rows.stream().map(WeaponPerkRows.Row::kind).toList());
        }
        var independent = frenzy(7);
        var expected = WeaponPerkRows.project(independent);
        for (int ticks : new int[]{144, 141, 140, 121, 120, 21, 20, 1, 0, 145, -1}) {
            WeaponPerkRows.project(snapshot(earlier, ticks));
            WeaponPerkRows.project(frenzy(ticks));
            assertEquals(expected, WeaponPerkRows.project(independent));
            assertEquals(7, independent.frenzyTicks());
        }
        assertTrue(WeaponPerkRows.project(frenzy(0)).isEmpty());
    }

    @Test void appendedSixteenthKindKeepsEveryLegacyPriorityAndFourRowCap() {
        assertTrue(WeaponPerkRows.Kind.values().length >= 21);
        assertEquals(PRIORITY, List.of(WeaponPerkRows.Kind.values()).subList(0, 15));
        assertEquals(ALL_PRIORITY, List.of(WeaponPerkRows.Kind.values()).subList(0,16));
        assertEquals(15, FRENZY.ordinal());
        assertEquals(TAP_THE_TRIGGER.ordinal() + 1, FRENZY.ordinal());
        assertEquals(4, WeaponPerkRows.MAX_ROWS);
        // Every subset of all fifteen older kinds retains its original priority.
        var competitors = PRIORITY;
        for (int mask = 0; mask < (1 << competitors.size()); mask++) {
            var active = EnumSet.noneOf(WeaponPerkRows.Kind.class);
            for (int bit = 0; bit < competitors.size(); bit++)
                if ((mask & (1 << bit)) != 0) active.add(competitors.get(bit));
            var rows = WeaponPerkRows.project(snapshot(active, 12));
            active.add(FRENZY);
            assertEquals(ALL_PRIORITY.stream().filter(active::contains).limit(4).toList(),
                    rows.stream().map(WeaponPerkRows.Row::kind).toList());
            assertEquals(WeaponPerkRows.project(snapshot(active, 0)),
                    rows.stream().filter(r -> r.kind() != FRENZY).toList());
            for (int slot = 0; slot < rows.size(); slot++) {
                assertEquals(slot, rows.get(slot).slot());
                assertEquals(778 - 32 * slot, rows.get(slot).y());
            }
        }
        assertEquals(PRIORITY.subList(0, 4), WeaponPerkRows.project(
                snapshot(EnumSet.allOf(WeaponPerkRows.Kind.class), 12)).stream().map(WeaponPerkRows.Row::kind).toList());
    }

    @Test void hiddenFrenzyPromotesWithCurrentTicksThenExpiresWithoutExtendingOrReplacingOldRows() {
        var crowded = EnumSet.of(OUTLAW, RAPID_HIT, FEEDING_FRENZY, PERPETUAL_MOTION);
        assertTrue(WeaponPerkRows.project(snapshot(crowded, 144)).stream().noneMatch(r -> r.kind() == FRENZY));
        crowded.remove(OUTLAW);
        var promoted = WeaponPerkRows.project(snapshot(crowded, 21)).getLast();
        assertEquals(FRENZY, promoted.kind()); assertEquals(3, promoted.slot());
        assertEquals(682, promoted.y()); assertEquals(21, promoted.ticks()); assertEquals(2, promoted.seconds());
        assertEquals(PERPETUAL_MOTION, WeaponPerkRows.project(snapshot(crowded, 0)).getLast().kind());
        assertEquals(PERPETUAL_MOTION, WeaponPerkRows.project(snapshot(crowded, 145)).getLast().kind());
        assertEquals(6, WeaponPerkRows.project(snapshot(Set.of(MEMENTO_MORI), 1)).getFirst().displayCount());
        assertEquals(4, WeaponPerkRows.project(snapshot(Set.of(HONED_EDGE), 1)).getFirst().displayCount());
    }

    @Test void exactlySixTimerNodesKeepMembershipAndCleanupCountsUnknownSuffixesHiddenAndExpiredRows() {
        var suffixes = List.of("marker", "label", "minutes", "colon", "tens", "ones");
        var expected = suffixes.stream().map(s -> "destiny:hud_perk_frenzy_" + s).toList();
        assertEquals(WeaponPerkRows.Layout.TIMER, FRENZY.layout);
        assertTrue(FRENZY.layout.timed()); assertFalse(FRENZY.layout.counted());
        assertEquals(expected, FRENZY.nodeIds());
        var stale = List.of("x", "count", "unknown").stream().map(FRENZY::nodeId).toList();
        var existing = new ArrayList<>(expected.reversed()); existing.addAll(stale);
        existing.add("destiny:hud_ammo_label"); existing.add("destiny:hud_perks_unrelated");
        // Countdown changes only digit content; registry membership stays stable for the full lifetime.
        for (int ticks = 1; ticks <= 144; ticks++) {
            var visible = WeaponPerkRows.project(frenzy(ticks));
            assertEquals(expected, visible.getFirst().kind().nodeIds());
            assertEquals(stale.stream().sorted().toList(), WeaponPerkRows.nodesToRemove(visible, existing));
        }
        var all = existing.stream().filter(s -> s.startsWith(WeaponPerkRows.PREFIX)).sorted().toList();
        for (int invalid : new int[]{Integer.MIN_VALUE, -1, 0, 145, Integer.MAX_VALUE})
            assertEquals(all, WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(frenzy(invalid)), existing));
        assertEquals(all, WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(
                snapshot(EnumSet.allOf(WeaponPerkRows.Kind.class), 12)), existing));
        assertEquals(all, WeaponPerkRows.nodesToRemove(List.of(), existing));
        assertTrue(WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(frenzy(1)), expected).isEmpty());
        var nodes = ALL_PRIORITY.stream().flatMap(k -> k.nodeIds().stream()).toList();
        assertEquals(nodes.size(), Set.copyOf(nodes).size());
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
        var modelId = Identifier.parse(graph.get("model").getAsString());
        var modelFile = FileToIdConverter.json("models").idToFile(modelId);
        assertEquals("destiny", modelFile.getNamespace());
        assertEquals(MODEL, resourcePath(modelFile));
        assertClasspathResource(modelFile, MODEL);
        var textureId = Identifier.parse(json(MODEL).getAsJsonObject("textures").get("0").getAsString());
        var textureFile = new FileToIdConverter("textures", ".png").idToFile(textureId);
        assertEquals(TEXTURE, resourcePath(textureFile));
        assertClasspathResource(textureFile, TEXTURE);
        assertClasspathResource(FileToIdConverter.json("items").idToFile(modelId), ITEM);
        assertFalse(Files.exists(resourcePath(FileToIdConverter.json("models")
                .idToFile(Identifier.parse("destiny:gui/hud/w172_missing_control")))));

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
        assertEquals("W172", manifest.get("stage").getAsString());
        assertEquals("FRENZY", manifest.get("label").getAsString());
        assertTrue(manifest.get("provenance").getAsString().contains("not an official Destiny sprite"));
        assertEquals("fcf34b330033e26c06e9bd466bea5a3e4b2f39272972275369beb7d8b257ed57",
                manifest.get("font_sha256").getAsString());
        assertEquals("12.3.0", manifest.get("pillow_version").getAsString());
        assertEquals("2.14.3", manifest.get("freetype_version").getAsString());
        var contract = manifest.getAsJsonObject("runtime_contract");
        assertEquals("TIMER", contract.get("layout").getAsString());
        assertEquals(JsonParser.parseString("[1,144]"), contract.get("valid_ticks"));
        assertEquals(4, contract.get("max_rows").getAsInt());
        assertTrue(contract.get("activation").getAsString().contains("no manufactured activation or counter"));
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
        var source = ART.resolve("frenzy.svg");
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
            assertEquals(Set.of("frenzy.svg", "manifest.json"),
                    paths.map(p -> p.getFileName().toString()).collect(Collectors.toSet()));
        }
    }

    @Test void pngAndSelfContainedSvgDecodeToIdenticalUnclippedWhiteCoverage() throws Exception {
        var image = ImageIO.read(TEXTURE.toFile()); assertNotNull(image);
        assertEquals(94, image.getWidth()); assertEquals(24, image.getHeight());
        var factory = DocumentBuilderFactory.newInstance();
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        var svg = factory.newDocumentBuilder().parse(ART.resolve("frenzy.svg").toFile());
        assertEquals("94", svg.getDocumentElement().getAttribute("width"));
        assertEquals("24", svg.getDocumentElement().getAttribute("height"));
        assertEquals("FRENZY - original W172 generated label", svg.getElementsByTagName("title").item(0).getTextContent());
        assertEquals(0, svg.getElementsByTagName("image").getLength());
        assertEquals(0, svg.getElementsByTagName("text").getLength());
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

    private static Path resourcePath(Identifier file) {
        return Path.of("src/main/resources/assets", file.getNamespace(), file.getPath());
    }

    private static void assertClasspathResource(Identifier file, Path source) throws Exception {
        try (var stream = FrenzyHudW172Test.class.getResourceAsStream(
                "/assets/" + file.getNamespace() + "/" + file.getPath())) {
            assertNotNull(stream, file.toString());
            assertArrayEquals(Files.readAllBytes(source), stream.readAllBytes());
        }
    }

    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }

    private static String sha(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
}
