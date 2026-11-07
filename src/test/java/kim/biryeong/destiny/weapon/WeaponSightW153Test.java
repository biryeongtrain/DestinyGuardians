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
        var expectedBodies=new java.util.HashSet<String>();
        var expectedFrames=new java.util.HashSet<String>();
        var derivativeFrames=new java.util.HashSet<String>();
        for(String id:IDS) {
            expectedBodies.add(id+"_body.json");
            for(int frame=0;frame<=20;frame++)for(String grip:Set.of("native","twohand"))
                expectedFrames.add(id+"_%02d_%s.json".formatted(frame,grip));
        }
        for(String id:Set.of("deliverance","subjunctive")) {
            assertTrue(WeaponCatalog.find(id).isPresent(), "Derivative must have a registered weapon");
            for(int frame=0;frame<=20;frame++)for(String grip:Set.of("native","twohand"))
                derivativeFrames.add(id+"_%02d_%s.json".formatted(frame,grip));
        }
        // These two body parents are published by the real pack-time skin mirror.
        // Validate against the emitted resource map, not only authored disk files.
        var emitted=new java.util.HashMap<String,eu.pb4.polymer.resourcepack.api.PackResource>();
        var resources=Path.of("src/main/resources");
        try(var paths=Files.list(ASSETS.resolve("models/weapon_sight_w153"))) {
            for(var file:paths.toList()) emitted.put(resources.relativize(file).toString(),
                    eu.pb4.polymer.resourcepack.api.PackResource.fromString(Files.readString(file)));
        }
        for(String name:Set.of("fusion_rifle/hollow_words","submachine_gun/the_recluse")) {
            var file=ASSETS.resolve("models/weapon/"+name+".json");
            emitted.put(resources.relativize(file).toString(),eu.pb4.polymer.resourcepack.api.PackResource.fromString(Files.readString(file)));
        }
        emitted.putAll(kim.biryeong.destiny.compat.pack.WeaponSkinAssets.plan(emitted));
        for(String id:Set.of("deliverance","subjunctive")) {
            var body=emitted.get("assets/destiny/models/weapon_sight_w153/"+id+"_body.json");
            assertNotNull(body,id+" generated body");
            assertNotNull(CuboidModel.fromStream(new StringReader(body.asString())));
            var json=JsonParser.parseString(body.asString()).getAsJsonObject();
            assertTrue(json.getAsJsonArray("elements").size()<=1000);
        }
        var bodies=new java.util.HashSet<String>();var frames=new java.util.HashSet<String>();
        var derivatives=new java.util.HashSet<String>();
        try(var paths=Files.list(ASSETS.resolve("models/weapon_sight_w153"))) {
            for(var p:paths.toList()) {
                var text=Files.readString(p);String name=p.getFileName().toString();
                assertNotNull(assertDoesNotThrow(()->CuboidModel.fromStream(new StringReader(text)),p.toString()));
                var json=JsonParser.parseString(text).getAsJsonObject();
                if(expectedBodies.contains(name)) {
                    bodies.add(name);assertTrue(json.has("elements"));
                    assertTrue(json.getAsJsonArray("elements").size()<=1000);
                } else if(expectedFrames.contains(name)) {
                    frames.add(name);assertFalse(json.has("elements"));assertTrue(json.has("parent"));
                } else {
                    assertTrue(derivativeFrames.contains(name), "Unreviewed W153 file: "+name);
                    derivatives.add(name);assertEquals(Set.of("parent","display"),json.keySet());
                    String id=name.startsWith("deliverance_")?"deliverance":"subjunctive";
                    String parent=name.contains("_00_") ? "destiny:weapon/"+WeaponCatalog.find(id).orElseThrow().family()+"/"+id
                            : "destiny:weapon_sight_w153/"+id+"_body";
                    assertEquals(parent,json.get("parent").getAsString());
                    assertTrue(emitted.containsKey("assets/destiny/models/"+parent.substring(8)+".json"), "Dangling emitted parent: "+parent);
                }
            }
        }
        assertEquals(expectedBodies,bodies);assertEquals(expectedFrames,frames);
        assertEquals(18*42,frames.size());assertEquals(derivativeFrames,derivatives);
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
