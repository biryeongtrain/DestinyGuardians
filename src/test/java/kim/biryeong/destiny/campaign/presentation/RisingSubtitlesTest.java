package kim.biryeong.destiny.campaign.presentation;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import kim.biryeong.destiny.campaign.RisingServices;
import net.minecraft.client.renderer.PostChainConfig;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Data/asset contract of the presentation lane. Native GPU compile, audio playback and visuals are in-game QA. */
class RisingSubtitlesTest {
    private static final Set<String> EXCLUDED = Set.of("80b75f70", "80b75f73", "80b75f6c", "80b75f6a", "80b75f69",
            "80b75f68", "80b75f6d");

    private static String resource(String path) throws IOException {
        try (var in = RisingSubtitlesTest.class.getResourceAsStream(path)) {
            assertNotNull(in, path);
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    @Test void voiceLinesHaveAudioSoundEventsAndExactSubtitles() throws IOException {
        JsonObject sounds = JsonParser.parseString(resource("/assets/destiny/sounds.json")).getAsJsonObject();
        int voiced = 0, authored = 0;
        for (var line : RisingSubtitles.lines()) {
            assertFalse(line.text().isBlank(), line.id());
            assertTrue(line.ticks() > 0, line.id());
            assertFalse(EXCLUDED.contains(line.id()), "excluded line present: " + line.id());
            if (line.voice()) {
                voiced++;
                assertFalse(line.authored(), line.id());
                String event = RisingServices.Voice.soundEvent(line.id());
                assertTrue(sounds.has(event), event);
                assertEquals("destiny:guardian_rises/voice/" + line.id(), sounds.getAsJsonObject(event)
                        .getAsJsonArray("sounds").get(0).getAsJsonObject().get("name").getAsString());
                try (var ogg = getClass().getResourceAsStream("/assets/destiny/sounds/guardian_rises/voice/" + line.id() + ".ogg")) {
                    assertNotNull(ogg, line.id());
                    assertEquals("OggS", new String(ogg.readNBytes(4), StandardCharsets.US_ASCII));
                }
            } else {
                authored++;
                assertTrue(line.authored(), "subtitle-only lines must be labelled authored: " + line.id());
                assertTrue(line.id().startsWith("rg."), line.id());
            }
        }
        assertEquals(45, voiced); // + 8 c104b wake-up lines (W301, 80b779e7..f0)
        assertEquals(9, authored); // 3 opening/arrival + rg.opening.who class prompt + 5 W300 r4 Walker callouts (rg.walker.*)
        assertEquals("당신의 빛은 강해요, 수호자.", RisingSubtitles.line("80B75F5C").orElseThrow().text());
        assertTrue(RisingSubtitles.line("80b75f70").isEmpty(), "Shaw Han is not part of this adaptation");
        for (String id : List.of("80b75f5c", "80b75f54", "80b75f53", "80b75f56", "80b75f59", "80b75f58", "80b75f5e"))
            assertTrue(RisingSubtitles.line(id).orElseThrow().voice(), "opening line " + id);
    }

    @Test void sfxEventsExist() throws IOException {
        JsonObject sounds = JsonParser.parseString(resource("/assets/destiny/sounds.json")).getAsJsonObject();
        for (String name : RisingAudio.SFX) {
            assertTrue(sounds.has("guardian_rises.sfx." + name), name);
            try (var ogg = getClass().getResourceAsStream("/assets/destiny/sounds/guardian_rises/sfx/" + name + ".ogg")) {
                assertNotNull(ogg, name);
            }
        }
    }

    @Test void wrapKeepsWordsAndWidth() {
        var lines = RisingSubtitles.wrap("모든 게 녹슬고 허물어진 폐허처럼 보이겠죠. 하지만 여길 빠져나가면 상상할 수 없는 경이를 보게 될 거예요.", 34);
        assertTrue(lines.size() >= 2);
        assertEquals("모든 게 녹슬고 허물어진 폐허처럼 보이겠죠. 하지만 여길 빠져나가면 상상할 수 없는 경이를 보게 될 거예요.",
                String.join(" ", lines));
        for (String l : lines) assertTrue(l.codePointCount(0, l.length()) <= 40, l);
        assertEquals(List.of("Heads up!"), RisingSubtitles.wrap("  Heads   up! ", 34));
    }

    @Test void postEffectsParseWithMinecraftCodecAndShadersDeclareTheirBlocks() throws IOException {
        for (String name : List.of("blackout", "scan", "revive", "ship_flash", "fade", "fade_1", "fade_2", "fade_3", "fade_4", "fade_5")) {
            String path = "/assets/destiny/post_effect/guardian_rises/" + name + ".json";
            var json = JsonParser.parseString(resource(path)).getAsJsonObject();
            assertTrue(PostChainConfig.CODEC.parse(JsonOps.INSTANCE, json).result().isPresent(), path);
            for (var pass : json.getAsJsonArray("passes")) {
                String shader = pass.getAsJsonObject().get("fragment_shader").getAsString();
                if (!shader.startsWith("destiny:")) continue;
                String source = resource("/assets/destiny/shaders/" + shader.substring(8) + ".fsh");
                for (String block : pass.getAsJsonObject().getAsJsonObject("uniforms").keySet())
                    assertTrue(source.contains("uniform " + block + " {"), shader + " declares " + block);
            }
        }
        for (var id : Curtain.STEPS)
            assertNotNull(getClass().getResourceAsStream("/assets/destiny/post_effect/" + id.getPath() + ".json"), id.toString());
        assertTrue(RisingSubtitles.line(RisingPresentation.ARRIVAL_LINE).orElseThrow().authored());
        for (var id : RisingPresentation.POSTS)
            assertNotNull(getClass().getResourceAsStream("/assets/destiny/post_effect/" + id.getPath() + ".json"), id.toString());
    }
}
