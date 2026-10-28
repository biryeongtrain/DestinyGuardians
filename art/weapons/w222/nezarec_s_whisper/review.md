# W222 Nezarec's Whisper — FIRST correction for SECOND

Owned slot4: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-pyroclastic_flow`.
Only these source files were created:

- `scripts/generate_reload_w222_nezarec_s_whisper.py`
- `art/weapons/w222/nezarec_s_whisper/profile.json`
- `art/weapons/w222/nezarec_s_whisper/review.md`

Read worktree AGENTS.md, RTK.md, weapon-art skill and Ace/Izanagi reference;
read W222 source-review, source-handling-evidence and selection JSON. Viewed
master's actual `source-sheets/glaive_f9784d8f-80A8A440-upper-chain.png`
read-only in main (the sheet is absent from this retained slot).

Source: master evaluated original `glaive_f9784d8f/blender/source.blend` in
separate Blender5.4 Alpha, action `Armature|fp_80A8A440_reload_full|Base`,
OBSlot, frames1..123 at30fps, 61 evaluated samples including shoulders;
prior cached joint error0, inputs unchanged. Worker reviewed that evidence
and sheet; no independent Blender evaluation claimed. Profile pins matching
sourceBlend/sourceMap/boneMap hashes and fresh W222 cache
`73e2109a902758b6a2816de4880841c1222c559e6c867525ef0fda7d0ca93b47`.
Source-review's older input-cache hash describes the pre-resampling W205 input.

Actual weapon-relative wrist excursions: RIGHT0.5977702659,
LEFT0.1692102682. RIGHT loads; LEFT supports the upper shaft. This supersedes
older W201 prose assuming LEFT reload. Keep RIGHT lower ready contact
`[8,8.7,8]`, LEFT upper contact `[8,12,8]` and their calibrated rotations.
Reload is RIGHT, `policy:fixed`, `partHint:loading_port`; existing contact
`[7.55,6.35,8]` remains a geometry-derived estimate from
`magenta_front_cell_-1`, not an extracted cell/cavity/event track.

Strategy: one intact148-element body, 61 neutral carrier poses/60 intervals,
CMD1 normalized0..1, exact float32(i/60) thresholds. Both native and twohand
display children retain accepted displays for both FP handed contexts and
all other contexts. Master replays original weapon bone and both complete
shoulder/elbow/wrist chains once through `sourceFullChain` and
`sourceWeaponMotion`. No local weapon sweep, detachable cell, extra geometry,
arm stretch/hide, axis damping or camera fitting. Effective existing framing
is merged with source flags only; rest transforms and blade-forward
first/third-person remain accepted values. Canonical endpoint graphs,
negative/overshoot fallback, nonFP, ADS/inspect and item metadata are preserved.
Timing/audio remain the existing62 ticks; no gameplay/ammo/input/guard changes.

Return mapping:125 absolute Path→bytes entries: one geometry parent,
122 display children, one item graph (124 pack files), one manifest. No
generated output was materialized. Simultaneous candidate148+448 ordinary
skin-arm reserve=596; unchanged raw canonical246+448=694≤1000. Alternatives
are not summed. Master must measure actual assembled routes and four arm
surfaces; this is a conservative reserve, not integrated-budget acceptance.

Small read-only validation passed under an audit hook rejecting writes,
mkdir, removals, renames, links, truncation and subprocess/system calls during
import/generate. Repeated default/explicit override calls produced identical
bytes. Checked exact125-path namespace, JSON decoding, output hashes, intact
geometry/UV, all122 accepted display children, canonical graph endpoints,
fallback/nonFP/ADS/inspect, and all60 float32 exact/predecessor boundary pairs.
No build, game/CU/Vision operation, dependency change or numeric perk test ran.

Limits: original source is ARMATURE only, with no weapon mesh, camera or
finger IK. The source sheet shows arm-chain motion, not native contact or
visibility.61 poses do not prove continuous60fps native interpolation.

FIRST completed: master reports native13/13, source tests2 and JUnit16 passing;
read the actual QA JSON for these results. Master measured all-route maximum
including arms694 in `assembled-budgets.json`. These passes do not accept the
visible reload. Viewed actual FIRST review/reload sheets and
`first-post-reload-review.png`: weapon visible near reload01/17, mostly or
completely absent05/09/13 while a huge RIGHT arm crosses center. Postreload
returns to the initial blade-forward appearance with7 rounds; the middle
reload defect is not a persistent rest-transform change. FIRST is visually
rejected pending the registration correction and SECOND.

The source idle action80A8A3C2 establishes weapon-local two-grip separation.
After existing global calibration C and conversion32 it is
`[-2.515967792,-0.575357401,-12.567755442]`; calibrated mesh LEFT−RIGHT is
`[0,3.3,0]`. Source shaft projects mostly−Z but the existing modeled shaft is
+Y: bare shaft/grip continue alongY and blade_core extendsY19.56..28.04.
This is an axis registration error, not evidence for a camera adjustment.

Profile now opts into `framing.sourceMeshBasis=Q` and `sourceMeshPivot=true`.
Q is the unique shortest-arc rotation between those normalized grip vectors,
92.570268057 degrees, with no added twist about the shaft:

```
Q = [[ 0.959739335418290,  0.196099952437725, -0.201109961724378],
     [-0.196099952437725, -0.044844595944699, -0.979557946661900],
     [-0.201109961724378,  0.979557946661900, -0.004583931362989]]
