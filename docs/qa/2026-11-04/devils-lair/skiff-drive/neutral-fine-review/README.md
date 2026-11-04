# Neutral-lit static skiff candidate

Offline Blender review only; not integrated. Original Drive source remains untouched.

Skiff bake now opts into the same lighting coefficients/world/view transform as source inspection. Other species retain the previous default. Normalized camera yaw was reversed to match the original source orientation. Candidate uses an experimental 4096 atlas and 12000-quad budget, retaining all 20 source bones plus emission groups. This is a comparison experiment, not an accepted runtime budget change.

Observed: brown hull and purple markings now match source intent much more closely; fine seams remain visibly stepped/pitted. Forward optics beam cards become opaque dark projections; these need a separate additive/translucent treatment or a source-grounded core-emission extraction. Not ready for runtime adoption.

Automatic fitting tried density .18, .041, .099 and retained the sparse .041 fit after the .099 atlas overflow. A bounded search between the fitting and failing densities can recover quality without simply increasing the budget again. Keep the failed initial candidate evidence.
