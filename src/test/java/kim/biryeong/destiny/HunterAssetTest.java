package kim.biryeong.destiny;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Pack routing checks complement GameTests: the server cannot detect missing client assets. */
class HunterAssetTest {
    private String resource(String path) throws IOException {
        try (var stream = getClass().getClassLoader().getResourceAsStream(path)) {
            assertNotNull(stream, "Missing pack resource " + path);
            return new String(stream.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    private JsonObject json(String path) throws IOException {
        return JsonParser.parseString(resource(path)).getAsJsonObject();
    }

    @Test
    void eachSuperHasDistinctTintAndResolvesShader() throws IOException {
        Set<String> tints = new HashSet<>();
        for (String element : new String[]{"arc", "solar", "void"}) {
            var chain = json("assets/destiny/post_effect/super/" + element + "_active.json");
            var passes = chain.getAsJsonArray("passes");
            assertEquals(2, passes.size());
            var grade = passes.get(0).getAsJsonObject();
            String shader = grade.get("fragment_shader").getAsString().replace(":", "/shaders/") + ".fsh";
            String glsl = resource("assets/" + shader);
            var uniforms = grade.getAsJsonObject("uniforms").getAsJsonArray("SuperConfig");
            assertTrue(glsl.contains("uniform SuperConfig"));
            for (var uniform : uniforms) {
                var u = uniform.getAsJsonObject();
                assertTrue(glsl.contains("vec4 " + u.get("name").getAsString()));
                assertEquals(4, u.getAsJsonArray("value").size());
            }
            tints.add(uniforms.get(0).getAsJsonObject().getAsJsonArray("value").toString());
            assertEquals(grade.get("output"), passes.get(1).getAsJsonObject().getAsJsonArray("inputs")
                    .get(0).getAsJsonObject().get("target"));
            assertEquals("minecraft:main", passes.get(1).getAsJsonObject().get("output").getAsString());
        }
        assertEquals(3, tints.size());
    }

    @Test
    void superItemDefinitionsResolveNonemptyCubeModels() throws IOException {
        for (String name : new String[]{"arc_staff", "golden_gun", "shadow_bow"}) {
            var definition = json("assets/destiny/items/" + name + ".json").getAsJsonObject("model");
            assertEquals("minecraft:model", definition.get("type").getAsString());
            String path = definition.get("model").getAsString().replace(":", "/models/");
            var model = json("assets/" + path + ".json");
            assertFalse(model.getAsJsonArray("elements").isEmpty());
            assertTrue(model.has("display"));
        }
    }
}
