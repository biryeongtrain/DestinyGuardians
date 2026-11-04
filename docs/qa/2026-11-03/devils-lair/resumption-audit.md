# Devils Lair resumed implementation audit

The previous goal turn made progress: shared revival completion variants were implemented, packaged and validated with five actual server tests and live framebuffer checks. User has now resumed the strike objective and authorized autonomous Vision QA.

## Requirements still governing this activity

- 1–3 admission, fixed three-player difficulty; no participant-based scaling.
- Rewards skipped per user direction; actual three-human difficulty acceptance deferred until implementation, not an admission gate.
- NBT map-templates chunk generator, retained existing Walker, Dusk Fallen / Normal Hive source appearance.
- Faction infighting with visible/attacking player priority; no enemy knockback.
- Team proximity revival and restricted/unrestricted self timers; latest shared audio/motion refinements retained.

## Current evidence and remaining acceptance

| Area | Current evidence | Remaining work |
|---|---|---|
| RY | Live 24/24 packs, native movement and player-directed fire in player-priority-live | Full natural clear and transition |
| RF / BL / SP navigation | NBT voxel comparison and a single RY left-lane admission fixture | All authored ordinary packs on actual generated maps; boss admission and combat-position coverage |
| Boss state / cap / factions | Targeted real-server and pure director fixtures recorded in implementation.md | Native full encounters, checkpoint wipes, shield transitions and no softlocks |
| Presentation | Live HUD plates, descent cue lifecycle, accepted two-tick revive | Remaining combat music source selection, awakening/exit review, per-player recovery |
| Models | Eight dl assets registered; original source/shader/native receipts | Close-range slice artifacts, weapon contacts, lighting and load acceptance |
| Performance | No complete measured acceptance | Three-player 32-actor sustained server/client measurement with hardware/settings |
| Regression | Prior full unit run has 16 failures | Classify and resolve current failures without treating old failures as an automatic waiver |

Next executed check expands the real NBT fixture from eight RY slots to all 31 ordinary packs (248 planned slots), preserving per-pack collision reservations and production spawn checks. Entry-seat reachability is a concrete baseline, not proof of all player positions, simultaneous cross-pack occupancy or boss admission.


## First expanded admission result

The original single-zone callback assertion could be replaced by subsequent tick failures in the final report. The fixture now accumulates failures across all four zones and only asserts at the end. The complete baseline reports multiple RF ground/flying candidate failures and BL exit reinforcement failures. First-pass commentary that RF passed was corrected. Source logs and XML are retained under runtime/all-route-aggregate-before.*.

Production candidate traversal has been changed to visit authored pads before offsets around a single pad, retaining the existing four navigation-probe cap, collision/support checks and minimum player distance. The all-zone regression is being rerun. This change is not yet accepted as a complete route fix; candidate rotation depends on world time, and the fixture does not cover every rotation or live player position.


Diverse-pad rerun remains FAILED: RF-defense1-2 Vandal slots4–6 and Captain7, the same roster RF-defense3-1 slots4–7, and RF-defense3-4 Wizard6 (nine failures). RY/BL/SP produced no failures in this run. No entire-map acceptance or production commit yet. Next inspect RF.C pads/routes for larger ground bodies and RF.D airborne clearance to the entry. Preserve the four-probe work bound; do not bypass path/support validation to force green. Canonical candidate rotation should be pinned in diagnostic comparisons before claiming a quantitative improvement.


## Native navigation diagnosis (22:39–22:44)

- The small Dreg probe reaches RF entry. The Vandal probe stops despite its physical body fitting the remaining passage. Per-node native probes locate top slabs that block Minecraft's rounded three-cell navigation envelope; one full polished-andesite voxel also physically clips the Vandal head.
- Reproducible refinery generator adaptations remove five specific ceiling voxels: local (54,14,65), (62,19,71), (53,14,64), (47,14,58), (46,14,57). Source GLB remains untouched; generated refinery and manifests were rebuilt from source. Other zones preserved.
- Mobile ordinary flyers on ground-authored pads now test lower hover positions down to the pad elevation, retaining bounds/fluid/body/reservation/path checks. Explicit airborne boss anchors retain their height.
- The admission fixture now exhausts one canonical candidate-rotation cycle before failing each slot. Each production attempt still has four navigation probes, and prior accepted slot reservations remain. This tests eventual admission under the existing retry behavior, not instantaneous full-pack spawn or a guaranteed retry latency. Real director timing and native traversal remain separate acceptance.
- Diagnostic failures are preserved in runtime/all-route-clearance-before.*, all-route-first-clearance-fix.log and all-route-node-diagnostic.*. Current corrected rerun is pending.