```

Generator derives Q independently from the actual source idle weapon basis,
source wrists and calibrated mesh grips and rejects an unrelated matrix.
It still emits the same neutral geometry/display/item carriers: only profile
metadata, validation and manifest registration declarations change. Accepted
rest/ADS displays, contacts, scale and sourceViewRotation zero are preserved.
No source rotation/travel attenuation or new camera/arm visibility value.

Master-owned helpers must apply Q coherently in
`scripts/rig_arms_w205.py`: `source_weapon_display` uses `Q*A*Qᵀ` and Q times
source translation; `source_palm_translations` uses Q times both weapon-local
wrist offsets; `apply` uses `Q*C*wtᵀ*forearm_basis`. Upper-arm relative bend
stays unchanged. Master has prepared the optional shared helper/regression;
worker made no shared-path edit and requests integration with this opt-in.

Also register the static source weapon origin relative to remodeled mesh:
`O=(rightGrip-8)-32*Q*C*wrᵀ*(restRightWrist-restWeapon)` gives
`[-0.185286203280,3.792944977606,-0.604136781030]` model units. With
`A'=Q*A*Qᵀ`, local translation is `32*Q*shift+(I-A')*O` BEFORE accepted ready
scale/rotation. The32 multiplier applies to source-space travel, not O.
This supplies the missing rigid rotation pivot; it does not tune the view.

Representative read-only reproduction of the old helper versus coherent
basis+pivot registration, using accepted twohand display translations:

| CMD1 progress | Old body translation | Registered body translation |
| --- | --- | --- |
| 0.2 | [-6.788434,6.478683,14.322755] | [5.401767,10.946512,-15.659347] |
| 0.4 | [0.271760,7.776432,13.296530] | [7.325135,12.890819,-8.291154] |
| 0.6 | [-1.635061,22.065245,7.032022] | [16.208206,19.807956,-9.360144] |

These are item-display translations, not recovered camera poses or exact
timestamps for framebuffer05/09/13. Wrong axes direct large source travel
toward the viewer; corrected Z moves into depth. Generic-C pivot alone has
|O|3.063 model units, hence at most7.658 units after accepted1.25 scale; it
cannot alone explain/correct the full axis-induced displacement. Cross-rig
comparison: Long Arm generic-C O=`[-0.662720,-0.116826,-2.189740]`, grip-axis
angle11.841019 degrees; Biting Winds O=`[-1.299615,-2.044349,-5.567032]`,
angle53.750140 degrees. Nezarec Q is an explicit opt-in, not a global change.

Small read-only correction checks: proper Q determinant1, orthogonality error
1.11e-16; all61 source pose compositions checked, both palm max error1.10e-14
model units against direct rigid source transform (including each hand's
constant remodeled contact offset), forearm max matrix error5.55e-16.
Pivot term maximum4.950405 model units; source travel magnitude preserved.
Pure import/generate assertions, deterministic125-file output, geometry/UV,
all122 accepted displays, canonical graphs and60 float32 predecessor pairs
passed again. An auxiliary cross-rig print initially shadowed its audit
module variable after those assertions; corrected cross-rig calculation ran
successfully. No output was materialized and no game/build test was run here.

Limits: source/mesh grip lengths differ12.830028 versus3.3 model units; Q
aligns direction only. No source length rescaling or ordinary-arm stretching
is introduced. Shortest arc is an explicit static registration choice, not
proof of recovered blade twist, original weapon mesh or camera. Actual posed
camera remains unavailable.61 poses remain bank samples, not continuous60fps.

Pending: master integrates the three owned source files with its optional
shared basis/pivot implementation, runs its registration regression and
regeneration, then SECOND actual framebuffer review of visible reload,
ordinary-arm contact/clearance, hip/ADS and return. No SECOND or final visual
acceptance claimed. Worker remains available.
