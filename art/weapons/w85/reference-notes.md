# W85 — incoming-hit flinch / Izanagi No Distractions

Research-only capture, 2026-10-24 UTC / 2026-10-25 KST. Only W85 reference-notes.md, references/* and data/research.json were written. W84 and production were not changed. No tests, Gradle, game/server, native app, editor or global MCP control was used.

## Integration facts now

| Event | Supported finding | Qualification |
|---|---|---|
| Base No Distractions proc | **1.0 second ADS without firing**, starting when **ADS input is pressed** | Pinned Clarity community research, not an official numeric perk description. |
| Active effect | **35% flinch resistance = 0.65× remaining flinch** | Clarity; Bungie's 2022 official worked stacking example independently includes 0.65 for No Distractions. |
| Fire before proc | The shot interrupts the required uninterrupted ADS-without-firing interval; a renewed quiet interval is needed | Inference from activation condition. Exact reset-versus-pause internals, dry fire and failed inputs are not described by the source. |
| Fire after proc | **Retain while still ADS** | Clarity explicitly says “Remains active until you're no longer ADS.” Do not treat every paid shot as removing an already active perk. |
| End ADS | Active effect ends | Explicit community text. |
| Stow | Ends the ADS-session effect; do not persist it like funded Honed Edge | Inference from ADS-ending removal condition, not an independently measured stow exception. |
| Reload / handling | **ADS termination clears**; no independent exception established | Held ADS input is not proof that actual ADS continued during reload/raise/lower. Neither unconditional retention nor an extra clear despite uninterrupted ADS is established. |

Official exact base trait **2866798147**, sandbox perk **3847840073**; official text: “Aiming this weapon for a short period reduces flinch.” Izanagi **3211806999** fixed socket 3 has `singleInitialItemHash:2866798147`. This is not an optional legendary socket choice. Enhanced No Distractions **3974407819** is **0.9 seconds** in Clarity and is **not** equipped by this fixed Izanagi roll. Do not shorten the base threshold to 0.9 seconds.

Evidence: `official-item-2866798147-raw.json`, `official-izanagi-item-raw.json`, and Clarity JSON pointer `/2866798147/descriptions/en`. `clarity-no-distractions-extracted.json` contains base, enhanced and Whisper-specific records for comparison; it is explicitly an extraction, not a fetched response.

## Official Stability-family resistance and stacking

[Bungie — This Week at Bungie, April 21, 2022](https://www.bungie.net/en/News/Article/51250) defines flinch as **“Aim deflection on receiving damage”**. It says Stability now also grants resistance, with these values **at 100 Stability**:

| At 100 Stability | Weapon families |
|---|---|
| **25%** | Auto Rifle, Submachine Gun, Bow |
| **20%** | Pulse Rifle, Scout Rifle, Sidearm, Machine Gun |
| **15%** | Hand Cannon, Trace Rifle |
| **10%** | Fusion Rifle, Shotgun, Sniper Rifle, both Breech and Drum Grenade Launchers, Special and Heavy Linear Fusion Rifles, Rocket Launcher |

The same article says **higher-zoom weapons are more affected by flinch**, Stability **below 20** technically incurs a small penalty, and **sources stack multiplicatively**. Its worked example is `0.8 * 0.8 * 0.9 * 0.65 * 0.7 * 0.5`, approximately 0.1 remaining flinch. This supports multiplying remaining-flinch factors, not adding resistance percentages. [Update 4.1.0, May 24, 2022](https://www.bungie.net/en/News/Article/51380) confirms the Stability system shipped and links the breakdown.

**Do not silently promote endpoints into an exact curve.** These retrieved official paragraphs do not give a complete interpolation/extrapolation equation, cap behavior, zoom scalar, or absolute pitch/yaw magnitude. A source-derived family endpoint does not itself prove `stability/100 * familyMaximum`, or any other exact formula. W84's fixed-roll Izanagi Stability **56** is supported by official display 41 + Chambered Compensator 10 + Composite Stock 5, but its exact resulting resistance is **null** here. Swords, Glaives and later weapon types are not assigned invented rows.

The article also gives historical Resilience endpoints 0% at stat0 and 10% at stat100. These are not a current2026 character-stat audit and must not silently become universal implementation requirements.

## Later official patch: retain scope

[Update 7.3.6 — April 9, 2024](https://www.bungie.net/7/en/News/article/destiny_2_update_7_3_6), **“Crucible Only Changes”**:

> Reduced flinch taken by all Primary weapons by 15%.

This is a **receiving/held Primary weapon** change in **Crucible**, not “any hit from a Primary weapon inflicts 15% less flinch.” It does not apply to a held Special-ammo Izanagi. The implied remaining factor is 0.85, but it is not an all-activity multiplier.

**Current-version limit:** this bounded pass did not establish a comprehensive unchanged-through-2026 table. Other attempted modern article slugs returned site shells despite HTTP200; searches were CAPTCHA-blocked or off-topic. Such responses do not prove there were no later changes. No unverified modern sniper/PvE reduction is adopted. The 2022 table remains labelled historical official, with the scoped verified 2024 change above, not labelled an exhaustive current sandbox specification.

## Incoming direction / aiming relation

Official retrieved text supports damage-induced aim deflection and a zoom relationship, **not** an exact attacker-vector-to-camera-rotation function. Do not claim universal upward kick, universal kick away from the attacker, or head-seeking aim correction from these sources.

Actual historical Destiny gameplay references are pinned, not generated:

- [CoolGuy — The Bizarre way Flinch works in Destiny 2](https://www.youtube.com/watch?v=zXJvpfdmWS0), **2018-10-11**. The raw creator description explicitly says he believes the odd mechanic may be controller/console-only and asks whether it is the same on PC. This is a material platform/input and historical-version limitation. L2 M0/M1 sheets cover approximately **0:00–0:48 / 0:50–1:38**, sampled every **2 seconds**, 160×90 tiles in a 5×5 sheet. Visually inspected repeated scoped target views with red damage overlays and visible scope displacement. These sparse samples cannot isolate a hit's full direction/recovery or establish whether a later shot returns toward a head under every input mode.
- [CoolGuy — Destiny 2: The new Flinch Resistance system is crazy and you NEED to do this!](https://www.youtube.com/watch?v=yZnltegf48g), **2022-06-17**. L2 M0/M1 cover approximately **0:00–2:00 / 2:05–4:05**, sampled every **5 seconds**. Visually inspected gameplay, loadout screens and official-text presentation. This corroborates the qualitative era/context of resistance testing, not a measured angle or proc/reset timing test.

`gameplay-evidence.json` retains the exact page metadata, storyboard specifications, sheet geometry and timestamp formula; JPEG URLs/retrieval times/hashes are in retrievals.json. No complete video/audio stream was downloaded. Captions request returned zero bytes, so no unseen transcript is claimed. Search-produced AI claims about source direction are **not evidence**.

## Explicit unknowns / local-policy handoff

The following remain **null**, not guessed: exact D2 kick degrees, recovery duration/curve, exact Stability interpolation, zoom scaling function, incoming-source yaw/pitch relation, damage-magnitude scaling, shield/health/absorption distinction, zero-loss/immune/DoT/area-damage matrix, exact native hook location and same-tick proc/shot ordering.

- A **post-`Player.actuallyHurt` effective-loss hook** is a local architecture choice; the retrieved sources do not specify Destiny's callback/debit ordering.
- An **authored clamped delta**, fallback direction, accumulation/cap and recovery are local feel/safety policies, not measured D2 angles. Do not add automatic head-seeking correction based on a historical controller observation.
- **20 ticks** is conversion of one second at20TPS, not an independently observed Destiny tick boundary. Decide same-tick ordering explicitly and test locally.
- Clear/restart according to actual ADS-session boundaries. Reload, handling, held input, owner changes and stack replacement must not be mistaken for demonstrated Destiny exceptions.

## Provenance and preservation

`references/provenance.json` inventories every delivered file with SHA256. `retrievals.json` retains every actual fetched body with URL/retrievedAt/SHA256 and classifies shell/CAPTCHA/404/empty/failure results as non-evidence. Jina URLs are the actual retrieval URLs; originUrl records the corresponding official/third-party page. Failed requests retain generated exception text and are labelled as failures, not fabricated raw HTTP bodies.

`reuse-provenance.json` records byte-identical W84 copies with original capture time where known, copy time separately, source URL and hash. The Clarity pin is immutable commit **039cfbc4732c33573568b28cc6335dd3332a9296**, original capture **2026-10-24T16:08:37.641389+00:00**, SHA256 **881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384**. Official inventory slices trace to the authoritative `/tmp/destiny-weapons-w30/bungie-items.json`, SHA256 **b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c**, original retrieval time unknown, manifest **245114.26.10.13.2000-1-bnet.66137**. W84's full provenance is retained byte-identically as `w84-provenance-raw.json`; its historical output hashes describe W84, not W85.

No production, tests, build scripts, logs, W84 research files or user applications were changed.
