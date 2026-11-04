# W104 tracking source/extractor lead — frozen handoff

## Exact source result

Pinned Bungie manifest `245114.26.10.13.2000-1-bnet.66137` and matching official inventory (199,128,691 bytes) / plugsets (10,438,797 bytes) were inspected **before web research**. All **63 selected item hashes**, every referenced randomized/reusable socket pool, and direct initial/reusable socket choices were scanned. The generator independently checks pinned hashes, manifest component paths, official selected item identity/stats/ammo metadata, socket categories and actual rollability.

| Support | Exact item | Socket | Source |
|---|---|---:|---|
| Automatic intrinsic eligibility | Pyroclastic Flow `1289324202` | 0 | Precision Frame **3419274965**, Intrinsic; initial socket, intrinsic category3956125808 |
| Optional selected base trait | Bad Omens `991314988` | 3 | Tracking Module **3977735242**, randomized pool **457210958**, real pool, currentlyCanRoll=true |
| Optional selected base trait | Bellowing Giant `2186258845` | 3 | Tracking Module **3977735242**, randomized pool **2605036073**, real pool, currentlyCanRoll=true |
| No tracking eligibility | Code Duello `2496242052` | — | High-Impact Frame1019291327; no selected base Tracking Module option |

Enhanced Tracking Module **406461158** is not supported and no selected enhanced pool option was found. No curated-only base option was found. Direct/initial Tracking Module entries on the two eligible rockets corroborate their randomized pool proof; **they do not force a local stack to equip the trait**. Do not infer any other same-name Precision Frame weapon tracks rockets.

## Behavior evidence / uncertain rules

Primary descriptions prove aimed/ADS locking. [Bungie's exact Bad Omens item page](https://www.bungie.net/en/Explore/Detail/DestinyInventoryItemDefinition/991314988) corroborates the pinned base description. The manifest is the authoritative source for the exact old Pyroclastic Flow hash and intrinsic, rather than similarly named newer edition3161496501.

A [light.gg/Clarity secondary entry](https://www.light.gg/db/ja/items/3977735242/%E8%BF%BD%E8%B7%A1%E3%83%A2%E3%82%B8%E3%83%A5%E3%83%BC%E3%83%AB/) reports one-second persistence when aiming away and diminished PvP tracking. It is preserved as secondary evidence only, **not promoted to an exact numeric runtime rule**. The direct English and localized page fetches failed402; URL-bound search excerpts are pinned in private research captures. No primary measurement protocol was inspected.

No verified acquire duration, angular cone, range, turn rate, target-death reacquire rule, launch snapshot rule, post-stow/edit persistence, or midflight LOS-loss behavior was found. In particular:

- An occluded target is **not** proven to immediately break in-flight homing.
- A wall physically blocking the projectile is distinct from cancelling tracking because shooter/rocket-to-target LOS was lost.
- Official ADS acquisition does not establish continued ADS after launch.
- Aim-loss grace is not rocket lifetime.
- No measured equivalence of precision intrinsic and trait turning/acquisition was found.

All unknown source values are `null` under `sourceRules.unknownSourceRules`. Master owns separately labelled local policy and Java; do not coerce these nulls to allegedly source-exact zeros/defaults.

## Frozen files / validation

- `scripts/extract_tracking_w104.py`
- `src/main/resources/destiny/weapons/w104-tracking.json`
- `art/weapons/w104/references/CONTRACT.md`
- `art/weapons/w104/references/mechanics.json`
- `art/weapons/w104/references/socket-pools.json`
- `art/weapons/w104/references/provenance.json`
- `art/weapons/w104/references/verification.json`

```sh
rtk proxy python3 scripts/extract_tracking_w104.py --verify --self-test
```

PASS: SHA-pinned offline reproduction; two disjoint output roots byte-identical for all four generated files. Five bounded semantic mutation fixtures reject canRoll=false, fake randomized pool, same-name wrong intrinsic hash, enhanced-type impostor, and curated/reusable masquerading as randomized source. Verification deliberately does not run builds or imply native gameplay acceptance.

Source profile SHA256: `c4ecf3805a1cc7c6529565f899cc45efbb811bf07c743558a40c76aadd3e789e`.

Research bounded to **8 query strings**, followed by opens of specific discovered pages. One direct guessed Clarity description-repository API fetch returned404; no data adopted. No further searches. Private captures under ignored `run/private-sources/w104`; no third-party code executed. No child-agent tools exposed; no child work claimed.

No Java/shared docs/tests/registry/build/runtime/CU work performed. W103 sealed artifacts were not changed. Public API/data contract is ready for master's `TrackingProfile.supportsIntrinsic(Entry)` and actual `WeaponPerks` selected optional trait integration.
