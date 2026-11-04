# W212 Antiope-D — FIRST Vision corrections, SECOND pending

## Source evidence and authorship

The master evaluated the **ORIGINAL** source.blend in a separately owned Blender 5.4.0 Alpha process. This worker read /private/tmp/destiny-w212-source/source-review.json and submachine_gun_cdf8185c.json and viewed the actual sheets/submachine_gun_cdf8185c-80A8A170-upper-chain.png with view_image. This is review of the master's original evaluation, not an independent worker Blender evaluation.

The source contains only Armature: no mesh and no camera. Shared-family action Armature|fp_80A8A170_reload_full|Base uses OBSlot, source aliases reload_full/reload_empty, frames 1..91 at 30 fps. The delivered matrix bank contains 61 uniformly normalized samples. The report states allInputsUnchanged=true and zero maximum error against previous cache samples. Antiope-D and Bug-Out Bag share this action; it is not weapon-exclusive.

Source provenance from the master report:

| Input | SHA-256 |
| --- | --- |
| Original blend | 474d2fb3e1b97e605ed54998e6a08311a0cba7f44e826f0b98f44076302caba6 |
| Source map | ccf84b37d2f0b48a4ffd196ab31e19e48d169ed40363e80215bad6333e57cd34 |
| Bone map | dfb12f16b062776714efec4bda53470ae694c0ec223773e9d3b48c688c522bf9 |
| Previous cache | 3f39125de0d3e6f65cc98932e84dc9c88e3b75fbe5f28eb4a227962b75b89a22 |

The worker independently hashed the delivered report (a30b83e9b4babbfefe70e09ad3be2b36488b945e29b6b865656e2bce45966db5), evaluated bank (d09352a9bd907ed80efdf4a46f4436500c4ed354175538d4fcf7b832bec6043f), and chain sheet (e04731565886e7c6bd52e3c860bfe1de156792f9bd815bb0553597ea334b9164). Original blend/map hashes are reported provenance, not recomputed worker claims.

The actual source XZ/YZ sheet at p=0,.2,.4,.6,.8,1 shows both articulated limbs, a substantial free support-chain excursion through the middle, and return at 1. Row-major column-vector matrices are in armature_object space without matrix_world. Ordinary segment length ranges at the existing 32 model units/source unit are:

| Segment | Minimum | Maximum |
| --- | ---: | ---: |
| Left upper arm | 8.72668724 | 8.72669305 |
| Left forearm | 8.14136224 | 8.14136695 |
| Right upper arm | 8.72656924 | 8.72657412 |
| Right forearm | 8.14135739 | 8.14136582 |

No arm stretching, invented camera, recovered mesh contact, finger IK or original camera silhouette is inferred from these bones.

## Semantic mesh and contacts

Viewed art/weapons/w123/antiope_d/comparison.png: source/default appearance plus semantic side, front and rear obliques. The pale/orange Hakke receiver, angled forward support grip, separate rear firing grip, narrow grip-fed magazine, open guard/stock and iron sights remain accepted geometry.

Read actual full model and design plus art/weapons/w201/contacts.json. The rear grip_core has bounds [7.37,7.32,8.5]..[8.63,11.32,10.48], X rotation -6 degrees. The forward foregrip_body has bounds [7.38,7.21,2.625]..[8.62,10.61,4.275], X rotation -27 degrees. The separate magazine_core spans [7.63,3.63,7.8]..[8.37,8.16,9.55].

Preserve W182's exact semantic partition: 113 fixed body solids plus 5 magazine solids (core, front spine, back spine, floor, pull front), 118 total, 708 explicit face UVs, zero triangle adapters. Every original element and field appears once. Pistol grip and charging handle remain fixed; there is no additional bolt stroke or scattered-round animation.

The part is named magazine, matching existing reload.partHint and policy. Inherit the existing right contact [8,9.3,9.48] / rotation [-6,0,0], left support [8,8.85,3.5] / [-27,0,0], and left reload target [7.5,5.8,8.68] / [0,0,0]. The right stays body-relative; the left follows the magazine only during handling. The initial candidate introduced no right/left numeric overrides; FIRST feedback below changes only the reload handling contact.

Profile schemaVersion 1 sets weapon antiope_d, sourceFullChain=true, keepMeshSupport=true and hideSupportAtRest=false, with reload.rigAction=80A8A170. The initial candidate retained every SMG family framing value, including translation [-.65,.6,0], rotation [-1,2,0], scale .98, rightWristRoll 28, meshArmDirections=true, reloadCameraLower 2.5 and sourceWeaponRelative=true. The existing reloadCameraLower value is inherited presentation, not a recovered source camera.

## Dense generator contract

