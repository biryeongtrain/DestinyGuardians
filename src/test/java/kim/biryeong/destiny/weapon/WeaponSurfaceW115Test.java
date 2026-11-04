package kim.biryeong.destiny.weapon;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.ResourcePackBuilder;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;

import static org.junit.jupiter.api.Assertions.*;

/** Pack conversion and asset regressions, not a claim of subjective/native visual fidelity. */
class WeaponSurfaceW115Test {
    private static final Path RES = Path.of("src/main/resources");
    private static final String MODEL = "assets/destiny/models/";
    private static JsonObject json(String path) throws IOException {
        return JsonParser.parseString(Files.readString(RES.resolve(path))).getAsJsonObject();
    }
    private static String read(String path) throws IOException { return Files.readString(RES.resolve(path)); }

    @Test void manifestHasExactlyTwoWholeBodiesAndFiveNamedMovingParts() {
        var rules = WeaponSurfaceAssets.rules();
        assertEquals(7, rules.size());
        assertEquals(WeaponSurfaceAssets.TARGETS, rules.keySet());
        assertEquals(7, rules.values().stream().map(WeaponSurfaceAssets.Rule::replacementPath).distinct().count());
        assertThrows(UnsupportedOperationException.class, rules::clear);
    }

    @Test void exactHistoricalInputsAreConvertedAndSourceFilesAreNotModified() throws IOException {
        var rules = WeaponSurfaceAssets.rules();
        for (String path : rules.keySet()) {
            String source = read(path); var rule = rules.get(path);
            assertEquals(rule.sourceSha256(), WeaponSurfaceAssets.sha256(source));
            var out = WeaponSurfaceAssets.convert(path, PackResource.fromString(source), rules);
            assertEquals(rule.replacement(), out.asString());
            assertNotEquals(source, out.asString());
            assertEquals(source, read(path));
        }
    }

    @Test void repeatedOutputConversionReturnsTheSameResourceWithoutChangingBytes() throws IOException {
        var rules = WeaponSurfaceAssets.rules();
        for (String path : rules.keySet()) {
            var once = WeaponSurfaceAssets.convert(path, PackResource.fromString(read(path)), rules);
            assertSame(once, WeaponSurfaceAssets.convert(path, once, rules));
        }
    }

    @Test void unrelatedPathsAreNotReadOrRewritten() {
        var unreadable = new PackResource() {
            public byte[] readAllBytes() { throw new AssertionError("Unrelated resource read"); }
            public java.io.InputStream getStream() { throw new AssertionError("Unrelated resource opened"); }
        };
        for (String path : List.of(MODEL+"weapon/pulse_rifle/chattering_bone.json",
                MODEL+"weapon/pulse_rifle/blast_furnace.json.bak",
                MODEL+"weapon_aim_w70/blast_furnace_00_native.json",
                "overlays/"+MODEL+"weapon/machine_gun/hammerhead.json",
                "assets/other/models/weapon/machine_gun/hammerhead.json",
                "assets/destiny/sounds.json"))
            assertSame(unreadable, WeaponSurfaceAssets.convert(path, unreadable, Map.of()));
    }

    @Test void unknownMissingOrChangedInputsAndRulesFailClosed() throws IOException {
        var rules = WeaponSurfaceAssets.rules();
        for (String path : rules.keySet()) {
            assertThrows(IllegalStateException.class, () -> WeaponSurfaceAssets.convert(path, null, rules));
            assertThrows(IllegalStateException.class, () -> WeaponSurfaceAssets.convert(path, PackResource.fromString(read(path)), Map.of()));
            for (String bad : List.of("", "{}", read(path)+"\n", rules.get(path).replacement()+"\n"))
                assertThrows(IllegalStateException.class, () -> WeaponSurfaceAssets.convert(path, PackResource.fromString(bad), rules));
        }
    }

    @Test void forgedReplacementBytesCannotPassThroughAMatchingManifestField() throws IOException {
        var rules = WeaponSurfaceAssets.rules();
        var path = rules.keySet().iterator().next(); var rule = rules.get(path);
        var bad = new WeaponSurfaceAssets.Rule(rule.sourceSha256(), rule.replacementSha256(), rule.replacementPath(), rule.replacement()+" ");
        assertThrows(IllegalStateException.class, () -> WeaponSurfaceAssets.convert(path, PackResource.fromString(read(path)), Map.of(path, bad)));
    }

