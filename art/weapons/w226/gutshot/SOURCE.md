# W226 Gutshot Straight — bounded BASIC source proof

- Bungie manifest: `245114.26.10.13.2000-1-bnet.66137`.
- BASIC hash `1365187766`: Trait/Common, non-dummy. Only real legendary canonical sources with trait category `4241085061`, `isFakePlugSet=false`, and `currentlyCanRoll=true` are emitted.
- Scanned all 63 canonical characteristics; exactly two legal BASIC sockets. Full selected socket and matching plug rows, JSON pointers, hashes and bounded DDC HTML row are in `source.json`.
- `ammit_ar2` / Ammit AR2: item `2119346509`, socket `4`, randomized pool `560115158`, BODY ×1.2.
- `allied_demand` / Allied Demand: item `1532276803`, socket `4`, randomized pool `703779397`, BODY ×1.1.
- [User DDC Weapon Perks](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278): row **110**, HTML ID `1662574278R109`; BASIC ADS nonprecision/nonweakspot damage +20% Auto Rifles / +10% Sidearms; AA cone −15% (scalar0.85), source-only. Enhanced −10%? excluded.

## Input SHA-256 pins

- `/tmp/destiny-weapons-w30/bungie-items.json`: `b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c`
- `/tmp/destiny-weapons-w60/bungie-plugsets.json`: `8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959`
- `/tmp/destiny-weapons-w60/manifest.json`: `bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce`
- `/private/tmp/destiny-w226/ddc-perks-live.html`: `6430f2f552832b903efb85be59adf4a1791d956d30fee4e4fe79c8ad2c53bc15`

## Runtime contract and limits

- BASIC only: hash1365187766. Enhanced uncertain -10%? AA cone entry is excluded.
- Base AA cone scalar0.85 is evidence only: no auto-aim cone engine path exists; no stability/spread surrogate.
- ADS means actual WeaponAiming.aimInput(p) at accepted paid fire, including an accepted ADS transition before completion; no raw sneak, pose, FOV preview or progress threshold.
- Only direct BODY components are scaled. Precision, weakspot, perk splash and unpaid/preview/rejected contexts use no Gutshot token. The existing hit classifier provides body versus precision; no separate Destiny weakspot/shield simulation is added.
- Token is immutable and self-contained. ADS release, later selection or source changes cannot retroactively alter an already-paid attack. No timer/lifecycle, metadata, ammunition, inventory, pose or registry mutation.
- Master owns selection registration, WeaponShotTraits.Snapshot capture, damageOnly token stripping, and applying bodyDamage only to hits.body; this slice does not implement those shared hooks.

- API: `GutshotProfile.ID`, `HASH`, `rolls()`, `supports(entry)`, `bodyMultiplier(entry)`; `WeaponGutshot.Token.NONE`, `capture(p, entry)`, `bodyDamage(token, body)`. No precision method or lifecycle API.
- `capture` is called only after the master accepts and pays an individual direct emission. It observes exact main-hand/inventory object identity, count1, current owner/use eligibility, canonical entry and exact selected BASIC socket. It does not infer payment from a roll or ammo count.
- Master stores the token in `WeaponShotTraits.Snapshot`, strips it in `damageOnly()`, and transforms only `hits.body` before combining mixed hit components. Preview, unpaid and perk splash callers retain `Token.NONE`.

## Reproduce

```sh
rtk proxy python3 scripts/build_gutshot_w226.py --root "$WORKTREE" --check
```

Without `--check`, only the three owned resource/evidence files are generated. No registry, build, game or pose assets are changed.

The targeted unit suite covers accepted versus rejected/unpaid contexts, actual ADS input policy, exact held identity/count/selected socket, immutable paid-shot snapshots, mixed BODY/precision/splash policy, and resource corruption. Minecraft bootstrap/real selected-roll capture and shared integration are master-owned checks; see the worker report for executed results.
