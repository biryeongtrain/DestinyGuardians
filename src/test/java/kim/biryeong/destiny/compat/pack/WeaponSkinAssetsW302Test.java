package kim.biryeong.destiny.compat.pack;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import eu.pb4.polymer.resourcepack.api.PackResource;
import kim.biryeong.destiny.weapon.WeaponSkins;
import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class WeaponSkinAssetsW302Test {
    private static final Path ROOT = Path.of("src/main/resources");

    private static Map<String, PackResource> load(WeaponSkins.Skin skin) throws Exception {
        var files = new HashMap<String, PackResource>();
        try (var walk = Files.walk(ROOT.resolve("assets/destiny"))) {
            for (var p : (Iterable<Path>) walk.filter(Files::isRegularFile)::iterator) {
                String rel = ROOT.relativize(p).toString().replace('\\', '/');
                boolean framing = rel.startsWith("assets/destiny/models/first_person_framing_w205/");
                if (!rel.contains(skin.base()) && !framing && !rel.contains(skin.id())) continue;
                byte[] bytes = Files.readAllBytes(p);
                if (framing && !new String(bytes).contains(skin.base())) continue;
                files.put(rel, PackResource.of(bytes));
            }
        }
        return files;
    }

    @Test void everyBaseRouteHasACompleteSkinMirror() throws Exception {
        for (var skin : WeaponSkins.ALL) {
            var files = load(skin);
            var out = WeaponSkinAssets.plan(files);
            assertFalse(out.isEmpty(), skin.id());
            var all = new HashMap<>(files); all.putAll(out);
            int geometry = 0;
            for (var e : out.entrySet()) {
                assertFalse(e.getKey().contains(skin.base()) && !e.getKey().contains("first_person_framing_w205"),
                        "base token left in path " + e.getKey());
                var json = JsonParser.parseString(e.getValue().asString()).getAsJsonObject();
                var refs = new HashSet<String>();
                refs(json, refs);
                for (String r : refs) {
                    assertFalse(r.contains(skin.base()) && !r.contains("/w123/") && !r.contains("weapon_insert"),
                            e.getKey() + " still references base " + r);
                }
                if (json.has("parent")) {
                    String parent = json.get("parent").getAsString();
                    if (parent.startsWith("destiny:")) assertTrue(all.containsKey(WeaponPackOptimizer.modelPath(parent)),
                            e.getKey() + " missing parent " + parent);
                }
                if (json.has("elements") && !e.getKey().contains("/gui/") && !e.getKey().endsWith("_shell.json")
                        && !e.getKey().endsWith("_shell_hidden.json")) {
                    geometry++;
                    assertEquals(skin.texture(), json.getAsJsonObject("textures").get("0").getAsString(), e.getKey());
                    assertTrue(json.getAsJsonArray("elements").size() > 0, e.getKey());
                }
            }
            assertTrue(geometry >= 3, skin.id() + " geometry leaves " + geometry);
            // Every item-model edge resolves.
            for (var e : out.entrySet()) {
                if (!e.getKey().contains("/items/")) continue;
                var models = new HashSet<String>();
                WeaponPackOptimizer.references(JsonParser.parseString(e.getValue().asString()), models);
                for (String m : models) if (m.startsWith("assets/destiny/") && (m.contains(skin.id()) || m.contains(skin.base())))
                    assertTrue(all.containsKey(m), e.getKey() + " -> missing " + m);
            }
        }
    }

    private static void refs(JsonElement el, Set<String> out) {
        if (el.isJsonObject()) for (var v : el.getAsJsonObject().entrySet()) {
            if (v.getValue().isJsonPrimitive() && v.getValue().getAsString().startsWith("destiny:")) out.add(v.getValue().getAsString());
            else refs(v.getValue(), out);
        } else if (el.isJsonArray()) for (var v : el.getAsJsonArray()) {
            if (v.isJsonPrimitive() && v.getAsString().startsWith("destiny:")) out.add(v.getAsString());
            else refs(v, out);
        }
    }
}
