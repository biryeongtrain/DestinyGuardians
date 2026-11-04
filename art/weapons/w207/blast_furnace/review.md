# Blast Furnace W207 — continuous reload movement and denser pose bank

The W114 `sample()` applies `t*t*(3-2*t)` separately to every pair of authored keys. This forces zero velocity at every internal waypoint, including the middle of raising and recovering the rifle. Its 21 poses at `i/20` also coarsen presentation when runtime progress advances over the existing gameplay duration. W207 replaces the generator path for this weapon; runtime routing/quantization and skin-arm sampling are integrated by master.

`scripts/generate_reload_w207_blast_furnace.py` provides a self-contained standard-library `generate() -> dict[Path, bytes]`. Import and generation perform no writes. It returns only the new `weapon_reload_w207_blast_furnace` model/item namespace and `art/weapons/w207/blast_furnace/manifest.json`. It does not invoke or overwrite W114/W123/W206 generators, assets or manifests.

## Concrete change

- Generate **61 poses at p=i/60**, each with body/magazine and native/twohand displays: 244 pose wrappers, two geometry leaves, one item graph, plus the manifest (247 assets, 248 returned paths). Part names retain `_body` and `_magazine` for the master's contact recognition. No invented cover, bolt, fingers, hand geometry or arm extension.
- Preserve the W114 movement landmarks and normalized phase times: raise at .10/.22, extracted-magazine hold .36–.48, approach .62, seated .72, recovery .80/.90, ready 1. Gameplay reload duration is not shortened or otherwise set here.
- Use scalar monotone cubic Hermite channels for rotation XYZ, view translation and local magazine offset. Adjacent spans share weighted harmonic interior tangents (PCHIP). Continuing movement passes through internal waypoints with nonzero velocity; actual holds and direction reversals have zero tangent. Both endpoints have zero velocity to meet stationary idle. Constant channels remain exact constants. The rotation channels stay within the original bounded Euler path, without angle-wrap crossings; no independent per-key smoothstep remains.
- Source geometry exclusively from current `weapon_surface_w123/blast_furnace_body.json` and `_magazine.json`: **92+5=97 cuboids**. Preserve every element, UV, element rotation and texture slot; no recentering. Native display comes from remodeled full `weapon_surface_w123/blast_furnace.json`. Accepted `weapon/pulse_rifle/blast_furnace_twohand.json` is read for its display only; its old geometry is never imported. Reproduce the existing inverse charged-crossbow carrier for intermediate twohand frames and copy the exact accepted endpoint display objects for both parts at 0 and 1.
- Item graph dispatches first-person contexts through float index1 (0..1), then boolean flag0 (native/twohand). Outer non-FP fallback and range fallback are exact deep copies of `items/weapon/blast_furnace.json`'s original `model`; its other top-level metadata is retained. Accepted canonical ADS/inspect/third-person geometry and W152 stock/optic correction stay behind that unchanged fallback.

A 61-pose bank removes the 21-bank quantization loss. **It is not proof of 60fps:** server item-state updates remain up to 20Hz. Client cadence, network sampling and actual smoothness still require master native review.

## References

Paths are repository-relative. The weapon-art skill and Ace/Izanagi study were read in W206 and inform retention of the remodeled semantic solids.

- `scripts/generate_reload_w114_blast_furnace.py`: existing keys, per-segment smoothstep cause and 21-pose output.
- `art/weapons/w114/blast_furnace/reference-notes.md` and `gameplay-provenance.json`; [KackisHD Blast Furnace footage](https://www.youtube.com/watch?v=SRNv0YDgYBM), 38.70–40.95s. Actual `reference-03.png` (39.15s) opened during W207: steep muzzle-up rifle with the handling hand at the rear/lower receiver. Actual `reference-00.png` and `reference-09.png` were opened during W206, showing ADS before reload and magazine handling at 40.05s. BRAVE reissue/shader differs; handling order is reference evidence, not exact recovered animation, camera or IK.
- `art/weapons/w123/blast_furnace/design.json`, full/body/magazine model JSON and `comparison.png`: current long Black Armory receiver, red barrel/breech, open stock, foregrip and rear bullpup magazine. Retain the W201 rear reload contact `[7.4,8,11.78]` through the master's hands path, rather than replacing it with a front-magazine target.
- `scripts/build_weapons_w30.py:two_hand_display` and `scripts/generate_reload_models_w100.py:rotate`: existing inverse carrier and rotationXYZ conventions reproduced locally without running either generator.

## Checks performed

Compiled/imported the owned source and called `generate()` in memory only. Checked 61 ordered thresholds, both grip branches, exact original graph fallbacks, exact accepted endpoint displays, unchanged 92/5 elements and texture/UV data, finite intermediate transforms and unchanged non-first-person displays. Finite differences around continuing .10/.80/.90 pitch keys show matching nonzero left/right velocities; the genuine .36–.48 hold and .72–1 seated magazine offset remain fixed. Checked returned paths stay in the new namespace/manifest. No generated output was written in the worker worktree, no build/game/CU/server/native operation ran.

## Pending master native verification

After routing to `destiny:weapon_reload_w207_blast_furnace/blast_furnace`, normalized CMD float1 with quantization60 and flag0 native/twohand:

- Play a complete reload at unchanged gameplay duration; raise and recover should flow through internal keys rather than pause at each one. The deliberate magazine-out hold must remain recognizable.
- Follow rear bullpup magazine extraction/approach/reseat with the left palm; inspect contact continuity, no forward-magazine substitution and no hand snap during phase handoff. Retain the W206 normal-length skin arms and framing.
- Compare first/last poses to accepted HIP for both grip modes, including mirrored first-person contexts; check ADS entry/exit, inspect/3P fallback, cancel/swap/death interruptions and return to idle.
- Open actual native PNGs/contact sequences to judge clipping, barrel/stock/optic visibility and part separation. No native success, final visual acceptance or 60fps claim is made by this worker.
