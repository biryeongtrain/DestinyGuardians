# W77 Dragonfly source pipeline

The pinned official manifest yields **four** exact base **2848615171** rolls after
an independent traversal of all **63** selected hashes, **678 sockets**, and
**627 plug-set references**. Socket indexes are zero based.

| ID | Weapon hash | Socket | Randomized plug set | Element |
|---|---:|---:|---:|---|
| brass_attacks | 2121785039 | 4 | 3403850295 | VOID |
| distant_relation | 2034817450 | 4 | 3824767299 | SOLAR |
| line_in_the_sand | 946443267 | 4 | 3257645194 | ARC |
| long_arm | 8293111 | 4 | 619833418 | ARC |

All four pools are nonfake randomized trait sets in category **4241085061**;
their exact base entries have `currentlyCanRoll=true`. Both weight fields are
zero and do not negate that flag. No base direct defaults/reusable items,
enhanced **169755979**, different same-name **3865257976**, or non-runtime base
pool occurrences were found. All four are ARC/SOLAR/VOID. No Kinetic, Stasis or
Strand occurrence was filtered: encountering any unsupported base element
fails explicitly. The 59 negative IDs and every inspected socket/reference are
recorded in `references/socket-pools.json`. The selected inventory has no
exotics; this is not a global catalyst or global drop-availability census.

## Integration API

`DragonflyProfile.ID = "dragonfly"`, `HASH = 2848615171L`.

* `rolls(): List<WeaponPerks.Roll>`: the four exact tuples above; each perk hash is 2848615171.
* `radius(): double`: **4.5**, community meters mapped to Minecraft blocks.
* `damage(): float`: **10f**, fixed authored Minecraft PvE center damage.
* `falloffFloor(): float`: **.3f**, authored minimum fraction inside the radius.
* `perk(): Perk`: typed runtime data with separate radius provenance and local policies.

The profile validates stage, trait identity/hash, finite exact tuning values,
source authorities/URLs/hash shape, policy labels, complete exact socket tuples,
catalog membership, W40 item hash, nonexotic status, supported families and
ARC/SOLAR/VOID elements. It exposes immutable rolls. Proven eligible rolls must
still be selected on the weapon copy; runtime integration belongs to the parent.

## Sources and authored policy

[Bungie's July 3, 2025 TWID](https://www.bungie.net/7/en/News/Article/twid_07_03_2025), under **Chain Reaction, Dragonfly,
Firefly**, announces that The Edge of Fate replaces combatant weapon-archetype
explosion scaling with more normalized perk scaling. It does not establish a
Minecraft HP conversion, universal damage number, radius or falloff curve.
The announcement concerns the July 15 expansion changes.

The exact-base [light.gg Community Research](https://www.light.gg/db/items/2848615171/dragonfly/) reports a **4.5 m**
weapon-element blast on precision kills, with reported update **2025-12-27**.
This is community evidence. The bounded English search result explicitly
identified Basic / Trait and API ID 2848615171; direct opens returned HTTP 402.
The stale **3 m** summary and weapon-archetype multipliers are not used.

**10 Minecraft HP is locally authored PvE tuning**, shared by all four eligible
weapons. It is not original Destiny damage and does not scale with weapon shot
damage, archetype, ammo, critical/range modifiers or active damage perks.
For finite nonnegative distance `d`, use `max(0.3, 1-d/4.5)` inside the inclusive
4.5-block radius and zero outside. Thus the center receives 10 HP and the edge
3 HP. The curve, floor, boundary inclusion and one-meter/one-block mapping are
project policy. Radius provenance is independent of the local damage policy.

`references/research.json` is a small pinned input with paraphrased claims,
URLs, dates, retrieval limitations and SHA256 identifiers for the exact
URL-bound web-tool result representations. No article/page payload is stored.
Those hashes are not original HTML hashes; offline verification cannot recover
or revalidate the discarded responses. `references/mechanics.json` preserves
this distinction. No enhanced behavior or fresh gameplay measurement is claimed.

## Offline reproduction

```sh
rtk proxy python3 scripts/extract_dragonfly_w77.py
rtk proxy python3 scripts/extract_dragonfly_w77.py --verify
rtk proxy python3 scripts/extract_dragonfly_w77.py --inspect-source
```

The default cache is the existing `run/private-sources/w73` official component
cache. Eight literal SHA256 pins bind W40 definitions/provenance, W30 catalog,
W40 runtime characteristics, inventory, plug sets, manifest and research summary.
The manifest version is `245114.26.10.13.2000-1-bnet.66137`. No older stage or cache is rewritten.

`--root` chooses the input checkout; `--sources-dir`/`--inventory` relocate
byte-identical caches; `--output-root` writes a separate reproduction tree.
Generation writes only the runtime JSON, socket/mechanics/provenance JSON and
these notes. `research.json` and Java are authored inputs, not generated files.
Provenance records the generator/profile hashes and four other output hashes.
`--verify` compares all five generated files byte for byte. `--inspect-source`
checks the pins and full extraction and prints input hashes plus eligible tuples.
Both modes are offline and read only, including failure paths: no downloads,
directory creation, cache repair, builds, Java/native launches or audio creation.
