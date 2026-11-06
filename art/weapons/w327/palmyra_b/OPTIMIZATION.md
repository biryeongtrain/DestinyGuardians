# W327 palmyra_b surface optimization

Emitted elements: 615 → 610. Faces: 3690 → 3618.

This model contains cuboids only, so no contour-cap merging was applied. Retained perimeter thickness, original facet profile and cutouts. Removed cuboid faces only when all four outward-offset corners are contained in a single convex cuboid belonging to the same moving part. Fully buried cuboids emit no elements. Long barrels, rails and original cross sections are retained; no arbitrary subdivision or silhouette flattening.

The authoring design, source mapping, material roles, pivots and retained cuboid transforms are unchanged. Atlas UV packing was regenerated with the same source projection and material pipeline; this is not a claim of byte-identical pixels. Original blend SHA-256, JSON parse, finite transforms, UV bounds, PNG size and body/magazine membership checked. Assembly is below 1,000 emitted elements.

Representative Deliverance side and quarter comparison: `../deliverance/review/optimization/comparison.png`. Cap diagonal seams visibly decrease while frame holes and profiles remain. Offline Blender review only; native pack/client/ADS/reload/FPS acceptance remains with master. Shared helper and kit files were not edited.
