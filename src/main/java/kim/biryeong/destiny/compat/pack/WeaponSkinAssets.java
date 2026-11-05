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
            var lazy = new java.util.LinkedHashMap<String, PackResource>();
            var framing = new HashMap<String, String>();
            for (var e : files.entrySet()) {
                String path = e.getKey();
                if (!path.startsWith("assets/destiny/") || !path.endsWith(".json")) continue;
                // W325: W123 surfaces are mirrored too (rocket/heavy sight leaves use them as parents); their elements
                // are replaced by the skin geometry like any other assembled-gun leaf.
                boolean framed = path.startsWith(FRAMING);
                String renamed = WeaponSkins.rename(skin, path);
                if (!framed && renamed.equals(path)) continue;
                if (!framed && path.startsWith("assets/destiny/items/") && !files.containsKey(renamed)) {
                    // W325: item routes are 10-60 MB each and ~60 skins share a few bases. Mirror them as a lazy textual
                    // rename of the base route (the same edit rewrite() makes: only "destiny:" ids change) so the heap
                    // never holds a parsed tree or a second full copy per skin.
                    lazy.put(renamed, new Renamed(e.getValue(), skin, framing));
                    continue;
                }
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
            result.putAll(lazy);
        }
        return result;
    }

    private static final java.util.regex.Pattern ID = java.util.regex.Pattern.compile("\"(destiny:[^\"\\\\]*)\"");

    /** Lazy renamed copy of a base item route; computed on read, never cached. */
    private record Renamed(PackResource source, WeaponSkins.Skin skin, Map<String, String> framing) implements PackResource {
        @Override public byte[] readAllBytes() {
            var m = ID.matcher(source.asString());
            var sb = new StringBuilder();
            while (m.find()) {
                String s = m.group(1);
                String r = framing.getOrDefault(s, WeaponSkins.rename(skin, s));
                m.appendReplacement(sb, java.util.regex.Matcher.quoteReplacement("\"" + r + "\""));
            }
            m.appendTail(sb);
            return sb.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);
        }
        @Override public java.io.InputStream getStream() { return new java.io.ByteArrayInputStream(readAllBytes()); }
    }

    private static final java.util.List<String> MOVING = java.util.List.of("magazine", "moving", "cylinder", "barrel", "cradle", "lever");
    private static final java.util.Set<String> MOVING_PARTS = java.util.Set.of("magazine", "barrel", "cradle", "lever");

    /** Leaf role: the suffix after the skin id and an optional frame number, without the _native/_twohand grip. */
    static String role(String leafName, String base) {
        var m = java.util.regex.Pattern.compile("(?:^|_)(?:\\d+_)?(magazine|moving|cylinder|barrel|cradle|lever|round|body)(?:_native|_twohand)?$")
                .matcher(leafName);
        return m.find() ? m.group(1) : "whole";
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
        // Reload banks split the gun into a body and moving leaves. W325 roles by leaf suffix:
        //   _magazine/_moving/_cylinder -> parts.magazine; _barrel -> parts.barrel or parts.magazine (salvager-style
        //   break-open GL); _cradle/_lever -> parts.<role> or nothing (pyroclastic loader pieces);
        //   _round -> base round art (like _shell); _body -> every part except moving ones when the bank is split;
        //   any other leaf is the whole assembled gun.
        String role = role(name, skin.base());
        if (role.equals("round")) {
            var t = leaf.getAsJsonObject("textures");
            if (t != null) for (var key : new ArrayList<>(t.keySet()))
                t.addProperty(key, t.get(key).getAsString().replace(skin.id(), skin.base()));
            return leaf;
        }
        String baseDir = dir.replace(skin.id(), skin.base());
        boolean split = false;
        for (String r : MOVING) split |= files.containsKey(baseDir + skin.base() + "_" + r + ".json");
        java.util.List<String> use = new java.util.ArrayList<>();
        switch (role) {
            case "magazine", "moving", "cylinder" -> use.add("magazine");
            case "barrel" -> use.add(p.has("barrel") ? "barrel" : "magazine");
            case "cradle", "lever" -> { if (p.has(role)) use.add(role); }
            case "body" -> { for (var key : p.keySet()) if (!split || !MOVING_PARTS.contains(key)) use.add(key); }
            default -> use.addAll(p.keySet());
        }
        for (var key : use) if (p.has(key)) for (var el : p.getAsJsonArray(key)) elements.add(el.deepCopy());
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
            // Skin HUD silhouettes live outside the closed W112 set: skin.hud() (w302/ or w325/ ammo_<skin>.png).
            for (var key : new ArrayList<>(t.keySet()))
                if (t.get(key).getAsString().equals("destiny:item/hud/ammo_weapon_w112_" + skin.id()))
                    t.addProperty(key, skin.hud());
            return t;
        }
        t.addProperty("0", skin.texture());
        t.addProperty("particle", skin.texture());
        return t;
    }

    static String utf8(byte[] b) { return new String(b, StandardCharsets.UTF_8); }
}
