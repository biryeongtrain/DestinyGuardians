package kim.biryeong.destiny.hud;

import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.PolymerResourcePackUtils;
import eu.pb4.polymer.resourcepack.api.ResourcePackBuilder;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

/**
 * W96: preserve authored nonzero alpha only for the explicitly marked critical ItemDisplayHud.
 * Pins the installed DisplayHUD 2.2 item vertex shader and vanilla 26.3 item fragment shader.
 * Unknown upstream bytes fail pack generation; this is deliberately not a general shader rewriter.
 */
public final class CriticalHudShader {
    public static final int BLOCK_LIGHT = 2;
    public static final int SKY_LIGHT = 3;

    static final String VERTEX_PATH = "assets/minecraft/shaders/core/item.vsh";
    static final String FRAGMENT_PATH = "assets/minecraft/shaders/core/item.fsh";
    private static final String VERTEX_SHA = "62a807a1cebf32fa1dcbd8633d7380c648c5d79a16c87d4295115644c80d55bc";
    private static final String FRAGMENT_SHA = "fe75ae09610add034d2578dff26ad4e95e75625253d7f7275d076da15ecc92c4";
    private static final String PATCHED_VERTEX_SHA = "d70487494707a61a682fe494a96fcdc317406e09bc228757b2b51d75ea989fa5";
    private static final String PATCHED_FRAGMENT_SHA = "fcdc2561724112ad48b91ed69da646ee9433a0346d25c12ac1e2814cbe3a213c";
    private static final String MAIN = "void main() {\n";
    private static final String VERTEX_FLAG = "layout(location = 7) flat out int destinyCriticalHud;\n\n";
    private static final String FRAGMENT_FLAG = "layout(location = 7) flat in int destinyCriticalHud;\n\n";
    private static final String MARKER =
            "    destinyCriticalHud = (displayhud_is_hud(Position) && all(equal(UV2, ivec2(32, 48)))) ? 1 : 0;\n";
    private static final String ORIGINAL_CUTOUT = """
                vec4 color = texture(Sampler0, texCoord0);
                #ifdef ALPHA_CUTOUT
                if (color.a < ALPHA_CUTOUT) {
                    discard;
                }
                #endif
            """;
    private static final String CRITICAL_CUTOUT = """
                vec4 color = texture(Sampler0, texCoord0);
                if (destinyCriticalHud == 1) {
                    // True transparency must not contribute depth, including OIT_ALPHA_ONLY.
                    if (color.a == 0.0) {
                        discard;
                    }
                } else {
                #ifdef ALPHA_CUTOUT
                if (color.a < ALPHA_CUTOUT) {
                    discard;
                }
                #endif
                }
            """;
    private static boolean initialized;

    private CriticalHudShader() {}

    /** Called once by product initialization; repeat calls do not register duplicate converters. */
    public static synchronized void init() {
        if (initialized) return;
        PolymerResourcePackUtils.RESOURCE_PACK_CREATION_EVENT.register(CriticalHudShader::configure);
        initialized = true;
    }

    static void configure(ResourcePackBuilder builder) {
        // Installed Polymer applies converters at output time, after copying and pre-finish tasks.
        builder.addResourceConverter(CriticalHudShader::convert);
        builder.addPreFinishTask(CriticalHudShader::prepare);
    }

    static void prepare(ResourcePackBuilder builder) {
        String vertex = requiredSource(builder, VERTEX_PATH);
        String fragment = requiredSource(builder, FRAGMENT_PATH);
        // Validate the pair before adding either source. Vanilla item.fsh is absent from the old pack;
        // converters only visit emitted resources, so explicitly materialize it from Polymer sources.
        transform(VERTEX_PATH, vertex);
        transform(FRAGMENT_PATH, fragment);
        materialize(builder, VERTEX_PATH, vertex);
        materialize(builder, FRAGMENT_PATH, fragment);
    }

    private static String requiredSource(ResourcePackBuilder builder, String path) {
        byte[] bytes = builder.getDataOrSource(path);
        if (bytes == null) throw incompatible(path, "missing resource and source");
        return new String(bytes, StandardCharsets.UTF_8);
    }

    private static void materialize(ResourcePackBuilder builder, String path, String source) {
        if (builder.getResource(path) == null && !builder.addData(path, PackResource.fromString(source))) {
            throw incompatible(path, "could not add required shader");
        }
    }

    static PackResource convert(String path, PackResource resource) {
        if (!isTarget(path)) return resource;
        if (resource == null) throw incompatible(path, "missing converter input");
        String source = resource.asString();
        String result = transform(path, source);
        return result.equals(source) ? resource : PackResource.fromString(result);
    }

    /** Pure byte-pinned source transformation, also used by source-only regression tests. */
    static String transform(String path, String source) {
        if (!isTarget(path)) return source;
        if (source == null) throw incompatible(path, "missing shader source");
        boolean vertex = VERTEX_PATH.equals(path);
        String fingerprint = sha256(source);
        String patchedHash = vertex ? PATCHED_VERTEX_SHA : PATCHED_FRAGMENT_SHA;
        if (fingerprint.equals(patchedHash)) return source;
        if (!fingerprint.equals(vertex ? VERTEX_SHA : FRAGMENT_SHA)) {
            throw incompatible(path, "unsupported SHA-256 " + fingerprint);
        }
        String result = vertex
                ? replaceOnce(path, source, MAIN, VERTEX_FLAG + MAIN + MARKER)
                : replaceOnce(path, replaceOnce(path, source, MAIN, FRAGMENT_FLAG + MAIN),
                        ORIGINAL_CUTOUT, CRITICAL_CUTOUT);
        if (!sha256(result).equals(patchedHash)) throw incompatible(path, "unexpected transform result");
        return result;
    }

    private static boolean isTarget(String path) {
        return VERTEX_PATH.equals(path) || FRAGMENT_PATH.equals(path);
    }

    private static String replaceOnce(String path, String source, String anchor, String replacement) {
        int at = source.indexOf(anchor);
        if (at < 0 || source.indexOf(anchor, at + anchor.length()) >= 0) {
            throw incompatible(path, "missing or duplicate transformation anchor");
        }
        return source.substring(0, at) + replacement + source.substring(at + anchor.length());
    }

    private static String sha256(String source) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(source.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException impossible) {
            throw new AssertionError(impossible);
        }
    }

    private static IllegalStateException incompatible(String path, String reason) {
        return new IllegalStateException("W96 critical HUD shader rejected " + path + ": " + reason);
    }
}
