# ATLAS R2 FROZEN — integrate now

CAS manifest: /private/tmp/destiny-w230-art/delta-atlas-r2/cas-manifest.json
SHA256: b7406d17fcc8020c9e4a22d068123fa4bc597cdc812aaeb0696c4d6ebadbb70a
Root: /private/tmp/destiny-w230-art/delta-atlas-r2/payload
Changes: 56 exact model/PNG paths already present in R1 manifest. No item IDs, geometry, display transform, HUD, runtime or W229 baseline changed. Expected source SHA required for each replacement.

28PNG: 23,068,672 -> 1,818,624 pixels. Saved21,250,048 (92.12percent). Four new Well sword PNGs2048² ->512². Each UV rectangle retains exact RGBA and source two-pixel neighbors; no resize/resample. UV mapping is the only model change. R1 frozen originals preserved.

Full R1c pack PNG inventory212,576,242 -> expected191,326,194 pixels if all56CAS entries integrated. This is inventory area, not exact atlas occupancy or a promise of stitching success. Device atlas cap was not reported in the log; native load required next. If still fails, product pack can omit unreferenced historical textures AFTER replacement converters, retaining both bows' w30 references. Do not remove the full w30 directory.

W229 baseline2K paths require separately authorized scope: titan/{class_ability,solar_super,void_super}{,_enemy}.png and warlock/{class_ability,solar_super}{,_enemy}.png under assets/destiny/textures/item/class_ability/. These10PNG are not edited here. Existing W229 solar sword itself shares identical normal PNG bytes with new Well variants, but no baseline references were changed.
