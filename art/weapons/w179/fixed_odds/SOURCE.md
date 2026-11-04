# W179 Fixed Odds — source and motion authorship

The actual source is [Ultraclocked, Destiny 2 - Unseeing, to Be Shown - Weapon Ornament for Fixed Odds (Legendary Machine Gun)](https://www.youtube.com/watch?v=cy3DRqtgKC8). Although the title names the ornament, this is a **labeled default-versus-ornament comparison**. Only the **DEFAULT** view supplies this reload reference. No white/blue ornament paint, squared ornament sight, or unrelated Hammerhead clip is used. The 0.50s inventory frame reads FIXED ODDS and shows the canonical gold/purple default weapon. Its triangular sight, gold longitudinal receiver, purple rectangles/medallions, open black stock and side-fed copper belt agree with the canonical model and Bungie default image.

Actual 1280x720 frames were decoded and visually inspected at the exact source frame indices below (60fps). Original complete split frames remain outside product at `/private/tmp/w179-fixed-odds-report/reference-01.png` through `reference-12.png`. `storyboard.png` crops only the labeled DEFAULT panel (left or top as listed); independent authored orthographic views sit below. The raw source preserves both panels for context. No audio was evaluated. HUD-free comparison footage establishes mechanical actions visually, not magazine refill timing.

| Seconds | Source frame | Panel | Observed pixels | Nearest authored p |
| --- | --- | --- | --- | --- |
| 0.50 | 30 | identity full frame | Inventory title FIXED ODDS and gold/purple default weapon; identity frame. | 0.00 |
| 10.25 | 615 | left | DEFAULT left: closed top cover, triangular sight, linked belt into side box. | 0.00 |
| 10.75 | 645 | left | DEFAULT left: receiver presentation begins, cover still closed. | 0.05 |
| 11.50 | 690 | left | DEFAULT left: cover raised about forward hinge, sight travels with cover; exposed feed tray. | 0.20 |
| 12.25 | 735 | top | DEFAULT top: support hand holds box below exposed feed, cover remains raised; exact outgoing path occluded. | 0.35 |
| 12.75 | 765 | top | DEFAULT top: support hand returns toward exposed feed area; payload partly hidden. | 0.50 |
| 13.25 | 795 | top | DEFAULT top: hand places connected belt at feed tray, descending linked rounds visible. | 0.62 |
| 13.75 | 825 | top | DEFAULT top: palm presses over belt/feed area under raised cover. | 0.68 |
| 14.25 | 855 | top | DEFAULT top: cover now closed; support hand near receiver. | 0.80 |
| 14.75 | 885 | top | DEFAULT top: closed receiver raised toward charging/settling hand action; exact handle travel partly obscured. | 0.86 |
| 15.25 | 915 | top | DEFAULT top: charging/settling hand action with muzzle raised; exact latch travel obscured. | 0.92 |
| 16.00 | 960 | left | DEFAULT left: ready hip view restored, belt and box assembled. | 1.00 |

The source shows a forward-hinged upper receiver/cover carrying the rear sight, exposed feed area, support-hand box handling, linked belt placement, cover closure and final charging/settling action. Box departure and some latch/hand contact are occluded. **Exact pivot placement, cover membership, box departure/return path, charging-handle travel, carrier angles and normalized phase boundaries are authored interpretations.** The same intact canonical box/belt represents outgoing and replacement feed; there is no extra payload or disappearance by scaling. This is a weapon-only animation without hands, extracted bones, extracted animation or hand IK.

Canonical source: `src/main/resources/assets/destiny/models/weapon_surface_w123/fixed_odds.json`, **153 emitted cubes, zero triangle adapter elements**. Existing five box solids plus 28 cartridge/link solids and six joining solids form the rigid 39-element moving box/belt. The 114-element receiver includes ten cover solids and two charging-handle solids articulated through body child element overrides. Every original face UV, texture, cuboid dimension and material stays intact. Both endpoints reconstruct the full canonical geometry and exact display for native/twohand and left/right FP. Other contexts and ADS/inspect use the exact canonical item graph. This is preservation/animation of accepted geometry, not a new 80–120-element remodel.

The cover opens before the box withdraws. The complete connected belt travels with the box, so no individual bullet floats away; the final cartridge stays inside the box opening. The feed lead clears the receiver while withdrawn and returns to the original feed port before cover closure. A short handle action follows closure. Motion keys are specific to this cover/feed sequence; only W178 matrix composition conventions and test/harness patterns are reused. The Hammerhead generator supplies a read-only CPU raster/UV utility, never footage or motion keys.

Gameplay remains canonical: 44-round magazine, 106 reload ticks, 360rpm / 3.333333333333 cadence ticks and burst1. Audio/data and canonical assets are read-only pinned inputs. Shared routing/admission/registries, clock/ammo behavior and all runtime/native tests belong to master. Worker tests cover assets, representative real 26.3 CuboidModel parser transforms and ItemModels codec. No native success, new third-person reload, sound or performance success is claimed.

Evidence is retained at `/private/tmp/w179-fixed-odds-report/`:

- `ornament.webm` SHA256 `080a6e24152b29927bc6f3d2041ef49c526c1fda9e9a4eb89ed24f6ec36eeb4f`; `ornament.info.json` SHA256 `9afe0e33953155eaf44196ef6f4d97dda5d6e7b7da1eb4fb7a8b2adcbfc93d28`.
- `motion-reference.json` contains each exact frame time/index/hash/observation. `default-selected.png`, `orn-a.png`, `orn-b.png` preserve inspection sheets (the earlier default-selected draft has two imperfect panel crops; final storyboard corrects them).
- `source.mp4` / `source.info.json` (Masochist, IGo_G9wEtps) and scout/detail renders were rejected for reload evidence: apparent actions were traversal/ability activity with unchanged magazine counter. These remain as failed research, not support for authored motion.
- `review.mp4` / `review.info.json` (Nexas Gaming, FvQKWWi0kPs) was downloaded as an alternative; not used as motion evidence after the clear labeled DEFAULT comparison was found.
- `failures.log`, Python/Java/generator logs, scope and export verification, and `REPORT.md` distinguish failures, final passes and pending native checks.

Rebuild previews with bundled Pillow/numpy Python and `scripts/generate_reload_w179_fixed_odds.py --render --evidence /private/tmp/w179-fixed-odds-report`. `--verify` regenerates core JSON and checks stored preview hashes without requiring source media. The manifest pins canonical source hashes and records the exact 21 samples, parent partition, cover members, phases, reference hashes and unchanged master boundary.

Master native scenario: use both FP contexts and native/twohand grip, begin a normal and accelerated reload, inspect cover opening before box movement, entire attached box/belt clearance, feed reseat before closure, charging action and exact ready recovery. Check canonical ADS/inspect plus GUI/ground/fixed/third-person fallback. Interrupt by swap/cancel/unequip/death/disconnect and verify master-owned cleanup; briefly inspect 10–20 displays and existing audio. Native hand framing, pack texture loading and sound/listening remain pending master.
