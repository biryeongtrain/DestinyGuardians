# W91 swap asset authoring

Only Austringer → Beloved and Beloved → Austringer. Each item contains its entire STOW and READY route. Float slot 5 is STOW 0..1 and READY 2..3, inclusive, with 21 samples per phase at .05 spacing. No helper offset is emitted; optional positive offsets below .001 keep the same sample. The reserved 1..2 gap holds the final STOW sample; values below 0 use incoming fallback; values above 3 hold the exact incoming HIP endpoint. Runtime owns valid values and cleanup.

Vanilla already selected the incoming stack. Flag 0 describes its CURRENT wire carrier: false = native stick, true = charged crossbow/twohand. It does not describe the outgoing weapon default grip. STOW inherits outgoing detailed geometry and corrects it for that carrier; READY inherits incoming geometry. Both directions have both carriers, including optional Austringer twohand.

Every model child contains only parent and display. Original cubes, face UVs, texture bindings, texture bytes, editable bbmodels, source displays and other item definitions are read-only inputs. Endpoint displays equal existing HIP native/twohand displays exactly. Only first-person poses animate. Other child contexts preserve the rendered source carrier variant, including twohand third-person overrides. The item wrapper always routes GUI, ground, fixed, head and third-person to the exact selected incoming original graph.

Pose deltas are locally authored, piecewise smoothstep: STOW exits downward with a strong pitch/roll; READY rises from below, lightly overshoots, and snaps back to exact HIP. They are not extracted/measured original game frames, render-frame interpolation, bone animation, hand motion or hand IK. The W30 catalog and bbmodels identify geometry provenance; W69/W70 establish generator and first-person wrapper conventions. No source video was measured here.

Handling owns all actual phase durations, zero-duration transitions, fire deadlines and ammo. Samples only describe normalized cosmetic progress. This generator contains no timing or gameplay mutation.

Reproduce with `rtk proxy python3 scripts/generate_swap_presentation_w91.py`; audit with the same command plus `--verify`. Verification reconstructs bytes, checks source inputs, matrix compensation for both hands, exact endpoints, non-first-person preservation, float32 phase routing and the output inventory without writing. No build, client/server, Blockbench or user app was run.

Parent preview: asset-samples.json lists all 168 children, item IDs, current carrier flags, selectors, parent models and both first-person displays. Review both carrier choices in both directions and both hands, especially STOW 0/.55/1 and READY 0/.8/1. Native pack codecs, actual framebuffer framing, hand/carrier continuity and gameplay integration remain central verification.

Review note: the initially observed SwapPresentationW91Test.child compared all child non-FP contexts to native even for twohand; its endpoint check also required the full twohand display. Existing twohand third-person overrides differ from native. Preserve carrier-specific source contexts when reviewing that assertion; this leaf does not edit tests.
