# Special actor admission regression

Actual generated NBT-world GameTest failed on both shield rounds: SP.S1/SP.S3
fail the stationary-flyer line-of-sight rule from the entry seat; SP.S2 fails collision.
The log preserves all three completed search attempts for each slot. Walker + two
Brigs + entry cohort and Sepiks + guard cohort produced no admission failures.

This is a fixed entry-seat fixture, not proof that every live player location fails.
SP.S2 collision still needs separation into map, entity or reservation obstruction.
Do not remove collision/distance checks or label blocked placements as kills.
No production map/placement change made in this batch. No Vision/native/audio QA:
Computer Use reported a locked Mac. Server exited normally after failed test.

## Fix and verification

The diagnostic server run separated live reservations from geometry: S2 intersected
five wall blocks at local x65, y17..19, z69..70; S1/S3 had empty bodies but entry rays
hit local (63,15,34)/(59,15,31). `diagnostic-fixture.java.txt` preserves the diagnostic
probe and candidate scan, which was removed from the final test source.

The map generator now authors three alternate floating pads per shield lane, inside
the same three arena sectors. It preserves every spatial safety rule and runtime
search budget. Source XYZ values are authored adaptations, not extracted markers.
Downloads GLBs were read-only. All four decompressed grids are unchanged; the old
Rocketyard gzip OS header was retained after regeneration differed only in that
header byte. Final DGZONE, NBT and route bytes remain unchanged. Only markers and
map provenance/manifest changed.

- Targeted Maps/Spatial JUnit:11/11 passed.
- Real generated-world GameTest:1/1 passed, including all ordinary packs, RF entry
  reservations, BL Walker/two Brigs/entry cohort, SP boss/guards and both shield
  trios plus adds from each of three arrival seats.
- Additional shield checks move the test player to SP.C.ground *after* admitting
  Sepiks from arrival, retaining the actual accepted boss AABB. The initial version
  mistakenly attempted to spawn Sepiks next to a central player, correctly rejected
  by the 12-block rule; `first-fixed-report.xml` retains that fixture failure.
- Full JUnit:2541 tests,16 failures,0errors. Exact suite/case failure set unchanged
  from control-notices baseline; no failures waived.
- Gradle `jar` succeeded with `--continue`; combined command exit1 reflects test
  failures. Packaged map resources byte-match sources; see artifact.json.
- Computer Use still reports locked Mac. No Vision/native/audio acceptance, no
  commit claiming final visual acceptance. No owned client or server left running.

Remaining spatial acceptance: arbitrary moving player/entity occupancy, players
close to a required shield lane, Sepiks alternate warp footprints, and native full
fight. Static admission fixtures do not demonstrate these conditions.
