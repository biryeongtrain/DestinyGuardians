# Pickup height and rifle announcement gate — 2026-11-02

## Changes

- Pickup markers imported from the source map can be inside the voxel floor or a low map box. Resolve the presentation anchor upward through up to three contiguous collision blocks, stopping at the first air gap. This uses the collision top (including slabs), keeps X/Z unchanged, and does not edit the map or pickup eligibility coordinates.
- Add 0.15 block of model clearance above the existing rifle/shotgun offsets. The cache crate, glow, particles and collection effect share the corrected presentation anchor. Weapon geometry, animation and resource pack assets are unchanged.
- ARM_YOURSELF stays locked until the actual `80b75f50` announcement finishes. The deadline is set when that exact line is dispatched, using the presentation return value including queue wait, not stage entry or earlier dialogue completion. The real Korean line is 66 ticks (3.2763 s audio).
- While locked, the objective says “고스트의 안내를 들으세요” with WAIT instead of GRAB. Resume before collection restarts the interrupted announcement and its gate. Missing voice uses the existing bounded 60-tick fallback; missing marker fallback cannot bypass the gate. Grants remain once-only.

## Verification

- Campaign targeted JUnit: 140 tests passed. Added tests for queued prior narration/actual announcement deadline, reconnect during speech, and missing-marker/voice fallback. Existing whole-mission test now allows the requested added dialogue wait, rather than assuming immediate collection.
- Full JUnit: 2460 tests, 2454 passed, six existing asset failures (GoldenGunHudW122AssetTest x2, WeaponSilhouetteW112AssetTest, InsertW179MindbenderTest, ReloadW168AustringerTest, WeaponSurfaceW115Test). No new failures; full suite remains non-green.
- Real Java 25 Gradle JAR, artifact.json records hash and bytes.

## Actual client/server QA

Copper Golem Vision 26.3, isolated Danmo copy at /tmp/destiny-reload-probe/run, isolated localhost QA server. Screenshots are actual inspected framebuffer PNGs. RCON stage setup/teleports and fixture enemy clearing were used; this is not a native-input combat acceptance test. Night Vision was applied temporarily to expose floor/box intersections, then removed. No speaker listening claim.

- Initial +0.6-block-only adjustment still left the rifle inside a map box (rifle-wait-first-pass.png); this failed visual review and was replaced with the collision-surface correction.
- Final rifle-raised.png shows the entire rifle above the map box, with the waiting objective and rifle-announcement subtitle. shotgun-raised.png shows the crate above the platform and the shotgun above its lid (viewed from its end). Both were reviewed after restarting against the corrected implementation.
- First live gate timeline (same final mission logic, before placement-only refinement): positioned within pickup reach, no weapon through 2.823 seconds; weapon present by 3.356 seconds. The line is 66 ticks. voice-trace.txt and rifle-gate.json record this. Final visual session also showed WAIT and no weapon during the line, followed by equipped rifle after it.
- Reconnect and malformed-marker paths were covered by JUnit, not repeated live. The visual fixture required returning to the combat area to load the last enemies before clearing them; remote unloaded mobs did not count as a cleared encounter. No production encounter behavior was changed.
- Cleanup: no active lease/held keys/pending steps; native movement neutral. Campaign aborted with escrow restoration, QA effects removed, owned server/client stopped. One-hour keep_awake coordinator used owned caffeinate PID 64640, then released. No general profile/security settings changed.

Only this batch's three source/test files and QA evidence are committed; unrelated existing work remains unchanged. No remote deployment.
