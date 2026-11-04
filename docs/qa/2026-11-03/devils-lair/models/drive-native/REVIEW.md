# Drive shader/native clip candidate — scoped handoff

Integration is restricted to the eight `manifest.json` paths (seven models plus generator). Compare each destination with its recorded baseline before copying. Do not copy the worktree's whole models directory: it still contains rejected historical candidates. Keep `rg_walker` and its existing 50-bone rig. `dl_walker` and `dl_marauder` are deliberately absent; Marauder routing remains master's decision.

## What changed

- Original Drive material graphs evaluated in a separate headless Blender scene, preserving explicit UV maps and normal/metal/roughness detail. Named source UVs now survive mesh joining; previous white/flat Hive bakes were incorrect and are superseded.
- Acolyte/Knight source blends contain weapon materials but no weapon geometry. Imported original delivered native weapon geometry/UVs and routed it to the native `19AB4BEF` weapon socket under `hand_r`. Their weapons animate through the original socket, not a static hand attachment.
- Combined + separate positive-strength emission bake. Legacy opacity branches missing a transparent closure are repaired in the temporary scene and recorded. For pure Transparent+Emission materials, cutout comes from actual emission intensity (>16), avoiding black FX cards. Original source files remain untouched.
- Shader-painted Brig Dusk adaptation uses textured colour multiplication/dye inputs with explicit receipts. This is authored faction adaptation, not recovery of an original Dusk Brig shader. `armor_plate` contains only the front chest plate; `optics_glow` is its child; `weakpoint_glow` is a separate authored orange radial core under `spine_upper`. Hiding the plate leaves the chassis and core visible (`brig-exposed.png`).
- Original native world-matrix clips retargeted, not copied Euler keys. Edited source control pivots restored; Knight's geometry/translation scale correction is 1.0286287699437537. Native input receipts and registration details are embedded.

## Evidence and limitations

`comparison-hive.jpg` and `comparison-fallen.jpg` show the source shader radiance bake on source geometry (left) versus final depth-slice geometry (right), under the same comparison camera. These are offline comparisons; the left side is a fixed-light shader bake, not live PBR rendering. Brig's left side includes the authored Dusk dyes.

`validation.json`: caps, one 2048 atlas, finite zero-thickness quads, hierarchy/UUID references, clip aliases, weapon/Brig contract, source hashes, and serialized FK against original native clips. Sample counts and numeric residuals are recorded per model. No Gradle, BetterModel runtime, gameplay animation, collision, FPS, or night-visibility acceptance is implied.

`visibility.json` preserves per-bone mean radiance and foreground screen luminance percentiles for both reference/candidate. Five models remain below the historical mean-luma-80 criterion. No global gamma lift was applied: dark robe/back/internal surfaces are part of the source appearance. Inspect their front detail and silhouette at actual game distances before acceptance. Depth-slice texture noise and stepped silhouettes are still visible at close range in comparison renders.

Master QA: preview these images before integration; test single/mixed mobs at combat distances, original fire/run/death clips, weapon socket motion, Wizard robe silhouette, Servitor/Sepiks emission and alpha at night, Brig armour hiding/weakpoint, and the requested 1/10/20/30 load scenarios. Preserve the separately exported `/tmp/devils-thrall-runtime-candidate` until its ongoing QA concludes; it is an older immutable candidate, not this final Thrall hash.

## Reproduction

Use `scripts/strikes/build_devils_models.py` in the supplied worktree/repo with existing `scripts/campaign/bake_dreglight.py`. Original `dump/bake/refresh` are historical palette experiments, not accepted outputs. The current route is one species per cache:

1. Headless Blender with `--disable-autoexec`, explicitly opening the source blend, `-P <builder> -- drive-dump --names <species> --source <same blend> --cache <species-cache> --native-cache <original-native-cache>`.
2. Python with NumPy/Pillow: `<builder> drive-register --names <species> --cache <species-cache> --native-cache <original-native-cache>`.
3. Python: `<builder> drive-native --names <species> --cache <species-cache> --native-cache <original-native-cache>`.

Source paths/hashes are in each `evidence/<species>/shader-bake.json`; source mesh/motion cache is `/tmp/devils-models-evidence`, evaluated cache is `/tmp/devils-drive-models/<species>`. The native cache derives from the original delivered November 2 geometry/motion package. Baker source and source inputs are read-only dependencies and are not duplicated into this delta.
