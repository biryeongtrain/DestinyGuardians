package kim.biryeong.destiny;

import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.renderer.PostChainConfig;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/** Actual Minecraft 26.3 CODEC coverage; native compilation/visibility is master QA. */
class PostPulseW180Test {
    private String resource(String path) throws Exception {
        try (var stream = getClass().getResourceAsStream("/assets/destiny/" + path)) {
            assertNotNull(stream, path);
            return new String(stream.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    @Test
    void sixPulseChainsDecodeWithActual263Codec() throws Exception {
        for (String element : List.of("solar", "arc", "void")) {
            for (String kind : List.of("activation", "impact")) {
                String path = "post_effect/super/" + element + "_" + kind + "_pulse.json";
                var result = PostChainConfig.CODEC.parse(JsonOps.INSTANCE,
                        JsonParser.parseString(resource(path)));
                assertTrue(result.result().isPresent(), () -> path + ": " + result.error());
            }
        }
    }

    @Test
    void actualCodecRejectsInventedUniformType() throws Exception {
        var chain = JsonParser.parseString(resource("post_effect/super/solar_activation_pulse.json"))
                .getAsJsonObject();
        chain.getAsJsonArray("passes").get(0).getAsJsonObject().getAsJsonObject("uniforms")
                .getAsJsonArray("PulseConfig").get(0).getAsJsonObject()
                .addProperty("type", "invented_renderer_uniform_type");
        assertTrue(PostChainConfig.CODEC.parse(JsonOps.INSTANCE, chain).error().isPresent());
    }

    @Test
    void sharedShapeAndTintMakeImpactPointwiseWeaker() throws Exception {
        for (String element : List.of("solar", "arc", "void")) {
            var a = JsonParser.parseString(resource("post_effect/super/" + element
                    + "_activation_pulse.json")).getAsJsonObject().getAsJsonArray("passes")
                    .get(0).getAsJsonObject().getAsJsonObject("uniforms").getAsJsonArray("PulseConfig");
            var b = JsonParser.parseString(resource("post_effect/super/" + element
                    + "_impact_pulse.json")).getAsJsonObject().getAsJsonArray("passes")
                    .get(0).getAsJsonObject().getAsJsonObject("uniforms").getAsJsonArray("PulseConfig");
            assertEquals(a.get(1), b.get(1), "Same nonnegative spatial response");
            var at = a.get(0).getAsJsonObject().getAsJsonArray("value");
            var bt = b.get(0).getAsJsonObject().getAsJsonArray("value");
            for (int c = 0; c < 3; c++) assertEquals(at.get(c), bt.get(c));
            assertTrue(bt.get(3).getAsDouble() < at.get(3).getAsDouble() * .75);
        }
    }
}
