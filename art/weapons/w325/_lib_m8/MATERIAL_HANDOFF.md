# W325 m8 material handoff

Common specification: T=20, STYLE=material. Geometry and sparse decal audit below; native QA remains master-owned.

## harmony_21

Elements: 132; same-facing coplanar candidates: 0; nonpositive box dimensions: 0. Special callback sample coverage: 0.43% (equal per-face grid, not atlas-area weighted).

| Role | Kind | RGB | Detail |
|---|---|---|---|
| black_steel | metal | [38, 44, 43] | 0.45 |
| steel | steel | [142, 154, 153] | 0.55 |
| aluminum | steel | [192, 202, 197] | 0.45 |
| rubber | rubber | [24, 27, 26] | 0.35 |
| recess | dark | [13, 17, 17] | 0 |
| orange | paint | [191, 103, 42] | 0.3 |
| shell | paint | [194, 209, 198] | 0.8 |
| frame | metal | [29, 39, 34] | 0.45 |

End/chamfer/affected projection faces return the same material with detail=0.

## protostar_csu

Elements: 108; same-facing coplanar candidates: 0; nonpositive box dimensions: 0. Special callback sample coverage: 0.17% (equal per-face grid, not atlas-area weighted).

| Role | Kind | RGB | Detail |
|---|---|---|---|
| black_steel | metal | [38, 44, 43] | 0.45 |
| steel | steel | [142, 154, 153] | 0.55 |
| polymer | polymer | [79, 79, 58] | 0.6 |
| rubber | rubber | [24, 27, 26] | 0.35 |
| recess | dark | [13, 17, 17] | 0 |
| shell | paint | [176, 184, 149] | 0.9 |
| cream | paint | [215, 200, 180] | 0.8 |
| grip | rubber | [205, 191, 168] | 0.5 |

End/chamfer/affected projection faces return the same material with detail=0.

## philippis_b

Elements: 145; same-facing coplanar candidates: 0; nonpositive box dimensions: 0. Special callback sample coverage: 0.06% (equal per-face grid, not atlas-area weighted).

| Role | Kind | RGB | Detail |
|---|---|---|---|
| black_steel | metal | [38, 44, 43] | 0.45 |
| steel | steel | [142, 154, 153] | 0.55 |
| aluminum | steel | [192, 202, 197] | 0.45 |
| polymer | polymer | [51, 46, 38] | 0.65 |
| rubber | rubber | [24, 27, 26] | 0.35 |
| recess | dark | [13, 17, 17] | 0 |
| shell | paint | [119, 119, 108] | 0.95 |

End/chamfer/affected projection faces return the same material with detail=0.

## sondok_c

Elements: 142; same-facing coplanar candidates: 0; nonpositive box dimensions: 0. Special callback sample coverage: 0.15% (equal per-face grid, not atlas-area weighted).

| Role | Kind | RGB | Detail |
|---|---|---|---|
| black_steel | metal | [38, 44, 43] | 0.45 |
| steel | steel | [142, 154, 153] | 0.55 |
| aluminum | steel | [192, 202, 197] | 0.45 |
| polymer | polymer | [70, 46, 33] | 0.65 |
| rubber | rubber | [24, 27, 26] | 0.35 |
| recess | dark | [13, 17, 17] | 0 |
| green_emitter | glow | [49, 150, 69] | 0 |
| shell | paint | [184, 191, 168] | 0.95 |

End/chamfer/affected projection faces return the same material with detail=0.

## badlands_mk_24

Elements: 141; same-facing coplanar candidates: 0; nonpositive box dimensions: 0. Special callback sample coverage: 0.30% (equal per-face grid, not atlas-area weighted).

| Role | Kind | RGB | Detail |
|---|---|---|---|
| steel | steel | [82, 91, 91] | 0.7 |
| polymer | polymer | [35, 37, 36] | 0.65 |
| rubber | rubber | [24, 27, 26] | 0.35 |
| recess | dark | [13, 17, 17] | 0 |
| shell | paint | [115, 49, 46] | 1.0 |
| brass | gold | [170, 143, 91] | 0.5 |

End/chamfer/affected projection faces return the same material with detail=0.

## botheration_mk_28

Elements: 149; same-facing coplanar candidates: 0; nonpositive box dimensions: 0. Special callback sample coverage: 0.97% (equal per-face grid, not atlas-area weighted).

| Role | Kind | RGB | Detail |
|---|---|---|---|
| black_steel | metal | [38, 44, 43] | 0.45 |
| steel | steel | [155, 174, 178] | 0.65 |
| aluminum | steel | [210, 222, 220] | 0.5 |
| polymer | polymer | [61, 44, 32] | 0.7 |
| rubber | rubber | [29, 26, 22] | 0.4 |
| recess | dark | [13, 17, 17] | 0 |
| shell | paint | [48, 79, 81] | 1.0 |

End/chamfer/affected projection faces return the same material with detail=0.

## fussed_dark_mk_21

Elements: 142; same-facing coplanar candidates: 0; nonpositive box dimensions: 0. Special callback sample coverage: 0.83% (equal per-face grid, not atlas-area weighted).

| Role | Kind | RGB | Detail |
|---|---|---|---|
| black_steel | metal | [38, 44, 43] | 0.45 |
| steel | steel | [175, 183, 175] | 0.6 |
| polymer | polymer | [65, 68, 49] | 0.7 |
| rubber | rubber | [34, 36, 29] | 0.4 |
| recess | dark | [13, 17, 17] | 0 |
| shell | paint | [154, 164, 125] | 1.0 |

End/chamfer/affected projection faces return the same material with detail=0.

Final ADS: all seven OK. Output-only ZIP compression measure: 1146787 bytes; this is not the full distribution resource pack.

Final source-relief exceptions include Sondok rear/upper-tail receiver to suppress duplicate HAKKE lettering.
Final combined review: art/weapons/w325/_lib_m8/material_combined_review.png. Individual *_compare.png now show the material pass; identity_combined_review.png retains the previous flat identity pass.
No commit, Gradle, Minecraft or kit.py edits performed by worker.
