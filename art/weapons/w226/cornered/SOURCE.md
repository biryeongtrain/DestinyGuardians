# W226 Cornered — BASIC only

[Destiny Data Compendium, Weapon Perks gid1662574278, row57](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278), HTML row `1662574278R56`:

> 57 Cornered While within 15 metres of 2 enemies : 0.85x Charge/Draw Time Multiplier ↑and +10 Stability. Buff lingers for 1.5 seconds once criteria isn't met. ↑Passively grants +5 Stability.

Apply only 2 enemies within 15 metres, charge/draw time ×0.85, linger 1.5 seconds = 30 ticks.
Enhanced hash `1008128453` and its active +10/passive +5 Stability are explicitly excluded.
Manifest `245114.26.10.13.2000-1-bnet.66137`; current official inventory and plugset component URLs are retained in source.json.

## Exact socket proof

Scan all 65 canonical identities; exactly **1 owned real weapon** matches: `dream_breaker` hash2931957300,
canonical trait socket4, randomized pool1206254527, BASIC perk1799762209, `currentlyCanRoll=true`,
`isFakePlugSet=false`, non-dummy/non-redacted/non-blacklisted Trait. No fabricated/fallback rolls.
`source.json` contains the complete bounded DDC row, definition, socket/pool and catalog scan.
Backup Plan1600092898 is also socket4/pool1206254527: the two perks cannot co-select and no stacking is added.

## Local application and integration contract

1 metre = 1 block, inclusive 3D footpoint radius. Match WeaponThreatDetector's loaded living PvE enemy
policy (exclude players, armor stands, tames, allies); no line-of-sight invention or chunk loading.
`WeaponCornered.update(p)` is the only entity-scanning/binding path. Master calls it on player ticks
and immediately before both accepted fusion-charge starts, then freezes the full result of
`WeaponCornered.charge(p, entry, base)`. Active charge ticks are `ceil(base.chargeTicks() * .85)`;
every other WeaponProfile field survives. Pure getters neither bind nor refresh linger.
The session pins owner/world/data/runtime/class/loadout mode, original held object/slot, identity and roll.
Actual stow, edits or invalidation revoke linger; first negative observation starts its exclusive deadline.
Master owns registration, shared runtime/handling/aim/shot-trait/command/GameTest wiring.

## Input pins

- `manifest`: SHA-256 `bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce` (188873 bytes).
- `inventory`: SHA-256 `b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c` (199128691 bytes).
- `plugsets`: SHA-256 `8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959` (10438797 bytes).
- `ddc`: SHA-256 `6430f2f552832b903efb85be59adf4a1791d956d30fee4e4fe79c8ad2c53bc15` (761562 bytes).
- `w40-characteristics.json`: SHA-256 `5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1` (34655 bytes).
- `w30.json`: SHA-256 `2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a` (13784 bytes).
- `w83-exotics.json`: SHA-256 `bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56` (3027 bytes).
- `w84-exotics.json`: SHA-256 `481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e` (2599 bytes).

Resource SHA-256: `4dbd6fdcbe0830cfb0310b64024a11b7003448ba676d86465e1198abb10a3e29`.

Reproduce: `python3 scripts/build_cornered_w226.py --root X --check` (read-only).
Omit `--check` to write only the three generated resource/proof files. Source paths default to the
user-pinned /tmp inventory, plugsets and manifest plus /private/tmp/destiny-w226/ddc-perks-live.html;
explicit source flags are supported and must match the exact pins above.
