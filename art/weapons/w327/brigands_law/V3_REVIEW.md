# Brigand’s Law V3 hero

V2 was rejected. V3 rebuilds the actual bow and exposed barrel, swept receiver, layered open muzzle, grip rake and palm swell, articulated gold lever, lateral steel tines and open trigger guard. The original side/top/front projections calibrate the geometry instead of stretching the source to a generic silhouette.

246 assembled cuboids (242 body + 4 inherited detachable heel), 1024×512 atlas, 963 visible source-mapped faces and 513 hidden faces. Distinct flank navy motifs follow exact source coordinates; source spider engraving is redrawn in the circular blue seal. Ivory fields remain calm; the steel barrel uses section-specific directional tones and narrow machining lines.

Existing Recluse, Blast Furnace and Gnawing Hunger runtime geometry and UV were inspected and actually rendered with the same camera, light and projected width as V2/V3. Evidence: `review/v3/same-size-benchmarks-v2-v3.png`, `original-v2-v3.png`, `close-views.png`; individual 1200×1000 views are preserved.

Validation: parsing, positive bounds, unique names, six normalized UV faces, original Blender SHA and active Dead Man Walking ADS topline pass. A rotated-cuboid separating-axis contact graph is one connected component at 0.025 model-pixel tolerance, including the assembled magazine. The small gaps in initial clay review are closed.

Supplied Blender file has no hand rig or actions. The existing base’s 61 reload poses and overlay are inherited; this is not a source animation conversion. Native grip/ADS/reload, pack load and 10–20 display review remain master-owned and pending. No main writes, gameplay edits, commits or native QA by worker.
