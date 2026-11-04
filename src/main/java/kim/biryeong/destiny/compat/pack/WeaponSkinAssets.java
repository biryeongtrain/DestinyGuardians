package kim.biryeong.destiny.compat.pack;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonPrimitive;
import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.ResourcePackBuilder;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.weapon.WeaponSkins;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

/**
 * W302 pack-time mirror of a base weapon's whole client asset tree for each {@link WeaponSkins.Skin}.
 * Item/route JSON and animation pose/framing leaves are copied with the base id token renamed (so every reload, ADS,
 * inspect and first-person-arm frame is identical); the geometry leaves get the skin's authored parts
 * ({@code models/weapon_skin_w302/<skin>.json}: {@code {"textures":..,"parts":{"body":[..],"magazine":[..]}}}),
 * keeping each leaf's display transforms and its non-weapon overlay elements (ADS aim tips).
 * Runs on the pre-finish snapshot before route compaction; source resources are not modified.
 */
public final class WeaponSkinAssets {
    private static final String FRAMING = "assets/destiny/models/first_person_framing_w205/";
    private WeaponSkinAssets() {}

    public static int mirror(ResourcePackBuilder builder, Map<String, PackResource> files) {
        var planned = plan(files);
        planned.forEach((path, res) -> { builder.addData(path, res); files.put(path, res); });
        DestinyGuardians.LOGGER.info("W302 weapon skins: {} mirrored client assets", planned.size());
        return planned.size();
    }

    /** Pure: the mirrored resources for every skin (files is not modified). */
    public static Map<String, PackResource> plan(Map<String, PackResource> files) {
        var result = new java.util.LinkedHashMap<String, PackResource>();
        for (var skin : WeaponSkins.ALL) {
            String partsPath = "/destiny/weapon_skins/" + skin.id() + ".json";
            JsonObject parts;
            try (var in = WeaponSkinAssets.class.getResourceAsStream(partsPath)) {
                if (in == null) { DestinyGuardians.LOGGER.warn("Weapon skin {} has no parts {}", skin.id(), partsPath); continue; }
                parts = JsonParser.parseString(utf8(in.readAllBytes())).getAsJsonObject();
            } catch (java.io.IOException ex) { throw new IllegalStateException(ex); }
            var out = new HashMap<String, JsonObject>();
            var framing = new HashMap<String, String>();
            for (var e : files.entrySet()) {
                String path = e.getKey();
                if (!path.startsWith("assets/destiny/") || !path.endsWith(".json")) continue;
                if (path.startsWith("assets/destiny/models/weapon_surface_w123/")) continue;
                boolean framed = path.startsWith(FRAMING);
                String renamed = WeaponSkins.rename(skin, path);
                if (!framed && renamed.equals(path)) continue;
                String text = e.getValue().asString();
                if (framed && !text.contains(skin.base())) continue;
                if (framed) renamed = path.substring(0, path.length() - 5) + "_" + skin.id() + ".json";
                if (files.containsKey(renamed)) continue; // never shadow an authored asset
                var json = JsonParser.parseString(text);
                if (!json.isJsonObject()) continue;
                if (framed) framing.put(id(path), id(renamed));
                out.put(renamed, json.getAsJsonObject());
            }
            for (var e : out.entrySet()) {
                var json = e.getValue();
                rewrite(json, skin, framing);
                if (json.has("elements")) json = geometry(json, e.getKey(), skin, parts, files);
                result.put(e.getKey(), PackResource.fromString(json.toString()));
            }
        }
        return result;
    }

    private static String id(String path) {
        return "destiny:" + path.substring("assets/destiny/models/".length(), path.length() - 5);
    }

    private static void rewrite(JsonElement el, WeaponSkins.Skin skin, Map<String, String> framing) {
        if (el.isJsonObject()) {
            var o = el.getAsJsonObject();
            for (var key : new ArrayList<>(o.keySet())) {
                var v = o.get(key);
                if (v.isJsonPrimitive() && v.getAsJsonPrimitive().isString()) {
                    String s = v.getAsString();
                    String r = framing.getOrDefault(s, s.startsWith("destiny:") ? WeaponSkins.rename(skin, s) : s);
                    if (!r.equals(s)) o.add(key, new JsonPrimitive(r));
                } else rewrite(v, skin, framing);
            }
        } else if (el.isJsonArray()) {
            var a = el.getAsJsonArray();
            for (int i = 0; i < a.size(); i++) {
                var v = a.get(i);
                if (v.isJsonPrimitive() && v.getAsJsonPrimitive().isString()) {
                    String s = v.getAsString();
                    String r = framing.getOrDefault(s, s.startsWith("destiny:") ? WeaponSkins.rename(skin, s) : s);
                    if (!r.equals(s)) a.set(i, new JsonPrimitive(r));
                } else rewrite(v, skin, framing);
            }
        }
    }

