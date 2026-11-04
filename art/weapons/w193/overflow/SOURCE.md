# Overflow — W193

Base [DDC Weapon Perks row 161](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278): **on Special or Heavy ammo brick pickup, refills the magazine with 100% increased capacity (2x base)**. May activate while stowed. Enhanced 120% capacity and Enhanced Trait hash `2682205016` are excluded. HTML SHA-256: `8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437`.

| Weapon | Official hash | Socket | Base Trait hash | Real plug-set hash | Base → target |
|---|---:|---:|---:|---:|---:|
| gnawing_hunger | 821154603 | 3 | 3643424744 | 1144396384 | 41 → 82 |
| lonesome | 2199171672 | 3 | 3643424744 | 3612808001 | 12 → 24 |
| brass_attacks | 2121785039 | 3 | 3643424744 | 100135553 | 24 → 48 |

All three assigned weapons are Primary. Refills follow the existing infinite-Primary policy; no finite Special/Heavy ammunition is generated or transferred into a Primary weapon. The pickup event is the trigger, not its reserve-credit amount.

The offline generator scans the full official catalog65 (63 base entries plus the two existing exotic extensions). Each accepted tuple requires the exact weapon hash, the weapon Trait socket category, its randomized plug-set hash, a nonfake real pool, a nondummy base Trait definition and `currentlyCanRoll=true`. All other catalog entries are recorded as negative matches. The local Parcel of Stardust frame suffix is an explicit catalog-label alias, not a different official weapon. Enhanced definitions are identified and excluded; they never supply fallback rolls.

Inputs: `/private/tmp/destiny-w193/remaining-sockets.json`, `/tmp/destiny-weapons-w30/bungie-items.json`, `/tmp/destiny-weapons-w60/bungie-plugsets.json`, `/tmp/destiny-weapons-w60/manifest.json`, and the pinned DDC HTML. Manifest version: `245114.26.10.13.2000-1-bnet.66137`. `source.json` records input hashes, the raw DDC row and normalized text, all 65 scan results and complete matching socket/pool proofs. Runtime resources are checksum-pinned. Provenance paths inside the repository are relative, so relocation does not change output bytes.

All predicates and capacity queries use existing read-only lookup paths: `WeaponItems.entry`, `WeaponPerks.selected`, `getAttachedOrElse` and `Guardians.runtimeIfPresent`. They create no player attachment or runtime, never save item data, and do not grant ammunition. Owner eligibility requires alive, connected, nonspectator, nonremoved players with an existing non-NONE Guardian and runtime outside Super. Stacks must be count-one original inventory objects, not copies or aliased references. Loadout mode requires the canonical equipped slot; standalone mode uses the actual hotbar.

## Checks and limits

Passed: exact pinned DDC row/hash validation, official full-catalog scan and the exact three base socket proofs, deterministic `--verify` for resource and evidence, and Java 25 `compileJava --offline` with `-Pgcb_server_dir=/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w193-overflow-magazines/libs/gcb-server`. Both dependency source directories resolve inside this isolated worktree. Compilation reported existing deprecation warnings only. Reviewed the current selected-perk decoder, original-stack/loadout ownership, base magazine path, timed reload credit callback, and reserve-only Lead from Gold pickup policy.

No assigned test file exists in this feature's ownership batch, so no new test file or mirror test was added. Master owns targeted GameTests for token lifecycle/ammo transfer, registry activation, shared runtime/lifecycle/pickup integration, persistent loaded-limit enforcement, actual HUD rounds and final integration validation. Full gates, Vision/native QA and animation work were not run. No commit, stash, reset, clean, push, child agent or shared source edit.

## Public API and master wiring

- Register `OverflowProfile.ID`, `rolls()`, and the display name in shared `WeaponPerks`. Profile static initialization is JSON-only, independent of registry initialization.
- Pure `boolean WeaponOverflow.selected(ServerPlayer, ItemStack)` checks current exact original equipped ownership, canonical entry, Primary type and exact selected base roll. It requires neither held status nor spare Special/Heavy reserves. Do not apply a held-weapon, handling, ADS or reload restriction.
- Pure `List<ItemStack> eligible(ServerPlayer)` returns an immutable list containing the actual eligible original references, in deterministic hotbar-slot order. Stowed eligible weapons are included. Aliased inventory objects are rejected. If an event boundary occurs before transfer, recheck `selected`; never retain this list as later pickup authority.
- Pure `int target(WeaponCatalog.Entry)` returns `2 * WeaponProfile.forEntry(entry).magazine()`, or 0 for unsupported/noncanonical entries. An entry alone grants no ownership: use it only after `selected` or `eligible`. `OverflowProfile.target` exposes the same calculation.
- Master AmmoEconomy invokes eligibility and target queries **inside a successful real Special/Heavy brick pickup transaction**, then performs `reloadOverflow(target)`, saving only actual gains on the original objects. It aggregates normal pickup, existing Lead from Gold and Overflow gains before consuming one brick and broadcasting. A brick can proc Overflow when that brick's normal reserves are full if an eligible Primary magazine can gain rounds. If every normal and Overflow transfer gains zero, preserve the brick.
- The helper has no sessions, attachments, mutators, RNG or lifecycle state. It does not consume a brick, refill a magazine, save inventory, clear reloads, fabricate a reload event, or proc on abilities/Dodge/manual refill. Master owns the persistent selected-perk loaded limit, actual-ammo HUD and cancellation semantics around its transfer.

Master integration checks should cover held and stowed targets, full picked-up reserves with Primary loaded gain, no brick consumption at zero aggregate gain, wrong socket/Enhanced/copy/alias rejection and cleanup of loaded authority after perk/lifecycle changes. No helper-only numeric mirror test is needed.

Regenerate: `rtk proxy python3 scripts/build_overflow_w193.py`. Read-only verification: append `--verify`. The generator writes only its two assigned JSON paths. Resource SHA-256: `8cd3a8a034557bc79cd83ec801edf105eff66870900689fdd09edfce3dd17cb6`.
