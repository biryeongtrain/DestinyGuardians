# W207 common reload arm sampling

Implemented only in `scripts/rig_arms_w205.py`; focused plain Python checks are in `scripts/qa/test_reload_hand_motion_w207.py`. Private gitdir was confirmed `refreshRevision=W207,status=ready` before edits. The generator, gun geometry, W206 profiles, gameplay durations and native apps were not edited or run.

## Sampling change

`round(progress*20)` held Ace/Duke arms on a nearest source frame even when gun banks had finer states. `sample()` now brackets the actual exported `frames[].progress` values, linearly interpolates joint positions and uses normalized shortest-arc quaternion slerp for joint rotations. This lets each authored output state use its own intermediate wrist/elbow pose. It does not add client-side interpolation or claim a 60fps server update rate; 21 exported evaluations still bound the motion detail.

Whole-magazine reloads blend from selected idle/ADS to the evaluated source over the first 10% and recover over the last 10% using smoothstep. Exact endpoints use the original rest matrices. This endpoint calibration closes source/target neutral differences without changing gameplay duration. Source evaluated matrices contain sub-micro scale/shear noise; quaternion normalization removes it at interior states.

`apply()` continues to use the source wrist/elbow direction and wrist twist. Its arm length comes from the unchanged selected idle/ADS source forearm, so linearly interpolated FK positions cannot shorten the displayed arm along a chord or introduce an extension. No new fingers or arm geometry are introduced. The existing hip/sourceViewRotation and native/two-hand carrier compensation are retained; body display rotation is not multiplied onto source FK a second time.

## Source selection and caller contract

`apply(...)` keeps its existing signature and already passes its `config` to `joints(data,state,progress,config=None)`. Existing three-argument `joints` calls for Ace/Duke remain valid.

| Weapon | Evaluated group / reload action | Selection |
| --- | --- | --- |
| Ace | `hand_cannon_f163a4c8 / 80A8A567` | Existing selection retained. |
| Duke | `hand_cannon_cedb29ae / 80A8A53D` | Existing selection retained. |
| Izanagi | `sniper_rifle_ececad46 / 80A8A140`, `80A8A14D` | Caller supplies normalized progress; original state CMD6 `2..3` chooses Honed, ordinary selects `140`, charged `4` stays idle. |
| Hammerhead | `machine_gun_e5b72131 / 80A8A005` | Unique evaluated reload action. |
| Dust Rock Blues | `shotgun_2eb0529e / 80A8A3F1` | Caller must set `config['insertPhase']` to `initial`, `loop`, or `return`, passing normalized per-phase progress. |
| Ammit | `auto_rifle_943c13a2 / 80A8A395, 80A8A38C, 80A8A38A` | Caller must explicitly set `config['reload']['rigAction']` to a reviewed action. No guessed default. |
| Blast Furnace | `pulse_rifle_b4d01502 / 80A8A36A, 80A8A368, 80A8A366` | Same explicit `reload.rigAction` requirement. No guessed default. |

Weapon identity for the five routes comes from `config['weapon']` or the final component of existing `config['canonicalModel']`. No generator edit is included here. **Master integration requirement:** forward the original state CMD6 and Dust `insertPhase`; supply reviewed Ammit/Blast `reload.rigAction` tags. Missing or invalid ambiguous actions raise a descriptive error rather than silently generating static or arbitrarily selected hands. Test tags are API examples, not a claim that one ambiguous variant is the exact weapon-specific animation.

Evidence read-only: `art/weapons/w205/rigs/{auto_rifle_943c13a2,pulse_rifle_b4d01502,machine_gun_e5b72131,shotgun_2eb0529e,sniper_rifle_ececad46}.json`, their `sourceBlend` locations and the original `source-map.json`, `clips.json`, `events.json` alongside the Blender directories under `/Volumes/qf-ssd/DestinyGuardians-Animation-Return-2026-10-27/destiny-animation-return/clips/`. In particular, the Ammit/Blast source maps call all three distinct variants `reload_full/reload_empty` and assign the shared selector to multiple weapons; they do not resolve a unique per-weapon action. The evaluated wrist matrices differ materially, so interchangeability cannot be assumed. Existing gun generators describe authored reference approximations, not a matching source-body timeline. No external exact-action evidence was invented.

## Mesh contacts and Dust lifecycle

The W206 `keepMeshSupport` branch remains: opted-in guns retain the generator's left moving-magazine/shell contact and idle/ADS forebody support; source wrist separation never replaces those positions. Non-opted-in Ace/Duke still use their evaluated changing wrist delta anchored on the right hand.

Dust's generic full-reload source is not a recovered per-shell event timeline. The following is explicit direction-only lifecycle calibration; the master still owns the actual moving-shell contact and phase motion:

- Initial: source progress rises smoothly `0 -> .35` by local phase `.36`, then holds. Only the phase start blends from rest.
- Loop: source progress follows `.35 + .30*sin(pi*p)^2`, an excursion/retrace through the evaluated source with matching `.35` direction at both boundaries. No idle blend at either loop boundary.
- Return: source progress rises `.35 -> 1` with smoothstep and blends to rest only in the final 10%.

Thus initial-end, every loop seam and return-start share the same non-idle source pose; only initial-start and return-end settle to idle. This prevents an artificial idle pulse per shell. The selected slice and excursion are authored calibration, not source contact-event recovery. Synchronization of source wrist angles with the authored gun-body/shell timeline still needs consolidated native review.

## Checks and remaining review

Ran `rtk proxy python3 -B scripts/qa/test_reload_hand_motion_w207.py`: **6 focused tests pass**. They cover intermediate position/short-arc rotation, whole-mag endpoint continuity, five route APIs with ambiguous-action rejection, ordinary/Honed/charged Izanagi, Dust phase seam continuity, and unchanged mesh-contact versus Ace dynamic separation plus constant ordinary arm length. No Minecraft build, full generator, CU, Vision or server was run.

Master pending: choose the two ambiguous action variants from actual motion/reference evidence; regenerate after passing those choices; check representative hip/ADS ordinary and Honed reloads, both grip modes and classic/slim skin arms; inspect wrist/mesh attachment and endpoint/insert-phase recovery. Retained compensation and source angles are source-level checks, not native verification. Source-body versus authored-gun phase alignment remains calibration and may need visual tuning.
