package kim.biryeong.destiny.weapon;

import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.ResourcePackBuilder;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import javax.imageio.ImageIO;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

import static org.junit.jupiter.api.Assertions.*;

/** Real classpath PNGs and pack callbacks; no native/art/performance acceptance. */
class WeaponSurfaceCullingW120Test {
    private static final String FLAG = "destiny.weapon.surface.cull.w119";
    private static final List<String> ATLASES = List.of(
            "assets/destiny/textures/item/weapon/w115/blast_furnace.png",
            "assets/destiny/textures/item/weapon/w115/hammerhead.png");
    private String previous;

    @BeforeEach void optIn() {
        previous = System.getProperty(FLAG);
        System.setProperty(FLAG, "true");
    }

    @AfterEach void restoreProperty() {
        if (previous == null) System.clearProperty(FLAG);
        else System.setProperty(FLAG, previous);
    }

    @Test void validStaticImagesPassDeferredPrefinishAndSevenModelConversionIsIdempotent() throws IOException {
        var fixture = configured();
        var expected = WeaponSurfaceAssets.optimizeRules(WeaponSurfaceAssets.rules()).rules();
        assertEquals(WeaponSurfaceAssets.TARGETS, expected.keySet());
        assertEquals(7, expected.size());
        fixture.populate();
        fixture.finish();
        for (String path : WeaponSurfaceAssets.TARGETS) {
            var converted = fixture.converter().convert(path, fixture.resources.get(path));
            assertEquals(expected.get(path).replacement(), converted.asString());
            assertSame(converted, fixture.converter().convert(path, converted));
            fixture.resources.put(path, converted);
        }
        fixture.finish();
        var allowed = new HashSet<>(WeaponSurfaceAssets.TARGETS);
        for (String path : ATLASES) {
            allowed.add(path);
            allowed.add(path + ".mcmeta");
            try (var metadata = getClass().getResourceAsStream("/" + path + ".mcmeta")) {
                assertNull(metadata, "The opacity proof requires static classpath images");
            }
        }
        assertEquals(allowed, new HashSet<>(fixture.lookups));
    }

    @ParameterizedTest @ValueSource(ints = {0, 1})
    void changedAlphaRejectsEachEmittedAtlas(int index) throws IOException {
        rejectPixelChange(index, 0x01000000);
    }

    @ParameterizedTest @ValueSource(ints = {0, 1})
    void changedRgbWithIdenticalAlphaAlsoRejectsEachEmittedAtlas(int index) throws IOException {
        rejectPixelChange(index, 0x00000001);
    }

    private void rejectPixelChange(int index, int mask) throws IOException {
        var fixture = configured();
        fixture.populate();
        String path = ATLASES.get(index);
        var image = ImageIO.read(new ByteArrayInputStream(bytes(path)));
        int pixel = image.getRGB(0, 0);
        image.setRGB(0, 0, pixel ^ mask);
        var encoded = new ByteArrayOutputStream();
        assertTrue(ImageIO.write(image, "png", encoded));
        var changed = ImageIO.read(new ByteArrayInputStream(encoded.toByteArray()));
        assertEquals(pixel ^ mask, changed.getRGB(0, 0));
        fixture.resources.put(path, binary(encoded.toByteArray()));
        rejected(fixture, path, "differs from classpath proof");
    }

    @ParameterizedTest @ValueSource(ints = {0, 1})
    void missingEmittedAtlasFailsClosed(int index) throws IOException {
        var fixture = configured();
        fixture.populate();
        String path = ATLASES.get(index);
        fixture.resources.remove(path);
        rejected(fixture, path, "missing emitted opacity image");
    }

    @ParameterizedTest @ValueSource(ints = {0, 1})
    void anyAddedMetadataFailsClosedWithoutReadingItsPayload(int index) throws IOException {
        var fixture = configured();
        fixture.populate();
        String path = ATLASES.get(index) + ".mcmeta";
        for (var metadata : List.of(PackResource.fromString("{\"animation\":{}}"),
                PackResource.fromString("{}"), unreadable())) {
            fixture.resources.put(path, metadata);
            rejected(fixture, path, "unknown emitted texture metadata");
        }
    }

    @Test void configureSnapshotSurvivesFlagChangeAndDoesNotRebaseOnMutatedEmittedBytes() throws IOException {
        var fixture = configured();
        fixture.populate();
        System.setProperty(FLAG, "false");
        fixture.finish();
        String path = ATLASES.getFirst();
        byte[] mutable = bytes(path);
        fixture.resources.put(path, binary(mutable));
        fixture.finish();
        mutable[mutable.length - 1] ^= 1;
        rejected(fixture, path, "differs from classpath proof");
    }

    @Test void absentAndFalseFlagKeepCanonicalBytesAndNeverRequestTextureOrMetadataPayloads() throws IOException {
        for (String value : new String[]{null, "false"}) {
            if (value == null) System.clearProperty(FLAG); else System.setProperty(FLAG, value);
            var fixture = configured();
            fixture.populate();
            for (String path : ATLASES) {
                fixture.resources.put(path, unreadable());
                fixture.resources.put(path + ".mcmeta", unreadable());
            }
            System.setProperty(FLAG, "true"); // Snapshot also preserves default behavior.
            fixture.finish();
            var canonical = WeaponSurfaceAssets.rules();
            for (String path : WeaponSurfaceAssets.TARGETS) {
                var output = fixture.converter().convert(path, fixture.resources.get(path));
                assertEquals(canonical.get(path).replacement(), output.asString());
                assertSame(output, fixture.converter().convert(path, output));
            }
            assertEquals(WeaponSurfaceAssets.TARGETS, new HashSet<>(fixture.lookups));
        }
    }

