package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Catalog/resource tests do not require High-Impact Reserves to be added to the shared perk registry. */
class HighImpactReservesW182Test {
    private static final Set<String> EXPECTED = Set.of(
        "seventh_seraph_officer_revolver:3037520408:4:3527094473",
        "bygones:2712244741:3:1760176771",
        "chattering_bone:568515759:4:423791138",
        "blast_furnace:3843477312:4:169306153",
        "claws_of_the_wolf:1280933460:4:753756428",
        "long_arm:8293111:4:619833418",
        "bug_out_bag:2744715540:4:575371383",
        "high_albedo:1197486957:4:718633408",
        "dream_breaker:2931957300:4:1206254527",
        "null_composure:1644680957:4:273", // W320 curated fixed roll
        "hammerhead:603242241:4:2479293397");

    static JsonObject resource() {
        var stream = HighImpactReservesW182Test.class.getResourceAsStream("/destiny/weapons/w182-high_impact_reserves.json");
        assertNotNull(stream);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader).getAsJsonObject();
        } catch (java.io.IOException e) { throw new AssertionError(e); }
    }
    static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }

    @Test void exactTenOfficialBaseSocketsAcrossCurrentCatalog() {
        assertEquals("high_impact_reserves", HighImpactReservesProfile.ID);
        assertEquals(2213355989L, HighImpactReservesProfile.HASH);
        var actual = new HashSet<String>();
        for (var r : HighImpactReservesProfile.rolls()) {
            assertEquals(2213355989L, r.perkHash());
            assertNotEquals(2002547233L, r.perkHash());
            assertTrue(actual.add(r.id()+":"+r.hash()+":"+r.socket()+":"+r.plugSetHash()));
            assertTrue(HighImpactReservesProfile.supports(entry(r.id())));
            assertEquals(r.hash(), WeaponCharacteristics.of(entry(r.id())).bungieHash());
        }
        assertEquals(EXPECTED, actual);
        assertEquals(65, WeaponCatalog.all().size());
        assertEquals(11, WeaponCatalog.all().stream().filter(HighImpactReservesProfile::supports).count());
        assertThrows(UnsupportedOperationException.class, () -> HighImpactReservesProfile.rolls().clear());
    }

    static int capacity(WeaponCatalog.Entry entry) { return WeaponProfile.forEntry(entry).magazine(); }
    @Test void publishedEndpointsAndCanonicalEvenOddThresholds() {
        for (var roll : HighImpactReservesProfile.rolls()) {
            var e = entry(roll.id()); int cap = capacity(e);
            assertEquals(1f, HighImpactReservesProfile.multiplier(e, cap / 2 + 2, cap), e.id());
            assertEquals(e.family().equals("fusion_rifle") ? 1.103f : 1.121f,
                HighImpactReservesProfile.multiplier(e, cap / 2 + 1, cap), e.id());
            assertEquals(e.family().equals("fusion_rifle") ? 1.229f : 1.256f,
                HighImpactReservesProfile.multiplier(e, 1, cap), e.id());
        }
        assertEquals(11, capacity(entry("seventh_seraph_officer_revolver")));
        assertEquals(14, capacity(entry("long_arm")));
        assertEquals(38, capacity(entry("bygones")));
        assertEquals(6, capacity(entry("dream_breaker")));
    }

    @Test void concreteMeasuredAdaptationFixturesPreservePlateausAndNonuniformRungs() {
        // Expected decimals from the published40-round damage table normalized to Clarity endpoints.
        // This verifies the stated local projection; it does NOT establish current Destiny fidelity.
        float[] officer = {1.256f,1.256f,1.175f,1.148f,1.1230769f,1.121f,1f};
        float[] fusion = {1.229f,1.1766615f,1.1049385f,1.103f,1f,1f};
        float[] bygones = {1.256f,1.256f,1.256f,1.256f,1.229f,1.2040769f,1.1999231f,
            1.175f,1.1729231f,1.1500769f,1.148f,1.1459231f,1.1438462f,1.1230769f,
            1.1230769f,1.1230769f,1.1230769f,1.1230769f,1.121f,1.121f,1f};
        var ids = List.of("seventh_seraph_officer_revolver","dream_breaker","bygones");
        var fixtures = List.of(officer,fusion,bygones);
        for (int i=0;i<ids.size();i++) {
            var e=entry(ids.get(i)); var expected=fixtures.get(i);
            for (int before=1;before<=expected.length;before++)
                assertEquals(expected[before-1],HighImpactReservesProfile.multiplier(e,before,capacity(e)),
                    0.0000002f,e.id()+" pre="+before);
        }
        // Earlier data plateau reaches maximum at more than the current DDC's7.5%.
        // Preserve and expose the discrepancy rather than silently claiming a fresh current curve.
        assertEquals(1.256f, HighImpactReservesProfile.multiplier(entry("bygones"),4,38));
    }

    @Test void everySupportedMagazineHasFiniteBoundedMonotoneScalars() {
        for (var roll : HighImpactReservesProfile.rolls()) {
            var e = entry(roll.id()); int cap = capacity(e); float previous = 1f;
            for (int rounds = cap; rounds >= 1; rounds--) {
                float scalar = HighImpactReservesProfile.multiplier(e, rounds, cap);
                assertTrue(Float.isFinite(scalar));
                assertTrue(scalar >= previous && scalar <= (e.family().equals("fusion_rifle") ? 1.229f : 1.256f));
                assertEquals((rounds - 1) * 2L > cap, scalar == 1f);
                previous = scalar;
            }
        }
    }

    @Test void zeroNegativeOverflowAndNoncanonicalCapacityRejectedRatherThanClamped() {
        for (var roll : HighImpactReservesProfile.rolls()) {
            var e = entry(roll.id()); int cap = capacity(e);
            for (int rounds : new int[]{Integer.MIN_VALUE, -1, 0, cap+1, Integer.MAX_VALUE})
                assertThrows(IllegalArgumentException.class, () -> HighImpactReservesProfile.multiplier(e, rounds, cap));
            for (int badCap : new int[]{Integer.MIN_VALUE, -1, 0, 1, cap-1, cap+1, cap*2, Integer.MAX_VALUE})
                assertThrows(IllegalArgumentException.class, () -> HighImpactReservesProfile.multiplier(e, 1, badCap));
        }
    }

    @Test void unsupportedExoticAndEveryForgedCanonicalFieldFailClosed() {
        assertFalse(HighImpactReservesProfile.supports(null));
        assertThrows(IllegalArgumentException.class, () -> HighImpactReservesProfile.multiplier(null, 1, 11));
        for (var e : WeaponCatalog.all()) if (!EXPECTED.stream().anyMatch(r -> r.startsWith(e.id()+":"))) {
            assertFalse(HighImpactReservesProfile.supports(e), e.id());
            assertThrows(IllegalArgumentException.class, () -> HighImpactReservesProfile.multiplier(e, 1, 11), e.id());
        }
        var e = entry("seventh_seraph_officer_revolver");
        String[] fields = {e.id(), e.family(), e.frame(), e.name(), e.source_frame_label(), e.item_model()};
        for (int i = 0; i < fields.length; i++) for (String bad : new String[]{"forged", null}) {
            var copy = fields.clone(); copy[i] = bad;
            var forged = new WeaponCatalog.Entry(copy[0], copy[1], copy[2], copy[3], copy[4], copy[5]);
            assertFalse(HighImpactReservesProfile.supports(forged));
            assertThrows(IllegalArgumentException.class, () -> HighImpactReservesProfile.multiplier(forged, 1, 11));
        }
    }

    @Test void strictResourceRejectsMissingExtraDuplicateAndWrongTypes() {
        var source = resource();
        assertDoesNotThrow(() -> HighImpactReservesProfile.validateResource(source.toString()));
        for (String key : source.keySet()) {
            var bad = source.deepCopy(); bad.remove(key);
            assertThrows(IllegalStateException.class, () -> HighImpactReservesProfile.validateResource(bad.toString()), key);
        }
        var extra = source.deepCopy(); extra.addProperty("durationTicks", 200);
        assertThrows(IllegalStateException.class, () -> HighImpactReservesProfile.validateResource(extra.toString()));
        String raw = source.toString();
        for (String bad : Arrays.asList(null, "null", "[]", "{}", raw+" {}", raw.replace("\"W182\"", "\"W182\",\"stage\":\"W182\""),
                raw.replace("2213355989", "\"2213355989\""), raw.replace("2213355989", "2213355989.1")))
            assertThrows(IllegalStateException.class, () -> HighImpactReservesProfile.validateResource(bad));
    }

    @Test void missingDuplicateEnhancedWrongSocketItemAndPoolRejected() {
        var source = resource();
        var missing = source.deepCopy(); missing.getAsJsonArray("weapons").remove(0);
        assertThrows(IllegalStateException.class, () -> HighImpactReservesProfile.validateResource(missing.toString()));
        var duplicate = source.deepCopy(); duplicate.getAsJsonArray("weapons").set(1, duplicate.getAsJsonArray("weapons").get(0).deepCopy());
        assertThrows(IllegalStateException.class, () -> HighImpactReservesProfile.validateResource(duplicate.toString()));
        for (var change : Map.of("perkHash", 2002547233L, "socket", 63L, "hash", 1L, "plugSetHash", 1L).entrySet()) {
            var bad = source.deepCopy(); bad.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty(change.getKey(), change.getValue());
            assertThrows(IllegalStateException.class, () -> HighImpactReservesProfile.validateResource(bad.toString()));
        }
    }

    @Test void allExactSourcedEndpointsAndSourceReferenceValidated() {
        for (String key : List.of("normalMinimum", "normalMaximum", "fusionMinimum", "fusionMaximum")) {
            for (var value : List.of(new JsonPrimitive(20), new JsonPrimitive(1), new JsonPrimitive("1.2"), new JsonPrimitive(Double.NaN), new JsonPrimitive(Double.POSITIVE_INFINITY), JsonNull.INSTANCE)) {
                var bad = resource(); bad.getAsJsonObject("perk").add(key, value);
                assertThrows(IllegalStateException.class, () -> HighImpactReservesProfile.validateResource(bad.toString()), key);
            }
        }
        var bad = resource(); bad.getAsJsonObject("perk").addProperty("damageSource", "unverified");
        assertThrows(IllegalStateException.class, () -> HighImpactReservesProfile.validateResource(bad.toString()));
    }
}
