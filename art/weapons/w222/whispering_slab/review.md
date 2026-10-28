# W222 Whispering Slab — FIRST reviewed; SECOND pending

Owned delta only: `scripts/generate_reload_w222_whispering_slab.py`,
`art/weapons/w222/whispering_slab/profile.json`, and this review. Retained slot2;
no shared files, rig, generated output, build, game input or commit changed.

Source: master read-only Blender5.4 Alpha evaluation of original
`bow_6239be39/source.blend`, action `80A8A207`
(`Armature|fp_80A8A207_reload_full|Base`, OBSlot), frames1..29,61 samples.
Read `source-review.json`, `source-handling-evidence.json`, `selection.json`;
viewed the actual `bow_6239be39-80A8A207-upper-chain.png` from main read-only
(sheet absent in retained worktree). Report says original inputs unchanged and
prior-cache joint error0. Worker did not independently evaluate Blender.
Profile records original Blend/map/bone-map SHA and fresh cache SHA
`cd8782f018f3a4c422c95be447f8ade8f34f45250b6ce93dab1295cdb9f3c623`.
Applied weapon-art skill and Ace/Izanagi reference; no geometry redesign.

Whole action is **RIGHT-hand nock**; LEFT supports its offset riser, X6.38.
Weapon-relative wrist excursions: right0.923394, left0.004348. Preserve both
calibrated rest contacts and existing nocking contact; reload hand:right,
policy:bow, partHint:body. Entire96-element current rest surface, all UVs,
arrow/string and accepted native/twohand displays remain exact.61 neutral body
carriers per grip let master replay original weapon and both complete
shoulder/elbow/wrist chains once. No source motion is baked into these displays.

Framing merges current bow family/weapon settings, preserving translation
[-5.5,-.2,0], scale.94, rotation[0,0,0], existing cameraDepth11, palm/support
lowering and wrist calibration. Required sourceViewRotation[0,0,0],
sourceWeaponMotion:true, sourceFullChain:true, keepMeshSupport:true,
hideSupportAtRest:false are explicit. No new camera adjustment, damping,
arm stretching or hiding. Ordinary four skin-arm surfaces reserve448.

Scope limits: source is ARMATURE only, no source weapon/arrow mesh, camera,
arrow bone events or recovered finger IK. No invented recovered arrow event
or source draw. Rest arrow/string stay with body. Master retains W50 draw hand
displacement, draw/string/arrow routing and lowered LEFT riser anchor. Shared
bow action does not prove a weapon-exclusive selector. Timing, audio, ammo and
inputs are untouched.61 discrete poses do not establish continuous native60fps.

Read-only stdlib validation passed under a Python audit hook rejecting writes,
mkdir, rename/remove and subprocess launch, covering import and generation.
Zero mutation/process attempts. Default and relative-rig/absolute-profile
override calls return identical bytes. Parsed every returned JSON; checked
exact125 allowed absolute paths, whole source geometry/UV equality, all122
neutral display children, all61 float32(i/60) thresholds and exact selection at
each knot. Canonical graph endpoints0/1, negative/overshoot fallback, nonFP,
original ADS/inspect cases and native/twohand branches passed. No files were
materialized; no build, large suite or numeric-perk tests run.

Output:125 returned files =1 geometry parent +122 display children +1 item
graph +1 manifest (124 pack files). Simultaneous reload96+448=544; larger raw
canonical alternative200+448=648, below1000; alternatives are not summed.
Actual assembled ordinary-arm/all-route count remains master's measurement.

## FIRST same-worker feedback — justified no product change

2026-10-28: inspected actual framebuffer sheets in main QA read-only:
`vision1/screenshots/whispering_slab-review.png`,
`vision1/screenshots/whispering_slab-reload.png`, and
`first-post-reload-review.png` (Whispering Slab panel). Also inspected original
full-size reload captures02,04,39 and ADS08 under `vision1/frames/`, and revisited
the original source-chain sheet plus source review/handling/selection evidence.

Reload sheet samples01..05 show upright entry, nock tilt/turn and recovery.
The visible hand/support junction stays against the lower offset riser through
the sampled tilt and return; no obvious floating support gap, detached arm
surface or collapsed/stretched segment is exposed in these views. Overlapping
hands and the lower framebuffer crop limit independent palm/elbow assessment.
RIGHT-hand nocking and near-fixed LEFT riser ownership are grounded in the
source chain/report, not inferred as recovered arrow events from the image.
The source asymmetry remains right0.923394 versus left0.004348 weapon-relative
wrist excursion, consistent with retaining this nock path and X6.38 contact.

Inherited ADS08 shows the gold sight aperture open above the forearm and to
the right of the bow shaft; the visible arm does not fill the aperture. The
closer ADS hand/shaft overlap alone supplies no source-grounded reason to alter
accepted framing or contact calibration. Postreload sheet and reload39 restore
the upright hip silhouette/contact with HUD ammo1. The finished oracle reports
`reloading=false`, `grip=native`, `model=destiny:weapon_bow_w50/whispering_slab`
and ammo1/0, supporting restoration to the existing W50 route.

Decision: no demonstrated defect in the owned generator/profile; preserve them
byte-for-byte. Do not add camera fitting/damping, move the offset riser palm,
hide/stretch arms, duplicate source motion or invent arrow exchange events.
This feedback pass changes **review.md only**. Unchanged SHA-256:

- `scripts/generate_reload_w222_whispering_slab.py`:
  `ed8c2095c530be4e1f5ef2d88f012324e5848894aad01b6a433df649c1e96ae9`
- `art/weapons/w222/whispering_slab/profile.json`:
  `fc76290cfb6568a55fb128a0a2cee8dafbdd75caad9c6956049626b1799ebb47`

Read master's saved validation, without rerunning build/runtime: native report
records13 sequences, Whispering Slab40 reload captures/17 ADS captures,
released input and finished ammo1/0; source-binding report2 tests/0 failures;
five JUnit XML reports total16 tests/0 failures/0 errors/0 skipped.
`assembled-budgets.json` measures Whispering Slab's actual alternative-route
maximum **651 including arms**, below1000 with349 headroom. This supersedes the
preparation-only648 planning estimate for all-route budgeting; the generator's
96+448=544 reload reserve calculation and125 returned files remain unchanged.

Evidence SHA-256 (paths relative to main `docs/qa/2026-10-28/w222/`):

- `vision1/screenshots/whispering_slab-review.png`:
  `9f4a98236d5858f0a463cb6d182236386b8b83520baa1d8c5c405b68fd703c35`
- `vision1/screenshots/whispering_slab-reload.png`:
  `d54742ed9c5849f98d47fe686913a8dd285e40be202f9961bd0c5c78803b6a9a`
- `first-post-reload-review.png`:
  `bd383bf0e1e4b59b2912dbfee4d890b2fb5aa9a8f94e48e16e735d36c355d2f3`
- `source-sheets/bow_6239be39-80A8A207-upper-chain.png`:
  `0cb2ce9b2ef4b07d3453727fdc155b0571cbbdbb142772ba380d037916591fcd`
- `assembled-budgets.json`:
  `6ef5e798eb42062fe23580e3a5ab6685fa148c3e675d8e5570383ef0efad04d5`

Remaining limits: sampled static views do not certify every intermediate
contact, both full shoulder/elbow chains outside the crop, all grip/context
variants, continuous60fps or audible sync. Source remains armature-only with
no recovered camera, finger IK or arrow event track. FIRST feedback is complete;
master alone owns integration/runtime and SECOND Vision before final acceptance.
No main/shared/generated files, game input, build or Git state changed here.
