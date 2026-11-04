#version 330
#extension GL_ARB_separate_shader_objects : require

uniform sampler2D InSampler;
layout(location = 0) in vec2 texCoord;
layout(location = 0) out vec4 fragColor;

void main() {
    vec4 scene = texture(InSampler, texCoord);
    float lum = dot(scene.rgb, vec3(0.299, 0.587, 0.114));
    float edge = smoothstep(0.20, 0.70, length(texCoord - 0.5));
    // Preserve the central Ghost's blue eye; warm desaturation and crimson live at the edges.
    vec3 grade = mix(scene.rgb, vec3(lum) * vec3(1.08, 0.86, 0.84), 0.25 + edge * 0.30);
    grade *= 1.0 - edge * 0.35;
    grade = mix(grade, vec3(0.32, 0.025, 0.045), edge * 0.42);
    fragColor = vec4(grade, scene.a);
}
