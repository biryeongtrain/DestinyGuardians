package kim.biryeong.destiny.sound;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import static org.junit.jupiter.api.Assertions.*;

/** Reconstruct approved later layers from their provenance, rather than accepting a namespace. */
final class ReviewedAudioW234 {
    private static final String RES = "src/main/resources/";
    private ReviewedAudioW234() {}
    private static JsonObject json(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }
    private static void merge(JsonObject target, JsonObject fragment) {
        for (var entry : fragment.entrySet()) target.add(entry.getKey(), entry.getValue().deepCopy());
    }
    static JsonObject w102Definitions() throws Exception {
        var result = json("docs/qa/2026-10-25/w98/before/src/main/resources/assets/destiny/sounds.json");
        merge(result, json("art/weapons/w98/audio/event-definitions.json"));
        merge(result, json("art/weapons/w102/audio/event-definitions.json"));
        return result;
    }
    private static JsonObject definition(String asset, JsonObject previous) {
        var result = previous == null ? new JsonObject() : previous.deepCopy();
        var sound = new JsonObject();
        sound.addProperty("name", "destiny:" + asset);
        sound.addProperty("stream", false);
        sound.addProperty("attenuation_distance", 32);
        var sounds = new com.google.gson.JsonArray(); sounds.add(sound);
        result.add("sounds", sounds);
        return result;
    }
    static JsonObject expectedCurrent() throws Exception {
        var result = w102Definitions();
        var shotgun = json("art/weapons/w210/shotgun-audio-manifest.json").getAsJsonObject("assets");
        for (String action : Set.of("insert", "finish")) {
            String event = "weapon.shotgun.reload_" + action;
            var entry = definition(assetId(shotgun.getAsJsonObject(action).get("asset").getAsString()), null);
            entry.addProperty("subtitle", "subtitles.destiny." + event);
            result.add(event, entry);
        }
        merge(result, json("art/classes/w229/audio/sounds-additions.json"));
        merge(result, json("docs/qa/2026-10-28/w230/sources/sounds-additions.json"));
        for (var value : json("art/audio/w233/applied.json").getAsJsonArray("bindings")) {
            var binding = value.getAsJsonObject();
            String event = binding.get("event").getAsString();
            var previous = binding.get("previousDefinition");
            assertEquals(previous.isJsonNull() ? null : previous, result.get(event), "W233 predecessor: " + event);
            result.add(event, definition(assetId(binding.get("output").getAsString()),
                    previous.isJsonNull() ? null : previous.getAsJsonObject()));
        }
        merge(result, json("docs/qa/2026-10-30/w270/sounds-fragment.json"));
        merge(result, json("art/ghost/w280/sounds-fragment.json"));
        return result;
    }
    /** Validate the complete current index, then expose the historical layer to its old assertions. */
    static JsonObject legacyW102(JsonObject current) throws Exception {
        assertEquals(expectedCurrent(), current, "Current audio must exactly match the reviewed stage layers");
        return w102Definitions();
    }
    private static String assetId(String path) {
        String prefix = "assets/destiny/sounds/";
        assertTrue(path.startsWith(prefix) && path.endsWith(".ogg") && !path.contains(".."), path);
        return path.substring(prefix.length(), path.length() - 4);
    }
    private record Pin(String sha256, Long bytes) {}
    private static void pin(Map<String, Pin> result, String asset, String hash, Long bytes) {
        assetId(asset);
        var value = new Pin(hash, bytes);
        var previous = result.putIfAbsent(RES + asset, value);
        if (previous != null) assertEquals(previous, value, "Shared WEM must have identical provenance");
    }
    private static Map<String, Pin> laterPins() throws Exception {
        var result = new TreeMap<String, Pin>();
        for (var value : json("art/weapons/w210/shotgun-audio-manifest.json").getAsJsonObject("assets").asMap().values()) {
            var entry = value.getAsJsonObject();
            pin(result, entry.get("asset").getAsString(), entry.get("sha256").getAsString(), entry.get("bytes").getAsLong());
        }
        for (String file : new String[]{"art/classes/w229/audio/provenance-mapping.json",
                "docs/qa/2026-10-28/w230/sources/audio-provenance.json"}) {
            for (var value : json(file).getAsJsonArray("entries")) {
                var entry = value.getAsJsonObject();
                // Disabled/retained clips are still shipped files and remain hash-checked.
                pin(result, entry.get("asset_relative_path").getAsString(), entry.get("asset_sha256").getAsString(),
                        entry.get("asset_bytes").getAsLong());
            }
        }
        for (var value : json("art/audio/w233/applied.json").getAsJsonArray("bindings")) {
            var entry = value.getAsJsonObject();
            pin(result, entry.get("output").getAsString(), entry.getAsJsonObject("processed").get("sha256").getAsString(), null);
        }
        for (var value : json("docs/qa/2026-10-30/w270/audio-import.json").getAsJsonArray("entries")) {
            var entry = value.getAsJsonObject();
            pin(result, entry.get("output").getAsString(), entry.get("sha256").getAsString(), entry.get("bytes").getAsLong());
        }
        for (var entry : json("art/ghost/w282/audio-manifest.json").entrySet()) {
            var value = entry.getValue().getAsJsonObject();
            pin(result, "assets/destiny/sounds/tutorial/ghost/" + entry.getKey() + ".ogg",
                    value.get("output_sha256").getAsString(), value.get("output_bytes").getAsLong());
        }
        return Map.copyOf(result);
    }
    static Set<String> laterSoundIds() throws Exception {
        var result = new HashSet<String>();
        for (String path : laterPins().keySet()) result.add("destiny:" + assetId(path.substring(RES.length())));
        return Set.copyOf(result);
    }
    static Set<String> verifiedLaterAudioPaths() throws Exception {
        var pins = laterPins();
        for (var entry : pins.entrySet()) {
            Path path = Path.of(entry.getKey());
            assertEquals(entry.getValue().sha256(), HexFormat.of().formatHex(
                    MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))), entry.getKey());
            if (entry.getValue().bytes() != null)
                assertEquals(entry.getValue().bytes().longValue(), Files.size(path), entry.getKey());
        }
        return Set.copyOf(pins.keySet());
    }
}
