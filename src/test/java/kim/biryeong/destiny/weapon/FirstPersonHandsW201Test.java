package kim.biryeong.destiny.weapon;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import net.minecraft.resources.Identifier;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import java.io.StringReader;
import java.nio.file.*;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class FirstPersonHandsW201Test {
    static final Path A=Path.of("src/main/resources/assets/destiny");
    static JsonObject json(Path p)throws Exception{return JsonParser.parseString(Files.readString(p)).getAsJsonObject();}
    @BeforeAll static void codecs(){
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
    }
    @Test void nativeCodecAcceptsRepresentativeIdleAdsAndReloadAndRetainsNonFirstpersonGraph()throws Exception{
        for(String route:List.of("weapon_reload_w222_biting_winds/biting_winds","weapon_reload_w222_whispering_slab/whispering_slab","weapon_insert_w222_long_arm/long_arm","weapon_reload_w222_nezarec_s_whisper/nezarec_s_whisper","weapon_insert_w221_ikelos_sg_v1_0_1/ikelos_sg_v1_0_1","weapon_insert_w221_mindbender_s_ambition_adept/mindbender_s_ambition_adept","weapon_insert_w221_parcel_of_stardust_fell_to_earth/parcel_of_stardust_fell_to_earth","weapon_reload_w221_pyroclastic_flow/pyroclastic_flow","weapon_reload_w221_seventh_seraph_officer_revolver/seventh_seraph_officer_revolver","weapon_reload_w220_edge_transit/edge_transit","weapon_reload_w220_canis_major/canis_major","weapon_reload_w220_dimensional_hypotrochoid/dimensional_hypotrochoid","weapon_reload_w220_deafening_whisper/deafening_whisper","weapon_reload_w220_salvager_s_salvo/salvager_s_salvo","weapon_reload_w219_allied_demand/allied_demand","weapon_reload_w219_dead_man_walking_xx7463/dead_man_walking_xx7463","weapon_reload_w219_high_albedo/high_albedo","weapon_reload_w219_frontier_justice/frontier_justice","weapon_reload_w219_retraced_path/retraced_path","weapon_reload_w218_line_in_the_sand/line_in_the_sand","weapon_reload_w218_stormchaser/stormchaser","weapon_reload_w218_code_duello/code_duello","weapon_reload_w218_bellowing_giant/bellowing_giant","weapon_reload_w218_bad_omens/bad_omens","weapon_reload_w217_erentil_fr4/erentil_fr4","weapon_reload_w217_hollow_words/hollow_words","weapon_reload_w217_dream_breaker/dream_breaker","weapon_reload_w217_null_composure/null_composure","weapon_reload_w217_coriolis_force/coriolis_force","weapon_reload_w216_distant_relation/distant_relation","weapon_reload_w216_patron_of_lost_causes/patron_of_lost_causes","weapon_reload_w216_brass_attacks/brass_attacks","weapon_reload_w216_ikelos_smg_v1_0_1/ikelos_smg_v1_0_1","weapon_reload_w215_duke_mk_44/duke_mk_44","weapon_reload_w215_farewell/farewell","weapon_reload_w215_apostate/apostate","weapon_reload_w215_fixed_odds/fixed_odds","weapon_reload_w214_halfdan_d/halfdan_d","weapon_reload_w214_claws_of_the_wolf/claws_of_the_wolf","weapon_reload_w214_bite_of_the_fox/bite_of_the_fox","weapon_reload_w214_retrofit_escapade/retrofit_escapade","weapon_reload_w213_lonesome/lonesome","weapon_reload_w213_steelfeather_repeater/steelfeather_repeater","weapon_reload_w213_aishas_embrace/aishas_embrace","weapon_reload_w213_chattering_bone/chattering_bone","weapon_reload_w212_antiope_d/antiope_d","weapon_reload_w212_bug_out_bag/bug_out_bag",
                "weapon_reload_w212_cold_denial/cold_denial","weapon_reload_w212_bygones/bygones","weapon/ace_of_spades","weapon/ammit_ar2","weapon/biting_winds",
                "weapon_reload_w157/ace_of_spades","weapon_reload_w169_duke_mk_44/duke_mk_44",
                "weapon_reload_w69/ammit_ar2","weapon_izanagi_w91/izanagis_burden",
                "weapon_sight_w159/ace_of_spades","weapon_sight_w151/ammit_ar2",
                "weapon/blast_furnace","weapon/hammerhead","weapon/dust_rock_blues","weapon/izanagis_burden",
                "weapon_reload_w114_blast_furnace/blast_furnace","weapon_reload_w114_hammerhead/hammerhead",
                "weapon_sight_w151/blast_furnace","weapon_sight_w151/hammerhead","weapon_sight_w148/dust_rock_blues",
                "weapon_reload_w207_ammit_ar2/ammit_ar2","weapon_reload_w207_blast_furnace/blast_furnace",
                "weapon_reload_w207_hammerhead/hammerhead","weapon_insert_w207_dust_rock_blues/dust_rock_blues",
                "weapon_reload_w208_the_recluse/the_recluse","weapon_reload_w208_beloved/beloved",
                "weapon_reload_w208_gnawing_hunger/gnawing_hunger","weapon_reload_w208_austringer/austringer",
                "weapon_insert_w208_first_in_last_out/first_in_last_out")){
            var original=json(A.resolve("items/"+route+".json"));
            var graph=json(A.resolve("items/weapon_hands_w201/"+route+".json")).getAsJsonObject("model");
            assertEquals(original.get("model"),graph.get("fallback"),route);
            assertEquals(JsonParser.parseString("[\"firstperson_righthand\",\"firstperson_lefthand\"]"),graph.getAsJsonArray("cases").get(0).getAsJsonObject().get("when"));
            var result=ItemModels.CODEC.parse(JsonOps.INSTANCE,graph);
            assertTrue(result.isSuccess(),route+": "+result.error());
        }
    }
    @Test void nativeCuboidParserAcceptsFingerlessSkinArmsAndRepresentativeComposedTransforms()throws Exception{
        for(String side:List.of("right_classic","left_classic","right_slim","left_slim",
                "right_upper_classic","left_upper_classic","right_upper_slim","left_upper_slim")){
            var path=A.resolve("models/skin_arm_w204/"+side+".json");
            assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(path))));
            var elements=json(path).getAsJsonArray("elements");assertTrue(elements.size()==(side.endsWith("slim")?96:112));
        }
        try(var paths=Files.list(A.resolve("models/skin_arm_w204/poses"))){
            for(var path:paths.limit(40).toList())
                assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(path))),path.toString());
        }
    }
    @Test void finalProjectionIsIdempotentAndNeverAddsAGameplaySelector(){
        var model=Identifier.parse("destiny:weapon/ace_of_spades");
        var alias=WeaponFirstPersonHands.model(model);
        assertEquals("destiny:weapon_hands_w201/weapon/ace_of_spades",alias.toString());
        assertEquals(alias,WeaponFirstPersonHands.model(alias));
        var foreign=Identifier.withDefaultNamespace("stick");assertSame(foreign,WeaponFirstPersonHands.model(foreign));
        assertNull(WeaponFirstPersonHands.model(null));
        for(var e:WeaponCatalog.all())if(!e.family().equals("sword"))
            assertNotEquals(Identifier.parse(e.item_model()),WeaponFirstPersonHands.model(Identifier.parse(e.item_model())),e.id());
    }
}
