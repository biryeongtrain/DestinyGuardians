# Base Quickdraw — W185

Base trait hash **706527188**. This implementation caps ready/stow handling at 100 for 20 server ticks after a real weapon selection. The 0.95 duration multiplier applies to ready only. ADS input irrevocably cancels the window, including during handling or a press/release between ticks. Reads do not arm or extend it. No ADS-speed, reload, stability, damage, ammo or passive HUD grant is implemented.

## Mechanics and provenance

- [Bungie, 8 April 2021](https://www.bungie.net/7/en/News/article/50237) documents the one-second / ADS end condition. This historical developer announcement is context, not proof of current animation coefficients. The current fetch returned a small web shell; the research search result supplies the article passage.
- [Current Clarity base entry](https://github.com/Database-Clarity/Live-Clarity-Database/blob/live/descriptions/clarity.json), hash 706527188, explicitly separates ready/stow handling from the ready-only multiplier and identifies ADS input as the cancellation event. Independently fetched live during W185; whole-file SHA256 **881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384**, identical to the pinned cache. The extracted row is in clarity-source.json.
- [Destiny Data Compendium, Weapon Perks](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278) independently confirms the base numbers and end condition. W185 fetched and parsed the public HTML row. The upward-arrow +5 handling notation denotes enhanced Quickdraw and is excluded. CSV refresh returned HTTP 401; that failure and the successful HTML refresh are preserved outside the worktree.
- Current official inventory, plug sets and manifest are pinned separately from community mechanics. Manifest version **245114.26.10.13.2000-1-bnet.66137**. All 65 selected weapons, including exotics, are scanned. Acceptance requires a nonexotic legendary weapon, real trait category, randomized pool, nonfake pool, base hash, and currentlyCanRoll=true. Enhanced hash **1961144892**, reusable-only matches, fake pools and exotic choices are excluded.
- Historical raw timing provenance uses the existing W43 mapping and W46 d2foundry oracle snapshot **dcd0c7d302b056ffbb532edcb711d724a17ca8c1** with its MIT/Unlicense sources. The source equations are in art/weapons/w46/weapon_formulas.json and stat_calc.rs. This is existing project calibration, not newly measured current Destiny timing. All 16 raw baselines reproduce W58 handling before the perk is applied. See curves.json and manifest source pins.

## Exact official rolls

| ID | Weapon hash | Socket | Randomized pool |
|---|---:|---:|---:|
| blast_furnace | 3843477312 | 3 | 1976101165 |
| dead_man_walking_xx7463 | 3751622019 | 3 | 3268663985 |
| biting_winds | 1621657423 | 3 | 3968704963 |
| whispering_slab | 211938782 | 3 | 1885424927 |
| beloved | 3107853529 | 4 | 887157889 |
| apostate | 2164448701 | 4 | 2826016044 |
| parcel_of_stardust_fell_to_earth | 2217366863 | 4 | 3424940310 |
| hollow_words | 607191995 | 3 | 637298592 |
| dream_breaker | 2931957300 | 4 | 1206254527 |
| edge_transit | 218335759 | 4 | 2535579724 |
| bad_omens | 991314988 | 4 | 2955928741 |
| bellowing_giant | 2186258845 | 3 | 2605036073 |
| code_duello | 2496242052 | 3 | 3719628667 |
| pyroclastic_flow | 1289324202 | 3 | 528513254 |
| fixed_odds | 2194955522 | 3 | 4227334000 |
| hammerhead | 603242241 | 3 | 2515290473 |

Apostate contains two current base Quickdraw plug entries in the same official randomized pool. Both matching entries are retained in official-sockets.json proof data; there is one selectable roll tuple. No invented second socket is exposed.

## Exact legal handling scalar companions

Threat Detector hash **4071163871** is the only implemented companion with a legal handling duration scalar: stacks 0/1/2 map to 1/0.9/0.81. QD already saturates the handling stat. Surplus (Beloved/Apostate) and Frenzy (Code Duello) can co-select, but their positive handling stats do not exceed that cap; they introduce no extra QD handling scalar. Snapshot legal pairs affect their existing ADS system only. All 37 legal implemented pairs and same-socket rejections are audited in official-sockets.json.

| Weapon | TD socket | TD pool | QD+TD2 ready ticks | QD+TD2 stow ticks |
|---|---:|---:|---:|---:|
| parcel_of_stardust_fell_to_earth | 3 | 2514419370 | 4 | 4 |
| dream_breaker | 3 | 3785896921 | 6 | 3 |
| edge_transit | 3 | 447678063 | 5 | 5 |
| bellowing_giant | 4 | 1722393382 | 5 | 4 |

## Runtime boundary

Master owns shared registry/debug/runtime/actualGT integration. Handling computes outgoing duration, calls selected on a genuine source identity change, then computes incoming duration. Initial tracking bind is not a draw. InputRouter invokes aimInput before the Guardian early return. Generic cancelUseForSkill must not cancel the newly armed draw.

Only selected creates a QD session. Exact owner, level, hotbar/loadout object, selected official roll, existing attachment/runtime identities and Guardian class are validated. Accepted skill-action changes, source edits, replacement, super, death, disconnect, ADS and expiration terminate authority. A pending incoming read is restricted to the same tick and captured outgoing object; debug remaining is genuinely held only. Master lifecycle/edit hooks retire sessions. No detached copy, backpack or offhand can authorize.

At accepted selection only, exact QD+TD pair validation permits master WeaponThreatDetector.selectionSample(p,incoming). Its loaded-entity sample is cached as incomingThreats. Pre-selection timing consumes that cached value; genuinely held timing uses WeaponThreatDetector.stacks(p). Timing/debug getters never scan entities or mutate TD held sessions. The authorized master TD source snapshot is compiled from the report only; no shared source is edited/exported by this worker.

All timing uses raw handling=100 curves, the proved TD scalar, and ready-only .95 before a single ceil(seconds*20). It never rescales prior rounded ticks. Inactive/invalid QD returns the prior wrapper result unchanged, preserving existing companion behavior.

## Validation limits

Two real JUnit classes exercise the production cycle/profile and check wrapper authority/read boundaries. Generator checks source pins, deterministic five-output reproduction, semantic/predicate negatives and source-corruption rejection. These do not prove Minecraft runtime or native input. ActualGT, shared hook execution, native ADS/swap behavior and integrated gates are master-owned and pending in this worker report. No game/client/server/CU/Vision/audio/performance certification is claimed.
