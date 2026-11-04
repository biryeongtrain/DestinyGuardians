# W190 Compulsive Reloader

Base trait **671806388** only. [Destiny Data Compendium, Weapon Perks, gid1662574278, row54](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1662574278), checked 2026-10-27 from `/private/tmp/destiny-w190/ddc-perks.html`: while **strictly above 50%** magazine, **+50 Reload Speed**, **0.95× Reload Duration**. No PvE/PvP split is stated. Enhanced +55 / hash595108252 is excluded. Exactly half is inactive; odd capacities use `2L * roundsBefore > capacity`.

Official cached manifest version `245114.26.10.13.2000-1-bnet.66137` establishes the five exact base weapon hashes and current randomized trait sockets. This is the supplied official snapshot, not a new network refresh. Inventory `/tmp/destiny-weapons-w30/bungie-items.json`, plug sets `/tmp/destiny-weapons-w60/bungie-plugsets.json`, manifest `/tmp/destiny-weapons-w60/manifest.json`; full input SHA256 pins, exact distinct companions, same-socket exclusions and raw arithmetic are in `source.json`.

| Weapon | Hash | Socket | Randomized plug set |
|---|---:|---:|---:|
| Aisha's Embrace | 2638190703 | 3 | 7997267 |
| Austringer | 3055790362 | 3 | 2750499928 |
| Beloved | 3107853529 | 3 | 1196545279 |
| Long Arm | 8293111 | 3 | 3056706286 |
| Nezarec's Whisper | 254636484 | 3 | 210449465 |

W43's selected family/category selects the existing W46 raw quadratic `q(stat) = evpp*stat² + vpp*stat + offset` from `art/weapons/w46/weapon_formulas.json`. Those licensed historical community curves are approximate, **not official current durations**; existing W46 attribution/licenses apply. For a whole magazine, evaluate `ceil(20 * q(clamp(baseStat + totalBonus, 0, 100)) * totalScalar)` once. Only actual selected, active, proven distinct reload companions enter those totals: **Frenzy on Austringer and Nezarec's Whisper**, +100 alongside W190's +50, with W190's 0.95 scalar retained. Other legal traits keep their existing independent behavior; same-socket perks cannot contribute.

Long Arm retains the existing W48 authored **1.0s first / 0.65s repeat / two cartridges** policy. Scale each raw phase by `q(cappedTotalStat) * totalScalar / q(baseStat)`, then ceil each final phase once. This is a local adaptation of a whole-magazine ratio, not a measured per-insert curve. Never scale an incoming rounded/modified tick plan. Acceptance above half freezes the two phase durations for the entire accepted reload; later inserts do not activate/recompute W190.

Master integration: register `CompulsiveReloaderProfile.ID`, `.HASH`, `.rolls()` and display name in `WeaponPerks`, then call `plan = WeaponCompulsiveReloader.plan(player, entry, plan)` **last**, immediately before `cycle.startReload(...)` and its reload-credit calculation. `plan` reads the genuine selected hotbar/loadout object and its current persisted ammo projection before reload, rejects active reloads, and returns the incoming plan unchanged below threshold. No lifecycle/aim/HUD hook is needed. Profile initialization is JSON-only; it never calls `WeaponCatalog.find`, `WeaponPerks` methods, or runtime state.

Run `rtk proxy python3 scripts/build_compulsive_reloader_w190.py` to regenerate the two JSON outputs; append `--verify` for read-only source/output checks. Verification is source/data/path only. No new tests, dependency builds, compile/JAR, Vision/CU/game, animations or models are part of this delta. Master owns shared integration and final compilation/lifecycle verification.
