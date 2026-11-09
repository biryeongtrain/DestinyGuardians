# W327 group 1 — implementation handoff, native acceptance pending

12 authored weapon models, material revision 2. Subjunctive was substantially redesigned after user rejection of its v1 silhouette. All 12 now use material-specific static RGBA finish cues, with selected official icon dye and variant authority; see MATERIAL_REVIEW.md per weapon and six source_v1_v2 comparison boards. No central registry, gameplay, build, or client changes. Worktree: `/Users/qf/.codex/worktrees/legendary-models-rifles/DestinyGuardians`.

| ID | body | moving | total | atlas |
|---|---:|---:|---:|---|
| krait | 136 | 4 | 140 | 512 x 512 |
| rufuss_fury | 107 | 9 | 116 | 512 x 512 |
| origin_story | 88 | 9 | 97 | 512 x 256 |
| age_old_bond | 82 | 9 | 91 | 512 x 512 |
| insidious | 95 | 9 | 104 | 512 x 512 |
| phyllotactic_spiral | 91 | 9 | 100 | 512 x 512 |
| igneous_hammer | 87 | 15 | 102 | 512 x 256 |
| eyasluna | 84 | 15 | 99 | 512 x 256 |
| nation_of_beasts | 81 | 15 | 96 | 512 x 256 |
| subjunctive | 134 | 9 | 143 | 512 x 512 |
| submission | 100 | 9 | 109 | 512 x 512 |
| hung_jury_sr4 | 95 | 9 | 104 | 512 x 512 |

All 12: JSON parsed, six normalized face UVs in 0..16, native coordinate limits, element budget, matching atlas/HUD hashes, conservative ADS base-height checks pass, exposed same-facing coplanar overlap count zero. Actual original .blend hashes unchanged. Five offline model views and three actual source views accompany each design.

Runtime files total 874999 bytes; isolated DEFLATE ZIP 368365 bytes. This is not the complete deployment pack measurement, which remains master responsibility.

Motion is existing base 61-pose transport, not extracted source reload. All 12 source files have no animation actions and no player hand rig. Krait keeps the actual side-loading moving bar instead of an invented hanging magazine. Hung Jury retains its forward fluid magazine; Subjunctive retains a long grip magazine. These especially need native hand/contact review because base motions are reused approximately. `contract.json` records rotated base moving bounds, new moving bounds, source bones, and explicit contact limits.

V1 was rejected for flat or incorrect materials. V2 replaces universal flat/grey surfaces with separate exposed alloy sheen, matte coated metal, rubber/cloth, organic/ceramic shell, foliage and luminous cell cues. Official selected finishes correct pale-blue Rufus, purple/teal Phyllotactic and teal/gold Hung Jury; source raw dye discrepancies are recorded. Subjunctive v2 has dense Vex chambers, a compact magazine, a stepped circular cell and irregular warm olive leaf clusters over cool aged alloy. First v2 native acceptance is still pending. No in-game acceptance, native input, actual FPS, client pack-load, or 10–20 weapon validation is claimed. Master first Vision feedback is still required; worker is available for revisions and second review.

Reproduce using Pillow Python: `scripts/art/w327/group1.py evaluate ID` (read-only Blender, autoexec disabled, sources/caches in /tmp), then `build ID`, `render ID`, `check ID`. Registry input remains the provided final-registry.json. Source controls are embedded in the exclusive wrapper; shared W325 kit is unchanged.
