#version 330
#extension GL_ARB_separate_shader_objects : require

// W300 Guardian Rises — original authored grade (not extracted). Darkness / Ghost scan.
// Animation uses only the vanilla Globals.GameTime (game ticks / 24000), so it keeps
// moving without any server uniform traffic. Periods are whole seconds (see heartbeat note).
#include <minecraft:globals.glsl>

uniform sampler2D InSampler;

layout(std140) uniform ScanConfig {
    vec4 Tint; // rgb = scan light colour, a = exposure kept for the un-keyed scene (0 = black)
    vec4 Key;  // x = cyan saturation key threshold, y = key softness, z = key gain, w = desaturation of the scene
    vec4 Fx;   // x = sweep band, y = scanlines, z = heartbeat, w = sweep period in seconds
};

layout(location = 0) in vec2 texCoord;
layout(location = 0) out vec4 fragColor;

void main() {
    vec4 scene = texture(InSampler, texCoord);
    float seconds = GameTime * 1200.0;
    float lum = dot(scene.rgb, vec3(0.299, 0.587, 0.114));

    // Ghost light key: the eye/beam are bright, strongly saturated cyan. Daylight sky is blue but pale
    // (low saturation), so it fails the key; blindness fog removes it anyway during the opening.
    float peak = max(scene.r, max(scene.g, scene.b));
    float cyan = (max(scene.g, scene.b) - scene.r) / max(peak, 0.001);
    float key = smoothstep(Key.x, Key.x + Key.y, cyan) * smoothstep(0.30, 0.55, peak);
    vec3 cold = mix(scene.rgb, vec3(lum) * vec3(0.80, 0.95, 1.10), Key.w);
    vec3 base = mix(cold * Tint.a, scene.rgb * Key.z, key);

    // Soft halo around keyed light so a small eye reads as a light source in the dark (8 taps).
    vec2 ring = vec2(ScreenSize.y / max(ScreenSize.x, 1.0), 1.0) * 0.012;
    vec3 halo = vec3(0.0);
    for (int i = 0; i < 8; i++) {
        float a = float(i) * 0.7853982;
        vec3 s = texture(InSampler, texCoord + vec2(cos(a), sin(a)) * ring).rgb;
        float sp = max(s.r, max(s.g, s.b));
        float sk = smoothstep(Key.x, Key.x + Key.y, (max(s.g, s.b) - s.r) / max(sp, 0.001)) * smoothstep(0.30, 0.55, sp);
        halo += s * sk;
    }
    base += halo * (0.08 * Key.z);

    // Head-to-toe sweep: a bright band travelling down the screen with a fading wake above it.
    float phase = fract(seconds / max(Fx.w, 0.1));
    float line = 1.08 - phase * 1.16;
    float d = texCoord.y - line;
    float band = exp(-d * d * 2600.0) + 0.35 * exp(-max(d, 0.0) * 18.0) * step(0.0, d);
    float lines = 0.5 + 0.5 * sin(texCoord.y * ScreenSize.y * 1.5707963);

    // Two-beat pulse (lub-dub) every 1.0 s (60 bpm), strongest at the frame edge. All periods are
    // 20 ticks so a frozen Fantasy level clock (client re-synced every 20 ticks) still loops seamlessly.
    float p = fract(seconds);
    float beat = exp(-p * p * 160.0) + 0.55 * exp(-(p - 0.21) * (p - 0.21) * 160.0);
    float radius = length((texCoord - 0.5) * vec2(1.6, 1.0));
    float edge = smoothstep(0.35, 1.05, radius);

    vec3 light = Tint.rgb * (band * Fx.x * (0.55 + 0.45 * lines) + beat * Fx.z * (0.25 + edge));
    vec3 graded = base * (1.0 - edge * 0.55) * (1.0 - Fx.y * 0.18 * (1.0 - lines));
    fragColor = vec4(graded + (1.0 - clamp(graded, 0.0, 1.0)) * light, scene.a);
}
