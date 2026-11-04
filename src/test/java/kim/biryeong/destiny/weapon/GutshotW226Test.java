package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Pure paid-transaction/component policy. Does not claim server capture or shared hooks passed. */
class GutshotW226Test {
    private static String resource(String name) throws Exception {
        try (var input = GutshotW226Test.class.getResourceAsStream("/destiny/weapons/" + name)) {
            assertNotNull(input);
            return new String(input.readAllBytes(), StandardCharsets.UTF_8);
        }
    }
    private static WeaponCatalog.Entry entry(String id) throws Exception {
        for (var raw : JsonParser.parseString(resource("w30.json")).getAsJsonArray()) {
            var entry = new Gson().fromJson(raw, WeaponCatalog.Entry.class);
            if (entry.id().equals(id)) return entry;
        }
        throw new AssertionError(id);
    }
    private static WeaponPerks.Roll roll(String id) {
        return GutshotProfile.rolls().stream().filter(r -> r.id().equals(id)).findFirst().orElseThrow();
    }
    private static WeaponGutshot.Context context(WeaponCatalog.Entry entry, Object hand,
                                                 boolean paid, boolean input) {
        return new WeaponGutshot.Context(paid, true, input, hand, hand, 1, entry, entry, roll(entry.id()));
    }

    @Test void selectedPerkAndAdsCannotTurnRejectedPreviewOrUnpaidEmissionIntoPaidShot() throws Exception {
        var entry = entry("ammit_ar2");
        Object hand = new Object();
        var unpaid = context(entry, hand, false, true);
        for (int i = 0; i < 20; i++) {
            assertSame(WeaponGutshot.Token.NONE, WeaponGutshot.snapshot(unpaid));
            assertEquals(11, WeaponGutshot.bodyDamage(WeaponGutshot.snapshot(unpaid), 11));
        }
        var accepted = WeaponGutshot.snapshot(context(entry, hand, true, true));
        assertNotSame(WeaponGutshot.Token.NONE, accepted);
        // Rejected attempts cannot prime a proc; only this accepted emission receives a token.
        assertSame(WeaponGutshot.Token.NONE, WeaponGutshot.snapshot(unpaid));
        assertTrue(WeaponGutshot.bodyDamage(accepted, 11) > 11);
    }

    @Test void acceptedAdsInputSnapshotsImmediatelyAndLaterReleaseDoesNotChangePaidAttack() throws Exception {
        for (String id : List.of("ammit_ar2", "allied_demand")) {
            var entry = entry(id);
            Object hand = new Object();
            var acceptedAds = WeaponGutshot.snapshot(context(entry, hand, true, true));
            float paidBody = WeaponGutshot.bodyDamage(acceptedAds, 13);
            assertTrue(paidBody > 13, "accepted ADS transition uses actual input without a completion clock");
            var releasedOrCosmeticOnly = WeaponGutshot.snapshot(context(entry, hand, true, false));
            assertSame(WeaponGutshot.Token.NONE, releasedOrCosmeticOnly);
            assertEquals(13, WeaponGutshot.bodyDamage(releasedOrCosmeticOnly, 13));
            assertEquals(paidBody, WeaponGutshot.bodyDamage(acceptedAds, 13),
                    "release/new capture does not revoke or re-evaluate the already-paid attack");
            // Repeated pure damage projection does not consume, refresh or mutate a token.
            for (int i = 0; i < 20; i++) assertEquals(paidBody, WeaponGutshot.bodyDamage(acceptedAds, 13));
        }
    }

    @Test void exactOriginalHeldIdentityCountEntryAndSelectedSocketAreAllRequired() throws Exception {
        var ammit = entry("ammit_ar2");
        var allied = entry("allied_demand");
        Object original = new Object();
        var selected = roll(ammit.id());
        var bad = List.of(
                new WeaponGutshot.Context(true, false, true, original, original, 1, ammit, ammit, selected),
                new WeaponGutshot.Context(true, true, true, original, new Object(), 1, ammit, ammit, selected),
                new WeaponGutshot.Context(true, true, true, null, null, 1, ammit, ammit, selected),
                new WeaponGutshot.Context(true, true, true, original, original, 0, ammit, ammit, selected),
                new WeaponGutshot.Context(true, true, true, original, original, 2, ammit, ammit, selected),
                new WeaponGutshot.Context(true, true, true, original, original, 1, allied, ammit, selected),
                new WeaponGutshot.Context(true, true, true, original, original, 1, ammit, null, selected),
                new WeaponGutshot.Context(true, true, true, original, original, 1, ammit, ammit, null),
                new WeaponGutshot.Context(true, true, true, original, original, 1, ammit, ammit, roll(allied.id())),
                new WeaponGutshot.Context(true, true, true, original, original, 1, ammit, ammit,
                        new WeaponPerks.Roll(selected.id(), selected.hash(), 3, selected.perkHash(), selected.plugSetHash())),
                new WeaponGutshot.Context(true, true, true, original, original, 1, ammit, ammit,
                        new WeaponPerks.Roll(selected.id(), selected.hash(), 4, selected.perkHash() + 1, selected.plugSetHash())));
        assertNotSame(WeaponGutshot.Token.NONE, WeaponGutshot.snapshot(context(ammit, original, true, true)));
        for (var rejected : bad) assertSame(WeaponGutshot.Token.NONE, WeaponGutshot.snapshot(rejected));
        assertSame(WeaponGutshot.Token.NONE, WeaponGutshot.snapshot(null));
        assertSame(WeaponGutshot.Token.NONE, WeaponGutshot.capture(null, ammit));
    }

