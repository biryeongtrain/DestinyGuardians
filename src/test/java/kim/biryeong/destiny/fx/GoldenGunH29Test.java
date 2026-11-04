package kim.biryeong.destiny.fx;

import com.google.gson.*;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import java.io.StringReader;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.fx.SuperMeshH28Test.*;

class GoldenGunH29Test {
    @Test void nativeCodecAcceptsSourceMeshAndAimContexts() throws Exception {
        ItemModels.bootstrap(); ItemTintSources.bootstrap();
        assertTrue(ItemModels.CODEC.parse(JsonOps.INSTANCE,
                asset("items/golden_gun_h29").get("model")).isSuccess());
        assertNotNull(CuboidModel.fromStream(new StringReader(
                asset("models/mesh/h29/golden_gun_triangle").toString())));
    }

    @Test void compiledMatricesRetainEverySourceTriangleAndGoldTint() throws Exception {
        var source = read("art/mesh/supers/h29/golden_gun.mesh.json");
        var vertices = source.getAsJsonArray("vertices");
        var triangles = source.getAsJsonArray("triangles");
        var parts = asset("items/golden_gun_h29").getAsJsonObject("model").getAsJsonArray("models");
        assertEquals(2350, triangles.size()); assertEquals(triangles.size(), parts.size());
        for (int i = 0; i < parts.size(); i++) {
            var t = triangles.get(i).getAsJsonObject(); var part = parts.get(i).getAsJsonObject();
            assertEquals("destiny:mesh/h29/golden_gun_triangle", part.get("model").getAsString());
            int color = t.get("color").getAsInt();
            assertEquals(color, part.getAsJsonArray("tints").get(0).getAsJsonObject().get("value").getAsInt());
            assertTrue((color >> 16 & 255) > (color >> 8 & 255));
            assertTrue((color >> 8 & 255) > (color & 255));
            assertTrue(t.has("diffuse_color"));
            var m = part.getAsJsonArray("transformation");
            for (var v : m) assertTrue(Float.isFinite(v.getAsFloat()));
            for (var index : t.getAsJsonArray("v")) {
                var expected = vertices.get(index.getAsInt()).getAsJsonArray();
                double closest = Double.POSITIVE_INFINITY;
                for (double[] xy : new double[][]{{-1, 0}, {0, 1}, {0, 0}}) {
                    double distance = 0;
                    for (int a = 0; a < 3; a++) {
                        double actual = (value(m, 4*a)*xy[0] + value(m, 4*a+1)*xy[1]
                                + value(m, 4*a+3) - .5)*16 + 8;
                        distance += Math.pow(actual - value(expected, a), 2);
                    }
                    closest = Math.min(closest, Math.sqrt(distance));
                }
                assertTrue(closest < .0001, "Displaced source corner in triangle " + i);
            }
        }
    }

    @Test void aimContextIsNotInventoryYawAndThirdPersonGripIsUnchanged() throws Exception {
        var display = asset("models/mesh/h29/golden_gun_triangle").getAsJsonObject("display");
        var first = display.getAsJsonObject("firstperson_righthand").getAsJsonArray("rotation");
        var inventory = display.getAsJsonObject("gui").getAsJsonArray("rotation");
        assertEquals(8, value(first, 0)); assertEquals(-170, value(first, 1));
        assertNotEquals(first, inventory);
        assertEquals(asset("models/item/golden_gun").getAsJsonObject("display")
                        .get("thirdperson_righthand"), display.get("thirdperson_righthand"));
        assertEquals(display, asset("models/item/golden_gun_h29").get("display"));
    }

    @Test void manifestPinsSourceAndRuntimeBytes() throws Exception {
        var m = read("art/mesh/supers/h29/manifest.json");
        assertEquals(2350, m.get("mesh_parts").getAsInt());
        Map<String, Path> paths = new HashMap<>();
        paths.put(m.get("source_sha256").getAsString(), Path.of("art/mesh/supers/h29/golden_gun.mesh.json"));
        for (var e : m.getAsJsonObject("runtime_sha256").entrySet())
            paths.put(e.getValue().getAsString(), Path.of("src/main/resources/assets/destiny/" + e.getKey()));
        paths.put(m.get("shared_texture_sha256").getAsString(),
                Path.of("src/main/resources/assets/destiny/textures/item/supers/mesh_triangle_h28.png"));
        for (var e : paths.entrySet()) assertEquals(e.getKey(),
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(e.getValue()))));
    }

    @Test void recoilAdapterRotatesPhysicalScreenZNotPitchX() {
        float roll = GoldenGunHandPose.sample(20, 0, 180, -1).roll();
        var q = kim.biryeong.minigamelib.displayhud.DisplayHud.vecToQuat(new org.joml.Vector3f(roll, 0, 0));
        var forward = new org.joml.Vector3f(0, 0, 1).rotate(q);
        assertEquals(0, forward.x, .00001); assertEquals(0, forward.y, .00001);
        assertEquals(1, forward.z, .00001);
        assertTrue(Math.abs(new org.joml.Vector3f(1, 0, 0).rotate(q).y) > .1);
    }

    @Test void summonAndDissolveRemainFiniteAndRecoverToAimPose() {
        var ready = GoldenGunHandPose.sample(20, -1, 180, -1);
        assertEquals(ready, GoldenGunHandPose.sample(30, 6, 170, -1));
        assertEquals(1190, ready.x()); assertEquals(850, ready.y());
        for (int age = 0; age <= 200; age++) {
            var p = GoldenGunHandPose.sample(age, -1, 200-age, -1);
            assertTrue(Float.isFinite(p.x()+p.y()+p.size()+p.roll()));
            assertTrue(p.size() >= 1 && p.size() <= 420);
        }
    }
}
