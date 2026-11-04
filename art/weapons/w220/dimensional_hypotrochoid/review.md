# W220 Dimensional Hypotrochoid — ready candidate, FIRST pending

Worktree: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w220-dimensional_hypotrochoid`.
This is a new weapon-specific authored reload route using shared heavy-GL source
action `80A8A104`, group `heavy_grenade_launcher_796e9ebf`. It is ready for the
master's FIRST review, not final native acceptance. No children were spawned.

## Owned delta

- `scripts/generate_reload_w220_dimensional_hypotrochoid.py`
- `art/weapons/w220/dimensional_hypotrochoid/profile.json`
- `art/weapons/w220/dimensional_hypotrochoid/review.md`

Only these three product files are authored. Generated resources, shared
loaders/runtime, QA, dependencies, SSD source, user DCC and game are untouched.
No commit, reset, stash, clean or push. The worktree contains the master's dirty
seed; unrelated existing changes are outside this delta.

## Source evidence and limits

Read `worker-common.md`, worktree `AGENTS.md`, RTK, the weapon-art skill and
Ace/Izanagi study. Read the master's complete `source-review.json`,
`source-handling-evidence.json`, `source-selection-review.json`; viewed the actual
`sheets/heavy_grenade_launcher_796e9ebf-80A8A104-upper-chain.png` with the image tool.
The profile records their hashes and observations.

The master evaluated original `source.blend` read-only in separate headless
Blender 5.4 Alpha before this implementation and exported 61 evaluated samples
from frames 1..142. **The worker did not independently open/evaluate Blender.**
Both reviewed source rigs contain ARMATURE objects only; mesh, camera and finger
IK are absent. Heavy104 has a moving LEFT loading wrist and essentially fixed
RIGHT carrier wrist. Single136 and126 were considered by the master for the
other GL class. This is shared class104, not a recovered weapon-specific selector
or exact Dimensional Hypotrochoid mesh/latch animation.

The source wrist samples show the large handling excursion around .25..60 and
return toward support around .65..80. Their motions are preserved by the master's
full-chain replay. New part motion/contact windows are authored from this timing
and the actual canonical geometry; no source palm or arm is moved to fit them.

## Geometry and mechanical decisions

The canonical surface model has **92 elements**, with every original element,
rotation, face UV, texture slot and name copied unchanged. No geometry or UV is
borrowed from High Albedo, Edge Transit or Canis Major; no new elements or atlas
are introduced. Indices are zero-based; actual drum names have suffixes0..3 and
0..7, not global-index suffixes.

| Part | Indices | Elements | Behavior |
| --- | --- | ---: | --- |
| body | 0..42, 62..91 | 73 | Identity authored motion; source weapon replay only |
| magazine | 43..54 | 12 | Four drum solids and eight jackets move as one rigid drum |
| latch | 55..61 | 7 | Root, handle, both returns and upper cage pivot together |

The drum anchor is its real center `[8.026,10.16,2.6]`, and extraction starts
toward canonical left `[-1,0,0]`. The authored latch hinge is at its rear mount
`[5.62,10.16,5.19]`: 70 degrees about local Y swings the forward end outward.
The cage remains gun-attached; only the removable drum has `policy=magazine`.
The opposite right latch62 stays fixed. Foregrip63..65, skeleton pistol grip
66..74, trigger frame75..77, open optics78..91, stock and long beam stay fixed.
The broad painted volumes and actual frame/sight voids survive the split.

| Progress | Authored mechanism |
| --- | --- |
| 0..08 | Source reach; mechanism seated |
| .08..20 | Left latch cage opens |
| .20..38 | Whole drum extracts left/down |
| .38..46 | Exchange hold; source wrist continues without attenuation |
| .46..64 | Replacement approaches; source-left attachment fades .52..64 |
| .64..68 | Released drum finishes coaxial seating |
| .68..80 | Drum remains seated; latch closes .70..80 |
| .80..1 | Source recovery; all authored parts at their canonical pose |

One rigid drum represents the outgoing and incoming assemblies through the
exchange hold. No duplicate drum, individual rounds, hidden shaft, mesh visibility
trick or source-derived latch event is claimed. Rear hinge placement, extraction
orientation, clearance and exchange interpretation are authored approximations.

Idle right `[8,8.2,9.05]`, left `[8,7.9,-2.7]` and reload drum-flank contact
`[5.65,10.1,2.6]`, including their rotations, match W201 exactly. Reload uses LEFT,
`partHint=magazine`, `policy=magazine`, `rigAction=80A8A104` and
`gripWindow=[.18,.24,.52,.64]`. Attachment ends before .68 seat, so later source
recovery cannot drag the seated drum. Native fingerless palm fit is unverified.

Read the current `first_person_framing_w205.load/profile` API. Preserve effective
heavy framing: translation/rotation zero, scale1, rightWristRoll15. Require
sourceFullChain/keepMeshSupport true and hideSupportAtRest false. No authored body
swing, source damping, arm stretching, support hiding or new camera offset. The
master applies source weapon motion once across body, latch, drum and full arms.

## Generator and checks performed

Pure stdlib `generate(root=ROOT, *, rig_path=None, profile_path=None)` returns
`dict[absolute Path, bytes]`. Default rig is
`art/weapons/w220/rigs/heavy_grenade_launcher_796e9ebf.json`; checks used the
master's scratch rig override under `/private/tmp/destiny-w220-source/`.
No returned resource was materialized. Default shared loader installation is
master-owned and was not exercised here.

Passed a bounded Python `-B` check with an audit hook that rejects file writes
during import and two generate calls:

- Deterministic **371 returned files**: 3 base geometries, 366 parent/display
  children (61poses ×3parts ×2grips), 1 item and 1 manifest. Pack files370.
- Exclusive output namespace and absolute Path/bytes mapping; all JSON parses.
- Fresh heavy104 source range1..142, all61 evaluated shoulder/elbow/wrist/weapon
  samples and profile source provenance verified; all hashed input bytes unchanged.
- Disjoint partition covers all92 source elements exactly; face records and
  texture references preserved without baking, duplication or triangle adapters.
- 61poses/60intervals and exact float32(i/60) thresholds; all knots reproduced;
  6,001 dense samples per moving part remain inside neighboring key extrema.
- Two-sided derivative checks at all interior knots support C1 continuity;
  largest finite-difference discrepancy at step1e-7 was0.002101 or less.
  Holds/extrema/endpoints use zero tangent. No per-segment smoothstep stops.
- Both FP contexts/native and twohand displays finite; nonFP displays unchanged;
  endpoint displays byte-value exact; body display unchanged at every pose.
- Item extra keys, nonFP fallback, negative/inactive,0/1,overshoot canonical
  graph, ADS and inspect precedence preserved. All interior entries select the
  intended body/magazine/latch children for both grips.
- Drum is exactly seated from.68 onward; latch holds open.20..70 and is closed
  from.80 onward. Attachment is zero before seating.
- Active weapon92 +448 ordinary four-arm surface reserve = **540**. Existing
  canonical fallback/ADS/inspect references in this seed resolve to198 elements,
  yielding **646** with that reserve. Alternatives are not summed. The first
  local budget assertion incorrectly assumed fallback92; inspection corrected
  the assertion, and all checks passed with the preserved198 route accounted for.

The manifest records generator/profile/rig/canonical geometry/texture/contact/
timing/sound and resolved fallback hashes, actual partitions, curve keys, phases,
authorship, output hashes, budgets and explicit native limitations.

## Pending master review

No full hands generation, Gradle, pack load, game, native input or Vision was run
by this worker. Full-chain arm output counts remain an estimate until the master
materializes and measures the route. 61 discrete poses do not prove continuous
native60fps interpolation. Source armature projections do not prove native
contact, latch clearance, sight visibility or exact recovered mechanics.

The master must install the fresh rig/profile route, run FIRST input/PNG review,
return feedback to this same worker, then integrate a correction or justified
no-change and run SECOND Vision. Prioritize left-palm/drum transfer and release,
rear latch hinge clearance, sight/arm occlusion, seated recovery, ADS/inspect and
canonical fallback preservation. Worker remains available for FIRST feedback;
no formal metadata-only acceptance edits are planned.
