# W179 Null Composure reload presentation

Canonical identity: long silver vaulted shroud, blue forward capacitor and breech,
restrained gold crest, open reflex hood and lower grip frame. The W144 accepted
91-solid model is retained exactly, with its face UVs and original texture reference.
No texture or canonical model/display/ADS/audio/data endpoints are edited.

## Actual same-weapon footage inspected

Datto, [Destiny 2: Null Composure is LITERALLY A Fusion Rifle (Season 14 Pursuit Weapon)](https://www.youtube.com/watch?v=FdLSPBirfps), published 2021-05-18.
Decoded actual 1280x720, 60fps gameplay pixels, not a thumbnail or a different fusion.
20.00s / frame1200 has the readable NULL COMPOSURE nameplate and default silver,
blue and gold silhouette. Gameplay at 136.8-138.8s retains the same shroud/crest,
blue breech and optic. The source also includes Loaded Question and Plug One;
those portions were not used as reload evidence.

Observed sequence in source-relative seconds:

- 136.80: hip before reload; 137.00: beginning to raise.
- 137.20: muzzle steeply upright at the right; support hand reaches lower battery face.
- 137.40, 137.60, 137.80: upright receiver hold/turn; perforated battery face remains
  visible, support hand offscreen. These frames do not establish an exact cell trajectory.
- 138.00: support hand returns to lower battery; source counter changes 4 to 7.
- 138.20: support hand leaves lower battery area.
- 138.40: support hand sweeps across upper receiver/optic.
- 138.60: hand withdraws and receiver lowers; 138.80: hip silhouette recovered.

Frame indexing uses decoded n/60 relative to the first video frame. MPEG-TS first
PTS is .016667; these are video-relative times, not absolute transport timestamps.
Reference frames 01-12 and decode log/index are retained outside the product at
`/private/tmp/w179-null-composure-report`. Storyboard embeds all twelve original
frame views above nearest authored poses; originals remain full resolution there.

## Authored interpretation

This is a rapid-fire fusion energy-cell presentation. A steep upward presentation
and positive roll expose the lower battery, with a compact withdrawal/clearance,
replacement approach and reseat. A small receiver rock accompanies the observed
upper-hand sweep before the authored exact canonical hip recovery. The sweep
has no hand mesh, hand IK, bolt or extra top component.

The hidden cell stroke, exact angles, phase normalization and grip pivot are
hand-authored, not extracted bones or measured motion. Since the housing remains
visible, the stroke is deliberately modest (3.2 model units down, .4 forward,
.3 lateral at maximum), with no full distant-magazine throw, scale hiding or spin.
The three existing battery solids (Battery_keel_solid, Battery_blue_spine,
Battery_heel) form the moving part; forward diagonal web, upper fill, lower frame
brace, blue front capacitor and sight remain fixed to the receiver. This semantic
split is authored; the canonical source has no recovered animation rig.

W178 is a reference for rigid Rx/Ry/Rz composition and item graph conventions only.
Null Composure has independent keys, grip pivot, battery topology, stroke and
upper-sweep phase. Its upward presentation is supported by its own footage.

All 91 canonical output cubes occur once: 88 receiver + 3 battery, zero triangle
adapter elements, zero additions; assembled total 91 <= 1000. Parents retain all
canonical geometry/UV/texture/metadata. 84 children are display-only (21 samples x
2 parts x 2 grips). At both endpoints the exact canonical grip displays return for
both FP contexts. Both grips use constant scale and rigid carrier compensation.

Item graph `destiny:weapon_reload_w179_null_composure/null_composure`: float1
progress, flag0 twohand. Only firstperson_righthand/firstperson_lefthand can select
reload. Canonical ADS/inspect branches precede progress. Negative inactive and all
nonFP contexts use exact canonical graph. Master owns admission, routing, registry,
clock, ammo and lifecycle tests. No route assertion belongs to this asset worker.
Existing six rounds, 41 reload ticks, 533ms charge, nine bolts and cadence stay
unchanged. Source counter/perks do not determine local mechanics or timing.

## Offline validation and native handoff

Dedicated Python tests cover meaningful asset behavior, phase order, connectivity,
canonical preservation, deterministic outputs, provenance and graph fallbacks.
Standalone JDK25 tests use actual cached Minecraft 26.3 CuboidModel parser,
ItemModels codec and representative ItemTransform/JOML points including left-hand
mirror and twohand carrier; no full Gradle gate or game runtime is needed.
Comparison uses three obliques with common framing and separate battery closeups.
Images are offline orthographic renders without hands, not native screenshots.

Native remains unverified. Master should check both FP contexts/both grips through
upright presentation, battery clearance/reseat, upper-sweep rock and hip return;
ADS/inspect precedence and nonFP fallback; interruption/completion/swap/equip/death/
disconnect recovery; unchanged sound, and briefly 10-20 displays. No new third-person
reload, native success, listening, performance or hand IK claim is made.

## Reproduction and retained failures

Use Pillow/NumPy Python and existing helper `generate_surface_w123_hammerhead.py`.
Generator requires external reference frames/video/metadata at `--reference-dir`
(default `/private/tmp/w179-null-composure-report`); SOURCE and manifest preserve
source details, and no new evidence-file paths are added to the exclusive scope.

```
rtk proxy env PYTHONDONTWRITEBYTECODE=1 /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/generate_reload_w179_null_composure.py --verify
rtk proxy env PYTHONDONTWRITEBYTECODE=1 /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/qa/test_reload_w179_null_composure.py
rtk proxy python3 /private/tmp/w179-null-composure-report/run-java.py
```

Reference download format18 unavailable (`download.log`); direct298 stopped with
HTTP403 (`download-298.log`, partial retained); HLS311 succeeded (`download-311.log`).
An unquoted URL format-list invocation failed in zsh; the quoted subprocess retry
succeeded (`formats.log`). Runtime Python lacked imageio_ffmpeg; read-only tools
in `/private/tmp/w172-video-tools` supplied the decoder/downloader. Initial scout
seeks on partial HLS emitted missing-reference warnings; final selected source
frames were sequentially decoded from the complete video (`decode-reference.log`).
No shared DCC, CU/Vision, game process or dependency build was used.

## Original reference frame hashes

| Relative seconds | Decoded frame n | PNG SHA256 |
|---|---|---|
| 20.00 | 1200 | `d2e81c00f6f902eb500369560ab6ff3dba0d7c8cc0347a55eb666a82242542c3` |
| 136.80 | 8208 | `f92d50e4ee19508de98b130c53c80b510569d51baeb4a5f1889f697994201039` |
| 137.00 | 8220 | `0b47366cb8d00a3101b525addbed0581bed5ab2501da619d89c76025c020cdcf` |
| 137.20 | 8232 | `e90a841b4cb22a53dba749ffc663c539f04b0d4de2a0f98ba79d135dbae3a7da` |
| 137.40 | 8244 | `e042a915c6e293928bcff35efe0a37561408ddd8441e678be66e93afe6e8925e` |
| 137.60 | 8256 | `da73f3663ad03589a72fb5a170f9488cd4afb44ca64fb2a7951404fbedb637c1` |
| 137.80 | 8268 | `04a416d1df9f5062e9ada041b85fe932a47c2bf2a8d56b86cc76abe3ab8155e0` |
| 138.00 | 8280 | `17c07a2ddaafd8bf77182e3379ccdef7768e2a491d4e5d689c6a346578a3d7d3` |
| 138.20 | 8292 | `f16d610cf0b6ba3408dc17a9ce3741c76f0db4e6aabf4a67109ab450f087fe22` |
| 138.40 | 8304 | `b9e4e82dab57076581b141ab9bd74a0ed50dc10fc0a537fc96e3bbc8c6ff2c6f` |
| 138.60 | 8316 | `1d3fff9a238feed8dd801841327d258683250f20bcf93bfcf14d7abc25180dd0` |
| 138.80 | 8328 | `c56ba9cb9efa5c697a32307fdef4f246b4c6fe62e768de9dc01aa7c14ec3ea05` |

null-composure-hls.mp4: SHA256 `38898aa7543c163cebf92dc0986a5bbf31f1a6066765c9d4a38f1a39b7ee19cf`.

null-composure-hls.info.json: SHA256 `3addf5b8d36b499192e47011f7d4d2a8e4e6c4be1b230d806a3f9898a7102149`.
