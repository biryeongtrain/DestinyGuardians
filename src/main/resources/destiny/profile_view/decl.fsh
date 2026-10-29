layout(location = 8) flat in int destinyArmInfo;
// Input is the native head cube UV net; output is the matching 6-pixel arm segment.
vec4 destinyArmSample(vec2 uv, int encoded) {
    int info = encoded - 1;
    bool leftArm = (info & 1) != 0;
    bool upper = (info & 2) != 0;
    bool slim = (info & 4) != 0;
    bool sleeve = (info & 8) != 0;
    vec2 px = uv * 64.0;
    // The hat cube has its own UV island. A sleeve is sampled on the arm surface below.
    if (px.x >= 32.0) discard;
    float w = slim ? 3.0 : 4.0;
    vec2 origin = leftArm ? vec2(36.0,58.0) : vec2(44.0,26.0);
    if (upper) origin.y -= 6.0;
    vec2 dest;
    vec2 size;
    vec2 local;
    if (px.y < 8.0) {
        bool topFace = px.x < 16.0;
        // Elbow seam omits the internal cap, exactly like W204 cuboid arms.
        if (topFace == upper) discard;
        local = vec2((px.x - (topFace ? 8.0 : 16.0))/8.0, px.y/8.0);
        dest = upper ? origin-vec2(0.0,4.0) : origin+vec2(w,-10.0);
        size = vec2(w,4.0);
    } else {
        float face = floor(min(px.x,31.999)/8.0);
        local = vec2((px.x-face*8.0)/8.0, (px.y-8.0)/8.0);
        // Native head side UV runs opposite the arm's shoulder-to-wrist axis.
        local.y = 1.0-local.y;
        // head east, north, west, south -> native arm face origins
        dest = origin + vec2(face < 0.5 ? -4.0 : face < 1.5 ? 0.0 : face < 2.5 ? w : w+4.0, 0.0);
        size = vec2((face < 0.5 || (face > 1.5 && face < 2.5)) ? 4.0 : w,6.0);
    }
    // Half-texel clamp prevents atlas bleed at a UV island boundary.
    vec2 samplePx = dest + clamp(local*size,vec2(0.5),size-vec2(0.5));
    vec4 base = texture(Sampler0,samplePx/64.0);
    if (sleeve) {
        vec2 offset = leftArm ? vec2(16.0,0.0) : vec2(0.0,16.0);
        vec4 outer = texture(Sampler0,(samplePx+offset)/64.0);
        base.rgb = mix(base.rgb,outer.rgb,outer.a);
    }
    return vec4(base.rgb,1.0);
}
