# Base Lead from Gold — W187

Base trait hash **1556840489**; enhanced **3442762221** is excluded. All 65 catalog weapons, including the two exotics, were independently scanned against the cached official inventory, plug sets, and manifest. Acceptance requires the real weapon trait category **4241085061**, a legendary nonexotic Special weapon, its randomized plug-set reference, a nonfake pool, the exact base hash, and `currentlyCanRoll=true`. Reusable-only, enhanced, exotic, wrong-category, fake, and unavailable entries cannot authorize a roll. The scan finds six unique base sockets and one excluded enhanced match. Full 65-weapon reference audit, exact definitions, source matches, and matching official pools are in official-sockets.json.

## Current community mechanics, separately from official availability

Clarity and the Destiny Data Compendium were independently fetched during W187. The live Clarity whole-file SHA256 is **881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384**, identical to the supplied W167 cache. The public DDC HTML whole-file SHA256 is **6bd6dd4534aac0490e77cb4d94caba9f3de23e75a498fbf22c763c7013d95044**. Both support 25% of maximum Special reserves for a Heavy pickup, activation while stowed, and halving to 12.5% when two Special weapons are equipped. DDC explicitly distinguishes enhanced 35%/17.5%; those numbers are excluded. The extracted base Clarity object and DDC row are preserved in clarity-source.json; full fetched inputs and fetch metadata are report-local.

- [Live Clarity source](https://raw.githubusercontent.com/Database-Clarity/Live-Clarity-Database/live/descriptions/clarity.json)
- [Destiny Data Compendium, Weapon Perks](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278)
- [Bungie developer note, 11 August 2022](https://www.bungie.net/7/en/News/Article/51645) explains that the perk must split Special pickups when two Special weapons are equipped. This supports the equipped-weapon count boundary, rather than counting only weapons selecting this perk. It does not establish an exact current integer algorithm.
- [Bungie Update 6.2.0](https://www.bungie.net/7/en/News/article/51707) records the double-Special correction. The article was checked through indexed search text; it is historical context, not new sandbox testing.

Official availability comes from `/tmp/destiny-weapons-w30/bungie-items.json`, `/tmp/destiny-weapons-w60/bungie-plugsets.json`, and that directory's manifest.json. Manifest version is **245114.26.10.13.2000-1-bnet.66137** with matching en inventory/plug-set component suffix `e677f6ea-2a1e-48d4-a8c8-700a39a62585`. These are pinned cached official definitions, not a new live Bungie inventory download. All local and external inputs are hashed in manifest.json and rejected on drift.

## Reserve meaning and integer policy

Current Clarity/DDC identify maximum Special reserves, not current ammunition or the amount accepted by the Heavy weapon. They do not unambiguously specify whether the original maximum includes a loaded magazine, nor a current rounding algorithm. Research also found an older test-guide mirror suggesting total magazine-plus-reserve and ceiling, explicitly as an estimate. Its original publication/version could not be established as current primary evidence, so it is not used to assert original rounding: [older mirrored guide](https://www.scribd.com/document/866079149/drfgdfgdgfdfgfdghyrtetryyrt). No exact original reserve definition or rounding success is claimed.

**Authored port policy:** maximum reserve means the project's bounded `WeaponProfile.reserve()` capacity, excluding magazine and conserved legacy overflow. It uses existing local PvE capacities, not newly sourced original Destiny reserve counts. Award `ceil(reserveCapacity / 4)` for one equipped Special and `ceil(reserveCapacity / 8)` for two, using one integer ceiling after the split. This preserves the sourced 25%/12.5% rate within the project's reserve model. It is a declared implementation choice, not evidence of exact Destiny arithmetic. Unsupported/noncanonical entries and equipped counts outside 1..2 yield zero. Amount queries are pure, independent of current ammo, and never award anything.

| Weapon | Hash | Socket | Randomized pool | Local reserve cap | One / two Special request |
|---|---:|---:|---:|---:|---:|
| apostate | 2164448701 | 3 | 1306932196 | 20 | 5 / 3 |
| mindbender_s_ambition_adept | 912150785 | 3 | 1732284294 | 25 | 7 / 4 |
| hollow_words | 607191995 | 3 | 637298592 | 30 | 8 / 4 |
| dream_breaker | 2931957300 | 3 | 3785896921 | 30 | 8 / 4 |
| deafening_whisper | 981718087 | 3 | 3110206796 | 16 | 4 / 2 |
| nezarec_s_whisper | 254636484 | 3 | 210449465 | 30 | 8 / 4 |

## Integration contract

`LeadFromGoldProfile.ID/HASH`, immutable `rolls()`, `supports(WeaponCatalog.Entry)`, and `amount(WeaponCatalog.Entry,int equippedSpecialCount)` are the profile API. Initialization reads JSON only to avoid catalog/trait-registry recursion. `WeaponLeadFromGold.grant(ServerPlayer)` returns actual accepted reserve rounds summed across qualifying unique stack identities. It requires an enabled real WeaponLoadout and a living, present, nonspectator owner. The genuine equipped Special list is built before looking for this trait, so a second Special without Lead from Gold still halves the first one's award. Stowed equipment works without main-hand or selected-slot checks.

WeaponLoadout's fixed slot/category and WeaponItems' live-combat validation exclude backpack, offhand, previews and wrong-slot weapons. The runtime additionally rejects non-singleton stack counts, rechecks exact inventory object/slot, canonical catalog identity, and deduplicates by stack identity before counting/awarding. Only exact selected base official roll tuples qualify. `WeaponItems.magazine` projects existing saved ammo; `WeaponMagazine.addReserve` caps newly accepted reserve rounds and preserves legacy overflow. Only positive acceptance is saved. Full reserve returns zero without a save. No magazine refill, reload/precision-trait callback, ability energy, ammo meter change, timer, passive HUD, or session state is introduced. No broadcast occurs; inventory is marked changed only for a positive total.

Master registers the trait in shared WeaponPerks and calls `grant` exactly once inside the validated real Heavy pickup transaction. The returned Special acceptance must participate in the brick-consumption decision, including full-Heavy/needy-Special cases. Master aggregates all changes and broadcasts inventory once. Ordinary ticks, inspection, Special pickups, fabricated events and unsuccessful pickup attempts must never call `grant`. The function intentionally has no independent pickup-event authentication or persistent deduplication: the real transaction is the authority. This worker edits no shared registry, AmmoEconomy or lifecycle hooks.

## Verification and limits

Two owned JUnit classes execute actual production profile/math and WeaponMagazine behavior, plus runtime source-boundary assertions and a null-owner call. Source assertions cover owner/loadout guards, correct equipped counting, identity deduplication, exact roll validation, reserve-only writes, absence of broadcast/ticks/HUD, and save-after-positive-acceptance. They do not execute a real player inventory grant. No stub runtime or Player classes are used. The generator verifies pinned inputs, exact six tuples, 65-weapon scan, deterministic output reproduction, semantic/predicate negative cases and corrupt-source rejection.

All worker Gradle user-home/project caches/build outputs, fetched sources, logs and machine reports are outside the repository at `/private/tmp/w187-gold-report`. Only ten assigned source/data/test/provenance files are exported. No native/server/client/CU/Vision/actualGT/runtime pass is claimed. Master owns actualGT for real grant boundaries, heavy transaction integration, shared gates, and native QA. Required scenarios include stowed 1/2 Specials (only one selecting the perk), both perk stacks, all rejected locations/owners, full reserves, full Heavy but needy Special, capped acceptance and legacy overflow conservation.