Cycle rerun: Wizard and Marauder admit, but RF.C tall ground actors still fail. Native per-node results show diagonal corner neighbours must also have three-cell headroom. Generator now clears the four orthogonal neighbours of the five diagnosed ceiling voxels (25 candidate cells, existing air included), preserving the floor. Rerunning before acceptance.

Native all-four-map GameTest PASSED after corner clearance (runtime/all-route-corners-pass.xml/log). All 31 packs / 248 slots eventually admit within a full canonical rotation cycle with per-pack reservations. This includes actual NBT voxel/heightmap/supplies checks. Does not certify arbitrary player positions, simultaneous cross-pack occupancy, boss admission or native actor traversal.


## Autonomous Vision 22:48–22:54

- Related Gradle unit tests 65/65 and jar passed (runtime/route-unit-build.log). One actual all-zone NBT GameTest passed.
- Owned Vision DevilsQA on 127.0.0.1:25610, port8102; native RY movement and RF entry movement completed with released leases. Actual PNGs inspected under runtime/route-clearance-live/. Input was neutral at cleanup.
- RY was cleared using server damage attributed to DevilsQA after admin revive/resistance; not native weapon combat acceptance. Earlier /kill commands caused lost/replacement actors, not legitimate kills; this is consistent with death provenance protection. A native jump attempt while down failed player_not_controllable and was preserved; admin revival is separate fixture evidence.
- RF native movement was followed by real spawn failures and checkpoint reset: RF-entry-1/6 and /7 flying slots, RF-entry-2/7 ground slot. `Three failed placements: RF-entry-1/6` at22:53:08. This disproves complete live admission acceptance despite the full-cycle isolated probe passing. The fixture currently allows16 candidate rotations, while production resets after3 failed attempts, and live actors occupy additional space.
- NEXT: reproduce actual director retry timeline and concurrent actor reservations/occupancy in the fixture, examine persisted spatial search progress versus rotating one index by time, and fix reset behavior without bypassing collision/routes or increasing unbounded per-tick path work. Do not claim the full-cycle fixture proves production admission timing.
- Actual PNGs also show source-conversion slice noise on mobs, coarse close-range map geometry and initial tutorial notice overlapping subtitle. These remain presentation defects, not accepted commercial quality.
- No new commit: live integration is not yet accepted. No production deployment. User's latest instruction authorizes autonomous Vision launches going forward.


## Resumable placement implementation (22:57)

Previous goal turn is progress: actual native failure identified a mismatch between candidate tests and production reset policy. Current change:

- `DevilsSpatial.Search` preserves candidate cursor and rotation across slices. Every slice revalidates current players, collisions, reservations and routes; each still runs at most four navigation probes. Exhaustion clears the cursor; acceptance clears it too. No cached valid point is inserted on a later tick.
- Session owns one search per slot, clears searches on generation cancellation, and reports `spawnDeferred(ref)` only for the immediately attempted reference. Accepted or fully failed placement removes the search.
- Director retains reservations and retries a deferred search next tick without increasing failures. Three fully exhausted placements still reset the checkpoint. Lost actors retain the existing policy.
- Actual all-map fixture now allows three completed searches, resuming budget yields with a250-slice guard. RF initial three-pack cohort also retains all24 reservations together. Obsolete per-node diagnostic code removed after archiving its evidence.
- Gradle unit66/66 and the real NBT GameTest passed (runtime/resumable-search-tests.*). Native live retest pending; tests do not certify full strike or arbitrary mobile occupancy.