    @Test void malformedMissingDuplicateForeignAndCrossPartManifestRulesAreRejected() throws IOException {
        String source = read(WeaponSurfaceAssets.MANIFEST);
        assertThrows(IllegalStateException.class, () -> WeaponSurfaceAssets.parseRules("{}"));
        for (String field : List.of("schema", "stage", "targets")) {
            var bad = JsonParser.parseString(source).getAsJsonObject(); bad.remove(field);
            assertThrows(RuntimeException.class, () -> WeaponSurfaceAssets.parseRules(bad.toString()));
        }
        var missing = JsonParser.parseString(source).getAsJsonObject(); missing.getAsJsonArray("targets").remove(0);
        assertThrows(IllegalStateException.class, () -> WeaponSurfaceAssets.parseRules(missing.toString()));
        var duplicate = JsonParser.parseString(source).getAsJsonObject(); duplicate.getAsJsonArray("targets").add(duplicate.getAsJsonArray("targets").get(0).deepCopy());
        assertThrows(IllegalStateException.class, () -> WeaponSurfaceAssets.parseRules(duplicate.toString()));
        for (String field : List.of("path", "replacement", "sourceSha256", "replacementSha256")) {
            var bad = JsonParser.parseString(source).getAsJsonObject();
            bad.getAsJsonArray("targets").get(0).getAsJsonObject().addProperty(field, "../foreign");
            assertThrows(IllegalStateException.class, () -> WeaponSurfaceAssets.parseRules(bad.toString()));
        }
        var swapped = JsonParser.parseString(source).getAsJsonObject();
        swapped.getAsJsonArray("targets").get(0).getAsJsonObject().addProperty("replacement", "assets/destiny/models/weapon_surface_w115/blast_furnace_magazine.json");
        assertThrows(IllegalStateException.class, () -> WeaponSurfaceAssets.parseRules(swapped.toString()));
    }

    @Test void existingDisplayAndNonGeometryMetadataRemainExact() throws IOException {
        for (var row : WeaponSurfaceAssets.rules().entrySet()) {
            var before = json(row.getKey()); var after = JsonParser.parseString(row.getValue().replacement()).getAsJsonObject();
            for (String key : List.of("elements", "textures", "credit")) { before.remove(key); after.remove(key); }
            assertEquals(before, after, row.getKey()+" keeps native/left/third/GUI display and lighting unchanged");
        }
    }

    @Test void fullGeometryIsExactlyTheDisjointNamedBodyMagazineAndCoverAssembly() throws IOException {
        for (String id : List.of("blast_furnace", "hammerhead")) {
            var full = json(MODEL+"weapon_surface_w115/"+id+".json");
            var expected = new com.google.gson.JsonArray(); var names = new HashSet<String>();
            for (String part : id.equals("hammerhead") ? List.of("body", "magazine", "cover") : List.of("body", "magazine")) {
                var model = json(MODEL+"weapon_surface_w115/"+id+"_"+part+".json");
                assertEquals(full.get("textures"), model.get("textures"));
                assertFalse(model.has("parent")); assertFalse(model.has("display"));
                assertFalse(model.getAsJsonArray("elements").isEmpty());
                for (var e : model.getAsJsonArray("elements")) {
                    assertTrue(names.add(e.getAsJsonObject().get("name").getAsString()), "No duplicate semantic parts");
                    expected.add(e);
                }
            }
            assertEquals(expected, full.get("elements"));
            assertTrue(expected.size() >= 200 && expected.size() <= 2048, "Source-faithful detail; never the rejected 71/86-box simplification");
            int faces=0; for(var e:expected) faces+=e.getAsJsonObject().getAsJsonObject("faces").size();
            var revisions=json(WeaponSurfaceAssets.MANIFEST).getAsJsonObject("artRevisions");
            int revision=revisions==null ? 2 : revisions.get(id).getAsInt();
            assertTrue(Set.of(2,3,4,5).contains(revision), "Unknown art review must not inherit a budget");
            int budget=revision == 5 || id.equals("hammerhead") && Set.of(3,4).contains(revision) ? 6144 : 4608;
            assertTrue(faces <= budget, "Reviewed emitted face budget, not an engine limit or runtime performance guarantee");
        }
    }

