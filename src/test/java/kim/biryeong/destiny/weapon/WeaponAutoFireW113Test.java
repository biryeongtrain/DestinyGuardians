package kim.biryeong.destiny.weapon;

import java.util.Set;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Catalog-only regressions: independent expected IDs, no server or runtime bootstrap. */
class WeaponAutoFireW113Test {
    private static final Set<String> INTRINSIC = Set.of(
            "halfdan_d", "ammit_ar2", "gnawing_hunger", "steelfeather_repeater",
            "antiope_d", "bug_out_bag", "ikelos_smg_v1_0_1", "the_recluse", "retraced_path",
            "fixed_odds", "hammerhead", "retrofit_escapade",
            "aishas_embrace", "dead_man_walking_xx7463", "ikelos_sg_v1_0_1");
    private static final Set<String> DEFERRED_OR_MELEE = Set.of(
            "biting_winds", "whispering_slab", "salvager_s_salvo", "abide_the_return",
            "goldtusk", "crown_splitter", "falling_guillotine", "temptation_s_hook");

    private static WeaponCatalog.Entry entry(String id) {
        return WeaponCatalog.find(id).orElseThrow();
    }

    @Test void enabledCoversExactly57OfAll65CanonicalEntries() {
        assertEquals(65, WeaponCatalog.all().size());
        int admitted = 0;
        for (var entry : WeaponCatalog.all()) {
            boolean supported = WeaponAutoFirePolicy.supportsAutomatic(entry, true);
            assertEquals(!DEFERRED_OR_MELEE.contains(entry.id()), supported, entry.id());
            if (supported) admitted++;
        }
        assertEquals(57, admitted);
    }

    @Test void disabledPreservesAll65OldIntrinsicDecisions() {
        assertEquals(65, WeaponCatalog.all().size());
        int admitted = 0;
        for (var entry : WeaponCatalog.all()) {
            boolean supported = WeaponAutoFirePolicy.supportsAutomatic(entry, false);
            assertEquals(INTRINSIC.contains(entry.id()), supported, entry.id());
            assertEquals(WeaponFirePolicy.supportsAutomatic(entry), supported, entry.id());
            if (supported) admitted++;
        }
        assertEquals(15, admitted);
    }

    @Test void bowsSwordsAndReleaseToDetonateStayExcludedInBothModes() {
        assertTrue(BreachGrenade.supports(entry("salvager_s_salvo")));
        for (String id : DEFERRED_OR_MELEE) {
            assertFalse(WeaponAutoFirePolicy.supportsAutomatic(entry(id), true), id);
            assertFalse(WeaponAutoFirePolicy.supportsAutomatic(entry(id), false), id);
        }
    }

    @Test void glaiveRangedAndWaveGrenadeArePermittedWithoutIntrinsicPromotion() {
        for (String id : Set.of("nezarec_s_whisper", "deafening_whisper", "ace_of_spades",
                "izanagis_burden", "null_composure", "bad_omens", "canis_major", "claws_of_the_wolf")) {
            assertTrue(WeaponAutoFirePolicy.supportsAutomatic(entry(id), true), id);
            assertFalse(WeaponAutoFirePolicy.supportsAutomatic(entry(id), false), id);
            assertFalse(WeaponFirePolicy.supportsAutomatic(entry(id)), id);
        }
    }

    @Test void nullUnknownAndNullIdFailClosedInBothModes() {
        rejected(null);
        rejected(new WeaponCatalog.Entry("unknown", "auto_rifle", "rapid_fire", "Unknown",
                "Rapid-Fire Frame", "destiny:weapon/unknown"));
        rejected(new WeaponCatalog.Entry(null, "auto_rifle", "rapid_fire", "Unknown", null, null));
        rejected(new WeaponCatalog.Entry("AMMIT_AR2", "auto_rifle", "precision", "Ammit AR2", null, null));
    }

    @Test void editingAnyCanonicalFieldFailsClosedForEveryEntry() {
        for (var e : WeaponCatalog.all()) {
            rejected(new WeaponCatalog.Entry(e.id() + "_edited", e.family(), e.frame(), e.name(), e.source_frame_label(), e.item_model()));
            rejected(new WeaponCatalog.Entry(e.id(), "auto_rifle_edited", e.frame(), e.name(), e.source_frame_label(), e.item_model()));
            rejected(new WeaponCatalog.Entry(e.id(), e.family(), e.frame() + "_edited", e.name(), e.source_frame_label(), e.item_model()));
            rejected(new WeaponCatalog.Entry(e.id(), e.family(), e.frame(), e.name() + " edited", e.source_frame_label(), e.item_model()));
            rejected(new WeaponCatalog.Entry(e.id(), e.family(), e.frame(), e.name(), e.source_frame_label() + " edited", e.item_model()));
            rejected(new WeaponCatalog.Entry(e.id(), e.family(), e.frame(), e.name(), e.source_frame_label(), e.item_model() + "_edited"));
            rejected(new WeaponCatalog.Entry(e.id(), null, e.frame(), e.name(), e.source_frame_label(), e.item_model()));
        }
    }

    @Test void exactValueCopiesAreCanonicalWithoutRequiringObjectIdentity() {
        for (var e : WeaponCatalog.all()) {
            var copy = new WeaponCatalog.Entry(e.id(), e.family(), e.frame(), e.name(), e.source_frame_label(), e.item_model());
            assertNotSame(e, copy);
            for (boolean enabled : new boolean[]{false, true})
                assertEquals(WeaponAutoFirePolicy.supportsAutomatic(e, enabled),
                        WeaponAutoFirePolicy.supportsAutomatic(copy, enabled), e.id());
        }
    }

    private static void rejected(WeaponCatalog.Entry entry) {
        assertFalse(WeaponAutoFirePolicy.supportsAutomatic(entry, false), String.valueOf(entry));
        assertFalse(WeaponAutoFirePolicy.supportsAutomatic(entry, true), String.valueOf(entry));
    }
}
