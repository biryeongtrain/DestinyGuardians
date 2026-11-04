# Sepiks warp pads and commit safety

Selection previously respected same-tick/pending spawn reservations, but actual
teleport commit only checked world point membership, general collision and player
distance. It could enter a newly reserved spawn footprint; selection also used a
different distance condition from commit.

DevilsSpatial now shares one predicate for selection and commit: body bounds,
terrain/hazards/occupancy/reservations,12block distance,1block body buffer and a
living nonspectator target firing line. Public commit recheck accepts only one of
the four exact authored anchors and rejects the current anchor. DevilsMob calls
the live environment commit hook immediately before setPos; the session passes
pending spawn footprints and records the accepted warp footprint for the tick.
The default hook refuses commit, so an adapter without validation cannot silently
allow movement. No source marker, warp timing, damage or animation was changed.

Validation:
-72strike JUnit tests passed.
-Generated NBT-world GameTest1/1 passed: all four authored pads admit the real6.5
 block Sepiks body from entry; each has another valid warp destination. All-pad
 reservations prevent selection; new reservations or an approaching Guardian
 reject the previously selected destination; a nonauthored offset is rejected.
-The test directly exercises spatial selection/commit helpers with a real typed
 probe. It does not advance a live boss through its16tick warp windup or observe
 particles/audio/native input. Those remain live acceptance tasks.
-Full2546JUnit: unchanged16failures,0errors, no newly failing cases. Gradle jar task
 succeeded under --continue; packaged changed classes match artifact.json.
-No native client launched and no acceptance commit made in this batch. Goal active.
