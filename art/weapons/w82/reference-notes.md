# W82 — Salvager’s Salvo remote-detonation evidence

Research completed 2026-10-25 Asia/Seoul (2026-10-24 UTC). Research-only sidecar. Exact selected key **`salvager_s_salvo` / 2060863616**. Parent owns implementation, input strategy, integration and tests. Only this file and `references/*` were written.

## Findings ready for the parent

| Question | Finding and strength | Source |
| --- | --- | --- |
| Identity | Energy-slot, Special-ammo, Arc grenade launcher; selected base magazine 1 and displayed RPM 90. | W40 pinned selected row and actual full official item definition, retained in `official-provenance.json` and `bungie-2060863616.json`. |
| Hold/release | **Official:** “One-shot handheld Grenade Launcher with remote detonation. \n[Shoot]  : Fire; release to detonate.” Fire launches the shot; release requests detonation, rather than launching a charged shot. | Actual item socket 0 → intrinsic **474269988**, `bungie-474269988.json`. The quoted `\n` denotes the source newline. |
| Direct character hit while held | **Official historical announcement:** breech GL projectiles “will now detonate on impact with a character, even if holding the trigger.” This supports a character-impact terminal path distinct from world ricochet. | Bungie TWAB, 2021-01-28, article 50040; retained full renderer text. Announced for the February 9 season. This pass did not independently retrieve the shipped patch note. |
| Arming minimum | **Community, qualitative:** an exact Salvo discussion says grenades have an “arming time” before release can detonate. No duration is given. | magicanon, 2021-02-15, comment `gnkkzt2`, literal retained text and timestamp. |
| Release before arming | **Unresolved:** no inspected source establishes ignored vs queued release, detonation exactly on becoming armed, or an early-release-specific fuse. | Official intrinsic is silent; community arming statement is insufficient to decide. |
| World bounce | **Community:** Salvo users report bouncing; advice explicitly discusses trajectory and bounce and floor-bounce detonation. World contact must not automatically inherit the character-impact rule. | Exact Salvo discussion; selected comments retained. |
| Bounce as arming bypass | **Tentative testimony only:** magicanon says bouncing “seems to help get around that arming time.” This is not an instrumented proof that contact instantly arms or zeroes a timer. | Same comment. Could reflect additional elapsed flight time; do not promote to a verified state transition. |
| Safety lifetime | **Unknown:** no maximum flight/held/fuse duration or mandatory expiry explosion established. | No numeric lifetime claim in retained relevant official/community content. |

**Do not source a 0.5 s / 0.6 s minimum, a tick count, distance threshold, or a safety fuse from this packet.** None was verified. The existence of a qualitative arming restriction is supported by dated community testimony, not an official numeric timing statement. “Arming time” in that testimony does not prove whether Destiny internally uses elapsed time, path distance, displacement, or a combination.

## Official pinned definitions, actually retained

Read W40 definitions/provenance and W46/W48 source notes first. W48 already resolved the exact intrinsic; this sidecar then opened the original complete cache and independently SHA-verified it against W40 before extracting full definitions, not just a paraphrase.

