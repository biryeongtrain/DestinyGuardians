# Bounded density fitting — 2026-11-04

Skiff-specific fitter now narrows the packed/overflow density interval instead of reverting to the first coarse fit. Same 12000-face/4096-atlas comparison budget; no global mob baker changes. 7 actual projection attempts selected density .073125 versus .04117 in prior generic fit, using .9125 of padded atlas area. Actual packing succeeds; 20 source bones, finite geometry/UVs, unique element ownership checked.

Actual Blender threequarter PNG inspected: smoother hull than preceding candidate, preserved brown/purple scheme; visible black card fragments and opaque forward glow beam still fail acceptance. Neither this candidate nor the larger comparison budget is integrated into runtime. Need source-material-aware additive FX treatment and close-range surface validation.

Native test in parallel independently found similar stippling on production Fallen/Hive. That is separate from this unregistered skiff candidate. Do not infer runtime performance from this concurrent session.
