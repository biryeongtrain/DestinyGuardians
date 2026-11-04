# Marauder surface diagnostic — 2026-11-04

Status: rejected offline comparison; no production model integration or visual acceptance.

The source cache contains 40,079 triangles. Naive per-bone reduction produced 3,210 triangles / 6,420 native planes. Welding with UV seams preserved produced 3,150 triangles / 6,300 planes. Both comparisons retain black, fragmented surfaces. The direct reduced-mesh control also reproduces the defect, so the native triangle adapter alone does not explain it.

Nearest-source texture reprojection sampled 3,389,760 texels, using only triangles assigned to the same source bone. Median projection distance is 0.00198 m, p95 0.01745 m, maximum 0.16110 m. Inspection of projected front and three-quarter PNGs still shows unacceptable dark/fragmented torso and limbs. A low median distance is not evidence of texture fidelity. The precise cause remains unresolved; material/cache provenance, reduction and projection/render assumptions need separate controls.

`comparison.png` contains source/current/naive controls. `reduced-source-control.png` bypasses the native plane adapter. `projected-*.png` and `projected-projection.json` preserve the latest failed reprojection. Scripts here are diagnostics, not the production asset pipeline.

## Native QA preflight

After the user authorized autonomous visual-client verification, Computer Use still reported the Mac locked. Ports 8102 and 25610 had no listeners. No client was launched, no native screenshot was taken, and no speaker or runtime acceptance is claimed. The existing request for manual unlock remains pending. On unlock, use the bounded keep-awake master wrapper and isolated QA profile; prioritize revive interpolation/completion audio and enemy model surfaces, followed by selected-pad telegraphs and Sepiks warp safety.

## Source and outward-ray controls

`control.py` re-rendered the unchanged source cache, reduced textured geometry, and both meshes with a solid diffuse material. The unchanged source reproduces its expected appearance. The reduced solid control retains broad surfaces, whereas its texture produces dark fragmentation. This separates texture correspondence from gross surface absence, although the reduction is visibly coarse.

The optional `project.py --normal-ray` control casts from 0.2 m outside along each reduced triangle normal into the same-source-bone BVH. It accepts a source hit with normal dot >0.1, falling back to nearest projection otherwise. 3,166,351 texels used a ray hit and 223,409 used fallback. Median source distance 0.00982 m, p95 0.11792 m, max 0.20000 m. `projection-controls.png` shows a substantial visible reduction of black fragmentation in the ray result, but cloth and joints remain distorted. The wide ray reach can transfer colour from another nearby layer. No fidelity acceptance or performance benefit is claimed.

These controls implicate selection of hidden/dark source surfaces in nearest reprojection. They do not establish that this is the sole cause in the production depth-slice pipeline. Next investigation should preserve the approved Dreg-Light method and isolate hidden surfaces / directional source sampling there, rather than adopt the 6,420-plane triangle diagnostic. The production source-radiance bake and group boundaries also need inspection before changing the shared baker.
