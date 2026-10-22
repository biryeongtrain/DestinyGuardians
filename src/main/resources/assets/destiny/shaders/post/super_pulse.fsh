#version 330
#extension GL_ARB_separate_shader_objects : require

uniform sampler2D InSampler;

layout(location = 0) in vec2 texCoord;

layout(std140) uniform PulseConfig {
    vec4 Tint;  // rgb = element, a = maximum light contribution
    vec4 Shape; // x = corona radius, y = width, z = edge weight, w = corona weight
};

layout(location = 0) out vec4 fragColor;

void main() {
    vec4 scene = texture(InSampler, texCoord);
    // Normalized-screen corona: deliberately elliptical on wide screens, with a quiet center.
    float radius = length((texCoord - 0.5) * 2.0);
    float edge = smoothstep(0.45, 1.35, radius);
    float band = (radius - Shape.x) / max(Shape.y, 0.01);
    float corona = exp(-band * band);
    float strength = clamp(Tint.a * (edge * Shape.z + corona * Shape.w), 0.0, 0.12);
    // One unshifted scene sample, no blur, darkening, clipping flash or depth/emissive selection.
    vec3 light = Tint.rgb * strength;
    fragColor = vec4(scene.rgb + (1.0 - clamp(scene.rgb, 0.0, 1.0)) * light, scene.a);
}
