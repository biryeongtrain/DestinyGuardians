# W222 Biting Winds — FIRST reviewed, no product change; SECOND pending

Owned delta only, in retained slot1 `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-ikelos_sg_v1_0_1`:

- `scripts/generate_reload_w222_biting_winds.py`
- `art/weapons/w222/biting_winds/profile.json`
- `art/weapons/w222/biting_winds/review.md`

Read AGENTS.md, RTK.md, minecraft-weapon-art-design and its Ace/Izanagi study, the three reference generators, and W222 source-review/source-handling-evidence/selection. Viewed `docs/qa/2026-10-28/w222/source-sheets/bow_6239be39-80A8A207-upper-chain.png` read-only from main (sheet absent in retained slot). Master evaluated the original `.blend` with Blender5.4 Alpha; this worker did not independently run Blender. Report: ARMATURE only, no mesh/camera/finger IK, inputs unchanged, previous sampled joint error0.

Source: `bow_6239be39`, `Armature|fp_80A8A207_reload_full|Base`, OBSlot, frames1..29,61 evaluated samples with both shoulder/elbow/wrist chains and weapon. Cache SHA256 `cd8782f018f3a4c422c95be447f8ade8f34f45250b6ce93dab1295cdb9f3c623`; original blend/map/bone-map hashes and paths are in profile.sourceRig. Shared action also binds Whispering Slab; weapon-exclusive selector recovery is not claimed.

Actual hand evidence: maximum weapon-relative wrist excursion RIGHT0.9233936977935914 versus LEFT0.004347778639555654 (source units). RIGHT nocks; LEFT supports riser. Entire action is nocking, not drawing. Profile retains existing right/left/reload contacts; reload explicitly `hand:right`, `policy:bow`, `partHint:moving`, `rigAction:80A8A207`. No generic left-hand handling blend or recovered arrow event is added.

Strategy:61 neutral body-carrier poses/60 intervals, exact float32(i/60) on CMD1, native/twohand variants with both FP contexts. One complete126-element semantic resting model includes the existing23 arrow/string elements; geometry, face UVs, textures and accepted display transforms are unchanged. No extra arrow, independent string motion, scale hiding or arm stretch. Master replays the source weapon/full arm chains once. Existing bow framing is merged, retaining translation[-5.5,-.2,0], rotation[0,0,0], scale.94 and existing cameraDepth11; sourceViewRotation becomes[0,0,0] as required, sourceWeaponMotion/fullChain/keepMeshSupport=true, hideSupportAtRest=false. No new camera fitting or damping.

Return only:125 absolute Path→bytes entries:1 geometry parent +122 display children +1 item graph +1 manifest.124 pack files; no outputs materialized. Complete canonical graph at endpoints0/1, negative fallback, overshoot and nonFP; ADS/inspect resolve through the entire original graph. Existing W50 draw route remains master-owned and unmodified. Master must retain W50 RIGHT string displacement and the lowered LEFT riser anchor after source_palm_translations; do not route draw through this nock bank.

Budget: candidate126 weapon +448 reserved for four ordinary skin-arm surfaces =574/1000. Raw canonical fallback250+448=698; raw W50 body229 + one maximum moving state23 +448=700/1000 conservative maximum. These are alternative representations, not summed together. No triangle adapter/new geometry. Final integrated arm counts remain master's measurement.

Small read-only stdlib validation passed using Python-B/runpy with an audit hook denying writes/mkdir/remove/rename/subprocess throughout import and generate. Checked deterministic default/relative-rig/absolute-profile calls,125 exact owned output paths, JSON parsing,61 ordered float32 thresholds and exact boundary selection, canonical guards/endpoints/fallback/nonFP, both grip leaves, exact parent elements/UVs and accepted displays for every sample, budget and all input/output hashes. Initial check exposed absent Biting Winds entry in W63 reload audio; fixed snapshot lookup to return null, rerun passed. No audio routing or assets changed. No big tests, builds, materialization, CU/Vision, numeric perk tests, commits or shared-file edits.

## FIRST same-worker feedback — 2026-10-28

Decision: **no generator/profile correction**. Reviewed the actual FIRST framebuffer sheets and source evidence read-only from `/Users/qf/IdeaProjects/DestinyGuardians/docs/qa/2026-10-28/w222`. No bounded defect justifies altering accepted camera/framing, ordinary arms, or geometry. Only this review changes in this feedback stage; the original preparation notes above remain historical.

