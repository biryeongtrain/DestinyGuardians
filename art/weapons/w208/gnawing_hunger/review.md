# W208 Gnawing Hunger framing and continuous reload

Worker deliverable for master integration; no native gameplay verification, build, shared QA, or live DCC session was performed.

## Inspected references and limits

Read the weapon art design skill and Ace/Izanagi study. Opened the actual W123 `art/weapons/w123/gnawing_hunger/comparison.png`: default-photo charcoal receiver/skeleton stock, white patterned bindings, recessed brass quatrefoil fore-end, true stock/trigger/sight openings and deep muzzle remain the identity. Read its design/review and the current effective `models/weapon_surface_w123/gnawing_hunger.json`. This task preserves that geometry and atlas rather than redesigning it.

Opened `art/weapons/w164/gnawing_hunger/storyboard.png` and read `motion-reference.json`. The twelve cached gameplay frames cover 25.900–27.275 seconds of [JMPDoubleX gameplay](https://www.youtube.com/watch?v=3XU0AygDiKI). ADS departure is visible by 26.150s, raised/rolled handling by 26.275s, an exchange plateau around 26.400–26.650s, seating around 26.775s, then lowering and recovery. Hands and the lower screen obscure magazine travel. The red shader is excluded; the existing default paint remains. These are existing reference images, not native captures of this candidate. Reload modifiers in the video do not establish gameplay duration. W164 normalized authored knots are retained exactly; no frame-exact extracted trajectory or camera is claimed.

Read `art/weapons/w205/rigs/auto_rifle_943c13a2.json` and the read-only source-map on the supplied Animation-Return volume. This non-fallback group explicitly lists four Gnawing Hunger variants, including API hash 821154603. It exports idle `80A8A422`, ADS `80A8A330`, and three actions `80A8A395` / `80A8A38C` / `80A8A38A`, all labeled `reload_full` plus `reload_empty`, each with 21 sampled frames over source frames 1–105. There is no per-weapon selector resolving these three actions. Select **80A8A395 as direction calibration only**. The source has no exported camera. Ordinary source forearm lengths from idle are approximately 8.14136 model units for both sides after the existing ×32 mapping; no length override is introduced.

Read W201 contact evidence, shared framing/rig application, W206 Ammit's profile as a schema/calibration pattern, W164's original rigid transform and W207 Ammit's continuous PCHIP implementation. W206 Ammit's native framing observations do not prove a Gnawing Hunger framing defect or justify copying its larger offsets.

## Candidate profile

`schemaVersion: 1`, weapon `gnawing_hunger`:

- Framing translation `[-0.7, 0.75, 1.0]`, rotation `[-2, 1.5, 0]`, uniform scale `0.98`. Relative to the auto-rifle default, the translation changes by `[-0.05, +0.15, +1.0]`, pitch by −1 degree and yaw by −0.5 degree. This is a modest inward/upward/closer placement of the complete gun/contact assembly for master tuning, without dramatic framing claims from unavailable native evidence.
- `sourceViewRotation: [0, 0, -4]` is a small rig direction/twist calibration; it affects arm orientation in ADS too and needs inspection. It does not change source joint distances.
- Mandatory `keepMeshSupport: true`; `hideSupportAtRest: false`. Retain W201 right contact `[8, 8.65, 8.28]` / `[-19, 0, 0]` on the cloth grip, and left `[7.8, 9.42, -1.4]` / `[0, 90, -85]` below the fore-end lower spine. No palm/forearm extension or stretch is requested.
- Reload override uses `rigAction: 80A8A395`, inherited magazine-middle contact `[7.4, 6.7, 3.35]` / `[12, 0, 0]`, `partHint: moving`, `policy: magazine`. The moving-part suffix agrees with the generator; the master hand builder follows that actual detached display through extraction and seating, then releases to the support anchor.

Under shared framing policy, hip translation/weapon rotation/scale fade to identity at full ADS and apply equally to weapon and hand contact frames. No camera-depth field or arm-only scale is added. Existing source wrist separation must not overwrite these mesh contacts. Master owns loading all W208 profiles and extending the shared rig whitelist with Gnawing Hunger and the three audited alternatives; the chosen profile action remains 395.

## Generator contract and preserved model

Required item model key: `destiny:weapon_reload_w208_gnawing_hunger/gnawing_hunger`.

`generate(root=ROOT)` returns absolute `Path -> bytes` and performs no disk writes. Import is also side-effect-free. The standalone stdlib generator uses W207's weighted-harmonic PCHIP slopes with W164's exact nine normalized knots. It retains nonzero velocity through monotone moving knots, zero endpoint/extremum velocities, the meaningful full handling hold at 0.38–0.50, and seated magazine spans at 0–0.12 and 0.74–1. Equal neighboring values return exactly constant channels, avoiding floating cancellation drift in holds.

The current surface contains **114 emitted opaque elements / 684 explicit UV faces**: **109 body + five magazine**, indices 54–58 (`neck`, `upper`, `middle`, `lower`, `floorplate`). The full surface and split are alternative representations, not 228 simultaneous elements. Generated static parts preserve every source element, face UV, texture reference and rotation record, and omit parent display so a missing child pose cannot expose a misleading static idle. Child displays preserve W164's `GRIP [8, 9.2, 8.1]`, `R_idle * R_body` convention, local rigid magazine displacement, uniform scale applied once and twohand carrier compensation. Both grips restore accepted displays exactly at endpoints; non-first-person displays remain unchanged. No shell/insert lifecycle applies to this detachable-magazine weapon.

There are **61 poses / 60 intervals**, with thresholds exactly `float32(i / 60)` as encoded by runtime float arithmetic. Output is **248 byte blobs: 247 pack assets (two static parts + 244 parent/display pose children + one item graph) and the owned manifest**. All asset paths are new `models/weapon_reload_w208_gnawing_hunger/` or `items/weapon_reload_w208_gnawing_hunger/` paths. Explicit ADS/inspect mode cases, negative-progress fallback, non-first-person fallback and endpoint graphs preserve the exact canonical item graph, including both grip branches. Active hip samples use rigid body+moving composites. The mode cases are individual strings for compatibility with the existing hand builder's state propagation.

The worker writes only its five owned source/profile/review/manifest files. Generated pack JSON is **not materialized** here; master writes returned assets and owns runtime routing/common pipeline. The manifest is written solely from its returned output bytes. No gameplay duration, ammunition, audio or common runtime file changes. Sixty intervals improve the available pose bank; they do not prove 60fps or change server update cadence.

## Bounded validation

Target command from the isolated worktree:

```sh
rtk proxy python3 -B scripts/qa/test_motion_w208_gnawing_hunger.py
```

Final result: **11 tests passed** in 0.102s, exit 0, in the ready isolated worktree. The seed private metadata was resolved through the `.git` pointer and reported `ready`; baseline `88016d66f31edad0791e20b7689f14adeccecc4063b67c39a2e8af2622fc7577` and relevant canonical/contact/rig inputs were verified before the first worktree write. The owned manifest was then written from `generate(root=ROOT)` returned bytes; all 247 pack outputs remain unmaterialized.

Eleven stdlib tests cover exact W164 keys/pivot, import/generate disk-mutation guards and deterministic outputs, owned absolute paths and model references/hashes, unchanged 109+5 geometry and all UV faces, accepted endpoint displays for both grips, non-first-person displays, float32 dispatch at every interior sample, exact non-FP/ADS/inspect/negative/end fallback behavior, finite bounded monotone curve spans, C1 one-sided knot velocities and zero endpoint velocities, exact handling/seated holds, rigid grip-pivot invariance and detached-magazine transform, profile anchors and ambiguous source-rig metadata. No historical screenshot dependency is needed by generation/tests. Native load/performance/skin rendering and shared route activation remain outside these Python results.

## Master Vision scenes still required

1. Classic and slim skins, both dominant grips: hip ready plus brief firing/recovery; grip and fore-end contact, normal-length forearms entering viewport edges, muzzle/optic composition, no receiver penetration or floating cuff. Compare before/after as this framing is intentionally conservative.
2. Hip → intermediate ADS → full ADS → hip, including ADS during stale reload progress: accepted centered sight and fallback, source-roll wrist clearance, no sudden contact jump.
3. Partial and empty magazine reload: left hand reaches moving magazine, follows rigid extraction, holds through 0.38–0.50, seats at 0.74 and releases/returns without endpoint snap. Check contact from both grip carriers, detached-magazine cropping, and interruption/weapon-switch recovery under the shared runtime.
4. Representative third-person/non-FP fallback and brief 10–20-weapon display observation after integration. Python equality is not a native load or performance claim.

Native review and final batch QA belong to master; no native-verified result is asserted.
