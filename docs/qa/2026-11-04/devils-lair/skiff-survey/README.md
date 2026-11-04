# Strike skiff feasibility — current NBT maps

## Scope and missing implementation

DevilsLair.Presentation declares incoming(), but DevilsSession currently only records spawn lead times and DevilsPresentation has no skiff implementation. Existing tutorial SkiffDrop is coupled to tutorial zones/FallenMob lifting and cannot be called as an unmodified strike adapter. No ships were integrated by this survey and gameplay spawn positions/timing remain unchanged.

The examined existing rg_skiff model has 54 elements and idle/arrive/drop/depart clips. It has no embedded credit field. Its present runtime form is not certified here as an extracted source-faithful strike Skiff. Model and all four NBT input hashes are in inputs.json.

## Actual server evidence

The full NBT fixture completed successfully (gametest.xml). Nine anchor searches ran in the generated four-map world. report.json records selected hover positions, yaw, entry visibility, search wall time and geometry-query count. Initial and classified runs are archived separately.

- RF.A / RF.D: no hover candidate under the existing open-sky policy. Searches took approximately 154 / 127 ms in the classified run (155 / 117 ms initially), despite only 64 / 151 counted solid reads. The current read budget does not bound the rest of the search CPU cost. Do not add this search to a combat tick as-is.
- RY.L / BL.H / SP.D2: hover candidates exist. Sampled failures are solely unloaded footprint columns; they do not prove terrain collision. Their approach/exit corridors need explicit preparation/loaded-world validation before playback.
- BL.EXIT / BL.L / BL.R / SP.D1: candidates exist, but some sampled animation positions have loaded columns whose heightmap exceeds the conservative hull-bottom height. Counts are 9 / 26 / 18 / 15 respectively. These need route/heading changes or exact geometry assessment, not merely extra chunk loading.
- BL.EXIT / BL.L candidates are not visible from the authored entry eye. That is one observer position only, not evidence that no combat player can see them.

## Limits and next implementation constraint

The scan samples original existing hull-position keyframes: arrival starts 87.5 blocks out / 16.25 up; departure ends 112.5 blocks out / 26.25 up. It uses an upright conservative hull footprint and open-sky heightmap rule. It does not evaluate pitch, intermediate interpolation, animated clamps, all eight selected spawn pads, native camera views or FPS. A failed open-sky sample is not automatically a triangle/body intersection, and unloaded columns are reported separately.

Before integration, author/precompute bounded flight corridors per selected delivery area, prepare their owned chunks during loading, then check full sampled animation envelopes and viewer exposure. Keep one ship per zone/session and generation-owned cleanup. Bind delivery to the exact selected spawn pads and actual spawn callback; do not lift already active strike mobs or change director timing through the tutorial adapter.

No production source/assets or JAR were changed by this diagnostic-only batch. Existing full-suite failures and native acceptance remain outstanding.
