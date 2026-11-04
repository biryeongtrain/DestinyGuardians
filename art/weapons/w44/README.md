# W44 aim data provenance

`scripts/extract_aim_w44.py --source /tmp/destiny-w43/weapon_formulas.json --verify`
checks the pinned source SHA, 63 generated profiles and attribution without writing files.
See `extraction.json` for exact stat hashes, source mappings, policies and source revisions.

The W40 official selected-item Handling/Stability/Zoom/Recoil Direction stats are not
necessarily perk/mod-adjusted current sandbox values. Handling ADS curves and independent
falloff scalars are based on the pinned May 2026 Foundry snapshot. Main research applied
the official May 29 AR/Pulse corrections; this does not update all balance values to today.
Machine gun 1.6 is explicitly a community guess. Visual Zoom is **not** the falloff scalar.

Kick is degrees; bloom and recovery are normalized server tuning. These are not ripped
Destiny recoil patterns. Sword/glaive profiles are neutral and ordinary ADS excludes them.
The copied source snippets are retained under the adjacent MIT-LICENSE and UNLICENSE;
packaged W43 license copies already accompany the runtime extraction.
