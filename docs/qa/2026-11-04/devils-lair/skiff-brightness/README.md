# Skiff hull brightness — 2026-11-04

User requested a brighter, opaque-looking hull after viewing the native image.
The original hull already has only alpha 0 and 255; enabling opaque would not raise its baked RGB
and forcing all pixels opaque would destroy the slice silhouette. Apply gamma 0.65 to RGB of the
hull PNG only, with the reusable scripts/assets/adjust_model_texture_gamma.py utility.

Visible texel mean encoded luma increases from 30.71 to 56.94. This is a readability adjustment,
not a claim to source-exact material radiance. Every alpha byte, emission PNG, element, UV, bone,
and animation remains identical. adjustment.json records both texture and model hashes.
The exact-hash atlas routing catalog is updated to the new hull PNG.

Targeted model/pack tests: 6 passed; actual Gradle JAR succeeded. No new Java gameplay or lifecycle
behavior changed in this brightness pass, so the preceding full regression is not repeated.
Native before/after uses the same isolated server fixture and camera, daylight, no local pack override.

Native-after.png was viewed: hull is visibly lighter, silhouette and orange optics retained.
comparison.png is a crop-only side-by-side of actual framebuffers, not a synthetic model render.
Flight/mob delivery integration remains separate and incomplete.