- Manifest version: **245114.26.10.13.2000-1-bnet.66137**.
- [Official pinned inventory URL](https://www.bungie.net/common/destiny2_content/json/en/DestinyInventoryItemDefinition-e677f6ea-2a1e-48d4-a8c8-700a39a62585.json).
- Original cache SHA-256: `b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c`.
- Full item 2060863616 canonical SHA-256: `2aac152f44fa7761604ed824701d6ee7c059ffaff5f054ab3146b703b7dfe64d`.
- Full intrinsic 474269988 canonical SHA-256: `2cc51f6a817ed965b6e8852b658349669deb4b9e06552d0fb04b2fc532336b5e`.

[official-provenance.json](references/official-provenance.json) records the original source URL/version/cache hash, complete socket entry, W40 selected row, W46 timing row, W48 evidence, local input byte hashes, canonical encoding, and retained-file hashes. [bungie-2060863616.json](references/bungie-2060863616.json) and [bungie-474269988.json](references/bungie-474269988.json) retain the complete actual definitions. Canonical hashes use UTF-8, sorted keys, compact separators and no newline; pretty-printed retained-file hashes differ legitimately.

The selected weapon initializes **Spike Grenades 3301904089** in socket 2, not Proximity Grenades; its full [definition](references/bungie-3301904089.json) is also retained. Do not introduce proximity detonation merely because another GL roll has it. Spike’s impact-damage description is not evidence of a world-surface impact explosion. The official Velocity stat is a unitless display stat, not recovered meters/second. W46’s firing/reload curves are cadence/reload evidence, not projectile arming or safety-fuse curves. W48’s `TRIGGER_PER_CYCLE` classification answers repeat-fire policy, not whether the existing input carrier reports release.

## Bungie historical character-impact statement

[This Week At Bungie – 1/28/2021](https://www.bungie.net/7/en/News/article/50040), published **2021-01-28T22:44:40Z**. Direct page fetch supplied a JavaScript shell; the substantive original article was read through [Jina’s renderer](https://r.jina.ai/https://www.bungie.net/7/en/News/article/50040). Full retrieved text is [bungie-50040-text.txt](references/bungie-50040-text.txt). This is original Bungie editorial content delivered through a third-party renderer, not renderer-authored mechanics.

> Breech Grenade Launcher usage is very low (outside of Mountaintop). We believe part of the reason is that the loop of "hold the trigger to arm, then release to detonate” is challenging to execute, particularly since projectiles can bounce off targets if the trigger is held
>
> Breech Grenade Launcher projectiles will now detonate on impact with a character, even if holding the trigger.

The article previews the next season. It is authoritative about the intended change, not a fresh October 2026 instrumented measurement. The later Salvo discussion independently corroborates actual direct-hit explosion behavior. Neither source says to defer a direct character impact until the remote-arming minimum; no numeric near-muzzle exemption/boundary was measured here. Do not generalize “character” to every Minecraft entity, ally, decoration, protected target or invulnerable object without local targeting policy.

## Exact Salvo community corroboration

[“Any tips on using Salvagers Salvo and similar grenade launchers?”](https://www.reddit.com/r/DestinyTheGame/comments/lkioea/any_tips_on_using_salvagers_salvo_and_similar/), **2021-02-15**. Actual browser page/comment DOM was inspected, including literal text, comment IDs, authors and `<time datetime>` timestamps. [community-salvo-comments.json](references/community-salvo-comments.json) retains selected transcriptions and permanent comment URLs. This is a dated discussion of the selected weapon, with independent commenters, but is not an authoritative timing test.

- [GoldkingHD, 17:44:37.298Z](https://www.reddit.com/r/DestinyTheGame/comments/lkioea/comment/gnjyv0k/): hit enemies directly, or keep holding the button and release when the grenade should explode.
- [SSaviorOfX, 17:47:43.609Z](https://www.reddit.com/r/DestinyTheGame/comments/lkioea/comment/gnjz92z/): “try to directly hit them* with it (it won't bounce off if you do that)”.
- [Duravash, 17:54:22.173Z](https://www.reddit.com/r/DestinyTheGame/comments/lkioea/comment/gnk035w/): “Direct hits explode on impact.” Holding/releasing R2 detonates manually.
- [magicanon, 20:40:20.553Z](https://www.reddit.com/r/DestinyTheGame/comments/lkioea/comment/gnkkzt2/), verbatim:

> All of these tips here are good. Another point I'd like to mention is that the grenades have what amounts to an "arming time" before you can release the trigger to detonate them. A good way around this is to bounce grenades off the floor and detonate them when the approach enemies. The act of bouncing off of something seems to help get around that arming time.

Preserve that commenter’s uncertainty. It does not establish how an already-released grenade behaves after the minimum, whether floor contact arms it immediately, or whether world impact after an early release causes explosion. Unsupported perk advice elsewhere in the thread was not adopted.

## Compendium check and bounded search result

Original Destiny Data Compendium [Weapon Perks](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit?gid=1662574278) and [Game Mechanics](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit?gid=1800463143) were fetched as exact CSV exports and retained. The Weapon Perks Lightweight Frame entry describes movement bonuses; it does not give this GL’s arming or early-release rule. No applicable numeric arming/lifetime claim was found in the inspected content. This absence is not proof of no arming restriction.

Original [Clarity live database](https://github.com/Database-Clarity/Live-Clarity-Database) was retrieved at immutable commit **039cfbc4732c33573568b28cc6335dd3332a9296**, commit time **2026-10-08T21:35:34Z**. The exact `descriptions/clarity.json`, commit API response and repository tree remain in references. It has no record for intrinsic 474269988 and supplied no applicable remote-detonation/arming statement. Do not cite Clarity as evidence of a delay merely because its other perk descriptions are credible.

[research-log.json](references/research-log.json) records inspected scope, negative results and access failures. Fightinglion.club returned HTTP 401 and Light.gg returned HTTP 403; their unread content is not cited. Google AI overview/search snippets were discovery only. Searches stopped without an exact timing claim; no continuing or exhaustive search is implied.

## Real video pixels retained; limited mechanics evidence

[EndgameXpress, “Destiny 2 - How to get Salvagers Salvo (Legendary Grenade Launcher)”](https://www.youtube.com/watch?v=lQZkhsr-cYs), published **2021-02-15T12:45:41-08:00** per retained YouTube player metadata. Description locates stats/perks at 4:28 and gameplay at 5:46. The actual downloaded [storyboard sheet](references/salvo-storyboard-sheet-2.jpg), [labeled contact sheet](references/salvo-storyboard-contact.jpg), and selected original 160×90 PNG cells retain real video-derived imagery. They are **low-resolution YouTube storyboard pixels**, not full-resolution extracted video frames or a downloaded continuous clip.

Revisit [04:35 / 275s](https://www.youtube.com/watch?v=lQZkhsr-cYs&t=275s), [04:40 / 280s](https://www.youtube.com/watch?v=lQZkhsr-cYs&t=280s), [05:45 / 345s](https://www.youtube.com/watch?v=lQZkhsr-cYs&t=345s), [05:50 / 350s](https://www.youtube.com/watch?v=lQZkhsr-cYs&t=350s), and [06:00 / 360s](https://www.youtube.com/watch?v=lQZkhsr-cYs&t=360s). The first two show the Salvo inventory screen; 280s includes a Lightweight Frame tooltip. Later cells show first-person combat and bright blue-white explosions. These were visually inspected. Fine tooltip wording comes from the official JSON, not unreadably small pixels.

The player’s storyboard spec uses 5-second spacing; M2 begins at sample index 50, hence approximately 250s. [salvo-storyboard-index.json](references/salvo-storyboard-index.json) retains that derivation, exact image URL, cell geometry, publication time and limits. Sampling is far too coarse to prove trigger release, a short arming minimum, collision timing, a bounce trajectory, or safety lifetime. Combat explosions may overlap weapon/perk/ability effects. Do not treat an explosion image as proof of its input cause. No physical trigger overlay or verified unmodified roll/buff state is present.

## Local implementation boundary — parent-selected TWO_HAND policy

The parent reports the user selected preserving **TWO_HAND**, accepting up to approximately **0.3s inferred release lag** (maximum 6 ticks at 20 Hz). This is a parent-reported decision, not independently tested by this research sidecar. Native-grip release was an earlier alternative and is not the selected strategy. The input-release approximation is **not** a sourced Destiny arming minimum, fuse, bounce window or latency measurement. Separate input-release inference/latency from projectile arming policy in naming, documentation and acceptance expectations.

The parent reports its current implementation uses **`ARM_TICKS=10` (0.5s), early release consumed/not queued, block reflection `.65`, cap 16, lifetime 100, range 48, and fallback blast**. These are explicitly **local policy**. The cap’s precise meaning, range units and terminal-expiry routing are parent-owned implementation details, not independently inspected here. If lifetime 100 denotes 20 Hz ticks, that is a local 5s cap; it is not evidence that Destiny has a 5s fuse. **No inspected authoritative source contradicts the reported arming/early-release policy, but no inspected source verifies its exact numeric threshold or consumed/not-queued behavior either.** “No contradiction found” must not be presented as validation of fidelity.

The following are implementation choices or engineering invariants, not recovered Bungie physics:

- Projectile velocity, gravity, drag, collision radius, swept collision, normal reflection, restitution, tangential damping, floor resting, bounce count and numerical offsets.
- The remote-arming threshold and its chosen time/distance representation. A positive local threshold can approximate the community restriction, but its value must be labeled authored.
- Whether pre-arm release is ignored, queued for eligibility, or falls back to a local fuse/impact rule. **No option is verified by this evidence.** The parent selected consumed/not-queued; keep it explicitly provisional local policy and do not write a test that claims it is measured Destiny behavior.
- Safety maximum age, whether expiry explodes or discards, chunk unload cleanup, owner death/disconnect, weapon-swap cancellation and multiple-projectile ownership.
- Owner/weapon/shot-token association, preventing a later gun’s release from controlling an unrelated old shot, exactly-once terminal detonation, protection/ally filtering, splash radius/falloff/LOS, damage transactions and server-tick quantization.

The source-backed behavioral core is launch on fire, hold for deliberate remote control, release to detonate when eligible, world-bounce capability, and direct-character-hit detonation despite hold. The retained community evidence motivates a pre-remote-detonation arming restriction but leaves its detailed policy unresolved. A generic “all block or entity hits explode immediately” model would omit the world-bounce behavior; a generic “every target hit bounces while held” model would contradict the official announced character-impact behavior and Salvo testimony.

## Artifact integrity and remaining gaps

[source-contract.json](references/source-contract.json) separates evidence from unknown numeric fields and parent-owned local decisions. [source-index.json](references/source-index.json) records URLs, capture times and source/derivative relationships. Capture times derived from retained-file mtimes are labeled as such; an official cached definition’s extraction time is not a fresh network retrieval or sandbox publication time. [file-inventory.json](references/file-inventory.json) hashes every other retained reference and these notes, excluding itself to avoid a recursive hash. Hashes establish local integrity, not that a community claim is true.

No exact early-release state transition, arming seconds/ticks/meters, current sandbox remeasurement, precise bounce physics, safety fuse, or native Minecraft input feasibility was established. No source or gameplay code, test, build, runtime, application configuration, commit or push was changed or executed by this sidecar.
