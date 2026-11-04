# Thrall color and surface isolation — 2026-11-04

Current production model and baseline match SHA256 2d850868818da42ccaa4e0aaee7651be5d2b9b853bf1fd897f222aea6312fb6c. No production model was modified. These are offline Cycles emission-texture frames, not native Minecraft acceptance.

Five identical-camera comparisons: registered source mesh with original shader bake; current depth slices; flat RGB preserving alpha; RGB encoding final pixel model coordinates; and nearest-source reprojection preserving all geometry/rig/animations/alpha.

Flat and coordinate renders show mostly continuous coverage with smaller residual gaps at torso and leg seams. Coordinate RGB varies smoothly, weakening a gross face-UV orientation error. Registered source mesh is visibly smoother than the slice model. Nearest-source reprojection changes 739,957 texels at their final model positions via a triangle BVH and barycentric UV, with bilinear sampling of the source shader bake. Median/95th percentile source distance is 0.080/0.213 model pixels. This global BVH is diagnostic: it does not constrain matching to the owning bone.

Result: nearest-source color reprojection does NOT eliminate the rough/stippled surfaces sufficiently. Rejected for integration. This evidence distinguishes large coverage holes from color/surface correspondence, but does not prove one root cause. Thin overlapping source surfaces, per-bone visibility, depth quantization and interpolation remain to isolate. Do not claim the model quality is accepted.

Reproduction scripts reference explicit isolated /tmp inputs; source Downloads and production model were read-only. Python image processing uses the bundled runtime; Blender runs headless in a separate process. The first mapping attempt repeatedly reloaded compressed UV arrays and was stopped by its verified owned PID; cached UV arrays complete mapping in ~7.4 seconds. A first setup attempt lacked Pillow in system Python; reran with bundled dependencies. These are tooling corrections, not product test failures.
