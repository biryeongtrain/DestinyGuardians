# W68 Snapshot Sights source and data sidecar

Full enumeration of all **63** selected exact official hashes yields **15 official randomized base rows**. **13 Primary/Special rows** are runtime selectable. Bad Omens and Edge Transit have official base Snapshot rolls, but their **2 Heavy rows** are excluded from runtime because no Heavy scalar was measured. Both direct duplicates and both enhanced occurrences are preserved separately. No native evidence is available.

## Exact runtime schema

`src/main/resources/destiny/weapons/w68-snapshot.json` has exactly `schemaVersion`, `perkHash`, `primaryScalar`, `specialScalar`, `rolls`, `timings`. Values are `1`, `957782887`, `0.5`, `0.8`, then the arrays. Each `rolls` entry uses the full WeaponPerks.Roll shape: `{id,hash,socket,perkHash,plugSetHash}`. Each `timings` entry has exactly `{id,baseTicks,snapshotTicks,ammoType,adsSeconds}`. `ammoType` is the official integer enum: **1 Primary, 2 Special, 3 Heavy**.

There are **57 raw timing rows** (29 Primary, 16 Special, 12 Heavy). Their presence does not imply perk eligibility. All Heavy timing rows explicitly retain `snapshotTicks=baseTicks`; no Heavy scalar is guessed or supplied. The six W44 neutral entries are omitted from runtime timings and retained with unchanged two-tick base/noSnapshot/exit values in `references/timings.json`: `abide_the_return`, `crown_splitter`, `falling_guillotine`, `goldtusk`, `nezarec_s_whisper`, `temptation_s_hook`.

## Exact selectable rolls

Socket indexes are zero based. Every row below comes from its own exact randomized trait plug set, with `currentlyCanRoll=true` and `isFakePlugSet=false`.

| ID | Weapon hash | Socket | Base perk hash | Randomized plug set |
|---|---:|---:|---:|---:|
| apostate | 2164448701 | 4 | 957782887 | 2826016044 |
| austringer | 3055790362 | 3 | 957782887 | 2750499928 |
| beloved | 3107853529 | 3 | 957782887 | 1196545279 |
| bite_of_the_fox | 1403800851 | 3 | 957782887 | 563442205 |
| biting_winds | 1621657423 | 4 | 957782887 | 2763203653 |
| blast_furnace | 3843477312 | 3 | 957782887 | 1976101165 |
| claws_of_the_wolf | 1280933460 | 3 | 957782887 | 206409262 |
| deafening_whisper | 981718087 | 4 | 957782887 | 3588287812 |
| dream_breaker | 2931957300 | 3 | 957782887 | 3785896921 |
| dust_rock_blues | 636912560 | 4 | 957782887 | 1624251370 |
| high_albedo | 1197486957 | 4 | 957782887 | 718633408 |
| mindbender_s_ambition_adept | 912150785 | 3 | 957782887 | 1732284294 |
| parcel_of_stardust_fell_to_earth | 2217366863 | 3 | 957782887 | 2514419370 |

## Official Heavy rolls excluded from runtime

These are real official base Snapshot rolls. They are unsupported for measured speed selection, rather than weapons without the perk.

| ID | Weapon hash | Socket | Randomized plug set | Unchanged base/snapshot ticks |
|---|---:|---:|---:|---:|
| bad_omens | 991314988 | 3 | 457210958 | 10 |
| edge_transit | 218335759 | 3 | 447678063 | 9 |

## Complete enumeration and exclusions

`references/socket-pools.json` records all 15 official base rows, the 13 runtime rows, `excludedHeavy` with its reason, full matching entry records/indexes, each eligible socket entry, and an audit of every socket of all 63 selected definitions. Both `randomizedPlugSetHash` and `reusablePlugSetHash` are visited, along with direct initial/reusable items, including negative findings. Zero weights are preserved and do not negate `currentlyCanRoll=true`. No inferred name/reissue eligibility is used. Literal enumerated tuple regressions are checked only after the independent traversal finishes.

The two base direct defaults are Bite of the Fox (1403800851, socket 3) and Mindbender's Ambition Adept (912150785, socket 3). Each duplicates its own proven randomized row, adding **zero** runtime rows. The complete direct records appear in `directSocketOptions` with `alsoProvenRandomized=true` and `addsRuntimeRow=false`. The complete enhanced occurrences are excluded:

| ID | Weapon hash | Socket | Enhanced perk hash | Randomized plug set |
|---|---:|---:|---:|---:|
| austringer | 3055790362 | 3 | 4116820839 | 2750499928 |
| beloved | 3107853529 | 3 | 4116820839 | 1196545279 |

The exact base definition is **957782887**, while enhanced Snapshot is **4116820839**. Enhanced stability bonuses and shared mechanics text cannot make an enhanced entry a supported base roll. There are no additional base pool occurrences outside the 15 proven randomized rows. All 63 selected items are nonexotic. Exotics/catalysts remain unsupported; this is selected-item coverage, not a global catalyst census.

## Raw ADS provenance and tick policy

