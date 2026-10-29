
    // Only owner-only probe displays use this reserved lane and legal brightness marker.
    destinyArmInfo = 0;
    if (Position.y < -9000000.0 && Position.y > -11000000.0 && UV2.y == 208 && UV2.x >= 0 && UV2.x <= 240) {
        destinyArmInfo = UV2.x / 16 + 1;
        vec3 p = Position + vec3(0.0, 10000000.0, 0.0);
        float aspect = abs(ProjMat[1][1] / ProjMat[0][0]);
        gl_Position = vec4(-p.x / 96000.0 * (16.0 / 9.0) / aspect, p.y / 54000.0,
                          0.6 - clamp(p.z / 2000000.0, -0.05, 0.05), 1.0);
        sphericalVertexDistance = 0.0;
        cylindricalVertexDistance = 0.0;
#ifdef PER_FACE_LIGHTING
        vertexPerFaceColorBack = Color;
        vertexPerFaceColorFront = Color;
#else
        vertexColor = Color;
#endif
#ifndef EMISSIVE
        lightMapColor = vec4(1.0);
#endif
#ifndef NO_OVERLAY
        overlayColor = vec4(0.0, 0.0, 0.0, 1.0);
#endif
    }
