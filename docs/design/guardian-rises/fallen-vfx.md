# Guardian Rises — Fallen combat VFX (W300 r5)

The D2 Fallen particle textures are ported as short-lived Polymer item-display sprites in `campaign/fallen/FallenVfx.java`. Sounds are not touched; FallenSounds (r6) owns SFX. The existing vanilla particles in FallenWeapons and WalkerBoss stay in place as the fallback read.

## Source and pipeline

- **Source (read-only):** `/Users/qf/Downloads/Rising-Guardian-Fallen-AV-2026-11-01/Rising-Guardian-Fallen-AV-2026-11-01/`, from Charm 3.5.0, Steam build 25932352. The pipeline uses `particle-assets.csv` (particle tag → textures), `actor-effects.csv` (sequence → particles) and `vfx/png/<tag>.png`, the first-surface previews.
- **Generator:** `scripts/campaign/fallen_vfx.py`, pure Python and deterministic.
  - Each sprite is a white image whose alpha is the source luminance times the source alpha.
  - Quads get a soft radial edge; beams fall off across their full width.
  - Flipbook sheets use one cell (the `cell` column in the table).
  - The generator asserts that every cited particle really lists that texture in `particle-assets.csv`.
- **Outputs:**
  - `assets/destiny/textures/item/guardian_rises/vfx/<name>.png`
  - `assets/destiny/models/guardian_rises/vfx/<name>.json`, either a quad, or a beam made of two crossed planes along +Z. Both use `light_emission` 15, unshaded faces and tintindex 0.
  - `assets/destiny/items/guardian_rises/vfx/<name>.json`, tinted by the first `custom_model_data` colour.
  - `destiny/guardian_rises/fallen_vfx.json`, the table, with source and output sha256.
- **Colour:** the tint colours are ours (the archetype arc colours, Walker orange and smoke grey). D2's material colour and HDR parameters are not reproduced.

## Sprites (texture provenance)

| sprite | D2 texture | shape / cell | D2 particle@sequence |
|---|---|---|---|
| glow | 80D8A448 | quad | 80CEA1D8@80CEA1DB, 80A6DB04@80A6DB1C, 80A5ABFB@80A5AC46, 80A5AFC8@80A5AFDB |
| energy_ring | 80D8D777 | quad | 80CEA1BE@80CEA1DB, 80A5A2B8@80A5A2D7 (ring) |
| flash_star | 80D8A430 | quad | 80CEA676@80CEA54B (flash_round) |
| flash_jet | 80D899BF | quad (directional) | 80CEA693@80CEA54B (flash_long) |
| burst_star | 80D8A2AB | quad | 80CEA681@80CEA54B |
| shrap_round | 80D89B5C | quad, cell 2×2 (0,0) | 80A6DAED@80A6DB1C (flash_round) |
| shrap_long | 80D89DF5 | quad, cell 1×3 (0,1), directional | 80A6DAF1@80A6DB1C (flash_long) |
| cannon_jet | 80D8A0AD | quad, cell 1×3 (0,1), directional | 80A5A2C4@80A5A2D7 (flash_long) |
| fire_puffs | 80D8A3E4 | quad, cell 2×2 (0,0) | 80A6DAFF@80A6DB1C, 80A5A261@80A5A26D (fireball) |
| smoke | 80D8A3E7 | quad, cell 2×2 (0,0) | 80A5A268@80A5A26D (smoke), 80D92741@80D9274A (smoke_plume) |
| emp_arcs | 80D8A3AB | quad | 80A5AC02/80A5AC22/80A5AC2D/80A5AC45@80A5AC46 |
| contrail | 80D8A384 | beam | 80CEA182@80CEA22C (contrail) |
| bolt_core | 80D8D7D0 | beam | 80CEA193@80CEA22C. Shipped but not used yet: the contrail alone reads as the bolt. |

## Effect → hook → sprites

