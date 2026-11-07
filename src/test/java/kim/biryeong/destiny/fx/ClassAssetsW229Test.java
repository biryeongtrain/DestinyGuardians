package kim.biryeong.destiny.fx;

import com.google.gson.*;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class ClassAssetsW229Test {
    private static JsonObject resource(String name) throws Exception {
        try (var stream = ClassAssetsW229Test.class.getResourceAsStream(name)) {
            assertNotNull(stream, name);
            return JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }

    @Test void sourceClipsRemapOntoTheCompletePlayerSkinRigWithoutChangingItsGeometry() throws Exception {
        var template = resource("/steve.bbmodel");
        var original = template.deepCopy();
        var clips = resource(ClassSuperModelAssets.RESOURCE).getAsJsonArray("animations");
        var built = ClassSuperModelAssets.buildModel(template, clips);
        assertEquals(original, template, "Template input is never mutated");
        for (String key : List.of("elements", "groups", "outliner", "textures"))
            assertEquals(original.get(key), built.get(key), key);
        var ids = new HashSet<String>();
        for (var group : built.getAsJsonArray("groups")) ids.add(group.getAsJsonObject().get("uuid").getAsString());
        int inherited = original.getAsJsonArray("animations").size();
        for (int i = 0; i < inherited; i++)
            assertEquals(original.getAsJsonArray("animations").get(i), built.getAsJsonArray("animations").get(i));
        var merged=SuperLocomotionW336.overlay(SuperMotionOverlaysW332.overlay(
                MeleeSuperAnimationTiming.overlay(clips,MeleeSuperAnimationTiming.SPECTRAL_RESOURCE),"w2"),"w2");
        assertEquals(inherited + merged.size(), built.getAsJsonArray("animations").size());
        for (int i = inherited; i < inherited + merged.size(); i++) {
            var animation = built.getAsJsonArray("animations").get(i).getAsJsonObject();
            assertTrue(animation.get("name").getAsString().startsWith("w229_")
                    || animation.get("name").getAsString().startsWith("w230_"));
            for (var entry : animation.getAsJsonObject("animators").entrySet()) {
                assertTrue(ids.contains(entry.getKey()), "Animator maps to a real skin bone");
                var channels = new HashMap<String, Integer>();
                for (var key : entry.getValue().getAsJsonObject().getAsJsonArray("keyframes")) {
                    var k = key.getAsJsonObject();
                    assertEquals("linear", k.get("interpolation").getAsString());
                    channels.merge(k.get("channel").getAsString(), 1, Integer::sum);
                }
                int maximum=(int)Math.ceil(animation.get("length").getAsDouble()*40)+1;
                assertTrue(channels.values().stream().allMatch(n -> n>=1&&n<=maximum),
                        "Runtime curves use the engine clock grid; authored61 poses remain in source");
            }
        }
    }

    @Test void sourceGapsStayAbsentWhileTheReviewedAuthoredFistsAttackIsAvailable() {
        assertTrue(ClassSuperModelAssets.hasClip("w229_warlock_void_attack"));
        assertFalse(ClassSuperModelAssets.hasClip("w229_warlock_void_start"));
        assertTrue(ClassSuperModelAssets.hasClip("w229_titan_arc_attack"),
                "R1-reviewed authored punch is explicit; no Hunter action or forward-cast substitution");
        assertEquals("w229_titan_solar", ClassSuperModelAssets.prefix("titan/solar_super"));
    }

    @Test void newClassHudItemsAreAcceptedByTheNative26ModelCodecs() throws Exception {
        ItemModels.bootstrap(); ItemTintSources.bootstrap();
        var root = Path.of("src/main/resources/assets/destiny");
        for (String name : List.of("titan_hammer", "titan_havoc", "titan_shield", "titan_barricade",
                "warlock_daybreak", "warlock_storm", "warlock_nova", "warlock_rift", "warlock_snap", "warlock_singularity")) {
            var item = JsonParser.parseString(Files.readString(root.resolve("items/gui/hud/" + name + ".json"))).getAsJsonObject();
            assertTrue(ItemModels.CODEC.parse(JsonOps.INSTANCE, item.get("model")).isSuccess(), name);
            assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(root.resolve("models/gui/hud/" + name + ".json")))));
            assertNotNull(javax.imageio.ImageIO.read(root.resolve("textures/item/hud/" + name + ".png").toFile()));
        }
    }
}
