package kim.biryeong.destiny.compat.pack;

import org.junit.jupiter.api.Test;
import java.nio.charset.StandardCharsets;
import static org.junit.jupiter.api.Assertions.*;

class UiFontPackTest {
    private static String resource(String path) throws Exception {
        try (var input = UiFontPackTest.class.getResourceAsStream(path)) {
            assertNotNull(input, path);
            return new String(input.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    @Test void generatedShaderFxAndColoredBitmapPathsSurviveTheFontPass() throws Exception {
        String original = resource("/shaders/text.fsh").replace("//%CASES%", "case 123: color = vec4(1.0); break;");
        String patched = UiFontPack.rewrite("assets/minecraft/shaders/core/text.fsh", original);
        assertTrue(patched.contains("case 123: color = vec4(1.0); break;"));
        assertTrue(patched.contains("color = rgbmap_decode(color);"));
        assertTrue(patched.contains("if (frames > 1)"));
        assertTrue(patched.contains("vec4 texColor = texture(Sampler0, texCoord0);"));
        assertTrue(patched.contains("executeAlphaOnlyPhase(gl_FragCoord.z, color.a);"));
        assertTrue(patched.contains("#ifdef IS_GRAYSCALE\n    vec4 texColor"));
        assertEquals(patched, UiFontPack.rewrite("assets/minecraft/shaders/core/text.fsh", patched));
    }

    @Test void worldAndGuiTextRemainOutsideTheHudFilter() throws Exception {
        String original = resource("/assets/minecraft/shaders/core/text.vsh");
        String patched = UiFontPack.rewrite("assets/minecraft/shaders/core/text.vsh", original);
        int neutral = patched.indexOf("destinyUiFont = 0;");
        int hud = patched.indexOf("if (displayhud_is_hud(Position))");
        int enable = patched.indexOf("destinyUiFont = (effectId == 0 && frames == 0) ? 1 : 0;");
        assertTrue(neutral >= 0 && hud > neutral && enable > hud);
        assertTrue(patched.substring(hud, enable).contains("#ifdef IS_GRAYSCALE"));
        assertTrue(patched.substring(0, hud).contains("#ifndef IS_GUI"));
        assertTrue(patched.contains("displayhud_above_hand_depth(gl_Position.z, UV2)"));
        assertEquals(patched, UiFontPack.rewrite("assets/minecraft/shaders/core/text.vsh", patched));
    }

    @Test void anIncompatibleShaderCannotSilentlyShipHalfOfTheInterface() {
        assertThrows(IllegalStateException.class, () -> UiFontPack.rewrite("text.vsh", "void main() {}"));
        assertThrows(IllegalStateException.class, () -> UiFontPack.rewrite("text.fsh", "void main() {}"));
        assertEquals("unchanged", UiFontPack.rewrite("item.vsh", "unchanged"));
    }
}
