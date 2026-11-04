# Skiff surface sampling comparison

## Question and result

Following unsuccessful shade-only and nearest-color reprojection experiments, inspect whether coincident depth slices or sample-derived depth/color selection cause the residual surface stippling.

The unchanged cutoff candidate has 4,647 excess coincident same-facing texel centers out of 975,934 supported samples (about 0.48%). All detected adjacent duplicates cross bone boundaries. This establishes some exact overlaps, not enough evidence to attribute the widespread defect solely to them. The audit does not detect arbitrary triangle intersections, camera-visible surfaces or GPU depth precision; it rounds centers to 0.001 model pixels and rejects rotated groups/elements.

Added an opt-in exact orthographic raster path in `project_skiff_drive.py`. It intersects source triangles at texel centers, evaluates source UV/coverage before nearest-depth selection, and quantizes depth afterward. Existing rig, shader source, six-face slices, atlas packing and output format remain in use. No hand-made replacement geometry or production model registration.

The exact-center candidate slightly improves color coherence but loses subtexel antennas and lights. It is **not accepted**. Added optional source-sample fallback only for cells not covered by any exact ray. This retains 19,836 source-sampled cells in the fitted candidate. The resulting offline render recovers thin details, but visible stippling and stepped surfaces remain. **No fidelity or native-performance acceptance yet.**

## Comparisons

`comparison.png`: left = previous sample-based model with cutoff-aware FX; middle = exact center rays; right = center rays with subtexel fallback. All rendered with the same headless factory-startup Blender script, lighting, camera and 1200×900 source frame. This is offline rendering, not a Minecraft framebuffer. The initial contact used the earlier compact FX baseline; it was replaced with a freshly rendered cutoff baseline to remove that FX-conversion difference.

| Candidate | Density | Elements | Packed rectangle area |
|---|---:|---:|---:|
| Previous samples | 0.073125 | 12,000 | See prior refined-fit evidence |
| Exact centers | 0.073125 | 12,000 | 0.8495 |
| Centers + fallback | 0.0685546875 | 12,000 | 0.9373 |

Fallback at original density exceeded atlas space (1.1049); the bounded fitter selected about 6.25% lower linear density. This is a tradeoff, not a free fidelity improvement. 12,000 elements remains an experimental cap, not an approved live budget. All candidates remain static and unregistered.

`candidates.json` identifies actual model paths/hashes; `center-stats.json`, `preserved-stats.json` record generation; overlap reports record diagnostics. Five unit tests pass: affine depth/UV, nearest cutout exposing deeper geometry, opposite viewing direction, deterministic coplanar/shared-edge ties, degenerate projection and subtexel fallback exclusion (some combined per test). These tests do not establish visual acceptance.

Generation commands use bundled Python with `--atlas 4096 --max-quads 12000 --density .073125 --rasterized --translucent-fx`, adding `--preserve-subtexel` for the third candidate. Source cache: `/tmp/devils-skiff-shader-neutral-20261104`. Output folders are recorded in `candidates.json`; Downloads originals untouched. `scripts-sha256.json` records the final tool revisions. The additive `surfaceSampling` output metadata field was added while the fallback process already held its source in memory; these two initial candidates therefore predate that metadata field. Their accompanying stats retain the actual sampling method and fallback count.

No client launched or production JAR rebuilt during this experiment. Existing bounded awake coordinator retained. Next: evaluate the fallback candidate against the same native fixture if its tradeoff is acceptable, and continue investigating depth quantization/visible surface selection; do not promote from unit tests or offline similarity alone.
