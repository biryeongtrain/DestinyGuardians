package kim.biryeong.destiny.weapon;

import java.util.Map;
import net.minecraft.resources.Identifier;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Catalog-only admission regression, independently runnable without asset/server bootstrap. */
class ReloadRoutingW114Test {
    private static final Map<String, String> EXPECTED = Map.ofEntries(
            Map.entry("biting_winds", "weapon_reload_w222_biting_winds/biting_winds"),
            Map.entry("whispering_slab", "weapon_reload_w222_whispering_slab/whispering_slab"),
            Map.entry("nezarec_s_whisper", "weapon_reload_w222_nezarec_s_whisper/nezarec_s_whisper"),

            Map.entry("pyroclastic_flow", "weapon_reload_w221_pyroclastic_flow/pyroclastic_flow"),
            Map.entry("canis_major", "weapon_reload_w220_canis_major/canis_major"),
            Map.entry("dimensional_hypotrochoid", "weapon_reload_w220_dimensional_hypotrochoid/dimensional_hypotrochoid"),
            Map.entry("deafening_whisper", "weapon_reload_w220_deafening_whisper/deafening_whisper"),

            Map.entry("allied_demand", "weapon_reload_w219_allied_demand/allied_demand"),
            Map.entry("dead_man_walking_xx7463", "weapon_reload_w219_dead_man_walking_xx7463/dead_man_walking_xx7463"),
            Map.entry("frontier_justice", "weapon_reload_w219_frontier_justice/frontier_justice"),

            Map.entry("erentil_fr4", "weapon_reload_w217_erentil_fr4/erentil_fr4"),
            Map.entry("coriolis_force", "weapon_reload_w217_coriolis_force/coriolis_force"),
            Map.entry("line_in_the_sand", "weapon_reload_w218_line_in_the_sand/line_in_the_sand"),
            Map.entry("stormchaser", "weapon_reload_w218_stormchaser/stormchaser"),
            Map.entry("code_duello", "weapon_reload_w218_code_duello/code_duello"),
            Map.entry("bellowing_giant", "weapon_reload_w218_bellowing_giant/bellowing_giant"),
            Map.entry("apostate", "weapon_reload_w215_apostate/apostate"),
            Map.entry("hollow_words", "weapon_reload_w217_hollow_words/hollow_words"),
            Map.entry("distant_relation", "weapon_reload_w216_distant_relation/distant_relation"),
            Map.entry("farewell", "weapon_reload_w215_farewell/farewell"),
            Map.entry("patron_of_lost_causes", "weapon_reload_w216_patron_of_lost_causes/patron_of_lost_causes"),
            Map.entry("high_albedo", "weapon_reload_w219_high_albedo/high_albedo"),
            Map.entry("antiope_d", "weapon_reload_w212_antiope_d/antiope_d"),
            Map.entry("ikelos_smg_v1_0_1", "weapon_reload_w216_ikelos_smg_v1_0_1/ikelos_smg_v1_0_1"),
            Map.entry("beloved", "weapon_reload_w208_beloved/beloved"),
            Map.entry("duke_mk_44", "weapon_reload_w215_duke_mk_44/duke_mk_44"),
            Map.entry("ammit_ar2", "weapon_reload_w207_ammit_ar2/ammit_ar2"),
            Map.entry("the_recluse", "weapon_reload_w208_the_recluse/the_recluse"),
            Map.entry("blast_furnace", "weapon_reload_w207_blast_furnace/blast_furnace"),
            Map.entry("hammerhead", "weapon_reload_w207_hammerhead/hammerhead"),
            Map.entry("ace_of_spades", "weapon_reload_w157/ace_of_spades"),
            Map.entry("gnawing_hunger", "weapon_reload_w208_gnawing_hunger/gnawing_hunger"),
            Map.entry("lonesome", "weapon_reload_w213_lonesome/lonesome"),
            Map.entry("steelfeather_repeater", "weapon_reload_w213_steelfeather_repeater/steelfeather_repeater"),
            Map.entry("bug_out_bag", "weapon_reload_w212_bug_out_bag/bug_out_bag"),
            Map.entry("cold_denial", "weapon_reload_w212_cold_denial/cold_denial"),
            Map.entry("austringer", "weapon_reload_w208_austringer/austringer"),
            Map.entry("bygones", "weapon_reload_w212_bygones/bygones"),
            Map.entry("retraced_path", "weapon_reload_w219_retraced_path/retraced_path"),
            Map.entry("aishas_embrace", "weapon_reload_w213_aishas_embrace/aishas_embrace"),
            Map.entry("chattering_bone", "weapon_reload_w213_chattering_bone/chattering_bone"),
            Map.entry("seventh_seraph_officer_revolver", "weapon_reload_w221_seventh_seraph_officer_revolver/seventh_seraph_officer_revolver"),
            Map.entry("retrofit_escapade", "weapon_reload_w214_retrofit_escapade/retrofit_escapade"),
            Map.entry("halfdan_d", "weapon_reload_w214_halfdan_d/halfdan_d"),
            Map.entry("edge_transit", "weapon_reload_w220_edge_transit/edge_transit"),
            Map.entry("fixed_odds", "weapon_reload_w215_fixed_odds/fixed_odds"),
            Map.entry("null_composure", "weapon_reload_w217_null_composure/null_composure"),
            Map.entry("dream_breaker", "weapon_reload_w217_dream_breaker/dream_breaker"),
            Map.entry("bite_of_the_fox", "weapon_reload_w214_bite_of_the_fox/bite_of_the_fox"),
            Map.entry("bad_omens", "weapon_reload_w218_bad_omens/bad_omens"),
            Map.entry("brass_attacks", "weapon_reload_w216_brass_attacks/brass_attacks"),
            Map.entry("claws_of_the_wolf", "weapon_reload_w214_claws_of_the_wolf/claws_of_the_wolf"),
            Map.entry("salvager_s_salvo", "weapon_reload_w220_salvager_s_salvo/salvager_s_salvo"));
    @Test void fiftyThreeRoutesIncludeBowNockingAndGlaive() {
        assertEquals(65, WeaponCatalog.all().size());
        int count = 0;
        for (var entry : WeaponCatalog.all()) {
            assertEquals(EXPECTED.containsKey(entry.id()), WeaponReloadPresentation.supports(entry), entry.id());
            if (EXPECTED.containsKey(entry.id())) {
                assertEquals(Identifier.fromNamespaceAndPath("destiny", EXPECTED.get(entry.id())), WeaponReloadPresentation.model(entry));
                count++;
            } else assertThrows(IllegalArgumentException.class, () -> WeaponReloadPresentation.model(entry), entry.id());
        }
        assertEquals(53, count);
        assertEquals(1, WeaponReloadPresentation.PROGRESS_INDEX);
    }
    @Test void nullHasNoReloadGraphOrPresentation() {
        assertFalse(WeaponReloadPresentation.supports(null));
        assertThrows(IllegalArgumentException.class, () -> WeaponReloadPresentation.model(null));
    }
}
