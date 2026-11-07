# W330 — Arc Staff / Spectral Blades source motion

User request: replace unnatural cast and melee motions with the supplied Destiny-Light-Abilities-2026-10-28 originals. Integration checkout: `/Users/qf/IdeaProjects/DestinyGuardians`.

## Implementation

- Both source `.blend` files were evaluated read-only in separately owned headless Blender processes. Source hashes, action mappings, coordinate conventions and representative evaluated source/retarget images are under `art/animation/w330/{arc_staff,spectral_blades}`. Downloads originals were not saved or edited.
- Arc restores full source cast lengths, ground weak1/2/3, air cast and air attack. The old .50s cast and .35s first attack compressed 1.433s / 1.30s originals. Existing Arc idle/move remain.
- Spectral replaces cast, air cast, three light stages, air light/third and separate ground/air heavy clips. Source wrist roll is independent of arm IK; pelvis/chest/head motion is separated. Heavy previously selected the third light clip. Source guard and upper-body movement are included.
- Authored quaternions are baked through opt-in shortest-path slerp to the existing BetterModel 40Hz sample grid, with continuous equivalent Euler branches. Legacy clips retain their existing path. This is not a claim of original-game or 60fps-perfect reproduction.
- Source duration, short entry/exit blending and per-clip contact/recovery drive playback and the attack gate. Contact beats are provisional kinematic cues: original damage-event semantics were not decoded. Existing damage values, session ownership, wall/LOS checks, one-contact ledger and movement validation were preserved.
- Arc snapshots accepted grounded state, as Spectral already did, so the longer source windup preserves the intended 2-block ground / 5-block air step when landing before contact.
- New content-addressed limb model names preserve existing installed artist models. Missing or malformed overlays fail explicitly instead of silently selecting old clips. Body geometry, group UUIDs and UVs remain unchanged.

## Actual checks

- Real Java25 Gradle `assemble compileGametestJava test --tests '*MeleeSuperAnimationW330Test' --tests '*SourceAnimationGridW255Test'`: passed, 10 JUnit tests.
- Central real GameTest server: 25 total including framework always-pass. All 8 non-H20 product cases passed (W329 area/ground-air movement/ownership, W276 speed/step, W265 resistance). Nine H20 assertions initially failed; `initial-gametest.xml` retains those failures.
- H20 failures were stale raw-vs-PvE-scaled damage and transient inherited dodge-camera expectations. Test-only followup uses current `PveDamageBalance.scale(...SUPER...)`, enough target HP for two contacts, and verifies Golden Gun does not acquire/replace the inherited camera and that the old dodge camera releases. The embedded fixture sends normal rotation heartbeat across the longer recovery to preserve the established camera watchdog contract.
- One isolated actual H20 rerun with normal BetterModel/Polymer initialization: 16/16 H20 + framework always-pass = 17/17 passed. `h20-followup.xml` and `h20-tested-input-hashes.json` identify that exact runtime. No production damage/camera change was made to satisfy the fixture.
- Native input and actual framebuffer evidence were collected by master on the existing authorized isolated QA client/server (`127.0.0.1:25610`, Vision8102, DevilsQA), using its already authorized background mode. Workers did not operate that client/lease.
- First baseline: Arc and Spectral screenshots were reviewed and passed to the source/runtime workers. The short-floor `baseline-arc-clean` attempt fell into terrain and is explicitly discarded in `baseline-review.json`.
- Second Vision: `arc-ground` cast + three lights moved exactly6 blocks; `arc-air` air cast/attack moved5. `spectral-ground` cast + three lights + heavy moved8. `spectral-air` exercised air cast and air heavy but one light request was rejected during recovery; it is not counted as full air-chain coverage. `spectral-air-chain` used longer gaps and confirmed three accepted air contacts at x305.5/310.5/315.5, followed by ordinary forward movement.
- The `*-sheet.jpg` files are contact sheets of actual PNGs, not synthetic source renders; matching JSON contains bracketed states. Representative full PNGs are preserved. Capture spacing (~0.28–0.5s) and FPS snapshots do not certify every subframe, frame percentiles or speaker output. Heavy cloak hides the ending grip, so that phase cannot be fully judged from the invisible body.
- Observed Spectral rolls match original actions; reviewed frames show no independent wrist flip, detached knife or forced-neutral endpoint. Original Steve limb thickness and particles can still visually crowd forward hand poses.

## Final refinement / lifecycle

A short Arc head/staff intersection was identified during second review. The first minimum-distance correction removed sampled intersections but could change its correction vector by .293 blocks between source samples. It was rejected before native acceptance because the request prioritizes smooth motion. A final continuity refinement and its exact native recheck are recorded in `validation.json`; second-Vision screenshots above intentionally preserve the pre-clearance observation.

The normal HUD was restored, the QA-only resistance effect cleared, native input released and the self camera restored before stopping the owned QA server/client for the final build. No general Minecraft profile, user Blender/Blockbench scene or original asset was changed. Raw evaluated-source caches remain local and are not required by runtime.

Final accepted native check: `arc-final-clean` on `guardian_hunter_w330_0ccfcf11254d` (Arc overlay `849f4adf…`) confirmed cast/light1/light2 and recovery with4-block total movement. Reviewed actual full PNGs and contact sheet show the intended clearance with no obvious new snap. An earlier nighttime attempt was disturbed by ordinary mobs/explosion and is preserved but discarded; the owner downed afterward, so the fixture was reset through a dimension transition, then tested in daylight with QA resistance. The test floor was repaired and resistance/HUD restored afterward. This remains a bounded visual acceptance, not every-subframe collision certification.
