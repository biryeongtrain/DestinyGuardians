package kim.biryeong.destiny.fx;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.resources.model.cuboid.ItemTransform;
import net.minecraft.world.item.ItemDisplayContext;
import org.joml.Vector3f;
import org.junit.jupiter.api.Test;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;

/** Resource contracts and native handed transforms; not proof of the final rendered player pose. */
class ShadowBowH19Test {
    private static final float EPS = 0.00001f;
    private JsonObject resource(String path) throws Exception {
        try (var stream = getClass().getResourceAsStream("/assets/destiny/" + path)) {
            assertNotNull(stream, path);
            return JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }

    private Vector3f vector(JsonObject json, String key, float fallback) {
        if (!json.has(key)) return new Vector3f(fallback);
        var a = json.getAsJsonArray(key);
        return new Vector3f(a.get(0).getAsFloat(), a.get(1).getAsFloat(), a.get(2).getAsFloat());
    }

    private PoseStack itemPose(JsonObject display, ItemDisplayContext context) {
        // JSON translations are in model units; the native loader normalizes by16.
        var transform = new ItemTransform(vector(display, "rotation", 0),
                vector(display, "translation", 0).div(16), vector(display, "scale", 1));
        var pose = new PoseStack();
        // Exercise the actual26.3 client implementation, including its left-hand Y/Z sign flip.
        transform.apply(context.leftHand(), pose.last());
        return pose;
    }

    @Test void nativeThirdPersonTransformPointsArrowForwardAndNockBackTowardTheDrawHand() throws Exception {
        for (String name : new String[]{"shadow_bow_h19", "shadow_bow_h19_drawn"}) {
            var displays = resource("models/item/" + name + ".json").getAsJsonObject("display");
            for (var context : new ItemDisplayContext[]{ItemDisplayContext.THIRD_PERSON_LEFT_HAND,
                    ItemDisplayContext.THIRD_PERSON_RIGHT_HAND}) {
                String key = context.leftHand() ? "thirdperson_lefthand" : "thirdperson_righthand";
                var matrix = itemPose(displays.getAsJsonObject(key), context).last().pose();
                var grip = matrix.transformPosition(new Vector3f(.5f));
                var nock = matrix.transformPosition(new Vector3f(16.24f / 16, .5f, .5f));
                var tip = matrix.transformPosition(new Vector3f(-6f / 16, .5f, .5f));
                assertEquals(0, grip.x, EPS, name + "/" + key + " grip X");
                assertEquals(.125f, grip.y, EPS, "Grip translation remains two model units");
                assertEquals(0, grip.z, EPS, "No accidental pivot displacement");
                assertTrue(nock.z > grip.z + .5f, name + "/" + key + " string must face the archer (+Z)");
                assertTrue(tip.z < grip.z - .8f, name + "/" + key + " arrow must point toward shot (-Z)");
                var direction = matrix.transformDirection(new Vector3f(-1, 0, 0));
                assertEquals(0, direction.x, EPS);
                assertEquals(0, direction.y, EPS);
                assertEquals(-1, direction.z, EPS);
            }
        }
    }

    @Test void bothStatesResolveAndKeepTheSameLeftHandGrip() throws Exception {
        JsonObject rest = resource("models/item/shadow_bow_h19.json");
        JsonObject drawn = resource("models/item/shadow_bow_h19_drawn.json");
        assertEquals(rest.get("textures"), drawn.get("textures"));
        assertEquals(rest.get("display"), drawn.get("display"));
        assertEquals("[0,90,0]", rest.getAsJsonObject("display").getAsJsonObject("thirdperson_lefthand")
                .get("rotation").toString());
        for (String name : new String[]{"shadow_bow_h19", "shadow_bow_h19_drawn"})
            assertEquals("destiny:item/" + name, resource("items/" + name + ".json")
                    .getAsJsonObject("model").get("model").getAsString());
    }

    @Test void drawAddsVStringAndNockedArrowWithoutChangingTheBowLimbs() throws Exception {
        var rest = resource("models/item/shadow_bow_h19.json").getAsJsonArray("elements");
        var drawn = resource("models/item/shadow_bow_h19_drawn.json").getAsJsonArray("elements");
        assertEquals(202, rest.size());
        assertEquals(206, drawn.size()); // Remove one straight string, add two strings and three arrow parts.
        // BB and vanilla export order differ: delete the string, not whichever cube has its BB index.
        var straightString = rest.get(rest.size() - 1);
        assertEquals("[11.23,-4.15,7.95]", straightString.getAsJsonObject().get("from").toString());
        assertFalse(drawn.contains(straightString), "Original straight string must not survive the draw");
        for (var element : rest) if (!element.equals(straightString))
            assertTrue(drawn.contains(element), "Every non-string cube, including wisps, must survive");
        int unchanged = 0;
        for (var element : rest) if (drawn.contains(element)) unchanged++;
        assertEquals(rest.size() - 1, unchanged);
        int angledStrings = 0;
        for (var value : drawn) {
            var element = value.getAsJsonObject();
            for (int axis = 0; axis < 3; axis++)
                assertTrue(element.getAsJsonArray("to").get(axis).getAsDouble()
                        > element.getAsJsonArray("from").get(axis).getAsDouble(), "Nonzero item cube");
            if (!rest.contains(value) && element.has("rotation")) {
                assertEquals(22.5, Math.abs(element.getAsJsonObject("rotation").get("angle").getAsDouble()));
                angledStrings++;
            }
            if (!rest.contains(value))
                assertEquals(straightString.getAsJsonObject().get("faces"), element.get("faces"),
                        "New faces must reuse normalized vanilla string UVs, not Blockbench pixel UVs");
        }
        assertEquals(2, angledStrings);
    }
}
