package kim.biryeong.destiny.fx;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import net.minecraft.client.resources.model.cuboid.ItemTransform;
import org.joml.Vector3f;
import org.junit.jupiter.api.Test;
import java.io.InputStreamReader;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import static org.junit.jupiter.api.Assertions.*;

class ShadowBowH20Test {
    private JsonObject model(String name) throws Exception {
        try (var stream = getClass().getResourceAsStream("/assets/destiny/models/item/" + name + ".json")) {
            assertNotNull(stream);
            return JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }

    @Test void stagesParseInActual26_3AndStringEndpointsMeetTheMovingNock() throws Exception {
        double[] nocks = {3.27, 5, 6.75, 8.24};
        JsonObject previous = null;
        for (int stage = 0; stage < 4; stage++) {
            var json = model("shadow_bow_h20_" + stage);
            assertNotNull(CuboidModel.fromStream(new StringReader(json.toString())), "Native parser, including intermediate angles");
            var elements = json.getAsJsonArray("elements");
            assertEquals(206, elements.size());
            if (previous != null) for (int i = 0; i < 201; i++)
                assertEquals(previous.getAsJsonArray("elements").get(i), elements.get(i), "Prop detail must not change");
            for (int index : new int[]{201, 202}) {
                var string = elements.get(index).getAsJsonObject();
                var from = string.getAsJsonArray("from"); var to = string.getAsJsonArray("to");
                double length = to.get(1).getAsDouble() - from.get(1).getAsDouble();
                double angle = Math.toRadians(Math.abs(string.getAsJsonObject("rotation").get("angle").getAsDouble()));
                assertEquals(8 + nocks[stage], 11.27 + length * Math.sin(angle), .00001);
                assertEquals(12, length * Math.cos(angle), .00001);
                string.getAsJsonObject("faces").entrySet().forEach(face -> {
                    for (var uv : face.getValue().getAsJsonObject().getAsJsonArray("uv"))
                        assertTrue(uv.getAsDouble() >= 0 && uv.getAsDouble() <= 16, "Vanilla UV, not BB pixels");
                });
            }
            previous = json;
        }
    }

    @Test void completeNativeDisplayAndHandedTransformsMatchBetterModelBodyCoordinates() throws Exception {
        for (String suffix : new String[]{"", "_0", "_1", "_2", "_3"}) {
            var json = model("shadow_bow_h20" + suffix);
            for (boolean left : new boolean[]{false, true}) {
                var display = json.getAsJsonObject("display").getAsJsonObject(left ? "thirdperson_lefthand" : "thirdperson_righthand");
                float angle = display.getAsJsonArray("rotation").get(1).getAsFloat();
                var transform = new ItemTransform(new Vector3f(0, angle, 0), new Vector3f(0, .125f, 0), new Vector3f(1));
                var pose = new PoseStack();
                // DisplayRenderer.ItemDisplayRenderer.submitInner applies this BEFORE
                // LayerRenderState applies the native handed item context transform.
                pose.rotateDegrees(Axis.YP, 180);
                transform.apply(left, pose.last());
                var arrow = pose.last().pose().transformDirection(new Vector3f(-1, 0, 0));
                // BM blueprint conversion mirrors X/Z: the body faces +Z before actor yaw.
                assertEquals(1, arrow.z, .00001);
                assertEquals(0, arrow.x, .00001);
                var nock = pose.last().pose().transformPosition(new Vector3f(16.24f/16, .5f, .5f));
                assertEquals(-8.24f/16, nock.z, .00001);
                assertEquals(.125f, nock.y, .00001);
            }
        }
    }
}