scripts/generate_reload_w212_antiope_d.py is a pure standard-library port of the necessary W182 algebra/partition. It does not import or execute the historical generator, its PIL/NumPy preview path or its output writer. The original 11 KEYS, GRIP, MAG_ANCHOR and all authored holds are retained. Component-wise weighted harmonic PCHIP tangents replace per-key smoothstop; derivatives are shared at knots and zero at endpoints, extrema and adjacent holds. Holds return exact stored values.

generate(root=ROOT) returns dict[absolute Path, bytes]: 2 partition parents, 244 pose/grip/part children, 1 item wrapper (247 pack assets), plus the returned-only manifest (248 entries total). The namespace is weapon_reload_w212_antiope_d/antiope_d. Nothing writes on import or generate, and no executable writer is supplied. The master owns materialization, including the manifest.

61 range entries use float32(i/60), progressFloatIndex=1 and gripFlagIndex=0. Both part children retain exact accepted displays at 0 and 1 for native/twohand. Endpoints also select the exact accepted item graph. Non-first-person, negative-progress fallback and complete accepted ADS/inspect cases retain the original graph and precedence. Child non-FP displays and all scales remain unchanged.

The returned manifest records semantic partition indices/names/counts, input/output SHA-256, original authored keys/holds, source provenance/action 80A8A170, 61 samples, geometry/UV preservation, unchanged gameplay timing/audio and explicit false native acceptance. Its output hashes cover the 247 pack assets; it does not hash itself. It reads the master's current W205 rig input for provenance but does not materialize or modify that cache.

The weapon carrier is still W182's authored same-weapon gameplay approximation (CammyCakes, https://www.youtube.com/watch?v=M3tC-IkkFRU), including hidden numeric extraction/insertion and one whole magazine proxy. The extracted shared-family chain is separate arm evidence; it does not turn those authored weapon keys into recovered original mesh motion.

## Checks and remaining acceptance

Read-only/in-memory checks:

- Python compilation and standard-library import; no old generator execution.
- All 11 authored keys exact; 1,010 within-segment probes stay inside each scalar endpoint range; holds exact; invalid/nonfinite progress rejected.
- Shared knot tangents are the W208 weighted harmonic formula; endpoints and hold/extremum derivatives zero. A 1e-7 finite-difference probe gives maximum left/right derivative residual 0.001118 (finite-step error, not a tangent discontinuity).
- Repeated generate results byte-identical; all 248 keys are absolute Paths and values bytes.
- 61 distinct float32 thresholds and correct dispatch at every sample; 240 context/mode/progress/grip routing combinations, including ADS/inspect with stale positive progress, inactive fallback and non-FP.
- No sampled Euler branch flip: maximum per-axis adjacent step 9.001132 degrees, minimum |cos(Y)| 0.868977, safely away from Euler singularity.
- All 244 child displays checked for exact endpoints, non-FP preservation and constant accepted scale; exact 113+5 element/UV multiset partition.
- All 247 returned pack hashes and manifest input hashes recomputed.
- Filesystem mutation audit rejects writes/mkdir/remove/rename during import/generate; canonical source/display/item/texture hashes remain unchanged. Initial prospective checks used in-memory substitutions while the seed was incomplete. After private metadata reported ready with baseline fingerprint 5728d043ce9f9a3ed93855debafbff261c2cbf4801bf444a83aae5ec09b0079f, the same generation/dispatch/hash/write-audit checks passed against the actual owned files imported with runpy. Family framing equality and the absence of generated directories/manifest were also verified. Only these three new owned files were written.

Only the three assigned new files are owned. No generated asset or manifest is written, no full pipeline/Gradle/native input is run, and no commit/stash/reset/push is performed.

**FIRST Vision screenshots have now been received and inspected.** The correction and remaining SECOND requirements are recorded below. The master owns W212 loading, runtime/rig cache/hands generation, regression checks and SECOND Vision before final native acceptance.


## FIRST Vision feedback and scoped correction

Inspected actual /private/tmp/destiny-w212-pass1-native/screenshots/antiope_d-reload.png, completed antiope_d-review.png, raw hip, reload samples01/05/08/10/15/19 and ADS samples09/10 via view_image. Also re-viewed the original61 upper-chain sheet and retained W182 storyboard containing actual same-weapon gameplay frames. No dynamic input or live QA was performed.

- Sample01 shows early raised weapon presentation. Sample05 shows the rolled receiver with support handling largely below/behind the gun. Sample08 shows a silver magazine cap at the palm end; most of its narrow body is obscured by the solid arm. Sample10 shows the raised source palm and cap near the forward/top receiver; this alone cannot establish a wrong action or wrong source hand. Sample15 shows receiver low with handling mostly below the viewport. Sample19 recovers the weapon presentation. The hip PNG has separated rear firing/front support contacts; ADS09/10 show a centered, readable aperture. FIRST observations are not post-correction acceptance.
- Capture numbers are ordinals, not source indices: samples01/05/10/15/19 bracket client ticks730-731/739/750/761-762/770-771. The server progress log is sparse (.0333/.1667/.30/.4333/.55/.6833/.8333/.95); exact source progress for each PNG is not supplied. Numerical probes below cover the source mid-reload interval, not an invented exact PNG-to-pose match.

