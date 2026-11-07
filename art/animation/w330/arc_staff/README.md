# W330 Arc Staff — first source-backed candidate

Status: candidate for master second native Vision, not final visual acceptance.

The read-only delivered `source.blend` was directly evaluated in a separate background Blender 5.4 process. `blend-inspection.json` records 18 actions/slots and 72 source bones; `headless-source-samples.json.gz` contains the evaluated 60 Hz matrices. The two review PNGs show five actual evaluated source joint poses above the unchanged Minecraft rig proxy. They are not game screenshots or a rendered original mesh.

| Runtime clip | Source tag | Duration | Provisional contact |
|---|---|---:|---:|
| h15_super_arc_start | 80A8A922 | 1.433333333 s | deploy .433333333 s |
| h15_super_arc_start_air | 80A8A95C | 1.3 s | — |
| h15_super_arc_attack | 80A8A937 | 1.3 s | .333333333 s |
| h15_super_arc_attack_weak_2 | 80A8A92A | 1.4 s | .266666667 s |
| h15_super_arc_attack_weak_3 | 80A8A92B | 1.233333333 s | .266666667 s |
| h15_super_arc_attack_air | 80A8A92D | .666666667 s | .266666667 s |

Original event payloads are opaque and have not been decoded as damage. Contacts/deploy are explicitly provisional visual beats. Weak2 uses the first fast hand sweep around source frame9; the opaque .733333 event is not claimed as its damage timing. Original full timing, preparation, force transfer, recovery and genuine rapid staff wrist twirls remain; no .5/.35 second compression and no forced neutral endpoint.

Retarget preserves the installed 18-group/26-element rig, pivots, UUIDs, geometry and UVs. Anatomical shoulder/pelvis frames and source limb directions drive Minecraft proportions. Source upper-leg rotation transports the knee pole through extension; arm IK pole continuity resolves straight-arm ambiguity. The right staff is attached to the wrist; a shared source cast frame44 defines its shaft basis. Left hand releases follow the source; regrip IK applies only near its shaft. Horizontal entity/root lunge belongs to runtime; positive source toe height is retained as visual root lift.

Every dense rotation key contains both continuous Euler values and a hemisphere-continuous unit quaternion in Blockbench intrinsic XYZ (Rz*Ry*Rx), before Minecraft signs. Runtime SourceAnimationGrid remains responsible for 40 Hz compilation. Entry1/exit2 blend ticks are metadata, not baked neutral poses.

Reviewed against master first native baseline-arc-02/07: restore full cast/attack rhythm, avoid immediate upright reset, retain whole-body action. The supplied baseline-arc-clean was excluded because of platform-edge interference. Native equipment grip, head rotation, late recovery/regrip, skin intersections and recovery into the existing idle remain master second-Vision checks. The unchanged idle/move clips are not claimed as source-backed replacements.

`validation.json` records targeted schema, mapping, quaternion agreement and unchanged input hash checks. No client/server, shared QA or runtime file was modified by this worker.

## Native second-Vision clearance follow-up

Master ground03/12–16/25–27 and air10/14 captures were reviewed. The source twirl is intentional, but the enlarged Minecraft head admits shaft overlap in the cast/light attacks. The follow-up shifts only 44 overlapping 60 Hz wrist poses: cast8, air cast7, weak1 7, weak2 12, weak3 10, air attack0. The staff keeps its original world orientation; right wrist and attached staff move together, and an established two-hand grip translates both wrists together. Candidate supporting-plane translations retain arm reach, with the smallest displacement among sampled reachable directions selected. Maximum displacement is 3.903414 model units (.243964 block); weak2 max2.756 units (.17225 block).

No duration, contact, recovery, blend metadata, head or other non-arm animation, geometry, UV or UUID changes. Original source hashes and sampled matrices remain unchanged. `clearance-validation.json` verifies zero expanded-head/shaft overlap at the generated 60 Hz keys and unchanged source shaft direction. This is an offline fixture check; master cast/light2 native recheck remains pending.

## Continuity revision (supersedes the one-pose minimum above)

The previous per-pose minimum changes avoidance side too abruptly. This revision chooses a continuous translation path only in the overlap windows and their three adjacent entry/exit poses. Adjacent correction changes are bounded during local selection; the measured maximum falls from4.69546 to1.553597 units (66.9% reduction). Maximum offset becomes5units (.3125block), weak2 max3.75units (.234375block), with zero expanded-head/shaft overlaps at the generated60Hz keys. The source staff world rotation, head/other non-arm keys, timing/contact/recovery/blend metadata, rig/UV and UUIDs remain unchanged. Representative PNGs show the prior clearance candidate; they are original source-evaluation evidence and were not rerendered for this continuity revision. Master final cast/light2 native recheck is pending.
