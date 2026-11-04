# W78 wave-frame research

Research date: 2026-10-24 (Asia/Seoul). Research only; parent owns runtime implementation.

## Immediate runtime handoff

- Both selected frame descriptions require **ground contact** to release the wave [O1]. A direct entity hit is not documented as an immediate wave trigger.
- Historical community descriptions say the flying grenade can ricochet from a **wall, object, or combatant** before landing. Wave heading then follows the grenade’s direction at ground contact, so a rebound can send it backward [C1]. This is useful qualitative support, not an authoritative current collision specification.
- **Heavy wave length is unverified.** Neither 15 m nor 22 m is established for Dimensional Hypotrochoid. The official 22-to-15 m change explicitly concerns special ammo [O4]. A heavy length chosen for Minecraft must be labeled authored.
- Bungie increased heavy-wave **width by 40%** in Update 7.3.5 [O3]. This is relative to its earlier heavy width, not an absolute width or a 1.4× heavy/special comparison.
- Do not invent a radial enemy-damage burst. Official material mentions heavy direct-impact/detonation damage changes and self-damage AOE, but supplies no usable compressed-wave damage split or burst radius [O2–O3]. Those mentions also prevent claiming the source game has universally zero impact/explosion/self-damage.

The parent’s selected terrain policy is an **authored Minecraft adaptation**: floor-UP contact creates a ground wave; lateral walls bounce the grenade in flight; wave lanes stop at walls/gaps; half slabs remain supported. Ground contact is the official anchor. Wall stopping has historical community support. The exact UP test, bounce coefficient, gap termination, slab support and slope tolerance are local rules, not verified Destiny constants. Entity collision should remain a separate decision from the floor trigger; current bounce-versus-detonation details have not been established. An entity collision must not acquire an invented ground wave or radial damage as a claimed official behavior.

## Pinned identity and provenance

W40 provenance and W73 manifest agree on version `245114.26.10.13.2000-1-bnet.66137`. The W73 inventory byte digest is `b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c`, matching W40 provenance. Both selected W40 stat maps match their exact W73 inventory entries.

| Selected weapon | Weapon hash | Ammo / element | Actual frame hash | Base BR / Velocity / RPM / magazine |
| --- | --- | --- | --- | --- |
| Deafening Whisper | `981718087` | Special / Void | `1395789926` Wave Frame | 50 / 64 / 72 / 1 |
| Dimensional Hypotrochoid | `1311684613` | Heavy / Stasis | `2571259936` Compressed Wave Frame | 50 / 33 / 120 / 5 |

These are definition stats before instance perks/mods. Velocity 64/33 is **not** a physical speed, and BR 50 is **not** 50 meters. Element alone does not prove a slow/freeze/volatile status effect.

Resolve the frame from `sockets.socketEntries[0].singleInitialItemHash`; reusable plug sets `29` and `430` each confirm the corresponding base frame. **Do not treat `sockets.intrinsicSockets[0]` as the frame:** both selected weapons put Legendary Infusion `3690882495` there. Enhanced frame variants returned by web search are not the selected base plugs. Same-name nonweapon records are also present, so resolve by exact selected hash.

The inventory source URL and per-entity canonical digests are in [pinned-identities.json](references/pinned-identities.json). Exact hashes, sizes, URLs and evidence boundaries for all inspected existing caches are in [cached-source-index.json](references/cached-source-index.json). The old W73 4.1.0 HTML is only a 1301-byte SPA application shell; its successful HTTP status does not make it an article-body source. Prior bow research files were inspected but provide no wave behavior evidence.

## Official evidence

