# W66 Rampage source and data sidecar

The pinned selection independently yields **21 real randomized base-Rampage rows** from 63 exact weapon hashes. The runtime resource contains only `stage`, `perk` and `WeaponPerks.Roll`-shaped `weapons`. Its values are 90 ticks per decay interval and multipliers 1.0 / 1.1 / 1.21 / 1.331.

## Eligibility

`references/socket-pools.json` preserves each item's exact hash, zero-based socket, socket entry, trait category 4241085061, randomized plug-set hash, `isFakePlugSet=false`, original matching-entry index and full `currentlyCanRoll=true` record. Enumeration scans all selected sockets before checking the independent 21-tuple regression oracle. Zero weights are retained and are not a rejection criterion.

Eight direct/initial defaults overlap those randomized rows and add no runtime rows: Gnawing Hunger, Dust Rock Blues, Parcel of Stardust, Dream Breaker, Line in the Sand, Stormchaser, Deafening Whisper and Hammerhead. These are defaults/curated evidence, not a second allowlist. Enhanced 288411554 occurs in Austringer, Beloved, Fixed Odds and Retrofit Escapade pools and is excluded. Huckleberry-specific 3551326236 has zero selected occurrences and is excluded. No sword or glaive is supported; names and same-name reissues do not prove eligibility.

## Evidence layers

1. **Official inventory and plug sets** prove the exact eligible roll and weapon-kill trigger with a three-stack limit. They do not supply numeric damage, duration, stow or refresh behavior.
2. **Bungie Update 9.5.0, December 2, 2025** establishes gradual one-stack expiration. The bounded quote and URLs are in `references/mechanics.json`. This date comes from the absolute article date, not a relative search-engine timestamp. `research2.json` contains the official mirror's change; `research3.json` contains the canonical article date but its saved body stops at line 285 of a reported 888, before the Rampage section. A direct ContentStack body fetch independently confirmed the change and absolute timestamp; its bounded metadata is in provenance. That in-memory response was not retained and is not independently rechecked offline.
3. **Exact-base light.gg Community Research** (hash 3425386926, reported update December 27, 2025) supplies 4.5 seconds, 10/21/33.1 percent increases and one-at-a-time expiration. It omits explicit stow and refresh statements. These are secondary measurements captured by search, not fresh gameplay tests; direct open returned HTTP 402.
4. **D2 Arsenal's Rampage section** on weapon 3132669561 explicitly supports keeping the buff through stowing and renewing its duration after additional weapon kills. It also agrees with the base duration and gradual decay. This is a single explicit secondary source for stow and refresh, on another weapon's page; it proves no selected weapon's pool. Its enhanced five-second annotation is excluded. Adjacent Killing Tally/Outlaw text and generic forum posts supply no official Rampage evidence.

Sources: [Bungie 9.5.0](https://www.bungie.net/7/en/News/Article/destiny_update_9_5_0), [official mirror](https://origin-static01.bungie.net/7/en/News/Article/destiny_update_9_5_0), [exact-base light.gg](https://www.light.gg/db/items/3425386926/rampage/?_=688), [D2 Arsenal](https://d2-arsenal.vercel.app/weapon/3132669561). Full captures remain private in `/tmp/destiny-weapons-w66/research1.json` through `research4.json`. Public output is compact evidence and paraphrase, not full articles or search dumps; the Bungie quotation is ten words.

## Runtime integration boundary

The agreed W66 policy retains timed sessions per owned ItemStack through stow, advances each elapsed decay interval, and resets the next deadline after a qualifying kill even at the three-stack cap. A delayed projectile final blow credits its original stack only if still possessed by the original owner with Rampage selected; it need not be the currently held gun. A projectile retains the multiplier captured at emission. Copies and new owners inherit no session. These object/ownership rules, exact tick endpoints, refresh ordering and shot snapshots are authored integration decisions, not proven Destiny internals. Independent live confirmation of stow and refresh remains unresolved. This sidecar does not implement or test the concurrent runtime.

## Reproduction

Run from the shared repository, without Gradle:

```sh
rtk proxy python3 scripts/extract_rampage_w66.py --verify
rtk proxy python3 scripts/extract_rampage_w66.py --output-root /tmp/destiny-weapons-w66/reproduced
rtk proxy python3 scripts/extract_rampage_w66.py --output-root /tmp/destiny-weapons-w66/reproduced --verify
```

The script's `--root` selects the read-only input checkout; `--inventory`, `--shared-sources-dir` and `--sources-dir` locate the pinned source caches. Defaults are `/tmp/destiny-weapons-w30/bungie-items.json`, `/tmp/destiny-weapons-w60/{manifest,bungie-plugsets}.json` and `/tmp/destiny-weapons-w66/research{1,2,3,4}.json`. W40 definitions and provenance are read from the input checkout. Source locations are recorded in provenance; changing those locations changes that metadata. `--output-root` alone does not change bytes.

Every consumed local source has a hard-coded SHA256 pin. Missing or changed inputs fail before any output write. `--verify` checks every byte of the resource, all three reference JSON files and this Markdown file, and never creates directories, writes, fetches or repairs sources. The generator's own SHA256 and all non-provenance output hashes are included in provenance. Source caches must already exist; raw captures are intentionally not bundled. No Gradle, native app, assets, runtime code or git commit is part of this sidecar.
