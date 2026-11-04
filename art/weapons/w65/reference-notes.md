# W65 ammo-credit source audit

The pinned source selects **six weapons: three hand cannons (0.71), three machine guns (0.65)**. The earlier LFR assumption is incorrect. Both selected LFR curves omit `ammo_percent`. The Duke footage shows ammo HUD credit before visual recovery finishes; it does not establish earlier fire eligibility or cancellation behavior.

[Machine-readable audit and SHA-256 pins](references/source-audit.json) · [Verbatim source excerpts](references/source-excerpts.md).

## Selected mappings, derived from extraction

Joined W46 `entries[].id` → W43 `entries[]` family/category/subfamily → `weapon_formulas.json[family].cat[category].reload`; compared the exact curve against W46 `reloadCurve` and joined official selected-item evidence by ID/hash. All extractor literal source pins and all W46 `sourceHashes` matched current local bytes. Seven source category rows explicitly contain the field, but only six catalog items use those categories. No family inferred from a prior task assumption.

| Selected ID | Bungie hash | Oracle family / category / subfamily | Explicit ratio | Base full / authored ammo ticks |
|---|---:|---|---:|---:|
| `duke_mk_44` | 2112909414 | Hand Cannon / 120 RPM / Aggressive | 0.71 | 59 / 42 |
| `austringer` | 3055790362 | Hand Cannon / default / Adaptive | 0.71 | 53 / 38 |
| `seventh_seraph_officer_revolver` | 3037520408 | Hand Cannon / default / Precision | 0.71 | 52 / 37 |
| `fixed_odds` | 2194955522 | Machine Gun / default / High-Impact | 0.65 | 106 / 69 |
| `hammerhead` | 603242241 | Machine Gun / default / Adaptive | 0.65 | 91 / 60 |
| `retrofit_escapade` | 3103325054 | Machine Gun / default / Rapid-Fire | 0.65 | 90 / 59 |

The last column uses existing W46 full ticks and `ceil(fullTicks*ratio)`; it is an authored 20Hz adaptation, not a new measurement of the original game. Six of63 are selected;57 retain existing policy, including five unsupported swords. `line_in_the_sand` (946443267; Precision) and `stormchaser` (3652506829; Adaptive_Burst) both map to **Linear Fusion Rifle / default**, whose curve has no ratio.

## Pinned code, defaults and units

Oracle repository: https://github.com/d2foundry/oracle_engine, commit **dcd0c7d302b056ffbb532edcb711d724a17ca8c1**, date **2026-05-20 as recorded by W43/W46**. Commit attribution is inherited from existing provenance, with local source hashes verified; no upstream date refresh performed. The audit JSON pins every consulted source and contains commit-specific links. Existing W46 MIT/UNLICENSE attribution applies.

- `weapon_formulas.json:440,450,460,470`: explicit Hand Cannon0.71 (default,120RPM,Eriana,LastWord). `:601,611,621`: explicit **Machine Gun**0.65 (default,Xenophage,Overture). Only default/120RPM hand-cannon and default machine-gun categories occur among the selected six.
- `build.rs:234–266,358–364,730–744,761–767`: JSON categories deserialize to `ReloadFormula`; each intrinsic selects its category, and the value is retained in generated `RELOAD_DATA`. `weapon_constructor.rs:45` retrieves that generated reload formula.
- `build.rs:615–622`: `ammo_percent: f64` has bare `#[serde(default)]`. The missing-field default is **0.0**, from Rust `f64::default()`, not1. `rs_types.rs:101–106` also derives `Default` with an `f64` field. No custom default1 is present on that path. A missing ratio is not proof of an instantaneous gameplay credit; retaining full-duration credit for those weapons is conservative consumer policy, not an Oracle default1 claim.
- `rs_types.rs:90–98`: quadratic evaluation is `evpp*x*x+vpp*x+offset`; `stat_calc.rs:24–29` initializes `reload_time` from it and `ammo_time=reload_time*ammo_percent`. This is a dimensionless fraction, not an additive duration or a fire-unlock field.
- The reload response fields are plain `f64` (`rs_types.rs:149–154`). `d2_enums.rs:250` declares `Seconds=f64`, but that alias alone does not annotate these fields. W46's extraction evaluates the quadratic as **seconds**, then uses `ceil(seconds*20)` (`extract_weapon_timing_w46.py:153–166`). The separate `/30` firing-frame conversion in `build.rs:691–703` must not be applied to reload coefficients or the ratio. Curves are historical community approximations, explicitly called approximate in `stat_calc.rs:34`, not official current-sandbox measurements.