| ID / source | Supported finding | Limit for implementation |
| --- | --- | --- |
| O1: [Pinned Bungie inventory](https://www.bungie.net/common/destiny2_content/json/en/DestinyInventoryItemDefinition-e677f6ea-2a1e-48d4-a8c8-700a39a62585.json) | Both intrinsics release their wave on ground contact; exact selected ammo, element and frame identity. | No dimensions, speed, slope, direct-hit damage or complete collision semantics. |
| O2: [Update 7.2.0.1](https://www.bungie.net/7/en/News/Article/season-witch-update-7-2-0-1) | Heavy-wave self-damage AOE size and damage were reduced for safer firing near the player’s feet. | Does not specify numerical radius or damage; does not establish a radial enemy burst. |
| O3: [Update 7.3.5, March 5, 2024](https://www.bungie.net/7/en/News/article/destiny_2_update_7_3_5) | Heavy-wave damage +20%, wave width +40%; enclosing heavy-GL section also reports impact +10% and detonation +5%, with a PvP offset. | Historical deltas; no absolute geometry or compressed-wave damage split. Do not stack these onto already-current values. |
| O4: [Update 8.0.0.1, June 4, 2024](https://www.bungie.net/7/en/News/article/destiny_2_update_8_0_0_1) | BR scales wave size, mostly width, also length/height. Display BR baseline becomes 50. Special-wave length changes 22→15 m except Dead Messenger. | Supports a published special-wave length for Deafening Whisper’s class. Does not establish a heavy length, width curve, linear interpolation law or 2026 live measurement. |
| O5: [Update 9.0.0.1, July 15, 2025](https://www.bungie.net/7/en/News/Article/destiny_update_9_0_0_1) | Fixed temporary immunity to other players’ similar-archetype wave damage. | Avoid a shared cross-player immunity gate; does not prove a same-wave hit count or cooldown. |
| O6: [Update 9.7.0, June 9, 2026](https://www.bungie.net/7/en-us/News/Article/destiny_update_9_7_0) | Both GL frame types receive Unstoppable in the archetype table; general heavy-GL damage vs bosses/champions +5%. | Later official context, outside the terrain implementation. No new wave dimensions or impact/wave split. |

O4’s general size paragraph is not restricted to special ammo; its following length-reduction paragraph is. Preserve this distinction. BR greater than 50 enlarges the wave segment relative to the stated baseline, but no exact width/length/height mapping is published in the examined text. Even at the selected base BR 50, this research cannot fill in heavy dimensions. A traveling wave’s total reach and an individual segment’s dimensions must not be silently treated as the same parameter.

## Community evidence, separately bounded

[C1: April 2022 player discussion](https://www.reddit.com/r/DestinyTheGame/comments/uewcis/is_there_a_trick_to_using_wave_frame_gls/) describes pre-ground bounces from walls/objects/combatants, backward waves after rebounds, waves stopping at walls, and travel on slopes/stairs. Other participants describe failures on uneven ground and tiny terrain features. These accounts support terrain-sensitive ground propagation qualitatively, without establishing a reliable slope angle, gap handling, slab rule, restitution or a current selected-weapon test.

**Reject C1’s old claim that BR does nothing.** Bungie’s June 2024 size-scaling change supersedes it. The thread is a historical community observation, not official Bungie policy; even a player post hosted on Bungie forums would remain community evidence.

[C2: Historical grenade-launcher breakdown](https://www.reddit.com/r/DestinyTheGame/comments/f1q96d/grenade_launcher_breakdown/) distinguishes wave damage from impact/blast contributions for Martyr’s Retribution. It is a different weapon in an older sandbox. Do not import its damage numbers, ratios or geometry into either selected weapon. Linked test images were not independently validated.

Summaries and claim-level limitations are stored in [community-observations.json](references/community-observations.json); official summaries are in [official-changes.json](references/official-changes.json). No large raw article content was copied.

## Explicit unknowns and local design boundary

| Parameter | What this research establishes |
| --- | --- |
| Deafening Whisper reach | Published special-wave length of 15 m in 8.0.0.1, previously 22 m; current persistence not exhaustively audited. |
| Heavy reach | Unknown; use a separately labeled authored value. Do not inherit either special value. |
| Absolute special/heavy width and height | Unknown; BR affects size, and heavy width received a historical +40% delta. |
| Wave propagation speed / duration | Unknown. Keep separate from the flying grenade’s Velocity stat. |
| Direct entity hit | Ground contact triggers the wave. Historical community account describes a possible prior entity bounce; current exact entity-collision behavior and damage remain unverified. |
| Wall / slope / gap / half slab | Community supports terrain sensitivity and wall stopping; precise Minecraft rules are authored. |
| Impact / detonation / wave damage split | Unknown for the selected weapons; historical generic heavy changes are insufficient to derive it. |
| Wave hit count / repetition | Unknown. Per-wave target deduplication is a possible local rule; cross-player immunity was officially fixed. |

The parent can keep a coherent ground wave without inventing radial damage: represent flying-grenade handling and surface-following wave propagation separately, use ground contact as the transition, and label collision thresholds/dimensions as Minecraft design. This is design guidance derived from the evidence, not recovered Destiny engine code or runtime verification.

## Research and verification boundary

The bounded pass used 15 queries in five batches, then targeted source opens/finds. Query themes, unverified fields and parent terrain choices are recorded in [research-boundary.json](references/research-boundary.json). Official sources through June 2026 were examined; this was **not an exhaustive patch audit through October 24, 2026**. No newer geometry change was established by this search. The October manifest pins identities and descriptions, not a complete executable physics specification.

External evidence came through a rendered/indexed web reader. These files retain source URLs, article/version locators and concise summaries, not origin HTTP bodies or raw reader payloads. No external byte hash is claimed. Existing on-disk caches were independently byte-hashed. Canonical entity hashes are explicitly distinguished from exact file hashes.

Validation is limited to parseable research JSON, pinned identity/stat/plug-set consistency, cached digests and owned-path checks. No builds or clients were run, no runtime file was edited, and no revert/commit/push was performed. W78 research files are the only writes by this sidecar.
