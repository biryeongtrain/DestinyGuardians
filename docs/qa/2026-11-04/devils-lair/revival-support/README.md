# Fractional player support for fall recovery and revival

The previous player safety checks inspected only `floor(feet).below()`. For bottom slabs the support is in the same integer cell as the player's feet, so this rejected a valid surface. A full-footprint ray requirement would also reject valid stair-edge stances with part of the player overhanging the lower step.

Both safe-position recording and revival completion now share DevilsSpatial.groundedPlayer: loaded feet cell, dry feet, unobstructed body and actual collision overlap in a thin 0.08-block contact slice directly below the footprint. Arena containment remains in the session. Spawn pads still use their existing conservative full-footprint checks; this does not change enemy placement.

## Evidence

12 actual server GameTests pass. The new fixture places a bottom slab over air and confirms the old below-cell query misses it, then verifies acceptance using the new helper. It also verifies full blocks and a partially overhanging stair-top stance; air gaps, embedded feet, an obstructed body, removed support and flooded feet are rejected. Temporary block states are restored in finally.

The fixture tests the shared spatial helper with real player dimensions and Minecraft collision shapes; it does not run the entire session death/revival animation or establish native visual acceptance. Existing 11 actor/audio cases also pass. Screenshots and in-game feel remain pending; no completion commit is claimed.

Final JUnit: 2550 tests / 16 failures / 0 errors. Failure identities match prior baseline: True. Existing failures remain unresolved. Gradle --continue completed jar; combined exit is failure due to tests. JAR SHA256 `21fe1a47f8fbcdaef545b90e9f1c4b556ac56c98082eda62e993a9db8fe2c35e`. Computer Use preflight again reported the Mac locked, so no native client was launched.
