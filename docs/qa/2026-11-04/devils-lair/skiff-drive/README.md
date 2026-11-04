# Dusk skiff shader source and bake

The user's supplied [House of Dusk Drive folder](https://drive.google.com/drive/folders/1cSe27uEuAvI0SUfJipNAs886xHFGEYzM) contains a skiff archive and reference render, located during this investigation. Download IDs, file sizes, and SHA256 are in `download-manifest.json`. New files reside in `/Users/qf/Downloads/Devils-Lair-Skiff-Drive-2026-11-04`; existing Downloads assets were not modified.

## Source verification

The supplied `.blend` contains 36 meshes and a 20-bone rig with connected shader graphs. File textures resolve against its extracted PNGs; the only unloaded image datablock is Blender's unrelated `Render Result`. `scene-audit.json` records image resolution, materials/node groups, meshes and bones. `source-shader-preview.png` is an actual isolated Blender render with the source materials under authored inspection lighting. It shows the expected brown hull, violet paint/flags and orange optics, unlike the earlier raw-FBX albedo diagnostic. This intermediate image was shown to the user. It is not a Minecraft screenshot or proof of a converted model.

Ten primary bones map exactly by their little-endian numeric hash to the earlier native 10-bone motion rig. A 180-degree Z rotation aligns the bone heads with maximum discrepancy 0.0000031473 source units (`native-rig-correspondence.json`). Ten additional Drive bones remain; do not discard or animate them by nearest-bone guess. This establishes head correspondence only, not full retarget correctness.

## Bake

`scripts/strikes/bake_skiff_drive.py` invokes the existing strike `drive_shader_dump` pipeline with an owned output cache. It preserves source shader graphs, evaluates the mesh/rig, records legacy transparency-closure compatibility repairs, and bakes combined radiance, separate emission and independent coverage. Source files are never saved. The intermediate evaluated scene is saved only under `/tmp/devils-skiff-shader-bake-20261104`.

- 38,113 evaluated triangles, 20 bones.
- Combined and emission maps: 4096 × 4096.
- Coverage: independent 4096 × 4096 float array; combined output is RGB, so its nonexistent alpha must not be used as coverage.
- Six positive source emission materials were identified, including blue/orange light decals.
- Basic validation: finite geometry; nonempty combined/emission pixels; coverage in [0,1]. This does not establish visual fidelity of projected planes.
- `shader-bake.json` records source hashes, resolved images, repairs, rig and lighting. `bake-checks.json` pins all cache artifacts. Compact data copies are under `bake-data/`; `shader_mesh.npz` embeds original cache texture paths, so rebind those if working from the archived copies.

Inspection runs use separate factory-startup/headless Blender with auto-execution disabled. The first render attempt failed because the source scene selected an animation output format; the script now explicitly requests a PNG image output. Final inspect and bake processes both exited 0 and were observed complete.

## Remaining

Create and inspect the source-derived display candidate using the separate coverage/emission data, preserve its auxiliary rig, validate full native bone matrices before retargeting the two moving original clips, and author/validate flight trajectory separately from those skeletal clips. Then wire the ship through session-owned incoming/spawn callbacks, enforce one non-attacking ship per zone, and validate swept collision/chunk ownership/lifecycle and native visual/audio/performance behavior. No production model was integrated and no new product JAR was built in this step. The full strike goal remains unfinished.