| effect (FallenVfx) | hook (one line) | sprites | D2 basis |
|---|---|---|---|
| `muzzle` ARC, Dreg | `FallenWeapons.bolt` | energy_ring, glow | shock pistol 80CEA1DB |
| `muzzle` ARC, Vandal/Shank | `FallenWeapons.bolt` | flash_star, flash_jet ×2 crossed, glow | wire rifle 80CEA54B |
| `muzzle` ARC, Walker AP guns | `FallenWeapons.bolt` | flash_star, flash_jet, glow | wire rifle 80CEA54B (scaled up) |
| `muzzle` ORB (Captain) | `FallenWeapons.bolt` | energy_ring, flash_star, glow | shock blast; reuses 80CEA1DB/80CEA54B |
| `muzzle` SHELL (Walker cannon) | `FallenWeapons.lob` | cannon_jet ×2, energy_ring, glow, smoke | Walker cannon 80A5A2D7 |
| `tracer` ARC | `FallenWeapons.trail` | contrail beam over the tick's segment (3 ticks, width 0.26 → 0.04) | 80CEA22C contrail |
| `tracer` ORB / SHELL | `FallenWeapons.trail` | glow / fire_puffs at the head | — |
| `impact` (player / block) | `FallenWeapons.step`, both non-splash hit branches | burst_star, glow | 80A6DB53/80CEA00A carry sounds only, so 80CEA681 is reused |
| `explosion` | `FallenWeapons.explode` (orb and shell) | glow, burst_star, fire_puffs ×2–3, smoke ×1–2; when big, shrap_long jets ×3 | 80A6DB1C / 80A5A26D fireball and smoke |
| `legBreak` | `WalkerBoss.legBroken` | big explosion, radius 2.2 | — |
| `walkerDeath` | `WalkerBoss.killed` | big explosion, radius 4.2, then emp | — |
| `explosion` (small) | `FallenMob.tickDeath`, Walker, every 9 ticks | radius-1.6 explosion | — |
| `emp` | `WalkerBoss.enter(STAGGER)` | emp_arcs gather (5 t) → burst, energy_ring, glow | 80A5AC46. The W300 Walker has **no EMP attack**, so this is the stagger discharge. |
| `weakpointExpose` | `WalkerBoss.enter(EXPOSED)` | glow, energy_ring, flash_star | 80A5AFDB bright_flash |
| `weakpointPulse` | `WalkerBoss.exposed`, every 4 ticks | glow | 80A5AFDB |
| `shankBurst` | `FallenMob.tickDeath`, Shank, deathTime 1 | shrap_round, glow, fire_puffs, smoke | 80A6DB1C |
| `shieldPop` / `shieldUp` | `FallenWeapons.shieldBreak` / `shieldUp` | energy_ring, emp_arcs, glow | 80A5A2D7 ring |
| `blink` | `FallenWeapons.blink` | glow + ring collapse at the origin; ring + glow at the arrival point | — |

## Runtime rules

- **Viewers:**
  - The effect is sent only to players within 48 blocks of its origin.
  - A player whose eye is within the effect's near-clip radius never receives it. The radius is 0.8–2.5 blocks, and for tracers it is measured to the segment. This stops screen-filling quads on the hit player or on a bolt passing their head.
- **Budget:**
  - At most 72 live sprites per player and 192 globally; above that, the effect is dropped.
  - Spawn packets go out in the creation tick. Interpolation starts on the next tick.
  - Each part grows from its start scale to its peak by `peakAt`, then shrinks to 8% and is removed at `life`. Lifetimes are 3–6 ticks for flashes and 10–30 for smoke.
- **Ticking:** FallenVfx self-registers its END_SERVER_TICK and SERVER_STOPPED handlers on first use.
- **Jets:** the model mirrors the south-face UV, so the image's left edge sits at model +X from both sides. The code rotates +X onto the shot direction, which assumes the vanilla item-display 180° Y turn. If jets point backwards in game, flip `axisX`.

## Not reproduced

- D2 shader stages: UV scroll, erosion/dissolve, HDR bloom, soft particles and flipbook animation (one frame only).
- Mesh particle 80CEA1B5 (`80D856D6.fbx`).
- Any sound.
