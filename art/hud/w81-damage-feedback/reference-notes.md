# W81 damage-feedback gameplay reference

Research only, 2026-10-24. Actual historical Destiny 2 creator gameplay was decoded and visually inspected. Source observations below are separate from authored Minecraft layout policy. No damage/audio/production assets, code, builds, app state, or Git history were changed by this sidecar.

## Sources and retained evidence

- **Automatic rifle:** [xHOUNDISHx — Ammit AR2 gameplay](https://www.youtube.com/watch?v=w3CYQprLoc0&t=19), uploaded 2022-09-01. Reused the existing W69 0–65 s private clip; its SHA256 matches W69's saved provenance. [Full source frame at 19.500 s](references/ammit-19.500s.jpg), [19.700 s](references/ammit-19.700s.jpg), [20.000 s](references/ammit-20.000s.jpg), and [comparison sheet](references/ammit-sequence.jpg).
- **Explosive Payload:** [Seven_11 — Taraxippos (Gutshot Straight + Explosive Payload) Damage Test](https://www.youtube.com/watch?v=2cqBmDC_z_4), uploaded 2023-05-07. Downloaded only this complete 21 s public short (640×360, 30 fps, video only, approximately 825 KiB). [Retained clip](references/ep-taraxippos.webm), [metadata](references/ep-source-metadata.json), [comparison sheet](references/ep-sequence.jpg). [10.000 s equipment frame](references/ep-10.000s.jpg) visibly names Taraxippos, Gutshot Straight, and Explosive Payload; EP identity is not inferred solely from its title.
- [Provenance, timestamps, byte sizes and SHA256](references/provenance.json) pins all delivered reference files and the reused Ammit clip. Filename seconds locate requested video seeks, not measured shot onsets or verified exact decoded PTS. JPEGs are uncropped gameplay frames recompressed at source resolution. Contact sheets resize and label them; no gameplay content was redrawn.

The W43 extraction was inspected: it pins Oracle weapon formulas, not Destiny framebuffer/number animation. W43 QA images are this project's Minecraft tests, not original Destiny 2 evidence. Existing Long Arm reload footage was also surveyed but did not establish an EP roll, so it is not delivered as EP evidence.

## Direct source observations

| Evidence | Visible result | Scope of conclusion |
| --- | --- | --- |
| Ammit 19.500 → 19.700 → 20.000 s | Ammo decreases 28 → 26 → 24 while several labels remain around the aimed combatant. White `1,253` and yellow `1,880` labels coexist; yellow labels are visibly larger. | Repeated automatic fire can leave multiple labels on screen, with visibly distinct ordinary/precision styling. This is not one replacing total. Other enemies, a teammate, and effects are present; do not attribute every peripheral number to the rifle. |
| Ammit 20.000 s | Several yellow labels crowd/partly overprint one another near the sight; other labels sit to the side. | Separation is useful but **strict nonoverlap is not an observed original-game guarantee**. |
| EP 3.000 s | White `1,468` sits left of the target while yellow `2,822` sits to the right; the ammo display reads 14. | EP-equipped precision fire visibly presents a white component alongside a yellow component, not a single all-yellow total. Identifying the white component as payload is consistent with the separately sourced W80 nonprecision-payload mechanic; the framebuffer itself does not label component types. |
| EP 3.400 s | Ammo reads 13; two yellow `2,822` labels are vertically separated while white text also remains visible. | Successive hits can coexist at distinct positions; this does not measure a fixed lane or gap. |
| EP 15.000 s | Yellow `2,821` and white `1,761` appear as separate labels on the same target, ammo 14. | Corroborates two-component presentation. Gutshot Straight/Unstoppable Shot and historical sandbox conditions prevent treating these values as base EP damage coefficients. |
| EP 16.000 s | Two white values, `1,720` and `1,355`, appear on opposite sides of the target, ammo 13. | Consistent with a nonprecision/body hit displaying two white components. Exact hit location/event identity is visually inferred, not instrumented. |
| EP 15.000 → 15.400 s | Yellow text changes screen position upward/right while white text is no longer clearly legible at 15.400 s. The camera, target, and environment also move. | Confirms transient/repositioned presentation only. **Independent rising trajectory, fade curve, lifetime, and relative component expiry were not isolated or measured.** |

White ordinary/body versus yellow precision is the supported visual direction in these samples. Yellow is not a universal proof of a precision hit across all Destiny effects/debuffs. Exact font, RGB, size ratio, pixels, movement speed, delay between EP components, and current sandbox behavior are not established here.

## Authored layout policy for the parent implementation

The following are local readability decisions, **not extracted Destiny constants or a specification of Bungie's algorithm**:

1. Accept only already confirmed damage events. Keep event values and ordinary/precision identity intact. Layout must not invent hits, change damage, or promote white payload feedback to yellow because another component crits.
2. Allow several recent confirmed numbers to coexist during automatic fire. Keep EP impact/payload components individually readable rather than silently summing them into one critical label.
3. Resolve occupied label bounds deterministically, using the actual rendered text width/height and a local margin. Prefer nearby free positions; do not assume a fixed character count or that alternating two lanes is enough for rapid fire.
4. Any upward drift, spacing, lane count, stacking order, overflow cap, fade, and lifetime are authored tuning. Choose them for readability and bounded cost; do not cite the source video as having supplied exact timings or spacing.
5. Verify rapid-fire same-target traffic, simultaneous EP components, mixed white/yellow labels, different digit widths, multiple targets/viewers, and expiry freeing occupied space. These are suggested layout acceptance cases, not work executed by this reference sidecar.

Historical source frames support differentiated, transient, spatially distributed numbers. The parent’s generic nonoverlap policy is a deliberate readability adaptation; source footage itself still permits crowding.