    @Test void materialTexturesAndUvIslandsContainRealSurfaceOpacity() throws IOException {
        for (String id : List.of("blast_furnace", "hammerhead")) {
            var image = ImageIO.read(RES.resolve("assets/destiny/textures/item/weapon/w115/"+id+".png").toFile());
            assertNotNull(image); assertTrue(Set.of(256, 512, 1024).contains(image.getWidth())); assertEquals(image.getWidth(), image.getHeight());
            var model = json(MODEL+"weapon_surface_w115/"+id+".json");
            assertEquals("destiny:item/weapon/w115/"+id, model.getAsJsonObject("textures").get("0").getAsString());
            for (var e : model.getAsJsonArray("elements")) {
                var cube = e.getAsJsonObject();
                for (int axis=0;axis<3;axis++) {
                    double lo=cube.getAsJsonArray("from").get(axis).getAsDouble(),hi=cube.getAsJsonArray("to").get(axis).getAsDouble();
                    assertTrue(Double.isFinite(lo) && Double.isFinite(hi) && hi>=lo);
                    assertTrue(lo>=-16 && hi<=32, "Native unrotated cuboid bound");
                }
                int dimensions=0;
                for(int axis=0;axis<3;axis++) if(cube.getAsJsonArray("to").get(axis).getAsDouble()>cube.getAsJsonArray("from").get(axis).getAsDouble()) dimensions++;
                assertTrue(dimensions>=2, "No line/point elements");
                int faceCount=cube.getAsJsonObject("faces").size();
                assertTrue(faceCount>=1 && faceCount<=6);
                if(dimensions==2) assertTrue(faceCount>=2,"Contour plane keeps both sides; only covered solid faces may be omitted");
                for (var face : cube.getAsJsonObject("faces").entrySet()) {
                    var f=face.getValue().getAsJsonObject(); assertEquals("#0",f.get("texture").getAsString());
                    for (var uv:f.getAsJsonArray("uv")) assertTrue(uv.getAsDouble()>=0 && uv.getAsDouble()<=16);
                    var uv=f.getAsJsonArray("uv");
                    // R2 contour planes intentionally mask off rectangle corners; the rectangle
                    // center need not belong to the source polygon. Scan the actual UV island.
                    int left=(int)Math.floor(Math.min(uv.get(0).getAsDouble(),uv.get(2).getAsDouble())/16*image.getWidth());
                    int right=(int)Math.ceil(Math.max(uv.get(0).getAsDouble(),uv.get(2).getAsDouble())/16*image.getWidth());
                    int top=(int)Math.floor(Math.min(uv.get(1).getAsDouble(),uv.get(3).getAsDouble())/16*image.getHeight());
                    int bottom=(int)Math.ceil(Math.max(uv.get(1).getAsDouble(),uv.get(3).getAsDouble())/16*image.getHeight());
                    boolean opaque=false;
                    for(int y=top;y<Math.min(bottom,image.getHeight());y++) for(int x=left;x<Math.min(right,image.getWidth());x++) {
                        int alpha=image.getRGB(x,y)>>>24;
                        assertTrue(alpha==0 || alpha==255,"Native cutout uses binary alpha, not translucent overdraw");
                        opaque|=alpha==255;
                    }
                    assertTrue(opaque,"Every emitted UV island must contain visible source surface: "+cube.get("name"));
                }
            }
        }
    }

    @Test void callbackDefersSourceValidationThenTransformsEveryEmittedTarget() throws IOException {
        var fixture = new BuilderFixture(); WeaponSurfaceAssets.configure(fixture.builder);
        assertEquals(1,fixture.converters.size());assertEquals(1,fixture.tasks.size());assertTrue(fixture.resources.isEmpty());
        for (String path:WeaponSurfaceAssets.TARGETS) fixture.resources.put(path,PackResource.fromString(read(path)));
        fixture.tasks.getFirst().accept(fixture.builder);
        for (String path:WeaponSurfaceAssets.TARGETS) {
            var out=fixture.converters.getFirst().convert(path,fixture.resources.get(path));
            assertEquals(WeaponSurfaceAssets.rules().get(path).replacement(),out.asString());
            fixture.resources.put(path,out);
        }
        fixture.tasks.getFirst().accept(fixture.builder);
    }

