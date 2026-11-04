# W84 — Izanagi's Burden research

Research-only capture, 2026-10-24 UTC / 2026-10-25 KST. Parent owns production integration, input mapping and runtime policy. No tests, Gradle, game/server, native app, editor or user-app control was used. Only the authorized W84 research/data paths were written.

## Integration summary

- Exact official weapon: **Izanagi's Burden 3211806999**, Exotic Kinetic **Special-ammo** sniper; **90 RPM, magazine 4**.
- Exact intrinsic: **Honed Edge 1070100196**, sandbox perk **2409900926**. Official inventory wording: “[Alternate Weapon Action] : Consume the magazine and load a round with additional range and damage.” Current DDC/Clarity: consume **up to four ammo**, one Honed stack per round, to produce **one shot**.
- Current DDC explicitly says the loaded **Honed Edge persists through stow until fired**. Do not copy Ace's loaded-buff loss-on-stow rule.
- Catalyst: optional **529188544**, **Peerless Edge**, sandbox perk **578483750**. The weapon's default socket 10 is **Empty Catalyst Socket 1498917124**, not an installed catalyst. The static manifest cannot tell whether any particular user's instance has the catalyst equipped. **Do not enable it by default.**
- **Reload Speed is 40, not 70.** 70 is Impact. No inspected source establishes a 70-tick Honed duration.

`data/bungie-izanagi.json` is the full parsed official item record, not a hand-authored runtime definition. `data/extraction.json` separates official facts, community estimates, null/unknown fields and local-policy boundaries.

## Honed damage: body and critical are separate

These are **rounded community-research values**, not official exact sandbox constants. Each multiplier is relative to the otherwise applicable **uncharged shot of the same hit type**. A critical multiplier is not an extra scalar to multiply on top of the body multiplier; do not apply both to the same precision damage.

| Honed rounds combined | PvE body | PvE critical | PvP body | PvP critical |
|---|---:|---:|---:|---:|
| 2 | **1.12×** | **1.79×** | 1.20× | 1.91× |
| 3 | **1.25×** | **2.31×** | 1.45× | 2.67× |
| 4, no catalyst | **2.12×** | **3.91×** | 2.65× | 4.89× |
| 4, Peerless Edge | **2.55×** | **4.70×** | 3.18× | 5.87× |

Evidence: live-fetched DDC **Exotic Weapons row 25**, locator `441434520R24`; pinned current Clarity `/1070100196` and `/529188544`; light.gg's matching Community Research updated **2026-01-16**. Clarity HEAD lookup resolved to the same immutable commit reused from W83, **039cfbc4732c33573568b28cc6335dd3332a9296**. light.gg mirrors community notes and is not a third independent damage measurement.

DDC also expresses the precision changes as **+1.92** at x2 and **+2.74** at x3/x4; the total damage table above is safer than translating those additive precision terms into an assumed Minecraft base crit formula. DDC/Clarity describe the catalyst as a 20% increase for x4. Their rounded outputs do not justify manufacturing more decimal precision or applying 20% only to `(multiplier - 1)`. The source's displayed rounded body/crit totals are retained separately.

DDC's absolute **7739** catalyst precision damage is a reference-setting value, not universal damage against every enemy and not Minecraft HP. No numeric Honed range multiplier, exact Barrier activation condition, x1 Honed variant or all-target damage formula was established. The official intrinsic links the named Barrier sandbox perk but its description is empty.

## Ammo transaction: facts versus unresolved policy

| State/action | Supported finding | Boundary not established |
|---|---|---|
| Full ordinary magazine of four | Magazine compression plus the documented per-round stack count supports **four ordinary rounds → one x4 shot**. | Exact debit/credit animation frame. |
| Combining two or three | x2/x3 and one resulting shot are documented. | Whether a partial magazine is first topped up from reserve; which pool limits the count. |
| Empty magazine with reserve | Historical Cheese Forever description says holding reload immediately after firing can **reload and compact the magazine in one action**, avoiding two reloads. | Current precise empty-mag transaction, reserve debit order, partial-reserve boundary, commit frame. |
| Partial magazine plus reserve | No exact current algorithm established. | Magazine-only compression versus reserve top-up, e.g. mag 2/reserve 10. `min(4,mag+reserve)` is **not a verified rule here**. |
| Only one actual round available | No sourced x1 behavior established. | No-op, ordinary reload or charged state. |
| Ordinary/tactical reload while an unfired Honed round exists | Not resolved by current official/DDC/Clarity descriptions. | Preserve, clear, refund/decompress, fill remaining slots, or reject. |
| Alternate reload while already Honed | Not resolved. | No-op, recharge/upgrade, refunds and further costs. |
| Cancel before/after insertion; replay input | Not resolved by exact current frame evidence. | Commit/refund boundary, post-cancel fire delay, locking and replay policy. |

