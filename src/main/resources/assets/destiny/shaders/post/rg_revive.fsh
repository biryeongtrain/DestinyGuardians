#version 330
#extension GL_ARB_separate_shader_objects : require

// W300 Guardian Rises — original authored bloom (not extracted). Light returns / ship flash.
#include <minecraft:globals.glsl>

uniform sampler2D InSampler;

layout(std140) uniform SamplerInfo {
    vec2 OutSize;
    vec2 InSize;
};

layout(std140) uniform ReviveConfig {
    vec4 Tint;  // rgb = light colour, a = centre wash strength
    vec4 Shape; // x = wash radius, y = bloom spread (px), z = scene exposure, w = ray shimmer
};

layout(location = 0) in vec2 texCoord;
layout(location = 0) out vec4 fragColor;

vec3 bright(vec2 uv) {
    vec3 c = texture(InSampler, uv).rgb;
    return max(c - vec3(0.55), vec3(0.0)) * 2.2;
}

void main() {
    vec4 scene = texture(InSampler, texCoord);
    vec2 texel = Shape.y / max(InSize, vec2(1.0));
    // 12-tap ring bloom on bilinear samples: highlights spill, the image itself stays sharp.
    vec3 glow = vec3(0.0);
    for (int i = 0; i < 12; i++) {
        float a = float(i) * 0.5235988;
        vec2 dir = vec2(cos(a), sin(a));
        glow += bright(texCoord + dir * texel) + 0.6 * bright(texCoord + dir * texel * 2.3);
    }
    glow /= 19.2;

    vec2 c = (texCoord - 0.5) * vec2(OutSize.x / max(OutSize.y, 1.0), 1.0);
    float r = length(c);
    float seconds = GameTime * 1200.0;
    float rays = 0.75 + 0.25 * sin(atan(c.y, c.x) * 11.0 + seconds * 0.9) * sin(atan(c.y, c.x) * 5.0 - seconds * 0.5);
    float wash = Tint.a * (1.0 - smoothstep(0.0, max(Shape.x, 0.01), r)) * mix(1.0, rays, Shape.w);

    vec3 lit = scene.rgb * Shape.z + glow * Tint.rgb;
    fragColor = vec4(mix(lit, Tint.rgb, clamp(wash, 0.0, 1.0)), scene.a);
}