    @Test void prefinishRejectsMissingOrOverriddenSourcesWithoutWritingAnyModel() throws IOException {
        var fixture=new BuilderFixture(); var rules=WeaponSurfaceAssets.rules();
        assertThrows(IllegalStateException.class,()->WeaponSurfaceAssets.prepare(fixture.builder,rules));
        for (String path:WeaponSurfaceAssets.TARGETS)fixture.resources.put(path,PackResource.fromString(read(path)));
        String changed=WeaponSurfaceAssets.TARGETS.iterator().next();fixture.resources.put(changed,PackResource.fromString("unreviewed override"));
        assertThrows(IllegalStateException.class,()->WeaponSurfaceAssets.prepare(fixture.builder,rules));
        assertEquals("unreviewed override",fixture.resources.get(changed).asString());
    }

    @Test void everyExistingAimGripInspectAndReloadPoseResolvesToExactlyOneReplacedGeometry() throws IOException {
        var roots = WeaponSurfaceAssets.TARGETS;
        int poses = 0, sightPoses = 0, sightBodies = 0;
        try (var paths = Files.walk(RES.resolve(MODEL))) {
            for (Path path : paths.filter(Files::isRegularFile).filter(p -> p.toString().endsWith(".json")).toList()) {
                String relative = RES.relativize(path).toString();
                // W123 replacement roots are a separate migration, not inherited W115 poses.
                if (relative.contains("weapon_surface_w115") || relative.contains("weapon_surface_w123")
                        || relative.contains("gui/hud")) continue;
                if (!path.getFileName().toString().startsWith("blast_furnace") && !path.getFileName().toString().startsWith("hammerhead")) continue;
                if (roots.contains(relative)) continue;
                // W151/W152 explicitly bake CURRENT W123 geometry for ADS, including the magazine once.
                if (relative.matches(MODEL + "weapon_sight_w151/(blast_furnace|hammerhead)_body\\.json")) {
                    reviewedSightBody(relative); sightBodies++; continue;
                }
                if (relative.startsWith(MODEL + "weapon_sight_w151/")) {
                    assertTrue(relative.matches(MODEL + "weapon_sight_w151/(blast_furnace|hammerhead)_[0-9]{2}_(native|twohand)\\.json"), relative);
                    String id = path.getFileName().toString().startsWith("blast_furnace") ? "blast_furnace" : "hammerhead";
                    var child = json(relative);
                    assertEquals(Set.of("parent", "display"), child.keySet());
                    String expectedParent = path.getFileName().toString().contains("_00_")
                            ? "destiny:weapon/" + (id.equals("hammerhead") ? "machine_gun/" : "pulse_rifle/") + id
                            : "destiny:weapon_sight_w151/" + id + "_body";
                    assertEquals(expectedParent, child.get("parent").getAsString());
                    reviewedSightBody(MODEL + "weapon_sight_w151/" + id + "_body.json");
                    sightPoses++; continue;
                }
                // W207 explicitly starts from the reviewed current W123 split geometry.
                // The historical W115 migration invariant does not apply to these new banks.
                if (relative.startsWith(MODEL + "weapon_reload_w207_blast_furnace/")
                        || relative.startsWith(MODEL + "weapon_reload_w207_hammerhead/")) {
                    var current = json(relative);
                    if (current.has("elements")) {
                        String name=path.getFileName().toString();
                        var source=json(MODEL+"weapon_surface_w123/"+name);
                        assertEquals(source.get("elements"),current.get("elements"),relative);
                        assertEquals(source.get("textures"),current.get("textures"),relative);
                    } else {
                        assertEquals(Set.of("parent","display"),current.keySet());
                        String parent=current.get("parent").getAsString();
                        assertTrue(parent.startsWith("destiny:weapon_reload_w207_"));
                        String source=parent.replace("destiny:weapon_reload_w207_blast_furnace/",MODEL+"weapon_surface_w123/")
                                .replace("destiny:weapon_reload_w207_hammerhead/",MODEL+"weapon_surface_w123/")+".json";
                        assertTrue(Files.isRegularFile(RES.resolve(source)),source);
                    }
                    continue;
                }
                var seen = new HashSet<String>();
                String next = relative;
                while (!roots.contains(next)) {
                    assertTrue(seen.add(next), "No cyclic parent chain: " + relative);
                    var model = json(next);
                    assertFalse(model.has("elements"), "No stale baked source geometry: " + next);
                    assertTrue(model.has("parent"), next);
                    String parent = model.get("parent").getAsString();
                    assertTrue(parent.startsWith("destiny:"));
                    next = MODEL + parent.substring("destiny:".length()) + ".json";
                }
                poses++;
            }
        }
        assertEquals(304, poses, "84 aim + 10 static variants + 210 moving-part poses inherit the seven replacements");
        assertEquals(2, sightBodies, "Only the reviewed W151 current-W123 baked roots");
        assertEquals(84, sightPoses, "21 samples times two carriers for each reviewed sight body");
    }

