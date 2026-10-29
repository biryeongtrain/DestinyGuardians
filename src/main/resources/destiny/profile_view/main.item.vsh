
    // Cuboid emission 15 raises both light channels to 240, replacing the sky-12 marker.
    if (Position.y < -9000000.0 && Position.y > -11000000.0 && (UV2.y == 192 || (UV2.x == 240 && UV2.y == 240))) {
        vec3 p = (Position + vec3(0.0,10000000.0,0.0)) / 32000.0;
        float aspect = displayhud_screen_aspect();
        float focal = 1.428148;
        // Preserve signed w: the GPU clips complete triangles at the near plane.
        float w = -p.z;
        gl_Position = vec4(p.x*focal/aspect,p.y*focal,w*(0.85-clamp(w/64.0,0.0,0.20)) + 0.025*(0.15+0.025/64.0),w);
        vertexColor=Color;
#ifndef OIT_ALPHA_ONLY
        lightMapColor=vec4(1.0);
        overlayColor=vec4(0.0,0.0,0.0,1.0);
        sphericalVertexDistance=0.0;
        cylindricalVertexDistance=0.0;
#endif
    }
