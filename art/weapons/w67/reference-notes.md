# W67 precision-return source and data sidecar

Independent enumeration of all 63 selected official weapon definitions yields **9 real randomized exact-base rows across 8 weapons**: five Triple Tap rows and four Fourth Time's the Charm rows. The runtime resource has exactly `stage` and `perks`; each perk has `id`, `hash`, `hits`, `returnRounds`, `windowTicks` and `weapons`. Every weapon row has exactly `id`, `hash`, `socket`, `perkHash` and `plugSetHash`.

## Exact eligible rows

All sockets below are zero based. Triple Tap is base hash **3400784728**; Fourth Time's the Charm is base hash **1354429876**.

| Perk | Selected ID | Weapon hash | Socket | Randomized plug set |
|---|---|---:|---:|---:|
| Triple Tap | aishas_embrace | 2638190703 | 3 | 7997267 |
| Triple Tap | ammit_ar2 | 2119346509 | 3 | 1723759242 |
| Triple Tap | austringer | 3055790362 | 3 | 2750499928 |
| Triple Tap | distant_relation | 2034817450 | 3 | 1131958073 |
| Triple Tap | duke_mk_44 | 2112909414 | 2 | 3744182842 |
| Fourth Time's the Charm | aishas_embrace | 2638190703 | 4 | 4211351701 |
| Fourth Time's the Charm | beloved | 3107853529 | 3 | 1196545279 |
| Fourth Time's the Charm | retrofit_escapade | 3103325054 | 3 | 3756086698 |
| Fourth Time's the Charm | seventh_seraph_officer_revolver | 3037520408 | 3 | 903350103 |

## Enumeration and exclusions

`references/socket-pools.json` preserves each eligible socket entry, trait category 4241085061, exact randomized plug-set hash, `isFakePlugSet=false`, original matching-entry index and full `currentlyCanRoll=true` record. Every selected item's sockets and referenced randomized/reusable set counts are audited, including negatives. Zero weights are preserved and do not negate rollability. The literal expected-tuple regression set was added after the independent scan; it never chooses eligible weapons or filters enumeration. Rows and audits are deterministically sorted.

Three direct defaults overlap their own exact randomized rows: Distant Relation and Aisha's Embrace for Triple Tap, and Retrofit Escapade for Fourth Time's the Charm. They add zero rows. Enhanced Triple Tap 573122728 occurs in Austringer and Ammit AR2; enhanced Fourth Time's the Charm 848860060 occurs in Beloved and Retrofit Escapade. All four enhanced entries are preserved as exclusion proof. There are no additional base occurrences outside the eligible randomized pools. None of the 63 selected definitions is exotic. All exotic catalysts remain excluded; catalyst-page text does not grant an unselected or exotic weapon a base randomized roll. This is selected-weapon proof, not a global census of catalysts.

## Source boundary and mechanics

Official pinned Bungie inventory and plug sets prove exact definitions, descriptions and eligible rolls. The descriptions establish rapid precision impacts and the returned round amounts. They do not establish the three/four-hit thresholds, numeric timing, reserve behavior, base-cap limit, stow behavior or reset rules.

Each exact-base light.gg Community Research section supplies its threshold and **2 seconds between successive precision hits**, rather than a two-second limit for the entire sequence. At 20 project ticks per second this is 40 ticks. Triple Tap generates one round after three hits; Fourth Time's the Charm generates two after four. The community measurements describe reserve-independent generation, a limit at the base magazine capacity and progress retained through stowing. Both sections report a July 30, 2024 research update. These are captured secondary measurements, not primary Bungie mechanics documentation or fresh gameplay tests. Enhanced timing and catalyst-granted variants are excluded.

The two consumed sections do not explicitly settle whether reloading, body hits or misses reset accumulated progress. Those points remain unresolved. The optional third capture is not consumed: neighboring Focused Fury reset text and Jade Rabbit/Cranial Spike body-shot discussion establish no reset rule for these two perks.

Sources: [Triple Tap exact base](https://www.light.gg/db/items/3400784728/triple-tap/?_=879), [Fourth Time's the Charm exact base](https://www.light.gg/db/items/1354429876/fourth-times-the-charm/?_=935). Official component URLs and SHA256 lineage are recorded in `references/provenance.json`. Full captures stay private in `/tmp/destiny-weapons-w67/research1.json` and `research2.json`; public evidence is paraphrased, without full article/search dumps or extended quotations.

## Main runtime's supplied policy

Expire progress at **at least 40 ticks since the last precision hit**, before counting a new hit. Each qualifying hit restarts that interval. Body hits and misses do not advance progress or update its clock, and no extra reset on reload is added without proof. No reload notifier is introduced. Stowing preserves progress but does not pause time. Returned rounds update the actual magazine without consuming reserves and are capped at base capacity. The existing HUD shows that real magazine; there is no invented precision-perk countdown row. Exact tick equality, reset handling and HUD choices are project integration policy, not independently proven Destiny internals. This sidecar neither implements nor verifies concurrent runtime changes.

## Offline reproduction

```sh
rtk proxy python3 scripts/extract_precision_return_w67.py
rtk proxy python3 scripts/extract_precision_return_w67.py --verify
```

`--root` selects the input checkout and defaults to the script's repository. `--output-root` selects a separate destination tree while keeping inputs at `--root`; it does not change output bytes. `--inventory`, `--shared-sources-dir` and `--sources-dir` override source-cache locations. Defaults are `/tmp/destiny-weapons-w30/bungie-items.json`, `/tmp/destiny-weapons-w60/{manifest,bungie-plugsets}.json` and `/tmp/destiny-weapons-w67/research{1,2}.json`. W40 selection and provenance come from the input checkout. Source locations are recorded; changing an input location changes provenance metadata, but never changes its required content hash.

All seven consumed source files have hardcoded SHA256 pins. The generator hashes itself in provenance and records the other four generated output hashes. Missing or changed sources fail before any output write. `--verify` compares all five generated outputs byte for byte, including this Markdown file, collects mismatches and performs no writes, directory creation, fetch, cache repair or network access. Missing outputs fail without repair. No Gradle, native app, git mutation or runtime edit is part of this work.
