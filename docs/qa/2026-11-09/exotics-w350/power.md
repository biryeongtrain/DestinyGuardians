# W350 power exotics — revision 2 offline handoff

Initial rectangular block drafts were rejected. The requested W327 Krait/Rufus/Origin/AgeOld/Insidious/Phyllotactic quality screenshot and accepted `group3_v3.py` closed-loft plus `group3_optimize.py` native polygon union were reviewed. Model work continued with Sol high per latest user override. No prior authored R2 generator was present; existing baseline/art evidence was preserved. No leftover owned Blender output writer was running before edits. Replacement checkpoint: `/tmp/exotic-expansion-20261109/power-sol-checkpoint/sha256.json`. Original rejected review images remain unchanged in each `review/` folder; complete initial art proof is `/tmp/exotic-expansion-20261109/power-r2-baseline/`.

| Weapon | Body | Cover | Magazine | Max assembled elements | Atlas |
|---|---:|---:|---:|---:|---|
| Gjallarhorn | 483 | 166 | 18 | 667 | 2048 x 512 |
| Whisper of the Worm | 603 | 0 | 15 | 618 | 2048 x 512 |
| Tractor Cannon | 702 | 0 | 9 | 711 | 2048 x 1024 |

The count includes every native masked polygon plane and solid cuboid, including moving pieces. Full and body+moving-part representations are alternatives, not cumulatively counted. Two classic W204 forearms add 224 elements when visible. Counts are compliance evidence, not an aesthetic/performance acceptance claim.

Gjallarhorn now has source-proportioned 12-sided hollow tubes, wolf head/muzzle/brow relief, source-anchored UV mane engraving, actual lateral sight apertures, three gold chamber collars, shallow barrel inset motifs, rear transverse open loop, properly raked support and a sloping open stock. Overlapping relief tiers caused black triangles in the first R2 preview; these were removed and shallow fur moved to UV. Both final obliques were inspected offline.

Whisper has a closed varying-width receiver, actual raked grip/stock bridge, two true stock/trigger voids, separated magazine, hollow scope/barrel, and authored skull/jaw/spines. Source Workbench FX cards are visibly opaque sheets in supplied evaluation renders; those card silhouettes and their misleading shadow detail were excluded from material projection. Clean source-anchored Taken fissures provide the finish interpretation. This is not a reconstruction of dynamic Taken shaders.

Tractor has a closed changing elliptical drum, deep hollow forward emitter, three radial swept claw solids, twin hollow diagonal exhausts, open upper/lower handle frame and source-based subdued blue/steel/white panels. White housing and small blue accents are pinned to the supplied Bungie base inventory icon, not the neutral gray rip material.

`r2/native-render-input.json` is extracted from the actual emitted `models/weapon_w350/<id>/full.json`, not an intermediate Blender authored mesh. `r2/native_{east,q,otherq,front}.png` are the native-element offline views. `r2/source-vs-native.png` provides source side/oblique comparisons. Whole weapon proportions use a single source-pixel scale in `power_r2.py`; dynamic reflections/PBR are not restored.

Source .blend SHA, original mesh/bone/material/action inspection and side/oblique/top proof remain in source-evaluation.json and source_*.png. All three original .blend SHA values were rechecked unchanged; all have zero source actions. Reload remains an explicitly authored PCHIP approximation, 61 poses and 21 aim samples; no source player wrists/elbows/hands or original reload provenance is invented. Contacts/loading/cover hinges were newly measured from the source-to-model frame and written to rig.json. New hand leaves use `destiny:weapon_w350/<id>/hands/`, which the master brief identifies as supported by ProfileArmGraph; initial unreferenced `weapon_hands_w350/<id>` leaves remain baseline files.

Offline checks passed: unique native element names, maximum 1000 assembled elements, valid bounded zero-depth polygon adapter planes or positive-volume cuboids, UV 0..16, matching atlas dimensions, all own item graph model references, 61 ordered reload samples, zero rest endpoints, 21 aim entries, 332 referenced W204 hand leaves per weapon, full/body+moving part agreement, original source hashes. `scripts/art/w350/power.py build|render|check` now forwards to the revision 2 generator, preventing accidental rebuild of rejected drafts. No shared registry/Java/audio files were changed, and no client/server/CU/build/commit/push operations were performed.

Pending master: resource pack load, first Vision hip/ADS/third person and reload contact/hand scale, delegated fix review, then second Vision; 10–20 displayed instances and performance remain unmeasured. These offline results are ready for integration review, not final native aesthetic acceptance.

Exact initial-baseline/new-SHA delta and ZIP are `/tmp/exotic-expansion-20261109/power-r2-delta.json` and `/tmp/exotic-expansion-20261109/power-r2-delta.zip`. Existing modified files carry their initial R2 baseline SHA; new files carry `ABSENT`. Do not apply over a changed integration file without reviewing its current hash.
