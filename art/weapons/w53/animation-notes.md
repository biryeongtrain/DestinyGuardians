# W53 sword animation sidecar — 2026-10-24

`guardian_sword_w53`: unchanged full H26-r2 skin/equipment rig, 21 literal-byte
inherited animations plus exactly eight new `h15_` clips. Runtime export contains
only the eight sword clips; it is not an inherited-super animation replacement.

## Authored clip-local cues

All values below are authored visual timing, not measured Destiny 2 timings,
server ticks, collision windows, input evidence, or automatic animation events.

| Clip | Length (s) | Contact/release cue (s) | Visual intention |
|---|---:|---:|---|
| `h15_sword_light_1` | 0.45 | 0.15 | right-to-left horizontal cut |
| `h15_sword_light_2` | 0.50 | 0.20 | left-to-right horizontal cut |
| `h15_sword_light_3` | 0.55 | 0.20 | broad right-to-left low finisher |
| `h15_sword_uppercut` | 0.85 | 0.35 | low-to-high uppercut |
| `h15_sword_dash` | 0.75 | 0.25 | forward drive silhouette; stationary root |
| `h15_sword_slam` | 0.95 | 0.40 | overhead-to-low slam; no jump |
| `h15_sword_vortex` | 1.05 | 0.45 | one visual yaw turn; no gameplay facing change |
| `h15_sword_caster` | 0.80 | 0.30 | blade sweep/release silhouette; no projectile asset |

Lights alternate right/left/right with a lower, wider third-cut finisher.
Linear keys give anticipation, fast slash, brief follow-through, and recovery.
Each clip uses all 16 animated rig bones, including hips/waist/chest, head,
legs/knees, both arms/forearms/items, and cape. Start/end silhouettes agree
modulo 360 degrees; vortex alone finishes one continuous visual root-yaw turn.

## Held-item contract / motion boundaries

- Existing `pri_right_item` is the right-hand weapon pivot. Both item bind
  rotations stay `[-90,0,0]`; no added sword, model, element, texture, or UV.
- Existing five native sword models retain third-person right-hand display
  rotation `[90,0,0]`, translation `[0,2,0]`, scale `[0.9,0.9,0.9]`.
  Their paths/SHA-256 are pinned in the generator/manifest. The clips compensate
  torso/arm/bind rotations with the existing H20 right-item helper, not a new
  runtime model mapping. Item scales stay 1; the free hand is not a staff grip.
- Root X/Z position is always zero. Dash is only a forward-drive body silhouette.
  Vortex yaw is visual animation only, not entity/camera rotation or targeting.
- Root Y is ONLY H15 skin-floor fitting, sampled at 40 Hz by H20. No jump,
  airborne arc, lunge displacement, gravity, projectile, physics, hitbox, damage,
  energy curve, camera code, or grounded/air activation policy is implemented.
  200 Hz static verification bounds floor-fit interpolation error; this is not
  rendered/native-client/terrain validation. Air variants are not claimed.

## Reused evidence (no downloads)

Visually inspected all four existing `art/weapons/w52/references/*contact.jpg`:
light (0.7/1.7/3.0/4.5s), heavy (143.9/144.3/144.7/145.1s), aerial, aggressive-heavy.
Source metadata and clip/still hashes remain in W52 `videos.json`; input hashes
are repeated in the W53 manifest without editing W52.

- Ultraclocked, **Destiny 2 vs Warframe - Sword Animations**, uploaded 2026-04-21:
  <https://www.youtube.com/watch?v=tTjwM26ilgo>. Light/body counter-rotation,
  planted low cuts, cape follow-through, and dash lean are pose inspiration only.
  Aerial 124.8s is **Warframe and excluded**; 126.3/128.2/130.5s Destiny poses do
  not prove inputs, current restrictions, frame identity, or world-unit motion.
- selFu, **You can now double heavy attack with Aggressive Frame Swords**,
  uploaded 2023-08-23: <https://www.youtube.com/watch?v=5oHxtta-a_I>.
  Historical 48.7/50.0/51.4/53.0s slam silhouette reference; predates October 2023
  fix. No assumption of a double-heavy mechanic, verified hash, or present rules.
- Official heavy *shape labels* are from pinned W51 `official-manifest.json`
  (manifest `245114.26.10.13.2000-1-bnet.66137`) and W52 `mechanics.json`:
  Abide/uppercut, Goldtusk/dash, Crown-Splitter/slam, Guillotine/spin,
  Temptation's Hook/projectile. These sources do not measure these authored poses.
  Uppercut/vortex/caster choreography is semantic authoring, not a traced capture.

Every joint angle, blade arc, pose, contact cue, transition, and recovery curve
is authored. No exact D2 distance, hit count, damage, attack time, energy curve,
air flag, or input is inferred from stills. Main owns runtime/camera integration.
No Blockbench/Minecraft/Gradle/native app was run; held-item render alignment and
camera behavior still need main's downstream native-client validation.

## Reproduce / read-only verify

`rtk proxy python3 -B scripts/build_sword_animation_w53.py --verify`

Verifies pinned input bytes, every rig field's raw bytes, each inherited clip's
raw bytes/order, required bones, finite transforms/FK, timing caps, root/scale
policy, endpoint recovery, runtime-only-eight export, and two independent
byte-identical generations. Only the five declared W53 paths may be written;
`--verify` compares saved outputs and writes nothing (including no pycache).
The manifest hashes the generator/model/export/notes, excluding its own hash.
