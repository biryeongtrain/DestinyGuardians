# W336 R2 composed class locomotion candidate

R2 only: `/Users/qf/Downloads/Destiny-Super-Idle-Movement-2026-11-07-R2`. R1 output is superseded; its private evidence is retained under `/tmp/w336-super-locomotion/classes-r1-private-evidence`. R1 group indirection,16-byte layer decoding, frozen upper-body masks and static-only floating assumptions are not reused.

The actual `Guardian_Super_Composed_R2.blend` was opened in separately owned headless Blender:105 composed actions,72 bones, original slots. Twenty-nine selected composed actions were evaluated at start/middle/end and compared against reconstructed20Hz delivered TRS; maximum matrix-component error was1.06e-5. TRS already includes rest and is composed once through the source hierarchy. Originals are read only; no blend/FBX/raw cache enters this delta.

The31 loop names keep the runtime contract. Five ground families have idle plus four directions using the genuine R2 v0 movement takes; no speed adjustment is applied. Floating Stormtrance/Nova Warp use distinct animated idle and move, with optional air alias of idle. `source_revision:"R2"` is mandatory at the resource root; floating metadata tells runtime to select idle/move by resolved horizontal displacement even airborne.

| Family | R2 binding | Important source composition |
|---|---|---|
| Fists of Havoc | unarmed candidate, not confirmed active-super selection | R2 candidate group27, all composed channels retained |
| Hammer of Sol | named state group32 | base plus original hammer grip |
| Sentinel | shared shield state group26 | original shield grip and conditional masks baked by R2 |
| Burning Maul | named conditional group39 | idleB251+A9CA+AB2D,6.8667s; movementA698-family+A9CA+A9C9, including hips/legs |
| Daybreak | named state group44 | original base + sword offset/grip |
| Stormtrance | named internal floating state | idle8D3=2.4667s; movement8AF=1.1333s |
| Nova Warp | named internal floating state | same animated layer families over distinct Nova base |

R2 source pelvis/spine/head/hip-socket/leg/clavicle/elbow/wrist motion remains coupled. The directly retargeted R2 composed idle supplies the anatomical calibration; only the existing target item bind nodes are retained. No older ready-animation hand position is used, and arms are not held/frozen. Both wrist displacement and rotation are driven by R2 source changes relative to the source torso. A common reach projection preserves the relative two-wrist trajectory while fitting the unchanged player limb lengths; translated IK and item counterrotation preserve the resulting hand endpoints.

Global source root travel is excluded to avoid duplicate server displacement. Root-relative visual pelvis movement, including the real floating bob, remains in the skeleton. Ground skin support correction is visual; floating source vertical motion is retained without invented sway. Geometry, cast/attack/dodge/contact, audio, RMB binding and2tick display interpolation are unchanged.

R2 missing/runtime-driven aim, speed-to-weight/phase, procedural layers and final game IK remain as documented in the R2 handoff. Floating movement weight1 is the supplied preview preset, not a recovered original speed driver. The source package does not supply final super props; source-wrist/target-mesh grip fit still needs master native review. Direction names remain foot-trajectory estimates, not decoded original direction enums.

`manifest.json` preserves each complete R2 bake/layer recipe and omitted-driver list. `representative-poses.png` is a bounded static FK review of first/middle idle and forward/generic-move poses; it is not native acceptance. Reproduce with headless Blender `--inspect composed`, then Python `--export`. Master owns runtime/resource integration and native idle/move/direction/stop/grip/floating checks.
