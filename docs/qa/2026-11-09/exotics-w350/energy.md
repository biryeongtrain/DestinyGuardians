# W350 energy exotics — first offline deliverable

Status: ready for first master Vision; no native acceptance claim. No client/server, live Blender scene, shared registry or Java edits.

| Weapon | Body | Moving part | Total | Atlas | Reload | Aim |
|---|---:|---:|---:|---|---:|---:|
| Sunshot | 92 | 10 | 102 | 512×512 | 61 | 21 |
| Graviton Lance | 103 | 9 | 112 | 512×512 | 61 | 21 |
| Jotunn | 108 | 6 | 114 | 512×512 | 61 | 21 |

Original archives were downloaded through the Drive connector into `/tmp/exotic-expansion-20261109/sources/<id>` and opened in owned headless Blender with auto-execution disabled. Source originals were never saved. Source SHA, source side/oblique/top renders, albedo evidence and official Bungie icon finish are under each `art/weapons/w350/<id>` directory.

Sunshot has no actions. Graviton has a 6,048-channel UV-only action (no pose action). Jotunn has four shader color channels with a single key each. All weapon rigs lack player wrists/elbows. Each authored reload therefore states approximate provenance explicitly. Source rig names do not establish captured player animation. Sunshot moves the separate cylinder/crane, Graviton withdraws the rear battery, and Jotunn raises its top cell. The left hand approaches, follows the moving part, releases and returns. All timing is authored; the actual 61 native poses are not continuous 60fps interpolation.

The authored solid models use small adjoining orthogonal blocks, real openings, an eight-role palette and face-specific 1-texel material edges. Flat material planes replace universal shiny banding. Source mesh triangles were not converted. Five review views per model were rendered and inspected. Exposed coplanar faces were checked and corrected. Generated JSON/model parents resolve; element bounds and UVs pass; endpoint poses exactly restore idle; body adjacent rotations remain below 3 degrees/sample. Generated hands reference existing W204 classic/slim skin-arm parents, ready flag 8, slim flag 9 and tint channels 64/192.

## Integration

For each ID `sunshot`, `graviton_lance`, `jotunn`:
- Root item `destiny:weapon/<id>`: static hip fallback, string CMD index 0 selects ads/inspect.
- Aim item `destiny:weapon_aim_w350/<id>`: 21 poses via float CMD index 3.
- Reload item `destiny:weapon_reload_w350/<id>`: 61 poses via float CMD index 1.
- Direct reload aliases `destiny:weapon_reload_w350/<id>/<0..60>`.
- Model geometry `destiny:weapon_w350/<id>/{full,body,magazine,ads,inspect}`.
- Separate static item aliases `destiny:weapon_w350/<id>/{hip,ads,inspect}`.
- HUD texture `destiny:item/hud/w350/ammo_<id>`.

All animated/hand graphs use a first-person display-context guard; GUI, ground and third person fall back to the full static weapon. The master owns catalog, numerical profile, central arm registration and runtime route changes. Per-weapon exact snippets are in `integration.json`.

## Verification and remaining work

Run `/tmp/exotic-energy-python/bin/python scripts/art/w350/energy.py check all` (Pillow required). Rebuild with `build all`; five-view renders with `render all`. Source evaluation/extraction helpers are owned scripts `energy_evaluate.py` and `energy_extract.py`. No original archive or .blend is packaged.

Pending: actual pack load, hip/ADS framing, 1P and 3P grip, source-relative reload contact and return, actual shots, 10–20 item observation, first Vision delegated review, second Vision. Exact source reload authenticity cannot be claimed because no such action exists in the supplied source.

Carrier contract: single native poses are intentional for the enabled owner ProfileView. Master confirmed its carrierCompensated check skips inverse crossbow compensation when bool0 selections are identical. Legacy fallback client camera with TWO_HAND remains unverified and may require a later bool0 compensation branch.
