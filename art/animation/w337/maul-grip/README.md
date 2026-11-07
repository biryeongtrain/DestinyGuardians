# W337 Burning Maul physical grip

The R2 export previously preserved wrist displacement around a rotation-only reference. Its baseline widened the anatomical wrist pair, while the item node stayed aligned to one wrist instead of the actual shaft. Both errors were visible in the native idle frame.

Only the five Maul locomotion loops now use absolute R2 chest-relative wrist positions. Existing source elbow planes and roll drive the two-arm solve. The actual model shaft is fitted between the two visible palm volumes, including the +2Y third-person model display transform. The left lower palm is at raw model Y5.25 inside the existing lower sleeve; the right upper palm moves along the same continuous shaft with the R2 trajectory. Source wrist roll supplies the remaining prop orientation. This compensates for source props/final procedural IK absent from the R2 handoff; it does not claim an extracted original prop/socket transform.

`validation.json` independently decodes the serialized payload and actual mesh bounds. Both distal skin boxes intersect the physical shaft in all five bounded clip samples. Other26 raw animation object bytes and all Maul non-arm channels match main. Original periods and exact endpoint times are unchanged.

Review PNGs show actual nonzero-volume skin and prop cuboids with diagnostic colors: orange right arm, cyan left arm, gold head. Before/after use idle3.425s from the same source period. In this follow-up, before is the integrated first two-hand fit (FC83 payload); after slides only the prop along its shaft. The sleeve5.25 grip is0.5u inside its lower bound. Single-pose actual OBB SAT clears the head from both arms/head/chest; this is bounded evidence, not an all-frame clearance claim. They are offline geometry evidence, not native shading or client acceptance. Master owns the native idle6.87s, four movement directions, attack and recovery review.

Reproduce bounded audit/review with separate headless Blender:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python art/animation/w337/maul-grip/review.py
```

Regenerate only five Maul clip objects while preserving the other26 main object bytes:

```sh
python3 scripts/art/w336_class_locomotion.py --export --maul-only
```

Raw source/evaluation caches remain outside the repository. See `provenance.json` for original/model hashes and limits.
