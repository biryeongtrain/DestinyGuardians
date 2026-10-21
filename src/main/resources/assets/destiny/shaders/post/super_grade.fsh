#version 330
#extension GL_ARB_separate_shader_objects : require

// 궁극기 활성 화면 보정 (docs/design/07). Tint.rgb = 속성 색, Tint.a = 강도.

uniform sampler2D InSampler;

layout(location = 0) in vec2 texCoord;

layout(std140) uniform SuperConfig {
    vec4 Tint;
    vec4 Vignette; // x = 비네트 세기, y = 가장자리 색 혼합
};

layout(location = 0) out vec4 fragColor;

void main() {
    vec4 c = texture(InSampler, texCoord);
    float lum = dot(c.rgb, vec3(0.299, 0.587, 0.114));
    vec3 graded = mix(c.rgb, Tint.rgb * (lum * 1.35 + 0.08), Tint.a);
    vec2 d = texCoord - 0.5;
    float edge = smoothstep(0.30, 0.78, length(d));
    graded = mix(graded, Tint.rgb * 0.9, edge * Vignette.y);
    graded *= 1.0 - edge * Vignette.x;
    fragColor = vec4(graded, 1.0);
}