    private static void reviewedSightBody(String path) throws IOException {
        String id = path.contains("blast_furnace") ? "blast_furnace" : "hammerhead";
        var manifest = JsonParser.parseString(Files.readString(Path.of("art/weapons/w151/pulse-sights.json"))).getAsJsonObject();
        var rows = manifest.getAsJsonArray("weapons").asList().stream().map(e -> e.getAsJsonObject())
                .filter(e -> e.get("id").getAsString().equals(id)).toList();
        assertEquals(1, rows.size()); var row = rows.getFirst();
        String sourcePath = "src/main/resources/" + MODEL + "weapon_surface_w123/" + id + ".json";
        assertEquals(sourcePath, row.get("source").getAsString());
        assertEquals(row.get("sourceSha256").getAsString(), WeaponSurfaceAssets.sha256(Files.readString(Path.of(sourcePath))));
        assertEquals("weapon_sight_w151/" + id + "_body", row.get("body").getAsString());
        assertTrue(row.getAsJsonArray("removedSightNames").isEmpty());
        var source = json(MODEL + "weapon_surface_w123/" + id + ".json");
        var body = json(path); assertFalse(body.has("parent")); assertFalse(body.has("display"));
        var original = source.getAsJsonArray("elements"); var actual = body.getAsJsonArray("elements");
        assertEquals(row.get("sourceElementCount").getAsInt(), original.size());
        assertEquals(original.size() + 2, actual.size());
        assertEquals(row.get("elementCount").getAsInt(), actual.size());
        for (int i = 0; i < original.size(); i++) assertEquals(original.get(i), actual.get(i), "Current W123 element/UV order preserved");
        assertEquals(Set.of("w151_front_pin_stem", "w151_front_pin_tip"),
                Set.of(actual.get(original.size()).getAsJsonObject().get("name").getAsString(),
                        actual.get(original.size() + 1).getAsJsonObject().get("name").getAsString()));
        var textures = source.getAsJsonObject("textures").deepCopy();
        textures.addProperty("sight", "destiny:item/weapon/w148/sights");
        assertEquals(textures, body.get("textures"));
        assertEquals(row.get("sightTextureSha256").getAsString(),
                shaBytes(RES.resolve("assets/destiny/textures/item/weapon/w148/sights.png")));
    }

    private static String shaBytes(Path path) throws IOException {
        try { return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))); }
        catch (java.security.NoSuchAlgorithmException e) { throw new AssertionError(e); }
    }

    private static final class BuilderFixture {
        final Map<String,PackResource> resources=new HashMap<>();
        final List<ResourcePackBuilder.ResourceConverter> converters=new ArrayList<>();
        final List<Consumer<ResourcePackBuilder>> tasks=new ArrayList<>();
        final ResourcePackBuilder builder=(ResourcePackBuilder)Proxy.newProxyInstance(ResourcePackBuilder.class.getClassLoader(),new Class<?>[]{ResourcePackBuilder.class},
                (proxy,method,args)->switch(method.getName()) {
                    case "getResource"->resources.get((String)args[0]);
                    case "addResourceConverter"->{converters.add((ResourcePackBuilder.ResourceConverter)args[0]);yield null;}
                    case "addPreFinishTask"->{@SuppressWarnings("unchecked")var task=(Consumer<ResourcePackBuilder>)args[0];tasks.add(task);yield null;}
                    default->throw new AssertionError("Unexpected mutation/API: "+method);
                });
    }
}
