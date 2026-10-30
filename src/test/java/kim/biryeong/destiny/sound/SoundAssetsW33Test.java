package kim.biryeong.destiny.sound;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.hud.SuperHudCue;
import org.junit.jupiter.api.Test;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import static org.junit.jupiter.api.Assertions.*;

class SoundAssetsW33Test {
    private JsonObject definitions() throws Exception {
        try (var in = getClass().getResourceAsStream("/assets/destiny/sounds.json")) {
            assertNotNull(in);
            return JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }
    @Test void allPackReferencesAreNamespacedMonoVorbisWithBoundedSize() throws Exception {
        var root = definitions();
        ReviewedAudioW234.legacyW102(root);
        var laterSounds = ReviewedAudioW234.laterSoundIds();
        assertFalse(root.isEmpty());
        var seen = new HashSet<String>();
        int totalBytes = 0;
        var izanagiSounds = new HashSet<>(java.util.Set.of(
                "destiny:w84/izanagis_burden/fire_reg_1", "destiny:w84/izanagis_burden/fire_reg_2",
                "destiny:w84/izanagis_burden/fire_reg_3", "destiny:w84/izanagis_burden/reload_1",
                "destiny:w84/izanagis_burden/reload_2", "destiny:w84/izanagis_burden/fire_honed_1",
                "destiny:w84/izanagis_burden/fire_honed_2", "destiny:w84/izanagis_burden/reload_honed_2",
                "destiny:w84/reload/izanagis_burden_honed_61"));
        // The dedicated Honed61 event is not in the ordinary id/ticks lookup. Validate its
        // exact sidecar definition separately; never exempt an arbitrary W84 sound prefix.
        var w84 = JsonParser.parseString(java.nio.file.Files.readString(java.nio.file.Path.of(
                "art/weapons/w84/audio/event-definitions.json"))).getAsJsonObject();
        assertEquals(w84.get("weapon.reload_w84.izanagis_burden.honed.61"),
                root.get("weapon.reload_w84.izanagis_burden.honed.61"));
        assertEquals("destiny:w84/reload/izanagis_burden_honed_61", root.getAsJsonObject(
                "weapon.reload_w84.izanagis_burden.honed.61").getAsJsonArray("sounds")
                .get(0).getAsJsonObject().get("name").getAsString());
        // Only canonical runtime-validated ordinary timed clips join the finite supplied W84 source set.
        for (var clip : ReloadAudioProfile.all()) if (clip.id().equals("izanagis_burden")) {
            assertTrue(clip.asset().startsWith("assets/destiny/sounds/w84/") && clip.asset().endsWith(".ogg"));
            izanagiSounds.add("destiny:" + clip.asset().substring("assets/destiny/sounds/".length(), clip.asset().length() - 4));
        }
        // W102 explicitly admits these sixteen pinned named resources, never the whole namespace.
        var w102Sounds = new HashSet<String>();
        for (String id : java.util.Set.of("blast_furnace", "chattering_bone", "aishas_embrace", "long_arm", "whispering_slab", "retrofit_escapade"))
            w102Sounds.add("destiny:w102/" + id + "/fire");
        for (String id : java.util.Set.of("blast_furnace", "chattering_bone", "aishas_embrace", "retrofit_escapade"))
            w102Sounds.add("destiny:w102/" + id + "/reload");
        for (String pair : java.util.Set.of("aishas_embrace:46", "blast_furnace:24", "blast_furnace:43", "chattering_bone:24", "chattering_bone:34", "retrofit_escapade:90")) {
            var parts = pair.split(":");
            w102Sounds.add("destiny:w102/" + parts[0] + "/reload_" + parts[1]);
        }
        assertEquals(16, w102Sounds.size());
        for (var event : root.entrySet()) {
            assertTrue(event.getKey().matches("[a-z0-9_.]+"));
            var values = event.getValue().getAsJsonObject().getAsJsonArray("sounds");
            assertFalse(values.isEmpty(), event.getKey());
            for (var value : values) {
                var name = value.isJsonPrimitive() ? value.getAsString() : value.getAsJsonObject().get("name").getAsString();
                if (value.isJsonObject() && value.getAsJsonObject().has("type")
                        && value.getAsJsonObject().get("type").getAsString().equals("event")) {
                    assertTrue(name.startsWith("destiny:") && root.has(name.substring(8)), "Resolvable alias: " + name);
                    continue;
                }
                assertTrue(name.startsWith("destiny:w33/") || name.startsWith("destiny:w34/") || name.startsWith("destiny:w36/") || name.startsWith("destiny:w56/") || name.startsWith("destiny:w63/reload/")
                        || java.util.Set.of("destiny:w83/ace_of_spades/fire", "destiny:w83/ace_of_spades/reload",
                                "destiny:w83/reload/ace_of_spades_55", "destiny:w83/reload/ace_of_spades_39").contains(name) || izanagiSounds.contains(name)
                        // W98 admits only these six individually pinned named alternatives, never an arbitrary namespace.
                        || java.util.Set.of("destiny:w98/seventh_seraph_officer_revolver/fire_2", "destiny:w98/seventh_seraph_officer_revolver/fire_3",
                                "destiny:w98/steelfeather_repeater/fire_2", "destiny:w98/steelfeather_repeater/fire_3",
                                "destiny:w98/the_recluse/fire_2", "destiny:w98/the_recluse/fire_3").contains(name) || w102Sounds.contains(name) || laterSounds.contains(name), name);
                if (!seen.add(name)) continue;
                try (var stream = getClass().getResourceAsStream("/assets/destiny/sounds/" + name.substring(8) + ".ogg")) {
                    assertNotNull(stream, name);
                    byte[] bytes = stream.readAllBytes(); totalBytes += bytes.length;
                    assertTrue(bytes.length > 64, name);
                    assertEquals("OggS", new String(bytes, 0, 4, StandardCharsets.US_ASCII));
                    int i = -1;
                    for (int j = 0; j < Math.min(200, bytes.length - 16); j++)
                        if (bytes[j] == 1 && new String(bytes, j + 1, 6, StandardCharsets.US_ASCII).equals("vorbis")) { i = j; break; }
                    assertTrue(i >= 0, "Vorbis identification: " + name);
                    assertEquals(1, bytes[i + 11], "Positional effects must be mono: " + name);
                }
            }
        }
        assertTrue(seen.containsAll(w102Sounds), "All sixteen exact W102 references are covered");
        assertTrue(totalBytes < 32 * 1024 * 1024, "Bound resource-pack download size");
    }
    @Test void allWeaponFamiliesHaveAnExplicitFireMapping() throws Exception {
        var root = definitions();
        for (var entry : WeaponCatalog.all()) assertTrue(root.has("weapon." + entry.family() + ".fire"), entry.family());
        for (String element : new String[]{"arc", "solar", "void"}) {
            assertTrue(root.has("hunter." + element + ".super.start"), element);
            assertTrue(root.has("hunter." + element + ".super.fire"), element);
            assertTrue(root.has("hunter." + element + ".grenade.impact"), element);
            assertTrue(root.has("hunter." + element + ".melee.cast"), element);
        }
        assertTrue(root.has("ui.super_ready"));
    }
    @Test void exactAliasesDoNotLeakToOtherModelsAndMissingImpactsStayUnmapped() {
        var exact = WeaponCatalog.find("cold_denial").orElseThrow();
        assertEquals("weapon.cold_denial.fire", DestinySounds.weaponKey(exact, "fire"));
        var familyOnly = WeaponCatalog.find("duke_mk_44").orElseThrow();
        assertEquals("weapon.hand_cannon.fire", DestinySounds.weaponKey(familyOnly, "fire"));
        for (var entry : WeaponCatalog.all()) {
            assertTrue(DestinySounds.has(DestinySounds.weaponKey(entry, "fire")));
        }
        assertEquals("weapon.pulse_rifle.impact", DestinySounds.weaponKey(exact, "impact"));
        assertFalse(DestinySounds.has(DestinySounds.weaponKey(exact, "impact")));
    }
    @Test void readyAudioEdgeReturnsOnceEvenWithSameTickRedrawAndLoadoutChanges() {
        var cue = new SuperHudCue();
        assertFalse(cue.sample(1, "arc", true, false)); // Joining full is not a charge.
        assertFalse(cue.sample(2, "arc", false, false));
        assertTrue(cue.sample(3, "arc", true, false));
        for (int i = 0; i < 64; i++) assertFalse(cue.sample(3, "arc", true, false));
        assertFalse(cue.sample(4, "void", true, false));
        assertFalse(cue.sample(5, "void", false, true));
        assertFalse(cue.sample(6, "void", false, false));
        assertTrue(cue.sample(7, "void", true, false));
    }
}
