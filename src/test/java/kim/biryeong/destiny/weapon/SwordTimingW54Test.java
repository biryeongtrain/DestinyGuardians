package kim.biryeong.destiny.weapon;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/** Pure authored timing/asset contracts; no Minecraft bootstrap or native playback evidence. */
class SwordTimingW54Test {
    private static final String RUNTIME = "destiny/animation/sword_w53.animation.json";
    private record Cue(String clip, SwordProfile.Shape shape, boolean heavy, int combo,
                       double seconds, int ticks) {}
    private static final List<Cue> CUES = List.of(
            new Cue("h15_sword_light_1", SwordProfile.Shape.UPPERCUT, false, 1, .15, 4),
            new Cue("h15_sword_light_2", SwordProfile.Shape.UPPERCUT, false, 2, .20, 5),
            new Cue("h15_sword_light_3", SwordProfile.Shape.UPPERCUT, false, 3, .20, 5),
            new Cue("h15_sword_uppercut", SwordProfile.Shape.UPPERCUT, true, 1, .35, 8),
            new Cue("h15_sword_dash", SwordProfile.Shape.DASH, true, 1, .25, 6),
            new Cue("h15_sword_slam", SwordProfile.Shape.SLAM, true, 1, .40, 9),
            new Cue("h15_sword_vortex", SwordProfile.Shape.VORTEX, true, 1, .45, 10),
            new Cue("h15_sword_caster", SwordProfile.Shape.CASTER, true, 1, .30, 7));

    @Test void allEightAuthoredMappingsIncludeExactlyOneStartBlendTick() {
        assertEquals(1, SwordTiming.START_TICKS);
        for (var cue : CUES) {
            assertEquals(cue.seconds(), SwordTiming.contactSeconds(cue.shape(), cue.heavy(), cue.combo()),
                    0.0, cue.clip());
            assertEquals(cue.ticks(), SwordTiming.contactTicks(cue.shape(), cue.heavy(), cue.combo()), cue.clip());
            assertEquals(1, cue.ticks() - (int) Math.ceil(cue.seconds() * 20.0), cue.clip());
        }
    }

    @Test void lightComboClampsAtBothIntegerExtremesAndIgnoresShape() {
        var shapes = new java.util.ArrayList<>(List.of(SwordProfile.Shape.values()));
        shapes.add(null);
        for (var shape : shapes) {
            for (int combo : new int[]{Integer.MIN_VALUE, -1, 0, 1, 2, 3, 4, Integer.MAX_VALUE}) {
                int clamped = Math.max(1, Math.min(3, combo));
                assertEquals(clamped == 1 ? .15 : .20,
                        SwordTiming.contactSeconds(shape, false, combo), 0.0);
                assertEquals(clamped == 1 ? 4 : 5, SwordTiming.contactTicks(shape, false, combo));
            }
        }
    }

    @Test void heavyIgnoresComboButClearlyRejectsMissingShape() {
        for (var cue : CUES) {
            if (!cue.heavy()) continue;
            for (int combo : new int[]{Integer.MIN_VALUE, 0, 1, 3, Integer.MAX_VALUE}) {
                assertEquals(cue.seconds(), SwordTiming.contactSeconds(cue.shape(), true, combo), 0.0);
                assertEquals(cue.ticks(), SwordTiming.contactTicks(cue.shape(), true, combo));
            }
        }
        var secondsError = assertThrows(NullPointerException.class,
                () -> SwordTiming.contactSeconds(null, true, 1));
        var ticksError = assertThrows(NullPointerException.class,
                () -> SwordTiming.contactTicks(null, true, 1));
        assertEquals("shape is required for a heavy sword attack", secondsError.getMessage());
        assertEquals(secondsError.getMessage(), ticksError.getMessage());
    }

