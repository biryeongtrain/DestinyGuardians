# W83 — Ace of Spades trait/mechanics research

Research capture: 2026-10-24 UTC / 2026-10-25 KST. Research-only sidecar. This work writes only `art/weapons/w83/reference-notes.md` and `references/*`; parent owns catalog extraction, runtime and audio.

## Integration facts and unresolved decisions

| Mechanic | Supported statement | Evidence / confidence |
|---|---|---|
| Identity | Ace of Spades **347366834**, Exotic Kinetic primary hand cannon, 140 RPM, 13 rounds | Official pinned manifest |
| Intrinsic | Memento Mori **647617635**; radar while ADS, reload after kill grants empowered bullets | Official description; radar wording does not require an active damage buff |
| Kill-to-reload window | **Finish** a reload within **3.6 seconds** of a kill | DDC Ace row 6; Clarity `/647617635`; light.gg intrinsic Community Research |
| Mori rounds | **6**; firing consumes a stack per shot | Current DDC; count/stow independently confirmed by shipped Bungie Update 2.5.0.1 |
| Mori damage | **+68% PvE / +29% PvP**, i.e. **1.68× / 1.29×** the otherwise applicable shot damage | Community DDC + Clarity + light.gg; not official numeric specifications |
| Mori range | **15% decreased damage falloff distance** while active | Community DDC + Clarity; not a 15% damage penalty |
| Stow | Removes loaded Mori buff; **pending reload trigger persists through stow** | Current DDC expressly distinguishes the two states; official 2019 patch confirms loaded bullets lost on stow |
| Firefly | Exact Ace trait **1561789734**; precision kills produce **Solar** explosion and improve reload | Official description; weapon's main damage stays Kinetic |
| Firefly reload | **+50 Reload Speed for 6 seconds** | Ace-specific Clarity + light.gg; general DDC Firefly says reload buff persists through stow |
| Firefly geometry | **7.5 m radius**, damage falloff starts at **3.75 m** | Ace-specific DDC + Clarity + light.gg |
| Funeral Pyre | Optional catalyst **3708505013**, sandbox perk **113389597**; Firefly stronger while Mori active | Official catalyst linkage and exact description |
| Catalyst number | **+50% Firefly explosion damage / 1.5×**, while Mori active | DDC Ace row + light.gg catalyst Community Research |

**Reload event boundary:** inspected sources say “finishing a reload,” not “starting a reload.” They do not distinguish the ammo-transfer frame from full animation completion. Mapping completion to W65 ammo credit is a local integration choice. Capturing eligibility solely at reload start can allow activation after 3.6 seconds and is not established by the source. Exact equality at the deadline, simulation ticks, interruption and cancellation rules remain unknown.

**Reload while buffed:** no inspected source directly establishes whether reloading without a fresh kill preserves remaining Mori rounds. Neither the source's list of removal events nor a video chapter entitled “Memento Mori w/ Reload Sound” resolves that state transition. A fresh qualifying reload “grants six”; replace-versus-add behavior with existing stacks is not explicitly documented here. Preserve these as unverified integration decisions, not externally verified behavior.

**Firefly duration scalar:** no independent **0.8× reload duration** is supported. +50 is a reload **stat** bonus with a 6-second lifetime, not a 50% reduction in reload time. Sources do not provide the project's stat-to-duration conversion.

**Kill/action eligibility:** descriptions say “a kill” without exhaustively specifying direct Ace kills, Firefly, other owned damage, grenade or melee eligibility. Do not assert direct-shot-only eligibility from these entries. Removal on stow does not enumerate grenade, melee, super, death/respawn, teleport or inventory events; action-to-stow mappings remain local policy. Catalyst eligibility on the final Mori round after consuming its last stack is also unresolved.

## Official fixed roll and stats

[official-summary.json](references/official-summary.json) contains exact fixed plug identities, complete relevant sandbox perk records, and separately labelled arithmetic. Zero-based sockets 0–4 are **Memento Mori 647617635**, **Corkscrew Rifling 4090651448**, **High-Caliber Rounds 1561002382**, **Firefly 1561789734**, **Smooth Grip 3326204863**. Their reusable sets are singleton **fake** sets, not randomized perk pools. Default socket 10 is **Empty Catalyst Socket 1498917124**; Funeral Pyre must not be assumed active by default.

| Stat | Weapon definition display value | Fixed-plug bonus | Derived fixed-roll display value |
|---|---:|---:|---:|
| RPM | 140 | 0 | 140 |
| Impact | 84 | 0 | 84 |
| Range | 75 | +10 | **85** |
| Stability | 40 | +10 | **50** |
| Handling | 40 | +10 | **50** |
| Reload Speed | 42 | 0 | **42** |
| Magazine | 13 | 0 | **13** |
| Aim Assistance | 70 | 0 | 70 |
| Zoom | 14 | 0 | 14 |
| Recoil Direction | 100 | 0 | 100 |
| Airborne Effectiveness | 14 | 0 | 14 |
| Ammo Generation | 56 | 0 | 56 |

The three derived increases are arithmetic using the official fixed plug investment stats and identity-scaled stat curves. Do not re-interpolate the already displayed 140 RPM, 84 impact or 13 magazine using their raw investment values. These are UI/stat values, not a sourced reload duration, damage-per-shot formula or reserve-ammo count. The manifest also links Memento Mori to sandbox perk **3469621377**, “[Shield-Piercing] Barrier,” with an empty description; detailed activation conditions were not established.

## Source separation and numeric cautions

