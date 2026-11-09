package kim.biryeong.destiny.compat.pack;

import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.PolymerResourcePackUtils;
import java.nio.charset.StandardCharsets;

/** Filtering for screen-fixed grayscale outline fonts. World text, bitmap art and ShaderFX keep their own path. */
public final class UiFontPack {
    private static final String MARKER = "// Destiny UI outline font filtering";
    private static boolean initialized;
    private UiFontPack() { }

    public static synchronized void init() {
        if (initialized) return;
        initialized = true;
        PolymerResourcePackUtils.RESOURCE_PACK_CREATION_EVENT.register(builder ->
                builder.addPreFinishTask(output -> output.addResourceConverter((path, data) -> {
                    if (data == null || !(path.equals("assets/minecraft/shaders/core/text.vsh")
                            || path.equals("assets/minecraft/shaders/core/text.fsh"))) return data;
                    return PackResource.of(rewrite(path, new String(data.readAllBytes(), StandardCharsets.UTF_8))
                            .getBytes(StandardCharsets.UTF_8));
                })));
    }

    static String rewrite(String path, String source) {
        if (source.contains(MARKER)) return source;
        if (path.endsWith("text.vsh")) {
            source = replace(source, "layout(location = 3) out vec2 texCoord0;",
                    "layout(location = 3) out vec2 texCoord0;\n" + MARKER
                            + "\nlayout(location = 8) flat out int destinyUiFont;");
            source = replace(source, "texCoord0 = UV0;", "texCoord0 = UV0;\n    destinyUiFont = 0;");
            return replace(source, "if (displayhud_is_hud(Position)) {", """
                    if (displayhud_is_hud(Position)) {
                    #ifdef IS_GRAYSCALE
                            destinyUiFont = (effectId == 0 && frames == 0) ? 1 : 0;
                    #endif""");
        }
        if (path.endsWith("text.fsh")) {
            source = replace(source, "layout(location = 3) in vec2 texCoord0;",
                    "layout(location = 3) in vec2 texCoord0;\n" + MARKER
                            + "\nlayout(location = 8) flat in int destinyUiFont;"
                            + "\n#include <destiny:ui_font.glsl>");
            source = replace(source, "vec4 texColor = texture(Sampler0, texCoord0).rrrr;", """
                    vec4 texColor = texture(Sampler0, texCoord0).rrrr;
                        if (destinyUiFont != 0) texColor = vec4(destiny_ui_font_coverage(Sampler0, texCoord0));""");
            return replace(source, "if (color.a < 0.1) {",
                    "if (color.a < (destinyUiFont != 0 ? (1.0 / 255.0) : 0.1)) {");
        }
        return source;
    }

    private static String replace(String source, String anchor, String value) {
        int at = source.indexOf(anchor);
        if (at < 0 || source.indexOf(anchor, at + anchor.length()) >= 0)
            throw new IllegalStateException("UI font shader contract changed: " + anchor);
        return source.substring(0, at) + value + source.substring(at + anchor.length());
    }
}
