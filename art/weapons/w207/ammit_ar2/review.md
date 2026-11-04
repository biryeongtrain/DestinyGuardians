# W207 Ammit AR2 continuous reload bank

## Concrete fix

`scripts/generate_reload_models_w69.py` selects 21 poses at `frame/20`. Its `sample()` reapplies `t*t*(3-2*t)` separately between every pair of authored keys, forcing zero velocity at every internal key even during a continuing extraction or body raise. More frequent runtime updates cannot recover states missing from that bank. The W69 generator also partitions the original older geometry by historical indices, which is inappropriate for the current remodeled weapon.

`scripts/generate_reload_w207_ammit_ar2.py` provides a self-contained, standard-library `generate(root=ROOT) -> dict[absolute Path, bytes]`. Import and generation perform no writes. The master writes the returned new W207 assets and manifest, routes runtime to `destiny:weapon_reload_w207_ammit_ar2/ammit_ar2`, and changes quantization to 60. This worker changed only this generator and this review.

The bank contains 61 poses (`p=i/60`) for each body/magazine and native/twohand combination. The output map contains two shared geometry parents, 244 pose models, one item definition and one new manifest. All asset paths are restricted to `models/weapon_reload_w207_ammit_ar2/` or `items/weapon_reload_w207_ammit_ar2/`; the only other returned path is `art/weapons/w207/ammit_ar2/manifest.json`. No historical asset, item or manifest is emitted or overwritten.

## Motion and retained reference

Retained every W69 normalized key and body/magazine value: raise at .16, extract through .30/.48, reseat at .64/.76, handling peak at .84, return at 1. Neither gameplay reload duration nor ammunition/audio/combat code changes here. The actual existing image `art/weapons/w69/references/ammit-reload-contact.jpg` was opened again for this revision. [xHOUNDISHx gameplay](https://www.youtube.com/watch?v=w3CYQprLoc0&t=24), including its 23.95–25.15s and 49.6–50.35s handling samples, remains the motion reference. Hand occlusion limits exact cartridge trajectory recovery; the path remains an authored approximation, not newly extracted animation or IK.

Each scalar Euler/translation/magazine component now uses C1 shape-preserving cubic Hermite interpolation. Adjacent monotone movement spans share a weighted harmonic tangent, so movement continues through internal keys. Tangents become zero at real extrema and holds; endpoints settle at rest. This preserves the body handling plateau .48–.64 and magazine seated spans 0–.16 and .76–1. No generic smoothstep is reapplied at every internal key. Keeping W69's display-space Euler and magazine offset convention avoids introducing an unrelated trajectory redesign. Euler ranges have no wraparound across these keys.

Twohand compensation is derived from the accepted canonical native/twohand transforms, then applied to the animated native matrix/position. No shared helper import or generator execution is needed. Both generated endpoint displays are exact deep copies of the corresponding accepted idle displays, including non-first-person contexts.

## Geometry and graph contract

Read only current `weapon_surface_w123/ammit_ar2.json`, `_body.json` and `_magazine.json`: full 126 elements, split 121 + 5. Preserve every element, face, UV, texture and material mapping; compare the combined partition to the canonical surface before generating. No original ripped elements or obsolete W69 magazine indices are used. Names retain `ammit_ar2_*_body_*` and `ammit_ar2_*_magazine_*` for master hand-contact recognition. Ammit has no independent moving cover, so none is invented. Existing OMOLON blue beam, receiver, fluid chamber, grip, peep and independent cartridge remain intact.

The item wrapper preserves metadata and the original `items/weapon/ammit_ar2.json` model exactly as non-first-person fallback, range fallback, and pose-bank entries 0/60. Interior first-person entries dispatch on CMD float 1 and flag 0 (`false=native`, `true=twohand`). Thresholds are float32 encodings of `i/60`, matching Java float division. Existing ADS, inspect and third-person fallback graphs remain unchanged; W206 first-person framing and arm overlays remain master-owned downstream steps.

## Checks completed and pending native work

Executed the generator only in memory, without writing generated outputs. JSON encoding succeeds; returned paths remain in the new namespace; there are 61 strictly ordered thresholds; fallback and endpoint item graphs equal the original; every endpoint part display equals accepted idle; body/magazine elements and UV data equal current remodeled sources. At selected moving knots (.16 body raise, .30 magazine extraction, .76 body handling), one-sided numerical slopes agree and remain nonzero. Original key values, seated-magazine holds and body plateau are retained. These are targeted implementation checks, not native animation acceptance.

No build, client, server, CU, Blender or generated-output write was performed. Pending master integration/native checks: shared route and /60 quantization; actual motion cadence at ordinary and fast reload stats; native/twohand and both hands; fingerless skin contact following the moving magazine; release/reseat/recovery without clipping or endpoint snap; ADS/scope and third-person fallback spot checks. A 61-pose bank removes extra /20 state quantization but the item state is still delivered at up to server 20Hz. This is not proof of 60fps animation or a claim of native verification.
