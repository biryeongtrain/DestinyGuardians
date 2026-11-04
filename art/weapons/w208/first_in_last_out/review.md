# W208 First In, Last Out

Authored first-person framing and skin-arm contact candidate, plus a continuous
one-shell reload bank. Native review is pending master integration.

## Inputs inspected and calibration limits

Read main AGENTS.md, RTK.md, minecraft-weapon-art-design/SKILL.md and its
Ace/Izanagi study. The latter guides preserving meaningful volumes and face UV;
this task retains the current surface rather than redesigning it.

Inspected the effective W123 surface mapping, W133 design/manifest, W201
contacts, W178 generator and motion-reference metadata, W207 Ammit PCHIP and
Dust lifecycle generator, W205 framing/hand/rig code and shotgun rig metadata.
Viewed actual art PNGs: W123 comparison, W178 reference-01 (26.4s hip) and
reference-06 (27.6667s held insertion). These show the teal-white SUROS shroud,
silver sleeve, dark fore-end and underside handling; the hand obscures the
cartridge. No CU, Vision, Blender or shared QA was used.

Exact counts: current canonical body 97 opaque elements / 582 UV faces;
unchanged W178 shell 12 elements / 72 UV faces; maximum assembly 109 weapon
elements, below the 1,000 limit. W133 source metadata records 8,040 source
triangles, 8,038 textured triangles and an earlier 226-cuboid representation;
those are source/history counts, not this emitted surface. No new texture.
W178 records 12 actual frames (1 identity, 11 reload/interrupt); two gameplay
PNGs were viewed this run. Source return is interrupted to fire, so the cosmetic
return remains authored rather than an exact recovered full-mag return.

Non-fallback shotgun_2eb0529e explicitly binds this weapon. Idle 80A8A3C2 and
ADS 80A8A3C5 each have one evaluated sample; generic full/empty reload 80A8A3F1
has 21 evaluated samples over source frames 1..101. cameraExported=false.
This supports source arm direction/ordinary length, not exact source camera,
FOV, per-shell event timing or finger IK.

Profile framing: translation [-0.75,0.55,0.50], rotation [-1.25,2,0], scale 0.98,
sourceViewRotation [0,0,0], keepMeshSupport=true, support visible at rest.
Relative to W205 shotgun defaults this changes translation by [-0.10,-0.05,+0.50]
and pitch by -0.25 degrees. It is a modest calibration candidate; W206's larger
camera-ward displacement was not copied without current native evidence.
The shared hip transform must move weapon and both contact frames together and
fade to identity at full ADS. No cameraDepth or forearm extension is added.

Inherit right [8,8.82,8.55] at grip_core and left [7.8,9.2,-2.5] beneath
foreend_belly. Only reload is overridden: contact [8,9.96,4.65], partHint shell,
policy shell, rigAction 80A8A3F1. This replaces the static loading-port estimate
with the actual moving shell anchor. Mandatory keepMeshSupport retains these
mesh contacts instead of substituting source wrist separation. Arm geometry and
ordinary source forearm lengths remain master-owned and unchanged.

## Motion and output contract

Self-contained stdlib generator; import and generate(root=ROOT) return absolute
Path -> bytes without writes. Only new models/items under
weapon_insert_w208_first_in_last_out/ and the owned W208 manifest are returned.
Master writes the pack; this worker materializes only its manifest artifact.

Required item model: destiny:weapon_insert_w208_first_in_last_out/first_in_last_out.
Required parts: body, shell. 61 poses / 60 intervals for each of initial, loop,
return; 183 CMD4 entries, flag0 native/twohand grip. Runtime thresholds use
float32(phase*2 + float32(frame/60)), matching Java's division then addition.
Initial 0..1, loop 2..3, return 4..5. Existing collision offset policy stays with
runtime. Gameplay durations, transfer/ammo, audio and six-tick cosmetic return
are unchanged. 61 poses reduce bank quantization; server pacing is still up to
20Hz and this is not a 60fps verification.

W207 Ammit weighted harmonic PCHIP replaces per-segment stop/start smoothstep.
W178 visible times, all body knot values, .30..58 initial held plateau and shell
visibility windows [.40,.87) initial / [.15,.80) loop are retained. Curves have
zero endpoint/hold/extremum velocities and shared nonzero tangents across
monotone moving knots. Rigid source grip pivot and native->twohand carrier
composition retain the authored W178 display-space shift convention.

Shell parents use full-size geometry when visible and elements=[] when hidden,
with ordinary display scale throughout. The invisible shell holds at seat until
.90 initial/.85 loop, then recycles to the pickup anchor by phase end, with zero
boundary velocity. This removes the old hidden contact jump. Body AND shell
displays coincide across initial1=loop0=loop1=return0. Return shell remains
hidden; shared lifecycle blends its hand back to the fore-end. Body endpoints
restore both accepted grip displays exactly. All non-first-person and ADS/
inspect item fallbacks are exact current canonical graphs.

Output count: 737 returned entries = 736 pack JSON assets (3 parents including
empty shell, 732 display children, 1 item) + 1 owned manifest. Generated pack
assets are never written into the worker checkout.

## Targeted validation

Draft fixture: `rtk proxy python3 -B scripts/qa/test_motion_w208_first_in_last_out.py`
from /private/tmp/w208-first_in_last_out-draft: 10 tests passed (0.269s), with
read-only symlinks to canonical inputs. Final isolated checkout: the same command passed all 10 tests in 0.274s.
Private .git pointer resolved to
/Users/qf/IdeaProjects/DestinyGuardians/.git/worktrees/w208-first_in_last_out;
worktree-batch.json status ready was confirmed before any checkout edits.
Baseline: 88016d66f31edad0791e20b7689f14adeccecc4063b67c39a2e8af2622fc7577.

Checks cover exact body/shell geometry and UV; both grips' idle restoration;
held body/shell seams and hidden geometry; all 183 float32 thresholds and their
previous representable values; complete namespaced graph references and exact
fallbacks; finite monotone bounded PCHIP channels, moving-knot derivative
continuity, zero endpoints and meaningful holds; moving contact displacement
against independent point rotation; profile/rig contract and output digests;
invalid progress rejection; audited write-free import/generate and determinism.

## Master integration and native scenes

Master must load W208 profile, route this model and 60 intervals in
WeaponInsertPresentation, extend rig action whitelist for first_in_last_out
80A8A3F1, and apply initial/loop/return CMD4 handling to skin-arm sampling and
reach/follow/release contact blends. Match partHint shell, retain hidden shell's
normal scale and apply shared framing once. Common pipeline/runtime untouched.

Pending one master Vision session: classic/slim skin; right/left FP hands and
native/twohand grips; hip, hip->ADS->hip and inspect; initial empty/partial reload,
multiple successful held shell inserts, shell occlusion/hand contact, cosmetic
return, fire interruption, cancel, swap, death/disconnect restoration and float4
collision ownership. Observe unchanged third-person/GUI/ground/head/fixed
fallback and briefly 10-20 displayed weapons for obvious defects. Actual ammo
transfer, timing and sound listening are master checks. This worker claims no
native visual/gameplay or performance verification.