    /** Replace a base geometry leaf with the skin parts, keeping display and overlay elements. */
    private static JsonObject geometry(JsonObject leaf, String path, WeaponSkins.Skin skin, JsonObject parts,
                                       Map<String, PackResource> files) {
        String name = path.substring(path.lastIndexOf('/') + 1, path.length() - 5);
        String dir = path.substring(0, path.lastIndexOf('/') + 1);
        var p = parts.getAsJsonObject("parts");
        var elements = new JsonArray();
        // A HUD sprite (single layer quad) is not weapon geometry.
        if (path.startsWith("assets/destiny/models/gui/")) {
            leaf.add("textures", textures(leaf, skin, true));
            return leaf;
        }
        if (name.endsWith("_shell") || name.endsWith("_shell_hidden")) {
            // Shared loose round keeps the base weapon's shell art.
            var t = leaf.getAsJsonObject("textures");
            if (t != null) for (var key : new ArrayList<>(t.keySet()))
                t.addProperty(key, t.get(key).getAsString().replace(skin.id(), skin.base()));
            return leaf;
        }
        // Reload banks split the gun into a body and one moving magazine leaf ("_magazine" or "_moving");
        // any other leaf is the whole assembled gun.
        boolean magazineLeaf = name.endsWith("_magazine") || name.endsWith("_moving");
        String baseDir = dir.replace(skin.id(), skin.base());
        boolean split = files.containsKey(baseDir + skin.base() + "_magazine.json")
                || files.containsKey(baseDir + skin.base() + "_moving.json");
        for (var key : p.keySet()) {
            boolean isMag = key.equals("magazine");
            if (magazineLeaf ? !isMag : (split && name.endsWith("_body") && isMag)) continue;
            for (var el : p.getAsJsonArray(key)) elements.add(el.deepCopy());
        }
        // Keep overlay elements that do not paint with the weapon atlas (e.g. W151/W148 ADS aim tips).
        // "no_overlay": the skin paints its own reticle (W302 Khvostov hairline holo), so drop the W148 aim dot.
        boolean keepOverlay = !(parts.has("no_overlay") && parts.get("no_overlay").getAsBoolean());
        if (keepOverlay) for (var el : leaf.getAsJsonArray("elements")) {
            var faces = el.getAsJsonObject().getAsJsonObject("faces");
            boolean overlay = faces != null && !faces.entrySet().isEmpty() && faces.entrySet().stream()
                    .allMatch(f -> !"#0".equals(f.getValue().getAsJsonObject().get("texture").getAsString()));
            if (overlay) elements.add(el.deepCopy());
        }
        var out = new JsonObject();
        for (var key : leaf.keySet()) if (!key.equals("elements") && !key.equals("textures")) out.add(key, leaf.get(key).deepCopy());
        out.add("textures", textures(leaf, skin, false));
        if (parts.has("texture_size")) out.add("texture_size", parts.get("texture_size").deepCopy());
        out.add("elements", elements);
        return out;
    }

    private static JsonObject textures(JsonObject leaf, WeaponSkins.Skin skin, boolean hud) {
        var t = leaf.has("textures") ? leaf.getAsJsonObject("textures").deepCopy() : new JsonObject();
        if (hud) {
            // Skin HUD silhouettes live outside the closed W112 set: textures/item/hud/w302/ammo_<skin>.png.
            for (var key : new ArrayList<>(t.keySet()))
                if (t.get(key).getAsString().equals("destiny:item/hud/ammo_weapon_w112_" + skin.id()))
                    t.addProperty(key, "destiny:item/hud/w302/ammo_" + skin.id());
            return t;
        }
        t.addProperty("0", skin.texture());
        t.addProperty("particle", skin.texture());
        return t;
    }

    static String utf8(byte[] b) { return new String(b, StandardCharsets.UTF_8); }
}