    @Test void actualManifestCuesAreFiniteAndStayWithinThePinnedRuntimeClips() throws Exception {
        JsonObject manifest;
        try (var reader = Files.newBufferedReader(Path.of("art/weapons/w53/manifest.json"),
                StandardCharsets.UTF_8)) {
            manifest = JsonParser.parseReader(reader).getAsJsonObject();
        }
        assertEquals("W53", manifest.get("stage").getAsString());
        assertTrue(manifest.get("authoredNotD2Measured").getAsBoolean());
        byte[] runtimeBytes;
        try (var stream = getClass().getResourceAsStream("/" + RUNTIME)) {
            assertNotNull(stream, RUNTIME);
            runtimeBytes = stream.readAllBytes();
        }
        assertEquals(manifest.getAsJsonObject("outputSha256")
                        .get("src/main/resources/" + RUNTIME).getAsString(),
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(runtimeBytes)),
                "Timing bounds must come from the W53 manifest's actual pinned runtime export");
        var runtime = JsonParser.parseString(new String(runtimeBytes, StandardCharsets.UTF_8)).getAsJsonObject();
        assertEquals(manifest.get("model"), runtime.get("model"));
        var authoredClips = clipsByName(manifest);
        var runtimeClips = clipsByName(runtime);
        var expected = CUES.stream().map(Cue::clip).collect(Collectors.toSet());
        assertEquals(8, expected.size());
        assertEquals(expected, authoredClips.keySet());
        assertEquals(expected, runtimeClips.keySet());
        assertEquals(8, manifest.get("runtimeExportCount").getAsInt());
        for (var cue : CUES) {
            var authored = authoredClips.get(cue.clip());
            var clip = runtimeClips.get(cue.clip());
            double seconds = finiteNumber(authored, "authoredContactOrReleaseSeconds");
            double length = finiteNumber(clip, "length");
            assertEquals(finiteNumber(authored, "lengthSeconds"), length, 0.0, cue.clip());
            assertTrue(length > 0 && seconds > 0 && seconds < length, cue.clip());
            assertEquals(seconds, SwordTiming.contactSeconds(cue.shape(), cue.heavy(), cue.combo()),
                    0.0, cue.clip());
            int ticks = SwordTiming.contactTicks(cue.shape(), cue.heavy(), cue.combo());
            double elapsedClipTicks = ticks - SwordTiming.START_TICKS;
            assertEquals((int) Math.ceil(seconds * 20.0) + SwordTiming.START_TICKS, ticks, cue.clip());
            assertTrue(elapsedClipTicks >= seconds * 20.0
                    && elapsedClipTicks < seconds * 20.0 + 1, cue.clip());
            assertTrue(elapsedClipTicks < length * 20.0, cue.clip());
            for (var animator : clip.getAsJsonObject("animators").asMap().values()) {
                for (var frame : animator.getAsJsonObject().getAsJsonArray("keyframes")) {
                    double time = finiteNumber(frame.getAsJsonObject(), "time");
                    assertTrue(time >= 0 && time <= length + 1e-6, cue.clip());
                }
            }
        }
    }

    @Test void everyContactPrecedesItsActualProfileCadenceAndLightInterval() {
        // Catalog/profile dependencies are JSON + Java only; no item registry or Minecraft bootstrap.
        var swords = WeaponCatalog.family("sword");
        assertEquals(5, swords.size());
        var shapes = EnumSet.noneOf(SwordProfile.Shape.class);
        for (var entry : swords) {
            var sword = SwordProfile.of(entry);
            var base = WeaponProfile.forEntry(entry);
            assertTrue(shapes.add(sword.shape()), entry.id());
            for (var cue : CUES) {
                if (cue.heavy() && cue.shape() != sword.shape()) continue;
                int ticks = SwordTiming.contactTicks(sword.shape(), cue.heavy(), cue.combo());
                var attack = sword.attack(base, base.damage(), cue.heavy());
                assertTrue(ticks < attack.intervalTicks(), entry.id() + ": " + cue.clip());
                assertTrue(ticks < attack.cadenceTicks(), entry.id() + ": " + cue.clip());
                assertTrue(ticks < base.intervalTicks(), entry.id() + ": before next light input");
                if (cue.heavy()) {
                    assertTrue(ticks < sword.heavyTicks(), entry.id());
                    if (sword.shape() == SwordProfile.Shape.CASTER) {
                        var caster = sword.caster(base, base.damage());
                        assertTrue(ticks < caster.intervalTicks() && ticks < caster.cadenceTicks(), entry.id());
                    }
                }
            }
        }
        assertEquals(EnumSet.allOf(SwordProfile.Shape.class), shapes);
    }

    private static Map<String, JsonObject> clipsByName(JsonObject root) {
        Map<String, JsonObject> clips = new HashMap<>();
        String field = root.has("clips") ? "clips" : "animations";
        for (JsonElement value : root.getAsJsonArray(field)) {
            var clip = value.getAsJsonObject();
            String name = clip.get("name").getAsString();
            assertNull(clips.put(name, clip), "Duplicate clip: " + name);
        }
        return clips;
    }

    private static double finiteNumber(JsonObject object, String key) {
        var value = object.get(key);
        assertNotNull(value, key);
        assertTrue(value.isJsonPrimitive() && value.getAsJsonPrimitive().isNumber(), key);
        double number = value.getAsDouble();
        assertTrue(Double.isFinite(number), key);
        return number;
    }
}
