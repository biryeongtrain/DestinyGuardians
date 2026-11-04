# W55 persistent sword stances — 2026-10-24

`guardian_sword_w55` inherits the entire W53 skin/equipment rig and all 29
animation objects (21 Hunter + 8 sword) as literal unchanged UTF-8 JSON bytes.
Exactly four loops are appended. The runtime sidecar has 12 clips: W53's eight
original sword objects, byte-identical and in original order, followed by four
loops. Every original attack length, key time, cue, transform and UUID is intact.

| Clip | Length (s) | Authored visual intention |
|---|---:|---|
| `h15_sword_idle` | 2.40 | W53 low ready with subtle breath and cape settling |
| `h15_sword_move` | 0.80 | alternating leg/knee gait, steady weapon carry, cape sway |
| `h15_sword_guard` | 1.60 | raised frontal blade, free hand up, defensive breath pulse |
| `h15_sword_air` | 1.20 | tucked knees, restrained torso motion and flowing cape |

Idle begins/ends at the exact sampled W53 ready pose, including fitted root Y.
Move alternates hips/thighs/knees and feet with restrained weapon carry and
cape follow-through. Guard holds a raised blade in front of the torso and a
raised free hand, with a small defensive pulse. Air keeps both knees tucked
while torso and cape move; it has no launch/fall trajectory. All four loops
have identical first/last values on every channel, including Euler angles,
root position and item scale. Seventeen authored poses per loop use linear
interpolation, with gradual sinusoidal changes and no full-turn Euler seams.

## Rig / root contract

All existing rig fields, elements, textures, UVs, equipment pivots, outliner,
bind transforms and inherited animation bytes remain unchanged. Only top-level
`name`/`model_identifier` become `guardian_sword_w55`. The original rig has 18
groups; the same 16 H15 bones animate in each new loop. Both item bind rotations
stay `[-90,0,0]`, both item scales stay 1, and the existing five native sword
models/display mappings remain pinned. H19 arm IK targets the equipment pivots;
H20 cancels torso/arm/bind rotation for the right item. With pinned native
third-person display Rx(+90), model blade +Y maps to item +Z; guard points
that direction upward and keeps both wrists in front (-Z).

Root rotation and X/Z translation are zero throughout all new loops. Root Y
is exclusively H15's lowest-skin-corner floor fit, keyed by H20 at 40 Hz
(including authored pose times), with move refined to 80 Hz for support-foot
crossovers. This applies to air too: its root correction
fits tucked legs to the same authoring floor; there is NO extra jump height,
bobbing offset, ballistic arc or entity motion. Move is an in-place gait;
static floor fit does not promise terrain contact, foot locking or no sliding.

## Existing reference boundary

No downloads or new external references. Reused only W53's already pinned W51
`official-manifest.json` and W52 `videos.json`, `mechanics.json`, and four
contact sheets. Inspected the W52 light and mixed aerial contact sheets locally:
torso/leg counter-motion and cape silhouettes are broad pose inspiration.
Aerial 124.8s is Warframe and excluded; 126.3/128.2/130.5s are Destiny frames.
Ultraclocked's *Destiny 2 vs Warframe - Sword Animations*:
<https://www.youtube.com/watch?v=tTjwM26ilgo> (uploaded 2026-04-21).
W52 also pins historical aggressive-heavy material by selFu:
<https://www.youtube.com/watch?v=5oHxtta-a_I> (2023-08-23); this is inherited
provenance, not evidence for these guard/idle loops or current mechanics.

All stance angles, gait/breath periods, guard pulse, knee tuck and cape curves
are authored adaptations, not exact Destiny 2 capture, traced timing or measured
animation. No input, damage, range, energy, grounded flag, activation policy or
per-frame sword behavior is inferred. Runtime selection/install/tests/docs
belong to main; no existing files, gameplay code or integration assets are edited.
No Gradle, Blockbench, Blender, native apps or client/server builds were run.

## Reproduce / verify

`rtk proxy python3 -B scripts/build_sword_stance_w55.py`

`rtk proxy python3 -B scripts/build_sword_stance_w55.py --verify`

Verification is read-only, including no Python cache writes. It checks SHA-256
pins, all rig fields and all 29 inherited raw animation objects, old eight raw
runtime objects and timings, 33/12 counts/order, all 16 animated bones, UUID
uniqueness, finite transforms/FK, explicit unit item scales, unchanged item
binds, literal endpoint equality and bounded adjacent Euler deltas. At 200 Hz
it checks floor-fit error <=0.04 model units, frontal lifted guard/free hand,
tucked air knees, alternating moving feet, and nonstatic torso/cape motion.
Two independent generations must be byte-identical and match saved artifacts;
manifest includes input/output hashes (excluding its own hash). Static FK is
not rendered/native/terrain verification; main owns that downstream validation.