    @Test void unrelatedPayloadsAndNearMissAtlasPathsAreNeverRequestedOrRead() throws IOException {
        var fixture = configured();
        fixture.populate();
        for (String path : List.of("assets/destiny/textures/item/weapon/w115/other.png",
                ATLASES.getFirst() + ".bak", "overlays/" + ATLASES.getFirst(),
                "assets/other/textures/item/weapon/w115/hammerhead.png.mcmeta",
                "assets/destiny/sounds.json")) {
            var untouched = unreadable();
            fixture.resources.put(path, untouched);
            assertSame(untouched, fixture.converter().convert(path, untouched));
        }
        fixture.finish();
        assertFalse(fixture.lookups.contains("assets/destiny/sounds.json"));
    }

    @Test void modelFingerprintGuardStillRejectsOverridesAndMissingTargetsWithValidImages() throws IOException {
        var fixture = configured();
        fixture.populate();
        String path = WeaponSurfaceAssets.TARGETS.iterator().next();
        var original = fixture.resources.get(path);
        fixture.resources.put(path, PackResource.fromString(original.asString() + "\n"));
        rejected(fixture, path, "unexpected source SHA-256");
        fixture.resources.put(path, PackResource.fromString(
                WeaponSurfaceAssets.optimizeRules(WeaponSurfaceAssets.rules()).rules().get(path).replacement() + "\n"));
        rejected(fixture, path, "unexpected source SHA-256");
        fixture.resources.remove(path);
        rejected(fixture, path, "missing emitted model");
    }

    private static void rejected(Fixture fixture, String path, String reason) {
        var failure = assertThrows(IllegalStateException.class, fixture::finish);
        assertTrue(failure.getMessage().contains(path), failure.getMessage());
        assertTrue(failure.getMessage().contains(reason), failure.getMessage());
    }

    private static Fixture configured() {
        var fixture = new Fixture();
        WeaponSurfaceAssets.configure(fixture.builder);
        assertEquals(1, fixture.converters.size());
        assertEquals(1, fixture.tasks.size());
        assertTrue(fixture.lookups.isEmpty(), "Validation must wait for emission");
        return fixture;
    }

    private static byte[] bytes(String path) throws IOException {
        try (var stream = WeaponSurfaceCullingW120Test.class.getResourceAsStream("/" + path)) {
            assertNotNull(stream, path);
            return stream.readAllBytes();
        }
    }

    private static PackResource binary(byte[] bytes) {
        return new PackResource() {
            public byte[] readAllBytes() { return bytes; }
            public InputStream getStream() { return new ByteArrayInputStream(bytes); }
            public String asString() { throw new AssertionError("Binary PNG decoded as text"); }
        };
    }

    private static PackResource unreadable() {
        return new PackResource() {
            public byte[] readAllBytes() { throw new AssertionError("Unrelated/metadata payload read"); }
            public InputStream getStream() { throw new AssertionError("Unrelated/metadata payload opened"); }
        };
    }

    private static final class Fixture {
        final Map<String, PackResource> resources = new HashMap<>();
        final List<String> lookups = new ArrayList<>();
        final List<ResourcePackBuilder.ResourceConverter> converters = new ArrayList<>();
        final List<Consumer<ResourcePackBuilder>> tasks = new ArrayList<>();
        final ResourcePackBuilder builder = (ResourcePackBuilder) Proxy.newProxyInstance(
                ResourcePackBuilder.class.getClassLoader(), new Class<?>[]{ResourcePackBuilder.class},
                (proxy, method, args) -> switch (method.getName()) {
                    case "getResource" -> {
                        String path = (String) args[0];
                        assertTrue(WeaponSurfaceAssets.TARGETS.contains(path) || ATLASES.contains(path)
                                || ATLASES.stream().anyMatch(p -> (p + ".mcmeta").equals(path)),
                                "Unapproved pack read: " + path);
                        lookups.add(path);
                        yield resources.get(path);
                    }
                    case "addResourceConverter" -> {
                        converters.add((ResourcePackBuilder.ResourceConverter) args[0]); yield null;
                    }
                    case "addPreFinishTask" -> {
                        @SuppressWarnings("unchecked") var task = (Consumer<ResourcePackBuilder>) args[0];
                        tasks.add(task); yield null;
                    }
                    default -> throw new AssertionError("Unexpected pack mutation/API: " + method);
                });

        void populate() throws IOException {
            for (String path : WeaponSurfaceAssets.TARGETS) resources.put(path, PackResource.of(bytes(path)));
            for (String path : ATLASES) resources.put(path, binary(bytes(path)));
        }

        ResourcePackBuilder.ResourceConverter converter() { return converters.getFirst(); }
        void finish() { tasks.getFirst().accept(builder); }
    }
}
