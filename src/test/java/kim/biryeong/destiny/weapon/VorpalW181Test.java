package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Catalog/resource tests do not require Vorpal to be added to the shared perk registry. */
class VorpalW181Test {
    private static final Set<String> EXPECTED = Set.of(
        "seventh_seraph_officer_revolver:3037520408:4:3527094473",
        "steelfeather_repeater:1251729046:4:2645685327",
        "patron_of_lost_causes:2723241847:4:120674550",
        "aishas_embrace:2638190703:4:4211351701",
        "farewell:541188001:4:3819615926",
        "whispering_slab:211938782:4:967526625",
        "bite_of_the_fox:1403800851:4:2442672691",
        "first_in_last_out:3616586446:4:1439234589",
        "hollow_words:607191995:4:1485010760",
        "stormchaser:3652506829:4:4213354588",
        "canis_major:2066434718:4:2791121719",
        "dimensional_hypotrochoid:1311684613:4:1092097342",
        "retrofit_escapade:3103325054:4:2461260598",
        "salvager_s_salvo:2060863616:4:254", // W320 curated fixed roll
        "crown_splitter:2782325302:4:99092784",
        "temptation_s_hook:35794111:4:2147541212",
        "nezarec_s_whisper:254636484:4:699056095");

    static JsonObject resource() {
        var stream = VorpalW181Test.class.getResourceAsStream("/destiny/weapons/w181-vorpal.json");
        assertNotNull(stream);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader).getAsJsonObject();
        } catch (java.io.IOException e) { throw new AssertionError(e); }
    }
    static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }

    @Test void exactSixteenOfficialBaseSocketsAcrossCurrentCatalog() {
        assertEquals("vorpal_weapon", VorpalProfile.ID);
        assertEquals(1546637391L, VorpalProfile.HASH);
        var actual = new HashSet<String>();
        for (var r : VorpalProfile.rolls()) {
            assertEquals(1546637391L, r.perkHash());
            assertNotEquals(3418165135L, r.perkHash());
            assertTrue(actual.add(r.id()+":"+r.hash()+":"+r.socket()+":"+r.plugSetHash()));
            assertTrue(VorpalProfile.supports(entry(r.id())));
            assertEquals(r.hash(), WeaponCharacteristics.of(entry(r.id())).bungieHash());
        }
        assertEquals(EXPECTED, actual);
        assertEquals(65, WeaponCatalog.all().size());
        assertEquals(17, WeaponCatalog.all().stream().filter(VorpalProfile::supports).count());
        assertThrows(UnsupportedOperationException.class, () -> VorpalProfile.rolls().clear());
    }

    @Test void sourcedMultipliersAreAmmoBasedIncludingSwordAndGlaiveProjectile() {
        var counts = new EnumMap<WeaponAmmoType, Integer>(WeaponAmmoType.class);
        for (var r : VorpalProfile.rolls()) {
            var e = entry(r.id()); var ammo = WeaponCharacteristics.of(e).ammo();
            counts.merge(ammo, 1, Integer::sum);
            float expected = switch (ammo) { case PRIMARY -> 1.20f; case SPECIAL -> 1.15f; case HEAVY -> 1.10f; };
            assertEquals(expected, VorpalProfile.multiplier(e), e.id());
        }
        assertEquals(Map.of(WeaponAmmoType.PRIMARY, 6, WeaponAmmoType.SPECIAL, 5, WeaponAmmoType.HEAVY, 6), counts);
        assertEquals(1.10f, VorpalProfile.multiplier(entry("crown_splitter")));
        assertEquals(1.15f, VorpalProfile.multiplier(entry("nezarec_s_whisper")));
        assertEquals(1.20f, VorpalProfile.multiplier(entry("whispering_slab")));
    }

    @Test void unsupportedExoticAndEveryForgedCanonicalFieldFailClosed() {
        assertFalse(VorpalProfile.supports(null));
        assertThrows(IllegalArgumentException.class, () -> VorpalProfile.multiplier(null));
        for (var e : WeaponCatalog.all()) if (!EXPECTED.stream().anyMatch(r -> r.startsWith(e.id()+":"))) {
            assertFalse(VorpalProfile.supports(e), e.id());
            assertThrows(IllegalArgumentException.class, () -> VorpalProfile.multiplier(e), e.id());
        }
        var e = entry("first_in_last_out");
        String[] fields = {e.id(), e.family(), e.frame(), e.name(), e.source_frame_label(), e.item_model()};
        for (int i = 0; i < fields.length; i++) for (String bad : new String[]{"forged", null}) {
            var copy = fields.clone(); copy[i] = bad;
            var forged = new WeaponCatalog.Entry(copy[0], copy[1], copy[2], copy[3], copy[4], copy[5]);
            assertFalse(VorpalProfile.supports(forged));
            assertThrows(IllegalArgumentException.class, () -> VorpalProfile.multiplier(forged));
        }
    }

    @Test void strictResourceRejectsMissingExtraDuplicateAndWrongTypes() {
        var source = resource();
        assertDoesNotThrow(() -> VorpalProfile.validateResource(source.toString()));
        for (String key : source.keySet()) {
            var bad = source.deepCopy(); bad.remove(key);
            assertThrows(IllegalStateException.class, () -> VorpalProfile.validateResource(bad.toString()), key);
        }
        var extra = source.deepCopy(); extra.addProperty("durationTicks", 200);
        assertThrows(IllegalStateException.class, () -> VorpalProfile.validateResource(extra.toString()));
        String raw = source.toString();
        for (String bad : Arrays.asList(null, "null", "[]", "{}", raw+" {}", raw.replace("\"W181\"", "\"W181\",\"stage\":\"W181\""),
                raw.replace("1546637391", "\"1546637391\""), raw.replace("1546637391", "1546637391.1")))
            assertThrows(IllegalStateException.class, () -> VorpalProfile.validateResource(bad));
    }

    @Test void missingDuplicateEnhancedWrongSocketItemAndPoolRejected() {
        var source = resource();
        var missing = source.deepCopy(); missing.getAsJsonArray("weapons").remove(0);
        assertThrows(IllegalStateException.class, () -> VorpalProfile.validateResource(missing.toString()));
        var duplicate = source.deepCopy(); duplicate.getAsJsonArray("weapons").set(1, duplicate.getAsJsonArray("weapons").get(0).deepCopy());
        assertThrows(IllegalStateException.class, () -> VorpalProfile.validateResource(duplicate.toString()));
        for (var change : Map.of("perkHash", 3418165135L, "socket", 3L, "hash", 1L, "plugSetHash", 1L).entrySet()) {
            var bad = source.deepCopy(); bad.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty(change.getKey(), change.getValue());
            assertThrows(IllegalStateException.class, () -> VorpalProfile.validateResource(bad.toString()));
        }
    }

    @Test void allThreeExactSourcedScalarsAndSourceReferenceValidated() {
        for (String key : List.of("primaryMultiplier", "specialMultiplier", "heavyMultiplier")) {
            for (var value : List.of(new JsonPrimitive(20), new JsonPrimitive(1), new JsonPrimitive("1.2"), JsonNull.INSTANCE)) {
                var bad = resource(); bad.getAsJsonObject("perk").add(key, value);
                assertThrows(IllegalStateException.class, () -> VorpalProfile.validateResource(bad.toString()), key);
            }
        }
        var bad = resource(); bad.getAsJsonObject("perk").addProperty("damageSource", "unverified");
        assertThrows(IllegalStateException.class, () -> VorpalProfile.validateResource(bad.toString()));
    }
}
