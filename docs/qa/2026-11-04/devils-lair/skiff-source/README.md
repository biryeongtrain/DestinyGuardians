# Original skiff FBX, materials and motion inspection

Executed in separately owned headless Blender 5.4 alpha processes using factory-startup. No user Blender scene or Downloads source was saved or modified. Scripts: `scripts/strikes/audit_skiff_sources.py` and `preview_skiff_sources.py`. `inputs.json` pins source FBX, DDS, material slots and motion metadata. These are source investigations, not a runtime model integration or Minecraft verification.

## Geometry and material evidence

Both original variants (`80C3EE92`, `80CC0740`) import as 42 meshes, 40,818 triangles, and one 10-bone armature. Model FBX files have no actions; separate motion FBX files exist. Model/motion bone-name sets match. Every provided DDS decoded successfully. Imported model materials have no connected image nodes, so directly baking the imported material would reproduce default gray rather than the original shader.

The initial `*-albedo-diagnostic.png` connects the explicitly recorded sRGB slot (prefer slot 0) to a simple Principled base color. It is **not** a reconstruction of dye constants, alpha, normal maps or emission. Unresolved materials are deliberately magenta. Inspection revealed a white outer surface hiding the detailed hull.

`*-excluded-surface-diagnostic.png` is a controlled comparison excluding only the `_Index9_3_` mesh (recorded by exact names in the corresponding materials JSON). The underlying hull becomes visible. This diagnoses an opaque effect-surface problem; it does not establish that this mesh should be permanently deleted. Rear effect cards, unresolved colored bands and component attachment positions still need shader/rig review. No gray, magenta, or noise-card preview has been adopted as a final asset. The intermediate excluded-surface image was shown to the user.

## Motion evidence

Six named source actions import at 30 FPS. Both variants produce the same observed pattern:

| Source clip | Manifest frames | Imported keyed range | Observed change |
|---|---:|---:|---|
| 80A8A4E2 | 2 | 1 frame | constant |
| 80A8A51D | 81 | 1 frame | constant |
| 80A8A51E | 81 | 81 frames | quaternion animation on two bones |
| 80A8A51F | 114 | 1 frame | constant |
| 80A8A520 | 121 | 121 frames | quaternion animation on two bones |
| 80A8A521 | 114 | 1 frame | constant |

There is no observed bone-head translation through these sampled clips; the two moving clips rotate bones `828A3F9F` and `F446DA9F`. Do not label these six actions as extracted flight trajectories. Source slot labels include movement/doors but do not by themselves identify runtime arrive/drop/depart semantics.

`*-motion.npz` preserves all imported sampled bone-world matrices plus rest matrices and metadata. `*-motion.json` records action ranges, manifest discrepancies, every F-curve's value range and maximum matrix change. Initial extraction failed when it assumed the manifest frame count equaled the imported keyed range. That failure is retained in logs. The final audit records the discrepancy without fabricating missing frames or claiming the clips are complete. Use `--python-exit-code 1`: Blender otherwise returned exit 0 despite the Python exception.

## Next work

Resolve the actual exterior/dye/effect material roles and child attachment transforms, then bake source-derived display geometry with a 10-bone-compatible rig and compare it against source views. Keep the original constant-duration metadata if creating hold clips; distinguish holds and authored flight movement from source-extracted skeletal animation. Original ship dimensions differ materially from the small authored `rg_skiff`, so its earlier route envelope is not acceptance evidence for this asset. Integrate one non-attacking ship per zone through the newly added presentation callbacks, validate the real swept volume and chunk ownership, then conduct native framebuffer/audio/performance QA.

No product Java/resource changes or new JAR in this investigation. Latest product remains the spawn-presentation build; full test failures and native acceptance remain unresolved.
