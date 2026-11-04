# W206 Ammit AR2 first-person calibration

Candidate profile for the master-owned modular loader and consolidated native review. No new native session, generation or build was run by this worker.

## Observed issue and source evidence

Opened the actual `docs/qa/2026-10-27/w205/screenshots/w205-ammit-hip.png` (1708×960): the support arm reaches the forward underside almost vertically, and its pale cuff ends inside the viewport around y920, above the bottom edge. The broad receiver sits to the right; the rear peep is low relative to the gameplay reference. The W205 reload sheet was also opened; its recovery repeats the exposed cuff. These are existing W205 images, not images of this new candidate.

Opened `/private/tmp/w205-reference-view/ammit-46s.png` (1280×720), from the existing cached `/private/tmp/destiny-w69-reference/w3CYQprLoc0-first65.mp4`. Source: [xHOUNDISHx gameplay, 46s](https://www.youtube.com/watch?v=w3CYQprLoc0&t=46). The support forearm enters diagonally from the bottom to the lower front of the gun. This is hip-ready between attacks, not proven stationary idle. Its taller golden optic differs from the existing model's OMOLON peep, so only broad gun/forearm composition informs this calibration; that optic is not copied. `docs/qa/2026-10-27/w205/reference-audit.md` records provenance and approximate ranges.

Opened `art/weapons/w69/references/ammit-reload-contact.jpg`: 23.95–25.15s and 49.6–50.35s show receiver/magazine handling, not idle placement. Opened `docs/qa/2026-10-27/w205/screenshots/w205-ammit-reload-sheet.png` for the current extraction/recovery presentation.

Read `art/weapons/w205/rigs/auto_rifle_943c13a2.json`: exact non-fallback Ammit group; idle `80A8A422`, ADS `80A8A330`, source reload `80A8A395`. The normal wrist-to-elbow length is approximately 8.141 model units after the existing ×32 mapping. Keep that established rig retargeting unchanged. `scripts/rig_arms_w205.py` currently replaces the mesh left position with source wrist separation at rest; the master-owned `keepMeshSupport` branch must retain the authored remodeled-gun contact instead. Source FK establishes directions/lengths, not a recovered camera. No new source-reload retargeting is requested: this gun retains its existing W69 magazine handling.

Read `scripts/build_first_person_hands_w201.py`, `scripts/first_person_framing_w205.py`, `scripts/skin_arm_models_w204.py`, `scripts/generate_reload_models_w69.py`, the Ammit surface generator and `scripts/generate_sight_bodies_w151_rifles.py`. Existing reach/reseat/release uses the moving magazine display and must remain active.

## Exact candidate values and purpose

- `translation: [-0.75, 1.2, 3.25]`, replacing auto-rifle `[-0.65, 0.6, 0]`: +Z brings the complete gun/contact assembly toward the camera so ordinary-length arms continue toward the viewport edge; modest inward/upward placement compensates the pitch change. This is a native-tuning candidate, not proof the cuff is now cropped.
- `rotation: [-5, 1, 0]`, replacing `[-1, 2, 0]`: modest extra negative pitch raises the rear relative to the forward barrel; reduce yaw slightly to limit broad side presentation. Check the muzzle and rear peep together in native review.
- `scale: 0.98` retains the family value. It is uniform presentation scaling; there is no arm-only scale or length override.
- `sourceViewRotation: [0, 0, -8]`: small clockwise approach/twist calibration helps the source left forearm approach diagonally from below-left. It calibrates rig direction only and also affects arm orientation in ADS; native wrist clearance remains pending.
- `leftPalmLower: 0.5`: lower the solid fingerless palm slightly beneath the retained blue support beam. This offsets contact-frame Y clearance; it does not alter mesh or forearm length. Reload still follows its existing magazine target.
- `keepMeshSupport: true`: preserve remodeled front underside contact rather than overwrite it with source wrist separation in idle/ADS. `hideSupportAtRest: false`: automatic rifle remains visibly supported.
- `contacts: {}` deliberately inherits W201: right `[8, 8.95, 8.3]` / `[-28, 0, 0]`; left `[7.8, 8.72, -3.8]` / `[0, 90, -85]`; reload `[7.4, 6.85, 2.68]` / `[-16, 0, 0]`, `partHint: magazine`, `policy: magazine`. The actual `Lower_blue_beam`, `Grip_backstrap` and `Magazine_body` bounds still warrant these anchors. No invented contact, arm-extension or cameraDepth field.

All translation/weapon rotation/scale changes are hip-only and fade to identity at full ADS under the existing framing policy. Existing full-ADS gun matrices, sight/scope passage, third-person displays, surface geometry, audio and combat are outside this edit. The profile's source-view rotation and palm clearance affect arms, and require ADS inspection even though the gun matrix stays fixed.

## Retained identity, geometry and checks

Retain the long blue OMOLON receiver and lower beam, fluid chamber/rims, open structural space, sloped grip, independent magazine and existing rear peep. `art/weapons/w123/ammit_ar2/manifest.json` reports 121 body + 5 magazine = 126 surface elements; direct current model JSON agrees. Existing sight assembly is 128 elements (123 body + 5 magazine), unchanged. The existing W201 generated manifest records a peak assembled presentation budget of 423 including its active parts/skin arms; that historical generator result is not a newly regenerated W206 count. This profile adds no geometry.

Checks completed: JSON parses with supported framing fields and finite numeric vectors; weapon/schema match; inherited contact anchors and the exact non-fallback rig are present; surface/sight element counts read directly; selected main source/contact/model/reload hashes remain unchanged across this edit. Only the two owned W206 files are written in the private ready worktree. No generator, build, native, Blender/Blockbench or UI operation was run.

## Pending master native review

1. Hip ready with classic and slim player skins: both wrists contact the correct grip/lower beam, left forearm enters from the bottom-left without exposed cuff termination, right forearm enters lower-right, no lengthening, floating palm or receiver penetration. Compare muzzle, rear peep and support wrist simultaneously against W205.
2. Hip → intermediate ADS → full ADS → hip, including the existing scope route: preserve the accepted centered sight/weapon alignment, clear the sight passage with both palms, and check the new rig roll for block-arm clipping or sudden hand-position jumps.
3. Empty and partial magazine reload: left hand releases lower beam, reaches/follows magazine during extraction/reseat, releases and returns to the retained beam contact without a final-frame snap. Check the +Z move does not crop the moving magazine or right hand excessively.
4. Brief fire/recovery and a third-person spot check after integration. Third-person values are unchanged by design; this worker has not visually reverified them.

No native success or exact original-camera recovery is claimed. Master may adjust this bounded calibration after integrating all five profiles.