**Conservation inference, not an observed reserve algorithm:** n ordinary rounds fund one compressed projectile. If the HUD represents that as one loaded round, compression lowers available round-equivalents by n−1 and firing spends the remaining funded projectile. It must not become “consume n, then consume another n/another unfunded ordinary round on fire.” This accounting statement does not select the magazine/reserve pool or authorize restoring spent compression rounds after a reload/cancel.

A conservative locked transaction, rejection of repeat/charged requests, ownership/stack validation, atomic commit and no free/replayed funded shot are reasonable implementation safeguards. Their exact state transitions, pool selection, charged-reload behavior and cancellation/refund choice must be documented as **local policy**, not claimed as verified Destiny mechanics. Parent has deliberately not selected ammo semantics yet; this research does not silently select them.

The clip “How to reload Izanagis without losing Honed Edge” explicitly uses **Transversive Steps** and calls the result an exploit (four displayed rounds plus x4, equivalent to seven). It is **not evidence that ordinary tactical reload preserves Honed**, and does not authorize minting extra ammunition in W84.

## Reload timing and cancellation

Official shipped [Destiny 2 Update 2.8.0](https://www.bungie.net/en/News/Article/48838), March 10, 2020:

> Honed Edge's animation is no longer affected by reload speed.
> Outlaw has been replaced with No Distractions.

The [February 20, 2020 announcement](https://www.bungie.net/en/News/Article/48743) specifically says the animation is no longer affected by the **reload stat**. Raw Jina-rendered text from both original official URLs is retained with retrieval URLs and SHA256.

Current DDC says: **“Honed Edge's Reload Animation Speed is the same as a regular reload's.”** It also calls the action a slower reload. This provides neither an exact time nor proof of a fixed additional firing delay. Read it alongside the explicit official no-reload-speed change; do not infer a restoration of reload-buff scaling from that one sentence. The historical official rule supports not accelerating Honed via Reload Speed; the inspected evidence does not exhaustively test every present-day duration scalar/ability exception.

**Unknown:** exact normal and Honed animation duration, full fire-ready duration, insertion fraction, cancellation frame, sprint/swap-cancel delay, and resulting simulation tick rounding. In particular **70 ticks, 3.3 seconds, 3.0 seconds, or an early-ammo-credit fraction are not established here**. Any duration derived from the project's historical stat curve or chosen timer-only cycle is local conversion, not an independently measured Honed charge time.

The 2019 Chevy cancellation guide predates 2.8.0 and cannot establish current cancel timing. Some showcase segments are explicitly slow-motion. Sampled storyboard images at one/two/five-second intervals cannot validate frame-level charging or hidden fire lockout. No full video/audio stream was downloaded and the attempted caption endpoint returned zero bytes.

## Official fixed roll and display stats

Zero-based sockets 0–4:

| Index | Fixed plug | Hash |
|---|---|---:|
| 0 | Honed Edge | 1070100196 |
| 1 | Chambered Compensator | 3661387068 |
| 2 | Accurized Rounds | 3142289711 |
| 3 | No Distractions | 2866798147 |
| 4 | Composite Stock | 3465198467 |

Their reusable plug-set hashes **1468, 850, 210, 1469, 192** are singleton **fake** fixed sets, not randomized socket pools. Do not install Outlaw or treat No Distractions as an optional legendary choice. Official No Distractions text reduces flinch after aiming briefly. General Clarity reports **35% flinch resistance after 1 second ADS without firing**, retained until leaving ADS; these numeric details are community research, not official numeric text.

| Stat | Official weapon display value | Fixed-plug change | Derived fixed-roll display value |
|---|---:|---:|---:|
| Impact | 70 | 0 | **70** |
| Range | 48 | +10 Accurized | **58** |
| Stability | 41 | +10 Chambered, +5 Composite | **56** |
| Handling | 47 | −5 Chambered, +5 Composite | **47** |
| Reload Speed | 40 | 0 | **40** |
| Recoil Direction | 73 | +10 Chambered | **83** |
| RPM | 90 | 0 | **90** |
| Magazine | 4 | 0 | **4** |
| Aim Assistance | 62 | 0 | **62** |
| Zoom | 45 | 0 | **45** |
| Airborne Effectiveness | 6 | 0 | **6** |
| Ammo Generation | 60 | 0 | **60** |

The affected stat curves are identity-scaled in official stat group **1069606838**. Already displayed RPM 90, Impact 70 and Magazine 4 are not reinterpolated from raw investment values. Ammo Generation 60 is **not a reserve-round count**. These display stats do not specify reload seconds, damage per shot, targeting geometry or flinch implementation.

## Raw sources, gameplay frames and provenance

Authoritative requested cache: `/tmp/destiny-weapons-w30/bungie-items.json`, SHA256 **b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c**. It matches the W83 official inventory pin. Original retrieval time is unknown; provenance records inspection/copy times separately. Pinned manifest version: **245114.26.10.13.2000-1-bnet.66137**. Official manifest/stat/stat-group/sandbox components and fixed plug sets were reused from W83/W73 without changing their bytes. Exact item-object slices from the authoritative cache are retained in `references/official-item-*-raw.json` and `official-izanagi-item-raw.json`; pretty-printed data and grouped records are labelled extractions, not fresh HTTP responses.

`references/retrievals.json` records every actual HTTP response, including blocked/empty discovery responses; each includes URL, retrievedAt, byte length and SHA256. `references/provenance.json` records the cache reuse chain, source URLs, original retrieval metadata where available, extraction relationships and hashes of all delivered files. Failed Google/Bing/DDG/Reddit discovery is not numeric mechanics evidence.

`references/gameplay-evidence.json` pins actual video identity/date, sheet geometry and timestamp formula. All listed sheets are actual fetched YouTube storyboard JPEGs, not cover thumbnails or generated reconstructions. Visually inspected:

- [Cheese Forever — Izanagi's Honed Edge Without Reloading Twice](https://www.youtube.com/watch?v=KgJR3zohsEs), **2019-01-11**: L3 320×180, 1-second sampling, 3×3 sheets M0–M4. Full reload and glowing charge poses are visible; M2 covers approximately 0:18–0:26 and illustrates a reload/compression sequence. The raw description explicitly says reload and compact in one action. This is historical qualitative evidence, not current reserve-debit/timing proof.
- [JesseRayCards — Honed Edge shot on every reload](https://www.youtube.com/watch?v=9ZajP0XS6UE), **2020-10-05**: L2 160×90, 2-second sampling; M0 visually inspected. Too small to establish a numeric ammo ledger.
- [Ultraclocked — audiovisual showcase](https://www.youtube.com/watch?v=ov6C5oF7KSc), **2021-06-21**: L2 160×90, 2-second sampling, M0–M2 visually inspected. Source chapters: ordinary reload 0:17, Honed 0:38, ADS Honed 1:26, reticles 1:48, turning Honed vfx on/off 1:54, holstered 2:13. These support appearance/animation references, not exact durations; slow-motion chapters are explicitly labelled.
- [Mert Iyigül — reload without losing Honed](https://www.youtube.com/watch?v=behjxV72rlY), **2020-04-09**: M0/M1 visually inspected; contextualized as the Transversive Steps exploit above, not ordinary reload behavior.
- [jackpot — Izanagi Rocket Reload](https://www.youtube.com/watch?v=NQ-RFx0EfgU), **2022-04-13**: M0 visually inspected; demonstrates a swap rotation qualitatively, not a measured current ammo algorithm.
- [Chevy — Reload Cancellation Tips & Tricks](https://www.youtube.com/watch?v=CXDF6_IVMnA), **2019-12-15**: raw metadata and sheets retained; historical guide only, no current numeric conclusion adopted.

No inferred unseen frames, invented frame measurements, unresolved ammo transactions or approximate community values are promoted to official facts. The unresolved boundaries above are the handoff for integration.
