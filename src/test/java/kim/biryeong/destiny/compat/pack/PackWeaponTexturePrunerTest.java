package kim.biryeong.destiny.compat.pack;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import eu.pb4.polymer.resourcepack.api.PackResource;
import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class PackWeaponTexturePrunerTest {
    private static final String BASE = "assets/destiny/textures/item/weapon/w30/";

    @Test void retainedReferencesAcrossFormatsProtectImagesWithoutChangingAnyBytes() {
        var files = new HashMap<String, PackResource>();
        var references = Map.of(
                "model", "destiny:item/weapon/w30/model",
                "font", "destiny:item/weapon/w30/font.png",
                "gui", BASE + "gui.png",
                "equipment", "textures/item/weapon/w30/equipment.png",
                "custom", "item/weapon/w30/custom",
                "metadata", "destiny:textures/item/weapon/w30/metadata.png",
                "key", "destiny/textures/item/weapon/w30/key.png");
        references.keySet().forEach(name -> files.put(BASE + name + ".png", resource("PNG " + name)));
        files.put("assets/destiny/models/base.json", resource("{\"textures\":{\"0\":\"" + references.get("model") + "\"}}"));
        for (String kind : Set.of("font", "gui", "equipment", "custom")) {
            var json = new JsonObject(); var nested = new JsonArray(); nested.add(references.get(kind));
            json.add("opaque", nested);
            files.put("assets/foreign/" + kind + "/definition.json", resource(json.toString()));
        }
        var metadata = new JsonObject(); metadata.addProperty("custom", references.get("metadata"));
        metadata.addProperty(references.get("key"), true);
        files.put("assets/foreign/textures/other.png.mcmeta", resource(metadata.toString()));
        files.put(BASE + "shader.png", resource("shader PNG"));
        files.put("assets/foreign/shaders/custom.glsl", resource("// destiny:item/weapon/w30/shader"));
        files.put(BASE + "pinned.png", resource("external PNG"));
        files.put(BASE + "unused.png", resource("unmodified PNG"));
        files.put(BASE + "unused.png.mcmeta", resource("{\"animation\":{\"frametime\":3}}"));
        files.put(BASE + "omitted_only.png", resource("old PNG"));
        String old = "assets/destiny/models/weapon_reload_w99/old.json";
        files.put(old, resource("{\"textures\":{\"0\":\"destiny:item/weapon/w30/omitted_only\"}}"));
        var omitted = new HashSet<>(Set.of(old));
        var before = new HashMap<String, byte[]>();
        files.forEach((path, value) -> before.put(path, value.readAllBytes().clone()));

        assertEquals(2, PackWeaponTexturePruner.prune(files, omitted, Set.of("destiny:item/weapon/w30/pinned")));
        assertEquals(Set.of(old, BASE + "unused.png", BASE + "unused.png.mcmeta", BASE + "omitted_only.png"), omitted);
        assertEquals(before.keySet(), files.keySet());
        before.forEach((path, bytes) -> assertArrayEquals(bytes, files.get(path).readAllBytes(), path));
        assertEquals(0, PackWeaponTexturePruner.prune(files, omitted, Set.of("destiny:item/weapon/w30/pinned")));
    }

    @Test void atlasDirectoryIsNotARootButExplicitSingleAndOtherNamespacesArePreserved() {
        var files = new HashMap<String, PackResource>();
        for (String path : Set.of(BASE + "single.png", BASE + "unused.png",
                "assets/destiny/textures/item/weapon/current/keep.png",
                "assets/destiny/textures/item/weapon/w30_extra/keep.png",
                "assets/destiny/textures/item/weapon/wx/keep.png",
                "assets/destiny/textures/item/ability_w255/grenade/keep.png",
                "assets/foreign/textures/item/weapon/w30/keep.png")) files.put(path, resource("PNG"));
        files.put("assets/minecraft/atlases/items.json", resource("""
                {"sources":[{"type":"minecraft:directory","source":"item","prefix":"item/"},
                {"type":"minecraft:single","resource":"destiny:item/weapon/w30/single"}]}
                """));
        var omitted = new HashSet<String>();
        assertEquals(1, PackWeaponTexturePruner.prune(files, omitted));
        assertEquals(Set.of(BASE + "unused.png"), omitted);
    }

    @Test void unknownOrStaleReferenceInventoryFailsClosedWithoutPartialExclusions() {
        var files = new HashMap<String, PackResource>();
        files.put(BASE + "unused.png", resource("PNG"));
        files.put("assets/foreign/custom/broken.json", resource("{broken"));
        var omitted = new HashSet<>(Set.of("already-omitted"));
        assertEquals(0, PackWeaponTexturePruner.prune(files, omitted));
        assertEquals(Set.of("already-omitted"), omitted);
        files.put("assets/foreign/custom/broken.json", resource("null"));
        assertEquals(0, PackWeaponTexturePruner.prune(files, omitted));
        files.put("assets/foreign/custom/broken.json", resource("{}"));
        files.put(BASE + "needed.png", resource("PNG"));
        files.put("assets/foreign/custom/live.json", resource("{\"custom\":\"destiny:item/weapon/w30/needed\"}"));
        omitted.add(BASE + "needed.png");
        assertEquals(0, PackWeaponTexturePruner.prune(files, omitted));
        assertEquals(Set.of("already-omitted", BASE + "needed.png"), omitted);
    }

    private static PackResource resource(String value) { return PackResource.fromString(value); }
}
