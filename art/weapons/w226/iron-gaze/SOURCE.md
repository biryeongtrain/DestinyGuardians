# W226 Iron Gaze — BASIC

Weapon Perks gid1662574278 displayed row127, HTML id1662574278R126.
[User DDC](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278). Live snapshot checked 2026-10-28; yellow enhanced annotations excluded.

127 Iron Gaze Passively grants +20 Aim Assist and -20 Range.

Exact sole legal canonical roll: Bite of the Fox hash1403800851, socket4, pool2442672691, BASIC perk hash4152709778.
Official legendary tier5; category4241085061; real randomized pool; currentlyCanRoll=true. All65 current canonical entries scanned including W83/W84 exotics; no fake/default/reusable fallback.

## Apply and limits

- Live count-one real WeaponItems source; original reference uniquely owned in inventory hotbar/loadout. No proc or persistent state.
- JSON-only. Canonical registries checked lazily in supports(entry).
- User simple-stat exception: no numerical-only unit tests, whole gate or Vision. Master owns integration.
- WeaponIronGaze.rangeBonus(player): signed -20 in master raw Range sum before existing clamp; held selected exact source only.
- +20 Aim Assist is source-only and unsimulated; no spread, cone or magnetism invented.

## Reproduce

`python3 scripts/build_iron_gaze_w226.py --root X --check` validates every input pin and all three generated outputs without writes.
Omit --check to regenerate the owned resource, source.json and SOURCE.md only. No network or registry access.

## SHA-256 input pins

- `/tmp/destiny-weapons-w30/bungie-items.json`: `b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c`
- `/tmp/destiny-weapons-w60/bungie-plugsets.json`: `8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959`
- `/tmp/destiny-weapons-w60/manifest.json`: `bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce`
- `/private/tmp/destiny-w226/ddc-perks-live.html`: `6430f2f552832b903efb85be59adf4a1791d956d30fee4e4fe79c8ad2c53bc15`
- `src/main/resources/destiny/weapons/w30.json`: `2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a`
- `src/main/resources/destiny/weapons/w40-characteristics.json`: `5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1`
- `src/main/resources/destiny/weapons/w83-exotics.json`: `bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56`
- `src/main/resources/destiny/weapons/w84-exotics.json`: `481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e`
- `src/main/java/kim/biryeong/destiny/weapon/WeaponExotics.java`: `8bc75359ace0e885e10e1b95811b6bb43e3a242cc720e7ce6427b763e3b2a4a7`

Manifest envelope version: 245114.26.10.13.2000-1-bnet.66137. Inventory and pool bytes are independently pinned; their local download dates differ.
Bounded raw HTML, socket/pool entries, canonical scan, definition excerpts and curve proof are retained in source.json.
