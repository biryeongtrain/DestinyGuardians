# W195 Opening Shot

Pinned Destiny Data Compendium **Weapon Perks row 157**; exact raw row, yellow enhanced spans and all input SHA256s are in [source.json](source.json). Base Trait `47981717`; enhanced `1370847713` excluded. All 65 canonical entries scanned against their actual randomized trait socket pool: `isFakePlugSet=false`, `currentlyCanRoll=true`, exact base `Trait`. 14 accepted tuples. No same-name substitute weapons.

**defaultSelection**: No trait selected by default; master registers only these exact base rolls. Enhanced/exotic unsupported.

**ownership**: Original count-one selected hotbar/equipped object, exact canonical entry and selected tuple; ServerPlayer/level/GuardianData/runtime/class/loadout/Super checked; accepted writers only; no query mutation. Old-owner cleanup cannot remove successor.

**integration**: Master owns shared registry/runtime/aiming/handling/HUD and central tests. Token.NONE for perkSplash; never fresh capture at explosion.

**conversion**: 20TPS elapsed server ticks are a provisional Minecraft mapping, not a measured Destiny clock.

**aa**: Sourced Aim Assist metadata is exposed only. This server port has no AA or client magnetism implementation.

**validation**: Focused event/timer/epoch cycle tests and isolated Java25 compile only; no numeric mirror tests, numeric-only Vision/fullgate, native or server QA.

**paid**: capture(p,entry,firstOfBurst) after each actual ammo payment before trace. Every paid emission restarts 60 ticks, including firstOfBurst=false supplementals; never fresh supplemental bonuses.

**application**: rangeBonus adds to existing raw Range before single master clamp; accuracyScalar/growthScalar multiply existing cone/growth; aimAssistBonus metadata only.

**snapshot**: Paid immutable bonus survives natural cooldown and later shots. Stow revokes tokens but retains last-shot timing; source edit/change/lifecycle permanently revokes epoch.

**uncertainty**: Primary/Power and Special values confirmed in DDC row157; exact native same-tick boundary and cross-stow cooldown are local event policies.

Regenerate with `rtk proxy python3 scripts/build_opening_shot_w195.py --root <worktree>`; add `--verify` for deterministic byte comparison without writes.

Confirmed base: Primary/Power +25 Range, +20 AA, 0.95 cone, 0.90 growth; Special +13 Range, +10 AA, 0.975 cone, 0.95 growth. 3 seconds after every paid shot; first shot of burst only.
