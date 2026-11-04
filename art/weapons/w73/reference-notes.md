# W73 Archer's Tempo source and data

Independent enumeration of all **63** exact W40 selected weapon hashes, **678 sockets**, and **627 plug-set references** yields **one** eligible base roll: Whispering Slab. Biting Winds has no exact base roll. No base direct occurrence or enhanced occurrence exists within the selected 63; no selected weapons are exotic. The full traversal precedes literal regression checks.

## Runtime contract

`src/main/resources/destiny/weapons/w73-archers-tempo.json` contains `stage: "W73"`, `perk`, `weapons`, and `timings`. `perk` has `id: "archers_tempo"`, `hash: 201365942`, `durationTicks: 60`, `drawScalar: 0.75`, and a `timingSource` string identifying the distinct official, community, and W46 inputs. Each `weapons` row is exactly `{id,hash,socket,perkHash,plugSetHash}`. Each `timings` row is exactly `{id,baseDrawMs,baseDrawTicks,acceleratedTicks}`.

**Candidate timing != eligible roll.** Only `weapons` controls eligibility. The two timing rows are candidates for both selected bows; they do not grant Biting Winds the perk. The supplied main-worker integration contract requires `ArcherTempoProfile.accelerated` to reject IDs absent from `rolls()`, explicitly including `biting_winds`. This sidecar does not independently audit that Java implementation. A proven optional roll must still be selected on the weapon copy before the runtime grants its effect.

## Exact eligible roll

Socket indexes are zero based.

| ID | Weapon hash | Socket | Base perk hash | Randomized plug set |
|---|---:|---:|---:|---:|
| whispering_slab | 211938782 | 3 | 201365942 | 1885424927 |

The match is entry index **3** of its own official randomized trait set. `currentlyCanRoll=true`, `isFakePlugSet=false`, socket category **4241085061**. Both `weight` and `alternateWeight` are **0.0**; these values do not override the explicit rollability flag. Full socket and matching-entry records are retained in `references/socket-pools.json`.

The generator scans every socket of all 63 selected exact definitions, including initial/direct reusable plugs and both `randomizedPlugSetHash` and `reusablePlugSetHash`. It retains a per-weapon/per-socket audit and all 62 negative IDs. It does not filter by presumed bow name or family during discovery. Exact base **201365942** is required. Enhanced **3523746922** is a separately checked official Enhanced Trait and is excluded. Leviathan's Breath/catalysts are excluded; this is selected-inventory coverage, not a global catalyst census.

## Milliseconds before tick rounding

| ID | W46 raw draw ms | Base ticks | Accelerated ticks | Eligible roll |
|---|---:|---:|---:|---|
| biting_winds | 667 | 14 | 11 | no |
| whispering_slab | 567 | 12 | 9 | yes |

Use **`ceil(rawDrawMs * 0.75 / 50)`**, after binding W46 `entries[n].officialStats.drawMillis` to the exact selected and official inventory draw stat **447667954**. Preserve W46 `drawTicks=ceil(rawDrawMs/50)`. Integer rational arithmetic uses `(ms*3+199)//200` for accelerated ticks. Whispering Slab: 567 ms × 0.75 = 425.25 ms → 9 ticks. Biting Winds: 667 ms × 0.75 = 500.25 ms → 11 ticks. Never scale rounded base ticks. The references audit all 63 W46 rows: two bows and 61 explicit non-bow exclusions with no fabricated draw timing.

## Mechanics and evidence boundaries

[Bungie Update 4.1.0](https://www.bungie.net/7/en/News/article/51380) supplies the **standard 0.75 draw scalar** in a discussion that separately identifies Leviathan's Breath's catalyst-specific **0.5625** scalar. This historical official statement supports the standard scalar only; it does not prove today's exact implementation or the 3-second duration. The generator verifies the official capture's identity and the distinct standard/exotic values.

The exact-base [light.gg Community Research](https://www.light.gg/db/items/201365942/archers-tempo/) reports **25% less draw time for 3 seconds after precision hits**, with removal on stow, and a reported update date of **2024-07-16**. This is community evidence. Direct browser-tool opens failed with 402/unavailable. The pinned raw search response returned the complete bounded English Community Research section at the same base-perk URL with `?_=727`, `Basic / Trait`, and API ID **201365942**. No enhanced, translated, mirror, or catalyst section establishes the selected base mechanics.

At the project's **20 TPS**, 3 seconds becomes **60 ticks**. One nonstacking window refreshed by a qualifying hit is a project runtime policy; the captured sources do not precisely document refresh/event ordering. Neither source establishes **mid-draw rescaling on buff activation or expiry**. A snapshot-at-draw-start or dynamic-rescaling choice must remain labeled project policy. Death/disconnect cleanup and exact expiry ordering are also runtime policy. This sidecar changes no runtime Java/HUD/tests.

`references/mechanics.json` separates official scalar, community duration/stow evidence, project quantization/policy, and unknown behavior. The pinned official English name is **Archer's Tempo**. No pinned official Korean inventory component was found in the inspected local source caches; a community Korean translation is not used as an official name.

## Reproduction and provenance

```sh
rtk proxy python3 scripts/extract_archers_tempo_w73.py
rtk proxy python3 scripts/extract_archers_tempo_w73.py --verify
```

All **eight consumed inputs** have literal SHA256 pins: W40 definitions/provenance, official English inventory/plug sets/manifest, raw research capture, W46 extraction, and W46 runtime. The default private raw directory is `run/private-sources/w73`. Official component copies retain the exact historical W40/W60 bytes; no older pins or historical metadata are rewritten. The fetched official HTML is a JavaScript shell and is not used as article-body proof. Ancillary raw retrieval attempts remain private and are listed in provenance as unconsumed evidence.

`--root` selects the input checkout, `--sources-dir` overrides the raw cache directory without relaxing pins, and `--output-root` selects a separate output tree. Generation writes only this Markdown, the four `references/*.json` files, and the runtime JSON. Provenance includes the generator SHA256 and all five other generated output hashes. Changing cache location changes recorded source paths, not the required content hashes.

**`--verify` is offline and read only.** It compares all six generated outputs byte for byte, including Markdown and provenance. It creates no files/directories, fetches nothing, repairs nothing, and fails on missing or changed input/output. Input validation completes before any output write. No native application or Gradle was run for this source/data task, and no fresh gameplay measurement is claimed.
