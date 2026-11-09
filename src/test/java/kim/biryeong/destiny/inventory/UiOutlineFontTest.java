package kim.biryeong.destiny.inventory;

import com.google.gson.JsonParser;
import com.mojang.blaze3d.font.TrueTypeGlyphProvider;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.gui.font.providers.FreeTypeUtil;
import net.minecraft.client.gui.font.providers.TrueTypeGlyphProviderDefinition;
import org.junit.jupiter.api.Test;
import org.lwjgl.system.MemoryStack;
import org.lwjgl.system.MemoryUtil;
import org.lwjgl.util.freetype.FT_Face;
import org.lwjgl.util.freetype.FreeType;
import java.nio.charset.StandardCharsets;
import static org.junit.jupiter.api.Assertions.*;

class UiOutlineFontTest {
    private static byte[] resource(String path) throws Exception {
        try (var input = UiOutlineFontTest.class.getResourceAsStream(path)) {
            assertNotNull(input, path);
            return input.readAllBytes();
        }
    }

    @Test void nativeClientFontAcceptsEveryLegacyGlyphWithTheSameAdvance() throws Exception {
        var json = JsonParser.parseString(new String(resource("/assets/destiny/font/ui_medium.json"), StandardCharsets.UTF_8));
        var definition = TrueTypeGlyphProviderDefinition.CODEC.codec().parse(JsonOps.INSTANCE,
                json.getAsJsonObject().getAsJsonArray("providers").get(0)).getOrThrow();
        assertEquals(20f, definition.size());
        assertEquals(2f, definition.oversample());
        var bytes = resource("/assets/destiny/font/" + definition.location().getPath());
        var memory = MemoryUtil.memAlloc(bytes.length);
        memory.put(bytes).flip();
        FT_Face face = null;
        TrueTypeGlyphProvider provider = null;
        try {
            synchronized (FreeTypeUtil.LIBRARY_LOCK) {
                try (var stack = MemoryStack.stackPush()) {
                    var pointer = stack.mallocPointer(1);
                    assertEquals(0, FreeType.FT_New_Memory_Face(FreeTypeUtil.getLibrary(), memory, 0, pointer));
                    face = FT_Face.create(pointer.get());
                    assertEquals("TrueType", FreeType.FT_Get_Font_Format(face));
                    assertEquals(0, FreeType.FT_Select_Charmap(face, FreeType.FT_ENCODING_UNICODE));
                    provider = new TrueTypeGlyphProvider(memory, face, definition.size(), definition.oversample(), 0, 0, "");
                }
            }
            var metrics = JsonParser.parseString(new String(resource("/assets/destiny/hud/rg_objective_metrics.json"),
                    StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonObject("medium");
            assertEquals(11364, metrics.size());
            for (var entry : metrics.entrySet()) {
                int codepoint = entry.getKey().codePointAt(0);
                var glyph = provider.getGlyph(codepoint);
                assertNotNull(glyph, "Missing U+" + Integer.toHexString(codepoint));
                assertEquals(entry.getValue().getAsFloat(), glyph.info().getAdvance(), .001f, entry.getKey());
            }
        } finally {
            if (provider != null) provider.close();
            else {
                if (face != null) FreeType.FT_Done_Face(face);
                MemoryUtil.memFree(memory);
            }
        }
    }
}
