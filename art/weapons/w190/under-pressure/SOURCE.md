# W190 — base Under Pressure

Base trait **1645158859**, `under_pressure`. Enhanced **3755250867** is excluded.
This work changes only the two W190 Java classes, W190 resource, generator, and this
directory's `SOURCE.md` / `source.json`. Master owns shared registration and aiming/runtime wiring.

## Numeric source and confidence

[Destiny Data Compendium — Weapon Perks, gid1662574278, row239](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278),
downloaded 2026-10-27 at `/private/tmp/destiny-w190/ddc-perks.html`.
Whole-page SHA-256: `8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437`.
The exact row HTML, its SHA-256, and decoded text are preserved in `source.json`.

Base text: “As Magazine decreases below 50%, down to 0%: Linearly grants -12.5% to
-25% Accuracy Cone Size, and up to +30? Stability.” The enhanced arrows `↑-30%?` and
`↑+?` remain in the source proof but contribute no effects. The row states no
PvE/PvP or weapon-family split; the same base effects apply to the admitted catalog entries.

Accuracy endpoints, linear interpolation, and strictly-below-half condition are
verified against this row. The stability endpoint is **`+30?`**, not a confirmed 30.
`originalStabilityVerified=false` is retained in the generated resource and proof.
The implementation's **30-point maximum, 0-at-half linear stability ramp, and integer
floor are temporary server tuning**, not verified original stability behavior.
The Bungie description confirms only improved stability/accuracy as the magazine gets lower.

For canonical base capacity `C` and valid loaded rounds `R`, `q=R/C`:

- At `q >= .5`, bonus = 0 and accuracy scalar = 1.
- Below half, `t=1-2q`; accuracy scalar = `1-(.125+.125*t)`.
- Temporary stability bonus = `floor(30*(C-2R)/C)`, using overflow-safe integer arithmetic.
- Empty is a valid passive state: accuracy scalar `.75`, temporary stability `30`.
- Null/noncanonical/unsupported sources, invalid capacities/rounds, malformed/missing saved
  ammo, or missing/changed pinned W190/catalog resources yield neutral `0` / `1`.

The accuracy scalar changes cone **size**, not cone growth, aim assist, damage,
recoil-direction stat, or a separate recoil multiplier. Add stability through the
existing stat path so the shared clamp and recoil/flinch curves apply once.

## Exact official pools

Pinned manifest version: `245114.26.10.13.2000-1-bnet.66137`.
The W30 inventory provenance and W60 manifest identify the same inventory component;
the manifest's matching plug-set component supplies the pools. Whole-file SHA-256 pins,
official component URLs, base/enhanced definitions, all 65 catalog scans, and full matching
pool definitions are in `source.json`.

Admission requires the exact catalog weapon hash, Legendary tier, actual trait category
`4241085061`, the socket's **`randomizedPlugSetHash`**, a nonfake official pool, and
base hash `1645158859` with `currentlyCanRoll=true`. Reusable/crafting-only, fixed initial,
fake, enhanced, nontrait, and nonrolling references do not authorize a roll. The generator
records those relevant references separately and proves the following complete ten-roll set.
Socket numbers are zero-based manifest indexes.

| Catalog ID | Weapon hash | Socket | Randomized pool hash |
| --- | ---: | ---: | ---: |
| bygones | 2712244741 | 4 | 3060320121 |
| chattering_bone | 568515759 | 4 | 423791138 |
| patron_of_lost_causes | 2723241847 | 4 | 120674550 |
| long_arm | 8293111 | 3 | 3056706286 |
| dead_man_walking_xx7463 | 3751622019 | 3 | 3268663985 |
| hollow_words | 607191995 | 3 | 637298592 |
| dream_breaker | 2931957300 | 3 | 3785896921 |
| coriolis_force | 3512349612 | 3 | 2568674372 |
| line_in_the_sand | 946443267 | 3 | 1503774254 |
| fixed_odds | 2194955522 | 3 | 4227334000 |

No family-wide grants, newly minted roll choices, or exotic grants. Profile support compares
the full canonical catalog record. Runtime selection must equal a complete admitted
`WeaponPerks.Roll` tuple, including item hash, socket, base perk hash, and pool hash.

## Master integration

`UnderPressureProfile.ID`, `.HASH`, and `.rolls()` expose registration data. Master adds
the ID, display name and exact pool to `WeaponPerks`; until registered, selection returns
empty and runtime queries remain neutral. No shared file was changed here.

Runtime APIs:

```java
int bonus = WeaponUnderPressure.stabilityBonus(player);
double scalar = WeaponUnderPressure.accuracyScalar(player);
```

Use the bonus in `WeaponAiming.shot`'s total stability before `RapidHitStability.kick` /
`.bloom`, and in `WeaponAiming.flinch`'s effective stability. Multiply the direction cone
size by the scalar once. Do not additionally multiply the growth increment by that scalar.

Authority is checked on every query: alive, connected, present, nonspectator, not in a
Super, usable loadout, main-hand object identical to its selected hotbar inventory object,
count one, actual equipped object when loadout is enabled, live combat entry, canonical
catalog record, and exact selected base roll. Merely possessing another copy or an offhand,
preview, or model item cannot grant the effect. Saved rounds accept only nonnegative
integral NBT counts within canonical capacity; reading never saves or normalizes the item.

**Default timing is authoritative live rounds at the time of the query.** Master's runtime
saves paid ammo before emission/direction and `WeaponAiming.shot`, so those calls naturally
observe the saved count (and any subsequent real ammo reward if it precedes the query).
DDC row239 does not settle pre/post-cartridge evaluation. This timing is a Minecraft
adaptation, not a verified original ordering; no cached paid-shot lifecycle is introduced.

Optional overloads `stabilityBonus(player, rounds, baseCapacity)` and
`accuracyScalar(player, rounds, baseCapacity)` retain current source authority and accept
caller-owned values. Pure entry equivalents are on `UnderPressureProfile`. If master
chooses pre-payment timing later, take `int roundsBefore=ammo.rounds()` and canonical
`int capacity=WeaponProfile.forEntry(entry).magazine()` into ordinary local variables
**before consumption**, then pass those values consistently to the accepted shot's
calculations. A post-save count plus one is unreliable after precision returns/refunds;
shared-cartridge bolts may reuse the caller's local values. No token API, stored player
state, ammo mutation, proc timers, cleanup hooks, HUD rows, models or animations are needed.

## Reproduction and performed checks

From this isolated worktree:

```sh
rtk proxy python3 scripts/build_under_pressure_w190.py
rtk proxy python3 scripts/build_under_pressure_w190.py --verify
```

Inputs default to the requested W30 inventory, W60 plugsets/manifest, W30 manifest
provenance, downloaded DDC page, and pinned local catalog/characteristics/exotic resources.
The generator writes only `w190-under-pressure.json` and `source.json`; `--verify` writes
nothing. Source SHA-256/identity, full catalog coverage, exact randomized-pool admission,
and DDC row/value/uncertainty checks run as part of generation. Runtime pins the W190 resource
and canonical base catalog; invalid resources disable only this profile with a warning.

No perk tests, builds, shared runtime gate, child agents, CU, game, animation, or native
verification were performed, following the stat-only policy. Shared integration remains
master-owned; no claim of in-game activation or original cartridge timing verification.
