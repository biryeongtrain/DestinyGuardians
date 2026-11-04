package kim.biryeong.destiny.hud;

import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.ResourcePackBuilder;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;

import static org.junit.jupiter.api.Assertions.*;

/** Source contracts only; neither GLSL compilation nor native framebuffer acceptance. */
class CriticalHudShaderW96Test {
    private static final String VSH = CriticalHudShader.VERTEX_PATH;
    private static final String FSH = CriticalHudShader.FRAGMENT_PATH;
    private static final String MAIN = "void main() {\n";
    private static final String OUT = "layout(location = 7) flat out int destinyCriticalHud;\n\n";
    private static final String IN = "layout(location = 7) flat in int destinyCriticalHud;\n\n";
    private static final String MARKER =
            "    destinyCriticalHud = (displayhud_is_hud(Position) && all(equal(UV2, ivec2(32, 48)))) ? 1 : 0;\n";
    private static final String ORIGINAL = """
                vec4 color = texture(Sampler0, texCoord0);
                #ifdef ALPHA_CUTOUT
                if (color.a < ALPHA_CUTOUT) {
                    discard;
                }
                #endif
            """;
    private static final String REPAIRED = """
                vec4 color = texture(Sampler0, texCoord0);
                if (destinyCriticalHud == 1) {
                    // True transparency must not contribute depth, including OIT_ALPHA_ONLY.
                    if (color.a == 0.0) {
                        discard;
                    }
                } else {
                #ifdef ALPHA_CUTOUT
                if (color.a < ALPHA_CUTOUT) {
                    discard;
                }
                #endif
                }
            """;

    @Test
    void exactInstalledTemplateAndVanillaTransformOnlyTheIntendedSourceSpans() throws IOException {
        String vertex = vertex(), fragment = fragment();
        String v = CriticalHudShader.transform(VSH, vertex);
        String f = CriticalHudShader.transform(FSH, fragment);
        assertNotEquals(vertex, v);
        assertNotEquals(fragment, f);
        assertEquals(vertex, v.replace(OUT, "").replace(MAIN + MARKER, MAIN));
        assertEquals(fragment, f.replace(IN, "").replace(REPAIRED, ORIGINAL));
        assertTrue(f.contains(REPAIRED));
        // This whole suffix includes modulation, GLINT, fog/calculateFinalColor and OIT dispatch.
        String tail = fragment.substring(fragment.indexOf("    color *= vertexColor * ColorModulator;"));
        assertTrue(f.endsWith(tail));
        assertEquals(2, CriticalHudShader.BLOCK_LIGHT);
        assertEquals(3, CriticalHudShader.SKY_LIGHT);
    }

    @Test
    void markerAndFlatInterfaceExistInEveryConditionalVariant() throws IOException {
        String v = CriticalHudShader.transform(VSH, vertex());
        String f = CriticalHudShader.transform(FSH, fragment());
        String[] names = {"GLINT", "GLINT_SPECIAL", "OIT", "OIT_ALPHA_ONLY", "OIT_ACCUMULATE", "ALPHA_CUTOUT"};
        for (int mask = 0; mask < 64; mask++) {
            Set<String> defines = new HashSet<>();
            for (int bit = 0; bit < names.length; bit++) if ((mask & (1 << bit)) != 0) defines.add(names[bit]);
            String vs = selectBranches(v, defines), fs = selectBranches(f, defines);
            assertEquals(1, count(vs, OUT.strip()), defines.toString());
            assertEquals(1, count(fs, IN.strip()), defines.toString());
            assertEquals(1, count(vs, MARKER.strip()), defines.toString());
            assertTrue(vs.indexOf(MARKER.strip()) < vs.indexOf("gl_Position ="), defines.toString());
            assertTrue(fs.indexOf("if (color.a == 0.0)") < fs.indexOf("color *= vertexColor"), defines.toString());
            if (defines.contains("OIT_ALPHA_ONLY")) {
                assertTrue(fs.indexOf("if (color.a == 0.0)") < fs.indexOf("executeAlphaOnlyPhase("));
                assertFalse(fs.contains("fragColor = calculateFinalColor(color);"));
            }
            assertEquals(defines.contains("ALPHA_CUTOUT") ? 1 : 0, count(fs, "color.a < ALPHA_CUTOUT"));
            assertEquals(defines.contains("ALPHA_CUTOUT") ? 2 : 1, count(fs, "discard;"));
        }
    }

    @Test
    void markedPathRejectsOnlyRawZeroWhileOrdinaryCutoutRemainsExact() throws IOException {
        String f = CriticalHudShader.transform(FSH, fragment());
        int marked = f.indexOf("    if (destinyCriticalHud == 1) {");
        int ordinary = f.indexOf("    } else {", marked);
        assertEquals("""
                    if (destinyCriticalHud == 1) {
                        // True transparency must not contribute depth, including OIT_ALPHA_ONLY.
                        if (color.a == 0.0) {
                            discard;
                        }
                """, f.substring(marked, ordinary));
        assertTrue(f.substring(ordinary).startsWith("    } else {\n" + ORIGINAL.substring(ORIGINAL.indexOf("    #ifdef"))));
        assertFalse(f.contains("#define ALPHA_CUTOUT"));
        assertFalse(f.contains("UV2"));
    }

