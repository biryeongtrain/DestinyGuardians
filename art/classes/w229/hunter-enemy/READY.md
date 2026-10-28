# Hunter enemy-red assets — READY / FROZEN

Frozen UTC: 2026-10-28T12:28:57.984621+00:00. Payload: **37 files / 3438414 bytes**.

Copy root: `payload/src/main/resources/` → destination `src/main/resources/`. This is a bounded asset delta; no existing source file is replaced by a same-name resource because every target resource has `_enemy` suffix.

## BetterModel: exact 8 names

| Current registered source | Prepared enemy name |
|---|---|
| `destiny_vfx_arc_h14` | `destiny_vfx_arc_h14_enemy` |
| `destiny_vfx_solar_h14` | `destiny_vfx_solar_h14_enemy` |
| `destiny_vfx_vortex_h14` | `destiny_vfx_vortex_h14_enemy` |
| `destiny_vfx_smoke_h14` | `destiny_vfx_smoke_h14_enemy` |
| `destiny_super_arc_sweep_h15` | `destiny_super_arc_sweep_h15_enemy` |
| `destiny_super_solar_muzzle_h15` | `destiny_super_solar_muzzle_h15_enemy` |
| `destiny_super_solar_impact_h15` | `destiny_super_solar_impact_h15_enemy` |
| `destiny_super_void_anchor_h15` | `destiny_super_void_anchor_h15_enemy` |

Bundled files are under `payload/src/main/resources/destiny/vfx/`. To load with BetterModel, master must also install these 8 files in the corresponding `bettermodel/models/` runtime directory and include/select the 8 enemy names through its integration. Existing `HunterVfxAssets` registration was not changed by this worker.

## Exact item roots

| Source ITEM_MODEL id | Prepared enemy ITEM_MODEL id |
|---|---|
| `destiny:arc_staff_h28` | `destiny:arc_staff_h28_enemy` |
| `destiny:golden_gun_h29` | `destiny:golden_gun_h29_enemy` |
| `destiny:shadow_bow_h28_drawn` | `destiny:shadow_bow_h28_drawn_enemy` |
| `destiny:shadow_bow_h28` | `destiny:shadow_bow_h28_enemy` |
| `destiny:shadow_arrow` | `destiny:shadow_arrow_enemy` |
| `destiny:hunter/arc_flashbang` | `destiny:hunter/arc_flashbang_enemy` |
| `destiny:hunter/solar_incendiary` | `destiny:hunter/solar_incendiary_enemy` |
| `destiny:hunter/void_vortex` | `destiny:hunter/void_vortex_enemy` |
| `destiny:hunter/solar_knife` | `destiny:hunter/solar_knife_enemy` |
| `destiny:hunter/void_smoke_bomb` | `destiny:hunter/void_smoke_bomb_enemy` |

The ten roots follow current `SuperVisuals`, `HunterAbilityVisuals`, and `HunterSuper.shadowArrow()`. `bowStage()` currently always uses the drawn H28 bow; release uses H28 rest bow. Arc Combination Blow returns an empty hand and has no item resource.

Dependency closure: **10 item definitions + 11 model JSON + 8 PNG**. All referenced destiny models/textures are cloned and rewritten to their exact `_enemy` IDs, including H28/H29 triangle adapters and the shared triangle alpha texture. No external dependencies or original destiny resource references remain in the cloned native dependency graph. No weapon catalog, old unused stages, HUD, player skin, or player-limb animations are included.

Preserved: dimensions and exact alpha bytes across **36 embedded PNG + 8 resource PNG**, including transparent RGB bytes. BetterModel elements, hierarchy, UUID links, geometry, animation channels/names and UVs remain equal. Native composite transformations, model elements, display poses, UVs and conditions remain equal; **7,416 constant tints** were recolored so mesh-based handheld models actually turn red.

Original mesh/composite counts are preserved; this is a recolor, not geometry redesign or a new output-budget certification. Team/enemy per-viewer routing, runtime registration, duplicate suppression and game/PvP verification remain the master integration responsibility. This worker made no main/SSD edits, build, game input, commit or runtime claim.

Integration files: `manifest.json`, `resource-mapping.csv`, `PAYLOAD_HASHES.json`. Optional previews: `comparison/model-comparison-contact-sheet.png` (18 pairs), `comparison/texture-comparison-contact-sheet.png` (44 pairs). These show offline static source geometry/UVs, not game lighting/animation.

**Payload frozen: do not rerun preparation scripts during master R3 integration.** Scripts are reproducibility records only.
