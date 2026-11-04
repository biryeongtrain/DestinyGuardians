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

/** W173 projection boundaries, source compatibility, and real Minecraft 26.3 asset codecs. */
class AdrenalineJunkieHudW173Test {
    private static final String NAME = "perk_adrenaline_junkie_w173";
    private static final Path ASSETS = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/hud/w173");
    private static final Path TEXTURE = ASSETS.resolve("textures/item/hud/" + NAME + ".png");
    private static final Path MODEL = ASSETS.resolve("models/gui/hud/" + NAME + ".json");
    private static final Path ITEM = ASSETS.resolve("items/gui/hud/" + NAME + ".json");
    private static final List<WeaponPerkRows.Kind> PREFIX = List.of(
            MEMENTO_MORI, HONED_EDGE, KILL_CLIP, MULTIKILL_CLIP, RAMPAGE, ONE_FOR_ALL,
            SURROUNDED, SWASHBUCKLER, OUTLAW, ARCHERS_TEMPO, NO_DISTRACTIONS,
            RAPID_HIT, FEEDING_FRENZY, PERPETUAL_MOTION, TAP_THE_TRIGGER, FRENZY);

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
                active.contains(RAPID_HIT) ? 5 : 0, active.contains(RAPID_HIT) ? 47 : 0,
                active.contains(PERPETUAL_MOTION) ? 2 : 0,
                active.contains(TAP_THE_TRIGGER) ? 12 : 0, active.contains(FRENZY) ? 144 : 0, stacks, ticks);
    }

    private static WeaponPerkRows.Snapshot aj(int stacks, int ticks) {
        return snapshot(Set.of(), stacks, ticks);
    }

    @Test void allSixLegacyConstructorAritiesCompilePreserveFieldsAndZeroBothNewFields() throws Exception {
        // Real source calls catch constructor removals that reflection-only checks would miss.
        var old14 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89);
        var old16 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89, 2, 73);
        var old18 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39);
        var old19 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 2);
        var old20 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 2, 12);
        var old21 = new WeaponPerkRows.Snapshot(99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 2, 12, 144);
        Object[] values = {99, 87, 3, 61, 43, 6, 4, true, 5, 101, 199, true, 5, 89, 2, 73, 4, 39, 2, 12, 144, 0};
        var components = java.util.Arrays.copyOf(WeaponPerkRows.Snapshot.class.getRecordComponents(), 28);
        assertEquals(28, components.length);
        assertEquals("frenzyTicks", components[20].getName());
        assertEquals("adrenalineJunkieStacks", components[21].getName());
        assertEquals("adrenalineJunkieTicks", components[22].getName());
        assertEquals(int.class, components[21].getType()); assertEquals(int.class, components[22].getType());
        var states = List.of(old14, old16, old18, old19, old20, old21);
        int[] arities = {14, 16, 18, 19, 20, 21};
        for (int n = 0; n < states.size(); n++) {
            var state = states.get(n);
            for (int i = 0; i < components.length; i++)
                assertEquals(i < arities[n] ? values[i] : 0, components[i].getAccessor().invoke(state),
                        "arity " + arities[n] + " field " + components[i].getName());
            assertEquals(0, state.adrenalineJunkieStacks()); assertEquals(0, state.adrenalineJunkieTicks());
            assertTrue(WeaponPerkRows.project(state).stream().noneMatch(r -> r.kind() == ADRENALINE_JUNKIE));
        }
        assertEquals(Set.of(14, 16, 18, 19, 20, 21, 23, 24, 25, 27, 28, 29, 35, 38, 40), java.util.Arrays.stream(
                WeaponPerkRows.Snapshot.class.getDeclaredConstructors()).map(c -> c.getParameterCount()).collect(Collectors.toSet()));
    }

    @Test void everyValidStackTickPairShowsObservedCountAndCeilOneThroughFiveSeconds() {
        for (int count = 1; count <= 5; count++) for (int ticks = 1; ticks <= 90; ticks++) {
            var state = aj(count, ticks);
            var rows = WeaponPerkRows.project(state); assertEquals(1, rows.size());
            var row = rows.getFirst();
            assertEquals(ADRENALINE_JUNKIE, row.kind()); assertEquals(NAME, row.label());
            assertEquals(count, row.count()); assertEquals(count, row.displayCount());
            assertEquals(ticks, row.ticks()); assertEquals((ticks + 19) / 20, row.seconds());
            assertTrue(row.seconds() >= 1 && row.seconds() <= 5);
            assertEquals(0, row.slot()); assertEquals(778, row.y());
            assertEquals(rows, WeaponPerkRows.project(state));
            assertThrows(UnsupportedOperationException.class, rows::clear);
        }
        assertThrows(NullPointerException.class, () -> WeaponPerkRows.project(null));
    }

    @Test void inconsistentOutOfBoundsAndOverflowInputsHideWithoutClamping() {
        int[] counts = {Integer.MIN_VALUE, -1, 0, 1, 2, 5, 6, 90, Integer.MAX_VALUE};
        int[] durations = {Integer.MIN_VALUE, -90, -1, 0, 1, 20, 21, 80, 81, 90, 91, 100, Integer.MAX_VALUE};
        for (int count : counts) for (int ticks : durations) {
            boolean valid = count >= 1 && count <= 5 && ticks >= 1 && ticks <= 90;
            assertEquals(valid ? 1 : 0, WeaponPerkRows.project(aj(count, ticks)).size(), count + "/" + ticks);
        }
        for (var kind : PREFIX) {
            var rows = WeaponPerkRows.project(snapshot(Set.of(kind), 0, 0));
            assertEquals(List.of(kind), rows.stream().map(WeaponPerkRows.Row::kind).toList());
        }
        var independent = aj(2, 7); var expected = WeaponPerkRows.project(independent);
        for (int ticks : durations) {
            WeaponPerkRows.project(snapshot(EnumSet.allOf(WeaponPerkRows.Kind.class), 5, ticks));
            assertEquals(expected, WeaponPerkRows.project(independent));
            assertEquals(2, independent.adrenalineJunkieStacks()); assertEquals(7, independent.adrenalineJunkieTicks());
        }
    }

    @Test void seventeenthKindPreservesSixteenKindPrefixAndFourRowCapForEveryOlderSubset() {
        assertTrue(WeaponPerkRows.Kind.values().length >= 21);
        assertEquals(PREFIX, List.of(WeaponPerkRows.Kind.values()).subList(0, 16));
        assertEquals(16, ADRENALINE_JUNKIE.ordinal()); assertEquals(4, WeaponPerkRows.MAX_ROWS);
        for (int mask = 0; mask < (1 << PREFIX.size()); mask++) {
            var active = EnumSet.noneOf(WeaponPerkRows.Kind.class);
            for (int bit = 0; bit < PREFIX.size(); bit++) if ((mask & (1 << bit)) != 0) active.add(PREFIX.get(bit));
            var before = WeaponPerkRows.project(snapshot(active, 0, 0));
            var after = WeaponPerkRows.project(snapshot(active, 5, 90));
            var expected = new ArrayList<>(PREFIX.stream().filter(active::contains).toList());
            expected.add(ADRENALINE_JUNKIE);
            assertEquals(expected.stream().limit(4).toList(), after.stream().map(WeaponPerkRows.Row::kind).toList());
            assertEquals(before, after.stream().filter(r -> r.kind() != ADRENALINE_JUNKIE).toList());
            for (int slot = 0; slot < after.size(); slot++) {
                assertEquals(slot, after.get(slot).slot()); assertEquals(778 - 32 * slot, after.get(slot).y());
            }
        }
    }

    @Test void hiddenBuffPromotesAtCurrentCountAndTicksThenExpiresAndCleansEveryNode() {
        var crowded = EnumSet.of(OUTLAW, RAPID_HIT, FEEDING_FRENZY, FRENZY);
        assertTrue(WeaponPerkRows.project(snapshot(crowded, 5, 90)).stream().noneMatch(r -> r.kind() == ADRENALINE_JUNKIE));
        crowded.remove(OUTLAW);
        var rows = WeaponPerkRows.project(snapshot(crowded, 3, 21));
        var promoted = rows.getLast();
        assertEquals(ADRENALINE_JUNKIE, promoted.kind()); assertEquals(3, promoted.count());
        assertEquals(21, promoted.ticks()); assertEquals(2, promoted.seconds());
        assertEquals(3, promoted.slot()); assertEquals(682, promoted.y());
        assertEquals(FRENZY, WeaponPerkRows.project(snapshot(crowded, 3, 0)).getLast().kind());
        assertEquals(ADRENALINE_JUNKIE.nodeIds().stream().sorted().toList(), WeaponPerkRows.nodesToRemove(
                WeaponPerkRows.project(snapshot(crowded, 3, 0)), ADRENALINE_JUNKIE.nodeIds()));
    }

    @Test void countTimerHasExactlyEightStableUniqueNodesAndReconcilesStaleSuffixes() {
        var suffixes = List.of("marker", "label", "x", "count", "minutes", "colon", "tens", "ones");
        var expected = suffixes.stream().map(s -> "destiny:hud_perk_adrenaline_junkie_" + s).toList();
        assertEquals(WeaponPerkRows.Layout.COUNT_TIMER, ADRENALINE_JUNKIE.layout);
        assertTrue(ADRENALINE_JUNKIE.layout.timed()); assertTrue(ADRENALINE_JUNKIE.layout.counted());
        assertEquals(expected, ADRENALINE_JUNKIE.nodeIds());
        var existing = new ArrayList<>(expected.reversed()); existing.add(ADRENALINE_JUNKIE.nodeId("unknown"));
        existing.add("destiny:hud_ammo_label"); existing.add("destiny:hud_perks_unrelated");
        for (int count = 1; count <= 5; count++) for (int ticks : new int[]{1, 20, 21, 80, 81, 90})
            assertEquals(List.of(ADRENALINE_JUNKIE.nodeId("unknown")),
                    WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(aj(count, ticks)), existing));
        var all = existing.stream().filter(s -> s.startsWith(WeaponPerkRows.PREFIX)).sorted().toList();
        for (var state : List.of(aj(0, 90), aj(5, 0), aj(6, 90), aj(5, 91), snapshot(EnumSet.allOf(WeaponPerkRows.Kind.class), 5, 90)))
            assertEquals(all, WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(state), existing));
        assertEquals(all, WeaponPerkRows.nodesToRemove(List.of(), existing));
        var nodes = java.util.Arrays.stream(WeaponPerkRows.Kind.values()).flatMap(k -> k.nodeIds().stream()).toList();
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
                .idToFile(Identifier.parse("destiny:gui/hud/w173_missing_control")))));

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
        assertEquals("W173", manifest.get("stage").getAsString());
        assertEquals("ADRENALINE JUNKIE", manifest.get("label").getAsString());
        assertTrue(manifest.get("provenance").getAsString().contains("not an official Destiny sprite"));
        assertEquals("fcf34b330033e26c06e9bd466bea5a3e4b2f39272972275369beb7d8b257ed57",
                manifest.get("font_sha256").getAsString());
        assertEquals("12.3.0", manifest.get("pillow_version").getAsString());
        assertEquals("2.14.3", manifest.get("freetype_version").getAsString());
        var contract = manifest.getAsJsonObject("runtime_contract");
        assertEquals("COUNT_TIMER", contract.get("layout").getAsString());
        assertEquals(JsonParser.parseString("[1,90]"), contract.get("valid_ticks"));
        assertEquals(JsonParser.parseString("[1,5]"), contract.get("valid_stacks"));
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
        var source = ART.resolve("adrenaline-junkie.svg");
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
            assertEquals(Set.of("adrenaline-junkie.svg", "manifest.json"),
                    paths.map(p -> p.getFileName().toString()).collect(Collectors.toSet()));
        }
    }

    @Test void pngAndSelfContainedSvgDecodeToIdenticalUnclippedWhiteCoverage() throws Exception {
        var image = ImageIO.read(TEXTURE.toFile()); assertNotNull(image);
        assertEquals(118, image.getWidth()); assertEquals(24, image.getHeight());
        var factory = DocumentBuilderFactory.newInstance();
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        var svg = factory.newDocumentBuilder().parse(ART.resolve("adrenaline-junkie.svg").toFile());
        assertEquals("118", svg.getDocumentElement().getAttribute("width"));
        assertEquals("24", svg.getDocumentElement().getAttribute("height"));
        assertEquals("ADRENALINE JUNKIE - original W173 generated label", svg.getElementsByTagName("title").item(0).getTextContent());
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

    private static Path resourcePath(Identifier file) {
        return Path.of("src/main/resources/assets", file.getNamespace(), file.getPath());
    }

    private static void assertClasspathResource(Identifier file, Path source) throws Exception {
        try (var stream = AdrenalineJunkieHudW173Test.class.getResourceAsStream(
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
