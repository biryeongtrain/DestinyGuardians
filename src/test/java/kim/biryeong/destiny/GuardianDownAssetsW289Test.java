package kim.biryeong.destiny;

import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.renderer.PostChainConfig;
import org.junit.jupiter.api.Test;
import java.nio.charset.StandardCharsets;
import static org.junit.jupiter.api.Assertions.*;

/** Actual game codec; GPU shader compilation is a separate client check. */
class GuardianDownAssetsW289Test {
    @Test void guardianDownChainParsesWithActualMinecraftCodec() throws Exception {
        try (var stream = getClass().getResourceAsStream("/assets/destiny/post_effect/crucible/guardian_down.json")) {
            assertNotNull(stream);
            var json = JsonParser.parseString(new String(stream.readAllBytes(), StandardCharsets.UTF_8));
            assertTrue(PostChainConfig.CODEC.parse(JsonOps.INSTANCE, json).result().isPresent());
        }
        assertNotNull(getClass().getResource("/assets/destiny/shaders/post/guardian_down.fsh"));
    }
}
