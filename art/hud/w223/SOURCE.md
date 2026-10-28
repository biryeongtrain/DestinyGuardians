# W223 confirmed weapon feedback: references and original art

Researched 2026-10-28. This is an original Destiny-inspired approximation, **not** extracted,
traced, or pixel-exact Bungie art. No external image pixels are generator inputs.

## Evidence and limits

- Bungie Help response confirms that hit markers remain a game feature and identifies
  Settings > Gameplay > Crosshair Feedback:
  <https://www.bungie.net/en/Forums/Post/264857129> (2025-07-15).
- Bungie's accessibility article says the enemy-target color setting also affects headshot-dot
  and hit-indicator UI. Therefore no single exact hit color is asserted for all original-game settings:
  <https://www.bungie.net/7/en/News/Article/destiny-2-accessibility-set>.
  Search indexed the relevant passage; the direct article fetch timed out in this research session.
- Bungie UI designer Bailey Kalesti's portfolio explicitly labels in-game Hunter/Titan/Warlock
  HUD screenshots. These are trustworthy **layout references**, not evidence for a hitmarker
  frame, hit/kill lifetime, or exact glyph dimensions:
  <https://www.baileykalesti.com/destiny-2>.
  Hunter HUD image:
  <https://images.squarespace-cdn.com/content/v1/54bea456e4b00aad29ea0032/3d25cf3b-cab9-4637-ab42-e4f3ce800972/Destiny-2_Screenshot_Stasis-HUD_Hunter.png>.
  Titan HUD image:
  <https://images.squarespace-cdn.com/content/v1/54bea456e4b00aad29ea0032/ffadc747-c1fa-4356-b9b9-c49e5918aef7/Destiny-2_Screenshot_Stasis-HUD_Titan.png>.
- The Destiny player discussion specifically describes a red hit-marker appearing on a kill:
  <https://www.reddit.com/r/destiny2/comments/drlbw0/colored_kill_number_idea/>.
  This is community corroboration of **red kill feedback**, not a Bungie specification.
  Its comment about white/yellow refers to **damage numbers**, so it is not used to invent
  a yellow precision-hit glyph or prove an ordinary-hitmarker palette.

White ordinary-hit feedback (#F1F3F5) is the local neutral/readability choice; red kill feedback
(#E85C50) follows the corroborated community convention. White ordinary-marker color is
not claimed as verified canonical Destiny color. There is deliberately no precision-yellow
state, target-hover red cue, damage speculation, or kill prediction. A recorded gameplay frame
sequence proving exact marker colors/timings was not obtained; that fidelity claim remains open.

## Authored glyph design

`scripts/generate_hit_confirmation_w223.py` generates two white RGBA masks with four tapered,
diagonal strokes and an open center. Custom-model-data tint supplies white hit / red kill.
Kill strokes are longer and thicker, so emphasis is not color alone. One stable 64x64 HUD plane
at (960,540), layer8, presents either mask above the hand; it does not move the existing reticle.
The transparent center contains at least a 14x14 square in both masks. Full transparent
padding keeps the cue compact; 64 is the plane size, not the opaque marker width.

The 4-tick hit and 7-tick kill lifetimes are **authored policy**, approximately 200/350ms
at nominal 20 TPS. They are not measured original-game constants or wall-clock guarantees.
No animated growth/fade or timing precision beyond server ticks is claimed. Repeated ordinary
hits refresh white. While red is alive, ordinary pellets are coalesced away and cannot extend red;
another confirmed kill may refresh it. There is no queue, extra dot, fullscreen wash, or sound.

Schema follows this checkout's `reticle_w44_dot` item/model pair: `minecraft:model`,
custom-model-data tint index0, front-lit flat two-sided north/south quad at z8.
The deterministic stdlib-only generator writes exactly six owned assets plus its manifest.

Reproduce from the reusable slot:

```sh
rtk proxy python3 scripts/generate_hit_confirmation_w223.py
rtk proxy python3 scripts/generate_hit_confirmation_w223.py --check
```
