# W226 Slickdraw — BASIC

Weapon Perks gid1662574278 displayed row200, HTML id1662574278R199.
[User DDC](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278). Live snapshot checked 2026-10-28; yellow enhanced annotations excluded.

200 Slickdraw Passively grants +100 Handling, 0.95x Ready Animation Duration Multiplier, and -20% Auto Aim Cone Size.

Exact sole legal canonical roll: Bite of the Fox hash1403800851, socket3, pool563442205, BASIC perk hash1821614984.
Official legendary tier5; category4241085061; real randomized pool; currentlyCanRoll=true. All65 current canonical entries scanned including W83/W84 exotics; no fake/default/reusable fallback.

## Apply and limits

- Live count-one real WeaponItems source; original reference uniquely owned in inventory hotbar/loadout. No proc or persistent state.
- JSON-only. Canonical registries checked lazily in supports(entry).
- User simple-stat exception: no numerical-only unit tests, whole gate or Vision. Master owns integration.
- Master wraps WeaponSlickdraw.handlingTicks(player,stack,ready,base) and adsTicks(player,entry,base,entering) outermost. Raw Handling25+100 saturates100; ready .95 only; stow and ADS scalar1.
- Ready accepts exact original owned incoming hotbar item before actual selection. Stow and ADS require current selected held source. No stored proc or selecting hook.
- No speculative companion scalar or rounded-duration composition. Other positive raw handling buffs are redundant at100.
- BASIC -20% Auto Aim Cone Size is source-only and unsimulated; no spread penalty invented. Enhanced -15%? excluded.

## Bounded raw curve proof

Only Bite's ready/stow/ADS curve is emitted. Source: pinned w202-steady-hands.json, original Handling25.
These are historical W46 community curves, not a new current-Destiny animation calibration.

```json
{
  "source": "src/main/resources/destiny/weapons/w202-steady-hands.json",
  "curve": {
    "id": "bite_of_the_fox",
    "baseHandlingStat": 25,
    "ready": {
      "evpp": 0.0,
      "vpp": -0.002623944983,
      "offset": 0.5079465458
    },
    "stow": {
      "evpp": 0.0,
      "vpp": -0.002083932479,
      "offset": 0.4392525789
    },
    "ads": {
      "evpp": 0.0,
      "vpp": -0.00194998437,
      "offset": 0.5021325414
    }
  },
  "rawSecondsAt100": {
    "ready": 0.24555204749999998,
    "stow": 0.23085933100000003,
    "ads": 0.3071341044
  },
  "calculation": "ceil(rawSeconds(100) * (0.95 iff ready else 1) * 20); ADS clamp2..20; never scale rounded ticks",
  "units": "Historical W46 community seconds mapped to local20TPS. Not a current exact Destiny animation measurement."
}
```

Exact socket4 pool2442672691 (all currentlyCanRoll BASIC):
- Explosive Payload hash3038247973: DDC row91 (1662574278R90); no Handling/ready/stow/ADS duration effect.
- Moving Target hash588594999: DDC row149 (1662574278R148); no Handling/ready/stow/ADS duration effect.
- Opening Shot hash47981717: DDC row157 (1662574278R156); no Handling/ready/stow/ADS duration effect.
- Vorpal Weapon hash1546637391: DDC row245 (1662574278R244); no Handling/ready/stow/ADS duration effect.
- Under-Over hash1870851715: DDC row240 (1662574278R239); no Handling/ready/stow/ADS duration effect.
- Iron Gaze hash4152709778: DDC row127 (1662574278R126); no Handling/ready/stow/ADS duration effect.

No legal socket4 perk adds Handling or ready/stow/ADS duration scalar. Snapshot Sights and Firmly Planted share Slickdraw socket3 and are exclusive.

## Reproduce

`python3 scripts/build_slickdraw_w226.py --root X --check` validates every input pin and all three generated outputs without writes.
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
- `src/main/resources/destiny/weapons/w202-steady-hands.json`: `95c6c89dc5c8490ccc5561753a2ef7d2eb8a3c474c07078c79d55f34e7cd1417`

Manifest envelope version: 245114.26.10.13.2000-1-bnet.66137. Inventory and pool bytes are independently pinned; their local download dates differ.
Bounded raw HTML, socket/pool entries, canonical scan, definition excerpts and curve proof are retained in source.json.
