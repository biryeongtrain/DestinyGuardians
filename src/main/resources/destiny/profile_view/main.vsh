
    destinyArmInfo = 0;
    if (Position.y < -9000000.0 && Position.y > -11000000.0 && (UV2.y == 208 || UV2.y == 192)) {
        if (UV2.y == 208 && UV2.x >= 0 && UV2.x <= 240) destinyArmInfo = UV2.x / 16 + 1;
        vec3 p = (Position + vec3(0.0,10000000.0,0.0)) / 32000.0;
        float aspect = displayhud_screen_aspect();
        float focal = 1.428148;
        // Preserve signed w: the GPU clips complete triangles at the near plane.
        float w = -p.z;
        gl_Position = vec4(p.x*focal/aspect, p.y*focal, w*(0.85-clamp(w/64.0,0.0,0.20)) + 0.025*(0.15+0.025/64.0), w);
        sphericalVertexDistance = 0.0;
        cylindricalVertexDistance = 0.0;
        // Skin arms use a player-head UV carrier with a remapped silhouette.
        // DisplayHud flattened the colors above; recompute native weapon lighting.
        if (UV2.y == 208) {
#ifdef PER_FACE_LIGHTING
            vertexPerFaceColorBack = Color;
            vertexPerFaceColorFront = Color;
#else
            vertexColor = Color;
#endif
        } else {
#ifdef PER_FACE_LIGHTING
            vec2 weaponLight = minecraft_compute_light(Light0_Direction, Light1_Direction, Normal);
            vertexPerFaceColorBack = minecraft_mix_light_separate(-weaponLight, Color);
            vertexPerFaceColorFront = minecraft_mix_light_separate(weaponLight, Color);
#elif defined(NO_CARDINAL_LIGHTING)
            vertexColor = Color;
#else
            vertexColor = minecraft_mix_light(Light0_Direction, Light1_Direction, Normal, Color);
#endif
        }
#ifndef EMISSIVE
        lightMapColor = vec4(1.0);
#endif
#ifndef NO_OVERLAY
        overlayColor = vec4(0.0,0.0,0.0,1.0);
#endif
    }
