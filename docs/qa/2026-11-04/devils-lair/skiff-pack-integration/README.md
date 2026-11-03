# Skiff product asset and shared atlas routing — 2026-11-04

Adopts the previously reviewed coarse candidate without new surface tuning. Only the root name
changes to `dl_skiff`; 12,000 elements, the hierarchy, two embedded PNGs, and six source-tagged
skeletal clips remain identical. See provenance.json and ../skiff-source-retarget for source evidence.
This registers the asset before BetterModel scanning; it does not yet spawn a strike ship.

`PackAtlasRouting` runs before the profile-arm early return in pack generation. The data catalog
matches exact PNG SHA-256 under an explicit texture prefix. It appends exact regex filters to
items and singles to blocks, preserving other sources. It is idempotent, handles generated name
changes/identical sprite aliases, rejects conflicting routes, and never resamples PNGs. An external
model replacement that changes PNG bytes is left alone and reported as an unmatched hash.

Targeted tests: 4 atlas routing + 2 model install/contract tests passed. The first model contract
run failed because the old test assumed all registered models were single-texture infantry;
the revised contract explicitly checks this noncombat prop's two textures and six source clips.
All original enemy clip requirements remain unchanged.

Actual Fabric: 14 actor tests passed. The generation callback matched bettermodel:item/x and /y.
The GameTest server exits after profile-graph publication, before ZIP finalization; its incomplete
ZIP is recorded in gametest-pack-limitation.json and is NOT a client-load success.
Persistent isolated server pack validation is recorded separately when complete.

Vision/native flight, client atlas load, FPS and speaker checks have not been performed in this batch.
Arrival/drop/departure renderer integration remains outstanding. No Downloads source was modified.

Persistent server exposed a real packaging defect: the initial pre-finish `addData(atlas)` calls
were consumed by Polymer's atlas accumulator after its merge had already run. No atlas JSON
was present in the completed ZIP, and the first client load failed. This is not a passing client run.
Fix: seed empty catalog atlas definitions in RESOURCE_PACK_CREATION_EVENT, then replace the
already-merged output through a resource converter in pre-finish. A real DefaultRPBuilder
pipeline regression is added to cover merge ordering, not just the pure JSON helper.

The DefaultRPBuilder regression requires a Fabric launcher (plain JUnit failed at CommonImpl
initialization), so it lives in PackAtlasRoutingGameTests. Actual Fabric run: 1/1 passed,
with both routed atlas definitions present in the final builder output. This is the packaging
boundary regression; final native client acceptance is still a separate check.

## Final native acceptance for this asset/pack boundary

- Persistent isolated server successfully finalized ZIP; generated-pack.json records both atlas
  definitions and byte-exact PNG hashes. No local resource-pack override (`resourcePacks:[]`).
- Fresh Vision client entered the world with no StitcherException. Native blocks atlas 8192²,
  items atlas 16384². This remains a large shared atlas footprint, not a broad GPU compatibility claim.
- native-skiff.png: actual framebuffer, daylight, debug fixture `dl_skiff`, source_80a8a51e accepted.
  Recognizable hull, texture and lights; residual stippling/gray FX remain as previously documented.
  Under the user's relaxed brief-display requirement, no further surface polish was performed.
- Server command fixture spawned the model and placed the camera; no native movement/combat input
  acceptance is claimed. Control state showed no lease, held keys, pending steps or native movement.
- Final full regression: 2582 tests, unchanged baseline 16 failures, no new failure identities.
  Real Gradle JAR completed. Source/pack changes are verified; strike flight integration is not.
