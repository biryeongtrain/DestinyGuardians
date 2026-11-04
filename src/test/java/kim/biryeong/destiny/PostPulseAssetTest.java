package kim.biryeong.destiny;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.regex.Pattern;

import static org.junit.jupiter.api.Assertions.*;

class PostPulseAssetTest {
    private String resource(String path) throws Exception {
        try (var stream = getClass().getResourceAsStream("/assets/destiny/" + path)) {
            assertNotNull(stream, path);
            return new String(stream.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    @Test
    void pulseChainsMatchShaderUniformLayoutAndNeverReadTheirOutput() throws Exception {
        String shader = resource("shaders/post/super_pulse.fsh");
        var block = Pattern.compile("layout\\(std140\\)\\s+uniform\\s+PulseConfig\\s*\\{([^}]+)}",
                Pattern.DOTALL).matcher(shader);
        assertTrue(block.find(), "26.3 uses named std140 uniform blocks");
        List<String> layout = new ArrayList<>();
        var fields = Pattern.compile("(vec[234]|float|int)\\s+(\\w+)\\s*;").matcher(block.group(1));
        while (fields.find()) layout.add(fields.group(1) + " " + fields.group(2));
        assertEquals(List.of("vec4 Tint", "vec4 Shape"), layout);
        assertTrue(shader.contains("uniform sampler2D InSampler;"));
        var samplers = Pattern.compile("uniform\\s+sampler\\w+\\s+(\\w+)\\s*;").matcher(shader);
        List<String> samplerNames = new ArrayList<>();
        while (samplers.find()) samplerNames.add(samplers.group(1));
        assertEquals(List.of("InSampler"), samplerNames, "Only the unshifted scene input");
        var blocks = Pattern.compile("uniform\\s+(\\w+)\\s*\\{").matcher(shader);
        List<String> blockNames = new ArrayList<>();
        while (blocks.find()) blockNames.add(blocks.group(1));
        assertEquals(List.of("PulseConfig"), blockNames, "No invented renderer/time inputs");
        assertTrue(shader.contains("layout(location = 0) in vec2 texCoord;"));
        assertTrue(shader.contains("layout(location = 0) out vec4 fragColor;"));

        for (String element : List.of("arc", "solar", "void")) {
            for (String kind : List.of("activation", "impact")) {
                String path = "post_effect/super/" + element + "_" + kind + "_pulse.json";
                JsonObject chain = JsonParser.parseString(resource(path)).getAsJsonObject();
                assertEquals(Set.of("swap"), chain.getAsJsonObject("targets").keySet(), path);
                assertTrue(chain.getAsJsonObject("targets").getAsJsonObject("swap").isEmpty(),
                        "No persistent history or fixed-resolution targets");
                JsonArray passes = chain.getAsJsonArray("passes");
                assertEquals(2, passes.size(), path);
                JsonObject pulse = passes.get(0).getAsJsonObject();
                assertEquals("destiny:post/super_pulse", pulse.get("fragment_shader").getAsString());
                assertEquals("swap", pulse.get("output").getAsString());
                assertInput(pulse, "minecraft:main");
                assertEquals(Set.of("PulseConfig"), pulse.getAsJsonObject("uniforms").keySet());
                JsonArray uniforms = pulse.getAsJsonObject("uniforms").getAsJsonArray("PulseConfig");
                assertEquals(layout.size(), uniforms.size());
                for (int i = 0; i < layout.size(); i++) {
                    JsonObject uniform = uniforms.get(i).getAsJsonObject();
                    assertEquals(layout.get(i), uniform.get("type").getAsString() + " "
                            + uniform.get("name").getAsString(), path);
                    assertFiniteVec4(uniform.getAsJsonArray("value"));
                }

                JsonObject blit = passes.get(1).getAsJsonObject();
                assertEquals("minecraft:post/blit", blit.get("fragment_shader").getAsString());
                assertEquals("minecraft:main", blit.get("output").getAsString());
                assertInput(blit, "swap");
                assertEquals(Set.of("BlitConfig"), blit.getAsJsonObject("uniforms").keySet());
                var blitConfig = blit.getAsJsonObject("uniforms").getAsJsonArray("BlitConfig");
                assertEquals(1, blitConfig.size());
                var color = blitConfig.get(0).getAsJsonObject();
                assertEquals("ColorModulate", color.get("name").getAsString());
                assertEquals("vec4", color.get("type").getAsString());
                assertFiniteVec4(color.getAsJsonArray("value"));
                for (var channel : color.getAsJsonArray("value")) assertEquals(1.0, channel.getAsDouble());
            }
        }
    }

    @Test
    void pulseParametersKeepCenterQuietAndImpactWeakerThanActivation() throws Exception {
        for (String element : List.of("arc", "solar", "void")) {
            double activationStrength = 0;
            for (String kind : List.of("activation", "impact")) {
                var chain = JsonParser.parseString(resource("post_effect/super/" + element + "_" + kind
                        + "_pulse.json")).getAsJsonObject();
                var config = chain.getAsJsonArray("passes").get(0).getAsJsonObject()
                        .getAsJsonObject("uniforms").getAsJsonArray("PulseConfig");
                var tint = config.get(0).getAsJsonObject().getAsJsonArray("value");
                var shape = config.get(1).getAsJsonObject().getAsJsonArray("value");
                for (var channel : tint) assertTrue(channel.getAsDouble() >= 0 && channel.getAsDouble() <= 1);
                double strength = tint.get(3).getAsDouble();
                assertTrue(strength > 0 && strength <= 0.12, "At most 12% added light");
                if (kind.equals("activation")) activationStrength = strength;
                else assertTrue(strength < activationStrength, "Repeated hit feedback stays modest");
                double radius = shape.get(0).getAsDouble(), width = shape.get(1).getAsDouble();
                assertTrue(radius >= 0.5 && radius <= 1.0);
                assertTrue(width > 0 && width <= 0.125);
                assertTrue(radius >= 5 * width, "Corona excludes the crosshair center");
                double edge = shape.get(2).getAsDouble(), corona = shape.get(3).getAsDouble();
                assertTrue(edge >= 0 && corona >= 0 && edge + corona <= 1.0,
                        "Combined contributions stay within Tint.a");
            }
        }
    }

    private static void assertInput(JsonObject pass, String target) {
        assertEquals("minecraft:core/screenquad", pass.get("vertex_shader").getAsString());
        var inputs = pass.getAsJsonArray("inputs");
        assertEquals(1, inputs.size());
        var input = inputs.get(0).getAsJsonObject();
        assertEquals(Set.of("sampler_name", "target"), input.keySet());
        assertEquals("In", input.get("sampler_name").getAsString());
        assertEquals(target, input.get("target").getAsString());
        assertNotEquals(target, pass.get("output").getAsString(), "No framebuffer feedback loop");
    }

    private static void assertFiniteVec4(JsonArray vector) {
        assertEquals(4, vector.size());
        for (var value : vector) assertTrue(Double.isFinite(value.getAsDouble()));
    }
}