- Nock: `vision1/screenshots/biting_winds-review.png` and `biting_winds-reload.png` show the lowered LEFT riser support, RIGHT handling/nock movement and return of the bow. The earliest sampled pose dips below the lower edge; subsequent samples02/03/04/06 raise and recover it. This sampled crop is not evidence of arm hiding or a reason to replace the original motion. Rechecked the source shoulder sheet and handling evidence: action80A8A207 remains RIGHT nock, LEFT support (excursions0.92339/0.00435). No arrow event is recoverable from the armature-only source.
- ADS: inspected full-resolution `vision1/frames/w222-biting_winds-ads-sample-09.png`. Yellow aiming pin, central aperture and background through it remain visible. The ordinary forearm crowds/meets the lower-right aperture edge and covers much of the lower frame; this is a visible limitation, not a claim of unobstructed clearance everywhere. No sampled center-pin blockage establishes a correction within this nock generator/profile. Keep calibrated framing and ordinary source arms; no camera shift, geometry edit, arm shrink/hide or damping to improve the crop.
- Separate W50 draw: inspected fire samples00/03/10/13. Between03 (client ticks553..554) and10 (570), the riser remains in place while string/arrow retreat toward/beyond the right edge;13 (577..578) retains the drawn state. Thus W50 travel has not been erased in these samples. The right hand/string contact near or beyond the edge cannot be certified pixel-by-pixel from this view. Sequence metadata keeps the W50 item route through these draw samples; the nock route is distinct. Master's bow-contact test reports retained RIGHT W50 displacement and lowered LEFT anchor in both FP contexts, with the after-profile source tests passing.
- Return: inspected `first-post-reload-review.png` and the full-resolution Biting Winds after-reload frame. Bow, resting arrow/string and support hand return to ready, HUD arrow count1. The after-reload frame metadata (client ticks724..725) uses the W50 hands route; reload-finished oracle reports `reloading=false`, `handling=NONE`, native grip and ammo1/0. No residual reload pose is evident in this sampled return.

Read master's recorded results, without rerunning: native-validation13 sequences, including Biting Winds16 fire/42 reload/19 ADS captures with inputs released; source-binding tests2/0 failures; JUnit16/0 failures; assembled budget Biting Winds700/1000 including arms. Manual review here covers the named frames/sheets, not every captured frame or all61 poses.

Evidence SHA256 (paths relative to the QA root above):

| File | SHA256 |
| --- | --- |
| `vision1/screenshots/biting_winds-review.png` | `76eb650ce62c565766c3b0228e4584313e0ef773f7bfc8f057ebfd6bb5ec8d7a` |
| `vision1/screenshots/biting_winds-reload.png` | `f2937aaebe88c20749697e9c105bd8476d29c26cf8ddeadc8e7d4bae40d42605` |
| `first-post-reload-review.png` | `bd383bf0e1e4b59b2912dbfee4d890b2fb5aa9a8f94e48e16e735d36c355d2f3` |
| `vision1/frames/w222-biting_winds-ads-sample-09.png` | `c4a8675689abb2e7c2e57cabba15643c5ed7aa6d43d624ff970c876ed897ce53` |
| `vision1/frames/w222-biting_winds-fire-sample-03.png` | `bc1ee073011ea60e01226e86d521b6698bd5bc93e9685348484400ee805d13c8` |
| `vision1/frames/w222-biting_winds-fire-sample-10.png` | `c98549e7925a549ffd8aef7031e736347cafabc6296eec2766417b5bac617833` |
| `vision1/frames/w222-biting_winds-after-reload.png` | `54068861433f709039bb2a344b707db97ba9e6b5e2e1b6d1df6b1535a1ff6b00` |

Unchanged owned product SHA256: generator `83de9ab2693f5b7d474e87b2aad1c3dca35932660a649a73ca9cb710f46755c1`; profile `ca26859e6bbad2ef9cc83e79b5ffbe9151a8ed8edef7fad0c367e982fe2379f7`. Profile preparation-time pending flags are untouched to avoid product/provenance churn; this review records the completed FIRST feedback stage.

Remaining: master integrates this no-change finding and performs SECOND Vision before final acceptance. This review does not establish both-grip/left-handed native visual parity, all transitions or all-pose contact, audio listening, performance, or continuous60fps interpolation. Source has no weapon mesh/camera/finger IK. No runtime/materialization/build/CU/Vision/Git mutation was performed by this worker during feedback. Worker remains available for SECOND findings.
