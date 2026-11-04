# hammerhead W154 feed correction

163 assembled opaque cuboids (0 triangle adapters; cap 1000). 8 linked rounds follow an XY curve from the receiver into the magazine. All tips point along -Z, parallel to the muzzle. The final round is seated in the existing magazine opening; exposed intermediate rounds form the photographed feed, not loose ammunition outside the housing.

The original semantic body, sight, magazine housing, material palette, display, scale, anchor and pivot are preserved. The face atlas is deterministically repacked for the new belt solids; existing material/UV motifs remain authored by the original compiler. Retrofit case band paint uses longitudinal Z after the axis correction. Hammerhead full = body + magazine + cover; the rigid corrected belt belongs to magazine.

References opened: actual /tmp/destiny-weapons-w31/references/ID.jpg for all three MGs, pre-change comparison.png files, and main sealed docs/qa/2026-10-26/w153/ads-heavy.png. comparison.png shows actual photo, three full views, and three receiver-to-magazine detail views with housing context.

Reproduce using bundled Python -B scripts/fix_belt_feed_w154.py; --verify compares every generated output. Targeted regression: scripts/tests/test_belt_feed_w154.py. Historical tests are not claimed as all passing. Pinned W114 reload source/frames and shared surface manifest are unchanged; master must derive shared pack, W151 pulse/ADS and W153 MG body/ADS.

Native HIP/ADS, static sideview and representative reload remain pending master, as do parser/pack and 10-20-display observations. Offline geometry/UV/CPU images do not prove native acceptance. Static cuboid noses and rigid links approximate the photographed rounds; no new dynamic belt deformation, IK, audio or combat work.
