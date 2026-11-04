# W206 Dust Rock Blues — first-person calibration

## Observed issue and evidence

W205 uses the common shotgun hip transform `translation [-0.65, 0.6, 0]`,
`rotation [-1, 2, 0]`, `scale 0.98`; no Dust Rock Blues override exists.
`scripts/rig_arms_w205.py` currently replaces an idle/ADS left contact with
source wrist separation for non-bows. That separation belongs to the source
rig, whereas the remodeled pump already has its own W201 mesh contact.
The shotgun rig is a non-fallback binding explicitly listing this weapon:
`art/weapons/w205/rigs/shotgun_2eb0529e.json`, idle `80A8A3C2`, ADS `80A8A3C5`.
Its ordinary elbow-to-wrist lengths remain unchanged. `cameraExported` is false;
all profile values below are authored calibration, not a recovered camera.

Read `scripts/first_person_framing_w205.py`, `scripts/rig_arms_w205.py`,
`scripts/build_first_person_hands_w201.py`, `scripts/skin_arm_models_w204.py`,
`scripts/generate_surface_w123_dust_rock_blues.py`, W201 contacts, and the W123
model/design. No generator was executed.

Actual PNGs viewed:

- `art/weapons/w123/dust_rock_blues/comparison.png`: actual default-paint photo
  plus side/front/rear/bore source-remodel comparison. Photo provenance:
  https://www.bungie.net/common/destiny2_content/screenshots/636912560.jpg
  and `art/weapons/w31/references.json`.
- `docs/qa/2026-10-26/w148/native/frames/w148-final-dust_rock_blues-hip.png`:
  historical gun-only lower-right hip composition; long shroud and pump are
  visible, stock crosses right/bottom crop. This predates W205 skin arms and
  is not a current W206 result or proof of a current arm defect.
- `art/weapons/w178/first_in_last_out/reference-01.png` (26.4s) and
  `reference-06.png` (27.6667s): actual related-shotgun gameplay; support hand
  beneath the fore-end, forearm entering from below, then underside handling
  during shell insertion. Source https://www.youtube.com/watch?v=5IZfs2bjrYY
  and `art/weapons/w178/first_in_last_out/motion-reference.json`.
  This is First In, Last Out, not Dust Rock Blues. It supports broad shotgun
  support/reload semantics only; its silhouette, exact grip coordinates,
  camera and timings are not copied.

## Concrete profile and contact retention

| Field | Value | Reason |
|---|---|---|
| `translation` | `[-0.9, 0.45, 3.5]` | Move gun and attached hand frames 3.5 model units toward camera rather than lengthening arms; add 0.25 inward relative to W205 and reduce upward shift by 0.15 for the long raised shroud. |
| `rotation` | `[-1.5, 2, 0]` degrees | Retain established small yaw; add half a degree downward hip pitch to limit rail intrusion when brought closer. |
| `scale` | `0.98` | Retain W205 scale; do not enlarge the arms to repair framing. |
| `sourceViewRotation` | `[0, 0, 0]` degrees | Retain the existing explicit X-forward/Z-up rig mapping and actual arm approach directions; no extra camera claim. |
| `keepMeshSupport` | `true` | Preserve the remodeled pump contact at idle/ADS rather than overwriting it with source wrist separation; source directions and lengths still apply. Requires the master-owned loader/retarget support. |
| `hideSupportAtRest` | `false` | A shotgun retains its support hand under the fore-end. |
| `contacts` | `{}` | Inherit all W201 contacts and reload policy unchanged. |

The W201 right contact `[8, 7.9, 11.42]` belongs to `Ivory_grip`.
The left `[7.8, 8.52, 0.7]` is below `Foreend_black_core`, which occupies
Y `8.775..9.465`, Z `-1.57..3.05`. No mesh evidence calls for moving these
landmarks. The fixed receiver `Loading_floor` spans Z `4.8..9.4` and retains
reload contact `[7.3, 9.15, 7.1]`, rotation `[0, 0, -80]`,
`partHint: loading_port`, `policy: shell`.
Do not parent that fixed port to the pump or an incidental moving payload.
No palm lowering, wrist fallback, arm-length or extension overrides are added.
The source rig overrides arm directions; existing family fallback rotations
remain available when no source rig applies.

Hip translation/rotation/scale fade to identity through ADS. There is no
`cameraDepth`, so this profile does not move accepted full-ADS weapon matrices.
`keepMeshSupport` intentionally retains the hand's mesh target in ADS as well.

## Retained model and checks

The current full weapon model has **97 emitted solid cuboids** (one full
representation; no additional magazine assembly), 0 triangle adapters.
Long red shroud, ivory stock/grip, silver six-rib pump, dark inserts, open bore,
lamp and open sight notch remain intact. Surface geometry/UV/texture, sight
and ADS geometry, third-person display, audio, combat and reload timing are
outside these two owned files and were not edited.

Checks performed: profile JSON parses with schemaVersion 1 and correct weapon;
framing keys match the supported interface, no cameraDepth/extension fields;
contacts are inherited, including loading_port/shell. Source model still has
97 elements. Seed input identity and owned-file scope were checked before
handoff. These are simple source checks, not regenerated/native acceptance.

## Pending master's consolidated native check

- Settled hip in both supported hand contexts: gun and both fingerless
  player-skin arms move together; right forearm enters from lower-right,
  left forearm enters from below and ends beneath the black/silver pump.
  Check open elbow ends crop naturally with ordinary rig length, no floating
  hand, shroud penetration, detached shoulder-looking slab or sight occlusion.
- Slow hip-to-ADS-to-hip: correction fades continuously; full-ADS sight remains
  aligned and weapon matrices retain the accepted endpoint. Left palm remains
  on the remodeled pump while idle/ADS source directions remain usable.
- Partial and empty per-shell reload: support releases from pump, approaches
  the fixed loading port for each insert, follows the existing shell phases,
  and returns beneath pump. Check interrupted reload recovery as well; no
  magazine-swap contact or attachment to pump/barrel/payload.
- Existing third-person presentation and sight/scope path remain intact;
  inspect for visible clipping during ordinary equip/fire/recovery.

No native verification, build, generator, Computer Use, Vision, server or DCC
operation was performed by this worker. Exact Dust Rock Blues gameplay camera
was not recovered; depth/pitch and near-plane clearance remain calibration
candidates pending that consolidated native check.