## Modifier inconsistency and deliberate adaptation

`stat_calc.rs:60–73` calculates the base pair first, then changes **only `out.reload_time`** using `reload_time_scale` (and a special bow calculation). It never recomputes `out.ammo_time`. Under scaling, its final pair therefore need not retain the authored ratio; sufficiently short modified full time can precede the unchanged base ammo time. Do not cite this function as proof that Oracle correctly rescales both deadlines with Outlaw.

The main task explicitly intends **ratio at captured server full duration**, not exact replication of that apparent inconsistency: capture existing full duration once, then calculate `ammoAt=start+ceil(capturedFullTicks*explicitRatio)` separately from full-ready. Applying the ratio after full-tick quantization can differ from rounding the raw seconds product; the requested order is deliberate.

| Duke scenario (main-authored integration contract) | Captured full ticks | Ammo-credit offset | Fire gate |
|---|---:|---:|---:|
| Normal |59|`ceil(59*0.71)=42`|59|
| Outlaw |33|`ceil(33*0.71)=24`|33|

These are the main-authored implementation examples, not runtime results from this audit or timings measured in the clip. Keep the sound full endpoint and HUD reload-progress endpoint at full-ready. Ammo credit alone supplies no new early-fire claim. Existing cancellation rules need their own implementation review; the evidence here establishes no cancellation rule.

## Duke frames: what is actually proved

Re-inspected the existing [27.100 full frame](../w64/references/duke-pre-ammo-27.100.jpg), [27.200 full frame](../w64/references/duke-post-ammo-27.200.jpg) and [selected contact sheet](../w64/references/duke-selected-contact.jpg); all hashes match W64 provenance. Source: [Rin, Deleted Duke - Outlaw + Rampage, Keeping Duke - Rangefinder + Kill Clip](https://www.youtube.com/watch?v=-oS68Bu_sDs&t=27), uploaded2018-11-12 per existing W64 provenance,1280×720/30fps. DUKE MK.44 is visible in the48.000 inventory panel; the exact Bungie hash comes from catalog evidence, not pixels.

| Requested source timestamp | Direct visual evidence |
|---|---|
|27.100|Magazine7, reserve107; hands and weapon in reload pose.|
|27.200|Magazine9, reserve105; hands remain at receiver and pose is unrecovered.|
|27.500/27.700|Subsequent selected frames retain receiver work/tilt and recovery.|
|27.900|Weapon returns forward.|
|28.000|A subsequent shot is demonstrated and magazine becomes8.|

The visible HUD transfer is bracketed to **(27.100,27.200]s**. The matched+2 magazine/−2 reserve is direct evidence of a visual ammo transfer during a partial reload and before the visual recovery tail. It is not an engine trace: timestamps are requested decoder seek times inherited from W64, not exact input or server-event timestamps. The sheet's earlier25.4/25.6 preparation does not supply a controlled reload-start instant, so this audit does **not** fit0.71 to the clip.

The sample has Kill Clip displayed and no observed active Outlaw. The title mentioning Outlaw is not an active-perk measurement. No normal-versus-Outlaw comparison, empty reload, exact full-reload duration, current-sandbox equivalence, or earliest allowed shot input was established. Later observed fire cannot prove an earlier shot was impossible. No cancel input is visible/tested; persistence or loss of credited ammo after cancellation remains unproved. No machine-gun footage was audited:0.65 rests on the pinned community formula.

## Audit boundary

Read-only source and existing selected-frame inspection. No broad search, article/metadata export, Gradle, native app, runtime edit or commit. This sidecar does not certify the main implementation. Only `art/weapons/w65/reference-notes.md` and the two linked files under `art/weapons/w65/references/` were written.
