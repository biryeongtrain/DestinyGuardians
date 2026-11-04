# W213 Chattering Bone — FIRST native review

Status: FIRST reviewed from actual PNGs and server artifacts; SECOND pending master. No product correction is warranted by the reviewed evidence. Only this review changes; generator and profile bytes remain identical to the submitted candidate.

## Source, contacts and authored timing

Read main AGENTS.md, RTK.md, minecraft-weapon-art-design SKILL.md and Ace/Izanagi study before the candidate. Original Blender evidence was reviewed before61-pose generation: master evaluated source.blend with Blender5.4.0 Alpha; worker read the evaluation, source-map, bone parents/rest transforms, source61 matrices and actual upper-chain PNG. Action80A8A36A is Armature|fp_80A8A36A_reload_full|Base, OBSlot, frames1..105 at30fps,61 samples. Evaluation records ARMATURE only, old-cache joint error0 and allInputsUnchanged=true. This shared pulse-family selector establishes no weapon-exclusive action, source mesh or camera.

Retain pulse-family framing, sourceFullChain=true, keepMeshSupport=true and hideSupportAtRest=false. Current MAIN contacts remain right rest [8,8.15,8.67] / [-33,0,0], left rest [7.8,9.78,-1.6] / [0,90,-85], reload [7.45,7.7,11.95] / [15,0,0], policy magazine and partHint moving. Read current MAIN source_palm_translations: REST mesh offsets plus original weapon-relative FK determine palms; reload.contact positions the held part relative to that palm. No substitution of a reload target into rest contacts is warranted.

Keep exact W172 knots, grip/magazine-anchor algebra, all90 weapon elements and face UVs. Only elements59..61 (magazine_root/main/foot) move; body87 retains receiver, stock, grip and guard. Withdrawal starts after.19, reaches4.2 at.29 and holds through.48, approaches3.5 at.57, reseats at.71, releases through.78 and recovers by1. Body rotation stays near78–80 degrees during rear access. The FIRST raised-weapon and off-screen exchange views are consistent with this authored sequence and the source-chain exchange/recovery posture; they do not recover an exact source magazine path. Preserve original FK and ordinary forearm/upper-arm lengths without stretching, attenuation, hiding or a speculative framing shift.

## Actual FIRST image review

Viewed both screenshots/chattering_bone-review.png and screenshots/chattering_bone-reload.png, then separately viewed raw frames/w213-chattering_bone-reload-sample-00/02/04/06/08.png at1708x960.

- Hip: support hand lies below the barrel/forearm and leaves the central view open. ADS: centered optic aperture remains clear; the visible arms do not block the sight opening.
- Raw00: low starting/raising weapon posture before the rear-access hold.
- Raw02: purple moving magazine meets the left palm near the receiver/rear handling area. Right firing-hand contact remains visible on the weapon.
- Raw04: left handling hand is off below the image during exchange; the receiver and firing palm stay visible. A single off-screen still cannot establish exact hidden contact or justify changing source FK.
- Raw06: left hand returns alongside the rear handling area, with the purple handled piece visible at its palm; selected stills do not prove uninterrupted contact throughout the interval.
- Raw08: weapon lowers and support/rest posture returns during recovery. HUD ammo still reads0 in this still; final ammo restoration is established by server evidence below.

The tall raised muzzle is partly cropped at the top, while the receiver/palm handling area remains visible. This does not warrant changing the accepted family framing, contacts, knots or ordinary arm lengths. No generator/profile correction is made merely to create a delta.

## Server timeline and release basis

Parsed all18 WeaponPresentation rows from oracles/w213-chattering_bone-reload-timeline.json. Active reload rows use destiny:weapon_reload_w213_chattering_bone/chattering_bone with progress0.016666668,0.16666667,0.35,0.55,0.7,0.8666667 at ticks1929,1934,1940,1947,1952,1958. These are sampled live60-grid values; reloadDuration stays34. At tick1964 the item returns to destiny:weapon/chattering_bone, progress-1, reloading=false and ammo33/0; later rows remain restored. reload-finished.json confirms the same at tick2035.

native-validation.json records12 sequences across the four weapons, neutralAfter=true, and Chattering Bone fire/reload/ADS capture counts3/27/13, each released with all native movement flags false. frames/w213-chattering_bone-after-reload.json confirms the canonical hands item, leaseActive=false, heldKeys=[], pendingSteps=0 and usingItem=false. postflight.json also records released/neutral state. Master reports FIRST12 passed and shared integration complete; worker inspected these saved artifacts without operating Vision/CU, client, shared builds or generators. Capture indices are not asserted to map exactly to individual server progress rows. Sampled images/timeline do not certify continuous60fps, every intervening hand contact or audio listening.

## Correct assembly budget

