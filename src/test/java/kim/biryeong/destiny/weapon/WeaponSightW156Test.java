package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import java.io.StringReader;
import java.nio.file.*;
import static org.junit.jupiter.api.Assertions.*;

class WeaponSightW156Test {
    static final Path A=Path.of("src/main/resources/assets/destiny");
    @Test void aceUsesHologramOnlyWhenRaised() {
        var ace=WeaponCatalog.find("ace_of_spades").orElseThrow();
        assertEquals("weapon_sight_w159/",WeaponAimPresentation.modelPrefix(ace));
        assertTrue(WeaponAimPresentation.supports(ace));
        for(float p:new float[]{0,.94f,Float.NaN,Float.POSITIVE_INFINITY})
            assertFalse(WeaponAimPresentation.physicalSight(ace,p));
        assertTrue(WeaponAimPresentation.physicalSight(ace,.95f));
        assertTrue(WeaponAimPresentation.physicalSight(ace,1));
    }
    @Test void actualCuboidParserAcceptsBodyAnd42Frames() throws Exception {
        try(var paths=Files.list(A.resolve("models/weapon_sight_w156"))) {
            var all=paths.toList();assertEquals(43,all.size());
            for(var p:all) {
                String text=Files.readString(p);
                assertNotNull(CuboidModel.fromStream(new StringReader(text)),p.toString());
                var json=JsonParser.parseString(text).getAsJsonObject();
                if(json.has("elements"))assertEquals(92,json.getAsJsonArray("elements").size());
            }
        }
    }
    @Test void actualItemGraphCodecAcceptsAce() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        var json=JsonParser.parseString(Files.readString(A.resolve("items/weapon_sight_w156/ace_of_spades.json"))).getAsJsonObject();
        var result=ItemModels.CODEC.parse(JsonOps.INSTANCE,json.get("model"));
        assertTrue(result.error().isEmpty(),result.error().toString());
    }
}
