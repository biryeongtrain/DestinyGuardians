# W194 Relentless Strikes — base Trait

## Sources and deterministic reproduction

- User DDC: Weapon Perks row 182, [spreadsheet](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278).
- DDC HTML `/private/tmp/destiny-w190/ddc-perks.html`, SHA256 `8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437`.
- Manifest version `245114.26.10.13.2000-1-bnet.66137`. Inventory, plugsets, manifest, DDC and four catalog inputs are SHA256-pinned by the generator.
- `source.json` preserves the exact matching name-cell row as `rawHTML` (including yellow enhanced markup), readable row text, full socket category/entry/plugset proofs, all 65 canonical catalog scan results, and output checksum.
- Eligible sockets are category `4241085061`, randomized pools with `isFakePlugSet=false`, base plug `currentlyCanRoll=true`, non-dummy/non-redacted/non-blacklisted exact `itemTypeDisplayName=Trait`. Exotics and enhanced definitions are excluded.
- Enhanced hash `4085959009` is excluded. No enhanced numbers, yellow text values or unknown chance are applied.
- Generated resource SHA256 `ebf46b35a98f1bcfbd91c8f1cf547f48c4de609a020163b62003d61f56b126f6`; profile independently pins this checksum and exact ordered roll tuples.

```sh
rtk proxy python3 scripts/build_relentless_strikes_w194.py
rtk proxy python3 scripts/build_relentless_strikes_w194.py --verify
```

`--verify` compares resource and provenance bytes without writes; generator uses no subprocess or network.

## Source rows

| Weapon id | Bungie hash | Socket | Plugset |
|---|---:|---:|---:|
| abide_the_return | 1644160541 | 3 | 211008653 |
| goldtusk | 3371413057 | 3 | 1162279549 |
| crown_splitter | 2782325302 | 3 | 427353656 |
| falling_guillotine | 614426548 | 3 | 2228304432 |
| temptation_s_hook | 35794111 | 3 | 4018960212 |

5 roll rows / 5 sword weapons; all 65 canonical items scanned, including W83/W84 exotics.

## Behavior and integration contract

Base DDC: three powered sword hits with each successive gap at most 2 seconds. Local mapping: 20 server ticks per second; inclusive 40-tick gap; reset after reward. Cleave counts each actually damaged target once per paid contact; direct/explosion share that contact. Counters survive stow; time still passes. Only confirmed positive finite actual HP/absorption loss generates loaded ammunition, never reserve transfer. Bounded local ledger retains latest 128 accepted contacts and 256 target identities per contact; evicted contacts never become eligible again.

- `WeaponRelentlessStrikes.capture(ServerPlayer)` returns opaque `Token` or `Token.NONE`. Master calls only once per accepted paid, nonempty sword contact. Share the exact token across cleave, caster direct and explosion; never recapture for splash. Source family must be sword. No capture from queries, generic death, abilities, glaives or empty-sword attacks.
- `confirmed(ServerPlayer, Token, LivingEntity, double actualLoss)` is an event after eligible positive **actual** HP/absorption loss; finite loss only. Nonpositive/NaN/infinite loss cannot consume a target credit. Each distinct target counts once per contact; the same target in a later paid contact can count again. The source helper does not require the target to survive the hit.
- Both event methods **perform** `WeaponItems.magazine(originalStack, profile).generateLoaded(1)`, save the same original stack, mark inventory changed and broadcast only if positive ammo was generated. Return value is actual generated rounds (0 or 1); master must not award it again. Reward at full ammo is consumed rather than deferred. No reserve/legacy-overflow transfer and no infinite sword ammunition.
- `progress(p)` is a pure held-source query. No attachment, accepted contact, counter mutation or ammo grant is performed.
- `update(p)` validates source identity, count-one ownership, hotbar/canonical loadout membership, original selected roll/catalog entry, owner object/world/GuardianData/class/GuardianRuntime/loadout state, alive/connected/non-spectator/non-Super status and monotonic server ticks. It never binds a replacement source.
- `changed(p, stack)` and `edited(stack)` invalidate original source epochs, including same-tick edit-away-and-back. `cleanup(p)` revokes owner source epochs at death/disconnect/world/class/runtime/loadout/Super transitions. `clear()` revokes all source epochs. Master owns dispatch. Never call changed/cleanup for ordinary stow; counters and delayed original-source callbacks survive stow.
- Ledger limits (128 contacts per source, 256 distinct targets per contact) are defensive local implementation limits, not DDC numbers. FIFO-evicted tokens fail closed; no contact TTL is invented.

## Validation and limits

- Java 25 targeted Gradle invocation compiles helpers against the actual snapshot and isolated GCB/minigame dependency sources. Exactly the two assigned Cycle tests run; no numeric mirror tests are added.
- Focused cases cover successive windows/expiry, positive actual loss, multi-target/direct-splash dedup, bounded ledgers, first kill and shared entitlement, stow persistence, query purity, source epoch, foreign token and tick rollback.
- Source application reviewed: `WeaponItems.magazine` projects sword single-pool ammunition; `WeaponMagazine.generateLoaded` explicitly creates capped loaded reward without reserve movement; `WeaponItems.save` updates the original ItemStack components. Current snapshot Runtime still needs master integration for these new profiles/tokens and event/lifecycle dispatch.
- Shared registry/Runtime/Aiming/Handling files, full gate, scoped server integration tests, game clients/Vision, animations, sealed historical QA and unrelated dirty/untracked files are outside this assigned delta. No child, commit, stash, reset, clean or push.

## Isolated result

- Both assigned Cycle suites: 12 tests total, 0 failures/errors/skips.
- Both generators: deterministic `--verify` passed for resource and provenance.
- Out-of-scope audit: 67,142 tracked/untracked non-owned paths retained the baseline aggregate SHA256 `298cd228bc490f652f6306794e09adf9c520c06b28cc3fb4ac4834dd77086855` (missing paths included); ignored build outputs are excluded.
- All 16 assigned files were absent at baseline and are newly added. Original dirty/untracked source and sealed QA were preserved.

```sh
rtk proxy env JAVA_HOME=/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home ./gradlew -Pgcb_server_dir=/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w194-sword-ammo/libs/gcb-server test --tests kim.biryeong.destiny.weapon.RelentlessStrikesCycleW194Test --tests kim.biryeong.destiny.weapon.TirelessBladeCycleW194Test --console=plain
```