    @Test
    void repeatedTransformAndResourceConversionAreIdempotent() throws IOException {
        for (String path : List.of(VSH, FSH)) {
            String once = CriticalHudShader.transform(path, path.equals(VSH) ? vertex() : fragment());
            assertSame(once, CriticalHudShader.transform(path, once));
            PackResource output = CriticalHudShader.convert(path, PackResource.fromString(once));
            assertSame(output, CriticalHudShader.convert(path, output));
        }
    }

    @Test
    void unrelatedPathsAndResourcesAreReturnedUntouchedWithoutReading() {
        PackResource unreadable = new PackResource() {
            public byte[] readAllBytes() { throw new AssertionError("Unrelated resource was read"); }
            public java.io.InputStream getStream() { throw new AssertionError("Unrelated resource was opened"); }
        };
        for (String path : List.of("assets/minecraft/shaders/core/entity.fsh", "assets/other/shaders/core/item.fsh",
                "assets/minecraft/shaders/core/item.fsh.bak", "overlays/assets/minecraft/shaders/core/item.vsh")) {
            assertSame(unreadable, CriticalHudShader.convert(path, unreadable));
            assertEquals("unrelated", CriticalHudShader.transform(path, "unrelated"));
        }
    }

    @Test
    void rejectsMissingChangedTruncatedDuplicateAndLocationConflictingUpstream() throws IOException {
        assertThrows(IllegalStateException.class, () -> CriticalHudShader.transform(VSH, null));
        assertThrows(IllegalStateException.class, () -> CriticalHudShader.convert(FSH, null));
        String v = vertex(), f = fragment();
        for (String bad : List.of("", v.substring(0, v.length() - 1),
                v.replace("layout(location = 6)", "layout(location = 7)"), v + "\nvoid main() {}\n",
                v.replace("ivec2 UV2", "vec2 UV2"), v.replace("displayhud_is_hud(Position)", "true"))) {
            assertThrows(IllegalStateException.class, () -> CriticalHudShader.transform(VSH, bad));
        }
        for (String bad : List.of("", f.replace("color.a < ALPHA_CUTOUT", "color.a < 0.01"),
                f.replace(ORIGINAL, ""), f.replace(ORIGINAL, ORIGINAL + ORIGINAL),
                f.replace("executeAlphaOnlyPhase(gl_FragCoord.z, color.a);", "discard;"))) {
            assertThrows(IllegalStateException.class, () -> CriticalHudShader.transform(FSH, bad));
        }
    }

    @Test
    void rejectsForgedOrPartiallyPatchedShadersInsteadOfTrustingAMarkerComment() throws IOException {
        String v = vertex(), f = fragment();
        for (String bad : List.of(v.replace(MAIN, OUT + MAIN), v.replace(MAIN, MAIN + MARKER),
                CriticalHudShader.transform(VSH, v).replace("ivec2(32, 48)", "ivec2(16, 32)"))) {
            assertThrows(IllegalStateException.class, () -> CriticalHudShader.transform(VSH, bad));
        }
        for (String bad : List.of(f.replace(MAIN, IN + MAIN), f.replace(ORIGINAL, REPAIRED),
                CriticalHudShader.transform(FSH, f).replace("color.a == 0.0", "color.a < 0.1"))) {
            assertThrows(IllegalStateException.class, () -> CriticalHudShader.transform(FSH, bad));
        }
    }

    @Test
    void registrationDefersValidationAndMaterializesMissingVanillaFragmentAtPreFinish() throws IOException {
        var fixture = new BuilderFixture();
        fixture.resources.put(VSH, PackResource.fromString("earlier placeholder"));
        fixture.sources.put(FSH, fragment());
        CriticalHudShader.configure(fixture.builder);
        assertEquals(1, fixture.converters.size());
        assertEquals(1, fixture.tasks.size());
        assertFalse(fixture.resources.containsKey(FSH));
        fixture.resources.put(VSH, PackResource.fromString(vertex()));
        fixture.tasks.getFirst().accept(fixture.builder);
        assertEquals(fragment(), fixture.resources.get(FSH).asString());
        assertEquals(1, fixture.writes);
        for (String path : List.of(VSH, FSH)) {
            var transformed = fixture.converters.getFirst().convert(path, fixture.resources.get(path));
            assertEquals(CriticalHudShader.transform(path, fixture.resources.get(path).asString()), transformed.asString());
        }
        fixture.tasks.getFirst().accept(fixture.builder);
        assertEquals(1, fixture.writes, "Repeated preparation must not overwrite existing sources");
    }

