# W47 — Beloved reload

Beloved is the only weapon with W47 reload assets. The main implementation session
viewed 23.3–25.3 seconds of the existing private download of
[MaverickSylvin's Beloved review](https://www.youtube.com/watch?v=xEu_l7vOJBQ)
(uploaded 2022-05-31). The rifle pitches and rolls up toward the left, the magazine
is pulled down and replaced, and the rifle returns to ready. These are qualitative
observations reported by that session; this sidecar did not independently view the video.

`gameplay-references.json` carries the original video and metadata SHA-256 pins from
`art/weapons/w45-models/references.json`. The reviewed window is a location in that
historical video, not an exact action duration or a current-sandbox timing measurement.
The private download is not included in the repository or resource pack.

The generated animation is a reference-informed approximation using 21 normalized
progress stages, from 0 to 1 in 0.05 increments. These stages are authored samples,
not source-video frames or measured event timings. There is no hand IK, animated
hand model, bolt simulation, or exact animation rip. No other weapon reload is claimed.

`scripts/generate_reload_models_w47.py` owns the assets and `manifest.json`. The
original 253 Beloved cubes are preserved as 243 body cubes and 10 magazine cubes,
selected by original element indices 107, 108, 109, 110, 111, 115, 120, 194, 195,
and 203. The magazine translates along its rotated local downward axis without
changing its geometry, rotation relative to the body, or scale. Start and end
poses reproduce the original HIP display transforms for native and two-hand grips.

The item wrapper selects reload models only in `firstperson_righthand` and
`firstperson_lefthand`. Progress uses custom-model-data float index 1; two-hand grip
uses boolean index 0. Every stage composites one body and one magazine. Third-person
and all other contexts retain the complete original item wrapper as their fallback,
including its ADS, inspect, and grip choices. This does not add third-person animation.

`WeaponReloadAssetsW47Test` covers all 87 generated asset hashes and inventory,
independently pinned original sources, the native Minecraft 26.3 `ItemModels.CODEC`
and `CuboidModel` parser, wrapper selection, all 21 stage references, exact geometry
partition, HIP endpoints, rigid magazine motion, and both hand/grip transforms.
The main session owns the JUnit/Gradle gate and subsequent launch QA; this sidecar
does not run Gradle or certify in-game playback.