## Resumable placement live result (23:00–23:06)

- Actual RF entry reached24/24 at23:00:57. Native move changed position from(794.069,76,284.381) to(794.700,75.5,290.700), lease/native keys neutral afterward.
- Native55-tick sneak at the RF device triggered the defense sequence. Actual RF_ENTRY → RF_DEVICE → defenses/intermissions1–3 → RF_CLEAR at23:04:01, with no checkpoint-reset or exhausted-spawn log. Combat kills used explicit server damage attributed to DevilsQA, resistance was active; this is progression/spatial acceptance, not difficulty or weapon-hit acceptance.
- BL arrival and native corridor traversal reached(1362.601,72,289.033). Actual boss/pack occupancy27/32, all three boss bars present, Brigs visible in framebuffer. This is admission/entry only; Walker parts, boss mechanics and full BL clear are not yet validated here.
- Evidence: runtime/resumable-live/{rf-defense-server.log,device-native.json,device-after.png,rf-native-move/report.json,bl-native.json,bl-corridor.json,bl-corridor.png}. Close-range mesh slice artifacts remain conspicuous and are not accepted quality.

Final gate after owned runtimes stopped:2537 tests,16 failures,0 errors. Failure suite/case set exactly matches the earlier16 (resumable-full-summary.json); not waived or resolved. Gradle jar ran under --continue and its four placement classes were byte-verified against current compilation (resumable-artifact.json). Owner returned to tower, resistance cleared, input neutral, server/client and owned caffeinate32607 stopped; ports8102/25610 clear. No production deployment.


### Surface diagnostic follow-up — exact texel raster

- Repeated Computer Use preflight: Mac remains locked. No client/server launched.
- Completed two isolated source-preserving offline model candidates and inspected
  actual front/q34 PNGs. Neither meets surface-quality acceptance; no product asset
  replacement or completion commit made.
- Ruled out Cycles transparent-bounce cap for the tested frame by exact pixel comparison.
- Evidence and rejected-candidate details: `models/surface-study/README.md`,
  `exact-comparison.png`, `exact-result.json`, `exact-no-fill-result.json`.
- Goal remains active. Native controlled-distance QA still awaits manual unlock;
  other implementation work can continue independently.


### Combat music bank structure recovery

- Added `scripts/strikes/audit_devils_music_bank.py`, ran successfully against the
  checksum-verified source and pinned wwiser dump: 68 tracks /49segments /40media.
- Recovered source trim/automation/marker/sequence information rather than assigning
  whole files arbitrarily. Preserved report, compressed XML and13diagnostic TXTPs.
-23 media IDs have unique duration candidates;17remain ambiguous. None claimed to
  be authenticated media mappings. Missing bus/multitrack parser limitations recorded.
- Runtime music unchanged; combat cue selection and audible acceptance remain open.
  See `music/bank-review.md`. This is implementation research progress, not completed
  BGM or in-game verification. Goal remains active.


### Deferred GCB notices during strike presentation

- Corrected prior attribution: actual overlap in route-clearance-live framebuffer was the GCB recommendation, matched to client log22:49:13.
- ClientControls now queues optional announcements per recipient during strike admission/running or cinematic presentation; capability detection remains immediate. Late detection cancels stale recommendation; bounded announcement history and disconnect-owned cleanup.
- Targeted14/14 tests and actual Gradle jar passed; byte-matched compiled classes. Full regression: {'tests': 2540, 'failures': 16, 'errors': 0, 'newFailures': [], 'resolvedFailures': []}; existing failures not waived.
- Actual visual recheck remains blocked by Computer Use locked-Mac result. No deployment/acceptance commit; goal active. Details: runtime/control-notices/README.md.


### Real Brig/Sepiks damage integration coverage

Added two real-actor GameTests alongside existing Walker tests; filtered actual
server run passed6/6 and exited normally. Both Brig armor thresholds and death
identity, Sepiks2200HP attribute, guard/intro/shield/recovery immunity, oversized
hit floors1474/726, six real Servitor deaths, final-phase death and exactly-once
completion are verified through Combat.damage. Prior encounters/ordinary add deaths
and intro acknowledgment remain scripted setup; director clocks are synchronous.
No native combat, animation/framebuffer, authored boss-pad or natural-time acceptance
claimed. Product source unchanged. Evidence: runtime/boss-phases/. Goal remains active.


