# W58 weapon switching Handling

Reproduce or verify from the repository root, with Python's standard library only:

```sh
rtk proxy python3 scripts/extract_handling_w58.py
rtk proxy python3 scripts/extract_handling_w58.py --verify
```

`--verify` is strictly read-only, including on failures: it checks fixed input
SHA-256 constants, regenerates in memory, and compares both output files byte for
byte. It never creates directories, repairs output, refreshes hashes, accesses the
network, or loads the full inventory. Missing files and drift fail the command.
Generation writes only `art/weapons/w58/extraction.json` and
`src/main/resources/destiny/weapons/w58-handling.json`.

All 63 W30 selected catalog ids are emitted in catalog order. The 58 nonswords,
including Nezarec's Whisper (glaive), are supported. The five swords have
`supported: false` and explicit null `handling`, `readyTicks`, and `stowTicks`;
neither an official Handling stat nor a pinned Oracle sword curve exists.

The runtime schema is an array of `{id, profile: {supported, handling, readyTicks,
stowTicks}}`. Handling and ticks are integers for supported rows. The official
Handling stat hash is **943549884**; the cached Bungie `DestinyStatDefinition`
confirms the name **Handling** and description “The speed with which the weapon
can be readied and aimed.” Every selected item's hash and complete official stats
must match W46's selected official evidence; W40 definitions must equal the W40
runtime characteristics. Input hashes are constant baselines in the generator,
independent of the generated metadata.

Official base stats come from W40's pinned Oct13 2026 manifest
`245114.26.10.13.2000-1-bnet.66137`. Curves come from
[Oracle Engine commit dcd0c7d302b056ffbb532edcb711d724a17ca8c1](https://github.com/d2foundry/oracle_engine/tree/dcd0c7d302b056ffbb532edcb711d724a17ca8c1)
(May20 2026), using the exact W43 family/category/subfamily mapping and the
existing W46 `weapon_formulas.json`, `stat_calc.rs`, `rs_types.rs`, `d2_enums.rs`,
and `build.rs` files. Oracle license texts remain in `art/weapons/w46/MIT-LICENSE`
and `art/weapons/w46/UNLICENSE`; their hashes are pinned too.

Handling curves already produce **seconds**. They are unrelated to Oracle's
30-fps firing-delay encoding; no `/30` conversion applies. The pinned build
transfers `cat.handling` directly into `HandlingFormula`. Its serde default makes
an absent `evpp` zero. The source solver evaluates:

```text
x = clamp(official Handling, 0, 100)      # solve_at_i, source stat clamp
q(x) = evpp*x*x + vpp*x + offset         # linear when evpp is absent
readySeconds = readyCurve(x)
stowFloorSeconds = stowCurve(100)
stowSeconds = max(stowCurve(x), stowFloorSeconds)
readyTicks = ceil(readySeconds * 20)
stowTicks = ceil(stowSeconds * 20)
```

The stow floor is required by `calc_handling_times_formula`; it is preserved
even when it does not change the selected base result. No extra minimum or
maximum tick clamp is introduced. Invalid source durations fail rather than
being replaced. Neutral evaluation uses zero stat/draw/stow adds and unit
draw/stow scales. The glaive's zero ADS curve is irrelevant to ready/stow support.

`extraction.json` retains each item's raw ready/stow curves, official Handling,
evaluated stat, ready seconds, raw stow seconds, stow-at-100 floor, and final stow
seconds. It also records official provenance, Oracle repository/commit/source,
units, fixed dependency hashes, runtime SHA-256, and the generator's own SHA-256.
The self-hash is computed from script bytes without timestamps or a circular
embedded hash; editing the generator causes verification against old metadata
to fail until intentional regeneration.

The official base stats and historical community duration approximations are
different sources and snapshots. These values do not claim current exact Destiny
balance or official animation durations. Perks, armor, subclass, socket rolls,
masterworks, exotics, and other animation modifiers are not modeled. Runtime
switching policy and fallback behavior are implemented separately by the consumer.
