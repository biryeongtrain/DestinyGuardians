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
    // Normalized-screen ellipse; no aspect/time uniforms or shifted scene samples.
    float radius = length((texCoord - 0.5) * 2.0);
    float quietCenter = smoothstep(0.30, 0.48, radius);
    float edge = smoothstep(0.52, 0.98, radius);
    float band = (radius - Shape.x) / max(Shape.y, 0.01);
    // Broad shoulder carries the event; the soft rim gives it a readable crest.
    float shoulder = 1.0 - smoothstep(0.0, 2.5, abs(band));
    float rim = exp(-band * band);
    float corona = mix(shoulder, rim, 0.25);
    // Lift the spatial response, never the light budget. Exact zero stays zero.
    float response = sqrt(clamp(edge * Shape.z + corona * Shape.w, 0.0, 1.0));
    float strength = clamp(Tint.a * quietCenter * response, 0.0, 0.12);
    // One unshifted sample; headroom blend preserves white and scene alpha.
    vec3 light = Tint.rgb * strength;
    fragColor = vec4(scene.rgb + (1.0 - clamp(scene.rgb, 0.0, 1.0)) * light, scene.a);
}
