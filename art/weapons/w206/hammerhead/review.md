# Hammerhead W206 first-person calibration

This profile brings the weapon and attached fingerless player-skin forearms toward the camera as one assembly. It uses ordinary unchanged source-rig forearm lengths. All screen-placement values are authored calibration; the source has no exported camera or projection.

## Observed source and current issue

`art/weapons/w205/rigs/machine_gun_e5b72131.json` is Hammerhead's exact, non-fallback rig; `machine_gun_82e319a0` is Fixed Odds and is not substituted. Idle `80A8A00D` and ADS `80A8A00E` both give approximately 8.14 model units for each wrist-to-elbow segment. Retain those directions, twist and lengths.

W205 machine-gun framing shares the generic rifle values `translation [-0.65,0.6,0]`, `rotation [-1,2,0]`, `scale 0.98`. Its rig retargeter overwrites the authored support position with original wrist separation in idle/ADS. Before screen/carrier rotation, the source idle left-minus-right wrist delta maps to about `[-2.56,-1.21,-11.67]`, whereas the remodeled mesh contacts differ by `[-0.2,1.25,-11.78]`. Copying that separation pulls the palm sideways/down from the intended forward underside. `keepMeshSupport` preserves that mesh contact while retaining exact rig directions and ordinary lengths. No current Hammerhead W205 native hip image was found in the existing W204/W205 QA folders; this is a source/configuration diagnosis, not a measured native before/after claim.

## Actual references inspected

- `art/weapons/w114/hammerhead/reference-15.png`: actual 1280x720 gameplay, ready at 106.4s. Large receiver occupies the lower-right, optic remains above the receiver and hands are partly cropped/occluded. Supports a nearby heavy assembly, but the overlay, shader and moving scene do not establish exact FOV, palm coordinates or camera recovery.
- `art/weapons/w114/hammerhead/reference-08.png`: actual gameplay at 103.8s, with cover raised, feed/receiver exposed and partly occluded handling. Keep magazine handling separate from the cover hinge.
- Recording: [Aztecross Hammerhead guide](https://www.youtube.com/watch?v=1lHv7453rUI&t=101), 2024-04-25; existing `art/weapons/w114/hammerhead/gameplay-provenance.json` and `reference-notes.md` identify 101.50-106.40s as manual empty reload. No perk-refill narration is used as mechanism evidence.
- `art/weapons/w123/hammerhead/comparison.png`: actual viewed offline geometry/reference PNG. Confirms long charcoal roof/red rails, fork muzzle, twin drums, open stock/carry handle, hinged reflex sight cover and exposed linked rounds. This is not native verification.
- `art/weapons/w201/contacts.json`, W123 design and `scripts/generate_surface_w123_hammerhead.py`: right pistol grip `[8,8.5,7.98]`; left underside support `[7.8,9.75,-3.8]` below the gas cylinder (bottom Y 10.16); reload contact `[4.4,8.4,3.9]` at the drum outer wall. Existing geometry warrants retaining all three.
- Read `scripts/build_first_person_hands_w201.py`, `scripts/first_person_framing_w205.py`, `scripts/rig_arms_w205.py` and relevant W114 reload-generator paths. Weapon and contact displays share framing; reload follows the moving magazine, not the separately hinged cover.

## Exact profile values and retained geometry

`translation [-0.8,0.45,4.25]` replaces the generic hip framing: a modest inward/upward placement and positive Z dolly bring the heavy receiver and normal-length arms nearer the camera. `rotation [-2,1,0]` gives a small pitch adjustment and less added side presentation than the generic yaw. `scale 0.98` retains existing uniform scale. These are conservative reference-informed candidates, not pixel-fitted camera values. Translation, rotation and scale fade to identity at full ADS; no `cameraDepth` is present.

`sourceViewRotation [0,0,0]` retains the existing explicit rig-axis calibration. `keepMeshSupport true` holds the forward lower support on the remodeled gun at idle/ADS, and `hideSupportAtRest false` keeps the heavy support hand visible. No palm-clearance or wrist/contact override is introduced; W205 wrist fallbacks and W201 contacts/reload policy inherit unchanged (`partHint: magazine`, `policy: magazine`).

The existing W154 surface assembly remains **163 opaque cuboids: body 70 + magazine 79 + cover 14; no triangle adapters**. Full and split representations are alternatives, not summed twice. Eight rigid linked cartridges stay in the XY feed curve with tips toward muzzle -Z; the magazine opening, receiver feed mouth and cover-mounted sight/hinge remain intact. No geometry, UV, skin-arm mesh, ADS sight geometry, third-person transform, audio, combat or timing file is edited.

## Checks and pending consolidated native review

Checks performed: profile JSON parses, weapon/schema and supported keys are correct, all repository evidence paths exist in the ready seeded worktree, and source rig/contact/model inputs match their seeded hashes. Surface full-element count agrees with its body+magazine+cover count. Only the two owned W206 files are written. No generator/build/native client/server or user app was run.

Master integration must load the modular profile and honor `keepMeshSupport`; otherwise the existing retargeter still replaces the support contact. Native acceptance remains **pending master**:

- Hip idle/equip/fire: receiver and both skin arms move together; normal-length forearms enter from viewport edges or credible occlusion; no floating cuff, near-plane clipping or sight-blocking palm. Support bears the forward underside, away from the belt/feed mouth.
- ADS in/out and settled full ADS: hip dolly/rotation/scale disappear smoothly, accepted weapon/sight matrix remains unchanged, optic stays centered and the retained mesh support does not jump or intersect the feed/receiver. Check both hand-display contexts.
- Representative manual reload: right hand stays on pistol grip; left releases support, follows the actual moving magazine/drum target, clears the raised cover and returns to the forward underside without snapping. Preserve belt direction and magazine/receiver seating. Existing generic hand blend does not reproduce every source cover-handling gesture; do not claim recovered hand IK.
- Master representative third-person and 10-20-display observation: unchanged weapon surfaces/identity and no visible missing parts or new presentation breaks. Dynamic player-skin rendering and final clearance require native confirmation.