    @Test
    void preparationValidatesBothStagesBeforeWritingAndRejectsMissingOrOverriddenSources() throws IOException {
        var invalid = new BuilderFixture();
        invalid.sources.put(VSH, vertex());
        invalid.sources.put(FSH, fragment().replace("color.a < ALPHA_CUTOUT", "false"));
        assertThrows(IllegalStateException.class, () -> CriticalHudShader.prepare(invalid.builder));
        assertEquals(0, invalid.writes);
        var missing = new BuilderFixture();
        missing.sources.put(VSH, vertex());
        assertThrows(IllegalStateException.class, () -> CriticalHudShader.prepare(missing.builder));
        assertEquals(0, missing.writes);
        var override = new BuilderFixture();
        override.resources.put(VSH, PackResource.fromString(vertex()));
        override.resources.put(FSH, PackResource.fromString("incompatible existing fragment"));
        override.sources.put(FSH, fragment());
        assertThrows(IllegalStateException.class, () -> CriticalHudShader.prepare(override.builder));
        assertEquals(0, override.writes, "Never replace an incompatible override with vanilla silently");
    }

    @Test
    void failedResourceInsertionAndModifiedPatchedInputsFailClosed() throws IOException {
        var fixture = new BuilderFixture();
        fixture.resources.put(VSH, PackResource.fromString(vertex()));
        fixture.sources.put(FSH, fragment());
        fixture.rejectWrites = true;
        assertThrows(IllegalStateException.class, () -> CriticalHudShader.prepare(fixture.builder));
        String changed = CriticalHudShader.transform(FSH, fragment()) + "\n// later incompatible converter\n";
        assertThrows(IllegalStateException.class, () -> CriticalHudShader.convert(FSH, PackResource.fromString(changed)));
    }

    private static String vertex() throws IOException {
        return Files.readString(Path.of("libs/minigame-lib/src/main/resources").resolve(VSH));
    }

    private static String fragment() throws IOException {
        try (var stream = CriticalHudShaderW96Test.class.getResourceAsStream("/" + FSH)) {
            assertNotNull(stream, "Exact vanilla 26.3 fragment must be available from Minecraft dependency resources");
            return new String(stream.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    private static int count(String source, String needle) {
        return (source.length() - source.replace(needle, "").length()) / needle.length();
    }

    // Select this template's conditional branches, without expanding includes or claiming GLSL compilation.
    private static String selectBranches(String source, Set<String> defines) {
        record Branch(boolean parent, boolean selected) {}
        var stack = new ArrayDeque<Branch>();
        boolean active = true;
        var result = new StringBuilder();
        for (String line : source.split("\n")) {
            String directive = line.strip();
            Boolean selected = null;
            if (directive.startsWith("#ifdef ")) selected = defines.contains(directive.substring(7));
            else if (directive.startsWith("#ifndef ")) selected = !defines.contains(directive.substring(8));
            else if (directive.equals("#if !defined(OIT)")) selected = !defines.contains("OIT");
            else if (directive.startsWith("#if ")) fail("Unsupported test branch expression: " + directive);
            if (selected != null) {
                stack.push(new Branch(active, selected));
                active = active && selected;
            } else if (directive.equals("#else")) {
                var branch = stack.peek();
                assertNotNull(branch);
                active = branch.parent() && !branch.selected();
            } else if (directive.equals("#endif")) {
                active = stack.pop().parent();
            } else if (active) result.append(line).append('\n');
        }
        assertTrue(stack.isEmpty());
        return result.toString();
    }

    private static final class BuilderFixture {
        final Map<String, PackResource> resources = new HashMap<>();
        final Map<String, String> sources = new HashMap<>();
        final List<ResourcePackBuilder.ResourceConverter> converters = new ArrayList<>();
        final List<Consumer<ResourcePackBuilder>> tasks = new ArrayList<>();
        int writes;
        boolean rejectWrites;
        final ResourcePackBuilder builder = (ResourcePackBuilder) Proxy.newProxyInstance(
                ResourcePackBuilder.class.getClassLoader(), new Class<?>[]{ResourcePackBuilder.class},
                (proxy, method, args) -> switch (method.getName()) {
                    case "getResource" -> resources.get((String) args[0]);
                    case "getDataOrSource" -> {
                        var resource = resources.get((String) args[0]);
                        String source = sources.get((String) args[0]);
                        yield resource != null ? resource.readAllBytes()
                                : source == null ? null : source.getBytes(StandardCharsets.UTF_8);
                    }
                    case "addData" -> {
                        if (rejectWrites) yield false;
                        resources.put((String) args[0], (PackResource) args[1]);
                        writes++;
                        yield true;
                    }
                    case "addResourceConverter" -> { converters.add((ResourcePackBuilder.ResourceConverter) args[0]); yield null; }
                    case "addPreFinishTask" -> {
                        @SuppressWarnings("unchecked") var task = (Consumer<ResourcePackBuilder>) args[0];
                        tasks.add(task);
                        yield null;
                    }
                    default -> throw new AssertionError("Unexpected builder call: " + method);
                });
    }
}
