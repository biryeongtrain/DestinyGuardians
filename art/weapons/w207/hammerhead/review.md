# Hammerhead W207 reload continuity fix

`scripts/generate_reload_w207_hammerhead.py` provides an inert, self-contained standard-library generator. `generate()` returns absolute `Path -> bytes`; it does not write files. Master integration owns generated asset writes, runtime routing, shared W206 framing, skin arms and native QA. The inherited W206 profile/review are unchanged.

## Cause and concrete change

W114 `sample()` applies `u*u*(3-2*u)` independently between every pair of authored keys, forcing zero velocity at every internal movement key. Its `range(21)`, `frame/20` pose bank additionally quantizes the entire reload to 21 poses. Increasing bank density alone would retain the repeated easing stops.

W207 retains the W114 ten authored keys and their normalized times, body motion, feed displacement and cover angles. Each bounded Euler/translation channel now uses nonuniform monotone cubic Hermite interpolation with a shared PCHIP weighted-harmonic tangent at each internal key. Monotone movement keys retain velocity; flat spans and extrema have zero tangent; endpoints rest. This is C1 through movement spans without cubic overshoot. These are authored Euler channels with no angle wrapping, not interpolated extracted camera/rig rotations. Cover rotation is composed as a matrix with the body rotation before serialization.

Intentional holds remain: body at p=.34–.48, fully open cover at p=.34–.63, magazine seated through .23 and again from .72 to 1. For example, body yaw at p=.10 now has velocity approximately -76.99 degrees per normalized progress, where the previous per-key smoothstep forced zero. Gameplay duration, ammo and audio are not changed.

The bank has **61 poses (`p=i/60`) for each of body/magazine/cover in native/twohand**: 366 display parents, three shared geometry models and one item graph (370 assets), plus one W207 manifest. These are alternative poses, not simultaneously rendered geometry. The new graph is `destiny:weapon_reload_w207_hammerhead/hammerhead`: first-person `range_dispatch`, CMD float index 1, grip flag index 0, quantization 60. Both outer context fallback and range fallback preserve `items/weapon/hammerhead.json`'s exact original `model`. Other top-level item fields are copied.

This is **not proof of 60fps animation**. Actual item-state updates can remain server 20Hz. The denser bank removes the extra coarse 21-pose quantization; native update cadence still limits displayed motion.

## Surface, hinge and accepted presentation

Only the current `weapon_surface_w123/hammerhead{,_body,_magazine,_cover}.json` supplies geometry/textures. The 163 remodeled opaque elements remain body 70 + magazine 79 + cover 14, with every element, face UV, rotation and texture reference retained. No cluttered original geometry is imported. The W154 rigid XY belt stays part of the magazine, tips along muzzle -Z; feed mouth, twin drums and cover-mounted sight remain intact.

The cover pivot comes from `art/weapons/w123/hammerhead/design.json`; `p-Rp` compensation keeps that hinge stationary during opening. Magazine offsets use the body frame. Native endpoints copy the accepted canonical display literally; twohand endpoints copy the accepted `weapon/machine_gun/hammerhead_twohand.json` display literally. Interior twohand poses use the existing W32 charged-crossbow compensation, preserving its non-first-person displays. Every part has its original idle transform at p=0 and p=1.

W206 framing is intentionally not baked into these display parents: master must apply the shared framing/skin-arm overlay once. This preserves the same final framed idle endpoints without double application. Part names retain `_body`, `_magazine`, `_cover` for moving-part hand attachment. No arm mesh, finger geometry or length/extension setting is introduced.

## References and validation

Motion identity/timing follows existing `scripts/generate_reload_w114_hammerhead.py`, `art/weapons/w114/hammerhead/reference-notes.md` and `gameplay-provenance.json`. Actual gameplay PNGs `reference-08.png` (103.8s, open cover/exposed feed with partly occluded magazine handling) and `reference-15.png` (106.4s, settled ready) were viewed during this worker's preceding W206 inspection. Recording: [Aztecross, 2024-04-25, manual empty reload at 101.50–106.40s](https://www.youtube.com/watch?v=1lHv7453rUI&t=101). Perk-refill narration is not motion evidence. W123 `comparison.png` was also viewed; it is an offline surface reference, not native acceptance. No new source video, live DCC or user app was opened.

Ran `generate()` in memory in the W207-ready worktree. Checks passed for complete new-namespace output inventory, JSON/graph thresholds and exact original fallback, remodeled part/UV/texture equality, literal native/twohand endpoints, retained non-first-person displays, authored keys/holds, finite-difference derivative continuity at the internal keys, and cover hinge conservation at a representative open pose. Generated assets/manifest were not written locally. Only the generator and this review are new worker files; no historical asset/manifest was overwritten.

**Native pending master:** route this item with normalized CMD float1 and quantization60; regenerate shared hand/framing wrappers; inspect continuous body roll, magazine extraction/reseat, raised-cover hold and closure, final settle, and return to hip idle. Check native/twohand and both hand-display contexts, ADS exit/return and unchanged non-first-person fallback. Watch left hand release/return and moving-magazine contact without snapping or cover/feed penetration. The rigid belt and generic hand following do not reproduce all source hand/cover gestures or recovered IK. No build, client/server, input automation, duration change or native verification was performed by this worker.
