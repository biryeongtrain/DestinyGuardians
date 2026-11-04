# W192 Backup Plan

Base **Backup Plan**, hash `1600092898`, DDC **Weapon Perks row 24**, exact name cell.
[DDC Weapon Perks](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278).
The pinned HTML SHA256 is `8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437`.
The raw HTML row and normalized row text are included in `source.json` and the runtime resource.

Upon readying after **3 seconds of observed stow**, grant **0.8 damage**, **+100 handling**,
and **0.7 charge time** for **2 seconds**. At 20 Hz those clocks are 60 and 40 ticks.
Paid Linear Fusion Rifle shooting refreshes an active window; ordinary Fusion Rifle shooting
does not. Exact expiry is expired. A late emission from a previously accepted buffed charge
retains its accepted profile, but cannot revive an expired window.
Enhanced hash `828056542` and the row's enhanced `↑2.5 seconds` annotation are explicitly excluded.

## Exact eligible rolls

| Weapon | Item hash | Trait socket | Randomized plug set |
| --- | ---: | ---: | ---: |
| hollow_words | 607191995 | 4 | 1485010760 |
| dream_breaker | 2931957300 | 4 | 1206254527 |
| line_in_the_sand | 946443267 | 4 | 3257645194 |

Generator scans the full selected catalog65, requires a real Trait socket, base Trait definition,
non-dummy/non-redacted/non-blacklisted plug, real randomized plug set and `currentlyCanRoll=true`.
The exact three matches must equal `/private/tmp/destiny-w192/base-sockets.json`'s `Backup Plan` list.
`source.json` retains every selected weapon's trait entries and plug sets, the complete catalog scan,
the allowed/excluded companion audit and SHA256/byte counts of all inputs.

Manifest version: `245114.26.10.13.2000-1-bnet.66137`. Official definitions come from
`/tmp/destiny-weapons-w30/bungie-items.json` and
`/tmp/destiny-weapons-w60/bungie-plugsets.json` / `manifest.json`.
The generator does not fetch network data or depend on timestamps or directory iteration.

## Timing and legal companions

Handling/ADS raw quadratics come from `art/weapons/w46/weapon_formulas.json`, mapped via
`art/weapons/w43/extraction.json`, historical Oracle commit
`dcd0c7d302b056ffbb532edcb711d724a17ca8c1`. These are historical community approximations,
separate from current official sockets/stats and DDC perk numbers. Their unmodified handling/ADS
baselines are checked against the authored W58/W44 profiles. No rounded-duration ratios are used.

+100 handling saturates the legal positive stat bonuses at the 100-stat cap. The wrappers retain
the other-socket scalar effects: Dream Breaker and Line in the Sand Threat Detector `1/.9/.81`,
Hollow Words active Quickdraw ready `.95`, and Dream Breaker entering Snapshot ADS `.8`.
TD is sampled for the exact incoming object once in `selecting`, before vanilla changes selection;
the timing wrapper reads that cache and never scans entities or imports the outgoing TD sample.
Quickdraw's pure incoming/held authority is probed with a sentinel base value solely to establish
activation; the resulting tick count is not used to derive a ratio. Evaluate raw seconds then ceil once.
Frenzy and Dream Breaker Quickdraw occupy Backup Plan's own socket and cannot co-select.
All 14 allowed companion rolls and same-socket exclusions have independent official socket proofs.

Charge time uses official raw milliseconds **800 / 667 / 533**, multiplied by `.7` before a single
ceil to ticks: **12 / 10 / 8**. Damage multiplies the incoming local Minecraft profile by `.8`;
this is a relative DDC effect, not a claim of original Destiny damage values. Every other profile
field (ammo, burst topology, recovery/cadence, reload, physics) is preserved.

## Master integration contract

Public static methods on `WeaponBackupPlan`:

```java
void update(ServerPlayer player);
void selecting(ServerPlayer player, ItemStack incoming);
void stowing(ServerPlayer player, ItemStack outgoing);
WeaponProfile charge(ServerPlayer player, WeaponCatalog.Entry entry, WeaponProfile base);
void paidEmission(ServerPlayer player, WeaponCatalog.Entry entry);
int handlingTicks(ServerPlayer player, ItemStack stack, boolean ready, int base);
int adsTicks(ServerPlayer player, WeaponCatalog.Entry entry, int base, boolean entering);
int remaining(ServerPlayer player);
int handlingBonus(ServerPlayer player);
void changed(ServerPlayer player, ItemStack stack);
void edited(ItemStack stack);
void cleanup(ServerPlayer player);
void clear();
```

Register `BackupPlanProfile.ID`, `HASH`, and `rolls()` in the shared perk registry. Initialization
of this profile reads JSON only; it does not call registry/catalog/characteristic initialization.

* Call `update` on gameplay ticks and before accepted selection. It observes every eligible equipped
  stack, including stowed stacks. A first-seen held weapon gets no proc; a first-seen stowed weapon
  starts its stow clock now. No unseen weapon receives a fictional previous 60 ticks.
* In `WeaponHandling.select`, accept outgoing duration first, then call `stowing(outgoing)`,
  then `selecting(incoming)` before accepting incoming ready duration. Keep the same `stowing`
  hook on `inventoryStowing` / observed inventory selection transitions. Never call `changed`
  for ordinary stow: it intentionally discards accumulated stow credit.
* Apply handling and ADS wrappers outermost, including after Well-Rounded. `selecting` samples
  incoming TD; wrappers/charge/HUD queries never bind, scan, create attachments or advance clocks.
* At **each new charge acceptance**, call `charge(player, entry, base)` and retain the complete
  returned profile as `acceptedCharge`. Both initial and continued charge paths, the charged gate,
  emission damage and delayed shared paid bursts must use that retained value. An accepted
  profile remains immutable across expiry; never call the wrapper again to continue that charge.
* Call `paidEmission(player, entry)` immediately after successful `cycle.fire`, once for the paid
  emission. Denied input, accepted charging, dry fire, canceled charge and per-bolt callbacks do not
  invoke it. Only a currently valid held LFR with a still-active window refreshes.
* Wire `edited` for perk/source edits; `changed` for replacements, drops, inventory transfers and
  source removal; `cleanup` for death, disconnect, dimension/class/loadout/runtime lifecycle and
  super invalidation; `clear` for global shutdown/reset. Events run on the main server thread.

Sessions pin actual player, level, hotbar slot and stack identity, canonical entry and exact selected
base roll, GuardianData/runtime identity, class, loadout-enabled state and monotonic observation time.
Reads reject invalid sources immediately; update permanently retires invalid sessions. Pending incoming
selection is valid only within its original same-tick transaction; abandoned preparation gains no credit.
Copied/offhand/backpack/foreign objects cannot reuse the owned source's clock. Ordinary stow cancels
the buff and begins a new real 60-tick interval. Source/lifecycle invalidation discards both clocks.

## Checks and limits

Passed in the assigned isolated worktree, Java 25:

```text
rtk proxy python3 scripts/build_backup_plan_w192.py --verify
rtk proxy env JAVA_HOME=/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home ./gradlew -Pgcb_server_dir=/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w192-backup-plan/libs/gcb-server test --tests kim.biryeong.destiny.weapon.BackupPlanCycleW192Test --console=plain
```

The Gradle command compiled main/test sources and passed **10 focused cycle tests** covering first
observation, 59/60-tick stow boundary, 39/40-tick expiry, duplicate selects/stows, same-tick away/back,
paid LFR refresh, no fusion or late-window refresh, pure reads, observed transitions, clock rewind,
overflow and lifecycle invalidation. The generator verifies both JSON outputs byte-for-byte.
No mirror numeric tests, unrelated fullserver gate, Vision/native operation or animation work ran.
Shared registry/runtime/handling/ADS integrations and the actual server charge/lifecycle scenarios
belong to master; isolated unit tests do not establish those integrated runtime results.

Only the eight paths assigned to `w192-backup-plan` in `batch.json` were authored. No commit,
reset, stash, clean or push was performed.
