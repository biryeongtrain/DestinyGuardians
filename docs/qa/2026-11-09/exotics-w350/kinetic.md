# W350 kinetic R2 — source-proportioned native model handoff

R1 rectangular drafts were rejected. This revision replaces all three geometries; original R1 designs, manifests, parts and review PNGs remain in each `rejected-r1` directory, and the original report is retained as `kinetic-r1-rejected.md`. No shared Java, data, sounds, registries, HUD wrapper or other weapon was changed. No game client, server, input lease or Computer Use was operated.

## Source and design

Read-only actual `.blend` evaluations and source side/oblique/top/material evidence are preserved. The generator rechecks the original SHA on each build. Crimson has no armature; Thorn has cylinder/crane/magazine/trigger/hammer bones; Outbreak has magazine/pedestal and unresolved hash bones. All have zero actions and no player wrist/elbow animation. The 61 reload poses are authored approximations; original extracted animation fidelity is not claimed.

The quality reference screenshot and accepted W327 Krait generator, native contour adapter and coplanar optimization strategy were inspected. Geometry is manually authored from source projected proportions as semantic closed solids: physical annular bores, chamfered source-shaped profiles and varying-width lofts. No ripped polygon conversion, voxelization, decimation or body alpha cutout is used. Each planar native surface belongs to a closed solid, including end caps and inner bore walls. Alpha masks trim native rectangle surfaces to their exact authored polygon; they do not substitute for solid thickness.

| Weapon | Closed solids | Native emitted body + moving part | Atlas |
| --- | ---: | ---: | --- |
| Crimson | 29 | 736 | 2048 × 512 |
| Thorn | 32 | 849 | 2048 × 512 |
| Outbreak Perfected | 42 | 775 | 2048 × 512 |

Counts include every emitted native polygon plane. Full and body/moving variants are alternative assemblies, not cumulatively counted. Player forearms are separate W204 assets and not included in these weapon counts; their native performance is not measured.

Crimson retains the sloped rear slide, two real front bores, open cylinder frame, curved inset grip, hollow guard and tapered underbarrel knife. Seven complete actual-source skull motifs are isolated from bracket seams/partial flakes at higher face texel density. Front red/silver marks remain source-derived. Thorn retains the long swept dorsal spines, real lower triangular barrel windows, ribbed gold chamber, varying-width bone grip and fitted closed wrap sections. Outbreak retains short muzzle, paired SIVA diamond chambers, exposed lattice, narrow rail, open grip cage and separate rear magazine.

Flat role palettes use the pinned official Bungie base inventory icons recorded in each manifest. The source Outbreak shader is undyed grey/white; its white circuit motif is recolored to canonical red. Source albedo relief is bounded and quantized; no random wear/noise is generated. Each face has its own atlas region with gutters. The 2K width preserves native first-person motif and panel legibility; actual compressed resource-pack ZIP and client atlas memory remain master's integration checks.

## Binding and proof

Existing root/reload/aim contracts are preserved: `destiny:weapon/<id>`, float index 1 with 61 reload thresholds, float index 3 with 21 aim thresholds, owned `weapon_w350/<id>/hands` leaves and W204 immutable parents. Grip/support/cylinder or magazine anchors are authored against the new geometry and recorded in `rig.json` and `r2-authored-solids.json`. First-person alignment and contact remain pending native review.

`review-r2/native_{side,oblique,opposite_oblique,top,front}.png` renders actual emitted native JSON with its atlas alpha. `source_vs_native_side.png` and `source_vs_native_oblique.png` use matching orthographic framing; `camera-contract-r2.json` records the mapping. `render-evidence-r2.json` binds those images to parts/texture SHA. Offline Blender images are not an in-game framebuffer or pack-load acceptance. HUD PNGs are derived from the actual native side render.

Exclusive transform-hashed hand leaves absent from all current own item graphs are removed; precise removed paths/hashes are in `manifest.json` and the R2 delta. R1 proof remains preserved.

## Verification and remaining acceptance

Performed offline: JSON parse; all model references resolve; native rectangle bounds and UVs; unique surface names; every authored solid edge has exactly two incident faces; original source SHA remains unchanged; 61 pose exact return endpoints; bounded angular increments; manifest output hashes; actual-native side, both obliques, top and front renders. Results are in `validation-r2.json`. No Java behavior was changed or built by this worker.

Reproduction uses a Python environment with Pillow: `kinetic_quality_r2.py [ids]`; owned headless Blender `kinetic_quality_render.py -- <id>`; Python `kinetic_quality_proof.py [ids]`; `kinetic_quality_finalize.py [ids]`; `kinetic_quality_check.py [ids]`. The Blender bundle lacks Pillow, so composition/HUD proof runs in the separate Python environment.

Pending: real pack load, hip/ADS grip, occlusion, third person, moving-part/hand reload contact and restoration, 10–20 display behavior/FPS. Master first Vision → delegated review/fixes → master second Vision remains required. This is an offline integration candidate, not final visual or performance acceptance.
