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

class WeaponSightW153Test {
    static final Set<String> IDS=Set.of("patron_of_lost_causes", "aishas_embrace", "long_arm", "antiope_d", "bug_out_bag", "ikelos_smg_v1_0_1", "the_recluse", "dead_man_walking_xx7463", "high_albedo", "brass_attacks", "erentil_fr4", "hollow_words", "dream_breaker", "null_composure", "coriolis_force", "edge_transit", "fixed_odds", "retrofit_escapade");
    private static final Path ASSETS=Path.of("src/main/resources/assets/destiny");
    @Test void eighteenRemainingRangedWeaponsUseTheNewRouteAndPhysicalSight() {
        for(String id:IDS) {
            var e=WeaponCatalog.find(id).orElseThrow();
            assertTrue(WeaponAimPresentation.supports(e));
            assertEquals("weapon_sight_w153/",WeaponAimPresentation.modelPrefix(e));
            assertFalse(WeaponAimPresentation.physicalSight(e,.94f));
            assertFalse(WeaponAimPresentation.physicalSight(e,Float.NaN));
            assertTrue(WeaponAimPresentation.physicalSight(e,.95f));
        }
    }
    @Test void targetCuboidParserAcceptsAllBodiesAndWrappers() throws Exception {
        int bodies=0,frames=0;
        try(var paths=Files.list(ASSETS.resolve("models/weapon_sight_w153"))) {
            for(var p:paths.toList()) {
                var text=Files.readString(p);
                assertNotNull(assertDoesNotThrow(()->CuboidModel.fromStream(new StringReader(text)),p.toString()));
                var json=JsonParser.parseString(text).getAsJsonObject();
                if(json.has("elements")){bodies++;assertTrue(json.getAsJsonArray("elements").size()<=1000);}
                else frames++;
            }
        }
        assertTrue(bodies>=18);assertEquals(18*42,frames);
    }
    @Test void targetItemCodecAcceptsEighteenGraphs() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        try(var paths=Files.list(ASSETS.resolve("items/weapon_sight_w153"))) {
            var all=paths.toList();assertEquals(18,all.size());
            for(var p:all) {
                var json=JsonParser.parseString(Files.readString(p)).getAsJsonObject();
                var result=ItemModels.CODEC.parse(JsonOps.INSTANCE,json.get("model"));
                assertTrue(result.error().isEmpty(),p+": "+result.error());
            }
        }
    }
}
