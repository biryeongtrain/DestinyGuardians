# W195 Box Breathing

Pinned Destiny Data Compendium **Weapon Perks row 35**; exact raw row, yellow enhanced spans and all input SHA256s are in [source.json](source.json). Base Trait `2551157718`; enhanced `23371658` excluded. All 65 canonical entries scanned against their actual randomized trait socket pool: `isFakePlugSet=false`, `currentlyCanRoll=true`, exact base `Trait`. 2 accepted tuples. No same-name substitute weapons.

**defaultSelection**: No trait selected by default; master registers only these exact base rolls. Enhanced/exotic unsupported.

**ownership**: Original count-one selected hotbar/equipped object, exact canonical entry and selected tuple; ServerPlayer/level/GuardianData/runtime/class/loadout/Super checked; accepted writers only; no query mutation. Old-owner cleanup cannot remove successor.

**integration**: Master owns shared registry/runtime/aiming/handling/HUD and central tests. Token.NONE for perkSplash; never fresh capture at explosion.

**conversion**: 20TPS elapsed server ticks are a provisional Minecraft mapping, not a measured Destiny clock.

**aa**: Sourced Aim Assist metadata is exposed only. This server port has no AA or client magnetism implementation.

**validation**: Focused event/timer/epoch cycle tests and isolated Java25 compile only; no numeric mirror tests, numeric-only Vision/fullgate, native or server QA.

**paid**: update(p,actualAds) only after master validated FOV/handling ownership. capture(p,entry,roundsBefore,actualAds) after actual payment before trace; do not update using post-payment empty magazine first. Supplementals and perkSplash use Token.NONE.

**application**: precisionMultiplier applies only to weakspot/precision hits; no body damage, generic damage or Dragonfly inheritance.

**snapshot**: 30 elapsed ticks from actual ADS input with positive magazine, no firing. Paid shot consumes readiness; release/stow/reload/edit resets. False/true same tick restarts clock. Natural magazine-empty polling does not erase accepted last-round snapshot.

**uncertainty**: DDC row35 text contains "Weakspot damage? Least convoluted way"; preserve raw question text as uncertainty. Shielded weakspot and Divinity semantics are not claimed simulated. Confirmed 40% for the two supported Special snipers; 30% Heavy/Glaive branch unsupported.

Regenerate with `rtk proxy python3 scripts/build_box_breathing_w195.py --root <worktree>`; add `--verify` for deterministic byte comparison without writes.

Confirmed base: 1.5 seconds ADS input with magazine >0; next ADS shot 1.40 weakspot damage, 1.10 AA falloff distance. Beloved/Apostate verified Special sniper rifles. `released(p,stack)` handles explicit release; `suspend(p,stack)` handles accepted reload/aim suspension. Both revoke prior epoch.