Raw seconds are read by exact ID/hash from the actual `entries` array in pinned `art/weapons/w44/extraction.json`, preserving its stored float precision. W44 records its community formula lineage as `d2foundry/oracle_engine`, commit `dcd0c7d302b056ffbb532edcb711d724a17ca8c1` (2026-05-20), `build_resources/weapon_formulas.json`, SHA256 `fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d`. This generator consumes the pinned W44 extraction, not an independently fetched/recomputed upstream formula snapshot. It checks the stored ADS curve against the exact official Handling value and binds the W44 runtime hash and all 63 IDs. `references/timings.json` preserves each raw numeric literal, JSON pointer, curve, Handling, and base/noSnapshot/exit ticks for all 63 selected weapons. The original upstream formula file is lineage metadata, not an additional consumed input.

For a selected supported roll, entry ticks are **`clamp(ceil(adsSeconds * ammoScalar * 20),1,20)`**. Scale raw seconds before rounding. Never scale W44's already rounded `baseTicks`, and never round raw seconds for calculation. Base ticks remain the pinned W44 runtime ticks, checked against its `clamp(ceil(adsSeconds*20),2,20)` policy. Unselected weapons retain those base ticks. **Exit remains unchanged at W44 base ticks**: entry-only speed is supplied project policy, not proof of Destiny's exit behavior.

| ID | Exact W44 adsSeconds | ammoType | baseTicks | snapshotTicks |
|---|---:|---:|---:|---:|
| austringer | 0.253333333351 | 1 | 6 | 3 |
| beloved | 0.41048327600999995 | 2 | 9 | 7 |
| dust_rock_blues | 0.37170040488 | 2 | 8 | 6 |
| apostate | 0.37538355734999995 | 2 | 8 | 7 |
| bad_omens | 0.48619899248 | 3 | 10 | 10 |
| edge_transit | 0.42162104 | 3 | 9 | 9 |

Beloved demonstrates the rounding order: raw `0.41048327600999995 * 0.8 * 20` yields **7** ticks after ceil, while incorrectly scaling its rounded nine-tick base would yield eight. Dust Rock Blues similarly yields **6**, rather than seven from rounded base ticks. W44 source/runtime files are not modified.

## Numeric evidence and unresolved historical conflict

The exact-base [light.gg Community Research section](https://www.light.gg/db/items/957782887/snapshot-sights/?_=150), reporting an update of **2024-04-12**, describes Primary ADS duration reduced by 50% and Special duration reduced by 20%. These correspond to duration scalars **0.5** and **0.8**. The generator binds those measurements to that exact URL, base API ID and bounded section. Enhanced sections, a mirror-domain result, and other weapon pages are not numeric base evidence. Official pinned definitions describe faster ADS and official socket pools prove roll availability; neither supplies these numeric reductions.

Historical official 2022 [May 5 clarification](https://www.bungie.net/7/en/News/article/51319), [Update 4.1.0](https://www.bungie.net/7/en/News/article/51380) and [April 21 preview](https://www.bungie.net/7/en/News/Article/51250?hidenav=true) instead document **0.75 Special**, with Primary remaining **0.5**. Their source statements are preserved as paraphrased findings in `references/mechanics.json`. **The conflict is unresolved.** No intervening patch explanation or fresh gameplay measurement establishes why 0.75 and 0.8 differ. The explicit **measured-modern server choice is 0.8 Special**, following the captured 2024 community measurement; this does not assert that Bungie confirmed 0.8 or certify today's Destiny sandbox. Heavy has no measured scalar and remains unsupported.

Raw source capture `/tmp/destiny-weapons-w68/research1.json` and official caches remain private. Public reference files contain bounded findings and selected socket proof, without full web/search captures. No native/client launch or live test was performed.

## Offline reproduction and verification

```sh
rtk proxy python3 scripts/extract_snapshot_w68.py
rtk proxy python3 scripts/extract_snapshot_w68.py --verify
```

All **eight consumed source files** have literal SHA256 pins: W40 definitions/provenance, official inventory/plug sets/manifest, the W68 research capture, W44 extraction, and W44 runtime. Default private caches are `/tmp/destiny-weapons-w30/bungie-items.json`, `/tmp/destiny-weapons-w60/{manifest,bungie-plugsets}.json`, and `/tmp/destiny-weapons-w68/research1.json`. Missing or changed input fails before any output write.

`--root` selects the input checkout. `--output-root` selects a separate output tree without changing inputs. `--inventory`, `--shared-sources-dir`, and `--sources-dir` override private source locations; content pins remain mandatory. Provenance records resolved source locations, so changing those locations changes provenance metadata only. The generator records its own SHA256 and all five non-provenance output hashes.

**`--verify` compares all six generated outputs byte for byte, including this Markdown**, collects every mismatch, and performs no writes, directory creation, networking, fetch or cache repair. Missing outputs fail without repair. Generation is limited to this notes file, the four `references/*.json` files, and the W68 runtime JSON. Production Java/tests, implementation.json, main docs and the existing W68 QA baseline are outside this generator's write scope.
