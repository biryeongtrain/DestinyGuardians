package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import java.io.StringReader;
import java.nio.file.*;
import java.util.Set;
import static org.junit.jupiter.api.Assertions.*;

class WeaponSightW151Test {
    // Frozen pre-W327 roster assertions retain their original counts; new identities have separate coverage.
    static final Set<String> IDS = Set.of("duke_mk_44", "austringer", "seventh_seraph_officer_revolver", "allied_demand", "farewell", "lonesome", "halfdan_d", "ammit_ar2", "gnawing_hunger", "steelfeather_repeater", "frontier_justice", "distant_relation", "cold_denial", "bygones", "chattering_bone", "blast_furnace", "claws_of_the_wolf", "hammerhead", "bad_omens", "code_duello");
    private static final Path ASSETS=Path.of("src/main/resources/assets/destiny");
    private static final Set<String> PRIOR=Set.of("dust_rock_blues","first_in_last_out","ikelos_sg_v1_0_1",
            "parcel_of_stardust_fell_to_earth","mindbender_s_ambition_adept","biting_winds","whispering_slab");
    private static final Set<String> LAUNCHERS=Set.of("canis_major","dimensional_hypotrochoid","deafening_whisper","salvager_s_salvo");
    private static final Set<String> TRACE_ROCKETS=Set.of("retraced_path","bellowing_giant","pyroclastic_flow");
    private static final Set<String> LFRS=Set.of("line_in_the_sand","stormchaser");
    @Test void twentyNewWeaponsUseTheNewRouteWithoutRegressingEarlierSights() {
        for(var entry:WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id())).toList()) assertEquals(entry.id().equals("ace_of_spades")?"weapon_sight_w159/":WeaponSightW153Test.IDS.contains(entry.id())?"weapon_sight_w153/":IDS.contains(entry.id())?"weapon_sight_w151/":(TRACE_ROCKETS.contains(entry.id()) || LFRS.contains(entry.id()))?"weapon_sight_w150/":PRIOR.contains(entry.id())?"weapon_sight_w148/":LAUNCHERS.contains(entry.id())?"weapon_sight_w149/":"weapon_aim_w70/",WeaponAimPresentation.modelPrefix(entry));
    }
    @Test void physicalSightsReplaceHipReticlesOnlyAtTheRaisedEndpoint() {
        for(var entry:WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id())).toList()) {
            assertFalse(WeaponAimPresentation.physicalSight(entry,0));
            assertFalse(WeaponAimPresentation.physicalSight(entry,.94f));
            assertFalse(WeaponAimPresentation.physicalSight(entry,Float.NaN));
            assertFalse(WeaponAimPresentation.physicalSight(entry,Float.POSITIVE_INFINITY));
            assertEquals(entry.id().equals("ace_of_spades") || WeaponSightW153Test.IDS.contains(entry.id()) || IDS.contains(entry.id()) || PRIOR.contains(entry.id()) || LAUNCHERS.contains(entry.id()) || TRACE_ROCKETS.contains(entry.id()),WeaponAimPresentation.physicalSight(entry,.95f));
            assertEquals(entry.id().equals("ace_of_spades") || WeaponSightW153Test.IDS.contains(entry.id()) || IDS.contains(entry.id()) || PRIOR.contains(entry.id()) || LAUNCHERS.contains(entry.id()) || TRACE_ROCKETS.contains(entry.id()),WeaponAimPresentation.physicalSight(entry,1));
        }
    }
    @Test void linearFusionRiflesKeepScopeFallbackButUseAlignedMovingOptic() {
        for(String id:Set.of("line_in_the_sand","stormchaser")) {
            var entry=WeaponCatalog.all().stream().filter(e->e.id().equals(id)).findFirst().orElseThrow();
            assertTrue(WeaponScopes.supports(entry));
            assertEquals("weapon_scope_w45/"+id,WeaponScopes.model(entry).getPath());
            assertEquals("weapon_sight_w150/",WeaponAimPresentation.modelPrefix(entry));
            assertFalse(WeaponAimPresentation.physicalSight(entry,1));
        }
    }
    @Test void actualTargetCuboidParserAcceptsEveryGeneratedDisplayAndSightBody() throws Exception {
        int bodies=0;
        try(var paths=Files.list(ASSETS.resolve("models/weapon_sight_w151"))) {
            for(var path:paths.toList()) {
                String text=Files.readString(path);
                var parsed=assertDoesNotThrow(()->CuboidModel.fromStream(new StringReader(text)),path.toString());
                assertNotNull(parsed);
                var json=JsonParser.parseString(text).getAsJsonObject();
                if(json.has("elements")){bodies++;assertTrue(json.getAsJsonArray("elements").size()<=1000);}
            }
        }
        assertEquals(21,bodies); // Twenty authored bodies plus Ammit's seated-magazine assembly.
        for(String id:TRACE_ROCKETS) {
            var p=ASSETS.resolve("models/weapon_surface_w123/"+id+".json");
            var model=assertDoesNotThrow(()->CuboidModel.fromStream(new StringReader(Files.readString(p))));
            assertNotNull(model);
            assertTrue(JsonParser.parseString(Files.readString(p)).getAsJsonObject().getAsJsonArray("elements").size()<=1000);
        }
    }
    @Test void targetItemModelCodecAcceptsAllTwentyWrappers() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        int graphs=0;
        try(var paths=Files.list(ASSETS.resolve("items/weapon_sight_w151"))) {
            for(var p:paths.toList()){
                var root=JsonParser.parseString(Files.readString(p)).getAsJsonObject();
                var result=ItemModels.CODEC.parse(JsonOps.INSTANCE,root.get("model"));
                assertTrue(result.error().isEmpty(),p+": "+result.error());graphs++;
            }
        }
        assertEquals(20,graphs);
    }
}