Official inventory version **245114.26.10.13.2000-1-bnet.66137** was reused from the W73 private cache referenced by W77/W80; W60's corresponding pins match. The requested `art/weapons/w40/bungie-manifest.json` does not exist in this checkout. W40 instead has `provenance.json`, which names the exact inventory URL and SHA256. The copied W73 manifest and W40 provenance are retained as raw JSON. Inventory SHA256 **b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c** and plug-set SHA256 **8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959** were checked. Original cache retrieval time is unknown; provenance distinguishes it from this session's cache inspection time. Exact raw weapon JSON is retained in [official-ace-item-raw.json](references/official-ace-item-raw.json). Additional stat/stat-group/sandbox components were fetched using URLs from that same pinned manifest.

The original [Destiny Data Compendium, Exotic Weapons](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit?gid=441434520) has Ace in **row 6**, HTML locator `441434520R5`. Its general Firefly entry is Weapon Perks **row 95**, locator `1662574278R94`. Full actual fetched HTML plus exact row extractions are retained. Blue `#a4c2f4` denotes PvE and red `#ea9999` PvP, as the Landing legend states. [mechanics-evidence.json](references/mechanics-evidence.json) preserves unmodified formatted rows and exact Clarity records.

[Clarity](https://raw.githubusercontent.com/Database-Clarity/Live-Clarity-Database/039cfbc4732c33573568b28cc6335dd3332a9296/descriptions/clarity.json) was fetched at the same immutable commit used in W80. The full raw JSON is retained; Ace-specific records are `/647617635` and `/1561789734`. These are community research. light.gg's matching community notes substantially mirror these records and should not be counted as an independent game measurement. light.gg dates its intrinsic/Firefly notes **2026-07-14** and catalyst notes **2026-07-08**. Capture date is not source update date.

Ace Firefly's community reference maximum is **436 PvE**, with a **20% PvE endpoint floor** reported by DDC. This is not universal damage against every target: DDC's general entry explicitly says scaling depends on weapon type and combatant rank. Its Landing legend specifies **Elite Combatants in the Shooting Range, 0 Weapons, Normal Difficulty Delta (0)** as the reference setting, and default Crucible settings for PvP. DDC marks PvP **[80?]** and minimum **[?]**, whereas Clarity/light.gg state 80 without uncertainty. Keep current PvP explosion numbers provisional. Neither source supplies a linear attenuation curve, LOS algorithm, AABB targeting or Minecraft health conversion.

Use **Ace's exact trait**, not ordinary Firefly **3824105627** or enhanced legendary **1183436451**. Clarity's ordinary row says 4 m while current DDC general Firefly says 7.5 m; Ace-specific rows agree on 7.5 m. The Clarity/light.gg claim “272% stronger” does not algebraically match their displayed 436 versus 104 damage figures; no exact universal relative multiplier is adopted. DDC's phrase “Enhanced Firefly” in the Ace row describes Ace's effect, not authorization to install the separately hashed enhanced legendary trait or grant its +55 reload.

The official [Update 2.5.0.1, June 4, 2019](https://www.bungie.net/en/News/Article/47880) explicitly shipped “Memento Mori restored to 6 bullets, but bullets are now lost on stow.” Full Jina-rendered official article text is saved with both retrieval and original URLs. The May 16 announcement is also retained; its PvP comments are historical and are not current numeric damage evidence.

## Gameplay frames and retrieval limits

[gameplay-evidence.json](references/gameplay-evidence.json) records video identity, publication date, chapters, exact storyboard layout and sample locators. Actual raw YouTube storyboard JPEGs were retrieved and visually inspected for these community clips:

- [Boosh Ninja — Ace of Spades sound/visual showcase](https://www.youtube.com/watch?v=YXSMO6Dk-r8), published **2023-02-17**: 160×90 frame tiles every 5 s. Sheet M0 samples near **0:05**, **0:15**, **1:20**, **2:00** show held/aimed weapon and reload/handling poses; M1 tile 24 near **4:05** shows combatant aiming. The description labels Mori shooting at 1:17 and Mori/reload at 1:50.
- [Aztecross — Ace of Spades Masterwork review](https://www.youtube.com/watch?v=NmBz_DZEEVc): 160×90 frames every 2 s; M1 tile 2 near **0:54** shows the Mori inspection tooltip. Historical 2019 numeric overlays are not current sandbox measurements.
- [Dumitrascu Andy — Ace of Spades Memento Mori clip](https://www.youtube.com/watch?v=dZBF6SqdKhI): 160×90 frames every 1 s, aiming/handling in a blue-lit environment.

These are sampled clip frames, not invented timestamps or promotional cover thumbnails. Resolution/sampling do not establish HUD stack changes, the 3.6-second boundary, reload-preservation behavior, exact fire cadence or catalyst proc ordering. No full video/audio stream was downloaded. Captions returned zero bytes. Google/DuckDuckGo/Reddit attempts yielded challenge/blocked shells; Bing discovery results were irrelevant. Their raw responses remain captured as unsuccessful discovery, never mechanics evidence. The direct Ace light.gg rendering was blocked; the intrinsic, exact Firefly and catalyst pages were accessible through Jina.

[provenance.json](references/provenance.json) records source URL, retrievedAt, response bytes/SHA256, reuse pins, and hashes of the delivered artifacts. Raw fetched content is retained beside the extracted findings. Verification is JSON parsing, source-pin/hash checks and exact identity/row checks only; no production edits, Gradle, game client, native app or tests were run.
