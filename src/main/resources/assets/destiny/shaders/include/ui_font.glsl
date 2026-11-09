#ifndef DESTINY_UI_FONT_GLSL
#define DESTINY_UI_FONT_GLSL

// FontTexture uses a NEAREST sampler. Reconstruct the coverage between its texels
// only for screen-fixed grayscale glyphs, retaining the source font's soft edges.
float destiny_ui_font_coverage(sampler2D atlas, vec2 uv) {
    ivec2 size = textureSize(atlas, 0);
    vec2 pixel = uv * vec2(size) - 0.5;
    ivec2 origin = ivec2(floor(pixel));
    vec2 blend = fract(pixel);
    ivec2 last = size - ivec2(1);
    float a = texelFetch(atlas, clamp(origin, ivec2(0), last), 0).r;
    float b = texelFetch(atlas, clamp(origin + ivec2(1, 0), ivec2(0), last), 0).r;
    float c = texelFetch(atlas, clamp(origin + ivec2(0, 1), ivec2(0), last), 0).r;
    float d = texelFetch(atlas, clamp(origin + ivec2(1), ivec2(0), last), 0).r;
    return mix(mix(a, b, blend.x), mix(c, d, blend.x), blend.y);
}

#endif