### Special actor admission at authored entry seats

Extended the existing real NBT map test with simultaneous BL bosses/entry pack,
SP boss/guards, and boss plus each shield trio/add pack. The test failed on six
Servitor slots: both rounds reject S1/S3 for line of sight and S2 for collision.
BL bosses/entry and SP boss/guard admission had no failures. These are entry-seat
conditions, not a claim that all player positions fail. Root-cause resolution and
live validation remain pending. Evidence: runtime/special-admission/.
Computer Use still reports the Mac locked; no Vision client launched. User now
authorizes autonomous Vision launches; only manual screen unlock is pending.
Goal remains active; no completion or acceptance commit.


### Shield Servitor pad repair

Diagnosed S2 against five actual wall blocks (no reservation overlap), S1/S3 against
entry-ray occlusion. Added three authored floating alternatives per lane without
loosening distance, collision, LOS or bounded search. Regenerated from read-only
source GLBs; final grid/NBT/route bytes unchanged. Targeted11/11 and expanded real
NBT GameTest1/1 passed across three entry seats and a central player with Sepiks
already admitted. Full2541: same16failures,0new; jar task succeeded and packaged
resources match. Evidence: runtime/special-admission/. Vision remains unperformed
because Computer Use still reports locked Mac. Required-lane proximity/dynamic
occupancy and warp/native fight acceptance remain open. Goal active.


### Temporary spawn obstruction no longer resets the encounter

Terrain-valid pads blocked by player proximity or entity/reservation occupancy now
retain reservations and retry after10ticks; bounded search continuations resume
next tick. This avoids both false checkpoint resets and starvation of later slots.
Hard geometry failures retain the three-failure reset behavior. Targeted68/68 and
actual NBT GameTest1/1 passed; full2542 with unchanged16failures; jar task succeeded
and changed runtime class bytes match. Evidence: runtime/transient-spawn/.
No native visual or audio acceptance claimed. Goal remains active.

Next presentation defect found in current code: DevilsPresentation.incoming draws
at the base lane anchor and expires at the original lead time. A later retry or
alternate-pad admission can therefore appear after its telegraph has expired or at
a different position. Actual selected-pad telegraph/activation synchronization
needs a generation-owned implementation and regression before full acceptance.


### Selected-pad warning and activation synchronization (completed server checks 2026-11-04)

Implemented generation-owned pending pad footprints and exact-position warnings.
Live host starts the full lead after selecting a valid pad, then rechecks that same
pad at activation. Reroutes cancel/restart the warning; pause freezes its director
clock; retirement/reset clears it. Other pending spawns and Sepiks warp include
reserved footprints. The old live reservation lead is disabled to avoid double
waiting. Targeted78/78 and NBT GameTest1/1 passed; full2546 with unchanged16failures;
jar task succeeded and runtime class bytes match. Evidence: runtime/selected-pad-telegraph/.
Actual Session/presentation framebuffer, sound and particle-load acceptance remain
pending; Computer Use again reported locked Mac. Goal active, no acceptance commit.


### Sepiks exact warp commit safety (2026-11-04)

Shared selection/commit validation now includes new pending spawn reservations,
exact authored-anchor membership and consistent player distance. Actual NBT
GameTest validated all four real6.5block pads and late obstruction/proximity refusal;
72targetedJUnit passed. Full2546 retains the same16failures, jar task succeeded and
changed class bytes match. Evidence: ../../2026-11-04/devils-lair/warp-pads/.
Live boss windup/framebuffer/audio remains unverified; no completion claim.

Model fidelity remains a major unresolved product requirement. A possible next
prototype is source-surface triangles through scripts/mesh/native_triangle_elements_w115.py
rather than another rejected axial-slice variant; inspect its constraints and the
existing surface-study rejection evidence before attempting an isolated prototype.
