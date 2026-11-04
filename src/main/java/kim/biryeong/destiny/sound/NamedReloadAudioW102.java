package kim.biryeong.destiny.sound;

import com.google.gson.Gson;
import kim.biryeong.destiny.sound.ReloadAudioProfile.Clip;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

/** Exact named-source replacements of existing W63 durations, never new gameplay deadlines. */
final class NamedReloadAudioW102 {
    private record Data(String stage, Clip[] entries) {}
    private static final Map<String, String> FAMILIES = Map.of(
            "aishas_embrace", "scout_rifle", "blast_furnace", "pulse_rifle",
            "chattering_bone", "pulse_rifle", "retrofit_escapade", "machine_gun");
    private static final Set<String> KEYS = Set.of("aishas_embrace:46", "blast_furnace:24",
            "blast_furnace:43", "chattering_bone:24", "chattering_bone:34", "retrofit_escapade:90");
    private static final Map<String, Clip> CLIPS = load();
    private NamedReloadAudioW102() {}
    private static String key(Clip c) { return c.id() + ":" + c.ticks(); }

    private static Map<String, Clip> load() {
        var in = NamedReloadAudioW102.class.getResourceAsStream("/destiny/sounds/w102-reload.json");
        if (in == null) throw new IllegalStateException("Missing W102 named reload profile");
        try (var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
            var data = new Gson().fromJson(reader, Data.class);
            if (data == null || !"W102".equals(data.stage) || data.entries == null || data.entries.length != KEYS.size())
                throw new IllegalStateException("Invalid W102 named reload profile");
            var result = new HashMap<String, Clip>();
            for (var c : data.entries) {
                if (c == null || !KEYS.contains(key(c))
                        || !("weapon.reload_w102." + c.id() + "." + c.ticks()).equals(c.event())
                        || !("weapon." + c.id() + ".reload").equals(c.sourceEvent())
                        || !("assets/destiny/sounds/w102/" + c.id() + "/reload_" + c.ticks() + ".ogg").equals(c.asset())
                        || c.sourceSha256() == null || !c.sourceSha256().matches("[a-f0-9]{64}")
                        || !c.sourceSha256().equals(resourceSha("/assets/destiny/sounds/w102/" + c.id() + "/reload.ogg"))
                        || result.put(key(c), c) != null)
                    throw new IllegalStateException("Invalid W102 named reload clip " + c);
            }
            if (!result.keySet().equals(KEYS)) throw new IllegalStateException("Incomplete W102 replacements");
            return Map.copyOf(result);
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }

    private static String resourceSha(String path) {
        try (var in = NamedReloadAudioW102.class.getResourceAsStream(path)) {
            if (in == null) throw new IllegalStateException("Missing named reload source " + path);
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(in.readAllBytes()));
        } catch (java.io.IOException | java.security.NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
    }

    static Clip overlay(Clip legacy) {
        var replacement = CLIPS.get(key(legacy));
        if (replacement == null) return legacy;
        String source = "weapon." + FAMILIES.get(legacy.id()) + ".reload";
        if (!("weapon.reload_w63." + source + "." + legacy.ticks()).equals(legacy.event())
                || !source.equals(legacy.sourceEvent())
                || !("assets/destiny/sounds/w63/reload/" + source.replace('.', '_') + "_" + legacy.ticks() + ".ogg").equals(legacy.asset()))
            throw new IllegalStateException("W102 must replace the exact inherited W63 key " + legacy);
        return replacement;
    }

    static boolean isReplacement(Clip c) { return c != null && c.equals(CLIPS.get(key(c))); }
}
