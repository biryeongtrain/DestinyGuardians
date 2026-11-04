package kim.biryeong.destiny;

import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.renderer.PostChainConfig;
import org.junit.jupiter.api.Test;
import java.nio.charset.StandardCharsets;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

/** Actual 26.3 config codec only; native GPU compile/framebuffer remains separate. */
class PostEffectCodecW179Test {
    @Test void nineAuthoredSuperChainsParseWithActualMinecraftCodec() throws Exception {
        for(String element:List.of("solar","arc","void"))
            for(String kind:List.of("active","activation_pulse","impact_pulse")) {
                var path="/assets/destiny/post_effect/super/"+element+"_"+kind+".json";
                try(var stream=getClass().getResourceAsStream(path)) {
                    assertNotNull(stream,path);
                    var json=JsonParser.parseString(new String(stream.readAllBytes(),StandardCharsets.UTF_8));
                    assertTrue(PostChainConfig.CODEC.parse(JsonOps.INSTANCE,json).result().isPresent(),path);
                }
            }
    }
    @Test void codecRejectsMalformedPassList() {
        assertTrue(PostChainConfig.CODEC.parse(JsonOps.INSTANCE,
                JsonParser.parseString("{\"targets\":{},\"passes\":\"not-a-list\"}")).error().isPresent());
    }
}