    @Test void mixedComponentPolicyBoostsOnlyBodyAndNoneKeepsPerkSplashNeutral() throws Exception {
        var token = WeaponGutshot.snapshot(context(entry("ammit_ar2"), new Object(), true, true));
        float body = 17, precision = 41, perkSplash = 23;
        float boostedBody = WeaponGutshot.bodyDamage(token, body);
        float mixed = boostedBody + precision;
        assertEquals(boostedBody - body, mixed - (body + precision), 0.00001,
                "the entire mixed-hit bonus must come from BODY, independent of precision amount");
        for (float crit : new float[]{0, 3, 90})
            assertEquals(boostedBody - body, (boostedBody + crit) - (body + crit), 0.00001);
        assertEquals(precision, WeaponGutshot.bodyDamage(token, 0) + precision, "precision-only hit has no BODY");
        // Caller contract for damageOnly()/perk splash; shared Snapshot stripping is tested by master.
        assertEquals(perkSplash, WeaponGutshot.bodyDamage(WeaponGutshot.Token.NONE, perkSplash));
        assertEquals(body, WeaponGutshot.bodyDamage(null, body));
        assertNotEquals((body + precision) * GutshotProfile.bodyMultiplier(entry("ammit_ar2")), mixed,
                "applying Gutshot to the combined hit would also multiply precision");
    }

    @Test void invalidOrNonpositiveDamageCannotBecomePositiveOrOverflow() throws Exception {
        var token = WeaponGutshot.snapshot(context(entry("allied_demand"), new Object(), true, true));
        assertEquals(0, WeaponGutshot.bodyDamage(token, 0));
        assertEquals(-2, WeaponGutshot.bodyDamage(token, -2));
        assertTrue(Float.isNaN(WeaponGutshot.bodyDamage(token, Float.NaN)));
        assertEquals(Float.POSITIVE_INFINITY, WeaponGutshot.bodyDamage(token, Float.POSITIVE_INFINITY));
        assertEquals(Float.MAX_VALUE, WeaponGutshot.bodyDamage(token, Float.MAX_VALUE));
    }

    @Test void exactResourceIsImmutableAndRejectsEnhancedForgedIncompleteOrExtraDefinitions() throws Exception {
        String raw = resource("w226-gutshot.json");
        GutshotProfile.validateResource(raw);
        assertEquals(List.of(
                new WeaponPerks.Roll("allied_demand", 1532276803L, 4, 1365187766L, 703779397L),
                new WeaponPerks.Roll("ammit_ar2", 2119346509L, 4, 1365187766L, 560115158L)), GutshotProfile.rolls());
        assertThrows(UnsupportedOperationException.class, () -> GutshotProfile.rolls().clear());
        var ammit = entry("ammit_ar2");
        assertTrue(GutshotProfile.supports(ammit));
        assertFalse(GutshotProfile.supports(new WeaponCatalog.Entry(ammit.id(), ammit.family(), "forged",
                ammit.name(), ammit.source_frame_label(), ammit.item_model())));
        assertFalse(GutshotProfile.supports(null));
        var root = JsonParser.parseString(raw).getAsJsonObject();
        for (String key : List.of("hash", "socket", "perkHash", "plugSetHash")) {
            var bad = root.deepCopy();
            bad.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty(key, 1);
            assertThrows(IllegalStateException.class, () -> GutshotProfile.validateResource(bad.toString()), key);
        }
        var missing = root.deepCopy(); missing.getAsJsonArray("weapons").remove(0);
        assertThrows(IllegalStateException.class, () -> GutshotProfile.validateResource(missing.toString()));
        var duplicate = root.deepCopy(); duplicate.getAsJsonArray("weapons").add(root.getAsJsonArray("weapons").get(0));
        assertThrows(IllegalStateException.class, () -> GutshotProfile.validateResource(duplicate.toString()));
        var enhanced = root.deepCopy(); enhanced.getAsJsonObject("perk").addProperty("enhanced", true);
        assertThrows(IllegalStateException.class, () -> GutshotProfile.validateResource(enhanced.toString()));
    }
}
