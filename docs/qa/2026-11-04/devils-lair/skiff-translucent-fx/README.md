# Skiff source emission / translucent candidate — 2026-11-04

Work in progress; not integrated. The original candidate treated all retained source emission as alpha 255, turning dim additive beam cards into opaque dark geometry. Minecraft 26.3 MaterialInfo.of has native translucent item/block-item rendering selected by texture Transparency.hasTranslucent, and ItemQuads separates blending quads. Bytecode and exact client JAR hash are retained here. This capability is not proof that BetterModel preserves the separate textures/alpha or that the resulting pack renders correctly.

Added opt-in --translucent-fx to the skiff-only projection tool. Pure emission source samples now take their emission RGB rather than max(combined, emission). A separate FX texture normalizes RGB in linear light and puts peak radiance into alpha. The hull remains on its own texture to avoid unnecessarily classifying it as translucent. Original rig and geometry are preserved. Candidate retains the preexisting 4096/12000 comparison budget; no runtime budget change is accepted.

The two targeted Python tests cover radiance reconstruction over black across 4096 varied RGB inputs (8-bit quantization error bounded), preserving non-FX hull pixels, source immutability and texture routing. Both passed with the bundled Python runtime.

Limitations: alpha blending is an approximation to additive emission and attenuates nonblack backgrounds; source emission support threshold 16 still drops the faintest samples; depth-slice overdraw may accumulate opacity; runtime export, visual and performance validation are pending. Original Downloads sources are read-only. No product JAR rebuild or gameplay integration yet.

## Candidate review

The complete projection process exited 0: 7 fitting attempts, density .073125, 12000 elements. Source-emission faces: 1303; FX translucent texels: 45,785; opaque FX texels: 2,518. Offline front threequarter, side and below renders completed and were inspected for the beam. The threequarter image shows the forward dark opaque beam replaced by translucent orange light. Hull surface stippling/black artifacts remain; this is not whole-model acceptance. Geometry, UV rectangles, rig, and all non-FX texels exactly match the preceding candidate. Two textures now use additional atlas storage; native performance is not certified.

`ModelTexture.toBlueprint` decodes the supplied Base64 PNG directly into a BlueprintTexture byte array (bytecode retained). Live generated-pack verification is recorded separately below once finished. No production model registration yet.

## Native pack failure and lossless packing repair

First live pack preserved both PNG files byte-for-byte and published 24 model routes; native client then rejected it with a StitcherException (could not fit 1024px weapon texture). This is a failed native load, not a pass. The new 4096 FX sprite consumed shared atlas capacity unnecessarily.

The FX exporter now packs all 1303 complete face rectangles with one-pixel gutters into 1024x1024 without resizing or cropping any face. Each remapped rectangle was compared against the first candidate: all RGBA pixels match exactly, and the hull image is byte-identical at the pixel level. Geometry and rig remain unchanged. Preview now reads each texture's own UV dimensions. Tests rerun after this packing change passed (2/2). Compact candidate is being checked in the same isolated server/client.

Compact FX alone still overflowed the existing shared item atlas (second native load failure retained). Minecraft 26.3 MaterialBaker explicitly checks the item atlas first, then the block atlas; item models accept either atlas. A strictly isolated QA pack now filters only the two verified skiff sprite IDs from items and inserts the exact same PNG resources into blocks. IDs are resolved by exact candidate PNG hashes from the current generated pack, not assumed stable obfuscated names. This tests lossless atlas placement rather than degrading other assets. Production pack-generation integration remains pending.

## Actual native result

With the skiff-only item-to-block atlas routing, the actual Vision client successfully loaded the pack and joined at 03:45:41 KST. The static source-derived candidate was spawned using the isolated debug fixture (not a flight/gameplay test). Day and night framebuffer PNGs were inspected. The model is present with no missing-texture checkerboard, but the beam that appears in the offline render is almost invisible in Minecraft. Hull striping, pitting and floating-looking fragments remain. **Not accepted for production.** Alpha cutoff, material classification and runtime emissive brightness require further investigation; neither the offline render nor the bytecode capability proves native beam fidelity.

No flight-path or strike spawn lifecycle integration was added in this turn, because source presentation and native resource constraints still failed acceptance. Generated pack bytes and actual native load now provide a viable route for the next iteration without reducing other assets' textures. The temporary model, local atlas override and owned client/server are cleaned up after capture; bounded master sleep prevention is retained.