Current main shared-code inspection confirms that sourceFullChain replaces both palm translations with evaluated source wrist travel plus REST mesh-contact offsets. reload.contact does not drive this palm; it controls magazine placement through reload_target and part_shift. The source action is shared and bone-only, so the high palm must be preserved and cannot by itself be classified as an insertion/charging error.

Actual magazine_core is only 0.74 units wide (X7.63..8.37); the classic fingerless forearm is 2.4 wide and deep. Existing reload contact [7.5,5.8,8.68] is just 0.13 outside that core. At full attachment, sampling 8x16x8 interior points per magazine solid, weighted by each solid volume, inside the source-oriented classic forearm envelope gives:

| Original source p | Old X7.5 overlap | New X6.5 overlap |
| --- | ---: | ---: |
| .40 | 52.73% | 10.44% |
| .45 | 50.13% | 10.54% |
| .50 | 49.72% | 8.26% |
| .55 | 49.39% | 8.33% |
| .60 | 49.74% | 10.86% |

This is an approximate geometric overlap estimate, not rendered visibility or native collision certification. The arm envelope uses actual W204 X/Z half-width1.2 and local Y[-6.5,1] scaled by ordinary source forearm length/6.5. It includes the entire forearm, not just the cap. No geometry is changed.

Three profile changes are supported:

1. reload.contact **[6.5,5.8,8.68]**: a side-flank handling point, one unit outward from the old contact. At full attachment this offsets the whole held magazine +1 canonical X relative to the unchanged source palm. Keep Y/Z, rotation, partHint=magazine, policy and action80A8A170. This addresses the mostly swallowed narrow magazine; do not erase the high source-hand excursion.
2. reloadCameraLower **0** instead of2.5: remove the extra inherited camera-Y drop applied on top of actual source weapon motion. At p=.70 the source-driven body Y is -0.223 before this extra drop and -2.723 after it; p=.75 is .683 versus-1.817. All source-driven dips and rotations remain. No new lift/crop/hide is added, and hip/fullADS/endpoints are unchanged.
3. reload.gripWindow **[.05,.20,.60,.70]**: retain reach/attach timing, release after the authored W182 seat at .60 and complete by original source foregrip recovery at .70. Source neutral-model left palm is [7.484,8.598,3.478] at .70 and essentially rest [8,8.85,3.5] by .75. The previous default stays fully attached through .78, pulling the already-seated magazine roughly5.20 units forward at .70; the new window has zero attachment then. The release envelope moves only the magazine; original wrists/elbows/shoulders/weapon samples and gameplay duration remain intact.

Right/left REST contacts, family translation/rotation/scale, wrist roll and full source61 rig are unchanged. The generator remains byte-identical, SHA-256 e92da4ac548aff20155a0aea8f5a14fed2589d21b7b684efd2791e60596c3bc8. No .40 early release, FK attenuation, stretching, arm hiding or source-action replacement is performed.

The W182 gameplay reference is a partial reload with authored magazine insertion .40..60 and support recovery .68..90. Original shared170 includes a high source-hand excursion at .45..60 and foregrip return by .70. Without source mesh or magazine event markers, an exact source insertion/bolt phase cannot be asserted. These changes correct observed clearance, the extra camera drop and clearly late attachment; they do not claim to solve or prove every part-contact phase. If SECOND still shows reseating conflict at .55..70, the master must resolve the shared phase-aware part attachment/seat policy while keeping original FK intact. Changing a static REST contact to force a middle phase or remapping original source time is not justified.

SECOND native must inspect held-magazine visibility at the sample08/10 equivalents, .55..70 reseating/release, sample15 handling visibility, exposed elbows, both hip contacts, ADS aperture and return. No SECOND evidence or final native acceptance exists yet.

Scoped post-correction checks passed: actual shared helper evaluation gives identical original FK matrices for all61 samples; source rig SHA remains d09352a9bd907ed80efdf4a46f4436500c4ed354175538d4fcf7b832bec6043f. Source palm X/Z and travel relative to body are unchanged; the only whole-assembly difference is removal of the old2.5*envelope camera-Y drop. Source body rotation/scale and full ADS remain exact. New magazine attachment is zero from .70 onward. Generator SHA remains e92da4ac548aff20155a0aea8f5a14fed2589d21b7b684efd2791e60596c3bc8. Its248-entry mapping is deterministic and all247 asset hashes recompute under a filesystem-write audit. No pack output or manifest was materialized. No further offline iteration is needed before master SECOND native.
