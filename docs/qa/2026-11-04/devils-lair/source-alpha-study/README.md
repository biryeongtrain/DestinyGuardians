# Explicit shader coverage — Marauder control

The production shader bake wrote `combined.png` as RGB. The downstream Dreg-Light sampling converted it to RGBA and used its synthetic alpha=255 to decide surface visibility. Pure-emission cards had a separate removal path, but ordinary transparent materials did not. Earlier source-cache comparisons using only this RGB texture also incorrectly showed some transparent cloak surfaces as black.

An isolated emission bake evaluates shader closure coverage in the original evaluated scene and existing shader_bake UV layout. It supports nested shader groups and Mix Shader factors; Principled Alpha is preserved, transparent closures are zero, opaque/emission closures one, and Add Shader coverage uses maximum. Pure-emission visibility remains governed separately by the emission texture. Unsupported closure types raise an error. This is cutout coverage for the Minecraft adaptation, not a full optical transparency simulation.

The independently baked mask classified 10,868 of 40,079 triangle centres below 0.5; 8,198 of these were also dark in combined RGB. This centre audit is not a surface-area percentage. A newly rendered original-shader comparison confirms transparent cloak/detail surfaces that the RGB-only control had represented as black.

## Tooling change

- `scripts/strikes/bake_shader_coverage.py` writes compressed linear float coverage and metadata, then restores original shader outputs, nodes and group interfaces.
- `build_devils_models.py` source dumps now emit pipeline version 5 with coverage file and SHA256. The native Dreg-Light consumer verifies hash, shape and finite values, then applies coverage >=0.5 alongside existing emission rules.
- Version-4 caches remain readable and are explicitly labelled legacy alpha in stats; they are not retroactively fixed. Regeneration is required before claiming other enemy assets are repaired.

Validation: the reusable helper output is pixel-identical to the independent prototype; graph node/link snapshots match before and after baking. The comparison preserves original colour/emission textures and 17 animation clips. The alpha prototype has 2,119 planes versus the previous 2,106. Source assets in Downloads were not modified.

The corrected Dreg-Light comparison removes some false black surfaces and improves transparency. Close-range stepped/noisy surfaces remain unacceptable for final fidelity. At the initial control stage no runtime model was replaced; see the integration follow-up below. No Minecraft screenshot/FPS/audio evidence was produced, and this is not visual acceptance. The original-shader frame uses actual restored source material graphs; the two slice frames use emissive baked colours, so luminance is not an exact like-for-like shading comparison.

`inspect-baked-images.py` examined generated images reopened from the saved scene. Generated buffers may be reinitialized on load; their all-one alpha alone is not evidence about the original bake buffer. The RGB file mode, independently rebaked shader mask and actual shader render establish the missing coverage problem.

## Sampling controls and integration follow-up

The coverage-preserving exact-texel control has 2,123 planes and still shows rough surface striping; it is not integrated. The fine-spacing control uses 5,653 planes, 4096 atlas, density 1.0 and spacing scale 0.4941 (versus 2,119 / 2048 / 0.8811 / 1.4776 for the coverage-only model). Arms and torso appear smoother in the same offline q34 render, but detail/step artifacts remain. Its 2.67x plane count and 4x atlas area require native FPS/MSPT checks before adoption. The fine renderer explicitly uses the model's atlas resolution instead of the old helper's hardcoded 2048. An initial density-only run reset the requested spacing to its spec default; it is preserved separately and is not described as the fine-spacing result.

The small coverage correction was regenerated with canonical `dl_marauder` identifiers and integrated into `src/main/resources/destiny/devils_lair/models/dl_marauder.bbmodel`. Before replacement, the runtime model byte-matched the audited original cache. All 17 animation JSON objects are exactly equal before/after; the face count changes 2,106 -> 2,119 and the atlas remains 2048. Previous asset and hashes are preserved in `before-dl_marauder.bbmodel` and `integration.json`. Other enemy assets remain untouched; this is a correctness improvement within an unfinished quality pass, not a claim of final visual acceptance.

Integration validation: DevilsModelAssetsTest 2/2 passed (bundled install/foreign-copy preservation and runtime clip contracts); real Gradle `test ... jar` exited 0. The packaged Marauder model is byte-identical to the current resource. No full-suite rerun for this isolated art correction; the prior 16 regression failures are not resolved by this scoped pass. See `asset-build.json`.
