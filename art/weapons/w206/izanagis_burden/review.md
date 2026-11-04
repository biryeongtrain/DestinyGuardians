# W206 Izanagi's Burden presentation candidate

This is an authored framing and arm-direction calibration. The dedicated source rig has no exported camera; these values are not a recovered Destiny camera. Native W206 verification remains pending with the master.

All repository-relative evidence paths below refer to the read-only main checkout `/Users/qf/IdeaProjects/DestinyGuardians`; ignored historical QA images may not be copied into this isolated seed.

## Observed issue and references

- `art/weapons/w205/rigs/sniper_rifle_ececad46.json` binds only `izanagis_burden`, `fallback=false`, idle `80A8A138`, ADS `80A8A13F`, `cameraExported=false`. Its source is `/Volumes/qf-ssd/DestinyGuardians-Animation-Return-2026-10-27/destiny-animation-return/clips/sniper_rifle_ececad46/blender/source.blend`, read through the existing JSON only. The wrist/elbow vectors provide ordinary forearm direction, twist and length, not screen projection.
- `scripts/rig_arms_w205.py` copies source wrist separation for non-bow idle/ADS. The source idle left-minus-right wrist displacement after its existing C basis is approximately `[-2.408,-0.758,-11.745]` model units, while the retained W201 model contacts differ by `[-0.2,-0.3,-6.9]`. The two meshes have different grip separation: preserving the remodeled forebody support is necessary to avoid relocating the support palm off its intended pad. These numbers diagnose retargeting, not exact screen placement.
- Actual PNG viewed: `docs/qa/2026-10-27/w197/native/frames/izanagis_burden-two_hand-recovered.png`. This historical gun-only hip view has a long diagonal forebody and receiver low/right. It does not show the current W205 arms and cannot prove their final placement.
- Actual PNG viewed: `docs/qa/2026-10-27/w205/screenshots/w205-izanagi-ads-sample-08.png`. Scope aperture fills the viewport; preserve this distinct full-ADS presentation, not a hip pose extrapolated from it.
- Actual gameplay image viewed: `art/weapons/w84/references/youtube-ov6C5oF7KSc-storyboard-L2-M0-raw.jpg`, [Ultraclocked audiovisual showcase](https://www.youtube.com/watch?v=ov6C5oF7KSc&t=2). Five-by-five 160x90 tiles, nominal two-second sampling, tile 1 about 2 seconds. Ready views show the receiver/scope close in the lower right and support under the long forebody. Reload/raised poses are not idle targets. This small historical storyboard supports broad composition only; no exact FOV, arm endpoint or transform was recovered. Provenance is `art/weapons/w84/references/gameplay-evidence.json`; the showcase also contains slow motion, so it supplies no timing measurement here.
- Read `art/weapons/w201/contacts.json`, `scripts/first_person_framing_w205.py`, `scripts/build_first_person_hands_w201.py`, `scripts/skin_arm_models_w204.py`, `scripts/generate_izanagi_presentation_w91.py` and the weapon-art skill plus `references/ace-izanagi-study.md`.

## Concrete profile and rationale

| Field | W206 value | Reason |
| --- | --- | --- |
| `translation` | `[-0.65,0.6,4.0]` | Retain W205 sniper XY; add +4 model units toward camera to bring weapon and attached palms/ordinary forearms closer as one hip assembly. Uses the existing ADS fade to zero. +4 is an authored first candidate, not measured source depth. |
| `rotation` | `[-1,2,0]` degrees | Retain the small family hip pitch/yaw; avoid changing accepted scope alignment. |
| `scale` | `0.98` | Retain existing uniform family hip scale; do not use arm extension to bridge the view. |
| `sourceViewRotation` | `[18,0,0]` degrees | Direction-only source-basis calibration: positive X turns the wrist approach upward, so the elbow runs farther downward toward the bottom edge. This keeps the original source length and twist; native continuity still needs checking. |
| `keepMeshSupport` | `true` | Keep left palm on the authored long forebody support during idle/ADS; retain source wrist/elbow direction and ordinary length. Requires master's new loader/rig option integration. |
| `hideSupportAtRest` | `false` | A long sniper needs visible forebody support. |
| `contacts` | `{}` | Inherit W201 unchanged: right `[8,7.9,8]` / rotation `[-12,0,0]`; left `[7.8,7.6,1.1]` / `[0,90,-85]`; reload `[7.5,6.85,6.92]` / `[0,0,0]`, `partHint=magazine`, `policy=magazine`. Geometry evidence does not warrant moving those contacts. |

No palm-clearance override is introduced without a native collision observation. No cameraDepth or length/extension key exists in this candidate. The source retains its ordinary wrist/elbow distance (about 8.14 model units under the existing 32x conversion); no extra length is requested. Full ADS weapon calibration is identity by the existing weight/display path. SourceViewRotation calibrates arms only and also applies in ADS: its occlusion consequences remain a native check.

## Retained identity and geometry

The canonical `src/main/resources/assets/destiny/models/item/weapon/izanagis_burden.json` contains **79 cubes**, no added mesh or triangle output. Its 474 explicit face UVs, long silver/blue forebody and decoration, black receiver, separate accent/lens atlases, scope/sight geometry and all 3P display values are untouched. W91 partitions magazine cube 26 and bolt cubes 25/77 from the other 76 body cubes: a split representation still totals 79. Forearm skin elements are shared existing assets, not new weapon geometry.

W91 ordinary clip `80A8A140`, Honed clip `80A8A14D` and existing runtime timing remain. W201's CMD6 mapping is retained: ordinary `0..1`, Honed `2..3`, charged idle `4`. Reload hand target remains attached to the moving magazine during handling and returns to the forebody via the existing blend. No generator, build, app, Vision or server was run by this worker.

## Checks and pending native checklist

Scratch checks completed: strict JSON parsing, supported framing keys and finite numeric triples, evidence path existence, and canonical model inspection (79 cubes / 474 faces with explicit UV) pass. Ready barrier confirmed in the private gitdir (`status=ready`, baseline `fdec8444...`). Inspected rig, contacts, canonical model and generator inputs match the ready dirty seed by SHA256. Historical W197/W205 native PNGs were viewed read-only from main; those ignored QA images are absent from this seed, and their main bytes still match the inspected hashes. Profile parses with only supported framing fields and finite numbers. Only the two allocated W206 files were installed; inspected source files remain byte-identical. No generation/build/native QA was run.

Master consolidated native checks, all pending:

- Hip settled idle in native and two-hand modes: closer gun and continuous classic/slim fingerless player-skin forearms, right grip attached, left palm under long forebody, elbow reaches screen edge/occlusion without extension, no floating block cuffs or new sight obstruction. Compare native PNG to the actual reference; tune +4 depth and +18 direction if necessary.
- Hip-to-ADS-to-hip: smooth existing fade, unchanged full-ADS weapon matrices/aperture/reticle, no hand crossing into the scope, correct left-hand mirroring. Scope image alone cannot verify arm continuity.
- Ordinary CMD6 `0..1` reload: support releases, reaches the moving magazine, follows extraction/reseat, and returns to the same forebody contact without a start/end snap.
- Honed CMD6 `2..3` reload and charged idle `4`: preserve distinct branch and source body/part motion, same magazine handling and recovery, clear scope while charged and firing; no unsupported exclusive bolt motion claim.
- Inspect/3P and audio/combat remain as baseline; master's regeneration/build and native review own final confirmation. This worker has not claimed native success.
