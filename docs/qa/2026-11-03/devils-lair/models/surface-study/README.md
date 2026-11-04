# Marauder surface diagnosis

All four candidates were evaluated offline and rejected for integration in this batch. Source files and runtime model bytes were preserved. These are emissive-texture Cycles comparisons, not Minecraft acceptance or measured game performance.

- Colour dilation: 228864 of761512 opaque texels change when filling from the projected destination colour instead of the first neighbour. Geometry, rig, animations and alpha are identical; visual gain insufficient.
- Finer slices:4197 versus2106 quads at2048 atlas. Face/hood readability improves, but cloth striping remains. Roughly doubled geometry without demonstrated acceptable visual quality.
- Finer slices plus4096 atlas:4166 quads. Small additional gain; fourfold nominal texture area is unjustified at this stage.
- Normal-axis filter abs(normal component)>=0.5:2163 quads, density1.0. Introduces surface gaps; rejected. Initial experiment had an unqualified FACES name and was corrected before generating the reported candidate.
- Correct outward winding and backface masking were also rendered for the current model. Surface defects persist; this offline material does not emulate Minecraft directional lighting or animated display transforms.

The source comparison intentionally uses the previously evaluated combined shader radiance; lower-hand arcs are supplied separately by the emission bake in candidates. Do not interpret the black source arc cards as missing actual source emission.

Next: controlled native-client near/mid-distance model comparison to localize the visible defect before changing the shared projection algorithm or raising all model budgets. No FPS, multiplayer, animation-contact or in-game acceptance claimed. No candidate is a release.

## Exact-raster follow-up

Computer Use repeated the locked-Mac result; no native QA client was launched.
Independent offline experiments used the registered Marauder shader cache unchanged.
`exact-extract.py` computes each texel-centre/triangle intersection and its UV directly,
retaining shader alpha and emission. `exact-run.py` reproduces the experiment with an
explicit isolated cache and native cache. It is Marauder-only diagnostic code, not a
replacement shared baker (the placeholder `win` indices are not valid for authored
Brig core recolouring). Runtime models and readonly source assets were not changed.

- Exact raster: 2106 quads, 17 clips. Face detail improves subjectively, but cloth/arms
  remain broken. Not accepted for integration.
- Exact raster without merge, depth walls or dilation: 2089 quads, 17 clips. Exposes
  additional gaps; not accepted. Packing adapts density, so this is a combined
  no-fill diagnostic, not an equal-density performance/fidelity comparison.
- Cycles transparent bounce cap 128 vs 1024 produced pixel-identical frontal output;
  renderer transparency depth does not explain this capture's defect.
- North-face-only orthographic diagnostic also remains visibly broken. This weakens
  a purely cross-axis overlap explanation; depth slices/rig partitions and UV mapping
  still require isolation. Do not claim exact raster solves the production defect.

`exact-comparison.png`: source / current / exact / exact without fill, same q34 camera.
These are headless Blender frames, not actual Minecraft rendering or native input.