The earlier538 calculation (candidate90 +224 classic forearm +224 classic upper-arm surfaces) describes a narrower candidate-bank estimate. It is NOT the master maximum across all emitted routes, including arms. Current MAIN art/weapons/w201/manifest.json records Chattering Bone maxAssembledElements=660, below1000. The same manifest records Lonesome684, Steelfeather Repeater687 and Aisha's Embrace665. These master values supersede the earlier broad budget wording. The unchanged candidate generator/profile still contain the narrower538 estimate; read that number only in its candidate-bank scope, never as all-route acceptance.

## Earlier limited candidate checks

Before integration, import and two in-memory generate calls under a write-rejecting open guard returned identical248 absolute Path->bytes entries (776113 bytes) with no writes. Exact W172 constants/knots, representative holds and interval bounds,87+3 geometry/UV/texture partition, canonical native/twohand endpoints, ADS/inspect priority, negative/non-FP routes,61 float32(i/60) thresholds and247 non-manifest output hashes passed. All61 rigid displays retained accepted scale; maximum adjacent Euler component step11.381789 degrees showed no branch flip. These historical checks were not rerun during this image review. They establish neither the master all-route budget nor final native acceptance.

## File scope and remaining gate

Bootstrap private metadata was confirmed before the three candidate files were copied into this assigned worktree. FIRST review changes only art/weapons/w213/chattering_bone/review.md. Generator/profile SHA-256 values below remain exact. No shared files, assets, tests, other weapon files or temporary evidence were modified.

SECOND Vision remains master-owned and pending. Recheck hip/ADS, rear handling/exchange/reseat and canonical return under the same scenario before final native acceptance. No recovered camera, weapon-exclusive selector, finger IK, audio-listening or continuous60fps claim is made.

## Evidence fingerprints

Runtime evidence base: /private/tmp/destiny-w213-pass1-native. The following files were read/viewed for this review.

- `screenshots/chattering_bone-review.png`: `6e1489ad05c23498d358c9a9b6b7e6e20b1a6fae4297c74bf00744397bc1ab8a`
- `screenshots/chattering_bone-reload.png`: `daa37226cbcc3100060e23382e2a35d41f39c96d960a201193fc97e14aeb16ec`
- `frames/w213-chattering_bone-reload-sample-00.png`: `f5a25367ce9e9f84820b11a2ee3637f7a2407259552fea75f604c4d00fbc5c0a`
- `frames/w213-chattering_bone-reload-sample-02.png`: `3c607e1d39acb23e1bb8d34052336e615e1aa9b85906aa6096970f952f61be17`
- `frames/w213-chattering_bone-reload-sample-04.png`: `b11226d6955e5742061ee4388bee17c00ebe13398937fc17ad314ec7c27aeba1`
- `frames/w213-chattering_bone-reload-sample-06.png`: `c2d13f70d140a796938ff03de1b2022849eb79544d28b1f5bd1b923b13c05f03`
- `frames/w213-chattering_bone-reload-sample-08.png`: `35295d00ded35a98b8f3d22b68d0b7c13b533d2f27aa780acc766cb9eca92709`
- `oracles/w213-chattering_bone-reload-timeline.json`: `7b561e7d1bb8f033864abcede184d9b20ff9623a9e8b054a65fb3711848009f6`
- `oracles/w213-chattering_bone-reload-finished.json`: `a732f3ac8866808e07dd77e98dd1824a05255e9efecb9936af0b4a9cf8c73fe3`
- `frames/w213-chattering_bone-after-reload.json`: `606493f23b0364b2426931b68689c21d1926f9456d92a7804465982e3d180fdd`
- `native-validation.json`: `e5dbafb2f51fe7b20b69a5df66584120eecab47eab915646ccc2f259049207cb`
- `postflight.json`: `979603d0f7b90265913e7ef943c1a52d4072be53599513d35becfeabbce98830`

Source audit/cache and current master budget evidence:

- `/private/tmp/destiny-w213-source/source-review.json`: `cc9ef72c7c7e85936f3cf9bc1ad521a46cfac15c48e891412b1cc15685066d7f`
- `/private/tmp/destiny-w213-source/pulse_rifle_b4d01502.json`: `23ddccddd8b3d7e0302f3bc7f7b2487c65ad10c55a18611c7505925bc014cc5f`
- `/Users/qf/IdeaProjects/DestinyGuardians/art/weapons/w201/manifest.json`: `519c1b8d22bbf7a83dae6a3e826814e370686a0e4c9a030083c97c353c387e3d`

Preserved candidate bytes:

- `scripts/generate_reload_w213_chattering_bone.py`: `f62fc99da46d49de30aa332a14a83fcbb29c03d91e772a1b4a33749b2688321c`
- `art/weapons/w213/chattering_bone/profile.json`: `bb52f88f76a3e4da2af85b9409d3b08d2f88a6f337bb1f2aa311a77ce5a0bda6`
