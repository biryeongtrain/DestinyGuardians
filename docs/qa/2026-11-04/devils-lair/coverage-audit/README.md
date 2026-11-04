# Cross-model shader coverage audit

Six version-4 source caches were checked against the current bundled assets: all six cached models byte-matched the runtime baseline before this batch. The evaluated source scenes are temporary caches; Downloads originals were not modified. Existing Walker and the separately sourced Thrall are outside this coverage audit.

The same explicit shader-coverage baker used for Marauder was applied to Acolyte, Knight, Wizard, Servitor, Brig and Sepiks. Initial Acolyte traversal rejected a colour-valued closure input. The helper now accounts for Blender's implicit numeric/colour-to-opaque-emission Surface conversion; unknown closure types still fail. This addition left the other five mask hashes unchanged (`unchanged-existing-masks.json`). The audit counts triangle centres, not surface-area percentages or every atlas texel.

| Model | Triangles | Ordinary centres below 0.5 coverage | Decision |
|---|---:|---:|---|
| Acolyte | 27,878 | 796 | Rejected: black facial rectangle exposed in q34 render |
| Knight | 28,085 | 912 | Coverage fix integrated, native acceptance pending |
| Wizard | 25,196 | 758 | Coverage fix integrated, native acceptance pending |
| Servitor | 19,072 | 0 | Unchanged; this sample audit does not prove no transparent texels anywhere |
| Brig | 63,532 | 19,119 | Coverage fix integrated, native acceptance pending |
| Sepiks | 20,879 | 2,027 | Coverage fix integrated, native acceptance pending |

Each affected candidate was regenerated and rendered alongside its original model using the same q34 camera, emissive atlas material and culling. These are headless Blender controls, not Minecraft framebuffer checks or original-shader optical equivalence. Knight/Wizard visible changes are small; Brig/ Sepiks preserve gross shape with corrected cutouts. Surface aliasing remains in all candidates. Acolyte's exposed black facial rectangle is a concrete rejection, not hidden by passing rig checks; investigate source surface/emission/visibility separately before adopting it.

Rig group metadata and all animation JSON objects match before/after for all five generated candidates (`contracts.json`). Integrated counts: Knight 2,151 (unchanged), Wizard 2,062 (unchanged), Brig 2,938 -> 2,964, Sepiks 2,905 -> 2,890. Previous bundled bytes and before/after hashes are saved locally. Integration rechecked baseline SHA256 immediately before copying only these four assets. No Acolyte/Servitor/Thrall/Walker model was changed.

Asset install/clip tests and actual Gradle JAR packaging results are recorded in `asset-build.json` after completion. Full native combat, performance and visual acceptance remain pending; no completion commit is claimed.

Result: scoped model tests 2/2 passed; Gradle test + jar exited 0. All four corrected resources and the unchanged Acolyte resource byte-match the built JAR. Previous full-suite failures remain unresolved; a scoped art pass does not supersede that baseline.

## Acolyte follow-up: additive transmittance

The first candidate's facial rectangle was caused by our coverage helper's Add Shader maximum rule, not evidence that the source facial surface should be opaque. The original shader render has no rectangle. Four isolated Cycles renders establish alpha: transparent + emission = 0; a half Mix = 0.5 (PNG 128/255); two half-transparent closures added = 0; two opaque closures added = 1. The helper now combines Add Shader transmittance, equivalently `max(0, coverageA + coverageB - 1)`. Its baked coverage matches those independent rendered alphas within 8-bit quantization (`add-shader-control-check.json`).

Rebaking Acolyte removes the black rectangle in the inspected q34 image. The corrected canonical model has 1,702 planes and all 17 animation JSON objects unchanged; it is now integrated (`acolyte-integration.json`). The rejected comparison remains preserved as evidence, not the current product state. The original shader's stronger eye radiance and general slice surface roughness still need work; removing the rectangle does not certify emission fidelity.

The new coverage audit is saved separately as `after-add-transmission.json`. Mask hashes changed for the other five caches as additive FX coverage changed, although their ordinary triangle-centre counts did not. Those previously integrated models have not been regenerated with this second coverage revision yet; centre counts alone do not prove full sample equivalence. Their temporary opacity.npz files now hold the new audit masks while the older shader-bake metadata hashes intentionally remain stale, so the consumer will refuse accidental regeneration until those cache metadata receipts are deliberately refreshed. Acolyte's receipt was refreshed and validated. This is a remaining audit/regeneration item, not a claim that every model uses the corrected Add rule already.

Acolyte integration verification: model asset tests 2/2 pass; actual Gradle test + jar exits 0; packaged model byte-matches source. This scoped pass does not resolve the existing full-suite failures or provide native acceptance.

## Completed Add-rule regeneration audit

Marauder, Knight, Wizard, Brig and Sepiks were regenerated using deliberately refreshed coverage receipts. The first four exactly match every current runtime/render payload field (meta, name, resolution, elements, textures, outliner, animations), so their bundled files were preserved. Sepiks matches all of these except texture data: 1,425 atlas texels change RGB, with alpha changes on 5 of them. This supersedes the pending regeneration item above for these five models. `add-rule-model-equivalence.json` records the actual field comparisons and new mask hashes.

Actual before/after Sepiks q34 PNGs were inspected: the silhouette and visible shell/core arrangement remain intact; the small colour differences are not a major visual-fidelity improvement. Its regenerated asset was integrated after rechecking the baseline bytes, with the old asset and hashes preserved. This removes the remaining audited Add-rule discrepancy; it does not certify source emission strength, close-range smoothness, native playback or FPS. Computer Use again reported the Mac locked; no native client was started.

Final Sepiks packaging: actual Gradle jar exits 0; packaged resource byte-matches current source (`add-refresh-jar.json`). No redundant JUnit pass was run for this texture-only change; the independently rendered coverage controls and unchanged geometry/animation comparisons are the targeted checks. Prior full-suite failures remain unresolved.
